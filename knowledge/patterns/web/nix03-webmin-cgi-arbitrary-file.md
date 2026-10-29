---
doc_kind: pattern
title: "DANTE NIX03 - Webmin 1.900 edit_html.cgi lecture/ecriture arbitraire root"
category: web
slug: nix03-webmin-cgi-arbitrary-file
created: 2026-10-29
status: active
tags:
  - webmin
  - cgi
  - arbitrary-file-read-write
  - unauth-primitive
chain_summary: "Le CGI edit_html.cgi de Webmin 1.900 permet de lire et ecrire n'importe quel fichier via les parametres file= et save, sans authentification necessaire."
---
# DANTE NIX03 - Webmin 1.900 edit_html.cgi lecture/ecriture arbitraire root

## Chain Summary

- One-line chain: Le CGI edit_html.cgi de Webmin 1.900 permet de lire et ecrire n'importe quel fichier via les parametres file= et save, sans authentification necessaire.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Contenu du flag retourne directement via le parametre file=.

## Escalation Order

1. Webmin expose, port SSH ferme.
2. Requete /cgi-bin/edit_html.cgi?file=/root/flag.txt -> lecture directe en root.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
CGI editeur de fichier Webmin ancien = primitive lecture/ecriture fichier arbitraire en root, chercher *.cgi avec parametre file/path sur toute interface Webmin ancienne.
```

## Related Writeups

- nix03-webmin-cgi-arbitrary-file

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
