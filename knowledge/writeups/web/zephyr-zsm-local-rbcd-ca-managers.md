---
doc_kind: writeup
title: "Zephyr - zsm.local - GenericAll CA Managers -> RBCD -> impersonation Administrator"
category: web
slug: zephyr-zsm-local-rbcd-ca-managers
created: 2026-10-29
status: solved
tags:
  - rbcd
  - resource-based-constrained-delegation
  - powermad
  - rubeus
  - generic-all
  - rdp-pivot
source: "HTB Pro Lab Zephyr"
target: "Groupe CA Managers + serveur CA"
---
# Zephyr - zsm.local - GenericAll CA Managers -> RBCD -> impersonation Administrator

## Challenge Summary

- Source: HTB Pro Lab Zephyr
- Target: Groupe CA Managers + serveur CA
- Goal: Un compte a GenericAll sur le groupe CA Managers (bloque via ACL non-RDP, necessite session interactive). Ajout au groupe puis attaque RBCD complete: compte machine rogue, ACE de delegation, puis S4U pour impersonner Administrator.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Activer RDP, pivot proxychains+remmina.
2. Via RDP (contourne la restriction ACL non-interactive): Add-DomainGroupMember sur CA Managers -> succes.
3. Powermad New-MachineAccount cree un compte machine rogue.
4. Construire un descripteur de securite avec le SID du nouveau compte.
5. Set-DomainObject msDS-AllowedToActOnBehalfOfOtherIdentity sur le serveur cible.
6. Rubeus hash (RC4) du compte rogue.
7. Rubeus s4u /user:<rogue>$ /impersonateuser:administrator /altservice:cifs /ptt.
8. Acces complet au serveur cible avec le ticket impersonifie.

## Key Evidence

- New-MachineAccount confirme la creation; Rubeus confirme le S4U2proxy success; klist montre le ticket administrator pour le service cifs.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Powermad New-MachineAccount, PowerShell RawSecurityDescriptor ACE, Rubeus hash + s4u.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout (lecture visuelle verifiee).

## Reusable Lessons

- RBCD complet (GenericAll/Write sur ordinateur cible, creation compte rogue, s4u2proxy) est une technique AD cle tres reutilisable, meme quand une restriction ACL bloque l'action en non-interactif (passer par RDP la contourne).

## Pattern Candidates

- Voir pattern associe de meme slug.
