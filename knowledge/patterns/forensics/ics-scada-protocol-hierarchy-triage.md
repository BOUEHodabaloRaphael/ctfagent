---
doc_kind: pattern
title: "Triage ICS/SCADA noye dans du trafic normal — Wireshark Protocol Hierarchy"
category: forensics
slug: ics-scada-protocol-hierarchy-triage
created: 2026-10-30
status: active
tags:
  - legacy-memory-migration
  - nctf26-prep
  - ics
chain_summary: "Statistics > Protocol Hierarchy dans Wireshark reste le reflexe n1 pour reperer un protocole industriel (Modbus/TCP, EtherNet/IP, DNP3, S7comm) meme sans le connaitre a l'avance — son volume de paquets/octets saute aux yeux dans la hierarchie."
---
# Triage ICS/SCADA noye dans du trafic normal — Wireshark Protocol Hierarchy

## Chain Summary

- One-line chain: Statistics > Protocol Hierarchy dans Wireshark reste le reflexe n1 pour reperer un protocole industriel (Modbus/TCP, EtherNet/IP, DNP3, S7comm) meme sans le connaitre a l'avance — son volume de paquets/octets saute aux yeux dans la hierarchie.

## Preconditions

- PCAP ou challenge impliquant un service/protocole industriel potentiellement noye dans du trafic web normal.

## Cheap Probes

- Statistics > Protocol Hierarchy dans Wireshark en tout premier reflexe sur un pcap suspect ICS.

## Telltale Evidence

- Une appli web legere type OpenPLC (fingerprint Server: Werkzeug/<ver> Python/<ver>) sert souvent d'interface HTTP qui traduit des requetes web en trafic Modbus reel cote PLC.

## Escalation Order

1. Statistics > Protocol Hierarchy pour reperer un protocole industriel par son volume, sans le connaitre a l'avance.
2. Statistics > Conversations trie par nombre de paquets pour isoler rapidement un attaquant qui brute-force (volume anormal vers un seul endpoint) parmi le bruit d'un operateur legitime.
3. Correler un endpoint web de monitoring/reload (ex. reload-program?table_id=, monitor-update?mb_port=) avec les logs applicatifs ET le pcap: un parametre ambigu dans les logs seuls se resout en ne gardant que la requete effectivement presente dans le trafic au moment de l'incident.
4. Chercher les creds par defaut documentes publiquement du produit identifie (ex. OpenPLC) avant de fuzzer a l'aveugle.

## Common Mistakes

- Fuzzer a l'aveugle les creds d'une interface PLC/SCADA web sans chercher d'abord les creds par defaut documentes du produit identifie.

## Payload Shapes

```text
Wireshark: Statistics > Protocol Hierarchy, puis Statistics > Conversations trie par paquets
```

## Related Writeups

- N/A

## Skill Impact

- Related skill: forensics/network: ICS/SCADA comme sous-cas de triage pcap, pertinent si un secteur NCTF26 touche a l'industriel.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
