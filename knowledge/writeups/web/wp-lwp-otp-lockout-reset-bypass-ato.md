---
doc_kind: writeup
title: "Plugin WordPress OTP Login With Phone Number - bypass du verrouillage anti-bruteforce -> ATO non authentifie"
category: web
slug: wp-lwp-otp-lockout-reset-bypass-ato
created: 2026-10-29
status: solved
tags:
  - wordpress-plugin
  - otp-bypass
  - lockout-reset
  - account-takeover
  - broken-authentication
  - missing-rate-limit
source: "Rapport de vulnerabilite reel (bug bounty, en triage)"
target: "Plugin WordPress OTP <=1.8.74"
---
# Plugin WordPress OTP Login With Phone Number - bypass du verrouillage anti-bruteforce -> ATO non authentifie

## Challenge Summary

- Source: Rapport de vulnerabilite reel (bug bounty, en triage)
- Target: Plugin WordPress OTP <=1.8.74
- Goal: Le correctif anti-bruteforce (5 tentatives max) est neutralise car toute nouvelle demande de code OTP remet le compteur d'echecs a zero, permettant un bruteforce illimite du code pour prendre le controle de n'importe quel compte.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. GET page d'accueil -> nonce anonyme public utilise par les endpoints AJAX non authentifies.
2. Appel de l'endpoint mot de passe oublie avec l'email/telephone de la victime -> genere un nouveau code et reinitialise le compteur d'echecs a 0.
3. Appel de l'endpoint de verification OTP avec 5 essais -> verrouillage declenche, code efface.
4. Retour a l'etape precedente -> nouveau code, compteur remis a 0, boucle illimitee sans rate-limit independant.
5. Essai correct apres suffisamment de cycles -> pose du cookie de session authentifiee de la victime (ATO complet).

## Key Evidence

- Plusieurs centaines de requetes HTTP suffisent pour obtenir le cookie de session de la victime; la fonction de generation de code remet le compteur a 0 sans aucun rate-limit independant sur l'endpoint lui-meme.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Boucle HTTP automatisee alternant demande de code puis essais de verification, jusqu'a succes.
```

## Flag / Outcome

- Flag obtenu / finding confirme, chaine terminee.

## Reusable Lessons

- Pattern generique correctif de lockout contournable par regeneration du secret: sur tout mecanisme OTP/anti-bruteforce, toujours verifier si l'action de regeneration du code remet aussi a zero le compteur de tentatives - si oui, le lockout n'a aucun effet reel.

## Pattern Candidates

- Voir pattern associe de meme slug.
