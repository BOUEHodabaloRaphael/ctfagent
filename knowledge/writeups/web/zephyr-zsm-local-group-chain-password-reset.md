---
doc_kind: writeup
title: "Zephyr - zsm.local - Abus chaine de groupes pour reset mot de passe"
category: web
slug: zephyr-zsm-local-group-chain-password-reset
created: 2026-10-29
status: solved
tags:
  - acl-abuse
  - group-membership
  - password-reset
  - powerview
source: "HTB Pro Lab Zephyr"
target: "AD zsm.local, groupe avec ForceChangePassword"
---
# Zephyr - zsm.local - Abus chaine de groupes pour reset mot de passe

## Challenge Summary

- Source: HTB Pro Lab Zephyr
- Target: AD zsm.local, groupe avec ForceChangePassword
- Goal: Un compte machine compromis peut ajouter des membres a un groupe qui a ForceChangePassword sur un autre compte; un utilisateur compromis est ajoute au groupe puis le mot de passe cible est change.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Purge des tickets en exces.
2. Add-DomainGroupMember sur le groupe cible (via le ticket du compte machine compromis).
3. Set-DomainUserPassword sur le compte cible.
4. Connexion au compte cible -> acces admin.

## Key Evidence

- Add-DomainGroupMember confirme l'ajout; Set-DomainUserPassword confirme le reset.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
PowerView.ps1 Add-DomainGroupMember, Set-DomainUserPassword.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout (lecture visuelle verifiee).

## Reusable Lessons

- Les chaines de groupes imbriquees avec droits sur mot de passe sont communes dans un AD mal configure; toujours suivre la chaine complete d'edges BloodHound jusqu'au bout.

## Pattern Candidates

- Voir pattern associe de meme slug.
