# Index — bibliothèques externes (NCTF26)

Catalogue de tout ce qui a été aspiré le **2026-11-06** pour la prépa NCTF26.
Règle : ce dossier est **en lecture seule** (référence) ; les skills réellement
déclenchables vivent dans `.claude/skills/`.

## Skills actifs (`.claude/skills/`)

| Skill | Source | Rôle |
|---|---|---|
| `ctf-reverse` | ljagiello/ctf-skills | Playbook RE principal (23 fichiers) : anti-analysis, VM, Unicorn, r2pipe, plateformes |
| `ctf-pwn` | ljagiello/ctf-skills | Exploitation binaire : heap, ROP, kernel, seccomp, format string, scripts |
| `ctf-web` | ljagiello/ctf-skills | Web : auth/JWT, client-side, prototype pollution, CVEs, XXE/SSTI/SSRF |
| `ctf-crypto` | ljagiello/ctf-skills | RSA/ECC/lattices/PRNG/padding oracle/ZKP |
| `ctf-forensics` | ljagiello/ctf-skills | Disque, mémoire, PCAP, stégo, logs, side-channel |
| `ctf-misc` | ljagiello/ctf-skills | Pyjail, esolang, RF/SDR, QR/audio, contraintes |
| `ctf-malware` | ljagiello/ctf-skills | Scripts obfusqués, C2, YARA, shellcode, anti-VM |
| `ctf-osint` | ljagiello/ctf-skills | Géoloc, DNS, dorking, image search |
| `ctf-ai-ml` | ljagiello/ctf-skills | Adversarial ML, extraction de modèle, prompt injection |
| `solve-challenge` | ljagiello/ctf-skills | Dispatcher first-pass (triage → catégorie) |
| `ctf-writeup` | ljagiello/ctf-skills | Writeup standardisé post-solve |
| `ctf-similar-search` | ljagiello/ctf-skills | Recherche de writeups similaires (Tavily) |
| `reverse-engineering` | plugin Anthropic installé (encidxvii) | Playbook multi-plateforme + 15 références + 6 scripts (triage, ghidra headless, endpoints) |
| `r2-reverse` | hunter-bridge/ctf-arsenal | Workflow radare2 |
| `ctf-evidence` | hunter-bridge/ctf-arsenal | Discipline preuve / rapport |
| `reverse-skill-router` | nous (pointeur) | Routeur vers `knowledge/external/reverse-skill/` |

Les triage existants (`rev-triage`, `pwn-triage`, `web-triage`) restent la porte
d'entrée : ils décident, puis délèguent aux `ctf-*` ci-dessus.

## Bibliothèques de référence (`knowledge/external/`)

### `reverse-skill/` — zhaoxuya520/reverse-skill @ `cab634b` (7 MB)
45+ modules RE, entrée `skills/MASTER-ROUTING.md`, index `skills/INDEX.md`.
Modules clés : `apk-reverse`, `dotnet-reverse`, `go-rust-reverse`, `macos-reverse`,
`firmware-pentest`, `js-reverse`, `browser-extension-reverse`, `protocol-reverse`,
`thick-client`, `patch-diff-exploit`, `binary-diff`, `ida-reverse`, `ghidra-reverse`,
`radare2`, `malware-analysis`, `mobile-reverse`, `case-review`.
Contenu partiellement en chinois ; les blocs de commandes restent utilisables.

### `reverse-skills-p4nda0s/` — P4nda0s/reverse-skills @ `a2baa31` (~100 KB)
7 modules outillés : `rev-frida`, `rev-unicorn-debug`, `rev-idapython`, `rev-dex-dumper`,
`rev-ios-dump`, `rev-struct`, `rev-symbol`, `rev-u3d-dump`.

Le binaire Android aarch64 `panda-dex-dumper` (1.7 MB, ELF strippé) **n'a pas été
versionné** : binaire tiers non audité. Le récupérer depuis le dépôt amont si un
challenge Android l'exige, et le traiter comme un artefact non fiable.

### `neurosploit/` — JoasASantos/NeuroSploit @ `92e8959` (2.4 MB)
- `techniques/` : les 486 fiches `agents_md/{vulns,recon,chains,code,infra,container,ai,meta}` + `REGISTRY.md`.
- fiches curatées à la racine : `rev/static_binary_triage.md`, `rev/obfuscation_analysis_deobfuscation.md`, `web/*`, `meta/*`.
- Voir `neurosploit/SOURCE.md` pour le périmètre et la licence (MIT).

### `ctf-arsenal/` — Durrell-229/hunter-bridge @ `f958d2b` (80 KB)
Commandes `/ctf-*` et agents (`rev-hunter`, `pwn-hunter`, `web-hunter`, `crypto-hunter`,
`forensics-hunter`, `ctf-lead`). Les commandes supposent des MCP `ctf/r2mcp/cyberchef`
absents ici → utiliser les équivalents CLI.

### `security-skills/` — NoorQureshi/security-skills @ `ee0e0c5` (396 KB, sous-ensemble)
`ctf/` (playbooks speed-run par catégorie), `reverse-engineering/` (18 modules :
triage, deobfuscation, Ghidra/IDA/Binja, .NET, firmware, malware…), `exploit-dev/`.

### `hacking-skills/` — securityfortech/hacking-skills @ `0aa49b4` (644 KB)
Skills web/offensifs génériques (complément à `ctf-web`).

### `pwn-htb/` — allsmog/pwn-claude-plugin @ `3a5e5bc` (432 KB)
7 skills pwn orientés HTB : `reconnaissance`, `static-analysis`, `dynamic-analysis`,
`heap-exploitation`, `libc-identification`, `exploit-development`, `environment-setup`.

### `android-reverse-engineering/` — SimoneAvogadro @ `0c7cf89` (1 MB)
Plugin APK complet (jadx/apktool/frida, SSL pinning, native `.so`).

## Ce qui n'a pas été copié

- `AI-agent-master-cyber-skills-list` (27 MB, 751 skills) : majoritairement blue-team,
  doublons. Sélection au cas par cas seulement.
- `claude-ctf-skills` : fork direct de `ctf-skills`, aucun contenu additionnel.
- Dépôts purement "pentest produit" (`CloverSec-CTF-Pack`, `pownie`, `nicetrygpt`,
  `cybersecurity-claude-skills`, `awesome-skills-security`) : redondants avec
  `security-skills` + `ctf-skills`.

## Licences

- `ctf-skills` : MIT (Lukasz Jagiello).
- `NeuroSploit` : MIT.
- `reverse-skill` : voir `reverse-skill/RULES.md` / LICENSE du dépôt.
- `reverse-skills`, `security-skills`, `hacking-skills`, `pwn-htb`,
  `android-reverse-engineering`, `hunter-bridge` : MIT/Apache selon dépôt ; usage
  interne prépa CTF, conserver les notices.
