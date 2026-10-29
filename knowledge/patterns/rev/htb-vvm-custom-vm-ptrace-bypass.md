---
doc_kind: pattern
title: "Reverse de VM maison protegee par ptrace: bypass + dump runtime + resolution algebrique"
category: rev
slug: htb-vvm-custom-vm-ptrace-bypass
created: 2026-10-29
status: active
tags:
  - custom-vm
  - anti-debug
  - ptrace-bypass
  - opcode-reversing
  - ld-preload
  - rotl32
chain_summary: "VM custom avec handlers dechiffres/mappes en RX au runtime et ptrace anti-debug: bypass ptrace via LD_PRELOAD, dump les handlers depuis la memoire du process, reconstruire la table d'opcodes, puis resoudre algebriquement si la verification est inversible."
---
# Reverse de VM maison protegee par ptrace: bypass + dump runtime + resolution algebrique

## Chain Summary

- One-line chain: VM custom avec handlers dechiffres/mappes en RX au runtime et ptrace anti-debug: bypass ptrace via LD_PRELOAD, dump les handlers depuis la memoire du process, reconstruire la table d'opcodes, puis resoudre algebriquement si la verification est inversible.
- Typical target shape: Binaire implementant sa propre VM/bytecode interprete; ptrace(PTRACE_TRACEME) ou equivalent empeche gdb/strace classique; pas de strings exploitables car logique deleguee a la VM.

## Preconditions

- Binaire implementant sa propre VM/bytecode interprete; ptrace(PTRACE_TRACEME) ou equivalent empeche gdb/strace classique; pas de strings exploitables car logique deleguee a la VM.

## Cheap Probes

- strace le binaire pour confirmer l'appel ptrace() qui echoue volontairement (anti-debug); chercher des zones mmap PROT_EXEC qui n'existent pas dans le fichier statique (handlers dechiffres au runtime).

## Telltale Evidence

- ptrace() retourne -1/EPERM en environnement non trace; une region memoire executable supplementaire apparait seulement a l'execution.

## Escalation Order

1. Ecrire un shim LD_PRELOAD qui intercepte ptrace() et retourne 0/succes pour permettre le debug.
2. Sous debugger desormais possible, dumper les zones mmap PROT_EXEC runtime (handlers de la VM).
3. Desassembler chaque handler individuellement pour reconstruire la table d'opcodes.
4. Desassembler le bytecode complet avec cette table pour identifier la structure de verification (gates, equations).
5. Si la verification se reduit a des operations inversibles (rotations, XOR, pack/unpack), resoudre algebriquement plutot que bruteforcer.
6. Valider la solution sur le binaire reel (via le shim) ET dans un emulateur maison reproduisant la trace, pour etre sur de ne pas avoir un faux-positif.

## Common Mistakes

- Abandonner un binaire anti-debug sans essayer un bypass LD_PRELOAD simple avant de chercher des techniques plus lourdes.

## Payload Shapes

```text
LD_PRELOAD shim: long ptrace(...) { return 0; }
```

## Related Writeups

- htb-vvm-custom-vm-ptrace-bypass

## Skill Impact

- Related skill: rev-triage: ajouter 'ptrace EPERM volontaire -> bypass LD_PRELOAD immediat' comme premiere reponse a l'anti-debug Linux.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
