---
doc_kind: pattern
title: "Zephyr - zsm.local - Shadow Credentials (Whisker/Rubeus) sur un compte machine"
category: web
slug: zephyr-zsm-local-shadow-credentials-mgmt1
created: 2026-10-29
status: active
tags:
  - shadow-credentials
  - whisker
  - rubeus
  - pkinit
  - adcs
chain_summary: "BloodHound revele une chaine AddKeyCredentialLink sur un compte machine. Whisker ajoute un Shadow Credential (certificat), puis Rubeus PKINIT obtient un TGT + hash NTLM via U2U."
---
# Zephyr - zsm.local - Shadow Credentials (Whisker/Rubeus) sur un compte machine

## Chain Summary

- One-line chain: BloodHound revele une chaine AddKeyCredentialLink sur un compte machine. Whisker ajoute un Shadow Credential (certificat), puis Rubeus PKINIT obtient un TGT + hash NTLM via U2U.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Whisker confirme l'ajout de l'attribut msDS-KeyCredentialLink; Rubeus confirme le TGT request successful et affiche le hash NTLM.

## Escalation Order

1. BloodHound documente le chemin AddKeyCredentialLink.
2. Migration de process pour contourner UAC.
3. Whisker.exe add /target:<compte machine> genere un certificat.
4. Rubeus.exe asktgt /certificate:... /getcredentials -> NTLM du compte machine.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Shadow Credentials (msDS-KeyCredentialLink) via l'edge AddKeyCredentialLink est une technique moderne tres reutilisable contre comptes machine/utilisateur.
```

## Related Writeups

- zephyr-zsm-local-shadow-credentials-mgmt1

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
