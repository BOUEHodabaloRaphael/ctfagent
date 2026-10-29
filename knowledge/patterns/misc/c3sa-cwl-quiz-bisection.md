---
doc_kind: pattern
title: "Bisection a variable unique pour quiz/formulaire a feedback global seul"
category: misc
slug: c3sa-cwl-quiz-bisection
created: 2026-10-29
status: active
tags:
  - quiz-bisection
  - dom-automation
  - react-ui
  - blind-feedback
  - certification
chain_summary: "Changer une seule reponse par tentative et interpreter le delta de score (+1/-1/0) pour isoler deterministiquement les questions fausses sous contrainte de tentatives limitees."
---
# Bisection a variable unique pour quiz/formulaire a feedback global seul

## Chain Summary

- One-line chain: Changer une seule reponse par tentative et interpreter le delta de score (+1/-1/0) pour isoler deterministiquement les questions fausses sous contrainte de tentatives limitees.
- Typical target shape: Quiz/formulaire ne donnant qu'un score global (pas de detail par question) avec un nombre de tentatives limite.

## Preconditions

- Quiz/formulaire ne donnant qu'un score global (pas de detail par question) avec un nombre de tentatives limite.

## Cheap Probes

- Premiere tentative avec les reponses les plus probables, noter le score de depart.

## Telltale Evidence

- Le delta de score entre deux tentatives ne differant que d'une seule reponse revele sans ambiguite si cette reponse etait correcte ou non (et parfois si l'ancienne etait aussi fausse si le delta est nul).

## Escalation Order

1. Repondre avec les meilleures estimations initiales, noter le score.
2. A chaque tentative suivante, changer une seule reponse par rapport a la precedente.
3. Interpreter strictement le delta (+1 = nouvelle correcte, -1 = revenir a l'ancienne, 0 = les deux fausses, chercher une 3e option).
4. Pour piloter une UI React/JS, utiliser le DOM (click()+verification d'etat) plutot que des coordonnees pixel fragiles.

## Common Mistakes

- Changer plusieurs reponses a la fois (rend le delta ininterpretable); piloter l'UI par coordonnees pixel qui se decalent entre rendus.

## Payload Shapes

```text
document.querySelector('input[name=qX][value=Y]').click()
```

## Related Writeups

- c3sa-cwl-quiz-bisection

## Skill Impact

- Related skill: Backlog: pattern transversal utile pour tout misc challenge/certification a feedback binaire global.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
