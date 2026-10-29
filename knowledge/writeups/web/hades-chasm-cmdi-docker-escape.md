---
doc_kind: writeup
title: "Endgame HADES - Chasm (injection de commande ${IFS} + pivot depuis conteneur Docker)"
category: web
slug: hades-chasm-cmdi-docker-escape
created: 2026-10-29
status: solved
tags:
  - command-injection
  - ifs-bypass
  - docker-pivot
  - chisel-socks
  - openssl-injection
source: "HTB Endgame HADES"
target: "Appli web generation de certificats (openssl)"
---
# Endgame HADES - Chasm (injection de commande ${IFS} + pivot depuis conteneur Docker)

## Challenge Summary

- Source: HTB Endgame HADES
- Target: Appli web generation de certificats (openssl)
- Goal: Une appli web de generation de certificats passe un parametre non filtre a openssl; le filtre bloquant les espaces est contourne avec ${IFS}, obtenant un shell dans un conteneur Docker utilise comme pivot vers le reseau AD interne.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Endpoint de generation de certificat: un parametre injecte dans un appel openssl cote serveur.
2. Filtre bloque les espaces -> contournement via ${IFS} comme separateur de commande.
3. Payload avec substitution de commande imbriquee -> reverse shell www-data dans le conteneur.
4. Flag lu dans un fichier a nom aleatoire du dossier web.
5. Le conteneur a une route NAT vers le reseau interne; chisel server --reverse + client depuis le conteneur -> SOCKS5 proxychains vers le reseau interne.

## Key Evidence

- curl vers l'endpoint avec payload ${IFS} retourne une connexion reverse shell confirmant le bypass du filtre d'espaces.

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
commande shell avec ${IFS} comme substitut d'espace dans un payload de command injection.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Quand un filtre applicatif bloque l'espace litteral dans une injection de commande, ${IFS} (ou $IFS$9, %09 en URL) est un contournement standard; un conteneur Docker en entry point avec route NAT sortante est un pivot ideal pour un tunnel chisel reverse SOCKS vers le reseau interne.

## Pattern Candidates

- Nouveau pattern: hades-chasm-cmdi-docker-escape
