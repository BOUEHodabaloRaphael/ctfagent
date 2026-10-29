---
doc_kind: pattern
title: "Zephyr - zsm.local - Abus chaine de groupes pour reset mot de passe"
category: web
slug: zephyr-zsm-local-group-chain-password-reset
created: 2026-10-29
status: active
tags:
  - acl-abuse
  - group-membership
  - password-reset
  - powerview
chain_summary: "Un compte machine compromis peut ajouter des membres a un groupe qui a ForceChangePassword sur un autre compte; un utilisateur compromis est ajoute au groupe puis le mot de passe cible est change."
---
# Zephyr - zsm.local - Abus chaine de groupes pour reset mot de passe

## Chain Summary

- One-line chain: Un compte machine compromis peut ajouter des membres a un groupe qui a ForceChangePassword sur un autre compte; un utilisateur compromis est ajoute au groupe puis le mot de passe cible est change.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Add-DomainGroupMember confirme l'ajout; Set-DomainUserPassword confirme le reset.

## Escalation Order

1. Purge des tickets en exces.
2. Add-DomainGroupMember sur le groupe cible (via le ticket du compte machine compromis).
3. Set-DomainUserPassword sur le compte cible.
4. Connexion au compte cible -> acces admin.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Les chaines de groupes imbriquees avec droits sur mot de passe sont communes dans un AD mal configure; toujours suivre la chaine complete d'edges BloodHound jusqu'au bout.
```

## Related Writeups

- zephyr-zsm-local-group-chain-password-reset

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
