---
doc_kind: writeup
title: "P.O.O. Mini Pro Lab - Recon Huh?! (fuite .DS_Store sur IIS)"
category: web
slug: poo-recon-dsstore-leak
created: 2026-10-29
status: solved
tags:
  - dsstore-leak
  - iis
  - info-disclosure
  - path-enumeration
  - web-config
source: "HTB Mini Pro Lab P.O.O."
target: "IIS servant un fichier .DS_Store (mapping MIME volontaire)"
---
# P.O.O. Mini Pro Lab - Recon Huh?! (fuite .DS_Store sur IIS)

## Challenge Summary

- Source: HTB Mini Pro Lab P.O.O.
- Target: IIS servant un fichier .DS_Store (mapping MIME volontaire)
- Goal: Un fichier macOS .DS_Store servi par IIS revele l'arborescence complete du site, y compris des dossiers nommes comme des hashs MD5 contenant un fichier de connexion SQL en clair.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. nmap -p- -> seulement deux ports ouverts (firewall filtrant).
2. curl /.DS_Store renvoie 200 -> parsing avec script Python dedie, filtrage ASCII imprimable.
3. Listing racine revele plusieurs dossiers; .DS_Store existe aussi dans chaque sous-dossier.
4. Parsing du .DS_Store d'un sous-dossier -> deux noms de dossiers ressemblant a des hashs MD5.
5. IIS shortname (8.3) teste et ne fonctionne pas - abandon rapide de cette piste.
6. Deduction du nom de fichier a partir du listing + nom de dossier -> creds SQL en clair.

## Key Evidence

- curl sur le chemin devine renvoie les parametres de connexion SQL en clair.

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
parsing binaire de fichier .DS_Store + enumeration de chemin devine.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Toujours tester /.DS_Store sur un serveur web servant des fichiers statiques; s'il repond 200, parser le format proprietaire pour reconstituer l'arborescence cachee; ne pas persister sur l'IIS shortname si le premier test wildcard echoue.

## Pattern Candidates

- Nouveau pattern: poo-recon-dsstore-leak
