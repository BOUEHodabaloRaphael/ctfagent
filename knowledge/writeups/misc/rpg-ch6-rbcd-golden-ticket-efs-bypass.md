---
doc_kind: writeup
title: "HTB Endgame RPG — Ch.6 RBCD + Golden Ticket + contournement EFS"
category: misc
slug: rpg-ch6-rbcd-golden-ticket-efs-bypass
created: 2026-10-29
status: solved
tags:
  - rbcd
  - golden-ticket
  - dcsync
  - efs-bypass
  - drsuapi
  - impacket-chain
source: "HackTheBox Endgame RPG"
target: "Active Directory, DC Shinra"
---
# HTB Endgame RPG — Ch.6 RBCD + Golden Ticket + contournement EFS

## Challenge Summary

- Source: HackTheBox Endgame RPG
- Target: Active Directory, DC Shinra
- Goal: Dump LSASS pour obtenir un hash Domain Admin, chaine RBCD via compte machine fabrique, DCSync de krbtgt, Golden Ticket, puis contournement d'un chiffrement EFS en obtenant un vrai TGT Kerberos (pas un contexte SYSTEM).

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Dump LSASS (mimikatz) -> hash NTLM du Domain Admin.
2. Creation d'un compte machine arbitraire via addcomputer.py.
3. Attribution du droit RBCD sur l'objet ordinateur du DC au compte machine fabrique via rbcd.py.
4. Ticket de service impersonne (S4U) pour le DC via getST.py.
5. atexec refuse (acces refuse pour compte machine) -> contournement via DRSUAPI sur ports RPC dynamiques (via tunnel SOCKS).
6. DCSync de krbtgt via secretsdump.py.
7. Golden Ticket (ticketer.py) -> shell SYSTEM/DA via wmiexec.
8. Flag protege EFS (certificat du vrai Administrator) -> acces refuse meme en SYSTEM/golden ticket.
9. Changement du mot de passe Administrator via Golden Ticket, obtention d'un vrai TGT (getTGT.py), puis wmiexec en contexte utilisateur authentifie pour lire le fichier EFS.

## Key Evidence

- "secretsdump.py -> krbtgt NT hash recupere"; "impacket-wmiexec -k -no-pass ... type flag.txt" apres TGT reel -> flag lu.

## Dead Ends

- atexec et psexec refuses meme avec Golden Ticket sur le fichier EFS - SYSTEM/golden ticket ne suffit pas pour dechiffrer EFS, il faut un contexte utilisateur authentifie reel.

## Payloads And Commands

```text
Chaine RBCD impacket (addcomputer.py+rbcd.py+getST.py) puis Golden Ticket (ticketer.py) puis TGT reel (getTGT.py) + wmiexec contexte utilisateur.
```

## Flag / Outcome

- Flag lu apres contournement EFS.

## Reusable Lessons

- Double pattern : (1) RBCD via compte machine fabrique pour acces DA sans mot de passe en clair du DA ; (2) un fichier protege EFS echoue meme en SYSTEM/Golden-Ticket, il faut un contexte utilisateur authentifie reel (changer le mot de passe + TGT + wmiexec, pas atexec/psexec).

## Pattern Candidates

- Nouveau pattern: efs-requires-real-user-context + rbcd-fake-machine-account
