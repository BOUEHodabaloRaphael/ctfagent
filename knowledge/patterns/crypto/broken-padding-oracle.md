---
doc_kind: pattern
title: "Oracle de padding PKCS7/AES-CBC exploitable sans cle"
category: crypto
slug: broken-padding-oracle
created: 2026-10-29
status: active
tags:
  - crypto
  - padding-oracle
  - aes-cbc
  - pkcs7
  - cbc-byte-at-a-time
chain_summary: "Endpoint renvoyant une reponse differenciee VALID/BAD_PADDING sur un dechiffrement AES-CBC = dechiffrement complet via byte-at-a-time CBC padding-oracle, sans connaitre la cle."
---
# Oracle de padding PKCS7/AES-CBC exploitable sans cle

## Chain Summary

- One-line chain: Endpoint renvoyant une reponse differenciee VALID/BAD_PADDING sur un dechiffrement AES-CBC = dechiffrement complet via byte-at-a-time CBC padding-oracle, sans connaitre la cle.
- Typical target shape: Service dechiffrant un ciphertext AES-CBC et exposant, meme indirectement (code erreur, message, timing), si le padding PKCS7 est valide.

## Preconditions

- Service dechiffrant un ciphertext AES-CBC et exposant, meme indirectement (code erreur, message, timing), si le padding PKCS7 est valide.

## Cheap Probes

- Envoyer un ciphertext legerement corrompu et observer si l'erreur distingue padding invalide d'un autre type d'erreur (format, dechiffrement).

## Telltale Evidence

- Reponse differenciee (message, code HTTP, timing) entre padding invalide et padding valide/autre erreur.

## Escalation Order

1. Confirmer la distinction de reponse VALID/BAD_PADDING/BAD_FORMAT.
2. Isoler le(s) bloc(s) ciphertext cible(s) (16 octets par bloc AES).
3. Appliquer l'attaque byte-at-a-time CBC padding-oracle bloc par bloc, derniere a premiere position.
4. XOR de l'etat intermediaire avec le bloc precedent (ou IV) pour obtenir le clair.

## Common Mistakes

- Chercher a lire la cle directement dans le code/binaire fourni au lieu de traiter le service comme une boite noire exploitable a distance (reduit la generalisation de l'exploit).

## Payload Shapes

```text
GET /?ct=<hex ciphertext modifie byte par byte>
```

## Related Writeups

- broken-padding-oracle

## Skill Impact

- Related skill: web-triage/crypto: ajouter le padding-oracle CBC comme pattern reconnaissable des qu'un endpoint distingue VALID/BAD_PADDING.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
