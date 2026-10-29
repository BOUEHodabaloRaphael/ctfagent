---
doc_kind: writeup
title: "vvm (VM custom + anti-debug)"
category: rev
slug: htb-vvm-custom-vm-ptrace-bypass
created: 2026-10-29
status: solved
tags:
  - custom-vm
  - anti-debug
  - ptrace-bypass
  - opcode-reversing
  - ld-preload
  - rotl32
source: HackTheBox
target: "ELF stripped, VM maison, handlers dechiffres au runtime"
---
# vvm (VM custom + anti-debug)

## Challenge Summary

- Source: HackTheBox
- Target: ELF stripped, VM maison, handlers dechiffres au runtime
- Goal: ELF stripped implementant une VM maison protegee par ptrace(PTRACE_TRACEME) ; bytecode desassemble revele une gate de longueur puis 8 equations rotl32 a inverser.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Recon statique : PIE+canary, aucune string sensible -> logique deleguee a une VM.
2. Anti-debug detecte via strace (ptrace=-1 EPERM) ; bypass LD_PRELOAD interceptant ptrace() (retourne 0).
3. Dump runtime des handlers (zone mmap PROT_EXEC absente du fichier statique) via gdb, desassemblage individuel -> table d'opcodes reconstruite.
4. Desassemblage complet du bytecode dword par dword -> gate de longueur + bloc repete PACK puis ROTL32 puis comparaison.
5. Reverse de la gate de longueur -> n deduit.
6. Reverse de la verification : groupes d'octets, pack little-endian, rotation gauche 32 bits, comparaison a des constantes.
7. Resolution algebrique directe (rotr inverse) du mot de passe complet.
8. Validation croisee sur binaire reel (shim LD_PRELOAD) ET emulateur Python reproduisant la trace opcode par opcode.

## Key Evidence

- Table de decodage des equations (constante, shift, indices -> octets) ; "LD_PRELOAD=... ./vvm -> Correct!, $?=0" ; emulateur "OUTPUT: Correct!, FINAL STACK: []".

## Dead Ends

- n/a - chaine confirmee via double validation (binaire reel + emulateur).

## Payloads And Commands

```text
Mot de passe resolu algebriquement (pas de bruteforce) depuis les equations rotl32.
```

## Flag / Outcome

- Mot de passe/flag recupere par resolution algebrique.

## Reusable Lessons

- Reverse de VM maison generique : bypass ptrace via LD_PRELOAD, dump des handlers runtime depuis mmap RX, reconstruction de table d'opcodes par desassemblage de blobs, resolution algebrique si la verification se reduit a des operations inversibles.

## Pattern Candidates

- Nouveau pattern: custom-vm-ptrace-bypass-opcode-dump
