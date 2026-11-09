---
name: ctf-attack-defense
description: Methodology for Attack-Defense / King-of-the-Hill (A&D/AWD/KOTH) CTF rounds, where your team both exploits the same vulnerable service on opponents and must detect and patch it on your own box between scoring rounds. Use when the challenge format is confirmed A&D/KOTH (shared vulnerable service image, repeated scoring rounds, SLA/uptime checks) rather than a solo jeopardy challenge. Covers log-based intrusion hunting without an alert in hand, incident workup from a lead, and turning a confirmed flaw into a minimal, reviewed patch that keeps the service passing its checker.
license: MIT
compatibility: Requires filesystem-based agent (Claude Code or similar) with bash, Python 3, and internet access for tool installation.
allowed-tools: Bash Read Write Edit Glob Grep Task WebFetch WebSearch Skill
metadata:
  user-invocable: "false"
  author: raphboue
  provenance: "Methodology adapted (not copied) from anthropics/defending-code-reference-harness (Apache-2.0, Copyright 2026 Anthropic PBC), reshaped for CTF A&D/KOTH time pressure. See Attribution section."
---

# CTF Attack-Defense / KOTH

Use this skill once the format is confirmed Attack-Defense or King-of-the-Hill,
not a solo jeopardy challenge: every team runs the same vulnerable service
image, you exploit it on opponents while defending your own instance, and a
gameserver scores repeated rounds (uptime/SLA + flag submission). If you are
still unsure which mode you are in, stay in `ctf-solver-profile` /
`web-triage` / `pwn-triage` until the format is confirmed — see "Exit
conditions" below for how to tell.

A&D is **not** jeopardy with a time limit. The defining constraint is that a
careless patch that breaks the service costs your own uptime score just as
much as the exploit you were defending against — so every fix here is
proposed and reviewed before it is applied, never auto-applied.

## Two tracks

Run these as needed, not necessarily in order — on your own box you hunt and
respond; against opponents you reuse your own confirmed exploit (see
`ctf-web`/`ctf-pwn` for the offensive side, this skill does not duplicate
that).

1. **Hunt** — no alert in hand yet, you suspect your box is already being hit.
2. **Respond** — a lead exists already (an alert, a suspicious IP, a dropped
   connection, a teammate's report) and you need the full picture fast.

Both tracks end the same way: a confirmed root cause, located at file and
function, with a minimal patch that a second pass reviews before it is
applied to the live service.

## Hard rules (apply to both tracks)

1. **Log evidence alone never confirms a vulnerability.** Use this verdict
   ladder:
   - `confirmed_exploited`: log evidence AND the flaw located in source
     (file + function) AND a PoC fired locally against a throwaway instance.
   - `suspected`: log evidence without a fired PoC yet.
   - `attempted_not_vulnerable`: attack traffic present, but source shows a
     guard and the PoC bounces off it.
2. **Query, don't read.** Never `cat`/`Read` a multi-MB log file whole.
   Profile first (`wc -l`, `du -h`, `head`, `tail`), then query with
   `grep`/`awk`/`sort | uniq -c` or a short `python3` one-liner.
3. **Propose, never auto-apply.** No blocking rules, service restarts, or
   config edits land on the live box without you (the operator) reviewing
   the diff. This skill produces a patch file and a rationale, not a
   `git commit` to the running service.
4. **PoCs fire locally only**, against an instance you started yourself
   (`127.0.0.1`, a throwaway copy of the service) — never against the live
   scored instance, and never against an opponent outside the match rules.
5. **Every number cited is a query result from this session**, never an
   estimate. If you cannot point to the exact command that produced a
   count, don't state the count.

## Track 1 — Hunt (no alert yet)

Inputs: the service's log directory (access log, app log, auth log if
separate), and the service source if you have it (you usually do in A&D —
every team gets the same image).

1. **Locate inputs.** Find the log files, note each one's format and size
   (`wc -l`, `du -h`). List the service source tree without reading it yet.
2. **Baseline before hypotheses.** A dozen cheap one-liners before touching
   any hypothesis:
   - time window covered by the logs
   - HTTP status histogram
   - top talkers by request count
   - normalized top routes (strip IDs/tokens so `/user/123` and `/user/456`
     collapse)
   - user-agent inventory — flag anything that looks automated (curl,
     python-requests, sqlmap, empty UA)
   - auth picture: login attempts, success/fail ratio per account
   - per-route response-size profile (a route that normally returns ~200
     bytes suddenly returning 4KB is a signal)
   - error log tail
   - any existing alert queue — treat alerts as inputs to investigate, not
     as findings already proven
3. **Hunt loop with a hypothesis ledger.** Keep a running table: hypothesis
   / query / result / verdict (`supported` / `refuted` / `needs-pivot`) /
   next pivot. Seed sweeps to run in round 1:
   1. 5xx errors — do they echo attacker-controlled input back?
   2. every existing alert, verdicted against the ladder above
   3. top-talker outliers (one IP doing 50x the median request count)
   4. injection grammar in query strings/bodies (encoded quotes,
      `UNION`/`SELECT`, SQL comment markers `--`/`#`, boolean pairs like
      `1=1`/`1=2`)
   5. sequential object enumeration (IDs incrementing in a tight loop)
   6. auth anomalies (password spray pattern, session reuse across IPs)
   7. size anomalies on normally-small responses
   8. quiet-hours activity (traffic when no human on your team was testing)

   Pivot from each hit's entities (the IP, the account, the route) one ring
   outward. Stop a hypothesis after two consecutive rounds with no new
   entities — move it to `ruled_out` rather than re-running the same query
   shape with cosmetic changes.
4. **Source confirmation.** For each implicated route, trace the handler:
   find where attacker input enters, follow it to the sink, name the exact
   flaw (or the exact guard that defeated it) at file:function precision.
   Check sibling routes in the same file for the same flaw class — in A&D
   the opponent who found one bug on your box will probe siblings next.
5. **PoC detonation (local only).** Start a throwaway copy of the service in
   the background (`Popen`, capture the PID, never a bare `&` you can't kill
   cleanly), poll its health endpoint, fire the minimal PoC, fire a negative
   PoC against any route you believe is already guarded, then kill that
   exact PID.
6. **Output.** Write `workspaces/<id>/artifacts/INCIDENTS.json` (list of
   incidents: id, verdict, attacker IPs, accounts involved, vuln{type,
   route, file, function}, timeline, impact, evidence, poc) and
   `INCIDENT_REPORT.md` (3-sentence summary, timeline, per-incident detail,
   ruled-out section, the ledger as an appendix). Then go straight to the
   Patch workflow below for each `confirmed_exploited` incident — in A&D,
   the gap between "found it" and "patched it" is live opponent exposure
   time.

## Track 2 — Respond (a lead already exists)

Use when you already have something concrete: an alert line, a teammate's
"something's wrong with /login", a specific IP, or a dropped connection.

1. **Parse the lead** into seed entities and state one working question,
   e.g. "did this IP's traffic against `/login` succeed?"
2. **Scope.** Pull every request from that IP, every login/authenticated
   request from that account (compare to its own history — a new IP alone
   is baseline noise unless paired with volume/cadence/follow-on actions),
   and every hit on the implicated route. Expand one ring of entities, once
   — don't chase a graph indefinitely under round-timer pressure.
3. **Verdict and blast radius.** Decide success from discriminating
   evidence, not status codes alone (a 401 wall vs. 200s with anomalous
   sizes, or error-then-success is the real signal). Quantify: records
   touched, distinct victims, time span, data actually reached — each
   number from a query you can point to. Check whether the activity is
   still ongoing right now.
4. **Root cause and PoC** — same bar as the hunt track, plus a negative PoC
   against the fix you're about to propose.
5. **Response plan (proposed, reviewed, then applied by you).** Write
   `RESPONSE.md`: verdict + summary, timeline, containment, eradication &
   remediation, recovery, detection notes for next round, open questions.
   Each action states what / why / risk-if-wrong — in A&D, "risk-if-wrong"
   usually means "does this break the checker."

## Turning a confirmed flaw into a patch

Never apply a diff sight-unseen, even under round-timer pressure — a patch
that fails the checker costs uptime score on top of the exploit you were
defending against.

1. Read the code at the cited file:function.
2. Root-cause first: trace backward from the sink to where the untrusted
   input actually enters, don't patch the symptom at the sink alone.
3. Variant hunt: check sibling call sites for the same flaw class (A&D
   images often repeat a vulnerable pattern across 2-3 routes).
4. Write the minimal diff, matching the existing code style.
5. Adversarial self-check: name one bypass input for your own patch. If one
   exists, the fix is at the wrong layer — go back to step 2.
6. Include one regression check (a request you can replay) that proves the
   service still behaves correctly for legitimate traffic — this is what
   protects your checker/SLA score.
7. **Independent review before applying**: have a second pass (another
   agent turn, or the human operator) look at just the diff and answer:
   is it in scope, does it fix the root cause or just suppress a symptom,
   does it open new attack surface, does it match house style. Only apply
   after that review, and verify the checker still passes immediately after.

If there is no time for a full code patch before the next scoring round,
fall back to a network-level block (see
[`ctf-attack-defense-tooling-reference`](../../../knowledge/patterns/misc/ctf-attack-defense-tooling-reference.md)
for `firegex`-style hot-patching) as a stopgap, and still write the real
patch afterward — a firewall rule is not a fix, it is a tourniquet.

## Related in-house methodology — read this first if you have not already

This repo already has battle-tested A&D doctrine from real competitions —
this skill does **not** override it, it deepens the "how do I actually
investigate and patch" step inside it:

- [`attack-defense-methodology-toolkit`](../../../knowledge/patterns/misc/attack-defense-methodology-toolkit.md)
  sets the order of operations: reverse first (15-20 min), run a working
  exploit in a loop against **every** opponent before patching, patch only
  after the exploit loop is live, never stop `sla_monitor.py`. **This skill's
  Hunt/Respond/Patch tracks run inside that "patch only after" step** — they
  do not tell you to patch earlier than that doctrine says to.
- `src/tools/ctf/attack_defense_toolkit/` is the existing operational
  toolkit: `exploit_runner.py` (solo test then loop against all teams),
  `sla_monitor.py` (your own uptime signal — keep it running while you
  patch), `pcap_watch.py` (live packet recon of what opponents are trying
  against you), `submitter.py`. Use `pcap_watch.py` output as a hunt-track
  input alongside logs; use `sla_monitor.py` as the regression check after
  applying a patch.
- [`koth-methodology-thm-validated`](../../../knowledge/patterns/misc/koth-methodology-thm-validated.md)
  and
  [`koth-continuous-king-reassertion-loop`](../../../knowledge/patterns/misc/koth-continuous-king-reassertion-loop.md)
  cover the King-of-the-Hill variant specifically (full port scan immediately,
  continuous re-assertion of ownership) — read those instead if the format is
  KOTH rather than scored A&D rounds.

## Exit conditions

- Format turns out to be solo jeopardy (one target, no opponents, no
  repeated scoring rounds) → this skill does not apply; use
  `web-triage`/`pwn-triage`/`rev-triage` instead.
- You have a confirmed exploit against the shared service image → reuse it
  against opponents via your team's normal exploit-distribution flow (see
  [`ctf-attack-defense-tooling-reference`](../../../knowledge/patterns/misc/ctf-attack-defense-tooling-reference.md)
  for the external tools that scene uses — this skill does not duplicate
  that tooling).
- Multiple incidents point to the same flaw class across routes → patch the
  class once (step 3, variant hunt), not each route separately.

## Attribution

The hunt/respond/triage/patch phase structure, the verdict ladder
(`confirmed_exploited`/`suspected`/`attempted_not_vulnerable`), and the
review-before-apply gate are adapted from the `/dnr-hunt`, `/dnr-respond`,
`/triage`, and `/patch` skills in
[`anthropics/defending-code-reference-harness`](https://github.com/anthropics/defending-code-reference-harness)
(Apache License 2.0, Copyright 2026 Anthropic PBC). That project targets a
general detection-and-response pipeline over arbitrary codebases, not CTF
A&D specifically; this skill reshapes the same structure for A&D/KOTH round
pressure (scoring SLA, shared vulnerable image, no production rollback) and
is not a copy of its prose or code. No files from that repo were imported
into this repository — only the methodology was adapted. See
`knowledge/external/INDEX.md` for how this repo tracks externally-sourced
material generally.
