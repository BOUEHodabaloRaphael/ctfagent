---
doc_kind: pattern
title: "HTB EU Mini Pro Lab Unintended - Gitea -> MySQL -> Mattermost -> Samba AD -> Duplicati"
category: misc
slug: htb-euminiprolab-unintended-samba-ad-chain
created: 2026-10-29
status: active
tags:
  - samba-ad
  - gitea-hash-forge
  - pass-the-hash
  - duplicati-auth-bypass
  - docker-pivot
  - credential-reuse
  - pro-lab
chain_summary: "Chaine multi-machine partant de vhosts caches exposant Gitea, pivotant via un MySQL par defaut permettant de forger un hash PBKDF2 sans le casser, jusqu'au hash NT de l'Administrator et un bypass d'authentification Duplicati."
---
# HTB EU Mini Pro Lab Unintended - Gitea -> MySQL -> Mattermost -> Samba AD -> Duplicati

## Chain Summary

- One-line chain: Chaine multi-machine partant de vhosts caches exposant Gitea, pivotant via un MySQL par defaut permettant de forger un hash PBKDF2 sans le casser, jusqu'au hash NT de l'Administrator et un bypass d'authentification Duplicati.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Hash NT Administrator extrait via ldbsearch sur le backup Samba, utilise directement en pass-the-hash sur le partage SMB du DC.

## Escalation Order

1. Bruteforce de vhosts par header Host -> services caches decouverts (chat, code).
2. Repo Gitea public -> secrets dans l'historique git (git show).
3. Compte restreint utilise en SSH -D (SOCKS forward) pour atteindre un MySQL root:root interne.
4. Forge d'un hash PBKDF2 Gitea directement en base sans casser le hash existant -> login admin API.
5. Repo prive -> bash_history revele une passphrase reutilisee comme mot de passe de domaine -> SSH (flag).
6. PostgreSQL Mattermost accessible en interne -> mot de passe en clair dans un message -> SSH compte docker group -> montage du / hote (flag).
7. Backup Samba exfiltre -> ldbsearch extrait unicodePwd Administrator -> pass-the-hash SMB (flag).
8. Duplicati: bypass du nonce d'authentification -> recuperation et dechiffrement local de fichiers (flag).

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Un MySQL par defaut root:root adjacent a une appli avec un hash de mot de passe connu permet de forger l'auth sans casser le hash. Bypass d'auth par nonce Duplicati reutilisable sur toute instance dont la passphrase a fuite. Toujours chercher les vhosts caches avant de se fier a un nmap -p- qui peut lister des ports filtres sans reveler le vrai point d'entree.
```

## Related Writeups

- htb-euminiprolab-unintended-samba-ad-chain

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
