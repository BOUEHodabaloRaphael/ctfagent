---
doc_kind: pattern
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
chain_summary: "Scenario forensics Windows classique: VM d'analyse accessible en RDP sur laquelle il faut reconstruire une chaine d'activite (connexion VPN, agent de gestion a distance, commandes suspectes, client de messagerie) a partir d'artefacts systeme locaux."
---
# Holmes CTF 2026 Sherlock 02 - Bottle Out (VM Windows RDP, triage initial)

## Chain Summary

- One-line chain: Scenario forensics Windows classique: VM d'analyse accessible en RDP sur laquelle il faut reconstruire une chaine d'activite (connexion VPN, agent de gestion a distance, commandes suspectes, client de messagerie) a partir d'artefacts systeme locaux.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- NON RESOLU: scoreboard local indique 9/10 flags deja soumis par une session anterieure, mais aucune valeur de reponse n'est presente dans les fichiers locaux (grep negatif). Pas de preuve citable pour les reponses elles-memes.

## Escalation Order

1. RDP vers la VM avec les credentials fournies.
2. Identifier config/logs du client VPN (adresse+port serveur distant, CA du certificat client, IP assignee).
3. Identifier l'agent de gestion a distance installe (nom+version, FQDN du serveur de management, token d'auth).
4. Reconstruire les commandes suspectes executees (historique shell/EDR/prefetch).
5. Identifier le client de messagerie instantanee + compte email + mot de passe.
6. Identifier l'identite complete de l'attaquant.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Grille de questions reutilisable comme checklist de triage Windows post-compromission: artefacts VPN -> agent de gestion a distance -> historique de commandes -> credentials de messagerie -> identite de l'attaquant.
```

## Related Writeups

- bottleout-sherlock02-windows-triage-questionnaire

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
