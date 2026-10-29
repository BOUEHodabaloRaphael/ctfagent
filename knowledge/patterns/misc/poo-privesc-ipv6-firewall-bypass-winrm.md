---
doc_kind: pattern
title: "Bypass de firewall IPv4 via le meme service accessible en IPv6"
category: misc
slug: poo-privesc-ipv6-firewall-bypass-winrm
created: 2026-10-29
status: active
tags:
  - ipv6-bypass
  - firewall-evasion
  - winrm
  - dual-stack
  - nmap-6
chain_summary: "Un firewall configure uniquement en regles IPv4 peut laisser le meme port ouvert sans restriction sur l'adresse IPv6 de la machine, meme si le port parait filtre en IPv4."
---
# Bypass de firewall IPv4 via le meme service accessible en IPv6

## Chain Summary

- One-line chain: Un firewall configure uniquement en regles IPv4 peut laisser le meme port ouvert sans restriction sur l'adresse IPv6 de la machine, meme si le port parait filtre en IPv4.
- Typical target shape: Hote dual-stack (IPv4+IPv6) avec un firewall dont les regles ne couvrent visiblement qu'IPv4; une adresse IPv6 de la cible est connue ou decouvrable.

## Preconditions

- Hote dual-stack (IPv4+IPv6) avec un firewall dont les regles ne couvrent visiblement qu'IPv4; une adresse IPv6 de la cible est connue ou decouvrable.

## Cheap Probes

- nmap -6 -p <port-filtre-en-v4> <adresse-ipv6> sur tout port considere ferme/filtre en IPv4.

## Telltale Evidence

- Le meme port repond ouvert en IPv6 alors qu'il etait filtre en IPv4.

## Escalation Order

1. Decouvrir l'adresse IPv6 de la cible (ipconfig local, DNS AAAA, ou deduction).
2. Rescanner en -6 les ports consideres fermes/filtres en IPv4.
3. Si ouvert, se connecter directement via IPv6 (ajout /etc/hosts si un FQDN est attendu).

## Common Mistakes

- Conclure qu'un service est inaccessible sur la base d'un seul scan IPv4 sans tester IPv6 si la cible est dual-stack.

## Payload Shapes

```text
nmap -6 -p 5985 <ipv6>; echo '<ipv6> <fqdn>' >> /etc/hosts; evil-winrm -i <fqdn> ...
```

## Related Writeups

- poo-privesc-ipv6-firewall-bypass-winrm

## Skill Impact

- Related skill: pwn-triage/recon: ajouter un rescan -6 systematique des ports filtres en IPv4 sur toute cible dual-stack.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
