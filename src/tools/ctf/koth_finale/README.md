# KoTH finale (NCTF26) — kit de tenue de colline, prêt à brancher

Préparé pour la finale (KoTH ouvre **jeudi 19 nov 10:00, Lomé**). Tout est **paramétré par variables
d'env** (`hill.env`), **zéro secret en dur**, **stdlib Python uniquement** (aucun `pip`, marche hors-ligne).

Inspiré de ce qu'une équipe a réellement fait au préqual (kit « Th3N00bs » : `run_koth.sh` + `STOP` +
`status.json` + créneaux alignés + persistance on-box + systemd), **avec les défauts corrigés** :
cadence plafonnée (leur `--rate 800` = DoS, interdit), redirections interdites, pas de rejeu d'une
mutation incertaine, watchdog et re-assertion après reset.

## LA commande (celle que tu lances et que tu oublies)

```bash
cd src/tools/ctf/koth_finale
bash koth_hold.sh start        # détaché (setsid) + watchdog + log ; survit à la fermeture du terminal
bash koth_hold.sh status       # ROI=OUI/NON, roi courant, cadence, uptime
bash koth_hold.sh stop         # arrêt propre (fichier STOP + kill du groupe)
```

Ça suppose `hill.env` rempli — **l'agent le fait à t+0** (`python3 recon_koth.py`, puis il renseigne
`KOTH_CLAIM_PATH` / `KOTH_STATUS_PATH` / `KOTH_OUR_ID`). Toi tu ne touches à rien.

## Les 3 modèles de colline et quoi lancer

| Modèle (à confirmer à l'ouverture) | Commande |
|---|---|
| **HTTP claim** (le plus probable côté CTFd) | `bash koth_hold.sh start` |
| **SSH + fichier « king »** (`ssh -p <port> player@<ip>`) | `bash koth_ssh_takeover.sh` (boucle de re-assertion) |
| **Shell déjà obtenu sur la box** | `KOTH_TOKEN=<jeton> KING_FILE=/koth/king bash onbox_persist.sh` |

`koth_ssh_takeover.sh` fait : root (vecteurs non destructifs) → jeton dans le king file → boucle
`/usr/lib/.koth-hold` + `/etc/cron.d/koth-hold` (`@reboot`) → **re-connexion toutes les 20 s** pour
re-poser la persistance si le conteneur est reset. Option `--purge` pour neutraliser la persistance
rivale sur cette box (désactivée par défaut).

## Fichiers

| Fichier | Rôle |
|---|---|
| `koth_hold.sh` | **lanceur unique** : start / stop / status / logs / probe / **selftest** |
| `hold_hill.py` | moteur HTTP : threads, cadence plafonnée, créneaux, no-redirect, backoff 429/503, `status.json`, `STOP` |
| `koth_ssh_takeover.sh` | prise d'une colline SSH + persistance on-box + re-assertion |
| `onbox_persist.sh` | persistance à poser depuis un shell déjà obtenu (setsid + flock + cron @reboot) |
| `mock_hill.py` | fausse colline locale : permet de tester **sans réseau** |
| `recon_koth.py` | à t+0 : découvre claim/status/team-id en observant le trafic de la page KOTH |
| `recon_target.sh` | recon rapide d'une box (`bash recon_target.sh <IP>`) |
| `hill.env.example` | modèle de config (copier en `hill.env`) |
| `koth-hold.service` | unité systemd pour survivre à un **reboot** de ta machine |

## Vérifier que le kit marche (à faire avant le jour J)

```bash
bash koth_hold.sh selftest
# [1/4] probe OK | [2/4] ROI=OUI face à un rival | [3/4] STOP | [4/4] verdict
# -> SELF-TEST: PASS
```

Le self-test démarre une fausse colline avec un rival qui réclame toutes les 1,5 s : il prouve que la
tenue, le watchdog et l'arrêt propre fonctionnent, **hors-ligne**.

## Survivre à un reboot de la machine (optionnel mais recommandé)

```bash
sudo cp koth-hold.service /etc/systemd/system/
sudo sed -i "s|/home/kali/ctfagent|$PWD/../..|" /etc/systemd/system/koth-hold.service
sudo systemctl daemon-reload && sudo systemctl enable --now koth-hold
journalctl -u koth-hold -f
```

## Réglages selon ce qu'on découvre

- **Le scorer ne compte qu'aux ticks** → `KOTH_SLOT_PERIOD=<période du tick>` (ex. 60) : on vise le tick
  au lieu de spammer.
- **Un bot adverse reprend la colline** → monter `KOTH_THREADS` (4 → 8/12) et baisser
  `KOTH_MIN_INTERVAL` (1.0 → 0.5) — **sans** dépasser ce que la plateforme tolère.
- **Claims signés** (comme « The Throne » au préqual : `team|ts` + HMAC) → `KOTH_SIGN_KEY` +
  `KOTH_SIGN_ALGO` et un body contenant `{sig}`.
- **Champ roi imbriqué** → `KOTH_KING_FIELD="data.king"`.
- **Auth par bearer** → `KOTH_AUTH="Bearer ..."` ; sinon les cookies de session suffisent.

## Règles (jamais enfreintes)

Colline **in-scope uniquement**, pas de DoS, pas d'attaque des autres équipes ni de l'infra organisatrice.
La purge de persistance rivale ne s'applique **que** sur la box de la colline elle-même.

## Méthode de fond

`knowledge/patterns/misc/koth-hold-the-hill-continuous-and-onbox-persistence.md`
