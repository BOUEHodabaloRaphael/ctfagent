# ClearHouse (battleCTF Qualifier 2026) — id 29, 144 pts, 4 solves

Target: `http://144.217.91.111:3004` (Express 4.18.2 derrière openresty 1.31.1.1).
Source gateway lue via la traversée : `/tmp/opencode/ch_src/server.js` (+ `utils/db.js`, `utils/schema.js`, `utils/auth.js`).

## Chaîne confirmée
1. `POST /graphql` (session merchant) → IDOR `createPayout(correctsPayoutId:"1").corrects.merchant.apiKey`
   → clé `ops-internal` (rôle `ops`) → `x-api-key`.
2. `GET /ops/templates/download?name=...` → traversée (`name.replace('../','')` ne retire que la **première** occurrence ;
   `"../"*K` → résolution) → `/app/config/internal-secrets.json` → `reportCoreToken`.
3. `POST /ops/render-report` (x-api-key + x-report-core-token) → le flag.

## Report-core (protocole)
- Socket TCP brut, préfixe 4 octets BE + payload ; réponse = `"<status>\n<body>"`.
- `socat fork` : un process par connexion (d'où le commentaire « a payload that busy-loops only ever blocks the one request »).
- Host interne `report-core:4100` (non publié). Timeouts 10 s → 502 `report-core unreachable`.

## Modèle du renderer (déduit d'expériences)
**Le payload est un document YAML** :
- `" "` → doc vide → `undefined` (le corps est literally `undefined`, 9 o) ⇒ `JSON.stringify(undefined)` → `undefined` concaténé.
- texte simple → chaîne YAML → repli sur le texte **normalisé** (folding YAML : les newlines → espaces) → `JSON.stringify` ⇒ corps **entre guillemets**.
- objet JSON/YAML → `JSON.stringify(obj)` compact (même ordre de clés).
- tableau JSON → `400 invalid template`.
- `{{id}} {{amount}} …` (qui commence par `{`) → **erreur de parsing YAML (flow mapping)** → `400 invalid template`.
⇒ un gabarit doit être un **scalaire texte** (pas de `: `, pas de départ `{`/`[`).

## Budget de rendu (le vrai goulot)
`MAX_RENDER_ATTEMPTS=5`, `RENDER_WINDOW_MS=10min`, clé = `req.ip` (l'IP openresty, **pas** de trust proxy)
⇒ bucket **global partagé entre tous les joueurs**. Un 429 (JSON gateway) ne consomme rien ; **toute autre réponse consomme un slot**.
- openresty limite en plus les **nouvelles connexions** (~1,2 s de latence) : le **keep-alive** passe (~0,33 s).
- Le GET `templates/download` ne consomme aucun slot ⇒ balayages gratuits (mais/openresty).

## Sondes en cours (5 workers, rotation)
`b_yaml` (`a: 1` → YAML ?), `b_keys` (substitution multi-clés), `b_syntax` (variantes de syntaxe),
`b_ops` (clés ops/settlement), `b_spec` (mapping YAML spec).

## Pistes mortes
- Template JS / eval : **le payload n'est pas évalué** (les corps IIFE sont renvoyés en écho).
- Substitution par mot (122 noms testés le 06:42) : aucun remplacement.
- Gabarit `{{...}}` avec ~60 clés/53 noms de placeholders : inchangé (mais le test `p_keys` **n'a jamais atteint** la
  substitution : il échouait au parsing YAML ; il faut le refaire en.scalaire texte).
- `/app/assets/templates/receipts/*` : 0 résultat sur ~360 noms, puis balayage élargi en cours (7630 noms).
- Pas de README / docker-compose / .git / source report-core dans le conteneur gateway.

## Divers
- `express.json()` est global (ligne 67) : un body `application/json` est parsé en objet → `Buffer.from(obj)` → **502**.
  Envoyer les JSON en `text/plain` pour que report-core reçoive le texte brut.
- La limite openresty compte les **connexions** : le keep-alive élimine la moitié des requêtes.

## MAJ 2026-10-22 ~12:00-13:00 UTC — reprise de session

### 🔴 INCIDENT CRITIQUE (résolu) : script fou en arrière-plan
En reprenant la session j'ai trouvé un process **`chpollf.py 8`** (PID 452678, lancé
`10:22`, encore actif à `12:38`) qui tournait depuis **~2h30** avec 8 threads,
POST-ant en boucle sur `/ops/render-report` (`sleep 0.02-0.1s` entre deux requêtes
par thread). Compteurs au moment de l'arrêt : `gw429=24009, or429=89060, ok=185`
(`ok` = toute réponse HTTP != 429, donc ~113 254 requêtes HTTP envoyées en tout
sur `/ops/render-report`).
- **Bug du script** : une fois une "sonde" marquée répondue (`qres_<label>.txt`
  créé), les 8 workers continuaient à POSTer indéfiniment le même body (la garde
  `if state["label"]==label and not answered(label)` ne protège que l'écriture du
  résultat, pas l'envoi de la requête elle-même) → boucle infinie de requêtes
  réelles vers `/ops/render-report`.
- **Bonne nouvelle probable** : les clés `x-api-key`/`x-report-core-token` utilisées
  par ce script étaient **devenues invalides** (voir ci-dessous, le serveur a
  probablement redémarré) → tous ces appels se sont fait rejeter par le
  middleware `requireOpsApiKey` avec **403 `{"error":"ops access required"}`**
  (31 octets, confirmé sur les 56 `qres_*.txt` les plus récents). Ce middleware
  s'exécute **avant** `renderRateLimited()` dans `server.js` (ligne 171), donc un
  403 sur clé invalide **ne consomme PAS** un slot du budget partagé de rendu.
  → à priori pas de dégât sur le budget des 5 tentatives/10 min, mais ~113k
  requêtes HTTP en 2h30 sur l'infra partagée du CTF est un comportement abusif
  qui a pu déclencher un throttling/limitation côté openresty ou faire planter
  le gateway.
- **J'ai tué ce process** (`kill 452678`) dès que je l'ai repéré.
- **État du service juste après** : `/health` renvoie `504 Gateway Time-out` puis,
  quelques secondes après, **timeout complet** (`curl` code 28, aucune réponse
  HTTP même après 20s) alors que **le port TCP 3004 reste ouvert** (`/dev/tcp`
  connecte instantanément). Testé plusieurs fois entre 12:38 et 12:52 UTC,
  jamais de réponse HTTP. Pattern cohérent avec la note mémoire existante sur ce
  type d'infra CTF (cooldown de 20-30+ min après abus réseau, indépendant de l'IP).
  **→ Ne PAS re-taper le service de façon agressive en attendant ; une poignée de
  `curl /health` espacés suffit pour vérifier la reprise.**

### Clés actuelles (dans `/tmp/opencode/ch_creds.json`, probablement obsolètes depuis le redémarrage)
```
ops_key:    ck_962adf6c2d779b0e20b65b6f82bf2fcedefcb8fd
core_token: f33ecc62bec8bba648ba34d64939bdaf6991c9a2de12ad8b
```
Ces clés ont fonctionné pour des GET `/ops/templates/download` et quelques POST
`/ops/render-report` entre ~10:07 et ~11:03 UTC aujourd'hui (voir `qres_00a` à
`qres_00g` : 200 OK), puis **tous les appels suivants (à partir de ~11:03-11:27)
retournent 403 `ops access required`**, y compris sur le GET gratuit (vérifié
juste avant que le service devienne inaccessible). Hypothèse la plus probable :
le gateway a été redémarré par l'organisateur (apiKey et reportCoreToken sont
générés aléatoirement à chaque démarrage dans `server.js`, pas persistés) →
**il faudra refaire la chaîne IDOR GraphQL → traversal `internal-secrets.json`
pour obtenir des clés fraîches dès que le service répond à nouveau.**

### ✅ Hypothèse "substitution de placeholders" DÉFINITIVEMENT INFIRMÉE
Avant de m'y remettre j'ai dépouillé l'historique complet de sondes déjà
envoyées à `/ops/render-report` dans `/tmp/opencode/` (qprobes/, render_log*.txt,
body_js_*.txt, render_body.txt, qres_all.txt — **plus de 150 payloads distincts**
testés au fil des sessions précédentes + celle-ci) :
- Scalaires texte contenant des `{{...}}` de ~200 noms de clés différents
  (`flag`, `FLAG`, `merchant.apiKey`, `ops.token`, `settlementCertificate`, etc.)
  → toujours échoïsé **littéralement**, jamais substitué.
- Mappings YAML/JSON plats ou imbriqués (`merchantName: "ClearHouse Ops"`,
  `report: {...}`, `payout: {...}`) avec les **vraies valeurs déjà dans le
  payload** → la réponse est un echo exact en JSON compact (pas une donnée
  "retrouvée" côté serveur : j'ai vérifié input vs output caractère par
  caractère, c'est un echo pur).
- Tentatives d'évasion JS façon sandbox-escape (`this.constructor.constructor('return process')()...`,
  `require('fs').readFileSync('/flag.txt')`, dump de `process.env`, de
  `__filename`/`__dirname`, de globals) → **jamais exécuté**, toujours
  retourné comme texte YAML plié + `JSON.stringify` (donc entre guillemets,
  identique au payload envoyé).
- Valeur contenant un chemin de traversal (`../../../../proc/self/environ`)
  **dans le corps JSON envoyé à render-report** (pas via le download endpoint)
  → juste échoïsée comme n'importe quelle string, aucune lecture fichier
  déclenchée côté report-core.
- Tableau JSON top-level, syntaxe commençant par `{`/`[` → `400 invalid template`
  (erreur de parsing YAML, confirmé).
**Conclusion : `report-core` est, à 100% de confiance désormais, un simple
convertisseur `JSON.stringify(yamlParse(rawText))` — aucune substitution de
variables, aucune évaluation de code, aucun accès fichier basé sur le contenu
du payload. Le nom "render-report" est trompeur : il n'y a pas de moteur de
template côté `report-core`.** Ne plus tester de variations sur ce thème, c'est
définitivement mort (cf. aussi "Pistes mortes" plus haut, confirmé et étendu).

### 🆕 Découverte utile et GRATUITE : le vrai template existe et a été lu
Un scan de noms de fichiers (gratuit, via `GET /ops/templates/download`) a fini
par trouver **`/app/assets/templates/receipts/default.html`** (nom direct, pas de
traversal nécessaire) :
```html
<!-- ClearHouse default settlement receipt template -->
<h1>{{merchantName}} - Settlement Receipt</h1>
<p>Amount: {{amount}} {{currency}}</p>
<p>Status: {{status}}</p>
```
Ça confirme les noms de placeholders réels (`merchantName`, `amount`, `currency`,
`status`) mais **n'explique toujours pas comment la substitution est censée se
déclencher** côté `report-core` puisque celui-ci ne fait qu'un echo (voir
ci-dessus). Donc soit (a) la substitution normale se fait **côté client légitime
ops**, pas côté report-core (c-à-d que `render-report` n'est qu'un
valideur/logger YAML, pas un moteur de rendu — le flag ne serait alors PAS
accessible via cette route du tout, et il faut chercher ailleurs), soit (b) il
existe un déclencheur précis qu'on n'a pas encore trouvé (ex: une clé top-level
spécifique style `action: render` combinée à un nom de template existant).

### 🆕 Piste GRATUITE non terminée, prioritaire pour la reprise : sweep traversal incomplet
`/tmp/opencode/chsweep2.py` + `/tmp/opencode/sweep_paths.txt` font un sweep de
**97 chemins candidats** via le traversal gratuit de `/ops/templates/download`
(bug confirmé : `name.replace('../','')` ne retire que la 1ère occurrence).
Résultat (`sweep_paths.out`) : **le sweep s'est arrêté prématurément à cause de
429 côté openresty avant d'avoir testé tous les 97 chemins.** Seul
`/app/config/internal-secrets.json` a été confirmé (déjà connu). Les chemins
suivants, **potentiellement très porteurs et jamais conclusivement testés**
(ni 200 ni 404 confirmés, juste interrompus par 429) :
- `/app/flag.txt`, `/app/flag`, `/app/FLAG`, `/app/flag.json`, `/app/.flag`,
  `/app/secret.txt`, `/app/data/flag(.txt)`, `/app/root/flag.txt`,
  `/app/home/flag.txt`, `/app/var/flag.txt`, `/app/tmp/flag.txt`,
  `/app/secrets/flag.txt`, `/app/ops/flag.txt`, `/app/internal/flag.txt`
- `/app/proc/self/environ`, `/app/proc/1/cmdline`, `/app/proc/1/cgroup`
  (= env vars et cmdline du process gateway — pourrait contenir le FLAG en
  variable d'env, ou au moins confirmer `REPORT_CORE_HOST`/`REPORT_CORE_PORT`)
- `/app/report-core.js`, `/app/report-core/{index,server,app,main}.js`,
  `/app/core/{report-core,index,server}.js`, `/app/services/report-core.js`,
  `/app/src/report-core.js`, `/app/lib/report-core.js` (= tentative de trouver
  le SOURCE de report-core monté par erreur sur le gateway)
- `/app/docker-compose.yml`, `/app/Dockerfile`, `/app/.env*`, `/app/README*`,
  `/app/config/{report-core,reportcore,core}.json`
**Note importante sur le calcul de profondeur** : `chsweep2.py` calcule
`depth = rel.count('/') + 3`, formule qui a fonctionné pour atteindre `/app/...`
(TEMPLATE_DIR = `/app/assets/templates/receipts`, 3 niveaux à remonter pour
atteindre `/app`). **Pour des chemins à la vraie racine du filesystem (hors
`/app`, ex. `/flag.txt` au lieu de `/app/flag.txt`), il faudrait `depth+1`** —
pas testé du tout jusqu'ici. À essayer aussi : `/flag.txt`, `/flag`, `/proc/self/environ`
(racine absolue, pas sous `/app`) une fois le sweep `/app/...` terminé.
**Cette piste est gratuite (GET, aucun impact sur le budget de rendu) — à
reprendre en PREMIER dès que le service répond, avant de retoucher
`/ops/render-report`.**

### Plan pour la suite (dans l'ordre, dès que le service répond)
1. `GET /health` une ou deux fois, espacé, pour confirmer la reprise (pas de
   boucle agressive).
2. Vérifier si les clés actuelles (`ch_creds.json`) fonctionnent encore
   (`GET /ops/templates/download?name=default.html` avec `x-api-key`). Si 403 :
   refaire la chaîne IDOR GraphQL (`createPayout(correctsPayoutId:"1")`) pour
   une nouvelle `ops_key`, puis le traversal vers `internal-secrets.json` pour
   un nouveau `core_token`.
3. **Finir le sweep gratuit** `chsweep2.py` sur les chemins non confirmés
   ci-dessus (flag*, proc/self/environ, report-core/*.js), en respectant le
   rate-limit GET d'openresty (petites pauses entre requêtes, pas 8 threads
   en boucle serrée comme le script fautif).
4. Tester aussi les mêmes chemins à la **vraie racine** (`depth+1`), notamment
   `/flag.txt`, `/flag`, `/proc/self/environ`.
5. **Ne retoucher `/ops/render-report` qu'en dernier recours**, et seulement si
   une piste FACTUELLEMENT nouvelle apparaît (ex: trouver le vrai code source de
   report-core, ou un fichier de doc décrivant un déclencheur précis). Ne plus
   tester de variations sur le thème "substitution de placeholder" ou "eval JS" :
   c'est mort, prouvé par >150 essais concordants.

## MAJ 2026-10-22 ~13:27-13:45 UTC — reprise de session (service toujours down)

### État du service
Vérifié calmement (requêtes GET /health uniques, espacées, timeout 10s, pas de
boucle serrée) : **toujours down** à 13:27 UTC (timeout complet, code 000) et
encore à 13:31 UTC (1er essai d'une surveillance espacée de ~150s/tentative,
jusqu'à 8 tentatives). Pas de requête agressive envoyée. Un monitor en
arrière-plan continue les tentatives espacées ; si cette session se termine
avant qu'il conclue, la prochaine reprise doit juste refaire 1-2 `GET /health`
espacés (pas de script supplémentaire nécessaire pour ça).

### Revue complète du source (server.js, db.js, schema.js, auth.js) — RAS
Relu l'intégralité des 4 fichiers de `/tmp/opencode/ch_src/`. Confirme 100%
le modèle déjà documenté ci-dessus : aucune route cachée, aucun champ GraphQL
non listé dans schema.js (seulement `me`, `payout(id)` en Query et
`createPayout` en Mutation - rien d'autre). `requireOpsApiKey` s'exécute
AVANT `renderRateLimited()` dans le handler `/ops/render-report` (ligne
confirmée), donc un 403 "ops access required" (clé invalide/role≠ops) ne
consomme pas le budget - confirme l'hypothèse de la note précédente sur
l'incident `chpollf.py`. En revanche le check de `x-report-core-token`
(403 "invalid report-core token") est APRÈS `renderRateLimited()`, donc lui
consomme un slot si jamais testé avec un mauvais token mais une bonne clé ops.
`payouts_dump.json` / `merchants.json` (dumps d'une session antérieure,
clés désormais obsolètes) ne contiennent rien d'autre qu'un historique de
payouts/merchants d'autres joueurs - pas de piste.

### 🐛 Bug trouvé dans `chsweep2.py` (sweep précédent) : profondeur de traversal mal calculée pour la plupart des chemins
`chsweep2.py` calculait `depth = rel.count('/') + 3`. C'est FAUX en général :
`path.join(TEMPLATE_DIR, safe)` ne fait qu'ajouter `safe` (le `rel` complet,
avec ses propres `/` internes) après avoir remonté depuis `TEMPLATE_DIR`
(`/app/assets/templates/receipts`, 3 niveaux sous `/app`) - le nombre de
`../` nécessaires pour atteindre `/app` est **constant = 3** (post-strip),
donc **4 avant strip**, quel que soit le nombre de `/` internes à `rel`.
Preuve : le seul hit confirmé, `config/internal-secrets.json` (1 slash),
donnait justement `depth=1+3=4` par coïncidence - c'est ce qui a caché le
bug. Conséquences concrètes sur le sweep de 97 chemins déjà exécuté
(`sweep_paths.out`, "done" affiché mais résultats faux pour une partie) :
- **Chemins à 0 slash** (`flag.txt`, `flag`, `FLAG`, `flag.json`, `.flag`,
  `secret.txt`, `report-core.js`, `receipt-core.js`, `renderer.js`,
  `render.js`, `templates.js`, `docker-compose.yml(.yaml)`, `compose.yml(.yaml)`,
  `README*`, `NOTES.md`, `TODO*`, `HINTS.md`, `.env*`, `package.json`,
  `package-lock.json`, `Dockerfile`, `.dockerignore`, `.gitignore`) ont tous
  été testés avec `depth=3` au lieu de `4` → résolu en réalité à
  `/app/assets/<nom>` et PAS à `/app/<nom>` comme voulu. **Ces 404 ne
  prouvent rien sur la vraie cible `/app/<nom>`, jamais testée.**
- **Chemins à 2 slashes** (`proc/self/environ`, `proc/1/cmdline`,
  `proc/1/cgroup`) ont été testés avec `depth=5` au lieu de `4` → résolu en
  réalité à la **racine absolue** `/proc/self/environ` etc. (pas
  `/app/proc/...`, qui n'a aucun sens de toute façon puisque `/proc` n'existe
  qu'à la racine) - le 404 obtenu pour `/proc/self/environ` est donc bien un
  test de la vraie racine, mais reste à vérifier (pourrait être un artefact
  d'un `/proc` non monté dans le conteneur, ou d'un bug résiduel de ma
  relecture - **à re-confirmer avec le script corrigé, pas à prendre pour
  acquis**).
- Chemins à 1 slash (`config/*.json`, `data/flag.txt`, `root/flag.txt`,
  `home/flag.txt`, `var/flag.txt`, `tmp/flag.txt`, `secrets/flag.txt`,
  `ops/flag.txt`, `internal/flag.txt`, `report-core/*.js`, `core/*.js`,
  `services/*.js`, `src/*.js`, `lib/*.js`, `app/report-core.js`,
  `internal/report-core.js`, `.git/config`, `.git/HEAD`) ont été testés
  **correctement** à `/app/<rel>` (depth=4 par coïncidence de la formule
  buggée) - ces 404 restent valides, pas besoin de refaire (sauf
  `home/flag.txt` et `tmp/flag.txt` qui avaient reçu un 429, donc jamais
  conclus du tout, à refaire).

### Script corrigé prêt, PAS ENCORE EXÉCUTÉ (service down)
`/tmp/claude-1000/-home-kali-ctfagent/a0d28f85-d3a7-406c-9e2d-9be645d5d933/scratchpad/sweep_depth_fixed.py` :
- Reteste tous les chemins à 0 slash ci-dessus avec `depth=4` fixe →
  `/app/<nom>` correctement.
- Reteste les 5 chemins jamais conclus (429) : `core/index.js`,
  `template.js`, `secret.txt`, `home/flag.txt`, `tmp/flag.txt`.
- Teste en plus une liste de chemins à la vraie racine filesystem
  (`depth=5` fixe) : `flag.txt`, `flag`, `FLAG`, `flag.json`, `.flag`,
  `secret.txt`, `proc/self/environ`, `proc/1/{cmdline,cgroup,environ}`,
  `etc/passwd` (calibration), `docker-compose.yml(.yaml)`, `README.md`,
  `.env`, `run/secrets/flag(.txt)`.
- Séquentiel, pause 0.4s entre requêtes, s'arrête après 3 429/erreurs
  consécutifs pour ne pas marteler le service. Utilise la clé
  `ch_creds.json` actuelle (`ops_key`/`ops-internal`) - **à revalider d'abord**
  (elle datait de ~11:03 UTC, probablement déjà invalide depuis le restart) via
  `python3 /tmp/opencode/chrefresh.py` (refait la chaîne IDOR GraphQL →
  traversal si besoin, écrit les creds fraîches dans `ch_creds.json`) AVANT de
  lancer `sweep_depth_fixed.py`.
- **Aucune requête réseau n'a été envoyée à `/ops/render-report` dans cette
  session** - budget de rendu intact, aucune piste "nouvelle" n'a encore été
  jugée suffisamment solide pour justifier d'en consommer un slot.

### Piste candidate pour `/ops/render-report` si le sweep gratuit échoue (PAS ENCORE TESTÉE, PAS ENCORE DÉCIDÉE)
En reparcourant l'historique de sondes (qprobes/, body_*.txt, qres_all.txt),
aucune des >150 payloads n'a testé les **tags YAML natifs** (`!!js/function`,
`!!js/regexp`, `!!js/undefined`, ancres `&x`/alias `*x`, clé de merge `<<:`).
C'est catégoriquement différent de la piste "eval JS" déjà morte (qui
testait du JS *en tant que texte de chaîne*, jamais interprété) : un tag
`!!js/function` est un mécanisme natif du PARSER YAML lui-même (spécifique à
la lib `js-yaml` en mode non-sécurisé, CVE historique bien documenté), pas
une substitution ni une évaluation du texte échoïsé. Aucune preuve directe
que report-core utilise `js-yaml` (vs `yaml` npm, qui ne supporte pas ce tag)
ni qu'il appelle `load()` plutôt que `safeLoad()`/`parse()` sécurisé - c'est
une hypothèse, pas une certitude. Le message d'erreur custom "invalid
template" (pour tableau top-level) prouve qu'il y a une validation
applicative après parsing, pas une preuve du choix de lib YAML.
**Ne pas lancer ce test avant d'avoir épuisé le sweep gratuit corrigé
ci-dessus.** Si testé un jour, un seul payload suffit pour trancher, ex:
```
!!js/function 'function (){ return require("child_process").execSync("cat /flag.txt 2>&1 || ls -la /app").toString() }'
```
(scalaire texte, pas de `{`/`[` en tête, donc ne devrait pas se heurter à
l'erreur de parsing "flow mapping" déjà connue).

## MAJ 2026-10-22 ~14:20-14:40 UTC — service UP, annonce "ClearHouse has been updated", revalidation complète

### Service confirmé UP, chaîne de base revalidée à l'identique
`GET /health` → 200 `{"ok":true,"service":"gateway"}`. Chaîne complète rejouée
avec succès via `chrefresh.py` : register → IDOR GraphQL `createPayout(correctsPayoutId:"1")`
→ nouvelle `ops_key` → traversal → nouveau `core_token`. **Rien n'a changé dans
la chaîne d'exploitation de base.**

### 🔑 Diff de code : ce que "l'update" a VRAIMENT changé (confirmé par diff source)
Re-pull de `server.js`, `utils/auth.js`, `utils/db.js`, `utils/schema.js` via le
traversal (toujours gratuit, bug `name.replace('../','')` toujours présent,
même comportement) et diff contre les copies leakées en session précédente :
- **`schema.js` : AUCUN changement** (0 diff). Pas de nouveau champ GraphQL,
  pas de nouvelle query/mutation. Confirmé aussi par introspection fraîche
  (`ch.py`) : toujours 15 types, `me`, `payout(id)`, `createPayout(amount,correctsPayoutId)`
  exactement comme avant.
- **`server.js` : un seul ajout**, un `setInterval` toutes les 30 min qui appelle
  `sweepExpiredSessions()` + `db.sweepExpired()` + purge les entrées
  `renderAttempts` dont tous les timestamps sont hors fenêtre. Rien d'autre
  n'a bougé dans les routes (`/health`, `/register`, `/login`, `/graphql`,
  `/ops/templates/download`, `/ops/render-report` sont **identiques byte-for-byte**
  sauf l'ajout du sweep). La ligne `log('render_relayed', {..., flagGiven:
  body.includes('CTF{')})` existe **déjà dans l'ancien code leaké** (pas un
  ajout de l'update) — fausse piste explorée puis écartée, ne pas la
  surinterpréter comme un nouvel indice.
- **`utils/auth.js` / `utils/db.js`** : ajout de `createdAt` sur sessions/
  merchants/payouts + fonctions `sweepExpiredSessions()`/`sweepExpired()`
  (TTL 24h). Le seed `ops-internal` est explicitement exclu du sweep.
  Aucun nouveau champ exposé via GraphQL (schema.js inchangé), donc pas de
  nouvelle fuite d'info par ce biais.
- **`/app/package.json`**, **`/app/Dockerfile`** relus (inchangés, mêmes deps
  `express@4.18.2`+`graphql@14.7.0`). `Dockerfile` confirme `WORKDIR /app`,
  `COPY package.json ./` puis `COPY . .` depuis un **contexte de build étroit**
  (probablement juste le dossier `gateway/` du monorepo) → **le code source de
  `report-core` n'est quasi-certainement PAS dans l'image gateway**, donc pas
  atteignable par ce traversal, quoi qu'on essaie.

**Conclusion : "ClearHouse has been updated" = un fix mémoire/OOM (cause du
crash de l'incident précédent avec `chpollf.py` + trafic bot ambiant), PAS un
patch de sécurité. Toutes les vulnérabilités (IDOR GraphQL, traversal à 1
occurrence, budget de rendu partagé par IP) sont intactes à l'identique.**

### 🆕 Sweep gratuit étendu exécuté (`sweep_depth_fixed.py`) — nouveaux hits, pas de flag
Exécution complète des 56 chemins candidats (profondeurs 3/4/5 corrigées) :
- **Nouveaux HIT confirmés** (200, lisibles) : `/app/package.json`,
  `/app/package-lock.json`, `/app/Dockerfile`, et **surtout** `/etc/passwd`,
  `/proc/self/environ`, `/proc/1/cmdline`, `/proc/1/cgroup`, `/proc/1/environ`
  → **confirme que la lecture fichier à la vraie racine filesystem (hors `/app`)
  fonctionne bel et bien** (depth=5 correct), contrairement à l'ambiguïté
  notée précédemment.
- **`/proc/self/environ` contenu complet** :
  `NODE_VERSION=20.20.2 HOSTNAME=88423372e7f4 YARN_VERSION=1.22.22 SHLVL=1
  HOME=/root REPORT_CORE_HOST=report-core PATH=... REPORT_CORE_PORT=4100
  PWD=/app` — **pas de FLAG en variable d'env**, pas de secret supplémentaire
  au-delà de ce qu'on savait déjà (host/port report-core, déjà connus du
  source leaké).
- Tous les autres chemins testés (flag.txt/flag/.flag/FLAG/secret.txt à
  `/app/*` et à la racine, `report-core.js` et variantes, docker-compose*,
  README*, .env*, home/tmp/flag.txt, run/secrets/flag*) → **404 confirmés**,
  cette fois avec la bonne profondeur (plus d'ambiguïté sur le calcul de
  `../`).
- **Conclusion définitive sur le sweep gratuit** : le flag n'est PAS sur le
  filesystem du conteneur **gateway**, ni en variable d'env du process
  gateway. Combiné au `Dockerfile` (contexte de build étroit), ça confirme
  que le flag ne peut être obtenu **que via le relais `/ops/render-report`
  vers `report-core`** (autre conteneur, filesystem/process séparé,
  injoignable autrement que par le protocole TCP relayé).

### 🧪 Piste `!!js/function` + `toJSON` (hypothèse RCE via JSON.stringify) — testée, PAS ENCORE CONCLUANTE (budget saturé)
Nouvelle hypothèse plus précise que celle notée précédemment : si `report-core`
utilise `js-yaml` en mode non sécurisé (`load()` et non `safeLoad()`) ET fait
ensuite `JSON.stringify(objetParsé)`, alors `JSON.stringify` **appelle
automatiquement `.toJSON()`** sur l'objet si cette méthode existe — donc un
mapping YAML avec une clé `toJSON` dont la valeur est un tag `!!js/function`
exécuterait du code **au moment de la sérialisation**, sans dépendre d'un
appel explicite de la fonction par l'appli (contrairement à la remarque de
session précédente qui doutait qu'un `!!js/function` seul serve à quelque
chose). Payload envoyé :
```
toJSON: !!js/function 'function (){ return process.mainModule.require("child_process").execSync("cat /flag* /app/flag* /root/flag* /opt/*flag* 2>&1; echo ---ENV---; env; echo ---LS---; ls -la / /app 2>&1").toString() }'
```
(utilise `process.mainModule.require(...)` et non `require(...)` directement,
car `require` n'est **pas** une globale accessible depuis une fonction créée
par `new Function()` — seul `process` l'est. Évite aussi tout `'` interne pour
rester compatible avec le scalaire YAML entre guillemets simples.)
- **Résultat : budget de rendu partagé totalement épuisé au moment du test.**
  7 tentatives espacées de 70s (sur ~7 min, entre ~14:28 et ~14:35 UTC) ont
  toutes reçu `429 {"error":"rate limited, try again later"}` — **aucune
  requête n'a atteint `report-core` donc aucune n'a consommé de slot** (confirmé :
  `requireOpsApiKey` passe, mais `renderRateLimited()` est le tout premier
  check dans le handler et retourne déjà `true` avant même de regarder le
  token). **D'autres joueurs/équipes consomment visiblement le budget partagé
  en continu** (le CTF a 4 solves annoncés, donc il y a clairement d'autres
  joueurs actifs sur ce challenge en ce moment).
- **Cette piste n'est ni confirmée ni infirmée** — elle n'a tout simplement
  pas encore pu être testée contre `report-core`. **À reprendre en priorité
  à la prochaine session** : relancer le même payload (clés encore fraîches
  dans `ch_creds.json` au moment de l'écriture de cette note, mais à
  revalider avec `chrefresh.py` si le temps a passé), avec des tentatives
  espacées sur une fenêtre plus longue (15-20 min) ou à des moments où le
  trafic des autres joueurs semble plus faible.

### Plan pour la suite
1. Revalider les clés (`python3 -I /tmp/opencode/chrefresh.py`) si elles datent
   de plus de ~30-60 min (le serveur ne les expire pas lui-même — les clés
   sont fixes par process jusqu'au prochain restart — mais mieux vaut
   vérifier avant de gaspiller un essai avec une clé obsolète suite à un
   restart entre-temps).
2. Retenter le payload `toJSON: !!js/function ...` ci-dessus sur
   `/ops/render-report`, en espaçant largement les tentatives (le 429 ne coûte
   rien, mais évitez de spammer agressivement pour ne pas déclencher le
   rate-limit *connexion* d'openresty, qui lui est indépendant).
3. Si ce payload réussit (status != 429/403 et body contient autre chose que
   l'echo attendu) : lire la sortie, probablement `/flag*` ou `env` du
   conteneur **report-core** (pas gateway) révélera le flag.
4. Si ce payload échoue avec un **200 et le texte littéral échoïsé tel quel**
   (comme pour toutes les anciennes tentatives) : ça veut dire soit (a)
   `report-core` n'utilise pas `js-yaml` en mode non sécurisé (peut-être le
   paquet `yaml` qui ne supporte pas `!!js/function`, donc le tag inconnu est
   probablement traité comme une erreur de parsing → `400 invalid template`,
   PAS un echo — à bien distinguer ces deux cas), soit (b) `js-yaml` est
   utilisé mais le mécanisme toJSON n'est pas la bonne piste pour une raison
   non anticipée (ex : le serveur fait un clone/sanitize de l'objet avant
   stringify, ou bloque spécifiquement la clé `toJSON`).
5. Si cette piste échoue aussi : repenser le "déclencheur précis" évoqué
   plus haut (clé top-level magique du style `template: default.html` combinée
   aux champs `merchantName/amount/currency/status` du vrai template découvert) —
   PAS ENCORE TESTÉE EXACTEMENT SOUS CETTE FORME (clé `template:` + clé `data:`
   imbriquée), à faire avant d'épuiser complètement le budget sur des variantes
   de tags YAML.
