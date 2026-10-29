---
doc_kind: pattern
title: "Reutilisation de mot de passe contre un compte Protected Users via Kerberos pur"
category: misc
slug: hades-dominion-password-reuse-protected-users
created: 2026-10-29
status: active
tags:
  - protected-users
  - kerberos-only
  - password-reuse
  - clock-skew
  - domain-admin
chain_summary: "Protected Users bloque NTLM/pass-the-hash mais pas une authentification Kerberos par mot de passe correct; un mot de passe local decouvert ailleurs vaut la peine d'etre retest via Kerberos (getTGT) contre ce compte, apres avoir verifie la synchronisation d'horloge."
---
# Reutilisation de mot de passe contre un compte Protected Users via Kerberos pur

## Chain Summary

- One-line chain: Protected Users bloque NTLM/pass-the-hash mais pas une authentification Kerberos par mot de passe correct; un mot de passe local decouvert ailleurs vaut la peine d'etre retest via Kerberos (getTGT) contre ce compte, apres avoir verifie la synchronisation d'horloge.
- Typical target shape: Compte cible membre de Protected Users; un mot de passe potentiellement reutilise est connu (ex: admin local d'une autre machine).

## Preconditions

- Compte cible membre de Protected Users; un mot de passe potentiellement reutilise est connu (ex: admin local d'une autre machine).

## Cheap Probes

- impacket-getTGT avec le mot de passe candidat; si echec immediat sans raison claire, verifier le clock skew avant de conclure a un mauvais mot de passe.

## Telltale Evidence

- getTGT reussit et produit un ccache valide.

## Escalation Order

1. Identifier qu'un compte cible est dans Protected Users (NTLM/PtH inutiles).
2. Tester tout mot de passe local decouvert ailleurs comme credential de ce compte via Kerberos pur (getTGT), pas via NTLM.
3. Si l'authentification Kerberos echoue de maniere suspecte, synchroniser l'horloge avant de conclure a un mauvais mot de passe.
4. Utiliser le TGT obtenu pour acceder aux ressources cibles.

## Common Mistakes

- Tenter pass-the-hash/NTLM contre un compte Protected Users (bloque par design) au lieu de Kerberos pur; attribuer un echec Kerberos a un mauvais mot de passe sans verifier le clock skew.

## Payload Shapes

```text
getTGT.py domain/administrator:<password-reuse-candidate>
```

## Related Writeups

- hades-dominion-password-reuse-protected-users

## Skill Impact

- Related skill: pwn-triage/AD: ajouter le rappel Protected Users = Kerberos pur uniquement, et verification de clock skew avant d'exclure un mot de passe candidat.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
