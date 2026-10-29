---
doc_kind: writeup
title: "DANTE Jenkins/NIX07 - RCE Groovy puis credentials via pspy et groupe disk"
category: web
slug: jenkins-nix07-groovy-rce-pspy-disk-group
created: 2026-10-29
status: solved
tags:
  - jenkins
  - groovy-rce
  - pspy
  - disk-group-privesc
  - credential-sniffing
source: "HTB Pro Lab DANTE"
target: "Jenkins Script Console + groupe disk"
---
# DANTE Jenkins/NIX07 - RCE Groovy puis credentials via pspy et groupe disk

## Challenge Summary

- Source: HTB Pro Lab DANTE
- Target: Jenkins Script Console + groupe disk
- Goal: Jenkins Script Console (Groovy) donne une RCE arbitraire; pspy64 revele un mot de passe en clair d'un process, exploitable car l'utilisateur appartient au groupe disk permettant de lire le disque brut.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Login Jenkins avec creds trouvees.
2. Manage Jenkins -> Script Console -> execute groovy 'cmd'.execute().text -> RCE.
3. Upload/execution pspy64 via la RCE pour surveiller les process.
4. pspy revele des creds en clair dans une commande.
5. L'utilisateur est membre du groupe disk -> lecture disque brut (/dev/sdX) -> extraction de secrets systeme -> flag.

## Key Evidence

- Sortie 'whoami'.execute().text confirmant RCE; pspy64 affichant une commande contenant des creds en clair.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Payload Groovy 'cmd'.execute().text dans Script Console; binaire pspy64 pour monitoring process.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Jenkins Script Console = RCE immediate si accessible; pspy64 pour capter creds de process transitoires; appartenance au groupe disk = acces disque brut equivalent root sur les fichiers.

## Pattern Candidates

- Voir pattern associe de meme slug.
