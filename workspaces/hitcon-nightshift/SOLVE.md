# Night Shift Archive — HITCON CTF 2026 (misc, 500pts)

Instancer: http://nsa.chal.hitconctf.com/
Description: "Your instance runs a private D-Bus service." Blackbox, no attachments.

## Progress log

### Session resumed (2026-10-23)
Previous agent's workspace was found EMPTY (no SOLVE.md, no cookies, no scripts saved
anywhere in the repo despite the handoff note claiming "Instance created, session cookie
set (team_id 307)"). Re-derived everything from scratch:

1. Confirmed no saved session/cookies/scripts anywhere under `/home/kali/ctfagent` or
   `/tmp` for this challenge.
2. Instancer requires a "Team Token" (HITCON CTF's per-team CTFd token). Found it via the
   already-authenticated Chrome tab (claude-in-chrome) on `https://ctf2026.hitcon.org`:
   team page (`/team/`) shows `Token: eb80976f-91e5-445f-ac94-f7ddf42601f3` for team
   "holl0w kn16th".
3. `POST http://nsa.chal.hitconctf.com/create` with `token=<team token>` → 302 redirect,
   sets session cookie `{"team_id":307}...` (matches the "team_id 307" mentioned in the
   handoff — confirms this is the same backend/team).
   - NOTE: the instancer backend is flaky/overloaded (intermittent 502 / connection
     refused under competition load). Retry with patience; GET / and POST /create both
     eventually succeed.
4. `GET /` (with session cookie) shows the created instance:
   - `http://nsa.chal.hitconctf.com:30307` — credential: `player / {Team Token}`
   - i.e. HTTP Basic Auth: username `player`, password = our team token
     `eb80976f-91e5-445f-ac94-f7ddf42601f3`
5. Port 30307 is an nginx reverse proxy in front of **ttyd** (web terminal), protected by
   HTTP Basic Auth (`WWW-Authenticate: Basic realm="Night Shift Archive"`).
   - `/token` → `{"token": ""}` (no extra ttyd auth token needed beyond the basic auth).
   - ttyd websocket endpoint: `ws://nsa.chal.hitconctf.com:30307/ws`, subprotocol `tty`.
6. Wrote a Python client (`/tmp/.../scratchpad/ttyd_client.py`, uses `websockets` lib) to
   drive the ttyd session non-interactively: connects with Basic Auth header, sends the
   ttyd init JSON `{"AuthToken":"","columns":200,"rows":50}`, then sends commands as
   `b'0' + cmd + "\n"` frames and prints all `'0'`-prefixed (output) frames.
7. Got a shell: `player@night-shift-archive:~$`, `id` → `uid=12000(player)
   gid=12000(player) groups=12000(player)`, home `/home/player` (empty, only `.` and
   `..`).

### D-Bus enumeration (session 2, 2026-10-23 continued)

D-Bus session bus address inside the shell: `DBUS_SESSION_BUS_ADDRESS=unix:path=/run/archive-bus/bus`.
`busctl` and `dbus-send` are available; `python3-dbus` (the `dbus` module) is installed on
the remote box (useful for scripting — `pydbus` is NOT installed).

`busctl --address=unix:path=/run/archive-bus/bus list` shows:
- `org.ctf.Archive1` (pid 10, user `archive-coordinator`) — the main service.
- `org.ctf.ArchiveWorker1` (pid 9, user `archive-worker`) — a worker service (not yet
  introspected directly — may be worth introspecting next).
- `org.freedesktop.DBus` (dbus-daemon itself, user `archive-bus`).

`busctl tree org.ctf.Archive1` only shows the static node `/org/ctf/Archive1` (job objects
are dynamic, so they never show up in the static tree).

**`/org/ctf/Archive1` interface `org.ctf.Archive1.Manager`:**
- `ListRecords() -> a(ss)` — lists record name + description pairs. Built-in public
  records seen: `welcome`, `manual` ("Archive export guide"), `ledger` ("Nightly run
  ledger guide"). Also lists any of our own `stg-N` staged records.
- `GetHistory() -> a(ts)` — returns a **ring buffer of the last 16 entries (8 pairs)** of
  `"verification run submitted"` / `"verification run abandoned"` log lines with
  microsecond-epoch timestamps. This is a periodic background job run by the coordinator
  itself, roughly every **~10.3 seconds**, submitted then abandoned ~0.3s later.
  **IMPORTANT: this history array appears to update atomically per full cycle** — in
  tight-loop polling we never observed a transient state showing "submitted" without its
  matching "abandoned" already present, suggesting GetHistory is not a reliable way to
  detect the live window (by the time you can see "submitted" in history, the job is
  probably already gone). Treat this as unconfirmed but a strong prior from testing.
- `Stage(name: s) -> token: s` — stages a record, returns a `stg-N` token. Confirmed that
  passing an arbitrary free-text string as `name` just creates a new personal record
  containing that literal string (shows up in ListRecords as `stg-N` / "Staged by your
  account") — i.e. `Stage` is NOT a path-traversal / arbitrary-file primitive, it's just a
  scratch note for ourselves.
- `Submit(record_name_or_token: s) -> job_path: o` — **accepts either a `stg-N` token OR
  any public record name directly** (e.g. `Submit("ledger")`, `Submit("welcome")` both
  work without staging first). Returns a job object path `/org/ctf/Archive1/jobs/j<N>`
  where `<N>` is a **single global, monotonically-increasing counter shared by ALL
  clients including the coordinator's own internal "verification" submissions** —
  confirmed by observing gaps in the counter sequence that correlate with background
  "verification run submitted" events.
  - Calling `Submit("verification")` or similar guesses directly as a record name gives
    `org.ctf.Archive1.Error.NotFound` — the verification job is NOT a record we can name
    ourselves; it must be the coordinator's own internal/hardcoded submission.
  - **`Submit()` has a per-account outstanding-job limit** — after ~7-8 uncollected jobs
    you get `org.ctf.Archive1.Error.LimitExceeded: The job limit has been reached.` Once
    hit, it does NOT auto-clear even after the job *objects* themselves expire off the bus
    (confirmed: `busctl introspect`/`Collect` on old job paths → `Unknown object`, yet
    `Submit` still refuses with LimitExceeded) — the Manager tracks outstanding count
    separately from live objects. **Did not yet find a way to clear this** — tried
    `Manager.Discard("welcome")`, need to test `Discard` with the job's own `stg-N` token
    or numeric id or full object path (untested due to instance going down — see below).
    **Next session: figure out the exact `Discard(s)` argument format and call it after
    every Submit to avoid exhausting the limit before a race attempt completes.**

**`/org/ctf/Archive1/jobs/j<N>` interface `org.ctf.Archive1.Job`** (confirmed via
introspecting a job we created ourselves right after Submit):
- `GetStatus() -> (s, s)` — returns `(state, description)`, e.g.
  `("Queued", "The job is waiting for the worker.")`,
  `("Running", "The worker is processing the export.")`,
  `("Completed", "The result is ready for collection.")`.
- `Collect() -> h` (UNIX_FD) — returns a sealed read-only file descriptor. **Confirmed
  working end-to-end**: `Submit("ledger")` → poll `GetStatus()` in a tight loop (no sleep)
  → ~5.1s later status becomes `Completed` → `Collect()` → `os.read()` the fd → got the
  full "ledger" record text (public, not the flag — just confirms the whole pipeline
  works). `Submit("welcome")` / `Submit("manual")` complete much faster (~0.1s).
- Jobs we create ourselves do NOT appear to self-destruct while `Running`/`Completed` and
  uncollected — a job we created via `Collect`-loop sat fine for 5+ seconds. However, jobs
  NOT created by us (i.e. presumably the coordinator's own verification jobs) could never
  be found: every attempt to `GetStatus`/`Collect` a candidate job id (computed precisely
  from counter-gap detection, see below) immediately returned `Unknown object`, even when
  checked within ~0.3-1ms of detecting the gap. This means the coordinator's own
  verification job is destroyed (or at minimum made un-queryable) **extremely fast** —
  likely synchronously as part of its own Submit+immediately-Discard code path, not after
  a real 300ms wait as the history timestamps might suggest (see atomicity note above).

**Key open question for next session:** is `Collect()`/`GetStatus()` even ownership-checked
at all (i.e. can any player client query/collect ANY job id regardless of who submitted
it)? This was never actually confirmed with a **real, independently-submitted-by-someone-
else** job, because we never successfully caught the coordinator's job object alive. All
successful Collect()s so far were on jobs **we ourselves submitted**. If Collect() has no
ownership check, the vuln is almost certainly a pure timing race on the coordinator's
"verification" job (which likely resolves to something with the flag inside — the fact
that it's a distinct, internal-only record name, abandoned every cycle, strongly suggests
it *is* the flag-bearing record and the challenge is literally "win the race before the
coordinator's own abandon/cleanup logic beats you to it").

### Tooling built this session (all in the session-scoped scratchpad — recreate if missing)
- `ttyd_client.py` — base websocket driver (Basic Auth + ttyd init frame), as before.
- `race_collect.py` — Submit(name) then tight-loop poll GetStatus/Collect on the resulting
  job; proves the Submit→poll→Collect pipeline works for a job we own.
- `catch_verify.py` — polls `GetHistory()` waiting for a new "verification run submitted"
  entry, then immediately probes our own counter and scans the small gap of ids below it
  for a collectible job. **Problem found and fixed in v2**: the burst-scan initially kept
  re-collecting our OWN leftover uncollected probe jobs from previous cycles (same content,
  108 bytes = the "welcome" text) instead of the coordinator's job, because those leftovers
  fell inside the scanned id window. Fixed by tracking `my_known_ids` and excluding them —
  but after the fix, zero coordinator jobs were ever found (see `Unknown object` issue
  above), AND this approach leaves lots of uncollected jobs lying around (contributing to
  the LimitExceeded problem).
- `gapwatch.py` — tighter approach: tight-loop `Submit("welcome")` (small 4ms sleep between
  calls) tracking our own returned job-id sequence; the moment our own ids skip by more
  than 1 (a "gap"), that gap-id is almost certainly the coordinator's concurrently-created
  verification job — try to `GetStatus`/`Collect` it immediately, sub-millisecond latency.
  **This is the most promising detection strategy so far** but two problems surfaced
  before it could prove out: (1) it also leaves a trail of uncollected "welcome" jobs
  (one per loop iteration before a gap is found) which exhausts the LimitExceeded quota
  very fast — **needs to self-collect its own probe job immediately after creating it,
  every iteration**, not just on gap detection; (2) the whole instance (both the
  instancer web app on port 80 AND the ttyd port 30307 for our running instance) went down
  with 502/connection-refused errors shortly after a `gapwatch.py` run that hit
  `LimitExceeded` repeatedly in a tight loop — **go easier on request volume**; add a
  small sleep/backoff when LimitExceeded is hit instead of busy-looping on it, since
  spamming Submit calls in a tight loop even after they start erroring may have
  contributed to overloading the backend (or it may be unrelated competition-wide load —
  unconfirmed).

### Immediate next steps for whoever resumes this
1. Recreate the instance (`POST /create` with the team token below) and reconnect ttyd —
   retry patiently through 502s, the backend is flaky under CTF load.
2. Fix `gapwatch.py`: after each `Submit("welcome")`, immediately `Collect()` that SAME job
   before looping again (don't leave it outstanding), to avoid `LimitExceeded`. Reduce
   request rate (e.g. ~20-50ms between iterations, or make the probe loop only run for a
   short burst just before each expected ~10.3s cycle boundary rather than continuously).
3. Figure out `Manager.Discard(s)` argument format (try the job's object path string, try
   a bare job-id string, try re-submitting the same record name to see if tokens repeat) so
   stray jobs can be cleaned up without waiting for the whole instance to be recreated.
4. If/when a coordinator-owned job id is caught alive (`GetStatus` succeeds and isn't
   `Unknown object`), immediately call `Collect()` on it regardless of state, and also try
   `Collect()` even while status is `Queued`/`Running` (don't necessarily wait for
   `Completed` — the fd might be valid earlier, or Collect might be the thing that actually
   triggers/locks in the race outcome).
5. Also worth trying in parallel: introspect `org.ctf.ArchiveWorker1` (pid 9, the worker
   service) directly — it was listed in `busctl list` but never introspected this session.
   It may expose its own methods (maybe without the per-account job limit, or with a
   different/weaker ownership check) that could shortcut the whole race.
6. Flag format is `hitcon{...}` — report exact string, do not submit yourself.

### Blocked on backend outage (2026-10-23, ~16:50-17:20 UTC)
After the `gapwatch.py` tight-loop run hit `LimitExceeded` repeatedly, both
`http://nsa.chal.hitconctf.com/` (the instancer, port 80) and our running instance's ttyd
port (30307) started returning `502 Bad Gateway` / `connection refused`. Recreating the
instance (`POST /stop` then `POST /create` with the team token) also returns `502` from
the instancer itself. Retried patiently across ~13+ minutes (two separate backoff loops,
~8s interval) with zero recovery — this is a sustained outage, not a transient blip.
Unclear if self-inflicted (our rapid Submit-spam before hitting the limit) or
competition-wide load; `ctf2026.hitcon.org` root also returned 403 but that's likely just
a WAF blocking non-browser curl requests, not evidence the whole platform is down.
**Next session: just retry `POST /create` with the token below every minute or two — no
new technique needed, this is purely an infra-availability wait.** Once an instance comes
up, resume directly at "Immediate next steps" above (fix gapwatch.py's self-collect +
rate-limit, then hunt the coordinator's verification job).

## Credentials / access (for continuing this session)
- Team token (HITCON CTF account "holl0w kn16th"): `eb80976f-91e5-445f-ac94-f7ddf42601f3`
  (do not leak outside this authorized engagement — CTFd explicitly warns not to leak it)
- Instance created via team_id 307, cookie value format:
  `{"team_id":307}.<sig>.<sig>` (curl cookie jar session name `session`)
- Instance endpoint: `http://nsa.chal.hitconctf.com:30307` (ttyd), Basic Auth
  `player:eb80976f-91e5-445f-ac94-f7ddf42601f3`
- Instance TTL: 900s from creation — if expired, re-POST `/create` with the token above
  (the instancer backend at `http://nsa.chal.hitconctf.com/` is flaky under load; retry on
  502/connection-refused).
- ttyd driver script: `/tmp/claude-1000/-home-kali-ctfagent/f1e984ea-c95a-42f7-b1b4-74be93508860/scratchpad/ttyd_client.py`
  usage: `python3 -I ttyd_client.py "cmd1" "cmd2" ...` (each arg is one shell command,
  output streamed to stdout). NOTE: this path is in a session-scoped scratchpad and may
  not persist — recreate from the snippet in this file if missing.

Flag: NOT YET FOUND.
