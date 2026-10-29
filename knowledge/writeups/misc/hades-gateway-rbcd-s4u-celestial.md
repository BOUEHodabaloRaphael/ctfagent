---
doc_kind: writeup
title: "Endgame HADES - Gateway + Celestial (RBCD via compte de service -> S4U2Self/Proxy)"
category: misc
slug: hades-gateway-rbcd-s4u-celestial
created: 2026-10-29
status: solved
tags:
  - rbcd
  - s4u2proxy
  - machineaccountquota
  - genericall-computer
  - dpapi-service-account
source: "HTB Endgame HADES"
target: "Objet ordinateur AD avec GenericAll + MachineAccountQuota"
---
# Endgame HADES - Gateway + Celestial (RBCD via compte de service -> S4U2Self/Proxy)

## Challenge Summary

- Source: HTB Endgame HADES
- Target: Objet ordinateur AD avec GenericAll + MachineAccountQuota
- Goal: Un compte de service recupere via DPAPI possede GenericAll/WriteDacl sur un objet ordinateur; avec un quota de comptes machine disponible, une delegation RBCD est ecrite pour forger un ticket S4U2Proxy impersonnant administrator.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Un compte de service (obtenu via DPAPI) a GenericAll/WriteDacl sur un objet ordinateur cible, et MachineAccountQuota>0 permet de creer un compte machine.
2. impacket-addcomputer cree un compte machine factice avec un mot de passe controle.
3. setrbcd.py ecrit la delegation RBCD depuis ce compte factice vers l'objet ordinateur cible.
4. impacket-getST impersonnant administrator avec le compte factice -> S4U2Self puis S4U2Proxy -> ticket Administrator sur la cible.
5. nxc smb avec ce ticket execute des commandes et lit plusieurs flags sur la meme machine sans repeter l'attaque.

## Key Evidence

- setrbcd.py confirme la modification reussie des droits de delegation avant que getST ne reussisse le S4U2Proxy.

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
chaine RBCD complete (addcomputer -> setrbcd write -> getST S4U2Self/Proxy).
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- GenericAll/WriteDacl sur un objet ordinateur + MachineAccountQuota>0 = RBCD exploitable sans etre admin du domaine; un meme ticket de service force reste valide pour lire plusieurs flags/ressources sur la meme machine sans repeter la chaine.

## Pattern Candidates

- Nouveau pattern: hades-gateway-rbcd-s4u-celestial
