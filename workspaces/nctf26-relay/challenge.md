---
doc_kind: challenge
id: nctf26-relay
title: "relay (NCTF26 #267)"
category: chains
platform: CTFd/arena.ctf.tg
platform_id: 267
url: ""
status: new
tags:
  - nctf26
  - chains
  - team_instance
  - blocked-quota
attachments:
  []
---
# relay (NCTF26 #267)

- ID: nctf26-relay
- Category: chains
- Platform: CTFd/arena.ctf.tg
- Platform ID: 267
- URL: (not provided)
- Attachments:
  - none

## Description

# relay (NCTF26 #267, chains, 498pts initial / decaying — 423pts at check time, 12 solves)

## Description (FR, verbatim depuis l'API /api/v1/challenges/267)

Relay est un service réseau qui parle un protocole maison : des trames binaires au format TLV
(type, longueur, valeur), envoyées encodées en hexadécimal. La page d'accueil documente deux
opérations élémentaires, dont un simple écho. À toi de rétro-concevoir ce dialogue et d'en tirer
le flag. Lance l'instance (bouton Démarrer) et rends-toi à l'adresse affichée.

Bloqué ? Des indices sont disponibles (ils coûtent quelques points). Flag format : NCTF{...}

## Métadonnées plateforme

- id: 267, category: chains, tags: chains, creator:hibris, creator:Clawd
- type CTFd: `team_instance` (plugin `team_instancer`), flag class `team_hmac`
- connection_info (template): `http://{host}:{port}/  (per-team instance; use the 'launch' button)`
- access mode déclaré par le challenge: `https` (champ "access":"https" dans l'API) ->
  d'après create.html du plugin, le mode `https` affiche normalement une URL du style
  `https://<label>.i.ctf.tg/`
- hints: 2 indices payants (20 pts, 40 pts) -- PAS déverrouillés (règle "pas de bruteforce",
  et on garde la réserve de points tant qu'on n'est pas bloqué net).
- files: aucun fichier attaché (tout est dans le dialogue de protocole une fois l'instance lancée).

## Mécanisme d'instance (reverse-engineered depuis les assets JS du plugin, authentifié)

- `GET /plugins/team_instancer/status?challenge_id=267` -> `{"status":"none","success":true}` tant
  qu'aucune instance n'est active pour l'équipe sur ce challenge précis.
- `POST /plugins/team_instancer/spawn` avec header `CSRF-Token: <nonce de window.init.csrfNonce>`
  et body `{"challenge_id":267}` -> démarre l'instance (bouton "Démarrer mon instance" côté UI).
- `POST /plugins/team_instancer/renew` et `/destroy` (même body) pour prolonger/arrêter.
- La réponse de spawn réussie contient `connection: {host, port, display, vpn}` -- pour le mode
  `https`, `display` donne vraisemblablement l'URL `https://<label>.i.ctf.tg/` directement (pas
  besoin du VPN équipe dans ce cas précis, contrairement au mode `vpn`).

## BLOCAGE ACTUEL (preuve brute)

Tentative de spawn (deux fois, à quelques minutes d'intervalle, CSRF nonce valide à chaque fois) :

```
$ POST /plugins/team_instancer/spawn {"challenge_id":267}
status_code=429
{"error": "Maximum 2 instances simultanees par equipe.", "success": false}
```

Vérification : la plateforme limite à 2 instances `team_instance` simultanées PAR ÉQUIPE
(Th3N00bs), tous challenges confondus (pas seulement #267). J'ai énuméré TOUS les challenges de
type `team_instance` visibles dans le catalogue actuel (`/api/v1/challenges`, 62 challenges au
total, 15 de type `team_instance`) et interrogé `/plugins/team_instancer/status` pour chacun :

```
486 thierry8petstar--oui-ou-non-1 misc  -> none
453 boazak--agokoli web               -> none
265 clinic chains                     -> none
433 algorithme123--zemidjan-classement forensics -> none
371 ai1-naive-guard ai                -> none
372 ai2-output-filter ai              -> none
373 ai3-tool-abuse ai                 -> none
374 agent-tool-abuse ai               -> none
384 adversarial-gate ml               -> none
385 pickle-rce ml                     -> none
386 model-inversion ml                -> none
487 thierry8petstar--oui-ou-non-2 misc -> none
509 oxdefault--fast-enough crypto     -> none
522 44r0nmeta--adzogbo boot2root      -> none
267 relay chains                      -> none
```

Toutes les instances connues et visibles rapportent `none` pour notre équipe, et pourtant le
quota de 2 est annoncé plein. Hypothèses (non vérifiables depuis ce siège, à faible privilège
joueur) :
- Un ou plusieurs challenges `team_instance` sont actuellement **cachés/verrouillés** pour mon
  compte (prérequis non débloqués) mais déjà résolus/débloqués pour un coéquipier qui y a une
  instance active -> invisible dans ma liste `/api/v1/challenges` (qui ne montre que les
  challenges "visible" pour MOI), donc invisible aussi à mon `status` (qui dépend du
  challenge_id, pas d'un listing global).
- Un coéquipier a lancé une instance sur un challenge entretemps retiré/masqué par les
  organisateurs (orpheline côté backend, toujours comptée dans le quota).
- Les hills KOTH (Armory/Citadel, `/plugins/koth/`, IP fixe 13.37.197.230) sont un système
  séparé d'après les notes de session précédentes -- a priori hors de ce quota `team_instancer`,
  mais non vérifiable à 100% sans accès admin.

Dans tous les cas : **ce n'est pas un blocage côté infra cible** (pas de scan agressif, pas de
rate-limit déclenché par nous sur l'instance elle-même -- l'instance n'a jamais démarré), c'est
un quota de ressources PARTAGÉ AU NIVEAU ÉQUIPE qui nécessite une coordination humaine (libérer un
slot côté coéquipier, ou attendre l'expiration naturelle (TTL) d'une instance orpheline).

## Statut : PISTE PRÉCISE EN COURS -- BLOQUÉ SUR QUOTA D'INSTANCES ÉQUIPE (pas blackbox-exhausted)

- Protocole et logique du challenge PAS ENCORE vus (jamais atteint la page d'accueil du service,
  faute d'instance active) -- donc pas de triage TLV/reverse possible tant que l'instance n'est
  pas lancée.
- Action requise côté humain : libérer un slot `team_instancer` (coordination équipe) puis relancer
  `POST /plugins/team_instancer/spawn {"challenge_id":267}` (script prêt, voir artifacts/).
- Prochaine étape dès déblocage : GET sur l'URL `https://<label>.i.ctf.tg/` renvoyée par
  `connection.display`, lire la page d'accueil (documentation des 2 opérations TLV dont l'écho),
  construire les trames hex TLV à la main/avec un script Python, dialoguer avec le service pour
  extraire le flag. Pas de VPN nécessaire a priori (mode `https` = domaine public par équipe, pas
  IP privée 10.100.16.0/24) -- à confirmer une fois l'instance levée.

## Constraints

- Pas de bruteforce/DoS. Pas de scan -p- agressif. Un seul flag soumis par l'agent principal, jamais par ce sous-agent.
