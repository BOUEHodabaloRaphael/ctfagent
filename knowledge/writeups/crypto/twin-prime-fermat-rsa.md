---
doc_kind: writeup
title: Twin_Prime
category: crypto
slug: twin-prime-fermat-rsa
created: 2026-10-29
status: solved
tags:
  - crypto
  - rsa
  - fermat-factorization
  - close-primes
  - weak-keygen
source: "ESIG TECH ARENA CTF 2026"
target: "Cle RSA avec p,q tres proches (close-prime)"
---
# Twin_Prime

## Challenge Summary

- Source: ESIG TECH ARENA CTF 2026
- Target: Cle RSA avec p,q tres proches (close-prime)
- Goal: Cle RSA generee avec deux facteurs premiers p et q extremement proches (twin primes), factorisable quasi instantanement par la methode de Fermat.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Dezippage ciphertext.txt (c), public.txt (n, e=65537), server.log (indice 'fenetres de recherche adjacentes').
2. Factorisation de Fermat: a=ceil(sqrt(n)), incrementer jusqu'a a²-n carre parfait b²; p=a-b, q=a+b.
3. Convergence en ~0.04s: p et q (511 bits) ne diffèrent que de 42014.
4. Dechiffrement RSA classique (phi(n), d=e^-1 mod phi(n), m=c^d mod n).

## Key Evidence

- Ecart p/q de 42014 pour des nombres de 511 bits; flag EthACTF{fermats_twins}.

## Dead Ends

- n/a.

## Payloads And Commands

```text
Script Python de factorisation de Fermat + dechiffrement RSA standard.
```

## Flag / Outcome

- EthACTF{fermats_twins}

## Reusable Lessons

- RSA avec p et q proches (close-prime) = factorisable instantanement par la methode de Fermat. Tester Fermat en priorite si indice 'twin'/'close'/'adjacent' primes.

## Pattern Candidates

- Nouveau pattern: rsa-close-prime-fermat-factorization
