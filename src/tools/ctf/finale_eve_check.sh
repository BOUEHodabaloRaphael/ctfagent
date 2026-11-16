#!/usr/bin/env bash
# =====================================================================
# NCTF26 — PRÉFLIGHT VEILLE DE FINALE (à lancer quand tu es en place)
#   bash src/tools/ctf/finale_eve_check.sh
# Revérifie toute notre préparation et dit GO / À CORRIGER. Lecture seule,
# n'attaque rien (le KoTH n'est de toute façon pas ouvert avant jeu 10:00).
# =====================================================================
set -u
cd "$(dirname "$0")/../../.." 2>/dev/null || true   # racine du repo
ROOT="$(pwd)"
KF="src/tools/ctf/koth_finale"
AD="src/tools/ctf/attack_defense_toolkit"
ok(){ printf "  \033[32m[OK]\033[0m %s\n" "$1"; }
ko(){ printf "  \033[31m[!!]\033[0m %s\n" "$1"; FAIL=1; }
wa(){ printf "  \033[33m[~ ]\033[0m %s\n" "$1"; }
FAIL=0
echo "================ PRÉFLIGHT NCTF26 FINALE — $(date '+%Y-%m-%d %H:%M') ================"

echo "-- 1. Outils système --"
for b in python3 playwright; do command -v "$b" >/dev/null 2>&1 && ok "$b présent" || wa "$b introuvable dans le PATH"; done
python3 -c "import requests" 2>/dev/null && ok "python requests" || ko "pip3 install requests"
python3 -c "import playwright" 2>/dev/null && ok "python playwright" || ko "pip3 install playwright && playwright install chromium"

echo "-- 2. Session plateforme (headless) --"
python3 - <<'PY'
import json,sys,time
from pathlib import Path
f=Path("src/tools/ctf/nctf26_storage_state.json")
if not f.exists(): print("KO storage_state absent"); sys.exit()
st=json.loads(f.read_text())
sess=[c for c in st.get("cookies",[]) if c["name"]=="session"]
if not sess: print("KO cookie session absent"); sys.exit()
exp=sess[0].get("expires",0); left=exp-time.time()
d=left/86400
print(("OK" if left>0 else "KO")+f" cookie session expire dans {d:.1f} jours")
PY
echo "     (test d'accès réel ci-dessous)"
ACC=$(timeout 70 python3 src/tools/ctf/nctf26_client.py list 2>&1 | grep -o "URL finale: .*" | head -1)
case "$ACC" in
  *"/challenges"*) ok "accès headless OK ($ACC)";;
  *"/login"*)      ko "session EXPIRÉE ($ACC) → rafraîchir les cookies avant le jour J";;
  *)               wa "réponse inattendue: ${ACC:-<vide>} (KoTH peut être fermé)";;
esac

echo "-- 3. Toolkit KoTH --"
python3 -I -c "import py_compile;py_compile.compile('$KF/hold_hill.py',doraise=True)" 2>/dev/null && ok "hold_hill.py compile" || ko "hold_hill.py"
python3 -I -c "import py_compile;py_compile.compile('$KF/recon_koth.py',doraise=True)" 2>/dev/null && ok "recon_koth.py compile" || ko "recon_koth.py"
bash -n "$KF/run_hold.sh" 2>/dev/null && ok "run_hold.sh syntaxe" || ko "run_hold.sh"
bash -n "$KF/onbox_persist.sh" 2>/dev/null && ok "onbox_persist.sh syntaxe" || ko "onbox_persist.sh"
bash -n "$KF/recon_target.sh" 2>/dev/null && ok "recon_target.sh syntaxe" || ko "recon_target.sh"
command -v nmap >/dev/null 2>&1 && ok "nmap présent (recon_target)" || wa "nmap absent → apt install nmap"
ARS="$KF/privesc-arsenal"
for a in linpeas.sh bin/traitor-amd64 bin/pspy64 pwnkit/PwnKit dirtypipe/dirtypipez; do
  [ -s "$ARS/$a" ] && ok "arsenal $a" || ko "arsenal manquant: $a (relancer fetch_privesc_arsenal.sh)"
done
[ -f "$KF/hill.env.example" ] && ok "hill.env.example présent" || ko "hill.env.example manquant"
[ -f "$KF/hill.env" ] && ok "hill.env déjà rempli" || wa "hill.env pas encore rempli (NORMAL avant l'ouverture → recon_koth.py à t+0)"

echo "-- 4. Toolkit A&D (Défense) --"
python3 -I -c "import py_compile;py_compile.compile('$AD/submitter.py',doraise=True)" 2>/dev/null && ok "submitter.py compile" || ko "submitter.py"
python3 -I -c "import py_compile;py_compile.compile('$AD/exploit_runner.py',doraise=True)" 2>/dev/null && ok "exploit_runner.py compile" || ko "exploit_runner.py"
python3 -I -c "import py_compile;py_compile.compile('$AD/config.py',doraise=True)" 2>/dev/null && ok "config.py compile" || ko "config.py"
grep -q "TEAMS = \[\]" "$AD/config.py" 2>/dev/null || grep -qE "^TEAMS = \[" "$AD/config.py" && wa "config.py: remplir TEAMS/SUBMIT_URL/headers à t+0 (normal si vide)"

echo "-- 5. Prépa / runbook / mémoire --"
for f in workspaces/nctf26-finale/FINALE-GO.md workspaces/nctf26-finale/FINALE-PREP-MASTER.md \
         knowledge/patterns/misc/koth-hold-the-hill-continuous-and-onbox-persistence.md \
         knowledge/writeups/pwn/nctf-bss-overflow-flip-admin-flag.md; do
  [ -f "$ROOT/$f" ] && ok "$(basename "$f")" || ko "manquant: $f"
done

echo "============================================================================"
if [ "$FAIL" = 0 ]; then
  printf " \033[32mGO\033[0m — préparation saine. Le jour J : 'finale' → recon_koth.py → remplir hill.env → tu lances run_hold.sh.\n"
else
  printf " \033[31mÀ CORRIGER\033[0m — voir les [!!] ci-dessus avant le lancement.\n"
fi
echo "============================================================================"
