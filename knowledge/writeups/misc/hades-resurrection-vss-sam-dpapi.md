---
doc_kind: writeup
title: "Endgame HADES - Resurrection (Volume Shadow Copy -> SAM/SYSTEM -> DPAPI)"
category: misc
slug: hades-resurrection-vss-sam-dpapi
created: 2026-10-29
status: solved
tags:
  - volume-shadow-copy
  - dpapi
  - secretsdump
  - credential-manager
  - vss-mklink
source: "HTB Endgame HADES"
target: "Hote Windows avec snapshot VSS anterieur"
---
# Endgame HADES - Resurrection (Volume Shadow Copy -> SAM/SYSTEM -> DPAPI)

## Challenge Summary

- Source: HTB Endgame HADES
- Target: Hote Windows avec snapshot VSS anterieur
- Goal: Dump des ruches SAM/SYSTEM/SECURITY en direct, puis recuperation d'un ancien snapshot VSS pour obtenir un hash Administrator different, permettant de dechiffrer la masterkey DPAPI et d'exfiltrer des credentials.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. reg save des ruches SAM/SYSTEM/SECURITY en direct, recuperees via un partage.
2. secretsdump.py offline -> hash Administrator courant (resistant au crack).
3. Decouverte d'un point de restauration VSS anterieur.
4. mklink vers le snapshot VSS puis copie des ruches historiques.
5. secretsdump sur les ruches VSS -> hash Administrator different, trouve dans une base de hashs publique -> mot de passe en clair.
6. dpapi.py masterkey dechiffre la masterkey, puis dpapi.py credential dechiffre les blobs Credential Manager -> flag + creds.

## Key Evidence

- le hash Administrator extrait du snapshot VSS differe de celui en direct et se trouve dans une base de hashs publique.

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
montage de Volume Shadow Copy via mklink + dechiffrement DPAPI en chaine (masterkey puis credential blob).
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Un ancien snapshot VSS peut contenir un hash plus faible/different de celui en cours, qu'il faut toujours tenter de recuperer meme si le hash courant resiste au crack; la chaine DPAPI (mot de passe -> masterkey -> credential blob) permet de recuperer des secrets caches a partir d'un seul mot de passe utilisateur local.

## Pattern Candidates

- Nouveau pattern: hades-resurrection-vss-sam-dpapi
