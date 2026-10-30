---
doc_kind: pattern
title: "Reverse .NET obfusque — trouver le point d'entree unique du dechiffrement de chaines"
category: rev
slug: dotnet-obfuscated-string-decrypt-entrypoint
created: 2026-10-30
status: active
tags:
  - legacy-memory-migration
  - nctf26-prep
  - dotnet
chain_summary: "Quand un obfuscateur .NET renomme tout en tokens mais laisse une methode statique string->string appelee partout avec un argument Base64-like, c'est presque toujours le point d'entree du dechiffrement de chaines."
---
# Reverse .NET obfusque — trouver le point d'entree unique du dechiffrement de chaines

## Chain Summary

- One-line chain: Quand un obfuscateur .NET renomme tout en tokens mais laisse une methode statique string->string appelee partout avec un argument Base64-like, c'est presque toujours le point d'entree du dechiffrement de chaines.

## Preconditions

- Binaire .NET avec noms obfusques en tokens hexadecimaux (type 0xXXXX), decompilable via dotPeek/ILSpy.

## Cheap Probes

- Decompiler directement avec dotPeek/ILSpy (pas besoin de desobfusquer les noms un par un).

## Telltale Evidence

- Une methode statique string->string appelee a de nombreux endroits avec un argument qui ressemble a du Base64 revele l'algo entier une fois ouverte (ex: Base64+MD5-key+TripleDES-ECB).

## Escalation Order

1. Decompiler le binaire entier avec dotPeek/ILSpy.
2. Chercher une methode statique string->string appelee dans de nombreux call-sites avec un argument Base64-like.
3. Ouvrir cette methode en premier: elle revele generalement l'algo complet de dechiffrement de chaines.
4. Reimplementer un script de dechiffrement generique reutilisable sur toutes les autres chaines obfusquees du binaire.
5. Verifier VirusTotal (onglet Community, matches YARA) pour l'attribution de famille si c'est un malware — souvent plus rapide qu'une identification comportementale manuelle.

## Common Mistakes

- Essayer de desobfusquer les noms de methodes un par un au lieu de chercher directement le point d'entree unique du dechiffrement de chaines.

## Payload Shapes

```text
dotPeek/ILSpy -> chercher 'public static string <nom_obfusque>(string s)' appele partout
```

## Related Writeups

- N/A

## Skill Impact

- Related skill: rev-triage (.NET): ajouter la recherche du point d'entree de dechiffrement de chaines comme premiere etape sur tout binaire .NET obfusque.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
