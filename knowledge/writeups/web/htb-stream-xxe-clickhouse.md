---
doc_kind: writeup
title: "HTB Stream (htb-airport.htb)"
category: web
slug: htb-stream-xxe-clickhouse
created: 2026-10-29
status: solved
tags:
  - web
  - xxe
  - clickhouse
  - actuator-heapdump
  - credential-reuse
  - rce-root
source: HackTheBox
target: "Spring Boot actuator + ClickHouse + Kafka pipeline"
---
# HTB Stream (htb-airport.htb)

## Challenge Summary

- Source: HackTheBox
- Target: Spring Boot actuator + ClickHouse + Kafka pipeline
- Goal: Fuite credentials ClickHouse via heap dump Spring Boot actuator, XXE aveugle in-band exfiltre via pipeline Kafka->ClickHouse, RCE root via capture de mot de passe en CLI (/proc/*/cmdline) + fonction file() de ClickHouse.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Fuzzing vhost -> api.* (Spring Boot) et db.* (ClickHouse).
2. /actuator/heapdump sans auth -> credentials svc_events reutilises par ClickHouse.
3. Cartographie pipeline Kafka->ClickHouse -> table flightleg_json lisible = canal d'exfiltration.
4. XXE aveugle (lxml load_dtd+resolve_entities) sur /feeds/aidx, OOB impossible -> lecture 'en bande' via le contenu serialise stocke en DB.
5. Lecture /etc/passwd puis server.properties Kafka -> credentials SASL svc-infra reutilises comme mot de passe systeme -> SSH.
6. Timer root (dlq_drainer.py) appelant clickhouse-client avec --password en CLI (visible /proc/*/cmdline).
7. Generation de messages DLQ + surveillance /proc -> capture mot de passe admin ClickHouse.
8. INSERT INTO FUNCTION file() (sandbox user_files) ajoute une ligne Python malveillante au script formatter execute en root -> RCE root.

## Key Evidence

- dump HPROF avec credentials en clair; /etc/passwd relu via requete ClickHouse JSONExtractString; credentials SASL Kafka dans server.properties; cmdline capture "clickhouse-client --user default --password ..."; uid=0(root) final.

## Dead Ends

- OOB (DNS/HTTP out-of-band) pour le XXE etait impossible depuis cet environnement, a force l'approche in-band.

## Payloads And Commands

```text
XML DOCTYPE avec entite SYSTEM file:// (XXE in-band); requete SQL INSERT INTO FUNCTION file() ajoutant os.system(base64...) au script cible.
```

## Flag / Outcome

- user + root flags obtenus.

## Reusable Lessons

- Actuator heapdump expose = fuite credentials DB. XXE blind sans OOB observable -> exfiltrer en bande via un pipeline aval qui serialise/stocke le contenu resolu. Secrets passes en --password CLI capturables via /proc/*/cmdline. Fonction file()/moteur analytique exploitable en ecriture pour empoisonner un script execute par un job privilegie.

## Pattern Candidates

- Nouveau pattern: xxe-blind-inband-via-pipeline + proc-cmdline-password-capture
