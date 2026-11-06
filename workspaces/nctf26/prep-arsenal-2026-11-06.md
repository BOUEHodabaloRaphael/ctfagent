# NCTF26 — Arsenal skills & RE (prépa 2026-11-06)

État : **prêt**. Toutes les bibliothèques sont dans le repo, les skills sont
déclenchables, les outils manquants ont été installés (sauf licence IDA/Binja).

## 1. Routage par catégorie

Ordre : `ctf-solver-profile` → triage → skill profond. Ne pas sauter le triage.

| Catégorie | Triage (décide) | Skill profond (exécute) | Référence externe |
|---|---|---|---|
| Reverse | `rev-triage` | `ctf-reverse`, `reverse-engineering`, `reverse-skill-router` | `knowledge/external/reverse-skill/`, `neurosploit/techniques/rev/` |
| Pwn | `pwn-triage` | `ctf-pwn` | `knowledge/external/pwn-htb/`, `security-skills/ctf/ctf-pwn` |
| Web | `web-triage` | `ctf-web` | `hacking-skills/`, `neurosploit/techniques/web/` |
| Crypto | — | `ctf-crypto` | `security-skills/ctf/ctf-crypto`, `knowledge/ceh/m20-cryptography.md` |
| Forensics | — | `ctf-forensics`, `ctf-malware` | `security-skills/ctf/ctf-forensics` |
| Misc / jail / SDR | — | `ctf-misc` | — |
| OSINT | — | `ctf-osint` | — |
| AI/ML | — | `ctf-ai-ml` | — |
| Android / APK | `rev-triage` | `reverse-engineering` + `reverse-skill-router` | `android-reverse-engineering/`, `reverse-skill/skills/apk-reverse` |
| .NET / Java | `rev-triage` | `reverse-engineering` | `reverse-skill/skills/dotnet-reverse`, `cfr` |
| Firmware / IoT | `rev-triage` | `reverse-engineering` | `reverse-skill/skills/firmware-pentest` |
| Challenge inconnu | `ctf-solver-profile` | `solve-challenge` | `knowledge/external/INDEX.md` |

Après résolution : `ctf-knowledge-capture` (repo) ou `ctf-writeup` (format concours).
Avant de rendre un flag : `ctf-evidence`.

## 2. RE quickstart (ordre de coût croissant)

```bash
# 0. triage maison : type, packer, entropie, strings, symboles
python3 src/tools/rev/rev_check.py ./chall --output recon.json
python3 src/tools/rev/crypto_consts.py ./chall          # AES/TEA/CRC/ChaCha constants

# 1. statique rapide
file ./chall; checksec --file=./chall; rabin2 -I ./chall
rabin2 -zz ./chall | less                                # strings + offsets
r2 -A ./chall                                            # aaa; afl; pdf @ main; axt @ sym.imp.strcmp

# 2. décompilation
./src/tools/rev/ghidra_headless.sh ./chall /tmp/ghidra_chall
#   → projet Ghidra 11.4.3 (image docker rekit-ghidra11), puis export décompilé :
#   .claude/skills/reverse-engineering/scripts/ghidra/  (voir SKILL.md)

# 3. dynamique
ltrace -f -s 200 ./chall; strace -f -e trace=openat,read,write ./chall
gdb -q ./chall    # b *main / b strcmp / catch syscall ; pwntools dispo pour scripter

# 4. solveurs
python3 -c "from z3 import *"        # contraintes
python3 -c "import angr"             # exploration symbolique (lourd, dernier recours)
python3 -c "import unicorn"          # émulation de blob/VM
```

Spécifiques :
```bash
# Android
jadx -d out/ app.apk ; apktool d app.apk -o apktool_out ; adb shell
frida -U -f com.target.app -l hook.js --no-pause

# .NET / Java
ilspycmd -p -o out/ Assembly.dll
cfr target.jar --outputdir out/            # wrapper java -jar ~/.local/opt/cfr/cfr.jar

# Firmware / carvings
unblob firmware.bin -d out/ ; binwalk -eM firmware.bin ; 7z x fw.img

# Mémoire / réseau / stégo
vol -f mem.raw windows.info ; vol -f mem.raw windows.pslist
tshark -r cap.pcapng -q -z io,phs ; exiftool img.png ; zsteg -a img.png
```

## 3. Outils — état vérifié le 2026-11-06

Présents : `file strings xxd readelf objdump nm c++filt`, `r2 rabin2 radiff2`,
`gdb 18.1` + `gdb-multiarch`, `checksec patchelf ROPgadget`, `pwntools 4.15`,
`capstone unicorn angr z3 lief 0.16.1 pyelftools pefile yara`,
`upx binwalk unblob 7z unsquashfs foremost`, `jadx jadx-gui apktool adb`,
`frida frida-ps` (installé), `ilspycmd dotnet monodis javap cfr`,
`node npx wasm2wat wasm-objdump`, `strace ltrace`, `tshark wireshark mitmproxy`,
`vol 3.28.2`, `exiftool steghide zsteg`, `capa floss olevba`,
`qemu-user-static`, `nmap curl jq socat nc`,
**Ghidra 11.4.3 headless via docker** (`rekit-ghidra11`, script
`src/tools/rev/ghidra_headless.sh`).

Absents / contournements :
- `ropper`, `one_gadget` : utiliser `ROPgadget` et `pwntools.ROP`.
- IDA Pro, Binary Ninja, x64dbg, WinDbg, lldb : non installés (licences / autre OS).
  Ghidra + r2 + gdb couvrent le besoin CTF Linux ; pour du Windows natif, passer par
  `wine` ou une VM si un challenge l'exige.
- Outils iOS (`class-dump`, `plutil`, `codesign`, `otool`) : non installés, à traiter
  au cas par cas (Mach-O reste lisible avec r2/rabin2).
- `qemu-system-*` (émulation système complète) : seul `qemu-user-static` est là.
- MCP `ctf`, `r2mcp`, `cyberchef` : **non disponibles** dans cette session. Les
  commandes/agents `ctf-arsenal` qui les supposent doivent être jouées en CLI.

## 4. Discipline preuve (non négociable)

1. Une commande, sa sortie brute, un hash de l'artefact — avant toute conclusion.
2. Flag = valeur **exacte** capturée (copier/coller + `sha256sum` du transcript),
   jamais reconstituée « de mémoire » ou « thématiquement » (cf. leçon Ascension).
3. Un challenge « qui échoue toujours » : re-vérifier le transport (session, fichier
   réellement exécuté, taille/md5) avant de changer d'exploit.
4. Deux hypothèses mortes = changer de catégorie, pas insister.

## 5. Rappels protocole NCTF26

- Déclencheur « **NCTF** » → login `nctf26_client.py login`, puis jeopardy.
- Instances accessibles **depuis le Togo uniquement** (pas de VPN étranger).
- TLS obligatoire : `ncat --ssl host 1337` (SNI = host), pas de `nc` nu.
- **Une soumission par flag**, aucun retry automatique, aucun bruteforce (art. 7).
- Vérifier qu'un coéquipier n'est pas déjà sur le challenge avant de consommer
  une instance.

## 6. Sauvegarde

Archive locale (hors dépôt git, pour survivre à un reset de branche) :

```text
/home/kali/backups/ctfagent-nctf26-arsenal-2026-11-06.tar.gz
sha256 b22e04ac72665f75b5f62c4f5e28fa88da47cbb644a9f72870ec32d32e9ce9b5
```

Contenu : `.claude/skills/` (16 skills), `knowledge/external/` (8 bibliothèques),
`src/tools/rev/`, les 3 notes NCTF26, `CLAUDE.md`, `docs/skills.md`.

Restauration :

```bash
cd /home/kali/ctfagent
tar xzf /home/kali/backups/ctfagent-nctf26-arsenal-2026-11-06.tar.gz
sha256sum -c /home/kali/backups/ctfagent-nctf26-arsenal-2026-11-06.sha256
```

État git : tout est committé (`83bc501`, puis `4138194`). Le push vers
`origin` (GitHub `huanghuoguoguo/ctfagent`) échoue faute d'identifiants dans cet
environnement — à faire avec un token/SSH si on veut une copie hors machine.

## 7. Installation reproductible (si besoin de refaire)

```bash
pip3 install --user --break-system-packages \
  lief volatility3 frida-tools flare-capa flare-floss
sudo apt-get install -y apktool jq foremost qemu-user-static ltrace unblob
# CFR (Java decompiler) :
curl -sSL -o ~/.local/opt/cfr/cfr.jar \
  https://repo1.maven.org/maven2/org/benf/cfr/0.152/cfr-0.152.jar
```

Note : Python 3.14 casse `ropper` (dépendance `filebytes`, `ast.Str` supprimé).
Ne pas perdre de temps dessus, `ROPgadget` fait le travail.
