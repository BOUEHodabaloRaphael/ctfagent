---
doc_kind: writeup
title: "ThunderCipher NightCipher - QR code cache, bruteforce SSH puis injection de variable dans script sudo"
category: misc
slug: nightcipher-qr-ftp-sudo-var-injection
created: 2026-10-29
status: solved
tags:
  - qr-code-creds
  - hydra-bruteforce
  - sudo-script-var-injection
  - docker-mount-escape
source: thundercipher.in/labs
target: "Script sudo NOPASSWD avec variable non sanitisee"
---
# ThunderCipher NightCipher - QR code cache, bruteforce SSH puis injection de variable dans script sudo

## Challenge Summary

- Source: thundercipher.in/labs
- Target: Script sudo NOPASSWD avec variable non sanitisee
- Goal: Un QR code cache revele des creds FTP donnant acces a une wordlist pour bruteforcer SSH; un script sudo NOPASSWD utilise une variable non sanitisee, permettant une injection de commande.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. QR code -> creds FTP.
2. FTP -> wordlist de mots de passe candidats.
3. hydra bruteforce SSH -> credential valide.
4. sudo -l -> script NOPASSWD avec variable non sanitisee.
5. Injection de commande via substitution $(...) -> root, ajout au groupe docker.
6. docker run -v /:/mnt -> flag.

## Key Evidence

- Sortie injection affichant uid=0(root) et appartenance au groupe docker; flag lu via montage docker.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Payload shell $(id > /tmp/out; cat /tmp/out) injecte comme valeur de variable; docker run -v /:/mnt.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Tout script sudo NOPASSWD qui lit une variable d'entree interpretee sans guillemets stricts est injectable par substitution de commande $(...); QR code = vecteur de credential-hiding a toujours scanner.

## Pattern Candidates

- Voir pattern associe de meme slug.
