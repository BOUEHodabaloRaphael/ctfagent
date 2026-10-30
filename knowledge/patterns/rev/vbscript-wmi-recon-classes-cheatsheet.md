---
doc_kind: pattern
title: "Analyse VBScript/WMI de recon — cheatsheet classes COM/WMI"
category: rev
slug: vbscript-wmi-recon-classes-cheatsheet
created: 2026-10-30
status: active
tags:
  - legacy-memory-migration
  - nctf26-prep
  - vbscript
chain_summary: "Un malware VBScript de recon se lit comme une checklist: chaque Function/Sub correspond typiquement a UNE classe WMI ou UN objet COM — identifier la classe/methode suffit a repondre a la plupart des questions sans tracer l'execution."
---
# Analyse VBScript/WMI de recon — cheatsheet classes COM/WMI

## Chain Summary

- One-line chain: Un malware VBScript de recon se lit comme une checklist: chaque Function/Sub correspond typiquement a UNE classe WMI ou UN objet COM — identifier la classe/methode suffit a repondre a la plupart des questions sans tracer l'execution.

## Preconditions

- Sample VBScript/WMI de recon a analyser (challenge forensics/malware-analysis).

## Cheap Probes

- Pour chaque Function/Sub du script, identifier quelle classe WMI ou quel objet COM est instancie (Shell.Application, Word.Application, Microsoft.XMLHTTP, StdRegProv).

## Telltale Evidence

- Classes WMI de recon les plus frequentes: Win32_ComputerSystem/Win32_OperatingSystem/Win32_Processor (fingerprint host, namespace root\cimv2), AntiVirusProduct (namespace root\SecurityCenter2, PAS root\cimv2), Win32_Process (process listing, root\cimv2).

## Escalation Order

1. Parcourir chaque Function/Sub et identifier la classe WMI/objet COM utilise.
2. StdRegProv (namespace root\default) = API WMI standard pour lire/ecrire le registre sans passer par WScript.Shell.RegWrite — reconnaitre ses methodes (GetStringValue/SetStringValue/SetDwordValue) et sa constante hk (&H80000001=HKCU, &H80000002=HKLM).
3. Repondre aux questions du challenge directement a partir de la classe/methode identifiee, sans tracer dynamiquement l'execution.

## Common Mistakes

- Essayer de tracer dynamiquement l'execution d'un script VBScript de recon au lieu de simplement identifier statiquement chaque classe COM/WMI utilisee.

## Payload Shapes

```text
N/A (lecture statique, pas de payload)
```

## Related Writeups

- N/A

## Skill Impact

- Related skill: rev-triage/forensics: ajouter cette cheatsheet de classes WMI comme reference rapide pour tout malware VBScript.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
