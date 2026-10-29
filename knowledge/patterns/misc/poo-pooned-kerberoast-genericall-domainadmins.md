---
doc_kind: pattern
title: "ModifyRequest LDAP brut quand PowerView/ADWS est injoignable"
category: misc
slug: poo-pooned-kerberoast-genericall-domainadmins
created: 2026-10-29
status: active
tags:
  - kerberoasting
  - genericall
  - ldap-modify
  - sddl
  - domain-admins
  - powerview-bypass
chain_summary: "Quand ADWS (port 9389) est bloque reseau et que PowerView ne fonctionne donc pas, un ModifyRequest LDAP brut (System.DirectoryServices.Protocols) reproduit les memes abus GenericAll/WriteDacl sans dependance a ADWS."
---
# ModifyRequest LDAP brut quand PowerView/ADWS est injoignable

## Chain Summary

- One-line chain: Quand ADWS (port 9389) est bloque reseau et que PowerView ne fonctionne donc pas, un ModifyRequest LDAP brut (System.DirectoryServices.Protocols) reproduit les memes abus GenericAll/WriteDacl sans dependance a ADWS.
- Typical target shape: GenericAll ou WriteDacl confirme via lecture SDDL sur un objet AD sensible (groupe, utilisateur); ADWS injoignable (meme si un test de connexion TCP donne un faux positif de disponibilite).

## Preconditions

- GenericAll ou WriteDacl confirme via lecture SDDL sur un objet AD sensible (groupe, utilisateur); ADWS injoignable (meme si un test de connexion TCP donne un faux positif de disponibilite).

## Cheap Probes

- Lire le SDDL d'un objet sensible (groupe Domain Admins, compte critique) et comparer les SID des ACE aux groupes dont on est membre ou qu'on controle.

## Telltale Evidence

- Une ACE du SDDL correspond a un SID qu'on controle directement ou indirectement, avec un droit GenericAll/WriteDacl/WriteProperty.

## Escalation Order

1. Lire le SDDL de l'objet cible pour confirmer le droit exploitable.
2. Si l'outillage standard (PowerView) est bloque reseau, ecrire un ModifyRequest LDAP brut via le binding .NET/Python disponible.
3. Executer la modification (ajout de membre, changement d'attribut) directement en LDAP.

## Common Mistakes

- Abandonner un abus GenericAll/WriteDacl confirme juste parce que l'outil habituel (PowerView, necessitant ADWS) ne fonctionne pas sur ce segment reseau.

## Payload Shapes

```text
DirectoryAttributeModification { Name='member', Operation=Add, Value=<DN du compte> } via LdapConnection.SendRequest(ModifyRequest)
```

## Related Writeups

- poo-pooned-kerberoast-genericall-domainadmins

## Skill Impact

- Related skill: pwn-triage/AD: ajouter le fallback ModifyRequest LDAP brut comme alternative a PowerView quand ADWS est injoignable.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
