---
doc_kind: pattern
title: "DANTE WS03 - RCE OMRS (EDB-49557) puis buffer overflow SERVER.EXE (JMP ESP)"
category: pwn
slug: ws03-omrs-rce-seh-bof-jmp-esp
created: 2026-10-29
status: active
tags:
  - buffer-overflow
  - jmp-esp
  - msfvenom-badchars
  - edb-49557
  - windows-bof
chain_summary: "OMRS vulnerable a une injection dans le flux d'inscription (EDB-49557) donnant RCE; un binaire sur le port 4444 avec creds en clair est exploite par un buffer overflow classique (JMP ESP)."
---
# DANTE WS03 - RCE OMRS (EDB-49557) puis buffer overflow SERVER.EXE (JMP ESP)

## Chain Summary

- One-line chain: OMRS vulnerable a une injection dans le flux d'inscription (EDB-49557) donnant RCE; un binaire sur le port 4444 avec creds en clair est exploite par un buffer overflow classique (JMP ESP).

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Reverse shell SYSTEM obtenu apres envoi du payload construit avec l'adresse JMP ESP en little-endian.

## Escalation Order

1. Script exploit public (injection flux d'inscription OMRS) -> RCE.
2. strings sur un binaire local -> creds en clair.
3. Analyse statique (Ghidra) -> offset overflow + adresse JMP ESP.
4. msfvenom shellcode avec badchars exclus.
5. Payload = padding + shellcode + adresse retour (little-endian) -> envoi au service.
6. Reverse shell SYSTEM obtenu.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
Schema BOF Windows standard (analyse statique pour offset+gadget JMP ESP, msfvenom -b pour badchars, LE pour l'adresse de retour) applicable a tout service TCP exposant un parsing non borne.
```

## Related Writeups

- ws03-omrs-rce-seh-bof-jmp-esp

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
