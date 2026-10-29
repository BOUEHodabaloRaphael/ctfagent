---
doc_kind: pattern
title: "DANTE NIX05 - buffer overflow binaire SUID readfile"
category: pwn
slug: nix05-suid-readfile-stack-bof
created: 2026-10-29
status: active
tags:
  - suid-binary
  - stack-overflow
  - env-return-address
  - pwntools
  - local-privesc
chain_summary: "Un binaire SUID root est vulnerable a un debordement de pile classique (adresse de retour injectee via une variable d'environnement) donnant un shell root."
---
# DANTE NIX05 - buffer overflow binaire SUID readfile

## Chain Summary

- One-line chain: Un binaire SUID root est vulnerable a un debordement de pile classique (adresse de retour injectee via une variable d'environnement) donnant un shell root.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Shell obtenu avec UID root apres execution du payload contre le binaire SUID.

## Escalation Order

1. Creds -> acces initial.
2. sudo -l -> binaire SUID root custom.
3. GDB/PEDA avec ASLR off, determination offset et taille shellcode.
4. Adresse de retour obtenue depuis env, injectee via variable d'environnement.
5. Payload = padding + shellcode + padding + stack_address -> shell root SUID.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
Technique de retour vers adresse stockee dans l'environnement (plutot que shellcode inline) utile quand l'espace de payload est limite; toujours checker sudo -l pour binaires SUID custom avant de chercher un BOF reseau.
```

## Related Writeups

- nix05-suid-readfile-stack-bof

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
