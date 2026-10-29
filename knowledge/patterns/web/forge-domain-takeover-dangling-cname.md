---
doc_kind: pattern
title: "Domain takeover via CNAME dangling sans preuve d'appartenance par projet"
category: web
slug: forge-domain-takeover-dangling-cname
created: 2026-10-29
status: active
tags:
  - domain-takeover
  - dns
  - cname
  - dangling-dns
  - multi-tenant
chain_summary: "Plateforme multi-tenant validant un domaine custom par CNAME partage sans token TXT per-project: un hostname libere apres suppression de projet reste dangling et reclamable."
---
# Domain takeover via CNAME dangling sans preuve d'appartenance par projet

## Chain Summary

- One-line chain: Plateforme multi-tenant validant un domaine custom par CNAME partage sans token TXT per-project: un hostname libere apres suppression de projet reste dangling et reclamable.
- Typical target shape: SaaS multi-tenant proposant des domaines personnalises avec validation CNAME vers une cible partagee (pas de challenge TXT unique par projet).

## Preconditions

- SaaS multi-tenant proposant des domaines personnalises avec validation CNAME vers une cible partagee (pas de challenge TXT unique par projet).

## Cheap Probes

- Chercher un hostname associe a un ancien projet supprime dont le CNAME DNS existe toujours; verifier si la plateforme accepte de re-revendiquer ce hostname sans nouvelle preuve.

## Telltale Evidence

- La validation de domaine passe directement a VALIDATED/pending-final sur la seule base de la resolution CNAME, sans token unique genere par projet.

## Escalation Order

1. Identifier un hostname avec CNAME residuel pointant vers la cible partagee de la plateforme.
2. Creer un projet et tenter de reclamer ce hostname via l'API de domaine custom.
3. Verifier si la validation passe sans etape de preuve supplementaire specifique au nouveau projet.

## Common Mistakes

- Concevoir la validation de domaine custom autour d'un seul CNAME partage par toute la plateforme au lieu d'un token TXT unique par projet avec delai de grace a la suppression.

## Payload Shapes

```text
PUT /projects/{id}/domain {"hostname":"<dangling-host>"}
```

## Related Writeups

- forge-domain-takeover-dangling-cname

## Skill Impact

- Related skill: web-triage: ajouter domain takeover / dangling CNAME multi-tenant comme sous-cas a tester sur toute plateforme SaaS avec domaines custom.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
