---
doc_kind: pattern
title: "Zephyr - internal domain - Reutilisation creds Chrome pour PSRemote cross-domaine"
category: web
slug: internal-zsm-local-chrome-cred-reuse-psremote
created: 2026-10-29
status: active
tags:
  - credential-reuse
  - psremote
  - invoke-command
  - cross-domain
chain_summary: "Un compte deja compromis via un dump Chrome plus tot dans le lab est membre d'un groupe qui peut CanPSRemote vers une autre machine. La connexion WinRM directe echoue (firewall), mais passer par un objet credential depuis une session existante fonctionne."
---
# Zephyr - internal domain - Reutilisation creds Chrome pour PSRemote cross-domaine

## Chain Summary

- One-line chain: Un compte deja compromis via un dump Chrome plus tot dans le lab est membre d'un groupe qui peut CanPSRemote vers une autre machine. La connexion WinRM directe echoue (firewall), mais passer par un objet credential depuis une session existante fonctionne.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Invoke-Command retourne directement le flag.

## Escalation Order

1. BloodHound: edge CanPSRemote identifie pour le compte deja compromis.
2. evil-winrm direct refuse (firewall).
3. Depuis une session existante: construction d'un objet PSCredential pour le compte compromis.
4. Invoke-Command vers la machine cible avec ce credential -> lecture du flag.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Reutilisation de creds cross-domaine decouverts tot dans l'engagement reste valable plus tard; passer par un objet credential dans Invoke-Command quand une connexion WinRM directe est filtree par le reseau.
```

## Related Writeups

- internal-zsm-local-chrome-cred-reuse-psremote

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
