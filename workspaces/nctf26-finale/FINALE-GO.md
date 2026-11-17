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
- Énumérer **Challenges**, **Défense**, **KOTH**, **Mes instances**, **Scoreboard**. Noter : nos IPs
  d'instances (les autres équipes ne sont **pas** joignables — le VPN ne route que `10.100.16.0/24`),
  l'API/les ports de la/les colline(s) KoTH, et l'endpoint de soumission jeopardy.

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
  préqual) : `python3 recon_koth.py` → je remplis `hill.env` → **user lance UNE commande** :
  `bash koth_hold.sh start` (détaché + watchdog + log ; `status` / `stop` pour suivre et arrêter).
- **Voie SSH + fichier « king »** (`ssh -p <port> player@<ip>`) : `bash koth_ssh_takeover.sh` — root →
  jeton dans le king file → persistance on-box (`/usr/lib/.koth-hold` + `cron @reboot`) → **re-assertion
  toutes les 20 s** (survit aux resets du conteneur). `--once` pour une prise unique, `--purge` pour
  neutraliser la persistance rivale sur cette box.
- **Vérif du kit avant le jour J** : `bash koth_hold.sh selftest` (fausse colline + rival, hors-ligne).
- **recon à t+0** : `cd src/tools/ctf/koth_finale && python3 recon_koth.py` pour savoir LEQUEL des deux modèles
  (observe le trafic + IP d'instances + notre identifiant d'équipe), puis appliquer la bonne voie.
- Contrainte géo-IP possible (préqual = IP togolaise) → sur site à Lomé c'est OK.

## 4. Défense (`/plugins/defend/`) — patch-and-hold contre un ROBOT, PAS de flag

⚠️ **Modèle CORRIGÉ le 2026-11-16** (règles réelles lues headless : `FINALE-PREP-MASTER.md` §1 +
`platform-rules/d-fense.txt`). Le modèle AFRICC « exploiter toutes les équipes + soumettre des flags »
**ne s'applique PAS** : le VPN d'équipe ne route que `10.100.16.0/24` (aucun accès inter-équipes) et la
défense ne se valide pas par un flag.

- **1 box/joueur**, mêmes creds SSH pour toute l'équipe → SSH via le WireGuard d'équipe → corriger sans
  casser les usages légitimes → **demander la vérification au robot**. **Aucun flag à soumettre** ;
  1ʳᵉ vérif réussie = challenge validé.
- **Séquence** : `tools-offline/defkit.sh backup` (t+0, AVANT tout) → patch app à la main dans `patchable/`
  (paramétrer SQLi, `jwt.verify({algorithms:['HS256']})`, whitelist de chemins) →
  `cp usecases.sh /root/.defkit/ && ./defkit.sh fix` (**sans `-y`**) → `./defkit.sh check` (SLA vert ? sinon `rollback`).
- ⚠️ **Adapter `usecases.sh`** (`UC_HOST`/`UC_WEB_PORT`/`UC_PWN_PORT`) **avant le premier `fix`**, sinon on casse
  le checker en silence. Le checker/SLA ne doit JAMAIS être bloqué.
- **Défense continue** : toutes les **5 min** le robot attaque la box de prod ; si elle tient = **+5 pts**.
  Délai entre deux vérifs = **120 s**. « Box de prod » = la dernière box vérifiée (reste en service).
  **Relancer l'instance = correctifs perdus.**
- **Challenge « audit »** : un rapport de pentest est fourni → chaque constat réellement corrigé (le robot ne
  le reproduit plus ET les usages passent) = points, compté **1×/équipe**.
- `attack_defense_toolkit/submitter.py` (forme `{"flags":[...]}`) = **jeopardy uniquement** (`nctf26_client.py`),
  **pas** la défense. Les valeurs `SUBMIT_JSON_KEY`/`SUBMIT_JSON_VALUE_LIST` de `config.py` ne servent qu'à ça.
- Règles d'or : patch réversible d'abord, jamais de kill aveugle, preuve (pcap/log) avant action, `rollback` prêt.

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
- **Accès plateforme délégué (décision user 2026-11-16, choix « A »)** : l'agent utilise la session
  (`src/tools/ctf/nctf26_storage_state.json` + `src/tools/ctf/.env`) **en headless uniquement**, et en
  **lecture seule avant l'ouverture**. **Confirmation explicite du user requise avant** : toute soumission de
  flag, tout lancement/destruction d'instance, tout téléchargement de config VPN, toute modification de
  profil/équipe. Aucun secret (mot de passe, cookies, clé VPN) n'est recopié dans le chat ni dans un commit.
