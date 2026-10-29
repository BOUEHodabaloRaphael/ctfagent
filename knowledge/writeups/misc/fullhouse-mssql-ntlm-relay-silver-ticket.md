---
doc_kind: writeup
title: "FullHouse - La maison gagne toujours (relais xp_dirtree + silver ticket MSSQL -> Domain Admin)"
category: misc
slug: fullhouse-mssql-ntlm-relay-silver-ticket
created: 2026-10-29
status: solved
tags:
  - xp_dirtree
  - ntlm-coercion
  - silver-ticket
  - mssql-relay
  - xp_cmdshell-potato
source: "HTB Pro Lab FullHouse"
target: "Instance SQL Express du DC"
---
# FullHouse - La maison gagne toujours (relais xp_dirtree + silver ticket MSSQL -> Domain Admin)

## Challenge Summary

- Source: HTB Pro Lab FullHouse
- Target: Instance SQL Express du DC
- Goal: Un utilisateur avec acces a l'instance SQL du DC force le compte de service SQL a s'authentifier vers Responder via xp_dirtree; le hash casse permet de forger un silver ticket impersonnant Administrator directement dans MSSQL.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Tunnel de port local vers le port MSSQL du DC, accessible via proxychains.
2. Connexion MSSQL via le tunnel avec authentification Windows.
3. EXEC xp_dirtree vers un chemin UNC force le service SQL a s'authentifier vers Responder (relaye).
4. Hash NetNTLMv2 du compte de service casse avec une wordlist -> conversion en hash NTLM.
5. impacket-ticketer avec ce hash NTLM, le SID de domaine et un SPN arbitraire forge un silver ticket pour Administrator.
6. Connexion MSSQL avec ce ticket -> contexte Administrator sans casser son vrai mot de passe.
7. Activation de xp_cmdshell puis un Potato -> SYSTEM complet.

## Key Evidence

- SELECT suser_name() renvoie le compte Administrator alors que l'authentification s'est faite uniquement via un silver ticket Kerberos forge.

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
silver ticket Kerberos (impacket-ticketer) forge a partir d'un hash NTLM de compte de service MSSQL.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- xp_dirtree vers un chemin UNC est une coercition NTLM classique contre le compte de service SQL; un silver ticket pour le SPN MSSQL ne necessite que le hash NTLM du compte + SID de domaine, pas d'acces DC, et permet d'impersonner n'importe quel utilisateur directement dans l'app ciblee.

## Pattern Candidates

- Nouveau pattern: fullhouse-mssql-ntlm-relay-silver-ticket
