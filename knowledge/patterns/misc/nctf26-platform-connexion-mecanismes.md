---
doc_kind: pattern
title: "NCTF26 (arena.ctf.tg) — mecanismes de connexion aux instances, KOTH et VPN"
category: misc
slug: nctf26-platform-connexion-mecanismes
created: 2026-10-31
status: active
tags:
  - nctf26
  - platform
  - koth
  - vpn
  - wireguard
  - logistics
chain_summary: "Login via /login confirme, 3 modes de connexion aux instances (web xxxx.t.ctf.tg, service reseau TLS via ncat --ssl port 1337 obligatoire SNI, VPN WireGuard pour boot2root sur 10.100.x.y), KOTH + l'epreuve entiere ouvrent vendredi 6 novembre 19h00 (heure de Lome), fichier king confirme nomme litteralement 'king' contenant le jeton d'equipe affiche sur la page KOTH (pas un pseudo libre)."
---
# NCTF26 (arena.ctf.tg) — mecanismes de connexion aux instances, KOTH et VPN

## Chain Summary

- Verifie le 2026-10-31 via session connectee (compte ryuк): page `/connexion` ("Se connecter aux instances") documente 3 modes de connexion selon le type de challenge; page `/plugins/koth/` confirme l'ouverture de l'epreuve entiere le vendredi 6 novembre 2026 a 19h00 (heure de Lome); page `/plugins/team_instancer/vpn` confirme qu'aucune config WireGuard n'est encore generee (rien a nettoyer avant l'ouverture).

## Preconditions

- Compte NCTF26 cree et session valide (voir `src/tools/ctf/nctf26_client.py`, creds dans `src/tools/ctf/.env` non commite).

## Telltale Evidence

- Texte exact relu sur `/connexion` le 2026-10-31 (session `ryuк`):
  - Site web: `https://xxxxxxxxxxxxxxxx.t.ctf.tg/` -> ouvrir dans le navigateur.
  - Service reseau (pwn/crypto): `ncat --ssl xxxxxxxxxxxxxxxx.t.ctf.tg 1337` -- **TLS obligatoire, SNI = le nom d'instance, port TOUJOURS 1337**. Un `nc` simple sans TLS NE fonctionne PAS. Alternative sans ncat: `openssl s_client -quiet -connect <host>:1337 -servername <host>`. pwntools: `remote(host, 1337, ssl=True, sni=host)`.
  - Machine reseau equipe (boot2root/sysadmin/multi-ports): adresse privee `10.100.x.y`, uniquement joignable via le VPN WireGuard de l'equipe (page `/plugins/team_instancer/vpn`, bouton "Telecharger ma configuration" -- une config par JOUEUR, pas par equipe; retelecharger annule l'ancienne config; cle privee generee a la demande, jamais conservee cote serveur).
  - Contrainte reseau: instances **joignables uniquement depuis le Togo** -- desactiver tout VPN commercial/proxy etranger avant de tester, sinon "instance introuvable" trompeur.
- King of the Hill (`/plugins/koth/`): bandeau "LES COLLINES OUVRENT AVEC L'EPREUVE" + countdown -- confirme que **l'ensemble de l'epreuve NCTF26 (pas seulement KOTH) ouvre le vendredi 6 novembre 2026 a 19h00 (heure de Lome)**. Avant cette date: aucune colline, aucun challenge a instance disponible, juste la plateforme/login/nav.
  - Mecanique confirmee par le texte officiel (corrige l'hypothese anterieure "pseudo/nom d'equipe libre" de `koth-methodology-thm-validated.md`): le **jeton a ecrire est affiche sur la page King of the Hill elle-meme, specifique a l'equipe**, pas un pseudo choisi librement. Le fichier a ecrire est nomme **`king`** (texte officiel: "ecrivez le jeton de votre equipe ... dans son fichier « king »"), pas garanti etre `king.txt`.
  - Collines web: `http://...:port` (navigateur direct). Collines SSH: `ssh://player@...:port` -> `ssh -p <port> player@<adresse>` (user SSH fixe: **`player`**).
  - Points: tombent **a chaque tour** tant que la colline est tenue; sur boot2root, **le fichier root rapporte le double** de celui du fichier utilisateur -- donc une prise root doit ecrire/maintenir DEUX fichiers king (user ET root) si les deux existent.
  - Contrainte d'equipe: **il faut une equipe complete (4 a 5 joueurs) presents** pour marquer des points KOTH (pas un mecanisme purement technique -- a anticiper niveau logistique/presence, pas seulement outillage).

## Common Mistakes

- Supposer que `nc` (sans TLS) fonctionne sur les instances "service reseau" -- NCTF26 impose `--ssl` + SNI exact, sinon la connexion echoue silencieusement ou est refusee par le reverse-proxy.
- Tenter de tester une instance en etant hors Togo sans desactiver son VPN/proxy -- message d'erreur trompeur ("instance introuvable") qui ressemble a un bug plateforme alors que c'est un filtre geographique volontaire.
- Supposer un nom de fichier king libre (king.txt/owner.txt/flag.txt deviné) au lieu du nom confirme `king` + jeton d'equipe affiche sur la page -- a corriger dans koth_auto.sh (KING_FILENAMES) une fois la page KOTH ouverte et le jeton reel observe.

## Related Writeups

- src/tools/ctf/nctf26_client.py (client headless login/list/submit)
- knowledge/patterns/misc/koth-methodology-thm-validated.md (methodologie generale KOTH, a corriger avec le nom de fichier `king` + jeton confirme ci-dessus une fois la page reelle observee le 2026-11-06)
- src/tools/ctf/koth_auto.sh (a mettre a jour: ajouter "king" en tete de KING_FILENAMES, et prevoir la double ecriture user+root)

## Skill Impact

- Related skill: ctf-solver-profile / skill-maintainer: avant l'ouverture du 2026-11-06, verifier que `koth_auto.sh` propose bien `king` (sans extension) en premier candidat et gere la double ecriture user+root sur les boot2root.
- Rule to add or update: backlog -- mettre a jour koth_auto.sh KING_FILENAMES et ajouter un mode "ecrire les deux fichiers king (user+root) si presents" avant le 2026-11-06.
