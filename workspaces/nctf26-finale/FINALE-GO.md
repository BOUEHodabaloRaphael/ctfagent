# FINALE-GO — séquence d'activation au mot « finale » (NCTF26, 19-20 nov, arena.ctf.tg)

Quand l'utilisateur tape **« finale »** (feu vert permanent pour la durée de l'épreuve, pas de pause de
confirmation sur les actions de routine), exécuter automatiquement, **DANS CET ORDRE**, via la méthode
**headless** (jamais le groupe Chrome pour arena.ctf.tg — cf. [[nctf26-trigger-protocol]]).

Plateforme confirmée le 2026-11-15 : **arena.ctf.tg**, format MIXTE — onglets **Challenges (jeopardy) +
Défense (A&D) + KOTH**, flags `NCTF{...}`, « Mes instances » par équipe. KoTH ouvre 19 nov 10:00 (Lomé).

## 0bis. Préflight (veille / juste avant) — `bash src/tools/ctf/finale_eve_check.sh`
Revérifie tout (accès headless, expiry session, syntaxe des 2 toolkits, prépa/mémoire) → GO / À CORRIGER.
Lecture seule. À lancer quand le user me lance la veille ou avant le coup d'envoi.

## 0. Connexion (headless, pas Chrome)
- Vérifier l'accès : `python3 src/tools/ctf/nctf26_client.py list`. Si redirigé vers `/login` → la session
  a expiré : demander à l'utilisateur des cookies frais (session/cf_clearance/nctf_d) ou NCTF_USER/NCTF_PASS,
  régénérer `src/tools/ctf/nctf26_storage_state.json`. (Session actuelle valable jusqu'au 23 nov.)

## 1. Charger le contexte (sans attendre qu'on le demande)
- `workspaces/nctf26-finale/FINALE-PREP-MASTER.md` (§1 plan A&D + KoTH, §2 techniques par catégorie),
  `discord-harvest/AFRICC-AD-PLAYBOOK-FOR-NCTF.md`, mémoires [[nctf26-finale-ad-playbook]],
  [[ctf-african-scene-technique-patterns]]. Auto-consulter le catalogue pour CHAQUE challenge/service.

## 2. Reconnaissance plateforme (headless)
- Énumérer **Challenges**, **Défense**, **KOTH**, **Mes instances**, **Scoreboard**. Noter : IPs des
  services A&D de notre équipe + adverses, l'API de la/les colline(s) KoTH, l'endpoint de soumission.

## 3. KoTH — tenir la colline DÈS t+0 (tenir du début à la fin)
**MODÈLE PROBABLE (recherche 2026-11-15) : KoTH CTFd = "contrôler la BOX / posséder le FICHIER roi".**
Un agent sur la box reporte le propriétaire (`/status` → `{"data":{"identifier":"<équipe>"}}`), CTFd sonde
et donne les points au propriétaire à CHAQUE tick (cf. 0xThiebaut/ctfd-koth = "qui possède le fichier", +
KoTH officiel CTFd). = exactement le "Citadel/king file" du préqual. Donc :
- **Voie PRINCIPALE (own-the-box)** : identifier la box cible (IP via "Mes instances"/page KOTH) →
  `bash src/tools/ctf/koth_finale/recon_target.sh <IP>` (ports/versions/énum rapide) → l'exploiter
  → **root** : copier `src/tools/ctf/koth_finale/privesc-arsenal/` sur la cible → `./bin/traitor-amd64 -a`
  (auto) ; sinon cheatsheet `knowledge/patterns/misc/linux-privesc-quick-wins.md` (sudo/GTFOBins, SUID, caps,
  cron inscriptible, PwnKit `pwnkit/PwnKit`, Dirty Pipe `dirtypipe/dirtypipez`, container escape) →
  `KOTH_TOKEN=<notre_id> KING_FILE=<ex:/koth/king> KING_FILE2=<ex:/king/king.txt> bash onbox_persist.sh`.
  La persistance réécrit le fichier roi en boucle (setsid + cron @reboot) → **tient TOUTE SEULE jusqu'au reset,
  même sans terminal ouvert** → user+agent libres pour Défense + challenges. C'est la cible n°1 à t+0.
- **Voie FALLBACK (HTTP-claim)** si une colline est une éco/claim HTTP (comme le "Throne/Réseau Fortune" du
  préqual) : `python3 recon_koth.py` → remplir `hill.env` → **user lance** `bash run_hold.sh` (watchdog, log koth.log).
- **recon à t+0** : `cd src/tools/ctf/koth_finale && python3 recon_koth.py` pour savoir LEQUEL des deux modèles
  (observe le trafic + IP d'instances + notre identifiant d'équipe), puis appliquer la bonne voie.
- Contrainte géo-IP possible (préqual = IP togolaise) → sur site à Lomé c'est OK.

## 4. Défense / A&D
- Remplir `src/tools/ctf/attack_defense_toolkit/config.py` avec l'infra réelle (TEAMS, SUBMIT_URL,
  `SUBMIT_HEADERS={"Authorization":"Bearer <token>"}`, `SUBMIT_JSON_KEY="flags"`+`SUBMIT_JSON_VALUE_LIST=True`
  pour la forme ICC, FLAG_REGEX=`NCTF\{...\}`, SERVICES).
- Doctrine : **reverse d'abord (15-20 min) → exploit en boucle sur TOUTES les équipes AVANT de patcher →
  patcher nos services sans casser le SLA → ne jamais couper `sla_monitor.py`.** (submitter.py corrigé :
  retry seen-only-on-success + forme liste.)

## 5. Jeopardy
- Router par catégorie (web/pwn/rev/crypto/forensics/misc/osint/ml) via le catalogue + skills ; soumettre
  via `nctf26_client.py submit <id> <flag>`. Une seule soumission par flag, respecter le rate-limit.

## 6. Journalisation (obligatoire, instruction user)
- À CHAQUE flag confirmé accepté → bloc immédiat dans `workspaces/nctf26-finale/solve-log.md` (cible,
  catégorie, vuln, technique/payload, flag, notes), sans bloquer la boucle. `ctf-knowledge-capture` complet
  pendant un creux / après le match.

## Garde-fous (jamais levés par « finale »)
- Jamais de bouton « abandon » sans décision humaine. Jamais les identifiants user dans un service tiers hors
  arena.ctf.tg. KoTH/persistance : **colline in-scope uniquement, pas de DoS, pas d'attaque d'autres équipes /
  de l'infra orga**. Objectif = l'ÉQUIPE finit devant.
