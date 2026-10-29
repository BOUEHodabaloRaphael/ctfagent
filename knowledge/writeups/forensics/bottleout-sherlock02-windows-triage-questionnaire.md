---
doc_kind: writeup
title: "Holmes CTF 2026 Sherlock 02 - Bottle Out (VM Windows RDP, triage initial)"
category: forensics
slug: bottleout-sherlock02-windows-triage-questionnaire
created: 2026-10-29
status: draft
tags:
  - dfir
  - windows
  - rdp-triage
  - vpn-forensics
  - remote-management-agent
  - holmes-ctf
source: "Holmes CTF 2026: The Reichenbach Directive - Sherlock 2 Bottle Out"
target: "VM Windows accessible en RDP"
---
# Holmes CTF 2026 Sherlock 02 - Bottle Out (VM Windows RDP, triage initial)

## Challenge Summary

- Source: Holmes CTF 2026: The Reichenbach Directive - Sherlock 2 Bottle Out
- Target: VM Windows accessible en RDP
- Goal: Scenario forensics Windows classique: VM d'analyse accessible en RDP sur laquelle il faut reconstruire une chaine d'activite (connexion VPN, agent de gestion a distance, commandes suspectes, client de messagerie) a partir d'artefacts systeme locaux.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. RDP vers la VM avec les credentials fournies.
2. Identifier config/logs du client VPN (adresse+port serveur distant, CA du certificat client, IP assignee).
3. Identifier l'agent de gestion a distance installe (nom+version, FQDN du serveur de management, token d'auth).
4. Reconstruire les commandes suspectes executees (historique shell/EDR/prefetch).
5. Identifier le client de messagerie instantanee + compte email + mot de passe.
6. Identifier l'identite complete de l'attaquant.

## Key Evidence

- NON RESOLU: scoreboard local indique 9/10 flags deja soumis par une session anterieure, mais aucune valeur de reponse n'est presente dans les fichiers locaux (grep negatif). Pas de preuve citable pour les reponses elles-memes.

## Dead Ends

- NON RESOLU localement. Investigation engagee (acces RDP confirme), mais aucune reponse/flag n'est etablie par une preuve litterale locale. Statut formel: draft, a reprendre uniquement avec un acces complet a la VM d'analyse, pas de resume depuis une session anterieure sans verification.

## Payloads And Commands

```text
Analyse manuelle via session RDP (xfreerdp) + probablement Prefetch/EventLog/registre/credential-manager Windows.
```

## Flag / Outcome

- NON RESOLU localement. Investigation engagee (acces RDP confirme), mais aucune reponse/flag n'est etablie par une preuve litterale locale. Statut formel: draft, a reprendre uniquement avec un acces complet a la VM d'analyse, pas de resume depuis une session anterieure sans verification.

## Reusable Lessons

- Grille de questions reutilisable comme checklist de triage Windows post-compromission: artefacts VPN -> agent de gestion a distance -> historique de commandes -> credentials de messagerie -> identite de l'attaquant.

## Pattern Candidates

- Voir pattern associe de meme slug.
