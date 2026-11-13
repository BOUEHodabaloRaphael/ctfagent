# NCTF Finale — Master Prep (Discord writeup harvest consolidated)

Built 2026-11-13 from a full sweep of every CTF server in the user's Discord. This is the
single entry point: it consolidates every technique/writeup found and points to the detailed
digests. Finale = **attack-defense** (Lomé). Flag format for the finale: `NCTF{...}`.

Detailed digests (read for depth): `discord-harvest/INDEX.md` lists all of them.
Downloaded corpora (UNTRUSTED — read-only, never execute): `flagyard-writeups/downloads/`,
`discord-harvest/downloads/{battlectf,africc,click2trace,misc,africc-ad-live}/`.

---
## 0. Servers swept (yield)
RICH + analyzed: **FlagYard, BattleCTF, AFRICC, Click2Trace**, + African repos (0xFun, kBxAc,
HackerLab, 404CTF). LOW/empty: CERT-TG-NCTF, AFRICC-2027-Quals, Dirtbags&Flags, ThunderCipher
(video only), GBT_Hackers, NICC (notion), NEST, CTFZone, Root-Me, pwn.college, CWL, UCAO, Haker_st.
BLOCKED: HITCON (sparse), HackTheBox #holmes-writeups (role-gated).

---
## 1. ★★ ATTACK-DEFENSE GAME PLAN (highest priority — this IS the finale format)

Grounded in AFRICC's real ICC dry-run boxes (`downloads/africc-ad-live/`) + BattleCTF-2023 Final.
Full playbook: `discord-harvest/AFRICC-AD-PLAYBOOK-FOR-NCTF.md`.

**Box anatomy** (expect this shape): one vulnerable box per team at `10.3.<team>.2`
(web `:8080`, pwn `:31337`), a single editable `patchable/` dir, **two flags/box** mounted
read-only, Docker (compose.yaml + Dockerfile). Submit API = `POST .../FrontendService/SubmitFlags`,
header `Authorization: Bearer <token>`, body **`{"flags":[...]}` (a LIST)**, tick ~120s.

**Doctrine**: exploit-first, patch-later. Never hold a flag submission to finish a patch.

**Round-1 checklist** (from playbook §6):
- t+0 grab one flag by hand (curl the SQLi + a forged-JWT GET).
- t+1 confirm the submit API actually scores one flag before automating.
- t+2 launch the exploit loop across all enemy teams (skip own IP).
- t+3 patch own web box, re-verify SLA checker still green.
- t+4 patch own pwn box (firewall first), re-verify benign path passes.
- t+5+ steady state + pcap watch on own ports (learn enemies' exploits from traffic).

**Reusable attack harness**: `downloads/africc-ad-live/ad_jwt_attack_script.py`
(`AutomatedJWTAttacker`: 120s tick, teams 2-20, graceful shutdown, stats). Distilled into
`src/tools/ctf/attack_defense_toolkit/` (config + exploits/juice_todo.py + exploit_runner).
⚠️ **KNOWN BUG to fix before finale**: `src/tools/ctf/attack_defense_toolkit/submitter.py`
sends a single-flag JSON, but ICC wants `{"flags":[...]}` (list). Fix the body shape.

**Web A&D exemplar — juice-todo** (Node/Express/EJS, SQLite):
- ATTACK A: SQLi in `patchable/app.js:69` `INSERT INTO todos (task) VALUES ('${task}')`
  → `task = "' || (select flag from flags) || '"` → flag1 rendered back.
- ATTACK B: JWT `alg:none` forgery — `apiRoutes.js:26` uses `jwt.decode` not `jwt.verify`
  → forge admin token → `GET /api/admin/flag` → flag2.
- ATTACK C/D: `/admin/file` path traversal; md5-truncated-to-5-hex admin check that also
  leaks the full hash in the 401 body.
- DEFEND: parameterize the INSERT (`VALUES (?)`,[task]); `jwt.verify(token, SECRET,
  {algorithms:['HS256']})`; full-hash compare + whitelist file param. Don't break the todo
  render, `/todos` redirect, empty-task 400, or `/api/token` issuance.

**Pwn A&D exemplar — pwn-sample-kun** (`-no-pie -fno-stack-protector`):
- Easy flag: cmd7 file_read path traversal (`../flag`, no char validation).
- Other bugs: stack BOF (cmd1 buf[16]/fgets 1000), format string (cmd2), heap overflow+
  double-free (cmd4/5), `system()` backdoor (cmd8), libc leak (cmd9).
- DEFEND: only `patchable/firewall_filter.py` is editable → block `/`,`..`,non-alnum on cmd7;
  cap cmd1 ≤15 bytes; forbid `%` in cmd2; cap cmd8; wrap main in try/except (if the filter
  crashes, the wrapper fails OPEN — so never let it throw).

---
## 2. TECHNIQUE CATALOG BY CATEGORY (jeopardy side)

### Web
- **SQLi → flag table** (`' || (select flag from flags) || '`), classic on A&D todo apps.
- **JWT**: `alg:none` / `jwt.decode`-vs-`verify` forgery; weak HS256 secret (john → re-sign → IDOR).
  Detail: BATTLECTF + AFRICC + CLICK2TRACE digests.
- **SSTI** `{{7*7}}` → `__globals__` RCE (Flask); **XXE** `file:///`.  (MISC-AFRICAN digest.)
- **Node/JS RCE combos** (BattleCTF signature): prototype-pollution→EJS `outputFunctionName`;
  **js-yaml v3 `toJSON` + verbatim-tag blocklist bypass**; NoSQL `$or` scope-drop IDOR;
  **CL.TE request smuggling** to forge internal headers. Trick: JSON `\uXXXX` escaping defeats
  string-matching WAFs; path-casing bypasses OpenResty rate limits. (BATTLECTF digest.)
- **GraphQL field-suggestion recovery** (introspection off, "Did you mean?" oracle). (CLICK2TRACE.)
- **GSUB `calt` font-shaping stego → SSRF** (real URL in font shaping, cmap is decoy). (CLICK2TRACE.)
- **Operator-precedence cookie forgery** (access_token = client-computable arithmetic over leaked
  headers across routes). (CLICK2TRACE.)
- **SSRF** decimal-IP + uppercase-host filter bypass; **ExifTool RCE** CVE-2021-22204 (0xFun Shell).
- Universal filter-bypass idiom across the scene: **string-split + base64-decode**.

### Pwn
- **FlagYard baby_pwn lib** (`flagyard-writeups/downloads/baby_pwn/`): write-what-where → full ORW;
  `rop_call(rdi,rsi,rdx)`; forged `_IO_2_1_stdout_` leak/arb-write; **canary neutralization by
  pointing `__stack_chk_fail@GOT` at the main loop**; saved-RIP finder scanning for
  `__libc_start_call_main`.
- **seccomp**: when `execve` blocked → `write(1, environ, n)` flag oracle, or ORW shellcode.
- **Cross-arch** canary-leak+ROP ports (PPC/ARM/MIPS/RISC-V64/AArch64, CHERI) — stage qemu-user.
- **JS-engine pwn** (V8 Turbofan typer bug / b3typer BitAnd-range): wrong type-range deletes a
  bounds check → OOB → addrOf/fakeObj → arbitrary R/W. (AFRICC digest.)
- **Kernel pwn** (404CTF level): QEMU/initramfs, task_struct cred overwrite, seccomp strip,
  `/dev/vault` UAF. **glibc-2.42 heap**: tcache safe-linking, House of Einherjar, off-by-one.
- Full pwn arsenal catalogued in FLAGYARD digest (tcache unmangle, `__free_hook`/House-of-Force,
  FILE-struct arb R/W, SROP for static bins, `/proc/self/maps` ASLR defeat).

### Reverse
- **Scene default**: Ghidra decompile → invert a static per-char XOR/add/rotate array in Python.
  Crackmes dominate the entry tier. Pin the flag format (`NCTF{`) as a z3 constraint or z3 yields
  many spurious flags.
- **z3 BitVec SMT** for linear/constraint keygens (Breakout `total_sum==0x1BADCF514706D`, zigger).
- **angr + symbolic execution** for CFG-flattened/VM binaries.
- **Custom-VM / bytecode** unified method (CLICK2TRACE): 5 VM challenges (ELF VM, WASM, Ruby YARV,
  eBPF, Forth) all reduce to `input[i] = inv_sbox[target[i] ^ keystream[i]]` — recognize the
  (256B S-box + 16B keystream + 16B target) triple, invert.

### Crypto
- **Mersenne-Twister 3-tier kit** (FLAGYARD): `mt19937predictor`/`randcrack` for full outputs;
  `symbolic_mersenne_cracker` (Z3 Untwister) for truncated bits; Z3 `init_by_array` seed inverter.
  Pre-install offline.
- **Lattice signature forgery** (SaqrSign): average ~300 sigs vs sparse HashBall challenge → forge.
  Recognize "many sigs + sparse hashed challenge" ⇒ averaging, not single-shot CVP.
- **Factorable RSA first, CBC/CFB keystream reuse, padding oracle** (drop-in solver), partial-nonce
  ECDSA via Sage `small_roots`; key/nonce reuse across param sets → linear algebra.
- **HAWK structured lattice** (404CTF): linearize Gram matrices then LLL-on-kernel. Quantum: Qiskit/Shor.

### Forensics / DFIR  (heavily weighted in this scene — drill it)
- Fixed **Volatility chain**: imageinfo→pslist→netscan→cmdscan→filescan→dumpfiles→hashdump +
  Registry Explorer.
- **git-history recovery**: `git log --all --stat`, recover blobs deleted in later commits
  (vaultic: `git show <commit>:.vaultic/vault.png`).
- **PNG/file repair & stego**: walk ancillary `tEXt`/`zTXt` chunks (identical dims + size delta =
  hidden chunk, not pixel stego); IDAT reorder, IHDR dim+CRC fix, gzip flag-byte fix.
- **pcap→CVE reconstruction**; **gRPC-over-pcap** extractor (FLAGYARD hokan): hand-rolled HTTP/2
  frame walker + protobuf varint decoder + AES-GCM, no .proto needed (port 50051), ending in
  OpenSSL `Salted__` → PBKDF2-HMAC-SHA256 → AES-256-CBC.

### OT / ICS  (recurring African-scene category — pre-stage a Modbus client)
- Client-first TCP, no banner, single persistent connection, **flag appears only WHILE the
  dangerous physical condition is sustained** (loop the write, poll during danger).
- Modbus (water-treatment register abuse; centrifuge unauth maintenance-override coil), custom
  binary protocols (Aurora out-of-sync breaker close Δ≈180°; SIS sharing the process session,
  mixed BE-transport/LE-message endianness), SSRF-to-plant. (BATTLECTF digest + 2026 Benin SCADA theme.)

### AI-agent / tool-abuse  (relevant to the nctf26-agent-tool-abuse challenge)
- **Secterm chain** (CLICK2TRACE): the agent trusts instructions planted in side-channel data it
  reads back (profile bio, support ticket), not just chat. Harvest state-transition keywords from
  its refusal messages, carry the per-session nonce, drive its `escalate`→`fetch_url` tool as SSRF
  to `*.internal` (169.254.169.254 metadata decoy).

### Misc / scene-specific
- Discord BOTS as challenge targets (OAuth invite abuse, bot-mediated SQLi).
- Themed Vigenère keys from Dahomey/Benin history; OSINT needs exact French names/accents
  (Wayback, Wikipedia, specialist registries).

---
## 3. PRE-STAGE TOOLKIT CHECKLIST (do before the finale, offline)
- A&D: fix `submitter.py` to `{"flags":[...]}`; parameterize exploit loop (TEAMS, TICK=120,
  FLAG_REGEX=`NCTF{...}`, SUBMIT_URL+Bearer, skip-own-IP) in `attack_defense_toolkit/`.
- pwntools + qemu-user (PPC/ARM/MIPS/RISCV/AArch64) + checksec + one-gadget + ropper.
- z3 + BitVec constraint template; angr; `mt19937predictor`/`randcrack`/symbolic MT cracker; SageMath.
- Volatility3 + Registry Explorer; scapy; a hand-rolled Modbus client + per-opcode framing harness.
- gRPC/HTTP2 pcap extractor (lift `grpc_messages()`/`protobuf()`/`varint()` from FLAGYARD hokan).
- uharfbuzz (font shaping); AFL++/libFuzzer+ASAN (vuln-research track).

---
## 4. Pointers
- Telegram CYBERSÉCURITÉ channel resources (5 PDFs, read them directly):
  `telegram-harvest/pdfs/` — Linux data exfiltration, ZTE MF293N2 auth-bypass report,
  ethical-hacking phases, social-engineering techniques. Catalog: `telegram-harvest/SOURCES.md`.
  (Automated technique-extraction agent was stopped by Claude's cyber safeguards; open the PDFs
  directly for the details.)
- All digests + corpora: `discord-harvest/INDEX.md`.
- A&D playbook (actionable): `discord-harvest/AFRICC-AD-PLAYBOOK-FOR-NCTF.md`.
- Pending/blocked: HTB Holmes CTF 2026 writeups (role-gated — would need external search or
  higher HTB access); NICCTF-2026 Notion (JS-only, needs headless render).

---
# NCTF — Préparation finale — Détection exfiltration et défense web
(Ajout 2026-11-13, depuis `telegram-harvest/TELEGRAM-DEFENSIVE-NOTES.md`, lui-même tiré des PDFs
`telegram-harvest/pdfs/*.txt`. **Faits** = extraits des docs, cités fichier+ligne. **Reco/Hypo** =
mes recommandations défensives, marquées comme telles. N'ajoute pas de procédure offensive.)

## 5.0 Synthèse courte
Deux apports réellement actionnables pour défendre nos box en A&D : (1) **détecter l'exfiltration de
flags** via des binaires Linux légitimes (LOLBins) ou des listeners non prévus ; (2) **reconnaître une
auth web challenge-response reconstructible côté client sur HTTP clair** (cas ZTE). Le reste des PDFs
(5 phases, ingénierie sociale, sécu physique) est secondaire (voir 5.6).

## 5.1 Checklist AVANT match (préparer nos propres box)
- [ ] Inventorier les binaires réseau présents : `which nc ncat curl wget openssl busybox php ruby finger whois socat`.
- [ ] Lister l'état normal attendu : ports ouverts, processus, endpoints légitimes du/des service(s) de jeu.
- [ ] Vérifier la dispo de l'observabilité : `auditd`/`auditctl`, `journalctl`, `ss`, `lsof`, `tcpdump` installés.
- [ ] Identifier l'IP/port du **checker SLA** (à ne jamais bloquer) et, si possible, préparer un egress restrictif.
- [ ] Repérer où sont les flags (chemins montés read-only) et quels process ont le droit de les lire.
- [ ] Nos services web font-ils du hashing côté client / transportent-ils un nonce sur HTTP ? (cf. 5.4)

## 5.2 Checklist PENDANT match (surveillance continue, non destructive)
Compatible A&D : **observer d'abord, ne jamais tuer un service critique ni changer la conf sans validation.**
- [ ] Arbres de processus : `ps auxf` / `ps -ef --forest` — repérer un shell qui spawn un client réseau.
- [ ] Connexions & listeners : `ss -tlnp` (écoute) et `ss -tnp` (établies) — tout listener hors inventaire = suspect.
- [ ] Descripteurs réseau par process : `lsof -i` / `lsof -p <pid>`.
- [ ] Journaux : `journalctl -f`, logs du service applicatif ; exécutions via `ausearch -m EXECVE` si auditd actif.
- [ ] Accès fichiers sensibles : surveiller la lecture des flags (`auditd` watch sur le chemin ; `find <flag> -newer`).
- [ ] Trafic sortant : `tcpdump -ni <iface> 'not host <checker>'` (capture passive) — corréler avec `pcap_watch.py`.
- [ ] Comparer en continu à l'inventaire "état normal" de 5.1 : agir sur l'écart, pas sur une alarme isolée.

## 5.3 Indicateurs de compromission (exfiltration) — Fait=doc, Reco=action
Source : `exfiltration-donnees-binaires-linux-fr.txt` (familles LOLBins l.14-16, détails par binaire).
Pour chaque indicateur : signification | où l'observer | éviter les faux positifs | action non destructive.
- **`/dev/tcp/<ip>/<port>` dans un `bash -c`/`ksh -c`** (Fait l.129, 307) : canal réseau natif ⇒ exfil/reverse.
  Observer: `ps auxf`, `/proc/<pid>/cmdline`. FP: scripts d'admin légitimes → vérifier user/parent. Action: isoler le process (cgroup/pause), capturer, escalader au lead avant kill.
- **Listener non prévu** `busybox httpd` / `php -S` / `ruby -run -e httpd` / webrick / `python -m http.server`
  (Fait l.168-348) : serveur de fichiers monté par l'adversaire. Observer: `ss -tlnp`. FP: service de jeu légitime → comparer à l'inventaire. Action: identifier le binaire/owner, tuer **seulement** si hors service de jeu.
- **`execve` d'un `nc/curl/wget/openssl/whois/finger`** juste après lecture d'un flag/`/etc/passwd`
  (Fait l.44-258) : exfil. Observer: `ausearch -m EXECVE` + watch fichier flag. FP: healthcheck/outil légitime → whitelister. Action: bloquer l'egress de ce process, préserver la preuve.
- **HTTP POST dont le corps = contenu d'un fichier** (Fait l.70-78, 221-230) : transfert sortant. Observer: pcap/tcpdump. FP: upload applicatif normal → comparer endpoint/taille attendue.
- **TLS/TCP brut inhabituel, pics DNS, egress vers IP/port non standard** (Reco, générique) : canal caché. Observer: tcpdump, compteurs par flux. FP: mises à jour/telemetry → baseline.
- **Lecture d'un flag suivie immédiatement d'une connexion réseau** (Reco, IoC composite) : signature exfil la plus fiable.

## 5.4 Fiche reconnaissance défensive — auth web challenge-response (cas ZTE)
Source : `Rapport_ZTE_MF293N2_Auth_Bypass.txt`. (Angle détection/durcissement uniquement, pas d'exploitation.)
- **Séquence générale** (Fait l.86-97) : le client fait un GET qui récupère un **nonce**, puis un POST d'une
  **réponse dérivée** (ici un hash 64-hex). Reconnaître ce motif dans nos logs HTTP.
- **Risque HTTP clair** (Fait l.84, 200-201) : si l'algo est côté client et le canal non chiffré, la réponse est
  **reconstructible** par un observateur passif ; le nonce empêche le **rejeu** (l.214) mais pas une attaque
  **hors-ligne** (l.291-297). → distinction clé : anti-rejeu ≠ anti-dictionnaire.
- **Mot de passe faible/défaut** (Fait l.295-297, 271) : facteur décisif, indépendant de l'algo.
- **Analyse** (Fait l.166-201) : examiner le **JavaScript client** et les **journaux HTTP** pour repérer le schéma.
- **Piège d'analyse** (Fait l.249-252) : casse hexadécimale JS (maj) vs `hashlib` (min).
- **Durcissement** (Fait, reco du rapport l.307-317) : HTTPS, restreindre l'accès à l'admin, remplacer les
  identifiants par défaut, mot de passe fort, (fabricant) KDF serveur (PBKDF2/Argon2) ; **Reco** : rate-limit des tentatives.

## 5.5 Workflow défense pendant la finale (court)
1. Recon **autorisée de NOS propres** services. 2. Inventaire ports/process/endpoints attendus (5.1).
3. Analyse des anomalies (5.2/5.3). 4. **Validation non destructive** (observer, capturer, corréler).
5. Correction **ou confinement** (patch minimal validé, egress, isolation process) — jamais de kill aveugle.
6. Revérifier que **checker + SLA** passent toujours après chaque action. 7. Conserver les preuves (pcap,
logs, hash), prévoir un **retour arrière** (sauvegarde de la conf avant tout changement).

## 5.6 Secondaire (moins prioritaire pour la défense technique)
`Phases_du_hacking_ethique_FR.txt` (5 phases : recon→analyse→accès→maintien→traces), 
`Techniques_d_ing_nierie_sociale__*.txt` (10 techniques SE), `Mythe_vs_r_alit__*.txt` (sécu physique).
À ne traiter que si le **règlement NCTF** les rend pertinents (ex. volet OSINT/SE explicite). Sinon, ignorer pendant le match A&D.

## 5.7 À adapter à NOS services réels (le jour J)
Remplacer les génériques par le concret annoncé sur place : interface/`iface` de capture, IP+port du checker,
liste blanche des process/listeners légitimes, chemins réels des flags, et (dans `attack_defense_toolkit/config.py`)
TEAMS / FLAG_REGEX / SUBMIT_URL+token / `SUBMIT_JSON_KEY`+`SUBMIT_JSON_VALUE_LIST`.

## 5.8 Rôles équipe (Reco — à confirmer avec l'équipe)
- **Attaque** : lance/maintient la boucle d'exploit + soumission (doctrine exploit-first).
- **Défense/Blue** : surveillance 5.2/5.3, confinement non destructif, préserve le SLA.
- **Patch** : applique les correctifs minimaux validés, revérifie le checker (workflow 5.5 étapes 5-6).
- **Preuves/Lead** : journalise les flags (solve-log), arbitre les kills/patches, garde la vue d'ensemble.
