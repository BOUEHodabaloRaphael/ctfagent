---
doc_kind: pattern
title: "Bypass de biometrie vocale par voice-cloning sans liveness check"
category: web
slug: fullhouse-voice-clone-auth-bypass
created: 2026-10-29
status: active
tags:
  - voice-cloning
  - biometric-bypass
  - jwt-manual-cookie
  - ai-model-abuse
  - vault
chain_summary: "Une verification vocale sans anti-replay/liveness est contournable en clonant la voix a partir d'un echantillon de reference qui a fuite, via un service de voice-cloning IA accessible publiquement."
---
# Bypass de biometrie vocale par voice-cloning sans liveness check

## Chain Summary

- One-line chain: Une verification vocale sans anti-replay/liveness est contournable en clonant la voix a partir d'un echantillon de reference qui a fuite, via un service de voice-cloning IA accessible publiquement.
- Typical target shape: Systeme d'authentification biometrique vocale (prononcer un mot-cle) sans mecanisme de liveness/anti-replay; un echantillon audio de reference de la voix cible est accessible (fuite, fichier local).

## Preconditions

- Systeme d'authentification biometrique vocale (prononcer un mot-cle) sans mecanisme de liveness/anti-replay; un echantillon audio de reference de la voix cible est accessible (fuite, fichier local).

## Cheap Probes

- Chercher des fichiers audio de reference sur le systeme/disque accessible; identifier le mot-cle attendu par l'interface.

## Telltale Evidence

- L'interface affiche explicitement le mot-cle attendu ou le processus d'enrollment.

## Escalation Order

1. Localiser un echantillon audio de reference de la voix cible.
2. Nettoyer l'audio pour ameliorer la qualite de clonage (filtre passe-haut, debruitage, normalisation).
3. Utiliser un service de voice-cloning pour generer l'audio prononcant le mot-cle attendu.
4. Soumettre l'audio clone a la verification.
5. Si l'API renvoie un token sans poser de cookie, le construire manuellement pour l'etape suivante.

## Common Mistakes

- Supposer qu'une authentification est cassee juste parce qu'aucun Set-Cookie n'est renvoye apres un succes API, sans essayer de construire le cookie attendu manuellement.

## Payload Shapes

```text
Cookie: access_token_cookie=<jwt recupere dans la reponse JSON>
```

## Related Writeups

- fullhouse-voice-clone-auth-bypass

## Skill Impact

- Related skill: web-triage (auth biometrique): ajouter le test de voice-cloning sur toute biometrie vocale sans liveness, et la construction manuelle de cookie quand un JWT est renvoye sans Set-Cookie.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
