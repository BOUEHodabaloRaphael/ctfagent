---
doc_kind: writeup
title: "AarMe — IDOR/BOLA sur GET /api/aarme/status"
category: web
slug: aarme-idor-status-session-only-check
created: 2026-10-29
status: solved
tags:
  - idor
  - bola
  - broken-object-level-auth
  - session-only-check
  - cwe-639
source: "Bug bounty CyberAar / AarMe"
target: "API de consultation de statut de rapport de vulnerabilite"
---
# AarMe — IDOR/BOLA sur GET /api/aarme/status

## Challenge Summary

- Source: Bug bounty CyberAar / AarMe
- Target: API de consultation de statut de rapport de vulnerabilite
- Goal: L'endpoint de statut verifie uniquement qu'une session authentifiee existe, sans verifier que les donnees demandees appartiennent au compte de la session active - IDOR permettant de consulter le statut d'un rapport d'un autre compte.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Observation du client interrogeant l'endpoint de statut avec des identifiants fournis cote client.
2. Hypothese : controle base sur 'session presente' plutot que 'session autorisee sur ces donnees'.
3. Requete sans session sur identifiants compte A -> rejetee (unauthenticated), confirme l'exigence de session.
4. Meme requete authentifiee depuis session compte B mais visant compte A -> acceptee et traitee (not_found faute de rapport existant, pas faute d'autorisation).
5. Le changement de code d'erreur (unauthenticated -> not_found) prouve que la requete croisee est traitee sans verification de propriete.

## Key Evidence

- Requete anonyme -> {"error":"unauthenticated"}; meme requete avec session B visant compte A -> {"error":"not_found"} (changement de code = requete acceptee cote serveur).

## Dead Ends

- n/a.

## Payloads And Commands

```text
Requete GET avec parametres d'un compte tiers, sous une session authentifiee d'un compte different.
```

## Flag / Outcome

- n/a - finding bug bounty reel, pas de flag CTF.

## Reusable Lessons

- Pattern IDOR/BOLA classique : observer le changement de code d'erreur entre requete anonyme et requete authentifiee croisee pour prouver l'absence de controle d'autorisation, meme sans donnees tierces reelles disponibles.

## Pattern Candidates

- Nouveau pattern: idor-error-code-delta-proof
