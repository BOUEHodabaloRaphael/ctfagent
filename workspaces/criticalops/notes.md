# HTB Challenge: Criticalops (web, Very Easy, 100 XP)

- Target: 154.57.164.72:34375 (HTTPS, self-signed cert -- curl needs -k / requests needs verify=False)
- Official writeup PDF (Downloads/9f26bee2-...pdf): JWT secret hardcoded client-side, forge admin
  role, access admin panel.

## SOLVED ✅ — Flag: HTB{Wh0_Put_JWT_1n_Cl13nt_S1d3_lm4o}

### Vulnerability
Classic "JWT auth implemented entirely client-side" bug:
- `POST /api/auth/login` returns `{id, username, role}` but sets **no cookie, no session** at all.
- The frontend (Next.js/React) itself calls `generateToken()` (in `lib/jwt.ts`, bundled into
  `/_next/static/chunks/176-eb986a17f94086c9.js`) using a **hardcoded signing secret**:
  `SecretKey-CriticalOps-2025` (HS256, `jose` library) and stores the resulting JWT as both
  `localStorage.authToken` and an `authToken` cookie.
- Server middleware on `/dashboard` and `/admin` only checks that an `authToken` **cookie is
  present** (confirmed: a garbage cookie value like `authToken=dummy` is enough to get a 200 and
  the full page bundle instead of the 307 redirect to `/login`).
- Actual authorization for role-gated UI/data happens by trusting the JWT's `role` claim, which
  we can set to `"admin"` ourselves since we know the signing secret.

### Confirmed identical build across instances
The dashboard page bundle filename (`176-eb986a17f94086c9.js`) is byte-identical to the one shown
in the official writeup's screenshots -- the challenge's static Next.js build is **not
randomized per spawn**, so the secret recovered in the writeup transferred directly to this live
instance (verified independently by downloading the chunk and grepping for the string -- did not
blindly trust the writeup).

### Exploit flow
1. `POST /api/auth/register` + `POST /api/auth/login` -> get a real `userId`.
2. Forge `{userId, username, role: "admin", iat, exp}` signed HS256 with
   `SecretKey-CriticalOps-2025` (PyJWT).
3. Send the forged token as both `Authorization: Bearer <token>` and `Cookie: authToken=<token>`
   on API calls (no need to actually click through the UI).
4. `GET /api/tickets` (an endpoint any authenticated user can normally hit, confirmed via the
   app's `lib/constants.ts`-equivalent chunk listing `LOGIN/REGISTER/TICKETS/CONTROLS/SENSORS`,
   no dedicated `/api/admin` or `/api/flag` endpoint exists) returns a pre-seeded ticket whose
   title/description literally contains the flag (a fake "forgot my password" ticket with
   `password: HTB{...}` embedded by the challenge author as the plant).

### Gotchas during solving
- Target uses **HTTPS with a self-signed cert** -- `curl -k` / `requests(verify=False)` needed.
  Browser automation (claude-in-chrome) **cannot** attach to a tab stuck on Chrome's "Privacy
  error" interstitial for a self-signed cert, so this had to be solved via scripted HTTP calls
  instead of clicking through the UI like the writeup's screenshots show.
- The chunk containing the JWT secret (`lib/jwt.ts`) is **not referenced in the static
  `/register` or `/login` page HTML** -- it's a Next.js app-router route chunk that only gets
  pulled in on `/dashboard` (or `/admin`). Discovered it by requesting `/dashboard` with *any*
  non-empty `authToken` cookie (bypasses the presence-only middleware check) and reading the
  `<script src=...>` tags in the returned HTML.
- `/api/auth/login` sets no `Set-Cookie` at all -- don't waste time looking for a session cookie
  server-side; the whole auth model is client-trust-based by design (that's the bug).

### Script
`workspaces/criticalops/solve.py` -- fully automated, one run, registers a fresh throwaway
account, forges the admin JWT, and extracts the flag from `/api/tickets`.
