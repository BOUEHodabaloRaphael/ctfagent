---
doc_kind: pattern
title: "Loader natif hebergeant du code .NET via COM Interop — pattern de reverse"
category: rev
slug: holmes2025-com-interop-dotnet-native-reverse
created: 2026-10-30
status: active
tags:
  - legacy-memory-migration
  - nctf26-prep
  - holmes2025
chain_summary: "Un loader C++ natif qui verifie clr.dll charge, genere une cle XOR, dechiffre un domaine killswitch et se propage par SMB est un pattern COM Interop (CoCreateInstance + vtable + call [rax+offset]) a reconnaitre par la signature des appels."
---
# Loader natif hebergeant du code .NET via COM Interop — pattern de reverse

## Chain Summary

- One-line chain: Un loader C++ natif qui verifie clr.dll charge, genere une cle XOR, dechiffre un domaine killswitch et se propage par SMB est un pattern COM Interop (CoCreateInstance + vtable + call [rax+offset]) a reconnaitre par la signature des appels.

## Preconditions

- Binaire natif (.exe) suspecte d'heberger du code .NET managee via COM Callable Wrapper.

## Cheap Probes

- Chercher CoInitialize (ole32.dll) + CoCreateInstance (GUID du composant .NET) dans les imports/desassemblage.

## Telltale Evidence

- Chaque appel vers une methode managee depuis le code natif passe par un offset de vtable fixe (ex. call [rax+68h] pour une methode, [rax+58h] pour une autre) — ces offsets correspondent a l'ordre de declaration des methodes dans l'interface COM-visible .NET.

## Escalation Order

1. Identifier CoInitialize/CoCreateInstance et le GUID du composant instancie.
2. Reconnaitre la technique: COM Interop (COM Callable Wrapper) exposant du code .NET managee a un appelant natif C++.
3. Pour chaque call [rax+offset] identifie, noter l'offset — ils correspondent a l'ordre des methodes de l'interface .NET [ComVisible].
4. Si possible, recompiler une DLL .NET equivalente ([ComVisible], [Guid(...)], meme structure de classe) et l'enregistrer via regasm /codebase pour valider dynamiquement le comportement sans avoir le vrai binaire original.
5. Extraire la cle XOR/le mecanisme de chiffrement du domaine killswitch generalement derive par des constantes simples (multiplicateur+addition) visibles dans le desassemblage natif.

## Common Mistakes

- Essayer de reverser toute la logique en natif sans reconnaitre le pattern COM Interop, qui explique directement pourquoi certains appels semblent 'sauter' vers du code non visible statiquement (il est dans l'assembly .NET hebergee).

## Payload Shapes

```text
N/A (reconnaissance de pattern, pas de payload)
```

## Related Writeups

- N/A

## Skill Impact

- Related skill: rev-triage: ajouter 'loader natif + CoCreateInstance + call [rax+offset]' comme signature de reconnaissance COM Interop .NET/natif.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
