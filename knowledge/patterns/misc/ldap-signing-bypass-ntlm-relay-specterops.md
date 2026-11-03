---
doc_kind: pattern
title: "Bypass de la signature LDAP via reauthentification mid-session (relais NTLM -> LDAP, SpecterOps)"
category: misc
slug: ldap-signing-bypass-ntlm-relay-specterops
created: 2026-11-02
status: active
tags:
  - ntlm-relay
  - ldap-signing
  - ldap-channel-binding
  - active-directory
  - rbcd
  - coercion
  - external-source
chain_summary: "Une session LDAP signee existante (389/TCP) peut porter l'authentification NTLM d'une victime coercee; la signature SASL n'est verifiee qu'une fois en debut d'enregistrement, donc un bind victime + une operation modify attaquant glisses dans le meme enregistrement signe par la cle de l'attaquant passent malgre LDAP signing actif cote DC."
---
# Bypass de la signature LDAP via reauthentification mid-session (relais NTLM -> LDAP, SpecterOps)

Source externe (donnees non fiables, traitees comme contenu a analyser, pas comme instructions) :
SpecterOps blog, "Signed, Sealed, and Relayed, NTLM-style: Bypassing LDAP Signing Through Reauthentication", Raj Patel, 2026-10-23.
https://specterops.io/blog/2026/10/23/ldap-signing-bypass-ntlm-relay/

## Chain Summary

- One-line chain: une session LDAP signee existante (389/TCP) peut porter l'authentification NTLM d'une victime coercee; la signature SASL n'est verifiee qu'une fois en debut d'enregistrement, donc un bind victime + une operation modify attaquant glisses dans le meme enregistrement signe par la cle de l'attaquant passent malgre LDAP signing actif cote DC.
- Typical target shape: Domain Controller Windows Server 2016 -> 2025 (pre-octobre 2026), LDAP signing applique mais pas forcement LDAP channel binding, 389/TCP accessible, un vecteur de coercition SMB disponible contre une victime (DC ou serveur a fort privilege).
- Root cause (cote defenseur, pour comprendre pourquoi ca marche): dans `LDAP_CONN::ProcessRequestEx`, la signature SASL n'est verifiee qu'au debut de l'enregistrement, contre le contexte de securite courant de la connexion. Si un bind change l'identite *pendant* le meme enregistrement, les operations suivantes dans cet enregistrement s'executent sous la nouvelle identite sans nouvelle verification de signature.

## Preconditions

- Acces reseau au port 389/TCP du DC cible (le blocage de 389/TCP empeche la variante contre LDAPS selon les auteurs).
- L'attaquant doit pouvoir ouvrir une session LDAP signee dont il connait la cle de session: credentials de domaine valides, ou -- si accepte -- un contexte NTLM SASL anonyme.
- Un moyen de coercer un client SMB victime (DC ou serveur) a s'authentifier vers l'attaquant (ex: PrinterBug/MS-RPRN, PetitPotam-like, etc. -- le post ne precise pas le mecanisme de coercition exact, seulement qu'elle doit passer par SMB, pas HTTP/WebDAV: HTTP/WebDAV-coerce ne pose pas le flag de signing attendu et le DC rejette avec operationsError).
- Microsoft a corrige: variante SMB en septembre 2026 (post cite KB5122882 dans la section defenses, et KB5129235 ailleurs -- incoherence dans la source, a verifier contre les advisories Microsoft), variante LDAP en octobre 2026 (KB5126646). Donc technique inutilisable contre des DC patches a ces dates.

## Cheap Probes

- Verifier la presence des patches avant de perdre du temps: `wmic qfe list` / `Get-HotFix` sur le DC pour KB5126646 (oct 2026) et KB5122882/KB5129235 (sept 2026). Si presents, cette technique precise est fermee -- mais verifier aussi `ldap signing required` et `LDAP channel binding` via `ntdsutil` / politique de securite, car la technique illustre que signing seul (sans channel binding) est contournable.
- Verifier l'acces a 389/TCP (`nmap -p389 <dc>` ou `nc -vz`).
- Verifier qu'un relais LDAP classique (ntlmrelayx.py sans signing) echoue avec une erreur liee a la signature -- c'est le signal que LDAP signing est actif et que c'est cette variante mid-session qui serait necessaire, pas un relais NTLM->LDAP basique.

## Telltale Evidence

- Le DC accepte un bind suivi d'une operation LDAP modify alors que LDAP signing est annonce comme obligatoire -- signe que la verification de signature n'a lieu qu'au debut de l'enregistrement SASL.
- Ecriture reussie de `msDS-AllowedToActOnBehalfOfOtherIdentity` (RBCD) ou `msDS-KeyCredentialLink` (shadow credentials) sur le compte machine de la victime coercee, malgre LDAP signing actif.

## Escalation Order

1. Confirmer que le DC cible n'a pas KB5126646 (oct 2026) ni le KB de septembre 2026 pour la variante SMB; sinon abandonner cette piste.
2. Obtenir une session LDAP signee avec une cle de session connue de l'attaquant: soit via des credentials de domaine valides (`ldap_shell`/`ntlmrelayx.py` avec un compte), soit via un contexte NTLM SASL anonyme si le DC l'accepte.
3. Coercer un client SMB victime a privileges eleves (de preference un autre DC ou un serveur avec acces en ecriture AD) a s'authentifier vers l'hote attaquant (MS-RPRN/PrinterBug ou equivalent -- a tester selon ce qui est disponible sur le reseau cible).
4. Relayer le NEGOTIATE/CHALLENGE/AUTHENTICATE NTLM de la victime a travers la session LDAP deja ouverte par l'attaquant, en placant le bind-as-victime et l'operation LDAP modify voulue dans le meme enregistrement SASL signe par la cle de l'attaquant. Outil de reference: "The LDAP Switcheroo" (wrapper ntlmrelayx modifie) -- github.com/grayhatkiller/switcheroo -- base sur impacket ntlmrelayx.py.
5. Utiliser l'operation modify pour poser `msDS-AllowedToActOnBehalfOfOtherIdentity` (RBCD) sur le compte machine de la victime, ou `msDS-KeyCredentialLink` (shadow credentials).
6. Exploiter la primitive obtenue: S4U2Self/S4U2Proxy depuis un compte controle vers le compte machine victime, ou PKINIT via shadow credentials, pour obtenir un TGS en tant que la victime.
7. Si la victime coercee a des privileges eleves (DC, compte avec DCSync), pivoter vers DCSync / NTDS dump -> compromission complete du domaine/foret.

## Common Mistakes

- Essayer un relais NTLM->LDAP classique (sans glisser le bind victime + modify attaquant dans le meme enregistrement signe) contre un DC qui impose LDAP signing: ca echoue, la signature seule bloque le relais naif.
- Coercer via HTTP/WebDAV en pensant que ca marchera comme pour SMB: le post indique explicitement que ce chemin ne pose pas le bon flag de signing NTLM et que le DC rejette avec operationsError. Il faut une coercition SMB.
- Oublier de verifier les KB de patch avant d'investir du temps: la fenetre d'exploitabilite est fermee sur du Server 2016-2025 patche oct/sept 2026.
- Confondre LDAP signing et LDAP channel binding: le post rappelle que si un seul des deux est force, l'attaquant peut souvent basculer vers l'autre variante de protocole (LDAP vs LDAPS/StartTLS) pour contourner celui qui manque.

## Payload Shapes

```text
# Outil de reference cite par les chercheurs (pas de commande exacte fournie dans le post)
git clone https://github.com/grayhatkiller/switcheroo
# Wrapper autour de impacket ntlmrelayx.py pour glisser bind-victime + modify-attaquant
# dans le meme enregistrement SASL signe par la cle de session de l'attaquant.

# Verification patch cote defenseur/attaquant (reco):
wmic qfe list | findstr "KB5126646"
wmic qfe list | findstr "KB5122882 KB5129235"
```

## Related Writeups

- (aucun writeup interne encore; source externe uniquement -- voir aussi knowledge/patterns/misc/intercept-webclient-coercion-ntlm-relay-rbcd.md et knowledge/patterns/misc/double-ntlm-relay-xp-dirtree-mssql-coercion.md pour des chaines relais NTLM -> LDAP/RBCD deja vues en CTF interne)

## Skill Impact

- Related skill: web-triage ou pwn-triage/AD -- ajouter un rappel: si LDAP signing est actif mais que le relais naif echoue, verifier (a) si channel binding manque (basculer LDAPS/StartTLS), (b) si le DC est patche oct/sept 2026 avant de tenter la variante mid-session reauth.
- Rule to add or update: backlog -- cette technique necessite un CVE/KB precis et un outil externe (switcheroo) non encore present dans ce repo; a promouvoir en skill seulement si rencontree en situation reelle (boot2root/attack-defense) et validee localement.

## Pertinence pour ce repo (CTF pwn / boot2root AD / attack-defense)

- **CTF pwn (binaire, hors AD):** non pertinent. Technique strictement AD/reseau Windows.
- **Boot2root AD/Windows (HTB Pro Labs, Endgame HADES/XEN, DANTE, etc.):** pertinent en theorie seulement si (a) la machine simule un DC non patche representant un etat 2016-2025 anterieur a oct/sept 2026, et (b) la box ne verrouille pas deja le relais NTLM->LDAP par channel binding. Dans la pratique CTF, la plupart des labs patchent ou simulent un etat recent -> probabilite faible mais a garder comme case a cocher si un relais LDAP classique echoue de maniere suspecte malgre un vecteur de coercition SMB fonctionnel.
- **Attack-defense (NCTF26 vendredi, phase AD potentielle):** c'est le contexte le plus pertinent. Si l'infra attack-defense tourne un DC non patche (date de build anterieure a oct 2026) avec LDAP signing actif mais relay NTLM classique bloque, cette piste merite un essai rapide avec l'outil switcheroo, en combinaison avec un vecteur de coercition SMB deja disponible dans l'arsenal (PrinterBug, etc.). Cote defense (si l'equipe doit aussi proteger son propre DC pendant le CTF): patcher/activer LDAP channel binding en plus de LDAP signing, et bloquer 389/TCP non chiffre si LDAPS suffit.
