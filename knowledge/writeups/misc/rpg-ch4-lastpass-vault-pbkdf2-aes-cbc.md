---
doc_kind: writeup
title: "HTB Endgame RPG — Ch.4 dechiffrement manuel du vault LastPass"
category: misc
slug: rpg-ch4-lastpass-vault-pbkdf2-aes-cbc
created: 2026-10-29
status: solved
tags:
  - lastpass
  - pbkdf2
  - aes-cbc
  - wmi-double-hop
  - browser-vault
  - manual-crypto-impl
source: "HackTheBox Endgame RPG"
target: "Base WebSQL extension LastPass (machine Gelus)"
---
# HTB Endgame RPG — Ch.4 dechiffrement manuel du vault LastPass

## Challenge Summary

- Source: HackTheBox Endgame RPG
- Target: Base WebSQL extension LastPass (machine Gelus)
- Goal: Pivot WMI double-hop vers Gelus, puis extraction et dechiffrement manuel (aucun outil public adapte) de la base WebSQL de l'extension LastPass, en reconstruisant la derivation PBKDF2-HMAC-SHA256 et le format AES-256-CBC.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Un secret keyring correspond a un compte domaine ayant le droit WMI distant sur Gelus.
2. Contournement du double-hop WinRM via Invoke-WmiMethod -Credential explicite.
3. Reverse shell via WMI (DownloadFile puis execution).
4. DPAPI Chrome echoue -> copie directe du fichier SQLite WebSQL local de l'extension LastPass.
5. Reconstruction du format du champ chiffre : marqueur + base64(IV 16 octets) + separateur + base64(ciphertext).
6. Decouverte : un autre secret keyring est le masterkey LastPass -> cle = PBKDF2-HMAC-SHA256(masterkey, email, 100100, 32).
7. Validation en dechiffrant le champ email (connu en clair) avant d'attaquer les champs login/password en AES-256-CBC (IV dans les 16 premiers octets, pas ECB).

## Key Evidence

- pbkdf2_hmac('sha256', master, email, 100100, 32) ; champ email dechiffre valide avant d'attaquer les champs login/password -> flag recupere dans un champ dechiffre.

## Dead Ends

- DPAPI Chrome a echoue (pas de token valide dans ce contexte) - oblige a pivoter directement sur la base WebSQL de l'extension LastPass.

## Payloads And Commands

```text
Implementation manuelle ~40 lignes Python (hashlib.pbkdf2_hmac + AES-CBC).
```

## Flag / Outcome

- Flag obtenu dans un champ dechiffre du vault.

## Reusable Lessons

- Extraire un vault navigateur sans DPAPI en lisant directement la base WebSQL locale de l'extension, puis reconstruire manuellement le schema de derivation (PBKDF2, email comme sel) et le format des champs (marqueur+IV+ciphertext CBC) quand aucun parseur public ne colle.

## Pattern Candidates

- Nouveau pattern: browser-extension-vault-manual-decrypt
