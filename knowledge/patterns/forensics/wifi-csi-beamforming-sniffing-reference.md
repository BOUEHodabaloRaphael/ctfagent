---
doc_kind: pattern
title: "Sniffing du feedback de beamforming WiFi (CSI) — reconnaissance non autorisee passive"
category: forensics
slug: wifi-csi-beamforming-sniffing-reference
created: 2026-10-30
status: active
tags:
  - legacy-memory-migration
  - nctf26-prep
  - wifi
chain_summary: "Le feedback de beamforming compresse (802.11n/ac/ax/be) est transmis EN CLAIR, hors chiffrement WPA2/WPA3 et hors protection 802.11w/PMF — un adversaire purement passif en mode moniteur peut en tirer de l'info sur l'activite humaine (frappes clavier, presence, identite/demarche, localisation)."
---
# Sniffing du feedback de beamforming WiFi (CSI) — reconnaissance non autorisee passive

## Chain Summary

- One-line chain: Le feedback de beamforming compresse (802.11n/ac/ax/be) est transmis EN CLAIR, hors chiffrement WPA2/WPA3 et hors protection 802.11w/PMF — un adversaire purement passif en mode moniteur peut en tirer de l'info sur l'activite humaine (frappes clavier, presence, identite/demarche, localisation).

## Preconditions

- Challenge hardware/RF/osint impliquant une capture WiFi 802.11ac/ax/be avec MIMO, ou une question sur la confidentialite du sensing WiFi.

## Cheap Probes

- Wireshark ne decode PAS nativement le payload Givens-angle du beamforming feedback (limitation connue depuis 2014) — utiliser un outil dedie.

## Telltale Evidence

- Attaques nommees documentees: WiKI-Eve (CCS 2023, frappes clavier 88.9% precision/touche), LeakyBeam (NDSS 2025, presence a travers les murs 82.7%/96.7% TPR/TNR a 20m), BFId (CCS 2025, identite/demarche >90% sur 197 sujets).

## Escalation Order

1. Identifier si le challenge implique une capture 802.11ac/ax/be avec MIMO (beamforming compresse present).
2. Utiliser Wi-BFI (kfoysalhaque/Wi-BFI) pour extraire le feedback de beamforming (angles/PMI) depuis une capture over-the-air — Wireshark seul ne decode pas ce payload.
3. Pour du CSI brut (pas juste le feedback compresse): Nexmon CSI (seemoo-lab/nexmon_csi) sur Raspberry Pi/ASUS RT-AC86U est le framework le plus maintenu.
4. Noter que 802.11bf (ratifie 2025) ne protege QUE son propre protocole de sensing negocie, PAS le feedback de beamforming ordinaire exploite par ces attaques — le vrai fix (802.11bi, chiffrement des trames de beamforming) reste a l'etat de brouillon non ratifie.

## Common Mistakes

- Chercher a decoder le feedback de beamforming directement dans Wireshark (ne le supporte pas nativement) au lieu d'utiliser Wi-BFI.

## Payload Shapes

```text
N/A (reconnaissance passive, carte WiFi en mode moniteur)
```

## Related Writeups

- N/A

## Skill Impact

- Related skill: Reference pour un futur secteur hardware/osint/RF de NCTF26 si un challenge touche au sensing WiFi/beamforming.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
