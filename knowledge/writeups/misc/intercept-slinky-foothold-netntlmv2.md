---
doc_kind: writeup
title: "Intercept - Foothold initial (fichier slinky Search Connector + capture NetNTLMv2)"
category: misc
slug: intercept-slinky-foothold-netntlmv2
created: 2026-10-29
status: solved
tags:
  - searchconnector-slinky
  - netntlmv2
  - responder
  - smb-write-share
  - ad-recon-signing
source: "HTB Pro Lab Intercept (Advanced AD)"
target: "Partage SMB en ecriture + poste Windows"
---
# Intercept - Foothold initial (fichier slinky Search Connector + capture NetNTLMv2)

## Challenge Summary

- Source: HTB Pro Lab Intercept (Advanced AD)
- Target: Partage SMB en ecriture + poste Windows
- Goal: Un partage accessible en ecriture permet de deposer un fichier .searchConnector-ms (slinky) qui declenche une connexion sortante automatique vers un partage controle, capturant un hash NetNTLMv2.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Enumeration AD: signature LDAP/SMB non requise sur plusieurs hotes.
2. Decouverte d'un partage lecture/ecriture sur un poste contenant des fichiers d'amorcage.
3. Depot d'un fichier .searchConnector-ms (slinky) sur le partage.
4. Responder a l'ecoute (module HTTP desactive pour reserver le futur relais) capture le hash quand le poste ouvre le dossier.
5. hashcat -m 5600 casse le hash -> creds valides reutilisables.

## Key Evidence

- nxc smb/ldap confirme signature SMB non requise et LDAP signing/channel binding faibles - conditions prealables validees avant de lancer l'attaque.

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
fichier Search Connector (.searchConnector-ms) deploye sur un partage en ecriture.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Avant toute chaine de relais NTLM, verifier systematiquement signature SMB/LDAP et channel binding (nxc); un fichier slinky (.searchConnector-ms) sur un partage writable force une connexion sortante automatique similaire a .lnk/.scf, utile quand ceux-ci sont filtres.

## Pattern Candidates

- Nouveau pattern: intercept-slinky-foothold-netntlmv2
