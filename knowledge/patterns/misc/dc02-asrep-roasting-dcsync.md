---
doc_kind: pattern
title: "DANTE DC02 - AS-REP Roasting puis DCSync administrateur"
category: misc
slug: dc02-asrep-roasting-dcsync
created: 2026-10-29
status: active
tags:
  - asrep-roasting
  - dcsync
  - pass-the-hash
  - kerberos
  - secretsdump
chain_summary: "Un compte a la pre-authentification Kerberos desactivee (AS-REP roasting), menant a un acces utilisateur qui dispose des droits de replication pour un DCSync recuperant le hash NT administrateur."
---
# DANTE DC02 - AS-REP Roasting puis DCSync administrateur

## Chain Summary

- One-line chain: Un compte a la pre-authentification Kerberos desactivee (AS-REP roasting), menant a un acces utilisateur qui dispose des droits de replication pour un DCSync recuperant le hash NT administrateur.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Hash NT administrateur recupere via secretsdump (-just-dc-user); session SYSTEM obtenue par psexec -hashes.

## Escalation Order

1. Password spray/credential test -> premier acces utilisateur confirme.
2. impacket-GetNPUsers -> compte avec preauth desactivee -> hash AS-REP cracke.
3. secretsdump.py -just-dc-user administrator -> hash NT administrateur (DCSync).
4. psexec.py -hashes <NT> (pass-the-hash) -> flag admin, pivot.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
AS-REP roasting sur compte sans preauth + droits de replication (DCSync) = chemin direct vers hash administrateur sans toucher LSASS du DC; reutiliser le hash en pass-the-hash sur toute machine du domaine.
```

## Related Writeups

- dc02-asrep-roasting-dcsync

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
