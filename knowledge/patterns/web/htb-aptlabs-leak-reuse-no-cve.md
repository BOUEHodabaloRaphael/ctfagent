---
doc_kind: pattern
title: "APTLabs Pro Lab - fuite de credentials, reutilisation de mots de passe, appliances mal configurees (zero CVE)"
category: web
slug: htb-aptlabs-leak-reuse-no-cve
created: 2026-10-29
status: active
tags:
  - credential-leak
  - password-reuse
  - default-creds
  - django-csrf-bypass
  - gslb-admin
  - pro-lab-no-cve
chain_summary: "Progression sans aucun CVE: une base de fuite de credentials pivote vers un panel GSLB admin (creds par defaut) puis vers un gestionnaire de certificats Django mal protege contre le CSRF."
---
# APTLabs Pro Lab - fuite de credentials, reutilisation de mots de passe, appliances mal configurees (zero CVE)

## Chain Summary

- One-line chain: Progression sans aucun CVE: une base de fuite de credentials pivote vers un panel GSLB admin (creds par defaut) puis vers un gestionnaire de certificats Django mal protege contre le CSRF.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Deux flags distincts extraits (table domains GSLB, dashboard Django CA).

## Escalation Order

1. Recon reseau -> plusieurs services distincts identifies.
2. Moteur de recherche de fuites interne -> identites/mots de passe divulgues.
3. Mot de passe reutilise + login admin par defaut -> acces au panel GSLB.
4. Flag extrait via l'API SPA interne.
5. Login Django CA avec un credential issu de la fuite -> contournement CSRF (triple condition: cookie + champ POST + header + Origin exact).
6. Flag dans le dashboard; decouverte d'une infrastructure de certificats evil deja preparee.
7. Nextcloud: comptes valides mais bloques par 2FA forcee -> impasse documentee.
8. Defense reseau du lab (IPS) documentee comme contrainte operationnelle.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Base de fuite + reutilisation d'identifiants comme vecteur d'entree initial sans exploit technique. Checklist CSRF Django a retenir: cookie + champ POST + header + Origin exact, sinon 403 en DEBUG=False.
```

## Related Writeups

- htb-aptlabs-leak-reuse-no-cve

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
