---
doc_kind: writeup
title: "Holmes CTF 2026 Sherlock 08 - Borrowed Name / DIOGENES (forensics reseau: beacon C2 + evenements NTLM)"
category: forensics
slug: borrowedname-sherlock08-pcap-ntlm-c2-beacon
created: 2026-10-29
status: draft
tags:
  - dfir
  - pcap-forensics
  - c2-beacon
  - ntlm-operational-log
  - winrm
  - lateral-movement
source: "Holmes CTF 2026 - Sherlock 8 Borrowed Name DIOGENES AD Incident"
target: "Capture pcapng + Event Log NTLM operationnel"
---
# Holmes CTF 2026 Sherlock 08 - Borrowed Name / DIOGENES (forensics reseau: beacon C2 + evenements NTLM)

## Challenge Summary

- Source: Holmes CTF 2026 - Sherlock 8 Borrowed Name DIOGENES AD Incident
- Target: Capture pcapng + Event Log NTLM operationnel
- Goal: Une capture pcapng extraite en objets HTTP tous identiques est un motif typique de beacon C2 periodique; en parallele un export d'Event Log NTLM montre une authentification WinRM locale, utile pour tracer le mouvement lateral initial.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Extraire les objets HTTP de la capture pcapng (tshark/NetworkMiner).
2. Observer la repetition d'un pattern identique sur de nombreux objets = signature de beacon C2 periodique.
3. Parser l'export XML du canal NTLM operationnel -> authentification WinRM d'un compte local sur un hote donne.
4. Correler l'horodatage du beacon avec l'evenement NTLM pour situer le premier pivot.

## Key Evidence

- CONFIRME techniquement: ~98 paires d'objets HTTP identiques (JSON de statut identique) = signature de beacon; evenement NTLM EventID 4023 avec authentification WinRM d'un compte local confirme. NON RESOLU pour le flag/reponse finale du chapitre.

## Dead Ends

- NON RESOLU pour la reponse finale: le beacon C2 et l'evenement NTLM sont confirmes techniquement (preuve litterale), mais aucun flag de challenge n'est etabli. Statut formel: draft.

## Payloads And Commands

```text
Export HTTP objects depuis pcapng + export XML d'Event Log Microsoft-Windows-NTLM/Operational.
```

## Flag / Outcome

- NON RESOLU pour la reponse finale: le beacon C2 et l'evenement NTLM sont confirmes techniquement (preuve litterale), mais aucun flag de challenge n'est etabli. Statut formel: draft.

## Reusable Lessons

- Detecter un beacon C2 par la repetition exacte d'un pattern JSON/HTTP sur de nombreux objets extraits d'un pcap; croiser avec les logs NTLM operationnels (canal Microsoft-Windows-NTLM/Operational) pour identifier l'authentification WinRM locale servant de premier pivot.

## Pattern Candidates

- Voir pattern associe de meme slug.
