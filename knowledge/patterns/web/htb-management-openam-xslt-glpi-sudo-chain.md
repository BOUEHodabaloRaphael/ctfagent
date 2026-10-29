---
doc_kind: pattern
title: "HTB Management - OpenAM XSLT RCE -> dump LDAP -> dechiffrement secret GLPI -> sudo rdiff-backup root"
category: web
slug: htb-management-openam-xslt-glpi-sudo-chain
created: 2026-10-29
status: active
tags:
  - openam-xslt-rce
  - ldap-dump
  - glpi
  - xchacha20-poly1305
  - sudo-wildcard-bypass
  - credential-reuse
chain_summary: "Chaine complete d'une RCE sur OpenAM via injection XSLT jusqu'au root, en passant par un dump LDAP OpenDJ, le dechiffrement d'un secret applicatif GLPI (XChaCha20-Poly1305) et l'abus d'une regle sudo mal restreinte."
---
# HTB Management - OpenAM XSLT RCE -> dump LDAP -> dechiffrement secret GLPI -> sudo rdiff-backup root

## Chain Summary

- One-line chain: Chaine complete d'une RCE sur OpenAM via injection XSLT jusqu'au root, en passant par un dump LDAP OpenDJ, le dechiffrement d'un secret applicatif GLPI (XChaCha20-Poly1305) et l'abus d'une regle sudo mal restreinte.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Secret dechiffre verifie par roundtrip (rechiffrement = meme blob); commande sudo detournee avec double --restrict-path confirmee par le message de depart du mirroring.

## Escalation Order

1. Scan expose OpenAM (SSO), OpenDJ LDAP, GLPI.
2. RCE via injection XSLT sur un endpoint OpenAM -> shell service.
3. Dump LDAP OpenDJ avec creds Directory Manager par defaut -> decouverte d'un compte de service.
4. Acces MySQL GLPI -> table contenant un secret bind LDAP chiffre avec une cle applicative (XChaCha20-Poly1305).
5. Recuperation de la cle symetrique sur le filesystem -> dechiffrement du mot de passe bind LDAP.
6. Reutilisation du mot de passe pour un login SSH utilisateur humain.
7. sudo -l revele une regle rdiff-backup avec restrict-path et suffixe libre -> injection d'un second --restrict-path qui ecrase le premier (dernier gagne en argparse).
8. Lecture arbitraire de fichiers root via le serveur rdiff-backup detourne -> flag root.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Un secret applicatif chiffre avec une cle symetrique stockee sur le meme filesystem doit toujours faire chercher la cle avant d'attaquer le chiffrement lui-meme. Une regle sudoers avec wildcard suffixe sur un binaire qui accepte des options repetees (dernier gagne) permet souvent de reinjecter l'option supposement fixee en prefixe pour echapper a la restriction.
```

## Related Writeups

- htb-management-openam-xslt-glpi-sudo-chain

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
