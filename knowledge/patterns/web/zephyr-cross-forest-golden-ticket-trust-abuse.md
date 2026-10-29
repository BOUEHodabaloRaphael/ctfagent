---
doc_kind: pattern
title: "Zephyr - Abus de trust parent/enfant via Golden Ticket inter-royaume"
category: web
slug: zephyr-cross-forest-golden-ticket-trust-abuse
created: 2026-10-29
status: active
tags:
  - cross-domain
  - golden-ticket
  - trust-abuse
  - sid-history
  - mimikatz
  - rubeus
  - enterprise-admins
chain_summary: "Etant Domain Admin sur le domaine enfant, abus du trust parent/enfant pour compromettre le domaine parent: extraction de la cle de trust via mimikatz, puis forge d'un Golden Ticket avec extra SID Enterprise Admins du parent."
---
# Zephyr - Abus de trust parent/enfant via Golden Ticket inter-royaume

## Chain Summary

- One-line chain: Etant Domain Admin sur le domaine enfant, abus du trust parent/enfant pour compromettre le domaine parent: extraction de la cle de trust via mimikatz, puis forge d'un Golden Ticket avec extra SID Enterprise Admins du parent.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- mimikatz lsadump::trust confirme les SIDs et la cle de trust; Rubeus confirme le TGS request successful.

## Escalation Order

1. Upload des outils sur le DC enfant (deja admin).
2. mimikatz lsadump::trust /patch -> SID enfant+parent + cle de trust RC4.
3. mimikatz kerberos::golden avec l'extra SID Enterprise Admins du parent, service krbtgt, cible le domaine parent.
4. Rubeus.exe asktgs avec ce ticket vers le service CIFS du DC parent.
5. Acces complet au partage C$ du DC parent avec le ticket inter-royaume administrateur.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Technique classique d'abus de trust parent/enfant via extra SID history (SID Enterprise Admins) pour sauter de domaine enfant a domaine parent dans une foret AD.
```

## Related Writeups

- zephyr-cross-forest-golden-ticket-trust-abuse

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
