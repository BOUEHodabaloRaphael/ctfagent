---
doc_kind: pattern
title: "Zephyr - Painters.htb - ForceChangePassword -> BUILTIN\\Administrators"
category: web
slug: painters-htb-forcechangepassword-blake
created: 2026-10-29
status: active
tags:
  - acl-abuse
  - forcechangepassword
  - powerview
chain_summary: "BloodHound montre un droit ForceChangePassword sur un compte membre de BUILTIN\\Administrators sur une autre machine; PowerView change le mot de passe pour en prendre le controle."
---
# Zephyr - Painters.htb - ForceChangePassword -> BUILTIN\Administrators

## Chain Summary

- One-line chain: BloodHound montre un droit ForceChangePassword sur un compte membre de BUILTIN\Administrators sur une autre machine; PowerView change le mot de passe pour en prendre le controle.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Set-DomainUserPassword confirme le succes; whoami /groups confirme BUILTIN\Administrators.

## Escalation Order

1. BloodHound revele l'edge ForceChangePassword.
2. Set-DomainUserPassword via PowerView -> nouveau mot de passe.
3. Connexion a la machine cible avec le compte -> acces admin confirme.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Abus ForceChangePassword ACL classique: toujours verifier a quels groupes/machines le compte cible appartient avant de changer son mot de passe.
```

## Related Writeups

- painters-htb-forcechangepassword-blake

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
