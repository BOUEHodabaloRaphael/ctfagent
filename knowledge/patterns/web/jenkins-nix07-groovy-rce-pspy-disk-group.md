---
doc_kind: pattern
title: "DANTE Jenkins/NIX07 - RCE Groovy puis credentials via pspy et groupe disk"
category: web
slug: jenkins-nix07-groovy-rce-pspy-disk-group
created: 2026-10-29
status: active
tags:
  - jenkins
  - groovy-rce
  - pspy
  - disk-group-privesc
  - credential-sniffing
chain_summary: "Jenkins Script Console (Groovy) donne une RCE arbitraire; pspy64 revele un mot de passe en clair d'un process, exploitable car l'utilisateur appartient au groupe disk permettant de lire le disque brut."
---
# DANTE Jenkins/NIX07 - RCE Groovy puis credentials via pspy et groupe disk

## Chain Summary

- One-line chain: Jenkins Script Console (Groovy) donne une RCE arbitraire; pspy64 revele un mot de passe en clair d'un process, exploitable car l'utilisateur appartient au groupe disk permettant de lire le disque brut.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Sortie 'whoami'.execute().text confirmant RCE; pspy64 affichant une commande contenant des creds en clair.

## Escalation Order

1. Login Jenkins avec creds trouvees.
2. Manage Jenkins -> Script Console -> execute groovy 'cmd'.execute().text -> RCE.
3. Upload/execution pspy64 via la RCE pour surveiller les process.
4. pspy revele des creds en clair dans une commande.
5. L'utilisateur est membre du groupe disk -> lecture disque brut (/dev/sdX) -> extraction de secrets systeme -> flag.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
Jenkins Script Console = RCE immediate si accessible; pspy64 pour capter creds de process transitoires; appartenance au groupe disk = acces disque brut equivalent root sur les fichiers.
```

## Related Writeups

- jenkins-nix07-groovy-rce-pspy-disk-group

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
