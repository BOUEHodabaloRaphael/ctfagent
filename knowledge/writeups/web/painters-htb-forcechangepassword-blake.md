---
doc_kind: writeup
title: "Zephyr - Painters.htb - ForceChangePassword -> BUILTIN\\Administrators"
category: web
slug: painters-htb-forcechangepassword-blake
created: 2026-10-29
status: solved
tags:
  - acl-abuse
  - forcechangepassword
  - powerview
source: "HTB Pro Lab Zephyr"
target: "AD painters.htb, ACL ForceChangePassword"
---
# Zephyr - Painters.htb - ForceChangePassword -> BUILTIN\Administrators

## Challenge Summary

- Source: HTB Pro Lab Zephyr
- Target: AD painters.htb, ACL ForceChangePassword
- Goal: BloodHound montre un droit ForceChangePassword sur un compte membre de BUILTIN\Administrators sur une autre machine; PowerView change le mot de passe pour en prendre le controle.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. BloodHound revele l'edge ForceChangePassword.
2. Set-DomainUserPassword via PowerView -> nouveau mot de passe.
3. Connexion a la machine cible avec le compte -> acces admin confirme.

## Key Evidence

- Set-DomainUserPassword confirme le succes; whoami /groups confirme BUILTIN\Administrators.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
PowerView.ps1 Set-DomainUserPassword.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout (lecture visuelle verifiee).

## Reusable Lessons

- Abus ForceChangePassword ACL classique: toujours verifier a quels groupes/machines le compte cible appartient avant de changer son mot de passe.

## Pattern Candidates

- Voir pattern associe de meme slug.
