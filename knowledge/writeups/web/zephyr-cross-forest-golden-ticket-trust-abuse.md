---
doc_kind: writeup
title: "Zephyr - Abus de trust parent/enfant via Golden Ticket inter-royaume"
category: web
slug: zephyr-cross-forest-golden-ticket-trust-abuse
created: 2026-10-29
status: solved
tags:
  - cross-domain
  - golden-ticket
  - trust-abuse
  - sid-history
  - mimikatz
  - rubeus
  - enterprise-admins
source: "HTB Pro Lab Zephyr"
target: "Trust parent/enfant entre deux domaines AD"
---
# Zephyr - Abus de trust parent/enfant via Golden Ticket inter-royaume

## Challenge Summary

- Source: HTB Pro Lab Zephyr
- Target: Trust parent/enfant entre deux domaines AD
- Goal: Etant Domain Admin sur le domaine enfant, abus du trust parent/enfant pour compromettre le domaine parent: extraction de la cle de trust via mimikatz, puis forge d'un Golden Ticket avec extra SID Enterprise Admins du parent.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Upload des outils sur le DC enfant (deja admin).
2. mimikatz lsadump::trust /patch -> SID enfant+parent + cle de trust RC4.
3. mimikatz kerberos::golden avec l'extra SID Enterprise Admins du parent, service krbtgt, cible le domaine parent.
4. Rubeus.exe asktgs avec ce ticket vers le service CIFS du DC parent.
5. Acces complet au partage C$ du DC parent avec le ticket inter-royaume administrateur.

## Key Evidence

- mimikatz lsadump::trust confirme les SIDs et la cle de trust; Rubeus confirme le TGS request successful.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
mimikatz lsadump::trust /patch, mimikatz kerberos::golden (avec extra SID Enterprise Admins), Rubeus.exe asktgs.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout (lecture visuelle verifiee).

## Reusable Lessons

- Technique classique d'abus de trust parent/enfant via extra SID history (SID Enterprise Admins) pour sauter de domaine enfant a domaine parent dans une foret AD.

## Pattern Candidates

- Voir pattern associe de meme slug.
