---
doc_kind: pattern
title: "DFIR Windows complet: MFT, EVTX, suite Eric Zimmerman, WinDbg, cache RDP"
category: forensics
slug: windows-dfir-mft-evtx-zimmerman-toolkit
created: 2026-10-30
status: active
tags:
  - legacy-memory-migration
  - nctf26-prep
  - windows
chain_summary: "Image disque (.ad1/E01) montee via FTK Imager, puis suite Eric Zimmerman ciblee par artefact (ShellBags/RBCmd/PECmd/MFTExplorer/Registry Explorer) + EVTX cibles (RDP 1149, PowerShell 4104) + WinDbg pour un dump process isole."
---
# DFIR Windows complet: MFT, EVTX, suite Eric Zimmerman, WinDbg, cache RDP

## Chain Summary

- One-line chain: Image disque (.ad1/E01) montee via FTK Imager, puis suite Eric Zimmerman ciblee par artefact (ShellBags/RBCmd/PECmd/MFTExplorer/Registry Explorer) + EVTX cibles (RDP 1149, PowerShell 4104) + WinDbg pour un dump process isole.

## Preconditions

- Challenge forensics fournissant une image disque Windows (E01/.ad1/.vhd) ou un dump memoire/process isole, avec une intrusion a reconstituer.

## Cheap Probes

- mftecmd.exe -f <$MFT> --csv <dossier> --csvf result.csv (Eric Zimmerman) pour convertir le MFT brut en CSV exploitable dans Timeline Explorer.

## Telltale Evidence

- Timeline Explorer avec filtre IsSameDay([Created0x10], #YYYY-MM-DD#) ancre sur une date deja confirmee par un autre artefact (ex. horodatage RDP event 1149) isole les fichiers crees le jour de l'intrusion sans bruit.

## Escalation Order

1. EVTX a toujours verifier en premier sur un triage Windows: Microsoft-Windows-TerminalServices-RemoteConnectionManager%4Operational event 1149 (auth RDP reussie, IP source+user), Microsoft-Windows-PowerShell%4Operational event 4104 (ScriptBlock logging, commandes PowerShell en clair meme sans EDR).
2. ShellBags Explorer sur UsrClass.dat: dossiers ouverts par l'utilisateur, meme supprimes.
3. RBCmd sur $Recycle.Bin/S-1-5-21-.../$I*.ext: restaure nom original + date de suppression d'un fichier supprime.
4. PECmd sur Prefetch .pf: horodatage precis d'execution d'un binaire.
5. MFTExplorer sur $MFT: comparer SI_Created vs FN_Created pour detecter un timestomping.
6. Registry Explorer sur SYSTEM/SOFTWARE: chercher SilentProcessExit pour une persistence via GlobalFlags.
7. bmc-tools.py sur le cache bitmap RDP client (AppData\Local\Microsoft\Terminal Server Client\Cache) reconstruit le contenu visuel d'une session RDP passee en tuiles .bmp, meme sans capture video.
8. DeepBlueCLI (.\DeepBlue.ps1 <evtx>) detecte automatiquement des patterns d'attaque connus (Metasploit getsystem, services suspects) dans un EVTX System sans chercher l'EventID a la main.
9. WinDbg sur un dump process isole: !analyze -v (metadata OS), lmf/lm m <pattern> (modules charges, distingue variante legitime d'un hijack), s -a 0 L?0x<taille> "<motif>" (recherche texte dans tout l'espace adressable), !threads/!handle <critere> (compte threads/handles typés — index commence a 0).

## Common Mistakes

- Chercher un EventID a la main dans un EVTX volumineux au lieu de lancer DeepBlueCLI qui detecte automatiquement les patterns connus. Oublier de comparer SI_Created vs FN_Created sur le MFT quand un timestomping est suspecte.

## Payload Shapes

```text
mftecmd.exe -f \$MFT --csv out --csvf r.csv ; Timeline Explorer filtre IsSameDay([Created0x10], #2026-09-15#)
```

## Related Writeups

- N/A (methodologie generale, transposable a tout challenge forensics Windows avec image disque ou EVTX)

## Skill Impact

- Related skill: Candidat pour une future skill forensics-triage dediee si NCTF26 confirme avoir des epreuves forensics Windows riches en artefacts disque.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
