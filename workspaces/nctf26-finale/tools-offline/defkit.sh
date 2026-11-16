#!/usr/bin/env bash
# defkit.sh - CTF "Défense" : sauvegarde, audit, vérif des usages, correctifs SÛRS, rollback
# Usage (en root sur la boîte) :
#   ./defkit.sh backup          sauvegarde AVANT toute modif (obligatoire)
#   ./defkit.sh recon           audit lecture seule (ne modifie rien)
#   ./defkit.sh check           vérifie que les usages légitimes marchent encore
#   ./defkit.sh fix [-y]        applique les correctifs à faible risque (demande confirmation)
#   ./defkit.sh rollback <chemin|all>   restaure un fichier (ou tout) depuis la sauvegarde
#   ./defkit.sh all             backup + recon + fix + check
# Rejouable : relancer une instance remet la boîte d'origine -> relance simplement "./defkit.sh all".

KIT=/root/.defkit
TS=$(date +%Y%m%d-%H%M%S)
mkdir -p "$KIT"
R=$'\e[31m'; G=$'\e[32m'; Y=$'\e[33m'; N=$'\e[0m'
ok(){ echo "${G}[OK]${N} $*"; }
warn(){ echo "${Y}[!!]${N} $*"; }
bad(){ echo "${R}[VULN]${N} $*"; }
sec(){ echo; echo "=== $* ==="; }
need_root(){ [ "$(id -u)" -eq 0 ] || { echo "root requis (sudo -i)"; exit 1; }; }

RISKY_SUID='find|vim|vi|nano|nmap|bash|sh|dash|ash|python[0-9.]*|perl|ruby|php[0-9.]*|node|awk|gawk|less|more|man|cp|mv|env|tar|zip|taskset|time|timeout|strace|gdb|docker|systemctl|tee|dd|base64|xxd|openssl|wget|curl|socat|nc|ncat|busybox'
WEBROOTS="/var/www /srv /opt /app /usr/share/nginx /home"
CODE_PAT='(system|exec|shell_exec|passthru|popen|proc_open|eval|assert|unserialize)[[:space:]]*\(.*\$_(GET|POST|REQUEST|COOKIE)|include(_once)?[[:space:]]*\(?[[:space:]]*\$_|os\.system|subprocess\.[A-Za-z_]+\(.*shell[[:space:]]*=[[:space:]]*True|pickle\.loads|yaml\.load\(|render_template_string|debug[[:space:]]*=[[:space:]]*True|child_process|new Function\(|SELECT .*(\+|%s|\$\{|\.format)'

# ---------------------------------------------------------------- BACKUP
cmd_backup(){
  need_root
  d="$KIT/backup-$TS"; mkdir -p "$d"
  tar czpf "$d/files.tgz" --ignore-failed-read /etc /var/www /srv /opt /app /home /root/.ssh /usr/local /var/spool/cron 2>/dev/null
  ss -tulpn > "$d/ports.txt" 2>/dev/null
  systemctl list-units --type=service --state=running --no-legend > "$d/services.txt" 2>/dev/null
  find / -xdev -perm -4000 -type f 2>/dev/null | sort > "$d/suid.txt"
  ln -sfn "$d" "$KIT/latest"
  ok "sauvegarde + baseline (ports, services, SUID) : $d"
}

cmd_rollback(){
  need_root
  [ -f "$KIT/latest/files.tgz" ] || { echo "aucune sauvegarde"; exit 1; }
  case "${1:-}" in
    "") echo "usage: rollback <chemin absolu | all>"; exit 1;;
    all) tar xzpf "$KIT/latest/files.tgz" -C / && ok "tout restauré";;
    *) tar xzpf "$KIT/latest/files.tgz" -C / "${1#/}" && ok "restauré : $1";;
  esac
}

# ---------------------------------------------------------------- CHECK (usages légitimes)
cmd_check(){
  sec "Ports : écart avec la baseline"
  if [ -f "$KIT/latest/ports.txt" ]; then
    diff <(awk '{print $1,$5}' "$KIT/latest/ports.txt" | sort -u) \
         <(ss -tulpn | awk '{print $1,$5}' | sort -u) >/dev/null \
      && ok "mêmes ports en écoute qu'au départ" \
      || warn "ports différents (un service légitime est peut-être tombé) : compare avec $KIT/latest/ports.txt"
  fi
  sec "Services systemd en échec"
  f=$(systemctl --failed --no-legend 2>/dev/null)
  [ -z "$f" ] && ok "aucun" || warn "$f"
  sec "Réponse HTTP locale des ports TCP ouverts"
  ss -tln | tail -n +2 | awk '{print $4}' | sed 's/.*://' | sort -un | while read -r p; do
    [ "$p" = "22" ] && continue
    c=$(curl -sk -o /dev/null -m 3 -w '%{http_code}' "http://127.0.0.1:$p/" 2>/dev/null)
    [ "$c" != "000" ] && [ -n "$c" ] && echo "  :$p -> HTTP $c" || echo "  :$p -> (pas HTTP / pas de réponse)"
  done
  if [ -f "$KIT/usecases.sh" ]; then
    sec "Tes scénarios d'usage légitimes ($KIT/usecases.sh)"
    bash "$KIT/usecases.sh" && ok "scénarios OK" || bad "UN SCÉNARIO LÉGITIME ÉCHOUE -> rollback du dernier correctif !"
  else
    warn "écris $KIT/usecases.sh (curl de login, upload, recherche...) : c'est ton filet de sécurité"
  fi
}

# ---------------------------------------------------------------- RECON (lecture seule)
cmd_recon(){
  sec "Système"; uname -a; id; grep PRETTY /etc/os-release 2>/dev/null

  sec "Comptes"
  awk -F: '($3==0 && $1!="root"){print "UID 0 suspect : "$1}' /etc/passwd | while read -r l; do bad "$l"; done
  [ -r /etc/shadow ] && awk -F: '($2==""){print "mot de passe vide : "$1}' /etc/shadow | while read -r l; do bad "$l"; done
  awk -F: '($7 !~ /(nologin|false|sync)$/){print "  shell : "$1" ("$7")"}' /etc/passwd
  for f in /root/.ssh/authorized_keys /home/*/.ssh/authorized_keys; do
    [ -f "$f" ] && { echo "  clés dans $f :"; awk '{print "    "$NF}' "$f"; }
  done

  sec "Permissions critiques"
  for f in /etc/shadow /etc/passwd /etc/sudoers; do
    [ -e "$f" ] && echo "  $(stat -c '%a %U:%G %n' "$f")"
  done
  find /etc /usr/local /opt /srv /var/www /lib/systemd -xdev -type f -perm -0002 2>/dev/null | head -40 \
    | while read -r f; do bad "fichier modifiable par tous : $f"; done

  sec "Sudo"
  grep -rnE 'NOPASSWD|!authenticate' /etc/sudoers /etc/sudoers.d 2>/dev/null | while read -r l; do bad "$l"; done

  sec "SUID dangereux"
  find / -xdev -perm -4000 -type f 2>/dev/null | grep -E "/($RISKY_SUID)$" | while read -r f; do bad "SUID : $f"; done
  sec "Capabilities"; getcap -r / 2>/dev/null

  sec "Cron"
  grep -rhE '^[^#]' /etc/crontab /etc/cron.d 2>/dev/null
  find /etc/cron* /var/spool/cron -type f -perm -0002 2>/dev/null | while read -r f; do bad "cron modifiable par tous : $f"; done
  grep -rhoE '/[A-Za-z0-9_./-]+' /etc/crontab /etc/cron.d 2>/dev/null | sort -u | while read -r p; do
    [ -f "$p" ] && find "$p" -perm -0002 2>/dev/null | while read -r f; do bad "script lancé par cron modifiable : $f"; done
  done

  sec "Services réseau exposés"
  ss -tlnp 2>/dev/null | tail -n +2 | while read -r _ _ _ a _ proc; do
    p=${a##*:}; h=${a%:*}
    case "$h" in 127.*|"[::1]") continue;; esac
    case "$p" in
      21|23|2375|3306|5432|6379|9200|11211|27017|445|2049|5900) bad "service sensible exposé : $a  $proc";;
      *) warn "écoute : $a  $proc";;
    esac
  done

  sec "SSH (rapport seulement : NE PAS toucher, c'est ton accès)"
  sshd -T 2>/dev/null | grep -Ei '^(permitrootlogin|passwordauthentication|permitemptypasswords|pubkeyauthentication)'

  sec "Docker"
  [ -S /var/run/docker.sock ] && { ls -l /var/run/docker.sock; getent group docker; }
  command -v docker >/dev/null && docker ps --format '  {{.Names}}  {{.Ports}}' 2>/dev/null

  sec "Restes dangereux dans les webroots (.git, .env, backups, phpinfo)"
  find $WEBROOTS -xdev -maxdepth 7 \( -name .git -o -name .env -o -name '*.bak' -o -name '*.old' -o -name '*.sql' -o -name '*.swp' -o -name '*~' -o -name 'phpinfo.php' \) \
    -not -path '*/node_modules/*' 2>/dev/null | head -50 | while read -r f; do bad "$f"; done

  sec "Code à risque (injection, exec, désérialisation, debug)"
  grep -rInE --include=*.php --include=*.py --include=*.js --include=*.rb --include=*.jsp --include=*.java \
    --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=.git --exclude-dir=vendor --exclude-dir=.defkit \
    "$CODE_PAT" $WEBROOTS 2>/dev/null | head -80

  sec "Secrets en clair"
  grep -rInEi --include=*.env --include=*.conf --include=*.ini --include=*.yml --include=*.yaml --include=*.json --include=*.php --include=*.py \
    --exclude-dir=node_modules --exclude-dir=.defkit \
    '(password|passwd|secret|api_?key|token)[[:space:]]*[=:]' $WEBROOTS 2>/dev/null | head -40

  sec "Fichiers modifiés ces 2 derniers jours (backdoors, config altérée)"
  find /etc /var/www /srv /opt /app /usr/local /home /root -xdev -type f -mtime -2 -not -path '*/.defkit/*' 2>/dev/null | head -40

  sec "Processus root"
  ps -eo user:12,pid,args 2>/dev/null | awk '$1=="root"' | grep -v ' \[' | head -40
}

# ---------------------------------------------------------------- FIX (faible risque, réversible)
ASSUME_Y=0
ask(){ [ "$ASSUME_Y" = 1 ] && return 0; read -r -p "$1 [o/N] " a; [[ "$a" =~ ^[oOyY]$ ]]; }
quarantine(){ q="$KIT/quarantine$(dirname "$1")"; mkdir -p "$q" && mv "$1" "$q/" && echo "  -> $1 mis en quarantaine ($KIT/quarantine)"; }

cmd_fix(){
  need_root
  [ "${1:-}" = "-y" ] && ASSUME_Y=1
  [ -d "$KIT/latest" ] || cmd_backup

  if ask "1. Permissions /etc/passwd, /etc/shadow, /etc/sudoers"; then
    chown root:root /etc/passwd; chmod 644 /etc/passwd
    if getent group shadow >/dev/null; then chown root:shadow /etc/shadow; chmod 640 /etc/shadow
    else chown root:root /etc/shadow; chmod 600 /etc/shadow; fi
    [ -f /etc/sudoers ] && chmod 440 /etc/sudoers
    ok "permissions de base"
  fi

  if ask "2. Retirer l'écriture 'tous' sur fichiers de /etc, /usr/local, systemd, cron"; then
    find /etc /usr/local /lib/systemd /var/spool/cron -xdev -type f -perm -0002 -exec chmod o-w {} + 2>/dev/null
    ok "fichiers world-writable corrigés (les dossiers d'upload ne sont PAS touchés)"
  fi

  if ask "3. Retirer le SUID des binaires dangereux (GTFOBins)"; then
    find / -xdev -perm -4000 -type f 2>/dev/null | grep -E "/($RISKY_SUID)$" | while read -r f; do
      chmod u-s "$f" && echo "  SUID retiré : $f"
    done
  fi

  if ask "4. Verrouiller les comptes à mot de passe vide"; then
    awk -F: '($2==""){print $1}' /etc/shadow | while read -r u; do passwd -l "$u" && echo "  verrouillé : $u"; done
  fi

  if ask "5. sysctl de durcissement (sans impact applicatif)"; then
    cat > /etc/sysctl.d/99-defkit.conf <<'EOF'
kernel.randomize_va_space = 2
fs.protected_symlinks = 1
fs.protected_hardlinks = 1
fs.suid_dumpable = 0
kernel.dmesg_restrict = 1
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
EOF
    sysctl --system >/dev/null 2>&1; ok "sysctl appliqué"
  fi

  if ask "6. Mettre en quarantaine restes web (.git, *.bak, *.old, *.swp, *~, phpinfo.php)"; then
    for r in /var/www /srv /usr/share/nginx /app; do
      [ -d "$r" ] || continue
      find "$r" -xdev \( -name .git -type d -prune -o -name '*.bak' -o -name '*.old' -o -name '*.swp' -o -name '*~' -o -name phpinfo.php \) 2>/dev/null \
        | while read -r f; do quarantine "$f"; done
    done
  fi

  echo
  warn "À faire À LA MAIN (trop risqué pour l'auto) :"
  echo "  - code applicatif (SQLi, cmd injection, LFI, upload, SSTI...) : corriger la cause dans le code, relancer le service"
  echo "  - NOPASSWD sudo : restreindre la commande, ne pas supprimer la règle à l'aveugle"
  echo "  - DB/redis/mongo exposés : bind 127.0.0.1 + mot de passe dans leur config, puis restart"
  echo "  - .env / secrets : changer les valeurs ET adapter l'appli, vérifier avec 'check'"
  echo "  - clés SSH inconnues : retirer SAUF celle que tu utilises"
  echo; cmd_check
}

# ---------------------------------------------------------------- MAIN
case "${1:-}" in
  backup)   cmd_backup;;
  recon)    cmd_recon;;
  check)    cmd_check;;
  fix)      shift; cmd_fix "$@";;
  rollback) shift; cmd_rollback "$@";;
  all)      cmd_backup; cmd_recon | tee "$KIT/recon-$TS.txt"; cmd_fix;;
  *) sed -n '2,12p' "$0";;
esac
