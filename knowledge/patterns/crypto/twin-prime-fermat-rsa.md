---
doc_kind: pattern
title: "RSA close-prime factorisable par methode de Fermat"
category: crypto
slug: twin-prime-fermat-rsa
created: 2026-10-29
status: active
tags:
  - crypto
  - rsa
  - fermat-factorization
  - close-primes
  - weak-keygen
chain_summary: "RSA avec p et q proches (meme ordre de grandeur, ecart petit) = factorisable instantanement par la methode de Fermat (a=ceil(sqrt(n)), chercher a²-n carre parfait)."
---
# RSA close-prime factorisable par methode de Fermat

## Chain Summary

- One-line chain: RSA avec p et q proches (meme ordre de grandeur, ecart petit) = factorisable instantanement par la methode de Fermat (a=ceil(sqrt(n)), chercher a²-n carre parfait).
- Typical target shape: Modulus RSA n fourni; indice textuel ou contextuel suggerant des facteurs proches (twin/close/adjacent primes, generation 'rapide' de cle).

## Preconditions

- Modulus RSA n fourni; indice textuel ou contextuel suggerant des facteurs proches (twin/close/adjacent primes, generation 'rapide' de cle).

## Cheap Probes

- Calculer isqrt(n) et verifier rapidement si a=isqrt(n)+1 donne a²-n proche d'un carre parfait (quelques milliers d'iterations max si vraiment proches).

## Telltale Evidence

- Convergence de la boucle de Fermat en un temps tres court (<1s a quelques secondes) malgre un n de plusieurs centaines de bits.

## Escalation Order

1. Toujours tester Fermat factorization en premier reflexe sur un challenge RSA avant Pollard rho/ECM/Wiener si un indice suggere des facteurs proches.
2. a = ceil(sqrt(n)); tant que a²-n n'est pas un carre parfait, a += 1.
3. p = a - sqrt(a²-n), q = a + sqrt(a²-n).
4. Dechiffrer normalement une fois p,q connus.

## Common Mistakes

- Essayer Pollard's rho ou une reduction de reseau avant d'avoir elimine le cas trivial close-prime via Fermat (couteux et inutile si Fermat suffit).

## Payload Shapes

```text
from sympy import isqrt\na = isqrt(n) + 1\nwhile not is_square(a*a - n): a += 1
```

## Related Writeups

- twin-prime-fermat-rsa

## Skill Impact

- Related skill: web-triage n/a; pertinent pour un futur crypto-triage.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
