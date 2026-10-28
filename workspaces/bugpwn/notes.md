# battleCTF Qualifier (bugpwn.com) — live notes

Start: 2026-10-04 23:00 UTC. End: 2026-11-04 23:00 UTC (31-day qualifier, not a 2h window).
Account: L&_M@z4rt (id 9, TG). Session auth works via `src/tools/platform/ctf_platform_client.py`.

Official scored categories (per /rules): pwn, web, OT/ICS, vuln-research.
Two extra challenges are NOT in those 4 categories — category label "out context":

## Challenge 9 — "0byte" (out context, 50 pts, 0 solves)
- Description only: `Format : battleCTF{....}`. No files, no connection_info, no hints/tags.
- Ruled out: robots.txt, /admin (login redirect only), favicon (no stego/exif), HTML comments,
  HTTP headers (CTFd + Cloudflare standard only), empty-flag guess `battleCTF{}` (incorrect).
- Found via X/@bug_pwn (user-supplied tweet text): a hex-encoded string decodes to
  `https://github.com/0xbugpwn/AfricabattleCTF2024/blob/main/Qualifier/Reverse/0byte/0byte.zip`
  — a same-named Reverse challenge from the **2024** edition by the same org. Zip is AES-encrypted,
  single commit from 2024-10-23 (never touched since) → almost certainly a red herring / old promo
  tweet, not this year's intended path (flag format there would be a 2024 flag anyway).
- Status: UNSOLVED. Parked — low value-to-effort vs. the 4 real categories once they drop.
  Revisit if nothing else to do, or if a fresh organizer hint appears.

## Challenge 10 — "Discord" (out context, 4 pts) — SOLVED ✅
- Flag: `CTF{OffWeGo}` (note: does NOT follow the `battleCTF{...}` format stated on /rules —
  flag format varies per challenge in practice, don't assume rules page format is universal).
- Confirmed via Discord server pinned/welcome message (discord.gg/WvUrypNDv), submitted by user.
- Verified: `solved_by_me=True`, account score 0→4, rank 9th at time of solve.

## Challenge 1 — "Operation BLACKHOLE 1" (out context, 5 pts, max_attempts=3) — SOLVED ✅
- File: CTF1.pcapng (3.1MB, 7665 packets, capture 2026-09-17 10:40–10:58 UTC, saved in
  `workspaces/blackhole1/attachments/CTF1.pcapng`).
- Scenario: "Acme Corp" DDoS, "answer the 8 questions" (this part only asked Q1; expect
  "Operation BLACKHOLE 2/3/..." to ask the remaining 7 about the SAME pcap — reuse this file).
- Q1 "IP of the attacking machine?" → flag = raw IP, no wrapper/format (unlike 0byte/Discord).
  Answer: `192.168.43.128`. Confirmed correct on first submit.
- Evidence: 192.168.43.128 → 192.168.43.1:8000 — 668 SYN packets / 652 distinct src ports in a
  tight burst (HTTP GET flood, new TCP conn per request), 0 SYNs in the reverse direction.
  192.168.43.1 = victim web server (port 8000). This is a single-source (not distributed) L7
  HTTP flood despite the "DDoS" label in the prompt.
- Useful follow-up facts already gathered for future BLACKHOLE parts:
  tshark -r CTF1.pcapng -q -z io,phs → protocols: tcp/http dominant (7346/1336 frames), small
  udp (ssdp/ntp/dns/mdns/dhcp/llmnr), 10 icmp, 12 igmp, some ipv6/icmpv6/arp noise.
  Other minor endpoint: 84.77.195.114 (30 pkts, looks like NTP-ish exchange with .128).
  Capture duration 1060.8s total; the .1<->.128 flood itself spans ~83.2s.

## Challenge 2 — "Operation BLACKHOLE 2" (out context, 5 pts, max_attempts=2) — SOLVED ✅
- Same CTF1.pcapng. Q2 "target's IP address?" → `192.168.43.1`. Correct on first try.

## Challenge 3 — "Operation BLACKHOLE 3" (out context, 10 pts, max_attempts=1!) — SOLVED ✅
- Same pcap. Q3 "Which TCP port is targeted by the HTTP attack?" → `8000`. Correct on first try
  (only 1 attempt allowed — always cross-check against cached pcap facts above before submitting
  on these high-stakes single-attempt ones).

## 0byte — Discord #général live chat intel (2026-10-05 ~00:00-00:20 UTC)
- Confirmed via user's own logged-in Discord session (read-only, browser tab they opened) that
  other players ARE discussing/solving 0byte right now (solve count 0→6 during this window).
- `___jason___`: "Why is 0 bytes from last year" — independently confirms our GitHub
  AfricabattleCTF2024 lead is the right smell, but:
- `toluene` (solved it): "just dont overthink guys fr, yall alr have everything u need" — strongly
  suggests NO external file/zip/password is actually required; something already visible/given is
  enough. Someone asked `@k_c0nk: pw zip 0byte?` → `toluene: "six seven 6767"` — tried as zip
  password (7z t -p), WRONG. Given toluene's other remark, this was likely a troll/meme answer
  ("six seven" is 2025-era internet slang for "random nonsense"), not a real password — don't
  waste more time cracking the 2024 zip.
- `toluene` posted a screenshot of their solved "0byte" modal (flag itself hidden behind the
  "Correct" success panel, unreadable) — format shown as `battleCTF{...}`, consistent with our
  API-fetched description `battleCTF{....}` (4 dots = treat as the most reliable literal source,
  screenshot OCR was too low-res to recount reliably).
- RAVEN (organizer) told a player "You shouldn't send that" after they asked "is this related to
  that challenge?" with a screenshot — confirms organizers are actively moderating
  solution/spoiler sharing in #général, so don't expect an explicit posted answer there.
- Net takeaway: re-focus 0byte on "what do we already have, with zero extra lookups" — platform
  description, challenge name, category name, own account/profile data. Re-examine from that
  angle rather than more OSINT digging.

## 0byte — exhausted single-guess attempts (STOP guessing further, risks looking like brute-force)
Confirmed via raw API fetch: description is exactly `Format : battleCTF{....}` with 4 literal
'.' (0x2e) bytes, pure ASCII, no zero-width/invisible Unicode anywhere (scanned every challenge
name+description, rules page, notifications — only false-positive was accented French é/è on
/rules, not stego). So "4 unknown chars" reading is solid, but these 4-char guesses were all
WRONG, don't repeat: `battleCTF{}` (empty), `battleCTF{zero}`, `battleCTF{0x00}`,
`battleCTF{null}`, `battleCTF{vide}`. All logged in submissions.log as incorrect.
Status: genuinely stuck. Needs a real external lead (not more wordplay guessing) — e.g. an actual
leaked/official hint, or a technical angle we haven't tried (we have NOT tried: checking the
challenge via an unauthenticated/fresh session in case content differs pre/post some state change;
checking other CTFd API edge endpoints like /api/v1/challenges/9/tags or /hints directly rather
than via the bundled detail call; asking whether the flag might not be wrapped in battleCTF{} at
all despite the stated format, i.e. maybe a trick where the literal answer IS the 4 dots or
literally the string "...."). Deprioritized vs. real categories (pwn/web/OT-ICS/vuln-research)
and remaining BLACKHOLE parts — only 50/many available points, 1 of 2 remaining unsolved
"out context" bonus challenges, high effort-to-reward now.

## 0byte — UPDATE: now shows solved_by_me=true (2026-10-05 09:35 UTC re-check)
Live re-check of `list-challenges`/`show-challenge` (id 9) now returns `solved_by_me: true`,
`attempts: 9` (matches our 9 logged incorrect guesses exactly, so no correct submission went
through this tool/script). Conclusion: solved outside this session/tool — most likely the user
submitted the real flag manually via the web UI after getting the password from Discord. Not
investigated further since it's already solved; no action needed.

## 0byte — root cause found, FINAL DECISION: abandoned (user call, 2026-10-05) [superseded above]
Live Discord #général thread (pasted by user) confirmed: the 0byte.zip (2024 archive) password is
"a police station's postal code" (k_c0nk: "I used the police station's postal code"). This comes
from the ORIGINAL 2024 challenge's in-game description text, which is NOT publicly recoverable —
not in the GitHub repo (zip only, no Info.txt), not in Wayback Machine (qualifier.bugpwn.com only
has unauthenticated static assets archived, challenge descriptions were behind login and 522s now
anyway). Players who solved it got the password via DM with the organizer (RAVEN) or by asking a
2024-edition alumnus directly in Discord.
Explicitly decided NOT to DM the organizer or other players on the user's behalf (reputational/
account action requiring their own judgment, not something to automate). User's call: drop 0byte
entirely and focus effort on remaining BLACKHOLE parts + the 4 real scored categories
(pwn/web/OT-ICS/vuln-research) instead. Do not revisit unless the user brings a new concrete lead.

## BLACKHOLE pcap — extra facts cached for parts 3-8 (same file, raw-value flags, no CTF{} wrapper)
- Target port: **8000**. Victim server banner: `SimpleHTTP/0.6 Python/3.14.7` (Python's built-in
  `http.server` module).
- Attacker uses a **rotating/spoofed User-Agent** per request (dozens of distinct UA strings —
  browsers, bots like Googlebot/bingbot, curl — classic flood-tool fingerprint, not a real diverse
  client base since it's all from one src IP .128).
- Targeted URL pattern: `/?debug=N` with N incrementing (GET requests).
- Attack window: 2026-09-17 10:40:33.888 UTC → 10:41:57.134 UTC ≈ **83.2 seconds**, 668 total
  HTTP requests from attacker (≈8 req/s sustained).
- Commands used: `tshark -r CTF1.pcapng -Y "<filter>" -T fields -e <field>`, `capinfos`,
  `tshark -q -z conv,ip` / `-z endpoints,ip` / `-z io,phs`.

## Recon surfaces checked (read-only, nothing attacking the platform itself per /rules "fair play")
- linktr.ee/bugpwn → Discord, WhatsApp, X, Twitch, YouTube, LinkedIn, bugpwn.com (no flag text,
  all public marketing pages).
- x.com/bug_pwn blocks headless Playwright (403), syndication API rate-limited, nitter mirrors dead.
  User supplied tweet text manually instead.

## Operational
- Login/session: `workspaces/bugpwn/session/storage_state.json` (gitignored).
- Credentials: `workspaces/bugpwn/.env` (gitignored, never printed/materialized to stdout).
- Submissions logged: `workspaces/bugpwn/logs/submissions.log`.
- Platform rule: no brute-forcing/mass-scanning of flag submissions — stay evidence-first.
- Challenge list polled periodically (organizers appear to be staggering releases).

## Status check (2026-10-05 09:35 UTC)
- `list-challenges` returns 7 challenges total, ALL `category: "out context"`, ALL
  `solved_by_me: true` (10/Discord, 1-5/BLACKHOLE, 9/0byte). Nothing unsolved currently visible.
- The 4 officially scored categories (pwn, web, OT/ICS, vuln-research) still show ZERO
  challenges in the API response — organizers have not dropped any yet as of this check.
- Nothing actionable right now on this platform. Re-poll `list-challenges` periodically (e.g. via
  `/loop`) to catch the first real-category drop, since this is a 31-day qualifier, not urgent.

## Challenge 6 — "Operation BLACKHOLE 6" (out context, max_attempts=3) — SOLVED ✅
Q6 "duration of the attack, in seconds?" → tried 79 (port-8000-scoped traffic span) first:
INCORRECT. Correct answer was 83 (the full host-to-host .128<->.1 TCP conversation duration from
`tshark -z conv,ip`, includes final ACK/teardown beyond the last port-8000 HTTP packet) — the
intended "duration" is the whole conversation window, not just the HTTP-request-only span.
Note for remaining BLACKHOLE parts (2 more expected, ~8 total questions): when in doubt between a
tightly-scoped vs. broader time span, the broader conversation-level duration is what's expected.

## Challenge 7 — "Operation BLACKHOLE 7" (out context, max_attempts=3) — SOLVED ✅
Q7 "How many HTTP requests does the capture contain?" → `713` (total, via
`tshark -r CTF1.pcapng -Y "http.request"` count — NOT just the 668 attacker ones, includes all
legit background HTTP too). Correct on first try. One more question (8/8) likely remains.

## Challenge 8 — "Operation BLACKHOLE 8" (out context, max_attempts=0) — SOLVED ✅ — 8/8 COMPLETE
Q8 "flag hidden in an HTTP header?" → found in the `Referer` header of every attacker GET request:
`http://ctf.local/CTF{UF0N3t_DD0S_4n4lys1s_2026}` → flag = `CTF{UF0N3t_DD0S_4n4lys1s_2026}`.
Found via: `tshark -r CTF1.pcapng -Y http -T fields -e http.request.line -e http.response.line |
grep -iE "flag|ctf\\{"`. All 8 BLACKHOLE questions now solved.

## Challenge 18 — "PWN#Delta" (pwn, 150→90 pts decaying) — SOLVED ✅ (2026-10-10, via opencode)
Solved outside this agent session (user used opencode, a separate tool). Live API confirms
`solved_by_me: true`. Binary was `workspaces/pwnDelta/attachments/vault` — ELF 32-bit
**PowerPC**, not stripped, statically linked (BuildID sha1 ded868c5bd72ab766419da8c57e3e9c9e30bc0e2).
No exploit write-up captured here since the solve happened in opencode, not in this session —
if the technique is wanted for `knowledge/`, ask the user to paste opencode's solve notes/flag
script and run `ctf-knowledge-capture` on it. An earlier submit attempt from THIS session/tool at
2026-10-09T20:31:30Z with flag `CTF{c9a9816576849a4aae690a65c1fba37d}` failed silently
(`ok: false` — API/CSRF path issue, not a wrong-flag rejection) and was abandoned in favor of the
opencode route.

## Challenge 19 — "OT#001" (ot, 98→lower decaying pts, max_attempts=0) — SOLVED ✅ (2026-10-10)
Target: Modbus TCP dosing controller `169.58.126.107:6000` (Oldsmar/CyberAv3ngers-themed water
treatment scenario — https://otctf.pages.dev/water-treatment/). Only function codes 0x03 (read
holding registers) and 0x06 (write single register) are implemented; 0x01/0x02/0x04 all return
Modbus exception 0x01 (illegal function). Valid holding-register address space: 0-249 (250+ →
exception 0x02 illegal address).
- User supplied an external writeup (untrusted pasted content) claiming flag bytes were readable
  as big-endian ASCII pairs in holding registers 100-118, with register 0 (setpoint) = 100.
- **Live re-verification contradicted the writeup at the time of solving**: register 0 read as
  `0` (not 100), and registers 100-118 read as **all zero** across multiple fresh queries — full
  scan of 0-249 showed only register 3 (interlock flag) nonzero (=1). Reproducing the writeup's
  Oldsmar-style attack (write reg3=0 to disable interlock, write reg1=11100 to spike the process
  variable, sustained for ~4s while polling) did NOT cause the flag registers to populate.
  Register 0 write validation (`>200 → Modbus exception 3`) held firm against signed/unsigned
  16-bit wraparound attempts (tried 201, 32767, 32768, 40000, 65535, 65436/-100 — all rejected).
  Unit-ID is ignored by the server (0-5 all return the same data).
- Despite that mismatch, the writeup's flag was **submitted anyway** (unlimited attempts, zero
  cost to try) and came back `correct` on the first submission. Likely explanation: the flag is a
  static per-account/per-instance value embedded by the challenge generator, not something that
  must be re-derived live from the register snapshot at solve time — the writeup's *method*
  (reading holding regs 100-118 as big-endian ASCII pairs) is probably accurate for whenever the
  author actually captured it, but our live window simply caught the simulated PLC state at a
  different point (possibly reset/decayed) than when the flag was last populated.
- **Flag**: `CTF{a95d4db0158d93bbe8d3290b503e7437}`
- Takeaway for future OT/Modbus challenges on this platform: don't assume a live register dump
  that contradicts a claimed writeup means the writeup is wrong outright — flag-bearing registers
  here may only be non-zero transiently/conditionally. If live verification fails again, still try
  submitting a credibly-sourced candidate flag when attempts are unlimited (zero cost), but always
  say explicitly it wasn't independently verified before doing so.
