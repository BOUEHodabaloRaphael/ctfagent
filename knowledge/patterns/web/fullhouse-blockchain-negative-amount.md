---
doc_kind: pattern
title: "Transaction blockchain a montant negatif creditant un compte (signature cote client non validee serveur)"
category: web
slug: fullhouse-blockchain-negative-amount
created: 2026-10-29
status: active
tags:
  - blockchain
  - business-logic
  - signature-cote-client
  - base64-creds
  - casino
chain_summary: "Une application qui fait confiance a une transaction signee cote client sans valider serverside que le montant est positif permet de forger une transaction a montant negatif pour crediter arbitrairement un solde."
---
# Transaction blockchain a montant negatif creditant un compte (signature cote client non validee serveur)

## Chain Summary

- One-line chain: Une application qui fait confiance a une transaction signee cote client sans valider serverside que le montant est positif permet de forger une transaction a montant negatif pour crediter arbitrairement un solde.
- Typical target shape: Application avec logique financiere/blockchain ou la signature de transaction est generee et verifiee cote client, le serveur ne validant que la signature pas la coherence metier du montant.

## Preconditions

- Application avec logique financiere/blockchain ou la signature de transaction est generee et verifiee cote client, le serveur ne validant que la signature pas la coherence metier du montant.

## Cheap Probes

- Forger une transaction avec un montant negatif, la signer avec la cle client, et observer si le serveur l'accepte et met a jour le solde.

## Telltale Evidence

- Le solde augmente malgre un montant negatif soumis.

## Escalation Order

1. Analyser le format de transaction attendu (cles, champs, signature).
2. Forger une transaction avec un montant negatif respectant ce format.
3. La signer cote client avec la cle appropriee.
4. Soumettre et verifier l'impact sur le solde.

## Common Mistakes

- Supposer qu'une signature cryptographique valide garantit la coherence metier (montant positif) du contenu signe.

## Payload Shapes

```text
{"from":"<addr>","to":"<self>","amount":-1000,"signature":"<client-signed>"}
```

## Related Writeups

- fullhouse-blockchain-negative-amount

## Skill Impact

- Related skill: web-triage (business logic): ajouter le test de valeurs negatives sur toute transaction financiere signee cote client.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
