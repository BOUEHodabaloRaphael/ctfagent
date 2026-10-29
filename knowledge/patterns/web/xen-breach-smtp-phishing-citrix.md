---
doc_kind: pattern
title: "Phishing SMTP-enumere vers portail Citrix capture par listener brut"
category: web
slug: xen-breach-smtp-phishing-citrix
created: 2026-10-29
status: active
tags:
  - citrix
  - phishing
  - smtp-enum
  - netscaler
  - ad
  - swaks
chain_summary: "smtp-user-enum RCPT TO pour cibler un phishing, lien vers un nc listener qui capture les creds Citrix postees en clair par un bot interne."
---
# Phishing SMTP-enumere vers portail Citrix capture par listener brut

## Chain Summary

- One-line chain: smtp-user-enum RCPT TO pour cibler un phishing, lien vers un nc listener qui capture les creds Citrix postees en clair par un bot interne.
- Typical target shape: SMTP expose permettant RCPT TO enum; portail Citrix/NetScaler accessible; environnement avec automatisation (bot) qui clique les liens recus.

## Preconditions

- SMTP expose permettant RCPT TO enum; portail Citrix/NetScaler accessible; environnement avec automatisation (bot) qui clique les liens recus.

## Cheap Probes

- smtp-user-enum -M RCPT contre une liste de noms/departements courants.

## Telltale Evidence

- Adresses valides confirmees par reponse SMTP differenciee.

## Escalation Order

1. Enumerer les adresses valides via RCPT TO.
2. Construire un email de phishing usurpant une adresse IT credible.
3. Pointer le lien vers un listener nc brut plutot qu'une page de phishing applicative.
4. Recuperer les credentials postes en clair.

## Common Mistakes

- Construire une fausse page de login complexe quand un simple listener nc suffit a capturer un POST en clair.

## Payload Shapes

```text
swaks --to victim@ --from it@ --body 'click: http://attacker/citrix'
```

## Related Writeups

- xen-breach-smtp-phishing-citrix

## Skill Impact

- Related skill: web-triage/AD: ajouter smtp-user-enum + phishing listener brut comme vecteur initial Citrix.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
