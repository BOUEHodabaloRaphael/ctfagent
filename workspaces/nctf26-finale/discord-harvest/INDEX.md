# NCTF Finale prep — Discord writeup harvest INDEX (2026-11-13)

Harvested every CTF server in the user's Discord, extracted writeups/solvers, and ran
analysis agents to distill techniques for the NCTF finale (attack-defense format, Lomé).

## Technique digests produced (read these)
- `../flagyard-writeups/FLAGYARD-TECHNIQUES-FOR-NCTF.md`  — FlagYard/Black Hat MEA (pwn lib, gRPC pcap, Mersenne kit, lattice forgery, z3-vs-angr).
- `BATTLECTF-TECHNIQUES-FOR-NCTF.md`  — ★ MOST RELEVANT. bugpwn/BattleCTF: the 2023 A&D Final format match, OT/ICS category shape, Node/JS web RCE combos, seccomp pwn, 2026 vuln-research track.
- `AFRICC-TECHNIQUES-FOR-NCTF.md`  — AFRICC: JS-engine pwn, web A&D staples (SSRF/smuggling/pickle), crypto kit, vaultic git-history/PNG-chunk forensics, + A&D exploit-loop+submit template.
- `CLICK2TRACE-TECHNIQUES-FOR-NCTF.md`  — Click2Trace: AI-agent/tool-abuse chain (→ nctf26-agent-tool-abuse), unified custom-VM/bytecode reversing method, GSUB font stego→SSRF, GraphQL field-suggestion, cookie-forgery.
- `MISC-AFRICAN-CTF-TECHNIQUES-FOR-NCTF.md`  — 0xFun/kBxAc/HackerLab/404CTF repos. Scene patterns: reverse=static XOR crackmes, heavy DFIR/Volatility, web SSTI/XXE/JWT, OT/SCADA forensics, kernel pwn + HAWK lattice at 404CTF level.
- `AFRICC-AD-PLAYBOOK-FOR-NCTF.md`  — ★★ (pending agent) attack/defend playbook from REAL A&D dry-run boxes (see deep-read below).

## Deep-read results (2026-11-13, round 2)
- **AFRICC A&D (SUCCESS)** → `africc-ad-live-SOURCES.md` + `downloads/africc-ad-live/`:
  pulled the live dry-run attack scripts (`ad_jwt_attack_script.py` = full round-based 120s-tick
  harvest+submit framework; `ad_exploit_submit_loop_Ax0lotl.py` = SQLi loop) AND the vulnerable
  service sources (`juice-todo` Node web w/ `patchable/` + flag1/flag2 + `/todos` SQLi;
  `pwn-sample-kun` pwn w/ `patchable/firewall_filter.py`). This is the finale format 1:1.
- **HTB #holmes-writeups (BLOCKED)**: both Holmes CTF 2026 writeup threads are permission-gated
  for this account ("pas la permission de consulter l'historique des messages"). Titles only.

## Source manifests
- `../flagyard-writeups/SOURCES.md`, `africc-SOURCES.md`, `battlectf-SOURCES.md`,
  `click2trace-SOURCES.md`, `misc-servers-SOURCES.md`
- Tracker: `../discord-harvest-TRACKER.md`

## Downloaded corpora (untrusted; read-only)
- `../flagyard-writeups/downloads/` (hokan, baby_pwn, z0v3r1n repo, gists)
- `downloads/battlectf/`, `downloads/africc/`, `downloads/click2trace/` (15 writeups), `downloads/misc/`

## Server sweep result (all CTF servers)
RICH (downloaded+analyzed): FlagYard, BattleCTF, AFRICC, Click2Trace.
GOOD repos (in MISC agent): 0xFun, kBxAc, HackerLab, 404CTF, HITCON(php2shell).
LOW/empty: CERT TG NCTF, AFRICC-2027-Quals, Dirtbags&Flags, ThunderCipher(video walkthroughs),
  GBT_Hackers, NICC(notion), NEST, CTFZone, Root-Me, pwn.college, CWL, Haker_st, UCAO.
DEEP-READ CANDIDATES (in-Discord text, not yet analyzed): AFRICC ad-2025-dry-run / enowars-9
  channels (live A&D exploit scripts); HackTheBox #holmes-writeups forum (DFIR, Holmes CTF 2026).

## Top finale takeaways (A&D)
1. BattleCTF-2023 Final == the finale format: web-RCE entry + planted local privesc (SUID/setcap/weak-pw),
   two flags/box; patch the entry file not the framework to keep the SLA checker green.
2. The single highest-value artifact is the A&D exploit-loop + flag-submit template (AFRICC digest) —
   plug in the real flag regex, submit contract, and team subnet before round 1. Wire into
   src/tools/ctf/koth_auto.sh + attack_defense_toolkit (house doctrine: exploit-first, patch-later).
3. OT/ICS recurs in the African scene (BattleCTF/DazBot) — pre-stage a hand-rolled Modbus client.
