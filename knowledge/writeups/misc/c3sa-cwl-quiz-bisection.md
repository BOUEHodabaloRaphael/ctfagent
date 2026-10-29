---
doc_kind: writeup
title: "C3SA — Certified Cyber Security Analyst (CyberWarFare Labs)"
category: misc
slug: c3sa-cwl-quiz-bisection
created: 2026-10-29
status: solved
tags:
  - quiz-bisection
  - dom-automation
  - react-ui
  - blind-feedback
  - certification
source: "CyberWarFare Labs CyberRange (certification C3SA)"
target: "Quiz 30 questions, feedback global uniquement, tentatives limitees"
---
# C3SA — Certified Cyber Security Analyst (CyberWarFare Labs)

## Challenge Summary

- Source: CyberWarFare Labs CyberRange (certification C3SA)
- Target: Quiz 30 questions, feedback global uniquement, tentatives limitees
- Goal: Certification quiz-only resolue par bisection empirique stricte a variable unique sur tentatives limitees, combinee a l'automatisation DOM.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Detection que les clics souris par coordonnees pixel sur l'UI React sont peu fiables -> bascule sur pilotage direct DOM (click() + verification .checked avant soumission).
2. Recherche d'un writeup public existant -> echec (contenus payants, source non fiable).
3. Regle de bisection stricte : changer une seule question par tentative, interpreter le delta de score (+1=nouvelle bonne, -1=revenir a l'ancienne, 0=les deux fausses).
4. Historique de 7 tentatives isolant progressivement les questions fausses (regression volontaire pour confirmer une hypothese).
5. Bug de saisie (decalage d'indice) detecte par relecture manuelle, pas par le check automatique.
6. Expiration de session SSO entre deux jours -> re-authentification via IDP.

## Key Evidence

- Table d'historique des 7 tentatives avec scores exacts et deductions fermes par comparaison croisee ; score final 100% (30/30).

## Dead Ends

- Recherche d'un writeup public existant a echoue (contenus payants/non fiables) - obligation de resoudre en aveugle par bisection.

## Payloads And Commands

```text
Script JS de pilotage DOM (selection radio par name/value + verification stricte avant submit).
```

## Flag / Outcome

- Certification validee a 100%.

## Reusable Lessons

- Bisection a variable unique pour tout quiz a feedback global seul sous contrainte de tentatives limitees. Toujours piloter une UI React par le DOM plutot que par coordonnees pixel.

## Pattern Candidates

- Nouveau pattern: single-variable-bisection-blind-quiz
