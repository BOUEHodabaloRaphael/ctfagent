---
doc_kind: pattern
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
chain_summary: "Vecteur d'acces initial reconstitue a partir d'un extrait USB: un raccourci .lnk se presentant comme un PDF confidentiel declenche un faux visualiseur accompagne d'un DLL sideload et d'un second binaire de persistance, tandis qu'un leurre PDF est affiche a la victime."
---
# Holmes CTF 2026 Sherlock 08 - Borrowed Name / DIOGENES (acces initial via USB/LNK + sideload DLL)

## Chain Summary

- One-line chain: Vecteur d'acces initial reconstitue a partir d'un extrait USB: un raccourci .lnk se presentant comme un PDF confidentiel declenche un faux visualiseur accompagne d'un DLL sideload et d'un second binaire de persistance, tandis qu'un leurre PDF est affiche a la victime.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- `file`/strings confirment: binaires principaux PE32+ GUI stripped; DLL sideload PE32+ stripped; horodatage du .lnk coherent avec le pretexte social-engineering. CONFIRME comme technique d'acces initial, mais pas de flag/reponse finale etablie.

## Escalation Order

1. Extraction USB -> fichier README pretextant un document confidentiel.
2. Raccourci Windows .lnk a double extension (.pdf.lnk) pointant vers l'executable reel.
3. Execution -> ouverture d'un leurre PDF pour la victime.
4. En parallele, chargement d'un DLL sideload (nom de DLL systeme legitime) par l'executable principal.
5. Un second binaire (loader/persistance probable) accompagne la chaine.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Triage artefact USB/phishing: chercher les .lnk a double extension (.pdf.lnk), verifier la cible reelle du raccourci, `file`+strings sur chaque binaire adjacent pour detecter un DLL sideloading (nom de DLL legitime cote d'un .exe inconnu).
```

## Related Writeups

- borrowedname-sherlock08-usb-lnk-dropper

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
