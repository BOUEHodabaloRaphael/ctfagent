#!/usr/bin/env bash
# =====================================================================
# NCTF26 FINALE — recon rapide d'une BOX (colline KoTH / service A&D)
#   bash recon_target.sh <IP|host> [ports]
# But : accelerer la PRISE de box a t+0. Scan ports -> versions -> enum
# par service (HTTP/SSH/etc.). Rapide et CIBLE (une seule IP in-scope).
# Lecture/enum seulement : pas de scripts "intrusive"/vuln lourds, pas de
# brute-force massif, pas de DoS. In-scope UNIQUEMENT.
#
# Sortie : resume a l'ecran + fichier recon_<ip>_<ts>.txt
# =====================================================================
set -u
TARGET="${1:-}"
PORTS="${2:-}"
[ -z "$TARGET" ] && { echo "usage: bash recon_target.sh <IP|host> [ports]"; exit 1; }

TS=$(date +%Y%m%d_%H%M%S)
OUT="recon_${TARGET//[^0-9A-Za-z._-]/_}_${TS}.txt"
have(){ command -v "$1" >/dev/null 2>&1; }
log(){ echo "$@" | tee -a "$OUT"; }
sec(){ log ""; log "===== $* ====="; }

log "# recon $TARGET  ($TS)   -> $OUT"
have nmap || { log "[!] nmap absent (apt install nmap). Fallback limite."; }

# 1) Decouverte de ports (rapide). -Pn : les cibles CTF bloquent souvent l'ICMP.
OPEN=""
if have nmap; then
  sec "1. Ports ouverts (nmap -Pn -T4)"
  if [ -n "$PORTS" ]; then SCAN="-p $PORTS"; else SCAN="--top-ports 1000"; fi
  nmap -Pn -T4 --min-rate 1500 $SCAN "$TARGET" -oG "/tmp/.recon_$TS.gnmap" 2>/dev/null | tee -a "$OUT" | grep -Ei "open|/tcp"
  OPEN=$(awk -F'Ports: ' '/Ports:/{print $2}' "/tmp/.recon_$TS.gnmap" 2>/dev/null \
        | tr ',' '\n' | grep -i open | sed -E 's/ *([0-9]+)\/open.*/\1/' | paste -sd, -)
  rm -f "/tmp/.recon_$TS.gnmap"
  log "[i] ports ouverts: ${OPEN:-aucun detecte}"
  # 2) Versions + scripts par defaut (safe) sur les ports ouverts
  if [ -n "$OPEN" ]; then
    sec "2. Services / versions (nmap -sCV)"
    nmap -Pn -sCV -p "$OPEN" "$TARGET" 2>/dev/null | tee -a "$OUT" | grep -Ei "open|service|version|http|ssh|product|OS"
  fi
else
  sec "1. Ports (fallback nc, ports usuels)"
  for p in 21 22 25 80 143 443 3306 5985 8080 8443 31337 ${PORTS//,/ }; do
    (echo > "/dev/tcp/$TARGET/$p") 2>/dev/null && { log "  $p/tcp OPEN"; OPEN="$OPEN,$p"; }
  done
  OPEN="${OPEN#,}"
fi

contains(){ case ",$OPEN," in *",$1,"*) return 0;; *) return 1;; esac; }

# 3) Enum HTTP si 80/443/8080/8443
for hp in 80:http 8080:http 443:https 8443:https; do
  port="${hp%%:*}"; scheme="${hp##*:}"
  contains "$port" || continue
  url="$scheme://$TARGET:$port"
  sec "3. HTTP $url"
  if have curl; then
    log "--- en-tetes ---";  curl -ksS -m 10 -I "$url" 2>&1 | tee -a "$OUT"
    log "--- titre ---";     curl -ksS -m 10 "$url" 2>/dev/null | grep -oiE "<title>[^<]*" | head -1 | tee -a "$OUT"
    log "--- chemins usuels (statut) ---"
    for path in /robots.txt /.git/config /api /status /login /admin /koth /king; do
      code=$(curl -ksS -m 8 -o /dev/null -w "%{http_code}" "$url$path" 2>/dev/null)
      log "  $code  $path"
    done
  fi
  have whatweb && { log "--- whatweb ---"; whatweb -a1 "$url" 2>/dev/null | tee -a "$OUT"; }
done

# 4) SSH si 22 (ou autre port SSH detecte par nmap) -> banniere + rappel creds préqual
if contains 22; then
  sec "4. SSH $TARGET:22"
  if have nc; then (echo "" ; sleep 1) | nc -w 5 "$TARGET" 22 2>/dev/null | head -2 | tee -a "$OUT"; fi
  log "[i] KoTH own-the-box : si SSH 'player' accessible, tenter mdp faible (préqual: player:player),"
  log "    puis privesc -> onbox_persist.sh (planter notre id dans le king file)."
fi

# 5) Rappel orientation KoTH
sec "5. Prochaines etapes (prise de box KoTH)"
log "- But : ROOT sur la box + posseder le fichier roi (ex: /koth/king, /king/king.txt)."
log "- Une fois un shell : KOTH_TOKEN=<notre_id> KING_FILE=/koth/king bash onbox_persist.sh"
log "- Si web : tester les vulns du catalogue (SSTI/CORS/CVE-2022-44268/.git, voir FINALE-PREP-MASTER.md §2)."
log "- RÈGLES : cette IP in-scope uniquement, pas de DoS, pas d'attaque des autres équipes/infra orga."
log ""
log "# fini. Rapport: $OUT"
