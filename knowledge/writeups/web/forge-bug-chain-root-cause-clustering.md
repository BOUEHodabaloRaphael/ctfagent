---
doc_kind: writeup
title: "Methodologie: clusteriser les bugs d'un meme programme par cause racine partagee"
category: web
slug: forge-bug-chain-root-cause-clustering
created: 2026-10-29
status: solved
tags:
  - bug-chaining
  - methodology
  - root-cause-analysis
  - bug-bounty-program
source: "Programme de divulgation reelle Forge/RodiumAI"
target: "Plateforme Forge (RodiumAI) - API multi-tenant"
---
# Methodologie: clusteriser les bugs d'un meme programme par cause racine partagee

## Challenge Summary

- Source: Programme de divulgation reelle Forge/RodiumAI
- Target: Plateforme Forge (RodiumAI) - API multi-tenant
- Goal: Analyse transversale de 11 rapports de vulnerabilite reels sur une meme plateforme (Forge/RodiumAI) revelant que plusieurs bugs apparemment distincts partagent en realite la meme cause racine structurelle ou le meme sous-systeme, ouvrant des chainages d'impact plus eleves.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source report)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Lister tous les rapports/findings confirmes sur un meme programme/plateforme, pas seulement le plus recent.
2. Pour chaque paire de findings touchant une fonctionnalite voisine (meme sous-systeme: SSRF, slug/publish, garde de capacite payante), comparer explicitement le mecanisme root-cause (pas juste le symptome).
3. Identifier les paires partageant une cause structurelle identique (ex: deux SSRF avec la meme faille de validation check-then-connect, deux gardes d'autorisation echouant pour la meme raison de design).
4. Identifier un point d'escalade ultime (ex: RCE) qui rend obsoletes plusieurs controles d'acces plus fins une fois atteint, et noter cette hierarchie.
5. Documenter les chainages realistes (ex: bug A sans effort pour preparer le terrain, bug B pour l'impact actif au bon moment).

## Key Evidence

- Exemple concret (Forge/RodiumAI): 2 SSRF (popup window.open + DNS-rebinding chat) partagent la meme faille 'resolve puis connect sans pinning'; 2 bugs slug/publish (race + stale-files) partagent 'absence de purge garantie du prefixe objet'; 2 gardes RODI (endpoint non gate + fail-open post-logout) partagent 'enforcement par endpoint/etat plutot qu'au point d'entree unique'; le RCE git-filter rend obsoletes 3 autres bugs d'autorisation une fois atteint (lecture de secrets -> forge de session admin).

## Dead Ends

- n/a.

## Payloads And Commands

```text
Revue croisee des rapports/findings existants, pas un payload technique.
```

## Flag / Outcome

- n/a - methodologie d'analyse, pas un flag.

## Reusable Lessons

- Avant de chercher de nouveaux bugs sur une cible deja partiellement auditee, relire TOUS les findings confirmes groupes par sous-systeme pour detecter les causes racines partagees: cela revele souvent un chainage d'impact plus eleve que chaque bug pris isolement, et un point d'escalade ultime qui peut rendre certains controles plus fins non pertinents.

## Pattern Candidates

- Pattern meta de methodologie, pas un pattern technique specifique.
