# Source: Claude-Red (SnailSploit)

- URL du dépôt : https://github.com/SnailSploit/Claude-Red.git
- Commit cloné : `a8de813edc9f66f60d44cfe42d47750e89d9930b` (branche par défaut)
- Date du commit : 2026-10-12
- Clone effectué le 2026-11-09, via un agent de recherche dédié puis import manuel
  (clone temporaire hors repo principal, non committé, dans le scratchpad de session)
- Méthode de récupération : `git clone --depth 1` en lecture seule. Le dépôt contient
  `install.sh`, `convert_skills.py`, `tools/build_manifest.py` — **aucun n'a été
  exécuté** ; seuls des sous-dossiers `SKILL.md` ont été copiés.

## Licence

MIT License, Copyright (c) 2024-2025 SnailSploit / Kai Aizen.

## Pourquoi cet import

Dépôt trending (~10 500 étoiles au moment de la recherche), 78 `SKILL.md` sur 23
catégories. Complément naturel de `claude-ad/` (AD pur) : couvre explicitement
l'angle "assume breach → pivot → privesc → post-exploitation" qui manquait pour les
boot2root, en particulier le privesc Linux/Windows détaillé (SUID/GTFOBins,
capabilities, sudo/CVE-2021-3156, cron, PATH hijack, NFS no_root_squash, kernel CVEs,
Docker escape, LD_PRELOAD — mappé MITRE ATT&CK T1548) et le lateral
movement/persistence/exfiltration post-breach, quasi absents de nos patterns internes
sous forme de méthodologie structurée.

## Ce qui a été copié ici (sous-ensemble curé — le dépôt complet couvre 23 catégories
dont la plupart recoupent déjà `ctf-web`/`ctf-crypto`/`security-skills`)

- `active-directory/offensive-active-directory/` — BloodHound/SharpHound, PowerView,
  Kerberoasting/ASREProast, delegation, Golden/Silver/Diamond tickets, ADCS ESC1-ESC15,
  DCSync/DCShadow (recoupe partiellement `claude-ad`, gardé pour triangulation —
  formulation différente, utile en cas de blocage sur l'un des deux).
- `active-directory/offensive-netexec/` — usage de NetExec (ex-CrackMapExec).
- `privesc/offensive-linux-privesc/` — privesc Linux détaillée, lue intégralement,
  très complète.
- `privesc/offensive-windows-privesc/` — privesc Windows détaillée.
- `post-exploitation/offensive-lateral-movement/`
- `post-exploitation/offensive-persistence/`
- `post-exploitation/offensive-data-exfiltration/`
- `README.md`, `LICENSE`.

## Ce qui n'a PAS été copié (et pourquoi)

- `install.sh`, `convert_skills.py`, `tools/build_manifest.py` : scripts d'installation/
  build du dépôt source, sans valeur pour une lecture en référence, volontairement non
  exécutés.
- `assets/banner.png` : image décorative, aucune valeur.
- Les 16 autres catégories (`web/`, `crypto/`, `exploit-dev/`, `fuzzing/`, `wireless/`,
  `mobile/`, `cloud/`, `cicd/`, `container/`, `iot/`, `network/`, `forensics/`, `api/`,
  `auth/`, `recon/`, `social-engineering/`, `supply-chain/`, `infrastructure/`,
  `ai/`, `utility/`) : hors périmètre de ce besoin précis (boot2root/AD) et largement
  redondantes avec l'arsenal déjà importé (`ctf-web`, `ctf-crypto`, `security-skills`,
  `hacking-skills`). À revisiter ponctuellement si un besoin précis apparaît
  (ex. `container/offensive-container-escape` si un boot2root Docker/K8s bloque).

## Risques / code suspect

Aucun dans les fichiers copiés (uniquement Markdown). Les scripts non copiés
(`install.sh`, `convert_skills.py`) n'ont pas été audités en détail puisqu'ils ne sont
pas repris ici — à auditer avant toute exécution si on décide un jour de les utiliser.
