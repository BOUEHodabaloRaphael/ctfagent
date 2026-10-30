---
doc_kind: pattern
title: "Triage memoire Volatility2/3 — quel outil pour quel plugin, ADS, volshell"
category: forensics
slug: volatility-vol2-vol3-triage-methodology
created: 2026-10-30
status: active
tags:
  - legacy-memory-migration
  - nctf26-prep
  - volatility
chain_summary: "Certains plugins Linux legacy (linux_bash, linux_enumerate_files, linux_find_file) n'existent qu'en Volatility2, d'autres challenges n'utilisent que Volatility3 — toujours verifier laquelle est attendue avant de chercher un equivalent inexistant."
---
# Triage memoire Volatility2/3 — quel outil pour quel plugin, ADS, volshell

## Chain Summary

- One-line chain: Certains plugins Linux legacy (linux_bash, linux_enumerate_files, linux_find_file) n'existent qu'en Volatility2, d'autres challenges n'utilisent que Volatility3 — toujours verifier laquelle est attendue avant de chercher un equivalent inexistant.

## Preconditions

- Dump memoire (.raw/.vmem/.elf) fourni dans un challenge forensics, profil OS inconnu a l'avance.

## Cheap Probes

- vol.py -f <dump> kdbgscan (Vol2) ou windows.info.Info (Vol3) pour identifier le profil OS avant tout autre plugin.

## Telltale Evidence

- mftparser de Volatility3 extrait aussi les flux ADS (Alternate Data Streams) directement depuis la RAM — technique sous-utilisee pour trouver des donnees cachees en ADS sans image disque complete.

## Escalation Order

1. Identifier le profil OS (Vol2: kdbgscan ; Vol3: windows.info.Info).
2. pstree/windows.pslist pour la hierarchie parent/enfant des process (repere un exec lance depuis un shell/explorer suspect).
3. filescan | grep <mot-cle> (Vol2) ou windows.filescan (Vol3) pour localiser tout fichier par nom sans connaitre l'offset.
4. windows.dumpfiles --virtaddr <offset> (Vol3) pour extraire le contenu reel d'un fichier depuis la RAM via son DataSectionObject (pas ImageSectionObject qui est pagine/different).
5. mftparser pour extraire des flux ADS caches directement depuis la RAM.
6. volshell (Vol2) pour un contexte interactif Python: ps() liste process+offset EPROCESS, cc(<offset>) change de contexte et affiche le DTB (Directory Table Base).
7. Pour Linux non-standard: linux_enumerate_files | grep <mot-cle> pour localiser un fichier par inode sans chemin connu, puis linux_find_file -i <inode> -O <sortie> pour l'extraire.

## Common Mistakes

- Chercher l'equivalent Vol3 d'un plugin Linux legacy qui n'existe qu'en Vol2 (linux_bash, linux_enumerate_files, linux_find_file, linux_ifconfig) au lieu de basculer directement sur vol.py.

## Payload Shapes

```text
vol.py -f dump.raw --profile=<profil> filescan | grep -i <keyword>
```

## Related Writeups

- N/A

## Skill Impact

- Related skill: Forensics memoire NCTF26: verifier la version Volatility attendue avant de chercher un plugin absent.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
