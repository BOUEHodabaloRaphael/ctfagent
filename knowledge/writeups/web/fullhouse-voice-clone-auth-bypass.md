---
doc_kind: writeup
title: "FullHouse - Prouve que c'est toi (contournement auth vocale par voice cloning + JWT fait main)"
category: web
slug: fullhouse-voice-clone-auth-bypass
created: 2026-10-29
status: solved
tags:
  - voice-cloning
  - biometric-bypass
  - jwt-manual-cookie
  - ai-model-abuse
  - vault
source: "HTB Pro Lab FullHouse"
target: "Vault IIS avec verification biometrique vocale"
---
# FullHouse - Prouve que c'est toi (contournement auth vocale par voice cloning + JWT fait main)

## Challenge Summary

- Source: HTB Pro Lab FullHouse
- Target: Vault IIS avec verification biometrique vocale
- Goal: Un Vault IIS demande une empreinte vocale prononcant un mot-cle; l'audio de reference fuite permet de cloner la voix via un modele IA externe et de passer la verification, obtenant un JWT qui doit etre rejoue manuellement en cookie.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Depuis un acces precedent, trouver un fichier audio de reference sur le disque.
2. Le Vault affiche le mot-cle du jour attendu.
3. ffmpeg nettoie l'audio (highpass, afftdn, loudnorm) pour ameliorer le clonage.
4. Un modele de voice-cloning (service IA externe) genere l'audio clone prononcant le mot-cle.
5. Upload de l'audio clone -> reponse JSON confirmant le succes avec un JWT.
6. Pas de Set-Cookie renvoye -> construction manuelle du header Cookie avec le JWT -> acces au dashboard -> flag.

## Key Evidence

- reponse JSON confirmant le bypass de verification vocale avec un token JWT.

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
fichier audio clone (wav) via modele de voice-cloning + cookie JWT construit manuellement.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Une biometrie vocale sans liveness/anti-replay est contournable si un echantillon de reference fuite, meme via un service de voice-cloning tiers gratuit; quand une API renvoie un JWT sans Set-Cookie, construire le cookie attendu manuellement plutot que supposer l'auth cassee.

## Pattern Candidates

- Nouveau pattern: fullhouse-voice-clone-auth-bypass
