---
doc_kind: pattern
title: "Zephyr - internal domain - PowerUp Invoke-ServiceAbuse (service modifiable)"
category: pwn
slug: internal-zsm-local-service-abuse-wuauserv
created: 2026-10-29
status: active
tags:
  - privesc
  - powerup
  - service-abuse
  - amsi-bypass
  - runascs
chain_summary: "AMSI bypass + PowerUp Invoke-AllChecks identifie un service systeme comme modifiable (binPath). Invoke-ServiceAbuse modifie le binPath pour creer un utilisateur admin local."
---
# Zephyr - internal domain - PowerUp Invoke-ServiceAbuse (service modifiable)

## Chain Summary

- One-line chain: AMSI bypass + PowerUp Invoke-AllChecks identifie un service systeme comme modifiable (binPath). Invoke-ServiceAbuse modifie le binPath pour creer un utilisateur admin local.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Invoke-AllChecks confirme l'AbuseFunction Invoke-ServiceAbuse; Invoke-ServiceAbuse confirme la commande executee.

## Escalation Order

1. AMSI bypass (reflection).
2. Upload d'un outil pour shell interactif (requis pour PowerUp).
3. Invoke-AllChecks -> service identifie comme Modifiable Services.
4. Invoke-ServiceAbuse -> creation d'un utilisateur admin local via le service abuse.
5. evil-winrm avec le nouvel utilisateur -> lecture flag.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Service modifiable + PowerUp Invoke-ServiceAbuse = privesc Windows classique; certaines fonctions PowerUp necessitent un shell veritablement interactif (pas un reverse shell basique).
```

## Related Writeups

- internal-zsm-local-service-abuse-wuauserv

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
