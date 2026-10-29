---
doc_kind: writeup
title: "DANTE NIX03 - Webmin 1.900 edit_html.cgi lecture/ecriture arbitraire root"
category: web
slug: nix03-webmin-cgi-arbitrary-file
created: 2026-10-29
status: solved
tags:
  - webmin
  - cgi
  - arbitrary-file-read-write
  - unauth-primitive
source: "HTB Pro Lab DANTE"
target: "Webmin 1.900"
---
# DANTE NIX03 - Webmin 1.900 edit_html.cgi lecture/ecriture arbitraire root

## Challenge Summary

- Source: HTB Pro Lab DANTE
- Target: Webmin 1.900
- Goal: Le CGI edit_html.cgi de Webmin 1.900 permet de lire et ecrire n'importe quel fichier via les parametres file= et save, sans authentification necessaire.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Webmin expose, port SSH ferme.
2. Requete /cgi-bin/edit_html.cgi?file=/root/flag.txt -> lecture directe en root.

## Key Evidence

- Contenu du flag retourne directement via le parametre file=.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Requete GET CGI avec parametre file= (et save pour ecriture).
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- CGI editeur de fichier Webmin ancien = primitive lecture/ecriture fichier arbitraire en root, chercher *.cgi avec parametre file/path sur toute interface Webmin ancienne.

## Pattern Candidates

- Voir pattern associe de meme slug.
