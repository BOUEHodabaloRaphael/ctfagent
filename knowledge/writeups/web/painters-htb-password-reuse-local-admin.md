---
doc_kind: writeup
title: "Zephyr - Painters.htb - Pivot interne + reutilisation mdp en admin local"
category: web
slug: painters-htb-password-reuse-local-admin
created: 2026-10-29
status: solved
tags:
  - lateral-movement
  - password-reuse
  - local-admin
  - cme
source: "HTB Pro Lab Zephyr"
target: "Reseau interne painters.htb"
---
# Zephyr - Painters.htb - Pivot interne + reutilisation mdp en admin local

## Challenge Summary

- Source: HTB Pro Lab Zephyr
- Target: Reseau interne painters.htb
- Goal: Le mot de passe du foothold est reutilise via spray WinRM sur toutes les machines internes; succes sur une machine ou le compte est admin local (bien que non-admin domaine).

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Pivot vers le reseau interne, upload nmap statique, scan.
2. sshuttle pour pivot reseau.
3. cme winrm spray creds sur toutes les machines internes -> succes sur une machine.
4. evil-winrm SANS prefixe domaine -> contexte compte local admin.

## Key Evidence

- cme winrm output confirmant Pwn3d!; whoami /groups confirme Administrators local.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
crackmapexec winrm spray, evil-winrm, sshuttle.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout (lecture visuelle verifiee).

## Reusable Lessons

- Toujours tester un compte domaine comme compte LOCAL (sans prefixe domaine) sur les differentes machines, car les droits different souvent.

## Pattern Candidates

- Voir pattern associe de meme slug.
