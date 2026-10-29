---
doc_kind: pattern
title: "Holmes CTF 2026 Sherlock 06 - Silent Passenger (firmware IVI/Carplay vehicule)"
category: forensics
slug: silentpassenger-sherlock06-ivi-firmware-extraction
created: 2026-10-29
status: draft
tags:
  - dfir
  - firmware
  - ivi-carplay
  - ext4-mount
  - automotive-forensics
  - holmes-ctf
chain_summary: "La narration pointe vers l'unite centrale (head unit) d'un vehicule dont le logiciel aurait servi un second usage cache; artefact fourni est une image firmware d'infotainment deja extraite en partitions ext4/data."
---
# Holmes CTF 2026 Sherlock 06 - Silent Passenger (firmware IVI/Carplay vehicule)

## Chain Summary

- One-line chain: La narration pointe vers l'unite centrale (head unit) d'un vehicule dont le logiciel aurait servi un second usage cache; artefact fourni est une image firmware d'infotainment deja extraite en partitions ext4/data.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- NON RESOLU: `file system.img` confirme un ext4 valide et montable; aucun resultat d'analyse texte (logs Bluetooth/GPS trouves) n'est present localement.

## Escalation Order

1. Extraire l'archive firmware -> plusieurs partitions (dont un system.img ext4 valide).
2. Monter system.img en lecture pour explorer l'arborescence de l'IVI.
3. Lire le changelog de build (contexte Carplay/Google Store, pas de contenu forensics direct).
4. Etape suivante attendue (non realisee): chercher dans system.img les logs Bluetooth/pairing, historique navigation, logs reseau caches.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Triage firmware IVI: extraire l'archive -> identifier les partitions via `file` -> monter l'ext4 en lecture -> chercher logs Bluetooth/GPS/reseau caches comme second canal de telemetrie.
```

## Related Writeups

- silentpassenger-sherlock06-ivi-firmware-extraction

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
