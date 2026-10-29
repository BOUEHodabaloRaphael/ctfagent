---
doc_kind: pattern
title: "Plugin WordPress OTP Login With Phone Number - bypass du verrouillage anti-bruteforce -> ATO non authentifie"
category: web
slug: wp-lwp-otp-lockout-reset-bypass-ato
created: 2026-10-29
status: active
tags:
  - wordpress-plugin
  - otp-bypass
  - lockout-reset
  - account-takeover
  - broken-authentication
  - missing-rate-limit
chain_summary: "Le correctif anti-bruteforce (5 tentatives max) est neutralise car toute nouvelle demande de code OTP remet le compteur d'echecs a zero, permettant un bruteforce illimite du code pour prendre le controle de n'importe quel compte."
---
# Plugin WordPress OTP Login With Phone Number - bypass du verrouillage anti-bruteforce -> ATO non authentifie

## Chain Summary

- One-line chain: Le correctif anti-bruteforce (5 tentatives max) est neutralise car toute nouvelle demande de code OTP remet le compteur d'echecs a zero, permettant un bruteforce illimite du code pour prendre le controle de n'importe quel compte.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Plusieurs centaines de requetes HTTP suffisent pour obtenir le cookie de session de la victime; la fonction de generation de code remet le compteur a 0 sans aucun rate-limit independant sur l'endpoint lui-meme.

## Escalation Order

1. GET page d'accueil -> nonce anonyme public utilise par les endpoints AJAX non authentifies.
2. Appel de l'endpoint mot de passe oublie avec l'email/telephone de la victime -> genere un nouveau code et reinitialise le compteur d'echecs a 0.
3. Appel de l'endpoint de verification OTP avec 5 essais -> verrouillage declenche, code efface.
4. Retour a l'etape precedente -> nouveau code, compteur remis a 0, boucle illimitee sans rate-limit independant.
5. Essai correct apres suffisamment de cycles -> pose du cookie de session authentifiee de la victime (ATO complet).

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Pattern generique correctif de lockout contournable par regeneration du secret: sur tout mecanisme OTP/anti-bruteforce, toujours verifier si l'action de regeneration du code remet aussi a zero le compteur de tentatives - si oui, le lockout n'a aucun effet reel.
```

## Related Writeups

- wp-lwp-otp-lockout-reset-bypass-ato

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
