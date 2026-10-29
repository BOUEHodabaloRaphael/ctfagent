---
doc_kind: writeup
title: "P.O.O. - p00ned (Kerberoast interne + GenericAll LDAP sur Domain Admins)"
category: misc
slug: poo-pooned-kerberoast-genericall-domainadmins
created: 2026-10-29
status: solved
tags:
  - kerberoasting
  - genericall
  - ldap-modify
  - sddl
  - domain-admins
  - powerview-bypass
source: "HTB Mini Pro Lab P.O.O."
target: "AD interne via contexte MSSQL"
---
# P.O.O. - p00ned (Kerberoast interne + GenericAll LDAP sur Domain Admins)

## Challenge Summary

- Source: HTB Mini Pro Lab P.O.O.
- Target: AD interne via contexte MSSQL
- Goal: Kerberoasting depuis le contexte du service SQL recupere un compte avec SPN; son groupe possede GenericAll sur Domain Admins via SDDL, exploite par un ModifyRequest LDAP brut quand ADWS/PowerView est injoignable.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Rubeus kerberoast via xp_cmdshell depuis le contexte SQL -> hashs TGS.
2. Hashcat -m 13100 (option -O pour contourner une limite RAM) casse un credential.
3. Validation directe par authentification AD plutot que de se fier a un hash potentiellement non casse.
4. Enumeration LDAP .NET revele l'appartenance a un groupe particulier.
5. Lecture SDDL du groupe Domain Admins -> SID du groupe intermediaire possede GenericAll.
6. ADWS (port 9389) injoignable malgre un faux positif de test de connexion -> PowerView impossible.
7. ModifyRequest LDAP brut ajoute le compte casse a Domain Admins -> acces DC -> flag.

## Key Evidence

- GetSecurityDescriptorSddlForm('All') du groupe Domain Admins contient une ACE correspondant au SID du groupe intermediaire = GenericAll.

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
ModifyRequest LDAP (ajout d'attribut member) via System.DirectoryServices.Protocols.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Lire le SDDL d'un objet AD sensible transforme une intuition en preuve exploitable en une requete; si le chemin outille (PowerView/ADWS) est bloque reseau, un ModifyRequest LDAP brut de quelques lignes reproduit le meme abus GenericAll; valider un mot de passe casse par authentification reelle avant de depenser du temps de crack supplementaire.

## Pattern Candidates

- Nouveau pattern: poo-pooned-kerberoast-genericall-domainadmins
