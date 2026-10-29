---
doc_kind: writeup
title: "Zephyr - internal domain - PowerUp Invoke-ServiceAbuse (service modifiable)"
category: pwn
slug: internal-zsm-local-service-abuse-wuauserv
created: 2026-10-29
status: solved
tags:
  - privesc
  - powerup
  - service-abuse
  - amsi-bypass
  - runascs
source: "HTB Pro Lab Zephyr"
target: "Service Windows avec binPath modifiable"
---
# Zephyr - internal domain - PowerUp Invoke-ServiceAbuse (service modifiable)

## Challenge Summary

- Source: HTB Pro Lab Zephyr
- Target: Service Windows avec binPath modifiable
- Goal: AMSI bypass + PowerUp Invoke-AllChecks identifie un service systeme comme modifiable (binPath). Invoke-ServiceAbuse modifie le binPath pour creer un utilisateur admin local.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. AMSI bypass (reflection).
2. Upload d'un outil pour shell interactif (requis pour PowerUp).
3. Invoke-AllChecks -> service identifie comme Modifiable Services.
4. Invoke-ServiceAbuse -> creation d'un utilisateur admin local via le service abuse.
5. evil-winrm avec le nouvel utilisateur -> lecture flag.

## Key Evidence

- Invoke-AllChecks confirme l'AbuseFunction Invoke-ServiceAbuse; Invoke-ServiceAbuse confirme la commande executee.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
PowerUp.ps1 (Invoke-AllChecks, Invoke-ServiceAbuse), outil de shell interactif, AMSI bypass.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout (lecture visuelle verifiee).

## Reusable Lessons

- Service modifiable + PowerUp Invoke-ServiceAbuse = privesc Windows classique; certaines fonctions PowerUp necessitent un shell veritablement interactif (pas un reverse shell basique).

## Pattern Candidates

- Voir pattern associe de meme slug.
