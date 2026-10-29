---
doc_kind: writeup
title: "Video Conferencing with Zoom (WP) — Missing Authorization vczapi_sync_user"
category: web
slug: zoom-wp-plugin-vczapi-sync-user-missing-auth
created: 2026-10-29
status: solved
tags:
  - missing-authorization
  - cwe-862
  - wordpress-ajax
  - broken-access-control
  - privilege-check-omission
  - incomplete-patch
source: "Rapport de vulnerabilite plugin WordPress video-conferencing-with-zoom-api"
target: "Action AJAX vczapi_sync_user, plugin <=4.6.11"
---
# Video Conferencing with Zoom (WP) — Missing Authorization vczapi_sync_user

## Challenge Summary

- Source: Rapport de vulnerabilite plugin WordPress video-conferencing-with-zoom-api
- Target: Action AJAX vczapi_sync_user, plugin <=4.6.11
- Goal: Un gestionnaire AJAX charge inconditionnellement n'applique aucun controle de capacite ni de jeton, contrairement aux autres gestionnaires corriges - tout compte Subscriber peut exfiltrer les reunions Zoom du site et creer un article publie.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Reperage que la classe du gestionnaire est instanciee sans condition (atteignable par un role faible via admin-ajax.php).
2. Lecture du code : aucun current_user_can()/check_ajax_referer() avant traitement.
3. Comparaison avec d'autres gestionnaires du plugin qui verifient bien current_user_can('manage_options') -> confirme l'omission dans le changelog du correctif.
4. Authentification Subscriber de base (ni nonce ni capability requis).
5. Requete type=check -> le serveur interroge l'API Zoom du site et renvoie la liste complete des reunions a l'appelant faible privilege.
6. Requete type=sync -> cree un article publie avec une metadonnee sensible, contournant aussi un controle de capacite de publication.
7. Contraste : requete sur un gestionnaire protege renvoie une erreur, confirmant l'omission ciblee.

## Key Evidence

- "POST type=check&user_id=me -> reponse succes avec liste complete des reunions (topic, join_url+pwd)"; metadonnee sensible (URL de demarrage hote) exposee dans l'article cree; gestionnaire protege voisin renvoie 0/erreur.

## Dead Ends

- n/a.

## Payloads And Commands

```text
Requetes POST/GET admin-ajax.php avec action=vczapi_sync_user (type=check/sync) sous simple session Subscriber, sans nonce.
```

## Flag / Outcome

- n/a - rapport de vulnerabilite reel, pas de flag CTF.

## Reusable Lessons

- Pattern 'correctif de securite au niveau changelog incomplet car un gestionnaire precis a ete oublie' ; toujours auditer tous les hooks wp_ajax_* apres un changelog de securite, et comparer gestionnaires proteges vs non proteges du meme fichier.

## Pattern Candidates

- Nouveau pattern: wp-ajax-handler-missing-capability-check
