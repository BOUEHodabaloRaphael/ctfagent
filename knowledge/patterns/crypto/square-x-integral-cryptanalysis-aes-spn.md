---
doc_kind: pattern
title: "Attaque Square sur SPN maison 4 rounds sans MixColumns au dernier tour"
category: crypto
slug: square-x-integral-cryptanalysis-aes-spn
created: 2026-10-29
status: active
tags:
  - crypto
  - square-attack
  - integral-cryptanalysis
  - spn
  - chosen-plaintext
  - aes-like
chain_summary: "SPN type AES avec 4 rounds et dernier round sans MixColumns = casse par attaque Square (cryptanalyse integrale) via Lambda-sets, meme avec S-box/MDS personnalisees connues."
---
# Attaque Square sur SPN maison 4 rounds sans MixColumns au dernier tour

## Chain Summary

- One-line chain: SPN type AES avec 4 rounds et dernier round sans MixColumns = casse par attaque Square (cryptanalyse integrale) via Lambda-sets, meme avec S-box/MDS personnalisees connues.
- Typical target shape: Chiffre par blocs type AES/SPN avec un nombre reduit de rounds (souvent 4-5) et un oracle chosen-plaintext accessible; verifier si le dernier round omet une diffusion complete (MixColumns).

## Preconditions

- Chiffre par blocs type AES/SPN avec un nombre reduit de rounds (souvent 4-5) et un oracle chosen-plaintext accessible; verifier si le dernier round omet une diffusion complete (MixColumns).

## Cheap Probes

- Lire le spec/code du chiffre pour confirmer le nombre de rounds et la structure du dernier round; verifier si S-box/MDS sont personnalisees mais deterministes/connues (seed publique).

## Telltale Evidence

- Les octets d'un Lambda-set (256 clairs variant sur 1 octet) deviennent 'balanced' (XOR=0) apres propagation sur le nombre de rounds attaquable.

## Escalation Order

1. Construire des Lambda-sets (256 textes clairs identiques sauf 1 octet variable 0-255).
2. Valider l'attaque offline avec une cle connue avant d'utiliser le budget de requetes reseau.
3. Recuperer la derniere round-key octet par octet via la propriete balanced.
4. Inverser le key schedule pour obtenir la cle maitre.

## Common Mistakes

- Lancer l'attaque directement sur le reseau sans validation offline; oublier un format d'encodage (hex vs binaire brut) sur le ciphertext final.

## Payload Shapes

```text
16 bytes blocks, 15 fixed + 1 varying 0..255, sent hex-encoded to the oracle
```

## Related Writeups

- square-x-integral-cryptanalysis-aes-spn

## Skill Impact

- Related skill: Pertinent pour un futur crypto-triage; ajouter 'verifier structure SPN reduite (rounds, derniere diffusion)' comme heuristique de reconnaissance.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
