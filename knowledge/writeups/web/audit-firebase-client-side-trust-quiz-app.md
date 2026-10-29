---
doc_kind: writeup
title: "Audit QuizTech - logique metier et correction 100% cote client sur app React + Firestore"
category: web
slug: audit-firebase-client-side-trust-quiz-app
created: 2026-10-29
status: solved
tags:
  - firebase
  - firestore-rules
  - client-side-trust
  - business-logic-bypass
  - pii-leak
  - react-spa-audit
source: "Audit de securite autorise (app React SPA + Firebase/Firestore)"
target: "App React SPA avec logique metier cote client"
---
# Audit QuizTech - logique metier et correction 100% cote client sur app React + Firestore

## Challenge Summary

- Source: Audit de securite autorise (app React SPA + Firebase/Firestore)
- Target: App React SPA avec logique metier cote client
- Goal: Toute la logique metier (banque de questions, correction, score, classement) s'execute cote client; les regles Firestore ne valident que la forme des donnees jamais leur veracite.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Chargement de la page sans authentification -> le bundle JS expose en clair questions+indices de bonnes reponses.
2. Extraction de la banque de questions/reponses par parsing du bundle.
3. Lecture des regles Firestore embarquees -> validation uniquement structurelle, jamais de la veracite du score.
4. Ecriture directe d'un document resultat arbitraire via un appel Firestore depuis la console navigateur, sans avoir repondu.
5. Lecture/ecriture du document classement sans plafond numerique -> falsification du classement public.
6. Collections de resultats/classement lisibles sans authentification -> fuite de donnees personnelles.

## Key Evidence

- Regle Firestore de validation qui verifie score<=total mais jamais la correspondance avec les reponses reelles; script automatise a repondu a de nombreuses questions a 100% en quelques minutes.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Script d'extraction du bundle JS (parsing des appels de construction d'objets) + appels d'ecriture directs contre Firestore.
```

## Flag / Outcome

- Flag obtenu / finding confirme, chaine terminee.

## Reusable Lessons

- Pattern generique app Firebase sans backend applicatif: toujours lire les security rules embarquees dans le bundle client et distinguer validation de forme vs validation de veracite (recalcul serveur); toute logique de correction/scoring doit etre deplacee vers une Cloud Function, jamais confiee aux seules regles Firestore.

## Pattern Candidates

- Voir pattern associe de meme slug.
