---
doc_kind: pattern
title: "Zephyr - Painters.htb - mimikatz lsadump::sam + pass-the-hash"
category: web
slug: painters-htb-sam-dump-pth
created: 2026-10-29
status: active
tags:
  - pass-the-hash
  - mimikatz
  - lsadump
  - lateral-movement
chain_summary: "Sur une machine deja SYSTEM, mimikatz dump le SAM local et recupere un hash NTLM, utilise en pass-the-hash sur une autre machine interne."
---
# Zephyr - Painters.htb - mimikatz lsadump::sam + pass-the-hash

## Chain Summary

- One-line chain: Sur une machine deja SYSTEM, mimikatz dump le SAM local et recupere un hash NTLM, utilise en pass-the-hash sur une autre machine interne.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Sortie mimikatz du dump SAM local.

## Escalation Order

1. Upload mimikatz+nc.
2. lsadump::sam -> hash d'un utilisateur local.
3. cme smb hash spray sur les machines internes -> succes.
4. psexec.py avec le hash -> SYSTEM.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Dump SAM local puis pass-the-hash est un pattern standard de mouvement lateral post-SYSTEM.
```

## Related Writeups

- painters-htb-sam-dump-pth

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
