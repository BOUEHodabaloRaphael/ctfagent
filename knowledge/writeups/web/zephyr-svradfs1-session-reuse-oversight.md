---
doc_kind: writeup
title: "Zephyr - Acces a une machine oubliee via session admin existante"
category: web
slug: zephyr-svradfs1-session-reuse-oversight
created: 2026-10-29
status: solved
tags:
  - ad
  - wrap-up
  - lateral-leftover
  - flag
source: "HTB Pro Lab Zephyr"
target: "Machine jamais explorer dans le scope du lab"
---
# Zephyr - Acces a une machine oubliee via session admin existante

## Challenge Summary

- Source: HTB Pro Lab Zephyr
- Target: Machine jamais explorer dans le scope du lab
- Goal: Derniere etape du lab: avec un ticket inter-royaume limite, upgrade vers un acces plus complet en changeant le service du ticket, migration vers un process admin deja en session, puis decouverte qu'une machine du scope n'avait jamais ete touchee.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Rubeus asktgs avec le ticket existant mais vers un service different (permet PS Remoting).
2. Deposer+executer un payload pour un shell SYSTEM.
3. Migration de process vers un process d'un administrateur de domaine deja actif.
4. klist confirme un ticket administrateur legitime.
5. Constat: une machine du scope n'avait jamais ete exploree -> lecture du flag avec le contexte admin courant.

## Key Evidence

- klist confirme le ticket Administrator du domaine; flag final lu sur la machine oubliee.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Rubeus asktgs (changement de service), migration de process, lecture via chemin UNC.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout (lecture visuelle verifiee).

## Reusable Lessons

- Reflexe general reutilisable: toujours lister et verifier TOUTES les machines du scope avant de considerer un lab/engagement comme termine, meme apres avoir obtenu Domain Admin.

## Pattern Candidates

- Voir pattern associe de meme slug.
