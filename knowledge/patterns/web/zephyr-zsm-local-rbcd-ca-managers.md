---
doc_kind: pattern
title: "Zephyr - zsm.local - GenericAll CA Managers -> RBCD -> impersonation Administrator"
category: web
slug: zephyr-zsm-local-rbcd-ca-managers
created: 2026-10-29
status: active
tags:
  - rbcd
  - resource-based-constrained-delegation
  - powermad
  - rubeus
  - generic-all
  - rdp-pivot
chain_summary: "Un compte a GenericAll sur le groupe CA Managers (bloque via ACL non-RDP, necessite session interactive). Ajout au groupe puis attaque RBCD complete: compte machine rogue, ACE de delegation, puis S4U pour impersonner Administrator."
---
# Zephyr - zsm.local - GenericAll CA Managers -> RBCD -> impersonation Administrator

## Chain Summary

- One-line chain: Un compte a GenericAll sur le groupe CA Managers (bloque via ACL non-RDP, necessite session interactive). Ajout au groupe puis attaque RBCD complete: compte machine rogue, ACE de delegation, puis S4U pour impersonner Administrator.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- New-MachineAccount confirme la creation; Rubeus confirme le S4U2proxy success; klist montre le ticket administrator pour le service cifs.

## Escalation Order

1. Activer RDP, pivot proxychains+remmina.
2. Via RDP (contourne la restriction ACL non-interactive): Add-DomainGroupMember sur CA Managers -> succes.
3. Powermad New-MachineAccount cree un compte machine rogue.
4. Construire un descripteur de securite avec le SID du nouveau compte.
5. Set-DomainObject msDS-AllowedToActOnBehalfOfOtherIdentity sur le serveur cible.
6. Rubeus hash (RC4) du compte rogue.
7. Rubeus s4u /user:<rogue>$ /impersonateuser:administrator /altservice:cifs /ptt.
8. Acces complet au serveur cible avec le ticket impersonifie.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
RBCD complet (GenericAll/Write sur ordinateur cible, creation compte rogue, s4u2proxy) est une technique AD cle tres reutilisable, meme quand une restriction ACL bloque l'action en non-interactif (passer par RDP la contourne).
```

## Related Writeups

- zephyr-zsm-local-rbcd-ca-managers

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
