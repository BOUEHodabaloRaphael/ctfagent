---
doc_kind: writeup
title: "Tengu - Node-RED RCE non authentifie puis root Linux"
category: web
slug: tengu-nodered-rce-root
created: 2026-10-29
status: solved
tags:
  - node-red
  - unauth-rce
  - aes-ctr-decrypt
  - sha256-crack
  - sudo-nopasswd
source: "HTB Pro Lab Tengu"
target: "Node-RED 3.1.6 sans auth"
---
# Tengu - Node-RED RCE non authentifie puis root Linux

## Challenge Summary

- Source: HTB Pro Lab Tengu
- Target: Node-RED 3.1.6 sans auth
- Goal: Node-RED expose son editeur/API sans authentification, permettant un flux exec en webshell; les credentials chiffres des flux sont dechiffres, et un hash SHA-256 non sale d'un compte editeur est cracke.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Repere Node-RED ouvert sans auth (nmap + curl /flows).
2. Deploiement d'un flux custom avec noeud exec declenche par HTTP -> webshell.
3. grep credentialSecret dans settings.js -> cle = SHA256(secret).
4. Dechiffrement AES-256-CTR du blob credentials (IV = 16 premiers octets) -> creds.
5. Craquage hashcat -m 1400 du hash SHA-256 non sale d'un compte editeur -> mot de passe.
6. SSH + sudo -l -> NOPASSWD: ALL -> root, recuperation du keytab.

## Key Evidence

- uid confirmant le declenchement du flux; sortie hashcat donnant le mot de passe en clair; sudo -l affichant NOPASSWD: ALL.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Flux JSON Node-RED avec noeud exec + noeud HTTP in; script Python AES-256-CTR pour dechiffrement.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Node-RED editeur non protege = RCE immediate via noeud exec; schema generique de dechiffrement des credentials Node-RED (cle=SHA256(settings.js secret), IV=16 premiers octets du blob, AES-256-CTR).

## Pattern Candidates

- Voir pattern associe de meme slug.
