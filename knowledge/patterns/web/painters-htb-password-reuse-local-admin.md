---
doc_kind: pattern
title: "Zephyr - Painters.htb - Pivot interne + reutilisation mdp en admin local"
category: web
slug: painters-htb-password-reuse-local-admin
created: 2026-10-29
status: active
tags:
  - lateral-movement
  - password-reuse
  - local-admin
  - cme
chain_summary: "Le mot de passe du foothold est reutilise via spray WinRM sur toutes les machines internes; succes sur une machine ou le compte est admin local (bien que non-admin domaine)."
---
# Zephyr - Painters.htb - Pivot interne + reutilisation mdp en admin local

## Chain Summary

- One-line chain: Le mot de passe du foothold est reutilise via spray WinRM sur toutes les machines internes; succes sur une machine ou le compte est admin local (bien que non-admin domaine).

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- cme winrm output confirmant Pwn3d!; whoami /groups confirme Administrators local.

## Escalation Order

1. Pivot vers le reseau interne, upload nmap statique, scan.
2. sshuttle pour pivot reseau.
3. cme winrm spray creds sur toutes les machines internes -> succes sur une machine.
4. evil-winrm SANS prefixe domaine -> contexte compte local admin.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Toujours tester un compte domaine comme compte LOCAL (sans prefixe domaine) sur les differentes machines, car les droits different souvent.
```

## Related Writeups

- painters-htb-password-reuse-local-admin

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
