---
doc_kind: pattern
title: "Methodologie pivot SIEM (Wazuh/Kibana) pour investigation DFIR web"
category: forensics
slug: btf-cwl-dfir-soc-exercises
created: 2026-10-29
status: active
tags:
  - dfir
  - siem
  - wazuh
  - volatility3
  - pcap
  - soc-quiz
chain_summary: "Decoder+index Wazuh -> filtre data.url/code HTTP par signature d'attaque -> pivot vers data.srcip -> correlation PCAP/Volatility pour confirmer la chaine complete."
---
# Methodologie pivot SIEM (Wazuh/Kibana) pour investigation DFIR web

## Chain Summary

- One-line chain: Decoder+index Wazuh -> filtre data.url/code HTTP par signature d'attaque -> pivot vers data.srcip -> correlation PCAP/Volatility pour confirmer la chaine complete.
- Typical target shape: Investigation DFIR/SOC avec acces a des logs indexes (Wazuh/Kibana/ELK) et eventuellement PCAP/memory dump complementaires.

## Preconditions

- Investigation DFIR/SOC avec acces a des logs indexes (Wazuh/Kibana/ELK) et eventuellement PCAP/memory dump complementaires.

## Cheap Probes

- Chercher dans Kibana Discover les 'Top values' d'un champ URL/path filtre par code HTTP de succes (200) pour reperer des signatures d'attaque connues (UNION SELECT, onerror=, etc.).

## Telltale Evidence

- Un champ 'count' affiche dans une vue filtree Kibana peut etre un sous-total de cette vue, pas un total brut - toujours verifier le filtre actif avant de repondre a un quiz/rapport base sur ce chiffre.

## Escalation Order

1. Identifier le decoder/index pertinent pour le type de log (web-accesslog, auth, etc.).
2. Filtrer par pattern d'attaque connu dans le champ URL/body + code de reponse de succes.
3. Pivoter sur l'IP source pour tracer tous les evenements de ce meme acteur.
4. Correler avec PCAP (Wireshark) et/ou memory dump (Volatility3) pour confirmer la chaine complete (upload -> callback -> C2).

## Common Mistakes

- Repondre a un chiffre de quiz base sur un filtre de vue specifique en le confondant avec le total brut non filtre.

## Payload Shapes

```text
Kibana Discover: data.url: *UNION* AND data.response:200
```

## Related Writeups

- btf-cwl-dfir-soc-exercises

## Skill Impact

- Related skill: Pas de skill forensics-triage dediee actuellement; backlog candidate si un pattern DFIR recurrent se confirme sur un vrai challenge (celui-ci est un walkthrough guide, pas un live solve).
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
