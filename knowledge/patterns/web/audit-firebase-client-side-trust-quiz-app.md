---
doc_kind: pattern
title: "Audit QuizTech - logique metier et correction 100% cote client sur app React + Firestore"
category: web
slug: audit-firebase-client-side-trust-quiz-app
created: 2026-10-29
status: active
tags:
  - firebase
  - firestore-rules
  - client-side-trust
  - business-logic-bypass
  - pii-leak
  - react-spa-audit
chain_summary: "Toute la logique metier (banque de questions, correction, score, classement) s'execute cote client; les regles Firestore ne valident que la forme des donnees jamais leur veracite."
---
# Audit QuizTech - logique metier et correction 100% cote client sur app React + Firestore

## Chain Summary

- One-line chain: Toute la logique metier (banque de questions, correction, score, classement) s'execute cote client; les regles Firestore ne valident que la forme des donnees jamais leur veracite.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Regle Firestore de validation qui verifie score<=total mais jamais la correspondance avec les reponses reelles; script automatise a repondu a de nombreuses questions a 100% en quelques minutes.

## Escalation Order

1. Chargement de la page sans authentification -> le bundle JS expose en clair questions+indices de bonnes reponses.
2. Extraction de la banque de questions/reponses par parsing du bundle.
3. Lecture des regles Firestore embarquees -> validation uniquement structurelle, jamais de la veracite du score.
4. Ecriture directe d'un document resultat arbitraire via un appel Firestore depuis la console navigateur, sans avoir repondu.
5. Lecture/ecriture du document classement sans plafond numerique -> falsification du classement public.
6. Collections de resultats/classement lisibles sans authentification -> fuite de donnees personnelles.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Pattern generique app Firebase sans backend applicatif: toujours lire les security rules embarquees dans le bundle client et distinguer validation de forme vs validation de veracite (recalcul serveur); toute logique de correction/scoring doit etre deplacee vers une Cloud Function, jamais confiee aux seules regles Firestore.
```

## Related Writeups

- audit-firebase-client-side-trust-quiz-app

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
