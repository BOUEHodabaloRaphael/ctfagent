---
doc_kind: pattern
title: "Hash Administrator historique via Volume Shadow Copy quand le hash courant resiste au crack"
category: misc
slug: hades-resurrection-vss-sam-dpapi
created: 2026-10-29
status: active
tags:
  - volume-shadow-copy
  - dpapi
  - secretsdump
  - credential-manager
  - vss-mklink
chain_summary: "Un snapshot Volume Shadow Copy anterieur peut contenir une version historique du hash Administrator, potentiellement plus faible/connue, differente du hash courant qui resiste au crack."
---
# Hash Administrator historique via Volume Shadow Copy quand le hash courant resiste au crack

## Chain Summary

- One-line chain: Un snapshot Volume Shadow Copy anterieur peut contenir une version historique du hash Administrator, potentiellement plus faible/connue, differente du hash courant qui resiste au crack.
- Typical target shape: Acces admin/SYSTEM a une machine Windows avec au moins un point de restauration VSS existant; le hash Administrator courant resiste au crack.

## Preconditions

- Acces admin/SYSTEM a une machine Windows avec au moins un point de restauration VSS existant; le hash Administrator courant resiste au crack.

## Cheap Probes

- vssadmin list shadows (ou equivalent) pour verifier l'existence de snapshots anterieurs.

## Telltale Evidence

- Au moins un snapshot VSS existe, anterieur a la date courante.

## Escalation Order

1. Dumper SAM/SYSTEM en direct, tenter le crack (souvent infructueux sur un hash fort).
2. Lister les snapshots VSS disponibles.
3. Monter un lien symbolique vers le snapshot (mklink /d vers \?\GLOBALROOT\...\HarddiskVolumeShadowCopyN\).
4. Copier et dumper les ruches SAM/SYSTEM historiques depuis ce snapshot.
5. Comparer le hash obtenu au hash courant; s'il differe, le tester contre des bases de hashs publiques/wordlists.

## Common Mistakes

- Abandonner apres l'echec de crack du hash Administrator courant sans verifier l'existence de snapshots VSS anterieurs potentiellement plus faibles.

## Payload Shapes

```text
mklink /d C:\vss \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\  puis  reg save hklm\sam C:\vss\...\sam.hiv
```

## Related Writeups

- hades-resurrection-vss-sam-dpapi

## Skill Impact

- Related skill: pwn-triage (Windows credential extraction): ajouter la verification systematique des snapshots VSS comme source de hash historique quand le hash courant resiste.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
