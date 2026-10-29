---
doc_kind: pattern
title: "WIRETAP - capture C2 avec cle RSA fabriquee, factorisation de Fermat puis OAEP et openssl"
category: crypto
slug: esig-ctf-wiretap-rsa-fermat-pcap
created: 2026-10-29
status: active
tags:
  - rsa-fermat-factorization
  - close-primes
  - oaep
  - pcap-analysis
  - openssl-pbkdf2
  - c2-protocol
chain_summary: "Un pcap capture un echange implant<->C2. Le module RSA fait 2047 bits au lieu de 2048, signe d'une generation artisanale avec p et q tres proches, cassable par factorisation de Fermat en quelques secondes."
---
# WIRETAP - capture C2 avec cle RSA fabriquee, factorisation de Fermat puis OAEP et openssl

## Chain Summary

- One-line chain: Un pcap capture un echange implant<->C2. Le module RSA fait 2047 bits au lieu de 2048, signe d'une generation artisanale avec p et q tres proches, cassable par factorisation de Fermat en quelques secondes.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Ecart p-q bien plus petit qu'attendu pour des entiers 1024 bits; dechiffrement openssl avec la passphrase recuperee produit un flag lisible.

## Escalation Order

1. tshark conv,tcp -> un seul flux TCP, reconstruction des deux sens par payloads TCP bruts.
2. Identification du protocole maison (cle pub RSA / blob chiffre / blob openssl).
3. Analyse de la cle publique: module 2047 bits au lieu de 2048 -> suspicion de p et q trop proches.
4. Factorisation de Fermat -> p et q distants de tres peu sur des nombres 1024 bits -> casse en quelques iterations.
5. Dechiffrement RSA brut = bruit, PKCS#1v1.5 = FAIL -> test OAEP -> passphrase lisible mais PIEGE (pas le flag, mot de passe de l'etape suivante).
6. Blob openssl 'Salted__', balayage des combos cipher/KDF -> AES-256-CBC + PBKDF2 avec la passphrase OAEP -> flag en clair.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Tout module RSA dont la taille annoncee ne correspond pas exactement au bitlength reel est un signal fort de generation artisanale -> tester Fermat en premier. Devant un ciphertext RSA qui donne du bruit en brut et echoue en PKCS1v1.5, toujours tester OAEP avant d'abandonner. Un secret qui ressemble a un flag/mot de passe en cours de chaine peut etre un leurre intentionnel - verifier le format exact attendu avant de le soumettre.
```

## Related Writeups

- esig-ctf-wiretap-rsa-fermat-pcap

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
