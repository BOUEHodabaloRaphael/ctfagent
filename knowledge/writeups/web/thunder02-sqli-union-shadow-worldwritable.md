---
doc_kind: writeup
title: "ThunderCipher Thunder02 - SQLi UNION, craquage SHA256 puis edition directe de /etc/shadow"
category: web
slug: thunder02-sqli-union-shadow-worldwritable
created: 2026-10-29
status: solved
tags:
  - sqli-union
  - sha256-crack
  - shadow-world-writable
  - direct-root-overwrite
source: thundercipher.in/labs
target: "Base SQL + /etc/shadow world-writable"
---
# ThunderCipher Thunder02 - SQLi UNION, craquage SHA256 puis edition directe de /etc/shadow

## Challenge Summary

- Source: thundercipher.in/labs
- Target: Base SQL + /etc/shadow world-writable
- Goal: Une injection SQL UNION exfiltre les hash SHA256 des comptes; un hash cracke donne un acces SSH limite, mais /etc/shadow est world-writable par erreur, permettant d'ecrire directement un nouveau hash root.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Injection UNION SELECT group_concat(username||':'||password) FROM users.
2. john --format=Raw-SHA256 avec wordlist -> credential cracke.
3. ssh avec ce credential -> ls -la /etc/shadow -> world-writable.
4. Script reecrivant la ligne root: avec un nouveau hash connu.
5. su root -> shell root.

## Key Evidence

- Permissions world-writable sur /etc/shadow confirmees par ls -la; su root reussi apres reecriture.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Injection UNION SELECT group_concat; script de reecriture ligne /etc/shadow.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Toujours verifier les permissions effectives de /etc/shadow apres tout acces shell (meme limite): un bit world-writable sur le fichier seul suffit pour une prise de root directe.

## Pattern Candidates

- Voir pattern associe de meme slug.
