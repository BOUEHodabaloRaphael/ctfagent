---
doc_kind: writeup
title: "DANTE NIX05 - buffer overflow binaire SUID readfile"
category: pwn
slug: nix05-suid-readfile-stack-bof
created: 2026-10-29
status: solved
tags:
  - suid-binary
  - stack-overflow
  - env-return-address
  - pwntools
  - local-privesc
source: "HTB Pro Lab DANTE"
target: "Binaire SUID root custom"
---
# DANTE NIX05 - buffer overflow binaire SUID readfile

## Challenge Summary

- Source: HTB Pro Lab DANTE
- Target: Binaire SUID root custom
- Goal: Un binaire SUID root est vulnerable a un debordement de pile classique (adresse de retour injectee via une variable d'environnement) donnant un shell root.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Creds -> acces initial.
2. sudo -l -> binaire SUID root custom.
3. GDB/PEDA avec ASLR off, determination offset et taille shellcode.
4. Adresse de retour obtenue depuis env, injectee via variable d'environnement.
5. Payload = padding + shellcode + padding + stack_address -> shell root SUID.

## Key Evidence

- Shell obtenu avec UID root apres execution du payload contre le binaire SUID.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Buffer overflow via pwntools, adresse de retour fournie par variable d'environnement.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Technique de retour vers adresse stockee dans l'environnement (plutot que shellcode inline) utile quand l'espace de payload est limite; toujours checker sudo -l pour binaires SUID custom avant de chercher un BOF reseau.

## Pattern Candidates

- Voir pattern associe de meme slug.
