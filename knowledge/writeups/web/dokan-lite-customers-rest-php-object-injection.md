---
doc_kind: writeup
title: "Dokan-lite — PHP Object Injection via customer meta_data sur /dokan/v1/customers"
category: web
slug: dokan-lite-customers-rest-php-object-injection
created: 2026-10-29
status: solved
tags:
  - php-object-injection
  - cwe-502
  - wordpress-rest-api
  - incomplete-patch
  - woocommerce-meta
  - gadget-chain
source: "Rapport de vulnerabilite plugin WordPress Dokan-lite"
target: "Dokan-lite <=5.3.0, endpoint REST /dokan/v1/customers"
---
# Dokan-lite — PHP Object Injection via customer meta_data sur /dokan/v1/customers

## Challenge Summary

- Source: Rapport de vulnerabilite plugin WordPress Dokan-lite
- Target: Dokan-lite <=5.3.0, endpoint REST /dokan/v1/customers
- Goal: Le correctif 5.3.0 a ajoute une protection anti-objet-serialise uniquement sur l'endpoint REST products, oubliant customers qui reutilise le meme pipeline d'ecriture de metadonnees sans filtrage.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Analyse du diff entre versions : seuls password/email/role sont bloques, aucun controle sur meta_data du endpoint customers.
2. Comparaison avec l'endpoint products, qui applique un filtre anti-objet-serialise.
3. Authentification en vendeur (role le plus bas, precondition triviale) et nonce REST.
4. PUT /customers/{id} avec meta_data de cle non protegee contenant une chaine serialisee PHP.
5. Confirmation de persistance intacte en base (wp_usermeta).
6. Demonstration de revivification : la lecture via get_user_meta/WC_Customer passe par maybe_unserialize() -> objet hydrate, methode magique __wakeup() executee.

## Key Evidence

- Payload serialise PHP persiste en wp_usermeta ; maybe_unserialize() hydrate l'objet, methode __wakeup() executee et verifiee (effet observable).

## Dead Ends

- n/a - PoC valide de bout en bout sur environnement de test autorise.

## Payloads And Commands

```text
Objet PHP serialise (O:classe:nb_props:{...}) injecte dans un champ meta_data non protege via l'API REST WooCommerce/Dokan.
```

## Flag / Outcome

- n/a - rapport de vulnerabilite reel, pas de flag CTF.

## Reusable Lessons

- Pattern 'correctif applique a un seul endpoint REST partageant le meme pipeline de stockage qu'un autre endpoint non corrige' ; toujours verifier qu'un guard anti-deserialisation couvre toute surface partageant la meme fonction d'ecriture de metadonnees.

## Pattern Candidates

- Nouveau pattern: partial-patch-shared-storage-pipeline
