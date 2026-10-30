---
doc_kind: pattern
title: "Interaction fiable avec un quiz web React — javascript_tool plutot que coordonnees pixel"
category: misc
slug: react-quiz-reliable-dom-interaction
created: 2026-10-30
status: active
tags:
  - legacy-memory-migration
  - nctf26-prep
  - react
chain_summary: "Sur une UI quiz React, cliquer par coordonnees pixel peut cocher silencieusement la mauvaise case si le viewport diverge entre deux captures — lire/ecrire l'etat reel via JS (target.click(), pas .checked direct) est fiable, pas les coordonnees."
---
# Interaction fiable avec un quiz web React — javascript_tool plutot que coordonnees pixel

## Chain Summary

- One-line chain: Sur une UI quiz React, cliquer par coordonnees pixel peut cocher silencieusement la mauvaise case si le viewport diverge entre deux captures — lire/ecrire l'etat reel via JS (target.click(), pas .checked direct) est fiable, pas les coordonnees.

## Preconditions

- Challenge/plateforme avec une interface de quiz/formulaire React (radios, checkboxes) a remplir et soumettre de facon fiable et repetable.

## Cheap Probes

- Lire l'etat reel des radios via JS: document.querySelectorAll('input[type=radio]'), grouper par name, verifier .checked actuel avant toute action.

## Telltale Evidence

- Un screenshot 'a l'air' correct mais le DOM reel peut avoir une autre case cochee (zoom different entre deux captures, resize de fenetre entre deux etapes) — un quiz soumis avec des reponses qu'on croyait bonnes peut echouer sans erreur visible avant coup.

## Escalation Order

1. Toujours lire l'etat REEL du DOM via javascript_tool plutot que de se fier a un screenshot+coordonnees pixel.
2. Pour cocher une radio: utiliser element.click() (pas .checked = true directement, qui ne declenche pas les synthetic events React et laisse l'etat React desynchronise du DOM).
3. Revérifier le meme etat juste avant de soumettre, surtout apres un scroll ou un changement de layout.
4. Pour un bouton de confirmation duplique (ex. Submit qui ouvre une modale Confirm avec un 2e bouton Submit): ne pas chercher par textContent seul (ambigu entre les deux boutons) — retrouver le conteneur de la modale via le texte du message de confirmation, remonter de quelques niveaux parentElement, puis filtrer les boutons de CE conteneur par classe.

## Common Mistakes

- Cliquer par coordonnees pixel recalculees a la main sur un ancien screenshot, qui se desynchronise des que le viewport/zoom change entre deux captures.

## Payload Shapes

```text
document.querySelector("input[name=qX][value=Y]").click()  // pas .checked=true
```

## Related Writeups

- N/A

## Skill Impact

- Related skill: browser-automation: ajouter la lecture/ecriture DOM via javascript_tool comme methode par defaut pour tout quiz/formulaire React, plutot que les coordonnees pixel.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
