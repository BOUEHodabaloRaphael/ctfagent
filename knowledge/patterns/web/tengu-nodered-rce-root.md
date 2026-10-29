---
doc_kind: pattern
title: "Tengu - Node-RED RCE non authentifie puis root Linux"
category: web
slug: tengu-nodered-rce-root
created: 2026-10-29
status: active
tags:
  - node-red
  - unauth-rce
  - aes-ctr-decrypt
  - sha256-crack
  - sudo-nopasswd
chain_summary: "Node-RED expose son editeur/API sans authentification, permettant un flux exec en webshell; les credentials chiffres des flux sont dechiffres, et un hash SHA-256 non sale d'un compte editeur est cracke."
---
# Tengu - Node-RED RCE non authentifie puis root Linux

## Chain Summary

- One-line chain: Node-RED expose son editeur/API sans authentification, permettant un flux exec en webshell; les credentials chiffres des flux sont dechiffres, et un hash SHA-256 non sale d'un compte editeur est cracke.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- uid confirmant le declenchement du flux; sortie hashcat donnant le mot de passe en clair; sudo -l affichant NOPASSWD: ALL.

## Escalation Order

1. Repere Node-RED ouvert sans auth (nmap + curl /flows).
2. Deploiement d'un flux custom avec noeud exec declenche par HTTP -> webshell.
3. grep credentialSecret dans settings.js -> cle = SHA256(secret).
4. Dechiffrement AES-256-CTR du blob credentials (IV = 16 premiers octets) -> creds.
5. Craquage hashcat -m 1400 du hash SHA-256 non sale d'un compte editeur -> mot de passe.
6. SSH + sudo -l -> NOPASSWD: ALL -> root, recuperation du keytab.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
Node-RED editeur non protege = RCE immediate via noeud exec; schema generique de dechiffrement des credentials Node-RED (cle=SHA256(settings.js secret), IV=16 premiers octets du blob, AES-256-CTR).
```

## Related Writeups

- tengu-nodered-rce-root

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
