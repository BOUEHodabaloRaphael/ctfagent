---
doc_kind: pattern
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
chain_summary: "Une capture pcapng extraite en objets HTTP tous identiques est un motif typique de beacon C2 periodique; en parallele un export d'Event Log NTLM montre une authentification WinRM locale, utile pour tracer le mouvement lateral initial."
---
# Holmes CTF 2026 Sherlock 08 - Borrowed Name / DIOGENES (forensics reseau: beacon C2 + evenements NTLM)

## Chain Summary

- One-line chain: Une capture pcapng extraite en objets HTTP tous identiques est un motif typique de beacon C2 periodique; en parallele un export d'Event Log NTLM montre une authentification WinRM locale, utile pour tracer le mouvement lateral initial.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- CONFIRME techniquement: ~98 paires d'objets HTTP identiques (JSON de statut identique) = signature de beacon; evenement NTLM EventID 4023 avec authentification WinRM d'un compte local confirme. NON RESOLU pour le flag/reponse finale du chapitre.

## Escalation Order

1. Extraire les objets HTTP de la capture pcapng (tshark/NetworkMiner).
2. Observer la repetition d'un pattern identique sur de nombreux objets = signature de beacon C2 periodique.
3. Parser l'export XML du canal NTLM operationnel -> authentification WinRM d'un compte local sur un hote donne.
4. Correler l'horodatage du beacon avec l'evenement NTLM pour situer le premier pivot.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Detecter un beacon C2 par la repetition exacte d'un pattern JSON/HTTP sur de nombreux objets extraits d'un pcap; croiser avec les logs NTLM operationnels (canal Microsoft-Windows-NTLM/Operational) pour identifier l'authentification WinRM locale servant de premier pivot.
```

## Related Writeups

- borrowedname-sherlock08-pcap-ntlm-c2-beacon

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
