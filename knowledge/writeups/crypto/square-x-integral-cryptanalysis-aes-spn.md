---
doc_kind: writeup
title: "SQUARE-X MotHERfUCKER (Crypto, Hard)"
category: crypto
slug: square-x-integral-cryptanalysis-aes-spn
created: 2026-10-29
status: solved
tags:
  - crypto
  - square-attack
  - integral-cryptanalysis
  - spn
  - chosen-plaintext
  - aes-like
source: "ESIG TECH ARENA CTF"
target: "SPN maison façon AES, 4 rounds, oracle chosen-plaintext TCP"
---
# SQUARE-X MotHERfUCKER (Crypto, Hard)

## Challenge Summary

- Source: ESIG TECH ARENA CTF
- Target: SPN maison façon AES, 4 rounds, oracle chosen-plaintext TCP
- Goal: Chiffre SPN maison (4 rounds, dernier round sans MixColumns) avec oracle chosen-plaintext, casse par l'attaque Square (cryptanalyse integrale).

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Lecture du spec cipher.py : S-box/MDS generees deterministiquement par seed publique (connues), seule la cle maitre 128 bits secrete.
2. Reconnaissance de la structure visee par Square (dernier round sans MixColumns), confirmee par le nom du challenge.
3. Construction de 3 Lambda-sets (256 clairs identiques sur 15 octets, 1 octet variable) ; apres 3 rounds chaque octet devient 'balanced'.
4. Validation offline de l'attaque contre cipher.py avec cle aleatoire avant tout appel reseau.
5. Envoi de 768 requetes chosen-plaintext a l'oracle TCP, recuperation octet par octet de la derniere round-key.
6. Inversion deterministe du key schedule jusqu'a la cle maitre.
7. Dechiffrement du flag (attention au format hex-texte du ciphertext fourni, pas binaire brut).

## Key Evidence

- Offline "RK4 recupere == RK4 attendu, master recupere == master attendu" ; reseau "RK4 = 37cba322... / MASTER KEY = 7a1fc403..." ; flag EthACTF{squ4r3_1nt3gr4l_n0_h1nts_ju5t_think_h4rd}.

## Dead Ends

- Oracle reseau d'abord indisponible (port filtre) - script prepare a l'avance, relance periodique necessaire.

## Payloads And Commands

```text
Blocs 16 octets chosen-plaintext hex (Lambda-set structure, 15 octets fixes + 1 variable 0-255).
```

## Flag / Outcome

- EthACTF{squ4r3_1nt3gr4l_n0_h1nts_ju5t_think_h4rd}

## Reusable Lessons

- Attaque Square/cryptanalyse integrale generique pour tout SPN maison a 4 rounds dont le dernier round omet MixColumns, meme avec constantes personnalisees. Toujours valider l'exploit offline avant de consommer le budget reseau.

## Pattern Candidates

- Nouveau pattern: square-attack-4round-spn
