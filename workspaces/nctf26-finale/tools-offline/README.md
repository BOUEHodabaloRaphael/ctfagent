# tools-offline — kit défense A&D (pré-staged hors-ligne)

Copié ici le 2026-11-16 pour la finale NCTF (Lomé, 19-20 nov). Prêt sans réseau.

## Contenu

| Fichier | Rôle |
|---|---|
| `defkit.sh` | Kit défense A&D : `backup` → `recon` (lecture seule) → `fix` (bas-risque réversible) → `check` (filet SLA) → `rollback`. Auteur : coéquipier (Emerick). |
| `usecases.sh` | Filet SLA lu par `defkit.sh check`. **À ADAPTER** aux vrais endpoints AVANT le premier `fix`. Sort != 0 si un flux légitime casse. |
| `linpeas.sh` | Enum privesc post-shell (PEASS-ng). Téléchargé hors-ligne le 2026-11-16. |
| `linux-exploit-suggester.sh` | Kernel exploit matcher post-shell (The-Z-Labs). Téléchargé hors-ligne le 2026-11-16. |
| `patches/` | **Patchs app pré-écrits & testés** pour juice-todo (3 fichiers JS) et pwn-sample (`firewall_filter.py`). À coller dans `patchable/`. Voir `patches/README.md`. |

## Doctrine (rappel) : exploit d'abord, patch prudent ensuite

defkit **ne patche PAS le code applicatif** (SQLi, cmd injection, LFI, upload, SSTI) —
c'est volontaire, et c'est là que sont les points. Le patch app reste **à la main** dans
`patchable/` (paramétrer la SQLi, `jwt.verify({algorithms:['HS256']})`, whitelist de chemin —
cf. juice-todo/pwn-sample dans `../FINALE-PREP-MASTER.md §1`). defkit **complète** ce patch
en durcissant l'OS, il ne le remplace pas.

## Pré-requis n°1 : écrire usecases.sh

Sans `usecases.sh`, `check` ne peut pas détecter qu'un `fix` a cassé le checker.
Sur la box : `cp usecases.sh /root/.defkit/usecases.sh` puis **adapter host/port + flux**
(login curl, émission token, upload, rendu). Variables : `UC_HOST`, `UC_WEB_PORT`, `UC_PWN_PORT`.

## Ordre d'emploi par round (aligné t+0 → t+4 du playbook)

```
t+0  ./defkit.sh backup                 # AVANT tout, obligatoire (baseline ports/services/SUID)
t+0  (lancer la boucle d'exploit — PRIORITÉ absolue, ne jamais la retarder pour patcher)
t+1  ./defkit.sh recon | tee recon.txt  # triage défensif, ne modifie rien
t+3  patch app à la main dans patchable/ puis restart service
t+3  cp usecases.sh /root/.defkit/ && ./defkit.sh fix   # SANS -y, confirmer chaque étape
t+4  ./defkit.sh check                  # SLA vert ? sinon ./defkit.sh rollback <chemin|all>
```

## Garde-fous

- **Jamais `fix -y`** à l'aveugle : les étapes world-write / strip-SUID peuvent casser un
  service légitime. Confirmer chaque étape, puis `check`.
- defkit suppose un **shell/VM complet** (systemd, cron, SUID, webroots). Si la finale ne
  donne qu'un **conteneur + `patchable/`**, son durcissement OS est du bonus ; le vrai
  travail reste le patch app à la main.
- `rollback all` restaure tout `/etc`, `/var/www`… depuis la dernière sauvegarde.

## Enum post-shell (si on obtient un shell sur une box adverse)

- `linpeas.sh` (PEASS-ng) et `linux-exploit-suggester.sh` (The-Z-Labs) — **déjà présents ici**,
  prêts hors-ligne. Pas d'OpenVAS/OpenSCAP/ansible-lockdown en round (trop lourds / risque SLA).
