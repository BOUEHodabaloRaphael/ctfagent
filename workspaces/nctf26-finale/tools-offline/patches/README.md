# Patchs app pré-écrits — juice-todo & pwn-sample (A&D)

Patchs **exacts**, prêts à coller dans `patchable/`, écrits depuis la **vraie source** des box
dry-run AFRICC (`../../discord-harvest/downloads/africc-ad-live/extracted/`). Testés le 2026-11-16.

⚠️ La finale réutilise *le concept*, pas forcément ces fichiers à l'identique. Si les noms/lignes
diffèrent le jour J, **ré-applique la même logique** (c'est la logique qui compte, pas le copier-coller).
Doctrine : exploit d'abord, puis patcher ; chaque patch préserve les flux SLA listés plus bas.

---

## juice-todo (Node/Express/EJS/SQLite) — `juice-todo/`

Remplacer les 3 fichiers dans `patchable/`, puis **redémarrer le service** (`docker compose restart`
ou équivalent). Flags : `/flag1` (SQLi, 5-hex admin, API secret), `/flag2` (`GET /api/admin/flag`).

| Fichier | Vuln neutralisée | Correctif |
|---|---|---|
| `app.js` | **ATTACK A — SQLi** `INSERT ... VALUES ('${task}')` (l.69) → `' \|\| (SELECT flag FROM flags) \|\| '` leak flag1 | requête **paramétrée** `VALUES (?)`, `[task]` |
| `apiRoutes.js` | **ATTACK B — JWT** `jwt.decode` (pas de vérif signature) → forge token admin → flag2 | `jwt.verify(token, JWT_SECRET, {algorithms:['HS256']})` |
| `adminRoutes.js` | **ATTACK C** — auth = 5 hex de md5 (brute ~20 bits) **+ fuite `ADMIN_HASH`** dans le 401 | compare **hash complet** en temps constant (`timingSafeEqual`), **retire le hash** du message |
| `adminRoutes.js` | **ATTACK D** — `/admin/file` path traversal `path.join('/', name)` → `name=flag2` | confine à `__dirname/files`, rejette `..` `/` `\`, `basename` only |

**Flux SLA à NE PAS casser** (vérifiés, inchangés) :
- `GET /` et `GET /todos` (rendu EJS), `POST /todos` (ajout + redirect `/`), tâche vide → **400**.
- `POST /api/token` (émission JWT via `x-api-key: demo`), `GET /api/todos/:id` avec token valide.
- Les requêtes paramétrées acceptent toujours les tâches normales ; le token `demo` marche toujours.

---

## pwn-sample-kun (managed patch — filtre ligne-à-ligne) — `pwn-sample/firewall_filter.py`

**Seul fichier éditable.** Ce n'est PAS un proxy : il lit l'entrée ligne par ligne et répond
`PASS` (laisser passer au binaire) ou `KILL` (couper la connexion). Flag : `/flag`.

### Pièges du modèle (respectés dans le patch)
1. **Fail-open si le filtre meurt** : une exception non rattrapée tue le process → le wrapper
   laisse TOUT passer. → tout `main()` est sous `try/except` qui **fail CLOSED** (`KILL`).
2. **Contrat 1 verdict par ligne** : le wrapper lit exactement un `PASS`/`KILL` par ligne envoyée.
   Le filtre doit mirrorer l'état des `fgets` du binaire. → compteurs de sortie préservés à l'identique.
3. **Request-smuggling** (`atoll("1garbage")==1`) : lecture numérique identique au binaire.

### Vulns neutralisées (mappées à `prog.c`)
| cmd | Bug C | Règle KILL |
|---|---|---|
| 1 `stack_bof` | `buf[16]`, `fgets(buf,1000)` | input > 15 octets |
| 2 `fsb` | `printf(buf)` | input contient `%` |
| 4 `do_free` | `free` sans contrôle d'alloc | free d'un idx non alloué (double/invalid free) |
| 5 `heap_write` | `fgets(ptr, size+1000)` | data > `BUF_SIZE[idx]-1` |
| 7 `file_read` | `"/data/"+name`, aucune validation | name contient `/`, `..`, `\`, NUL |
| 8 `admin_backdoor` | `system(cmd)` + `fgets(cmd,104)` dans `cmd[64]` | `sha256(pw)==correct_hash` **OU** ligne command > 63 octets |
| 3/6/9 | malloc / file_write (C valide `[A-Za-z]`) / address_leak (feature) | **PASS** (bénins) |

### Déploiement
Copier `firewall_filter.py` dans `patchable/`. **Pas de recompilation** (c'est du filtre). Le wrapper
relit le fichier à chaque connexion.

### Tests (rejouables)
```
printf '1\nhello\n'            | python3 firewall_filter.py   # PASS PASS
printf '1\nAAAAAAAAAAAAAAAAAAAAAAAA\n' | python3 firewall_filter.py   # PASS KILL
printf '7\n../flag\n'          | python3 firewall_filter.py   # PASS KILL  (traversal bloqué)
printf '7\nmyfile\n'           | python3 firewall_filter.py   # PASS PASS  (lecture /data légitime)
```
(le `PASS` final éventuel en test = artefact d'EOF, absent en jeu réel.)

**Flux SLA à surveiller** : si le checker exerce cmd7 sur un fichier `/data/<alnum>`, cmd8 avec
mauvais mot de passe + commande courte, ou le menu normal → tout reste **PASS**. Les seules
hypothèses à valider le jour J : le checker ne teste pas une lecture `/data` avec un nom
non-alphanumérique, ni cmd8 avec commande > 63 octets. Si c'est le cas, assouplir la règle concernée.
