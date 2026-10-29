---
doc_kind: writeup
title: "Holmes CTF 2026 Sherlock 08 - Borrowed Name / DIOGENES (acces initial via USB/LNK + sideload DLL)"
category: forensics
slug: borrowedname-sherlock08-usb-lnk-dropper
created: 2026-10-29
status: draft
tags:
  - dfir
  - initial-access
  - lnk-dropper
  - dll-sideloading
  - usb-phishing
  - holmes-ctf
source: "Holmes CTF 2026 - Sherlock 8 Borrowed Name DIOGENES AD Incident"
target: "Extrait USB avec raccourci piege"
---
# Holmes CTF 2026 Sherlock 08 - Borrowed Name / DIOGENES (acces initial via USB/LNK + sideload DLL)

## Challenge Summary

- Source: Holmes CTF 2026 - Sherlock 8 Borrowed Name DIOGENES AD Incident
- Target: Extrait USB avec raccourci piege
- Goal: Vecteur d'acces initial reconstitue a partir d'un extrait USB: un raccourci .lnk se presentant comme un PDF confidentiel declenche un faux visualiseur accompagne d'un DLL sideload et d'un second binaire de persistance, tandis qu'un leurre PDF est affiche a la victime.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Extraction USB -> fichier README pretextant un document confidentiel.
2. Raccourci Windows .lnk a double extension (.pdf.lnk) pointant vers l'executable reel.
3. Execution -> ouverture d'un leurre PDF pour la victime.
4. En parallele, chargement d'un DLL sideload (nom de DLL systeme legitime) par l'executable principal.
5. Un second binaire (loader/persistance probable) accompagne la chaine.

## Key Evidence

- `file`/strings confirment: binaires principaux PE32+ GUI stripped; DLL sideload PE32+ stripped; horodatage du .lnk coherent avec le pretexte social-engineering. CONFIRME comme technique d'acces initial, mais pas de flag/reponse finale etablie.

## Dead Ends

- NON RESOLU pour le flag final: le mecanisme d'acces initial est identifie et confirme techniquement (preuve litterale via file/strings), mais aucune reponse de challenge n'est etablie. Statut formel: draft.

## Payloads And Commands

```text
Lot USB phishing: .lnk leurre + loader GUI + DLL de sideload + leurre PDF.
```

## Flag / Outcome

- NON RESOLU pour le flag final: le mecanisme d'acces initial est identifie et confirme techniquement (preuve litterale via file/strings), mais aucune reponse de challenge n'est etablie. Statut formel: draft.

## Reusable Lessons

- Triage artefact USB/phishing: chercher les .lnk a double extension (.pdf.lnk), verifier la cible reelle du raccourci, `file`+strings sur chaque binaire adjacent pour detecter un DLL sideloading (nom de DLL legitime cote d'un .exe inconnu).

## Pattern Candidates

- Voir pattern associe de meme slug.
