---
doc_kind: pattern
title: "ThunderCipher Mr. Robot - WordPress theme editor RCE puis evasion SUID nmap 3.81"
category: web
slug: mrrobot-wp-theme-rce-suid-nmap-escape
created: 2026-10-29
status: active
tags:
  - wordpress-theme-editor
  - md5-crack
  - suid-nmap-escape
  - interactive-shell-breakout
chain_summary: "robots.txt fuite un flag et une wordlist; un fichier license.txt contient des creds admin en base64; l'editeur de theme WordPress donne une RCE PHP; nmap 3.81 SUID permet une evasion interactive."
---
# ThunderCipher Mr. Robot - WordPress theme editor RCE puis evasion SUID nmap 3.81

## Chain Summary

- One-line chain: robots.txt fuite un flag et une wordlist; un fichier license.txt contient des creds admin en base64; l'editeur de theme WordPress donne une RCE PHP; nmap 3.81 SUID permet une evasion interactive.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Hash MD5 cracke donnant le mot de passe systeme; sortie nmap> !cat /root/root.txt confirmant l'evasion SUID.

## Escalation Order

1. robots.txt -> wordlist + flag direct.
2. license.txt -> creds base64 decodes.
3. Login WP -> editeur de theme -> injection PHP system($_GET['c']).
4. RCE -> lecture d'un hash MD5 systeme -> cracke (rockyou) -> mot de passe.
5. Script pty + su -> flag user.
6. nmap SUID 3.81 -> mode interactif nmap> !cat /root/root.txt -> flag root.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
Editeur de theme WordPress = RCE directe des acces admin, meme sans plugin vulnerable; tout binaire ancien SUID avec mode interactif (nmap <3.9x, vim, etc.) doit etre teste pour evasion shell via ! ou :!.
```

## Related Writeups

- mrrobot-wp-theme-rce-suid-nmap-escape

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
