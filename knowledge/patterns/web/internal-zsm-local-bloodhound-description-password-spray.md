---
doc_kind: pattern
title: "Zephyr - internal domain - Mot de passe en clair dans description AD + password spray"
category: web
slug: internal-zsm-local-bloodhound-description-password-spray
created: 2026-10-29
status: active
tags:
  - ad
  - description-field
  - password-spray
  - bloodhound
chain_summary: "SharpHound revele qu'un compte de service a un mot de passe en clair stocke dans le champ Description. Un spray de ce mot de passe contre tous les utilisateurs du domaine reussit sur un autre compte."
---
# Zephyr - internal domain - Mot de passe en clair dans description AD + password spray

## Chain Summary

- One-line chain: SharpHound revele qu'un compte de service a un mot de passe en clair stocke dans le champ Description. Un spray de ce mot de passe contre tous les utilisateurs du domaine reussit sur un autre compte.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Champ Description BloodHound visible; cme confirme Pwn3d! sur le compte spraye.

## Escalation Order

1. SharpHound+BloodHound import.
2. Node Info d'un compte de service -> champ Description contient un mot de passe en clair.
3. Wordlist de tous les utilisateurs du domaine.
4. proxychains cme winrm password spray -> succes sur un compte.
5. evil-winrm avec ce compte.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Toujours verifier les champs Description/Notes AD pour des mots de passe en clair oublies, puis sprayer ce mot de passe sur tous les comptes du domaine.
```

## Related Writeups

- internal-zsm-local-bloodhound-description-password-spray

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
