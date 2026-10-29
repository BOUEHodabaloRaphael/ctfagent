---
doc_kind: writeup
title: "APTLabs Pro Lab - fuite de credentials, reutilisation de mots de passe, appliances mal configurees (zero CVE)"
category: web
slug: htb-aptlabs-leak-reuse-no-cve
created: 2026-10-29
status: solved
tags:
  - credential-leak
  - password-reuse
  - default-creds
  - django-csrf-bypass
  - gslb-admin
  - pro-lab-no-cve
source: "HackTheBox Pro Lab APTLabs"
target: "GSLB admin + Django CA + Nextcloud"
---
# APTLabs Pro Lab - fuite de credentials, reutilisation de mots de passe, appliances mal configurees (zero CVE)

## Challenge Summary

- Source: HackTheBox Pro Lab APTLabs
- Target: GSLB admin + Django CA + Nextcloud
- Goal: Progression sans aucun CVE: une base de fuite de credentials pivote vers un panel GSLB admin (creds par defaut) puis vers un gestionnaire de certificats Django mal protege contre le CSRF.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Recon reseau -> plusieurs services distincts identifies.
2. Moteur de recherche de fuites interne -> identites/mots de passe divulgues.
3. Mot de passe reutilise + login admin par defaut -> acces au panel GSLB.
4. Flag extrait via l'API SPA interne.
5. Login Django CA avec un credential issu de la fuite -> contournement CSRF (triple condition: cookie + champ POST + header + Origin exact).
6. Flag dans le dashboard; decouverte d'une infrastructure de certificats evil deja preparee.
7. Nextcloud: comptes valides mais bloques par 2FA forcee -> impasse documentee.
8. Defense reseau du lab (IPS) documentee comme contrainte operationnelle.

## Key Evidence

- Deux flags distincts extraits (table domains GSLB, dashboard Django CA).

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Scripts Python de login/brute (flow CSRF Django, runner GSLB, enum DNS, clients Nextcloud).
```

## Flag / Outcome

- Flag obtenu / finding confirme, chaine terminee.

## Reusable Lessons

- Base de fuite + reutilisation d'identifiants comme vecteur d'entree initial sans exploit technique. Checklist CSRF Django a retenir: cookie + champ POST + header + Origin exact, sinon 403 en DEBUG=False.

## Pattern Candidates

- Voir pattern associe de meme slug.
