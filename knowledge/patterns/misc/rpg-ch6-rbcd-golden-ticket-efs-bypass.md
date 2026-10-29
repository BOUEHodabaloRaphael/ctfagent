---
doc_kind: pattern
title: "EFS resiste a SYSTEM/Golden Ticket: necessite un vrai contexte utilisateur authentifie"
category: misc
slug: rpg-ch6-rbcd-golden-ticket-efs-bypass
created: 2026-10-29
status: active
tags:
  - rbcd
  - golden-ticket
  - dcsync
  - efs-bypass
  - drsuapi
  - impacket-chain
chain_summary: "Un fichier protege par EFS (certificat utilisateur) reste illisible meme avec un acces SYSTEM ou un Golden Ticket; il faut obtenir un vrai TGT Kerberos pour ce compte (ex: via changement de mot de passe + getTGT) et executer en contexte utilisateur authentifie (wmiexec, pas atexec/psexec)."
---
# EFS resiste a SYSTEM/Golden Ticket: necessite un vrai contexte utilisateur authentifie

## Chain Summary

- One-line chain: Un fichier protege par EFS (certificat utilisateur) reste illisible meme avec un acces SYSTEM ou un Golden Ticket; il faut obtenir un vrai TGT Kerberos pour ce compte (ex: via changement de mot de passe + getTGT) et executer en contexte utilisateur authentifie (wmiexec, pas atexec/psexec).
- Typical target shape: Fichier/dossier chiffre EFS appartenant a un utilisateur specifique; acces SYSTEM ou Golden Ticket deja obtenu sur le domaine mais acces au fichier refuse.

## Preconditions

- Fichier/dossier chiffre EFS appartenant a un utilisateur specifique; acces SYSTEM ou Golden Ticket deja obtenu sur le domaine mais acces au fichier refuse.

## Cheap Probes

- Tenter une lecture du fichier EFS avec l'acces SYSTEM/Golden Ticket courant -> observer le refus d'acces malgre les privileges eleves.

## Telltale Evidence

- Acces refuse sur le fichier EFS malgre uid SYSTEM ou Golden Ticket valide pour le domaine.

## Escalation Order

1. Confirmer que le refus est specifiquement lie a EFS (pas un ACL NTFS classique).
2. Changer le mot de passe du compte proprietaire via le Golden Ticket/privileges DA.
3. Obtenir un vrai TGT Kerberos pour ce compte (getTGT.py ou equivalent) avec le nouveau mot de passe.
4. Executer la lecture en contexte utilisateur authentifie reel (wmiexec avec le ticket, pas atexec/psexec qui utilisent un contexte different).

## Common Mistakes

- Supposer que SYSTEM ou un Golden Ticket suffit a tout, y compris EFS, qui depend specifiquement d'un contexte d'authentification utilisateur reel.

## Payload Shapes

```text
getTGT.py domain/user:newpassword ; wmiexec.py -k -no-pass domain/user@target
```

## Related Writeups

- rpg-ch6-rbcd-golden-ticket-efs-bypass

## Skill Impact

- Related skill: pwn-triage/AD: ajouter 'EFS necessite contexte utilisateur reel, pas SYSTEM/golden ticket seul' comme piege connu en fin de chaine AD.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
