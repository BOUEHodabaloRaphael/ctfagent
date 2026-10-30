---
doc_kind: pattern
title: "Abus de trust AD intra-foret: golden ticket SID-History AES256 + contournement EFS"
category: misc
slug: ad-trust-sidhistory-golden-ticket-aes256-efs-bypass
created: 2026-10-30
status: active
tags:
  - legacy-memory-migration
  - nctf26-prep
  - ad
chain_summary: "Un golden ticket force avec cle RC4 echoue (KDC_ERR_TGT_REVOKED) dans un environnement durci exigeant AES256; EFS n'est jamais dechiffrable via acces reseau/SYSTEM meme en Domain Admin, il faut une authentification interactive reelle (reset mdp + RDP automatise)."
---
# Abus de trust AD intra-foret: golden ticket SID-History AES256 + contournement EFS

## Chain Summary

- One-line chain: Un golden ticket force avec cle RC4 echoue (KDC_ERR_TGT_REVOKED) dans un environnement durci exigeant AES256; EFS n'est jamais dechiffrable via acces reseau/SYSTEM meme en Domain Admin, il faut une authentification interactive reelle (reset mdp + RDP automatise).

## Preconditions

- Domaine enfant compromis (krbtgt dumpe), domaine racine de la foret (ou tout domaine en confiance non filtree) accessible seulement via cette confiance.

## Cheap Probes

- Get-ADTrust pour verifier SIDFilteringQuarantined: False avant de tenter un SID-History golden ticket.

## Telltale Evidence

- KDC_ERR_TGT_REVOKED sur un golden ticket forge avec -nthash (RC4) alors que le domaine exige AES256 pour Kerberos — pas forcement un hardening anti-golden-ticket exotique.

## Escalation Order

1. Si KDC_ERR_TGT_REVOKED apparait sur un golden ticket SID-History, verifier EN PREMIER le type de cle utilisee pour signer avant de supposer un hardening anti-golden-ticket exotique.
2. Refaire avec -aesKey <aes256_hmac du krbtgt> au lieu de -nthash/RC4 resout generalement l'erreur immediatement.
3. Preferer un golden ticket CLASSIQUE du domaine enfant (signe avec son propre krbtgt) + -extra-sid <SID_racine>-519,-500, plus simple et fiable qu'un ticket inter-royaume signe avec la cle de confiance elle-meme (restrictions PAC).
4. Si impacket echoue de facon non evidente apres un golden ticket SID-History normalement valide (wmiexec/psexec/smbclient.py -k), basculer sur les outils MIT Kerberos natifs (kinit/kvno) avec un /etc/krb5.conf declarant les deux royaumes et leurs KDC — le ccache MIT resultant reste utilisable par impacket ensuite.
5. Piege smbclient.py -k: le parametre domain doit etre le royaume SOURCE du ticket (domaine enfant), pas la cible — sinon STATUS_MORE_PROCESSING_REQUIRED trompeur (crealm incorrect dans l'Authenticator).
6. Si un fichier cible est EFS-chiffre: aucun acces reseau/SYSTEM (meme Domain/Enterprise Admin) ne peut jamais le dechiffrer — reinitialiser silencieusement le mot de passe reel du compte proprietaire via l'acces SYSTEM deja en main, puis etablir une vraie session RDP interactive automatisee (Xvfb + xfreerdp3 + xdotool pour piloter clavier/souris headless) et rediriger la lecture du fichier EFS vers un fichier NON chiffre dans cette session.

## Common Mistakes

- S'acharner sur un acces reseau/SYSTEM pour lire un fichier EFS, qui ne se dechiffre QUE lors d'une authentification interactive reelle avec le vrai mot de passe. Signer un ticket avec RC4 dans un environnement moderne sans tester AES256 en premier.

## Payload Shapes

```text
ticketer.py -aesKey <aes256> -domain-sid <SID_enfant> -extra-sid <SID_racine>-519,-500 Administrator
```

## Related Writeups

- N/A

## Skill Impact

- Related skill: pwn-triage/AD: ajouter le fix RC4->AES256 pour golden ticket, et le workflow EFS reset-mdp+RDP-automatise comme techniques AD avancees standards.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
