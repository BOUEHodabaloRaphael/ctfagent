---
doc_kind: pattern
title: "Password spray cible sur comptes de service *-svc apres un premier credential"
category: misc
slug: xen-doppelganger-bloodhound-password-spray
created: 2026-10-29
status: active
tags:
  - bloodhound
  - password-spray
  - service-accounts
  - rdp
  - ad-recon
chain_summary: "Les comptes de service partagent frequemment le meme mot de passe; sprayer ce mot de passe sur tous les comptes *-svc connus via BloodHound, puis chercher lequel a un edge d'acces exploitable (RDP/AdminTo)."
---
# Password spray cible sur comptes de service *-svc apres un premier credential

## Chain Summary

- One-line chain: Les comptes de service partagent frequemment le meme mot de passe; sprayer ce mot de passe sur tous les comptes *-svc connus via BloodHound, puis chercher lequel a un edge d'acces exploitable (RDP/AdminTo).
- Typical target shape: Un credential de compte de service deja obtenu; BloodHound/SharpHound deja collecte ou collectable, listant plusieurs comptes *-svc similaires.

## Preconditions

- Un credential de compte de service deja obtenu; BloodHound/SharpHound deja collecte ou collectable, listant plusieurs comptes *-svc similaires.

## Cheap Probes

- crackmapexec smb -u <liste *-svc> -p <mdp connu> --continue-on-success.

## Telltale Evidence

- Plusieurs comptes acceptent le meme mot de passe simultanement.

## Escalation Order

1. Lister tous les comptes de service via BloodHound/LDAP.
2. Sprayer le mot de passe deja connu sur cette liste.
3. Pour chaque compte valide, verifier dans BloodHound ses edges d'acces (RDP, AdminTo, GenericAll).
4. Utiliser le compte avec l'edge le plus direct vers la cible finale.

## Common Mistakes

- S'arreter au premier compte de service compromis sans sprayer son mot de passe sur les comptes similaires.

## Payload Shapes

```text
crackmapexec smb <dc> -u svc_accounts.txt -p '<password>' --continue-on-success
```

## Related Writeups

- xen-doppelganger-bloodhound-password-spray

## Skill Impact

- Related skill: pwn-triage/AD: ajouter le password-spray cible sur comptes *-svc comme etape systematique apres un premier credential de service.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
