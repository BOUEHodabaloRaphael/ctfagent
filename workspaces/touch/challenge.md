---
doc_kind: challenge
id: touch
title: Touch
category: misc
platform: manual
platform_id: ""
url: 10.129.9.158
status: new
tags:
  []
attachments:
  []
---
# Touch

- ID: touch
- Category: misc
- Platform: manual
- Platform ID: (not provided)
- URL: 10.129.9.158
- Attachments:
  - none

## Description

Machine HTB Easy Windows. Ports ouverts: 135 (RPC), 3389 (RDP), 5985 (WinRM), 8443 (HTTPS).
Panel web "Nexion DeviceHub DH-100" sur le port 8443, identifiants admin connus: admin / NX-DH-2024-B7042.
Kiosque Electron/Vite sur localhost:5173 (local à la machine), verrouillé, avec un écran "SCAN PASSPORT".
Accès RDP confirmé fonctionnel avec KioskUser / K!0sk2026#.
Indice HTB fourni: "Jenny Crawford / KS7X2M".
Piste RDP non testée: jenny / Fl1ghtDeck2026!
Endpoint /api renvoie 403 (piste de bypass: header X-Forwarded-For: 127.0.0.1).
Endpoint /api/scan renvoie 405 sur GET (tester PUT/PATCH/DELETE).
Endpoint /api/scanner/settings à fuzzer (paramètres logPath, exportPath possibles).
Objectif: obtenir user.txt et root.txt.

## Constraints

- Mode autonome demande par l'utilisateur: executer les commandes necessaires sans demander confirmation a chaque etape
- sauf si reellement bloque (credentiel manquant
- decision ambigue).
- Approche evidence-first: privilegier verification/source/metadata avant brute force.
- Ordre de pistes suggere par l'utilisateur: 1) RDP jenny/Fl1ghtDeck2026! 2) explorer kiosque Electron (localStorage/%APPDATA%/cache Vite) pour passport number 3) bypass 403 sur /api via X-Forwarded-For 4) methodes HTTP alternatives sur /api/scan 5) impacket-rpcdump sur 135 6) fuzzing parametres /api/scanner/settings 7) recherche CVE Nexion DeviceHub DH-100.
