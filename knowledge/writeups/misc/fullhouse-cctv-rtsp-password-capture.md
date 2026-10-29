---
doc_kind: writeup
title: "FullHouse - Quelqu'un observe (CCTV RTSP + mot de passe root tape a l'ecran)"
category: misc
slug: fullhouse-cctv-rtsp-password-capture
created: 2026-10-29
status: solved
tags:
  - rtsp
  - cctv
  - shoulder-surfing-video
  - arp-discovery
  - credential-leak
source: "HTB Pro Lab FullHouse"
target: "Camera de surveillance RTSP non authentifiee"
---
# FullHouse - Quelqu'un observe (CCTV RTSP + mot de passe root tape a l'ecran)

## Challenge Summary

- Source: HTB Pro Lab FullHouse
- Target: Camera de surveillance RTSP non authentifiee
- Goal: Une camera de surveillance interne diffuse en RTSP non authentifie; l'enregistrement de la video capture visuellement le mot de passe root tape par un administrateur a l'ecran.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Ping sweep + arp depuis un shell existant revele un hote invisible au ping mais present en ARP.
2. nmap --script rtsp-* decouvre l'URL du flux RTSP.
3. ffmpeg -rtsp_transport tcp enregistre le flux en fichier video.
4. Lecture de la video -> mot de passe root visible a l'ecran lors de la frappe.
5. SSH root avec le mot de passe observe -> flag.

## Key Evidence

- rtsp-url-brute du script nmap renvoie explicitement l'URL valide du flux.

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
capture video RTSP (pas de payload offensif, OSINT visuel).
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Un host present en ARP mais ne repondant pas au ping peut filtrer ICMP tout en exposant des services; enregistrer puis rejouer un flux de surveillance interne pour y detecter des credentials tapes a l'ecran est low-tech mais efficace.

## Pattern Candidates

- Nouveau pattern: fullhouse-cctv-rtsp-password-capture
