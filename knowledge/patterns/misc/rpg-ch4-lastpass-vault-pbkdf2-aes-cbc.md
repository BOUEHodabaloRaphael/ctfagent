---
doc_kind: pattern
title: "Dechiffrement manuel d'un vault d'extension navigateur sans parseur public"
category: misc
slug: rpg-ch4-lastpass-vault-pbkdf2-aes-cbc
created: 2026-10-29
status: active
tags:
  - lastpass
  - pbkdf2
  - aes-cbc
  - wmi-double-hop
  - browser-vault
  - manual-crypto-impl
chain_summary: "Quand DPAPI/outils publics echouent sur un vault de gestionnaire de mots de passe (extension navigateur), lire directement la base WebSQL/SQLite locale et reconstruire manuellement le schema de derivation de cle et le format des champs chiffres."
---
# Dechiffrement manuel d'un vault d'extension navigateur sans parseur public

## Chain Summary

- One-line chain: Quand DPAPI/outils publics echouent sur un vault de gestionnaire de mots de passe (extension navigateur), lire directement la base WebSQL/SQLite locale et reconstruire manuellement le schema de derivation de cle et le format des champs chiffres.
- Typical target shape: Acces au profil navigateur d'un utilisateur avec une extension de gestionnaire de mots de passe installee; DPAPI ou outils d'extraction publics ne fonctionnent pas (contexte, version, ou protection renforcee).

## Preconditions

- Acces au profil navigateur d'un utilisateur avec une extension de gestionnaire de mots de passe installee; DPAPI ou outils d'extraction publics ne fonctionnent pas (contexte, version, ou protection renforcee).

## Cheap Probes

- Localiser la base SQLite/WebSQL de l'extension dans le profil navigateur; identifier le format des champs chiffres (marqueurs, encodage base64).

## Telltale Evidence

- Un champ connu en clair par ailleurs (ex: email du compte) permet de valider la derivation de cle avant de s'attaquer aux champs sensibles.

## Escalation Order

1. Localiser et copier la base locale de l'extension (WebSQL/SQLite).
2. Identifier le format d'un champ chiffre par inspection (marqueur, IV, ciphertext).
3. Chercher dans l'environnement (autres secrets/credentials recuperes) une valeur jouant le role de masterkey/passphrase.
4. Reconstruire la derivation de cle (souvent PBKDF2 avec un sel connu comme l'email).
5. Valider sur un champ dont le contenu clair est deja connu avant de dechiffrer les champs sensibles.

## Common Mistakes

- Supposer un chiffrement ECB par defaut sans verifier la presence d'un IV explicite (CBC) dans le format du champ.

## Payload Shapes

```text
key = pbkdf2_hmac('sha256', masterkey, email, 100100, 32); AES-CBC(key, iv).decrypt(ciphertext)
```

## Related Writeups

- rpg-ch4-lastpass-vault-pbkdf2-aes-cbc

## Skill Impact

- Related skill: pwn-triage/post-exploit Windows: ajouter 'vault d'extension navigateur sans parseur public -> reconstruire le format manuellement' comme technique de derniere intention.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
