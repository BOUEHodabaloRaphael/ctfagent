---
doc_kind: writeup
title: "Contournement du garde SSRF via window.open() dans le clonage de site"
category: web
slug: forge-ssrf-window-open-popup-bypass
created: 2026-10-29
status: solved
tags:
  - ssrf
  - playwright
  - browser-context-scope
  - popup-bypass
  - internal-network
source: "Programme de divulgation reelle Forge/RodiumAI"
target: "Plateforme Forge (RodiumAI) - API multi-tenant"
---
# Contournement du garde SSRF via window.open() dans le clonage de site

## Challenge Summary

- Source: Programme de divulgation reelle Forge/RodiumAI
- Target: Plateforme Forge (RodiumAI) - API multi-tenant
- Goal: Le garde SSRF est scope a l'objet Page Playwright; un window.open() depuis le JS de la page clonee cree une nouvelle Page jamais interceptee, atteignant le reseau interne.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source report)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. _guard_route enregistre via page.route - scope Page, pas contexte navigateur.
2. Page a cloner attaquant-controlee avec script window.open(url_interne).
3. Chromium cree une nouvelle Page dans le meme contexte, jamais attachee au garde.
4. La requete popup atteint l'IP/port interne sans passer par la validation.
5. Comparaison: iframe cachee identique est interceptee et bloquable; window.open() ne l'est jamais.
6. Demonstration contre un service interne reel charge en integralite via le popup.

## Key Evidence

- Logs serveur: "ROUTE HIT" pour l'iframe, aucun log pour window.open(); 2 hits (iframe+popup) avec interception uniquement sur l'iframe; contenu du service interne recupere via le popup.

## Dead Ends

- n/a.

## Payloads And Commands

```text
Page HTML attaquant avec iframe cachee + script window.open(url_interne).
```

## Flag / Outcome

- Vulnerabilite confirmee et reportee.

## Reusable Lessons

- Un garde SSRF scope a Page au lieu de BrowserContext dans un outil headless-browser server-side: toute navigation Playwright/Puppeteer sur contenu attaquant-controle doit guarder le contexte entier, sinon un popup echappe au filtre. Partage la meme cause racine que forge-ssrf-dns-rebinding-toctou-attachments (validation qui ne lie pas l'IP validee a la connexion reelle).

## Pattern Candidates

- Nouveau pattern: ssrf-guard-scoped-to-page-not-context
