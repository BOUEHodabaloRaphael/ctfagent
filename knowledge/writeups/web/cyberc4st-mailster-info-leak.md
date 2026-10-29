---
doc_kind: writeup
title: "Bug bounty - cyberc4st.com (plugin Mailster WordPress)"
category: web
slug: cyberc4st-mailster-info-leak
created: 2026-10-29
status: solved
tags:
  - web
  - wordpress
  - information-disclosure
  - rest-api-misconfig
  - stack-trace-leak
  - bug-bounty-reel
source: "Programme bug bounty reel (Bounty Africa)"
target: "WordPress + plugin Mailster (API REST)"
---
# Bug bounty - cyberc4st.com (plugin Mailster WordPress)

## Challenge Summary

- Source: Programme bug bounty reel (Bounty Africa)
- Target: WordPress + plugin Mailster (API REST)
- Goal: Deux failles non authentifiees sur l'API REST WordPress du plugin Mailster: erreur fatale PHP divulguant chemin serveur/stack trace, et endpoint REST sans permission_callback exposant la config complete d'un formulaire.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Endpoint public POST /wp-json/mailster/v1/forms/{id}/data (formulaire newsletter visible sur le site).
2. Requete minimale (email seul, sans parametre 'fields' attendu) -> erreur fatale PHP non interceptee (TypeError sur array_keys(null)).
3. Reponse HTTP 500 affiche en clair (display_errors actif en prod) chemin absolu d'installation + stack trace complete du plugin.
4. Enumeration systematique des routes REST voisines (mailster/v1/*) -> toutes protegees (401), sauf wp/v2/mailster-form/{id} (CPT generique) qui repond 200 sans auth.
5. Endpoint CPT non protege expose la config complete du formulaire (template email de confirmation double opt-in).
6. Fingerprint version du plugin via readme.txt (4.1.14) -> correspond a une plage vulnerable connue (exploitation non testee, hors perimetre du programme).

## Key Evidence

- Stack trace complete en HTTP 500 avec chemins serveur absolus; tableau comparatif endpoints mailster/v1/* (401) vs wp/v2/mailster-form/{id} (200, fuite); readme.txt "Stable tag: 4.1.14".

## Dead Ends

- Exploitation du CVE d'upload correspondant a la version fingerprintee non testee car necessitait acces admin wp-admin, interdit par le programme.

## Payloads And Commands

```text
Requete POST minimale sans parametre attendu (curl --data-urlencode); requete GET simple sans auth sur l'endpoint CPT.
```

## Flag / Outcome

- n/a - finding bug bounty reel, pas de flag CTF.

## Reusable Lessons

- Absence de validation de type avant array_keys()/foreach sur un parametre REST optionnel = fuite de stack trace/chemin serveur en prod. CPT WordPress expose via wp/v2 sans permission_callback explicite alors que l'API custom du meme plugin (v1) est protegee - toujours tester les routes generiques wp/v2/{cpt} en parallele de l'API custom d'un plugin.

## Pattern Candidates

- Nouveau pattern: wordpress-rest-cpt-unprotected-while-custom-api-protected
