---
doc_kind: pattern
title: "RCE via filtre/attribut git quand .git/ est accessible en ecriture par une API de fichiers"
category: web
slug: forge-git-filter-rce
created: 2026-10-29
status: active
tags:
  - rce
  - git-filter
  - root-container-compromise
  - arbitrary-write
chain_summary: ".git/config (filtre clean) + .gitattributes + fichier trigger, ecrits via une API de fichiers qui ne protege .git/ qu'en suppression/renommage pas en ecriture, donnent une RCE au prochain git add declenche par le systeme."
---
# RCE via filtre/attribut git quand .git/ est accessible en ecriture par une API de fichiers

## Chain Summary

- One-line chain: .git/config (filtre clean) + .gitattributes + fichier trigger, ecrits via une API de fichiers qui ne protege .git/ qu'en suppression/renommage pas en ecriture, donnent une RCE au prochain git add declenche par le systeme.
- Typical target shape: Application exposant un repo git interne (historique de versions, snapshot) via la meme API de fichiers que l'arbre utilisateur, avec un processus systeme qui execute git add/commit periodiquement ou a la sauvegarde.

## Preconditions

- Application exposant un repo git interne (historique de versions, snapshot) via la meme API de fichiers que l'arbre utilisateur, avec un processus systeme qui execute git add/commit periodiquement ou a la sauvegarde.

## Cheap Probes

- Tester l'ecriture directe sur des chemins sous .git/ (pas seulement la suppression/renommage, qui sont souvent les seuls chemins bloques).

## Telltale Evidence

- L'API accepte un PUT/write sur un chemin commencant par .git/ sans erreur.

## Escalation Order

1. Ecrire un .git/config definissant un filtre clean (ou smudge) executant une commande shell.
2. Ecrire un .gitattributes associant un pattern de fichier a ce filtre.
3. Deposer un fichier correspondant a ce pattern (non suivi).
4. Declencher ou attendre le prochain git add -A/commit automatique du systeme.
5. Recuperer la sortie de la commande via un fichier de sortie lisible par l'API.

## Common Mistakes

- Ne bloquer que delete/rename sur .git/ en pensant avoir couvert tous les risques, en oubliant que l'ecriture directe de fichiers de config git est le vecteur reellement dangereux.

## Payload Shapes

```text
PUT .git/config: [filter "x"]\n\tclean = "sh -c 'id > /app/public/out.txt'"
```

## Related Writeups

- forge-git-filter-rce

## Skill Impact

- Related skill: web-triage (RCE): ajouter 'repo git interne expose via API fichiers -> tester ecriture .git/config+.gitattributes' comme sous-cas de RCE via fonctionnalite de versioning produit.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
