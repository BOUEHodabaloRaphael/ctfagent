---
doc_kind: writeup
title: "DANTE WS03 - RCE OMRS (EDB-49557) puis buffer overflow SERVER.EXE (JMP ESP)"
category: pwn
slug: ws03-omrs-rce-seh-bof-jmp-esp
created: 2026-10-29
status: solved
tags:
  - buffer-overflow
  - jmp-esp
  - msfvenom-badchars
  - edb-49557
  - windows-bof
source: "HTB Pro Lab DANTE"
target: "Online Marriage Registration System + SERVER.EXE"
---
# DANTE WS03 - RCE OMRS (EDB-49557) puis buffer overflow SERVER.EXE (JMP ESP)

## Challenge Summary

- Source: HTB Pro Lab DANTE
- Target: Online Marriage Registration System + SERVER.EXE
- Goal: OMRS vulnerable a une injection dans le flux d'inscription (EDB-49557) donnant RCE; un binaire sur le port 4444 avec creds en clair est exploite par un buffer overflow classique (JMP ESP).

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Script exploit public (injection flux d'inscription OMRS) -> RCE.
2. strings sur un binaire local -> creds en clair.
3. Analyse statique (Ghidra) -> offset overflow + adresse JMP ESP.
4. msfvenom shellcode avec badchars exclus.
5. Payload = padding + shellcode + adresse retour (little-endian) -> envoi au service.
6. Reverse shell SYSTEM obtenu.

## Key Evidence

- Reverse shell SYSTEM obtenu apres envoi du payload construit avec l'adresse JMP ESP en little-endian.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Buffer overflow classique padding+shellcode+retaddr, msfvenom avec badchars exclus.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Schema BOF Windows standard (analyse statique pour offset+gadget JMP ESP, msfvenom -b pour badchars, LE pour l'adresse de retour) applicable a tout service TCP exposant un parsing non borne.

## Pattern Candidates

- Voir pattern associe de meme slug.
