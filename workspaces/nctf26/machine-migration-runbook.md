---
doc_kind: runbook
title: "Migration vers une nouvelle machine Parrot OS avant la finale NCTF26"
created: 2026-11-10
status: active
---
# Migration vers une nouvelle machine (Parrot OS) — finale NCTF26 Lomé

Contexte : possibilité de changer de PC juste avant/pendant la finale
(19-20 nov), nouvelle install Parrot OS sur `sda`. Objectif : que
Claude Code + tout l'arsenal CTFAgent (skills, knowledge/, outils) soient
opérationnels sur la nouvelle machine sans rien reconstruire à la main.

## 0. Ce qu'il faut transférer — 2 catégories bien séparées

**A. Le dépôt git** (`/home/kali/ctfagent`, tout ce qui est versionné) —
peut passer par GitHub ou par copie directe.

**B. Les secrets non versionnés** (volontairement exclus par `.gitignore` —
`# Per-CTF secrets (session cookies, credentials) -- never commit these.`) —
**ne passent jamais par git/GitHub**, à transférer séparément (clé USB
chiffrée, ou retaper à la main) :

```text
.claude/settings.json              # config Claude Code locale
.claude/settings.local.json        # permissions locales
src/tools/ctf/.env                 # identifiants NCTF26 (NCTF_USER/NCTF_PASS)
src/tools/ctf/nctf26_storage_state.json   # session Playwright déjà loguée
workspaces/bugpwn/.env, workspaces/bugpwn/session/
workspaces/kbxac/.env,  workspaces/kbxac/session/
workspaces/vuln005/src/src/self.key, self.crt   # si encore pertinent
```

Vérifier la liste exacte au moment du transfert avec :
```bash
cd /home/kali/ctfagent && git status --ignored --short | grep "^!!"
```

## 1. AVANT d'éteindre l'ancienne machine

1. **Finir le push GitHub** si le token est configuré d'ici là :
   ```bash
   git push origin session/alchemy-tengu-recon
   # ou merger sur main si tu veux que main soit la référence
   ```
   Si push impossible, passer directement à l'option B ci-dessous.

2. **Option A — transfert par GitHub (préféré si le token marche)** :
   le repo complet sera récupérable par `git clone` sur la nouvelle
   machine. Les secrets (catégorie B) doivent quand même être copiés
   à part (USB), jamais poussés.

3. **Option B — transfert direct par clé USB (si pas de token/réseau)** :
   le repo fait **~3.2 Go** (dont ~314 Mo de `.git` et une bonne partie
   dans `workspaces/vuln001/`, `vuln003/` — des arbres sources amont
   volumineux type `aolserver`/`c-ares` probablement pas critiques pour
   la finale). Deux choix :
   - copie brute : `rsync -a /home/kali/ctfagent/ /media/usb/ctfagent/`
     (simple, mais prend toute la place)
   - tarball ciblé si la clé est petite, en excluant les gros arbres non
     essentiels :
     ```bash
     cd /home/kali && tar czf ctfagent-full.tar.gz \
       --exclude='ctfagent/workspaces/vuln001/src' \
       --exclude='ctfagent/workspaces/vuln003/attachments/c-ares-src.tar.gz' \
       --exclude='ctfagent/.pytest_cache' \
       --exclude='**/__pycache__' \
       ctfagent/
     ```
   Puis copier séparément et explicitement les fichiers de la catégorie B
   (secrets) listés en section 0.

4. L'archive de sauvegarde déjà prête (sous-ensemble arsenal seulement,
   **pas un remplacement de la copie complète**) :
   ```text
   /home/kali/backups/ctfagent-nctf26-arsenal-2026-11-09.tar.gz
   sha256 ceb1300648d0b69aff100f798157e3720e45e0091928d46973a078ed4c5dccdf
   ```
   Utile en filet si la copie complète échoue, mais ne contient ni
   `workspaces/` (sauf les 4 fichiers nctf26 notes) ni `tests/`.

## 2. Installer Parrot OS sur `sda`

Hors périmètre agent (installation OS classique) — points d'attention
seulement :
- Vérifier la version Parrot (Security Edition recommandée, outils CTF
  préinstallés : nmap, metasploit, wireshark, etc. — réduit le travail de
  réinstall en section 4).
- Garder le réseau/VPN prêt dès l'install (NCTF26 exige un accès **depuis
  le Togo uniquement** pour les instances — ça dépend du réseau sur place
  à Lomé, pas de la machine, donc pas d'action logicielle ici).

## 3-6. Un seul script fait les étapes 3 à 6 (Claude Code + dépôt + toolchain + vérif)

`scripts/bootstrap-parrot.sh` (ajouté 2026-11-10) automatise : installation
Node.js + Claude Code CLI, récupération du dépôt (USB déjà extrait OU clone
GitHub), tous les paquets apt/pip de `prep-arsenal-2026-11-06.md`
(sections 3 et 7, y compris `bruteshark` ajouté le 2026-11-10), puis lance
`pytest` et `check_skill_inventory.py` pour vérifier.

**Option A — repo déjà copié sur la machine (USB)** :
```bash
cd ~/ctfagent && ./scripts/bootstrap-parrot.sh
```

**Option B — repo seulement sur GitHub** (nécessite que le push ait été
fait avant de partir) :
```bash
curl -fsSL https://raw.githubusercontent.com/huanghuoguoguo/ctfagent/main/scripts/bootstrap-parrot.sh | bash
```

Le script ne touche **jamais** aux secrets (catégorie B) — il les liste
explicitement à la fin et dit où les recopier à la main. Il ne construit
pas l'image Docker Ghidra par défaut (lourd) ; ajouter
`--with-ghidra-image` pour l'inclure, ou la construire plus tard :
```bash
docker build -t rekit-ghidra11 workspaces/rekit-lab/sandbox-ghidra11/
```

Ensuite, dans tous les cas, recopier les fichiers de la catégorie B
(secrets) aux emplacements exacts listés en section 0 — ils ne sont dans
aucune archive/clone par construction — puis `claude login` si pas déjà
authentifié.

**Vérification finale** (déjà faite par le script, à refaire manuellement
si besoin) :
```bash
cd ~/ctfagent
python3 -m pytest tests/ -q                      # doit afficher 45 passed (ou plus si ajouts depuis)
python3 src/tools/common/check_skill_inventory.py --root .
claude    # ouvrir Claude Code dans le repo — le hook SessionStart
          # (src/tools/workspace/session_sync.py) doit afficher le rappel
          # pipeline + les entrées MEMORY.md au démarrage
```

Si le hook SessionStart n'affiche rien : vérifier que
`.claude/settings.json` (catégorie B, copié à la main) est bien en place —
c'est lui qui enregistre le hook.

## 7. Spécifique finale A&D

Une fois sur place et l'infra de la compétition connue, remplir
`src/tools/ctf/attack_defense_toolkit/config.py` (IPs équipes, FLAG_REGEX,
endpoint de soumission) — ce fichier n'est volontairement pas pré-rempli
puisque l'infra n'est annoncée que sur site.

## Related

- [`prep-arsenal-2026-11-06.md`](prep-arsenal-2026-11-06.md) — routage
  skills + liste outils vérifiée + section A&D ajoutée le 2026-11-09.
- [`notes.md`](notes.md) — historique complet de session, dont le blocage
  Cloudflare WAF à retester depuis un autre réseau avant la finale.
