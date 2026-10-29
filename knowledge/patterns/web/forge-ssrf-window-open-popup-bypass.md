---
doc_kind: pattern
title: "Garde SSRF scope a la Page Playwright/Puppeteer au lieu du BrowserContext"
category: web
slug: forge-ssrf-window-open-popup-bypass
created: 2026-10-29
status: active
tags:
  - ssrf
  - playwright
  - browser-context-scope
  - popup-bypass
  - internal-network
chain_summary: "Un garde SSRF enregistre via page.route() ne couvre que l'objet Page initial; window.open()/popups creent de nouvelles Pages dans le meme contexte qui echappent totalement au garde."
---
# Garde SSRF scope a la Page Playwright/Puppeteer au lieu du BrowserContext

## Chain Summary

- One-line chain: Un garde SSRF enregistre via page.route() ne couvre que l'objet Page initial; window.open()/popups creent de nouvelles Pages dans le meme contexte qui echappent totalement au garde.
- Typical target shape: Service headless-browser (screenshot, clone de site, rendu PDF) naviguant du contenu potentiellement attaquant-controle, avec un garde SSRF enregistre au niveau Page plutot que BrowserContext.

## Preconditions

- Service headless-browser (screenshot, clone de site, rendu PDF) naviguant du contenu potentiellement attaquant-controle, avec un garde SSRF enregistre au niveau Page plutot que BrowserContext.

## Cheap Probes

- Charger une page de test contenant un window.open() vers une cible controlee et verifier si cette requete popup passe par le meme garde que la navigation principale.

## Telltale Evidence

- Les logs du garde ne montrent aucune interception pour la requete issue du popup, alors que la navigation principale est bien loggee/filtree.

## Escalation Order

1. Confirmer le scope du garde SSRF (page.route vs context.route/context.on('page')).
2. Fournir du contenu HTML attaquant-controle au feature de clonage/rendu avec un script window.open() vers une cible interne.
3. Observer si la requete popup atteint la cible interne sans passer par le filtre.

## Common Mistakes

- Enregistrer un garde SSRF au niveau Page au lieu du BrowserContext complet dans un outil d'automatisation navigateur server-side.

## Payload Shapes

```text
<script>window.open('http://internal-target/')</script>
```

## Related Writeups

- forge-ssrf-window-open-popup-bypass, forge-ssrf-dns-rebinding-toctou-attachments

## Skill Impact

- Related skill: web-triage (SSRF): ajouter 'tester window.open()/popup dans tout service de rendu/clone headless-browser' comme sous-cas de bypass de garde SSRF.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
