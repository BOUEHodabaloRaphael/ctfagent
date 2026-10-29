---
doc_kind: pattern
title: "XXE aveugle sans OOB: exfiltration in-band via pipeline aval"
category: web
slug: htb-stream-xxe-clickhouse
created: 2026-10-29
status: active
tags:
  - web
  - xxe
  - clickhouse
  - actuator-heapdump
  - credential-reuse
  - rce-root
chain_summary: "Quand l'OOB (DNS/HTTP) est bloque pour un XXE aveugle, chercher un pipeline aval (message broker, DB analytique) qui stocke/serialise le contenu resolu et le relit en bande."
---
# XXE aveugle sans OOB: exfiltration in-band via pipeline aval

## Chain Summary

- One-line chain: Quand l'OOB (DNS/HTTP) est bloque pour un XXE aveugle, chercher un pipeline aval (message broker, DB analytique) qui stocke/serialise le contenu resolu et le relit en bande.
- Typical target shape: XXE confirme (parseur XML avec resolve_entities actif) mais aucune exfiltration OOB possible (reseau isole).

## Preconditions

- XXE confirme (parseur XML avec resolve_entities actif) mais aucune exfiltration OOB possible (reseau isole).

## Cheap Probes

- Tester une entite SYSTEM file:// et verifier si le contenu resolu reapparait ailleurs (DB, log, pipeline de traitement aval) plutot que de se fier a un callback DNS/HTTP.

## Telltale Evidence

- Contenu de fichier systeme visible dans une table/pipeline aval apres soumission du payload XXE.

## Escalation Order

1. Confirmer l'injection XXE basique (erreur de parsing, entite simple).
2. Tester OOB (DNS/HTTP out-of-band) - si bloque, chercher un stockage aval du contenu resolu.
3. Lire les fichiers systeme/config pertinents (credentials, server.properties) via ce canal in-band.
4. Chercher les secrets passes en argument CLI a des process root (--password) capturables via /proc/*/cmdline pendant leur execution.

## Common Mistakes

- Abandonner un XXE confirme juste parce que l'OOB classique ne fonctionne pas.

## Payload Shapes

```text
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>
```

## Related Writeups

- htb-stream-xxe-clickhouse

## Skill Impact

- Related skill: web-triage (XXE): ajouter l'exfiltration in-band via pipeline aval comme alternative quand OOB echoue.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
