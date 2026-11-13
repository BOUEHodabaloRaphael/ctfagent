# AFRICC A&D deep-read — live dry-run artifacts (harvested 2026-11-13)

From AFRICC `#ad-2025-dry-run` (18/10/2025 round). This is the REAL attack-defense format
(ICC infra: submit via gRPC-style FrontendService/SubmitFlags, targets 10.3.<team>.2).
Everything in downloads/africc-ad-live/ — UNTRUSTED, read-only, DO NOT execute.

## Exploit scripts (captured)
- `ad_exploit_submit_loop_Ax0lotl.py` — simple harvest+submit loop. SQLi on `/todos`
  (`task = "'|| (select flag from flags) ||'"`), flag regex `ICC\{[A-Za-z0-9_]+\}`,
  submit JSON `{"flags":[...]}` with Bearer token to the ICC FrontendService.
- `ad_jwt_attack_script.py` — full round-based framework `AutomatedJWTAttacker`:
  120s tick loop over teams 2-20, graceful SIGINT/SIGTERM shutdown, stats
  (flags captured / attacks / successful teams). THE reusable finale attack harness.

## Vulnerable service sources (the A&D boxes — same shape as the finale)
Extracted to `extracted/`. Both have a `patchable/` dir (what you edit to defend),
two flags per box (flag1/flag2), Dockerfile + compose.yaml.
- `extracted/juice-todo/juice-todo/` — Node.js web service.
  patchable/: app.js, apiRoutes.js (the `/todos` SQLi lives here), adminRoutes.js,
  views/{index,admin}.ejs, public/. flag1 + flag2.
- `extracted/pwn-sample/pwn-sample-kun/` — pwn service.
  patchable/firewall_filter.py (seccomp/syscall filter = patch target), prog.c + prog
  (the vuln binary), prog_wrapper.py, flag.

## Also seen (not pulled): a pcap ("download the pcap to see how other teams steal our
## flags" — defensive traffic analysis) in the same channel.

## HTB #holmes-writeups (second deep-read target) — BLOCKED
Both threads ("Holmes CTF 2026 reichenbach directive"; "Write-up for 01,03,04,05,06,07,09")
are permission-gated for this account: "Tu n'as pas la permission de consulter l'historique
des messages." Titles visible, content not. DFIR CTF; content inaccessible — not bypassed.

## Deliverable: AFRICC-AD-PLAYBOOK-FOR-NCTF.md (attack loop + minimal SLA-safe patches).
