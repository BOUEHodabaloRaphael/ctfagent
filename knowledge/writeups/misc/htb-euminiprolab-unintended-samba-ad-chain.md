---
doc_kind: writeup
title: "HTB EU Mini Pro Lab Unintended - Gitea -> MySQL -> Mattermost -> Samba AD -> Duplicati"
category: misc
slug: htb-euminiprolab-unintended-samba-ad-chain
created: 2026-10-29
status: solved
tags:
  - samba-ad
  - gitea-hash-forge
  - pass-the-hash
  - duplicati-auth-bypass
  - docker-pivot
  - credential-reuse
  - pro-lab
source: "HackTheBox EU Mini Pro Lab Unintended"
target: "Domaine Samba AD, Gitea, MySQL, Mattermost, Duplicati"
---
# HTB EU Mini Pro Lab Unintended - Gitea -> MySQL -> Mattermost -> Samba AD -> Duplicati

## Challenge Summary

- Source: HackTheBox EU Mini Pro Lab Unintended
- Target: Domaine Samba AD, Gitea, MySQL, Mattermost, Duplicati
- Goal: Chaine multi-machine partant de vhosts caches exposant Gitea, pivotant via un MySQL par defaut permettant de forger un hash PBKDF2 sans le casser, jusqu'au hash NT de l'Administrator et un bypass d'authentification Duplicati.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Bruteforce de vhosts par header Host -> services caches decouverts (chat, code).
2. Repo Gitea public -> secrets dans l'historique git (git show).
3. Compte restreint utilise en SSH -D (SOCKS forward) pour atteindre un MySQL root:root interne.
4. Forge d'un hash PBKDF2 Gitea directement en base sans casser le hash existant -> login admin API.
5. Repo prive -> bash_history revele une passphrase reutilisee comme mot de passe de domaine -> SSH (flag).
6. PostgreSQL Mattermost accessible en interne -> mot de passe en clair dans un message -> SSH compte docker group -> montage du / hote (flag).
7. Backup Samba exfiltre -> ldbsearch extrait unicodePwd Administrator -> pass-the-hash SMB (flag).
8. Duplicati: bypass du nonce d'authentification -> recuperation et dechiffrement local de fichiers (flag).

## Key Evidence

- Hash NT Administrator extrait via ldbsearch sur le backup Samba, utilise directement en pass-the-hash sur le partage SMB du DC.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Scripts Python (forge PBKDF2 Gitea, bypass nonce Duplicati), docker run pour ldbsearch et montage root FS, proxychains + ssh -D.
```

## Flag / Outcome

- Flag obtenu / finding confirme, chaine terminee.

## Reusable Lessons

- Un MySQL par defaut root:root adjacent a une appli avec un hash de mot de passe connu permet de forger l'auth sans casser le hash. Bypass d'auth par nonce Duplicati reutilisable sur toute instance dont la passphrase a fuite. Toujours chercher les vhosts caches avant de se fier a un nmap -p- qui peut lister des ports filtres sans reveler le vrai point d'entree.

## Pattern Candidates

- Voir pattern associe de meme slug.
