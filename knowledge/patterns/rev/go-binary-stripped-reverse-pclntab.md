---
doc_kind: pattern
title: "Reverse d'un binaire Go stripped — recouvrement de symboles via pclntab"
category: rev
slug: go-binary-stripped-reverse-pclntab
created: 2026-10-30
status: active
tags:
  - legacy-memory-migration
  - nctf26-prep
  - go
chain_summary: "GoResym/go_parser recouvre les noms de packages/fonctions depuis la pclntab d'un binaire Go strippe, meme sans symboles; les strings .rodata type chemin de module identifient le module root."
---
# Reverse d'un binaire Go stripped — recouvrement de symboles via pclntab

## Chain Summary

- One-line chain: GoResym/go_parser recouvre les noms de packages/fonctions depuis la pclntab d'un binaire Go strippe, meme sans symboles; les strings .rodata type chemin de module identifient le module root.

## Preconditions

- Binaire Go strippe (pas de symboles), challenge rev/forensics demandant de reconstituer la logique du programme.

## Cheap Probes

- Chercher les strings .rodata de type chemin de package (<module>/cmd/...) pour identifier le module root du binaire.

## Telltale Evidence

- Les immediates passes a time.Sleep/runtime.time_Sleep sont directement lisibles en desassemblage (en nanosecondes), sans besoin de symboles.

## Escalation Order

1. Utiliser GoResym ou go_parser pour recouvrer les noms de packages/fonctions depuis la pclntab.
2. Chercher les chemins de module dans .rodata pour confirmer le module root.
3. Pour une valeur de timeout/delai, lire directement l'immediate passe a time.Sleep en desassemblage.
4. net/textproto.CanonicalMIMEHeaderKey transforme un literal lowercase en header HTTP canonique (1ere lettre + lettre apres tiret en majuscule) — retrouver la valeur brute et appliquer la regle a la main si le symbole est absent.

## Common Mistakes

- Abandonner le reverse d'un binaire Go strippe en pensant qu'aucun symbole n'est recuperable, sans tester GoResym sur la pclntab.

## Payload Shapes

```text
goresym -pclntab <binaire> (ou go_parser equivalent) pour lister packages/fonctions recouvres
```

## Related Writeups

- N/A

## Skill Impact

- Related skill: rev-triage: ajouter GoResym comme premiere etape sur tout binaire Go strippe.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
