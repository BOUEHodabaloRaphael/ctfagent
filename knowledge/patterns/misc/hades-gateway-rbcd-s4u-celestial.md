---
doc_kind: pattern
title: "RBCD via compte de service avec GenericAll + MachineAccountQuota disponible"
category: misc
slug: hades-gateway-rbcd-s4u-celestial
created: 2026-10-29
status: active
tags:
  - rbcd
  - s4u2proxy
  - machineaccountquota
  - genericall-computer
  - dpapi-service-account
chain_summary: "GenericAll/WriteDacl sur un objet ordinateur combine a un MachineAccountQuota non nul permet de creer un compte machine factice et d'ecrire une delegation RBCD, forgeant ensuite un ticket S4U2Proxy impersonnant n'importe quel utilisateur sur cette machine."
---
# RBCD via compte de service avec GenericAll + MachineAccountQuota disponible

## Chain Summary

- One-line chain: GenericAll/WriteDacl sur un objet ordinateur combine a un MachineAccountQuota non nul permet de creer un compte machine factice et d'ecrire une delegation RBCD, forgeant ensuite un ticket S4U2Proxy impersonnant n'importe quel utilisateur sur cette machine.
- Typical target shape: Un compte controle (meme non-admin) possede GenericAll/WriteDacl sur l'objet ordinateur cible; ms-DS-MachineAccountQuota du domaine est superieur a 0.

## Preconditions

- Un compte controle (meme non-admin) possede GenericAll/WriteDacl sur l'objet ordinateur cible; ms-DS-MachineAccountQuota du domaine est superieur a 0.

## Cheap Probes

- Verifier les droits ACL sur l'objet ordinateur cible et la valeur de MachineAccountQuota.

## Telltale Evidence

- GenericAll/WriteDacl confirme via BloodHound/dsacls; MachineAccountQuota>0 confirme via LDAP.

## Escalation Order

1. Confirmer GenericAll/WriteDacl sur l'objet ordinateur cible.
2. Creer un compte machine factice (addcomputer).
3. Ecrire la delegation RBCD depuis ce compte factice vers la cible (setrbcd write).
4. Forger un ticket S4U2Self puis S4U2Proxy impersonnant l'utilisateur cible (ex: administrator).
5. Utiliser ce ticket pour executer des commandes/lire des ressources sur la machine cible, reutilisable pour plusieurs acces sans repeter la chaine.

## Common Mistakes

- Chercher une autre voie de privesc alors qu'un GenericAll/WriteDacl deja identifie sur un objet ordinateur avec quota machine disponible suffit pour un RBCD complet.

## Payload Shapes

```text
addcomputer.py -computer-name 'FAKE01$' -computer-pass 'Passw0rd!' domain/user:pass  puis  setrbcd.py -delegate-to TARGET$ -delegate-from FAKE01$ -action write
```

## Related Writeups

- hades-gateway-rbcd-s4u-celestial

## Skill Impact

- Related skill: pwn-triage/AD: ajouter GenericAll/WriteDacl sur objet ordinateur + MachineAccountQuota comme chemin RBCD systematique a tester.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
