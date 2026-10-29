---
doc_kind: writeup
title: "WIRETAP - capture C2 avec cle RSA fabriquee, factorisation de Fermat puis OAEP et openssl"
category: crypto
slug: esig-ctf-wiretap-rsa-fermat-pcap
created: 2026-10-29
status: solved
tags:
  - rsa-fermat-factorization
  - close-primes
  - oaep
  - pcap-analysis
  - openssl-pbkdf2
  - c2-protocol
source: "ESIG TECH ARENA CTF"
target: "PCAP avec protocole C2 maison + RSA artisanal"
---
# WIRETAP - capture C2 avec cle RSA fabriquee, factorisation de Fermat puis OAEP et openssl

## Challenge Summary

- Source: ESIG TECH ARENA CTF
- Target: PCAP avec protocole C2 maison + RSA artisanal
- Goal: Un pcap capture un echange implant<->C2. Le module RSA fait 2047 bits au lieu de 2048, signe d'une generation artisanale avec p et q tres proches, cassable par factorisation de Fermat en quelques secondes.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. tshark conv,tcp -> un seul flux TCP, reconstruction des deux sens par payloads TCP bruts.
2. Identification du protocole maison (cle pub RSA / blob chiffre / blob openssl).
3. Analyse de la cle publique: module 2047 bits au lieu de 2048 -> suspicion de p et q trop proches.
4. Factorisation de Fermat -> p et q distants de tres peu sur des nombres 1024 bits -> casse en quelques iterations.
5. Dechiffrement RSA brut = bruit, PKCS#1v1.5 = FAIL -> test OAEP -> passphrase lisible mais PIEGE (pas le flag, mot de passe de l'etape suivante).
6. Blob openssl 'Salted__', balayage des combos cipher/KDF -> AES-256-CBC + PBKDF2 avec la passphrase OAEP -> flag en clair.

## Key Evidence

- Ecart p-q bien plus petit qu'attendu pour des entiers 1024 bits; dechiffrement openssl avec la passphrase recuperee produit un flag lisible.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Scripts Python (pycryptodome, gmpy2) pour Fermat + RSA-OAEP, puis commande openssl enc en ligne de commande.
```

## Flag / Outcome

- Flag obtenu / finding confirme, chaine terminee.

## Reusable Lessons

- Tout module RSA dont la taille annoncee ne correspond pas exactement au bitlength reel est un signal fort de generation artisanale -> tester Fermat en premier. Devant un ciphertext RSA qui donne du bruit en brut et echoue en PKCS1v1.5, toujours tester OAEP avant d'abandonner. Un secret qui ressemble a un flag/mot de passe en cours de chaine peut etre un leurre intentionnel - verifier le format exact attendu avant de le soumettre.

## Pattern Candidates

- Voir pattern associe de meme slug.
