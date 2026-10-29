---
doc_kind: pattern
title: "Zephyr - zsm.local - Pivot via linked SQL server vers un second domaine"
category: pwn
slug: zephyr-zsm-local-linked-server-pivot-internal
created: 2026-10-29
status: active
tags:
  - mssql
  - linked-server
  - cross-domain-pivot
  - sweetpotato
chain_summary: "sp_linkedservers revele un lien vers un serveur SQL d'un second domaine; les requetes sont executees a distance via EXECUTE AT, permettant de repeter la chaine xp_cmdshell+SweetPotato sur ce second serveur."
---
# Zephyr - zsm.local - Pivot via linked SQL server vers un second domaine

## Chain Summary

- One-line chain: sp_linkedservers revele un lien vers un serveur SQL d'un second domaine; les requetes sont executees a distance via EXECUTE AT, permettant de repeter la chaine xp_cmdshell+SweetPotato sur ce second serveur.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- sp_linkedservers listing; whoami output confirmant le changement de domaine.

## Escalation Order

1. EXEC sp_linkedservers -> second serveur decouvert.
2. EXECUTE AS LOGIN='sa'; EXECUTE('select @@servername;') at [linked_server] confirme le pivot.
3. Meme chaine xp_cmdshell via syntaxe linked server.
4. whoami confirme le franchissement vers le 2e domaine.
5. Reverse shell, SeImpersonatePrivilege confirme, SweetPotato -> SYSTEM.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Pivot via serveurs SQL lies (linked servers) est une technique de mouvement lateral/cross-domain sous-estimee, a toujours tester apres un acces sysadmin sur une instance MSSQL.
```

## Related Writeups

- zephyr-zsm-local-linked-server-pivot-internal

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
