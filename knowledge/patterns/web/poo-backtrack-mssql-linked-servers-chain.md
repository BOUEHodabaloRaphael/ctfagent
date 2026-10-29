---
doc_kind: pattern
title: "Chainage de linked servers MSSQL jusqu'a sa"
category: web
slug: poo-backtrack-mssql-linked-servers-chain
created: 2026-10-29
status: active
tags:
  - mssql
  - linked-servers
  - xp_cmdshell
  - privilege-chaining
  - sql-pivot
chain_summary: "Des linked servers MSSQL imbriques (EXECUTE AT) peuvent etre chaines recursivement pour escalader depuis un compte faible jusqu'au contexte sa sur une instance distante."
---
# Chainage de linked servers MSSQL jusqu'a sa

## Chain Summary

- One-line chain: Des linked servers MSSQL imbriques (EXECUTE AT) peuvent etre chaines recursivement pour escalader depuis un compte faible jusqu'au contexte sa sur une instance distante.
- Typical target shape: Acces a une instance MSSQL avec un compte limite; sp_linkedservers liste au moins un lien.

## Preconditions

- Acces a une instance MSSQL avec un compte limite; sp_linkedservers liste au moins un lien.

## Cheap Probes

- EXEC sp_linkedservers; puis EXECUTE('select SUSER_NAME()') at [chaque lien] pour voir le contexte obtenu a chaque niveau.

## Telltale Evidence

- Le contexte utilisateur change (et s'eleve) a chaque niveau de chainage EXECUTE AT.

## Escalation Order

1. Lister les linked servers disponibles.
2. Tester le contexte utilisateur obtenu sur chaque lien individuellement.
3. Chainer les EXECUTE AT de maniere imbriquee si un premier niveau ne donne pas encore sa.
4. Une fois sa, activer xp_cmdshell pour RCE.

## Common Mistakes

- S'arreter au premier niveau de linked server sans tester un chainage imbrique plus profond.

## Payload Shapes

```text
EXECUTE('EXECUTE(''select SUSER_NAME()'') at [LS2]') at [LS1]
```

## Related Writeups

- poo-backtrack-mssql-linked-servers-chain

## Skill Impact

- Related skill: web-triage (MSSQL): ajouter le chainage recursif de linked servers comme etape systematique avant de conclure a une impasse sur un compte SQL limite.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
