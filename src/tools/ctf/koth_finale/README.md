# KoTH finale (NCTF26) — tenir la colline jusqu'à la fin

Kit **prêt à brancher**, testé hors-ligne. Stdlib Python uniquement (aucun `pip`), zéro secret en dur,
tout par variables d'env (`hill.env`).

## LA commande

```bash
cd src/tools/ctf/koth_finale
bash koth_run.sh start        # détaché, superviseur, survit à la fermeture du terminal
bash koth_run.sh status       # ROI=OUI/NON, niveau, threads, RTT, ticks gagnés
bash koth_run.sh stop         # arrêt propre
```

À lancer **dès qu'on a la colline**, puis on oublie. `hill.env` doit être rempli (l'agent le fait à t+0
via `recon_koth.py`).

## Ce qui fait gagner : le snipe au tick

Le scorer ne regarde pas qui claim le plus : il regarde **qui est roi au moment du tick**. Donc le seul
claim qui compte est **le dernier avant le tick**. Le moteur est bâti là-dessus :

| Mécanisme | Effet mesuré |
|---|---|
| **Train final** : tous les threads tirent sans relâche pendant les derniers `6×RTT` | dernier claim à **0–8 ms** du tick |
| **Keep-alive** (une connexion persistante par thread) | supprime le handshake TCP+TLS par claim (100–300 ms sur Internet) |
| **Périodes désynchronisées** par thread | plus de trous de 20 ms entre deux salves |
| **Pouls de fond** 1 claim/s hors fenêtre | tient même si la phase du tick est mal devinée |
| **RTT mesuré en continu** (EWMA) | le train se cale tout seul sur la latence réelle |
| **Backoff 429 local ≤ 20 ms** | un rate-limit ne fait plus rater le tick (c'était le bug n°1) |

### Résultats mesurés (mock adversarial local)

| Scénario | Ticks gagnés |
|---|---|
| Rival adaptatif (~1–3 claims/s) **+ 4 resets de conteneur en 80 s** | **94 %** (520 claims en 80 s) |
| Rival à **20 claims/s** (50 ms/claim) | **83 %** |
| Rival réaliste, sans reset | **100 %** |
| Self-test intégré (35 s, rival + resets) | **100 %**, resets traversés, arrêt propre |

À noter : sur le mock à 20 claims/s, c'est **le mock qui sature** (~37 req/s), pas nous.

## L'endurcissement (ce qui monte tout seul)

```
PROBE   → on mesure
CONTEST → 2 ticks perdus d'affilée : +1 niveau (threads ×2, tir resserré) + burst
HOLD    → 3 ticks gagnés ET 20 s de tenue : −1 niveau (on redevient discret)
```

Le niveau est **persisté** (`adaptive_state.json`) : après un crash, on repart directement à la bonne
intensité. Plafonds durs (`KOTH_THREADS_MAX`, `KOTH_INTERVAL_MIN`) : jamais de DoS.

## Multi-machines (toi + coéquipiers)

```bash
bash koth_run.sh bundle     # -> koth_finale_<date>.zip à envoyer aux coéquipiers
```

Chaque machine lance la même commande, avec `KOTH_PUMPS=<nombre total de machines>` dans `hill.env`.
Le débit de chaque machine est divisé par ce nombre (le total reste borné) et **N machines tiennent
mieux qu'une** : plus de connexions parallèles = plus de claims dans la dernière milliseconde.

## Les 3 modèles de colline

| Modèle | Commande |
|---|---|
| **HTTP claim** (probable côté CTFd) | `bash koth_run.sh start` |
| **SSH + fichier « king »** (`ssh -p <port> player@<ip>`) | `bash koth_ssh_takeover.sh` (re-assertion 20 s) |
| **Shell déjà obtenu sur la box** | `KOTH_TOKEN=<jeton> KING_FILE=/koth/king bash onbox_guardian.sh install` |

`onbox_guardian.sh` = persistance **double** qui se répare elle-même : deux boucles qui se surveillent
mutuellement, 3 copies du binaire dans 3 répertoires, cron `@reboot` + chaque minute, king file réparé
en < 0,7 s. Vérifié : `kill -9` d'une boucle → relancée en 1,5 s ; 2 copies sur 3 effacées → 3/3
restaurées.

## Vérifier avant le jour J (2 min, hors-ligne)

```bash
bash koth_run.sh selftest
# [1/4] probe OK | [2/4] 100% des ticks malgré rival + resets | [3/4] STOP | [4/4] king file
# -> SELF-TEST : PASS ✅
```

## Fichiers

| Fichier | Rôle |
|---|---|
| `koth_run.sh` | **entrée unique** : start / stop / status / logs / probe / selftest / bundle |
| `hill_hold.py` | moteur : snipe au tick, keep-alive, escalade, mode LOCAL king-file |
| `mock_rival.py` | colline adverse (agressivité, 429, resets, tick scorer) — pour les tests |
| `koth_ssh_takeover.sh` | prise d'une colline SSH + persistance on-box + re-assertion |
| `onbox_guardian.sh` | persistance on-box double, auto-réparatrice |
| `onbox_persist.sh` | persistance simple (setsid + flock + cron) |
| `recon_koth.py` | à t+0 : découvre claim/status/team-id |
| `recon_target.sh` | recon rapide d'une box |
| `hill.env.example` | modèle de config commenté |
| `koth-hold.service` | survie au reboot de la machine |

## Réglages utiles le jour J

- **Le score bouge chaque minute** → `KOTH_SLOT_PERIOD=60`. Chaque tick gagné = points.
- **Un bot adverse résiste** → le moteur escalade seul ; sinon `KOTH_MAX_LEVEL=3`,
  `KOTH_THREADS_MAX=12`.
- **La plateforme renvoie des 429** → `KOTH_THROTTLE_SOFT=3` (ralentit plus tôt), et baisser
  `KOTH_THREADS_MAX`.
- **Mauvais champ roi deviné** → le `probe` retombe automatiquement sur `king` et te le dit.
- **Claims signés** → `KOTH_SIGN_KEY` + `KOTH_SIGN_ALGO` + `{sig}` dans le body.

## Règles (jamais enfreintes)

Colline **in-scope uniquement**, pas de DoS, pas d'attaque des autres équipes ni de l'infra
organisatrice. La purge de persistance rivale (`--purge`) ne s'applique **que** sur la box de la
colline elle-même.

## Méthode de fond

`knowledge/patterns/misc/koth-hold-the-hill-continuous-and-onbox-persistence.md`
