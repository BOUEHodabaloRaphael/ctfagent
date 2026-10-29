---
doc_kind: pattern
title: "Regles de mutation hashcat avant d'abandonner un crack Kerberoast"
category: misc
slug: xen-ghost-kerberoast-smb-pivot
created: 2026-10-29
status: active
tags:
  - kerberoasting
  - metasploit-autoroute
  - hashcat-rules
  - smb-share
  - proxychains
chain_summary: "Un hash Kerberoast qui resiste a rockyou brut peut ceder avec une regle de mutation (keyboard walks, substitutions) avant de conclure a un echec."
---
# Regles de mutation hashcat avant d'abandonner un crack Kerberoast

## Chain Summary

- One-line chain: Un hash Kerberoast qui resiste a rockyou brut peut ceder avec une regle de mutation (keyboard walks, substitutions) avant de conclure a un echec.
- Typical target shape: Hash TGS Kerberoast obtenu, non casse par une wordlist brute standard.

## Preconditions

- Hash TGS Kerberoast obtenu, non casse par une wordlist brute standard.

## Cheap Probes

- hashcat -m 13100 avec rockyou + une regle de mutation connue (best64, dive.rule) avant d'abandonner.

## Telltale Evidence

- Le hash cede avec une regle appliquee alors que la wordlist brute seule echouait.

## Escalation Order

1. Kerberoaster systematiquement depuis le premier foothold.
2. Tester rockyou brut.
3. Si echec, appliquer des regles de mutation hashcat avant de changer de vecteur.

## Common Mistakes

- Conclure qu'un hash Kerberoast est incassable apres un seul essai de wordlist brute sans regle de mutation.

## Payload Shapes

```text
hashcat -m 13100 hash.txt rockyou.txt -r dive.rule
```

## Related Writeups

- xen-ghost-kerberoast-smb-pivot

## Skill Impact

- Related skill: pwn-triage/AD: ajouter regles de mutation hashcat comme etape systematique avant d'abandonner un crack Kerberoast.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
