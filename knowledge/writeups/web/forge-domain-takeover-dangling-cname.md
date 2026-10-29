---
doc_kind: writeup
title: "Custom domain hijack via residual DNS (no per-project ownership proof)"
category: web
slug: forge-domain-takeover-dangling-cname
created: 2026-10-29
status: solved
tags:
  - domain-takeover
  - dns
  - cname
  - dangling-dns
  - multi-tenant
source: "Programme de divulgation reelle Forge/RodiumAI"
target: "Plateforme Forge (RodiumAI) - API multi-tenant"
---
# Custom domain hijack via residual DNS (no per-project ownership proof)

## Challenge Summary

- Source: Programme de divulgation reelle Forge/RodiumAI
- Target: Plateforme Forge (RodiumAI) - API multi-tenant
- Goal: Verification de domaine custom basee uniquement sur un CNAME partage sans preuve d'appartenance par projet; un hostname abandonne avec CNAME residuel est reclamable par un attaquant.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source report)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Ancien client valide un domaine (CNAME vers la cible partagee) puis supprime son projet sans retirer le CNAME chez son registrar.
2. Le hostname reste dangling mais la ligne ProjectDomain est supprimee (ON DELETE CASCADE), liberant la contrainte unique.
3. Attaquant cree un projet et appelle PUT /projects/{id}/domain avec ce hostname.
4. advance_verification() verifie seulement la resolution CNAME vers la cible partagee.
5. En mode degrade (sans AWS), statut passe direct a VALIDATED; en prod, l'etape ACM bloque l'attachement final mais permet deja l'abus de quota ACM et le squatting de hostname.

## Key Evidence

- Lecture de code de advance_verification(); docstring reconnaissant le degraded mode; UniqueConstraint(hostname) + ondelete=CASCADE sur ProjectDomain.

## Dead Ends

- n/a.

## Payloads And Commands

```text
Requete HTTP PUT avec hostname cible + CNAME DNS preexistant pointant vers la cible partagee.
```

## Flag / Outcome

- Vulnerabilite confirmee et reportee.

## Reusable Lessons

- Toute plateforme qui valide la propriete d'un domaine custom via un seul CNAME partage (pas de token TXT par-projet) est vulnerable si le nom est libere sans delai de grace a la suppression du projet.

## Pattern Candidates

- Nouveau pattern: dangling-cname-domain-takeover
