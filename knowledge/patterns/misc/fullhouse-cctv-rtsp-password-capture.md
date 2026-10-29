---
doc_kind: pattern
title: "Capture visuelle de credentials via un flux RTSP de surveillance interne"
category: misc
slug: fullhouse-cctv-rtsp-password-capture
created: 2026-10-29
status: active
tags:
  - rtsp
  - cctv
  - shoulder-surfing-video
  - arp-discovery
  - credential-leak
chain_summary: "Un flux de camera de surveillance interne non authentifie peut etre enregistre et rejoue pour y lire visuellement des credentials tapes a l'ecran par un administrateur."
---
# Capture visuelle de credentials via un flux RTSP de surveillance interne

## Chain Summary

- One-line chain: Un flux de camera de surveillance interne non authentifie peut etre enregistre et rejoue pour y lire visuellement des credentials tapes a l'ecran par un administrateur.
- Typical target shape: Camera de surveillance/RTSP accessible sur le reseau interne, potentiellement filtrant ICMP (invisible au ping mais presente en ARP/scan de ports).

## Preconditions

- Camera de surveillance/RTSP accessible sur le reseau interne, potentiellement filtrant ICMP (invisible au ping mais presente en ARP/scan de ports).

## Cheap Probes

- arp-scan ou nmap -sn complete par verification ARP pour detecter des hotes filtrant ICMP; nmap --script rtsp-* sur les hotes candidats.

## Telltale Evidence

- rtsp-url-brute ou un scan de port RTSP (554) confirme un flux accessible.

## Escalation Order

1. Identifier un hote exposant RTSP (souvent invisible au simple ping).
2. Bruteforcer/enumerer l'URL du flux (rtsp-url-brute).
3. Enregistrer le flux avec ffmpeg.
4. Visionner l'enregistrement pour y chercher des credentials tapes a l'ecran ou affiches.

## Common Mistakes

- Se limiter a un ping sweep pour la decouverte d'hotes alors qu'un hote filtrant ICMP mais present en ARP peut exposer des services exploitables.

## Payload Shapes

```text
ffmpeg -rtsp_transport tcp -i rtsp://<ip>/<path> -t 60 capture.mp4
```

## Related Writeups

- fullhouse-cctv-rtsp-password-capture

## Skill Impact

- Related skill: pwn-triage/recon: ajouter RTSP/CCTV comme surface a tester sur tout hote decouvert via ARP mais invisible au ping.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
