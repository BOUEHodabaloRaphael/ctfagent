---
doc_kind: writeup
title: "Zephyr - internal domain - Reutilisation creds Chrome pour PSRemote cross-domaine"
category: web
slug: internal-zsm-local-chrome-cred-reuse-psremote
created: 2026-10-29
status: solved
tags:
  - credential-reuse
  - psremote
  - invoke-command
  - cross-domain
source: "HTB Pro Lab Zephyr"
target: "Compte deja compromis avec droit CanPSRemote"
---
# Zephyr - internal domain - Reutilisation creds Chrome pour PSRemote cross-domaine

## Challenge Summary

- Source: HTB Pro Lab Zephyr
- Target: Compte deja compromis avec droit CanPSRemote
- Goal: Un compte deja compromis via un dump Chrome plus tot dans le lab est membre d'un groupe qui peut CanPSRemote vers une autre machine. La connexion WinRM directe echoue (firewall), mais passer par un objet credential depuis une session existante fonctionne.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. BloodHound: edge CanPSRemote identifie pour le compte deja compromis.
2. evil-winrm direct refuse (firewall).
3. Depuis une session existante: construction d'un objet PSCredential pour le compte compromis.
4. Invoke-Command vers la machine cible avec ce credential -> lecture du flag.

## Key Evidence

- Invoke-Command retourne directement le flag.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
PowerShell PSCredential + Invoke-Command.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout (lecture visuelle verifiee).

## Reusable Lessons

- Reutilisation de creds cross-domaine decouverts tot dans l'engagement reste valable plus tard; passer par un objet credential dans Invoke-Command quand une connexion WinRM directe est filtree par le reseau.

## Pattern Candidates

- Voir pattern associe de meme slug.
