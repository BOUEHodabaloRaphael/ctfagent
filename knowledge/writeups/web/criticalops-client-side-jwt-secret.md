---
doc_kind: writeup
title: "HTB Criticalops - Client-Side JWT Signing Secret in Frontend Bundle"
category: web
slug: criticalops-client-side-jwt-secret
created: 2026-10-25
status: solved
tags:
  - jwt
  - client-side-auth
  - source-map
  - hardcoded-secret
  - privilege-escalation
source: "HTB Challenge (web, Very Easy)"
target: "CriticalOps Next.js app"
---
# HTB Criticalops - Client-Side JWT Signing Secret in Frontend Bundle

## Challenge Summary

- Source: HTB Challenge "Criticalops" (Web, Very Easy, official writeup by lordrukie, solved independently and confirmed live by the user, flag matches the user's own instance)
- Target: CriticalOps Next.js/React infrastructure-monitoring app; live instance `154.57.164.72:34375` (HTTPS, self-signed cert)
- Goal: Reach the admin panel and retrieve the flag stored in a ticket only an admin can read

## Initial Signals

- Entry point: `POST /api/auth/login` returns `{id, username, role}` but sets **no cookie, no session** — yet shortly after, an `authToken` JWT appears in the browser's `localStorage`.
- Visible hints: no server-side token generation visible in network traffic around login → the token must be minted client-side.
- First confirming probe: decode the `authToken` JWT (HS256) — payload contains `userId`, `username`, `role: "user"`; inspecting the Sources tab / source map for the Next.js bundle reveals `lib/jwt.ts` with a hardcoded `JWT_SECRET`.

## Exploit Chain

1. `POST /api/auth/register` + `POST /api/auth/login` → obtain a real `userId`.
2. Inspect the frontend bundle (Sources tab or exposed source map) for the chunk containing `lib/jwt.ts` — not referenced from `/login`'s static HTML, but pulled in once `/dashboard` (or `/admin`) is requested. Trick to force it to load: request `/dashboard` with *any* non-empty `authToken` cookie (the middleware only checks cookie **presence**, not validity) and read the `<script src=...>` tags in the returned HTML.
3. Recover the hardcoded HS256 signing secret from that chunk: `SecretKey-CriticalOps-2025` (visible either directly in the bundled JS or via the source map's `jwt.ts`).
4. Forge a JWT with `{userId, username, role: "admin", iat, exp}` signed HS256 with the recovered secret (PyJWT, or the browser's own JWT Encoder/Decoder tooling).
5. Send the forged token as both `Authorization: Bearer <token>` and `Cookie: authToken=<token>` (server middleware on `/dashboard`/`/admin` only checks cookie presence; actual role-gated authorization trusts the JWT's `role` claim, which is attacker-controlled once the secret is known).
6. `GET /api/tickets` (an endpoint reachable by any authenticated user, per the app's route-constant chunk listing `LOGIN/REGISTER/TICKETS/CONTROLS/SENSORS` — there is no dedicated `/api/admin` or `/api/flag` endpoint) returns a pre-seeded ticket whose body literally contains the flag (a planted "forgot my password" ticket).

## Key Evidence

- No `Set-Cookie` at all from `/api/auth/login` — the entire auth model is client-trust-based by design, confirming this isn't a server-side session bug but an architectural one.
- The dashboard bundle chunk filename (`176-eb986a17f94086c9.js` in this case) was byte-identical between the official writeup's screenshots and the user's independently-spawned live instance — the challenge's static Next.js build is **not randomized per spawn**, so a secret recovered once transfers directly to any instance of the same challenge (verified independently by downloading the chunk and grepping for the string, not by blindly trusting the writeup).
- Middleware on `/dashboard`/`/admin` accepts a garbage cookie value (`authToken=dummy`) and returns 200 with the full page bundle instead of a 307 redirect to `/login` — proves the gate only checks cookie presence, not signature.

## Dead Ends

- Target uses HTTPS with a self-signed cert — `curl -k` / `requests(verify=False)` required; browser automation tooling that can't click through Chrome's "Privacy error" interstitial for a self-signed cert cannot be used here, so the whole exploit had to be scripted HTTP calls instead of UI automation.
- The `lib/jwt.ts` chunk is not referenced from the static `/register` or `/login` page HTML — searching only those pages for the secret fails; it only loads on routes that actually use client-side JWT generation (`/dashboard`, `/admin`).

## Payloads And Commands

```bash
# Force the dashboard chunk (and thus jwt.ts) to load, bypassing the presence-only cookie gate
curl -sk -b 'authToken=dummy' https://<target>/dashboard | grep -o '<script src="[^"]*"'
```

```python
import jwt  # PyJWT
forged = jwt.encode(
    {"userId": user_id, "username": username, "role": "admin", "iat": iat, "exp": exp},
    "SecretKey-CriticalOps-2025",
    algorithm="HS256",
)
# send as Authorization: Bearer <forged> AND Cookie: authToken=<forged>
```

## Flag / Outcome

- Flag (official writeup sample target, same structure): ticket body contains the flag.
- Flag (user's own live instance, confirmed): `HTB{Wh0_Put_JWT_1n_Cl13nt_S1d3_lm4o}`
- Fully automated solver: `workspaces/criticalops/solve.py` (registers a throwaway account, forges the admin JWT, extracts the flag from `/api/tickets`).

## Reusable Lessons

- When login returns user data but sets no cookie/session, and a token only appears client-side shortly after, assume the token is being minted entirely in the frontend — grep the bundled JS (and any accessible source maps) for the signing secret rather than looking for a server-side signing endpoint.
- A middleware/gate that checks only for a cookie's *presence* (not its signature) is functionally equivalent to no auth at all once you can make the browser load whatever page exposes the secret — use a throwaway/garbage cookie value to force-load gated routes and their JS chunks for inspection.
- For CTF/lab platforms that spawn per-player instances from a shared static build, a secret recovered from one instance (or from a vendor's own official writeup) often transfers directly to a different live instance — but verify independently (download and grep the chunk yourself) rather than assuming it blindly.

## Pattern Candidates

- New pattern created: `knowledge/patterns/web/jwt-secret-in-frontend-bundle.md`
