---
doc_kind: pattern
title: "Zephyr - Painters.htb - DCSync /history -> mot de passe reutilise -> root sur serveur mail"
category: web
slug: painters-htb-dcsync-history-mail-root
created: 2026-10-29
status: active
tags:
  - dcsync
  - password-history
  - credential-reuse
chain_summary: "Un champ description BloodHound suggere un role admin; DCSync avec /history recupere les anciens mots de passe, reutilises pour se connecter au serveur mail et obtenir root via sudo."
---
# Zephyr - Painters.htb - DCSync /history -> mot de passe reutilise -> root sur serveur mail

## Chain Summary

- One-line chain: Un champ description BloodHound suggere un role admin; DCSync avec /history recupere les anciens mots de passe, reutilises pour se connecter au serveur mail et obtenir root via sudo.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- dcsync /history produit un ancien hash/mot de passe exploitable.

## Escalation Order

1. BloodHound node info -> description interessante sur un compte.
2. mimikatz lsadump::dcsync /user:<compte> /history.
3. Login sur le serveur mail avec les creds historiques.
4. sudo bash -> root.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Toujours verifier les champs description BloodHound + dcsync /history pour recuperer d'anciens mots de passe reutilises ailleurs.
```

## Related Writeups

- painters-htb-dcsync-history-mail-root

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
