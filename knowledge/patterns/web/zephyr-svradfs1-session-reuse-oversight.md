---
doc_kind: pattern
title: "Zephyr - Acces a une machine oubliee via session admin existante"
category: web
slug: zephyr-svradfs1-session-reuse-oversight
created: 2026-10-29
status: active
tags:
  - ad
  - wrap-up
  - lateral-leftover
  - flag
chain_summary: "Derniere etape du lab: avec un ticket inter-royaume limite, upgrade vers un acces plus complet en changeant le service du ticket, migration vers un process admin deja en session, puis decouverte qu'une machine du scope n'avait jamais ete touchee."
---
# Zephyr - Acces a une machine oubliee via session admin existante

## Chain Summary

- One-line chain: Derniere etape du lab: avec un ticket inter-royaume limite, upgrade vers un acces plus complet en changeant le service du ticket, migration vers un process admin deja en session, puis decouverte qu'une machine du scope n'avait jamais ete touchee.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- klist confirme le ticket Administrator du domaine; flag final lu sur la machine oubliee.

## Escalation Order

1. Rubeus asktgs avec le ticket existant mais vers un service different (permet PS Remoting).
2. Deposer+executer un payload pour un shell SYSTEM.
3. Migration de process vers un process d'un administrateur de domaine deja actif.
4. klist confirme un ticket administrateur legitime.
5. Constat: une machine du scope n'avait jamais ete exploree -> lecture du flag avec le contexte admin courant.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Reflexe general reutilisable: toujours lister et verifier TOUTES les machines du scope avant de considerer un lab/engagement comme termine, meme apres avoir obtenu Domain Admin.
```

## Related Writeups

- zephyr-svradfs1-session-reuse-oversight

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
