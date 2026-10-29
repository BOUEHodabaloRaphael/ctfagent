---
doc_kind: pattern
title: "ThunderCipher NightCipher - QR code cache, bruteforce SSH puis injection de variable dans script sudo"
category: misc
slug: nightcipher-qr-ftp-sudo-var-injection
created: 2026-10-29
status: active
tags:
  - qr-code-creds
  - hydra-bruteforce
  - sudo-script-var-injection
  - docker-mount-escape
chain_summary: "Un QR code cache revele des creds FTP donnant acces a une wordlist pour bruteforcer SSH; un script sudo NOPASSWD utilise une variable non sanitisee, permettant une injection de commande."
---
# ThunderCipher NightCipher - QR code cache, bruteforce SSH puis injection de variable dans script sudo

## Chain Summary

- One-line chain: Un QR code cache revele des creds FTP donnant acces a une wordlist pour bruteforcer SSH; un script sudo NOPASSWD utilise une variable non sanitisee, permettant une injection de commande.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Sortie injection affichant uid=0(root) et appartenance au groupe docker; flag lu via montage docker.

## Escalation Order

1. QR code -> creds FTP.
2. FTP -> wordlist de mots de passe candidats.
3. hydra bruteforce SSH -> credential valide.
4. sudo -l -> script NOPASSWD avec variable non sanitisee.
5. Injection de commande via substitution $(...) -> root, ajout au groupe docker.
6. docker run -v /:/mnt -> flag.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
Tout script sudo NOPASSWD qui lit une variable d'entree interpretee sans guillemets stricts est injectable par substitution de commande $(...); QR code = vecteur de credential-hiding a toujours scanner.
```

## Related Writeups

- nightcipher-qr-ftp-sudo-var-injection

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
