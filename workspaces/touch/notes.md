---
doc_kind: workspace-notes
id: touch
title: Touch
category: misc
status: new
tags:
  []
---
# Notes

- hypotheses:
- validated findings:
- dead ends:

## Résolution (2026-10-04)

- user.txt: 212d6787ae0c82cc404e1b2de010c116
- root.txt: 88513c5e29837f01f0911eed290c009c

Chaîne complète: RDP KioskUser -> breakout kiosque Electron (Alt+Tab -> cmd.exe -> Edge via popup erreur scanner) -> lecture user.txt via file:// -> shell cmd.exe interactif -> groupe "Printer Administrators" writable sur dossier plugins Nexion Printer (process SYSTEM session 0) -> plugin .NET 8 malveillant (namespace = nom DLL requis) -> trigger C:\ProgramData\Nexion\printer-restart.trigger -> exécution SYSTEM -> root.txt.
