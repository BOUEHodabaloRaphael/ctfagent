---
doc_kind: pattern
title: "JWT Signing Secret Hardcoded in Frontend Bundle (Client-Side Auth)"
category: web
slug: jwt-secret-in-frontend-bundle
created: 2026-10-25
status: active
tags:
  - jwt
  - client-side-auth
  - source-map
  - hardcoded-secret
  - hs256
  - privilege-escalation
chain_summary: "When the backend sets no session/cookie on login and a JWT only appears in localStorage shortly after, the token is being minted client-side; grep bundled JS chunks or source maps for the HS256 signing secret, then forge a token with an elevated role claim."
---
# JWT Signing Secret Hardcoded in Frontend Bundle (Client-Side Auth)

## Chain Summary

- One-line chain: When the backend sets no session/cookie on login and a JWT only appears in localStorage shortly after, the token is being minted client-side; grep bundled JS chunks or source maps for the HS256 signing secret, then forge a token with an elevated role claim.
- Typical target shape: a React/Next.js (or similar SPA) frontend talking to a thin backend API; login returns user data (id/username/role) but the response carries no `Set-Cookie`/session, yet a JWT (often named `authToken`) shows up in `localStorage` and/or a non-`HttpOnly` cookie shortly after.

## Preconditions

- Login/auth response sets no server-side session artifact at all.
- A JWT appears client-side after login without any visible network request that could have minted it server-side.
- The frontend is built with a bundler (webpack/Next.js/Vite) that either ships a readable source map, or inlines the signing logic directly into a JS chunk without minifying away string literals.
- Route-gating middleware (if any) checks only for the **presence** of the token/cookie, not its signature — common when the "real" authorization is deferred entirely to decoding the JWT's claims client- or server-side later.

## Cheap Probes

- Decode the JWT (any `jwt.io`-style tool) and check the `alg` header — `HS256` (symmetric) with a client-visible signing step is the target shape; `RS256`/`ES256` (asymmetric) would need the private key, which is far less likely to be shippable client-side.
- Grep the page's network-loaded JS chunks for `JWT_SECRET`, `signJWT`, `SignJWT`, `.sign(`, or similar — the signing call is frequently in a small, separately-chunked file (e.g. `lib/jwt.ts` compiled output) only loaded on routes that actually mint/verify tokens.
- If the signing-logic chunk isn't referenced from the public `/login`/`/register` page HTML, try loading a route that *requires* auth (`/dashboard`, `/admin`) with a throwaway/garbage token value first — if the gate only checks cookie presence, this forces the browser to load (and expose in dev tools) the chunk that actually needs the secret.
- Check for an accessible source map (`<chunk>.js.map`) via dev tools' Sources panel or by requesting the `.map` URL directly — source maps often reveal the original (unminified, commented) source file verbatim, including hardcoded secrets.

## Telltale Evidence

- No `Set-Cookie` header anywhere in the login flow, combined with a JWT appearing in `localStorage` moments later — the token has no server-side origin to investigate; it was built in the browser.
- A route gate that accepts a non-empty-but-garbage cookie value (returns 200 with the real page instead of a redirect to login) proves the gate checks presence only, which is also the mechanism used to force-load the page bundle that contains the secret.

## Escalation Order

1. Register/login to obtain a real user id (needed for a plausible forged payload).
2. Identify that the token is client-minted (no session cookie from login, token appears in localStorage).
3. Force-load the gated route/bundle chunk containing the signing logic if it isn't already loaded, using a garbage token to pass a presence-only gate.
4. Recover the signing secret from the bundle (direct string search) or its source map.
5. Forge a token with the same claim shape as a legitimate one, but with an elevated `role` (or equivalent privilege claim), signed with the recovered secret.
6. Send the forged token wherever the legitimate one is expected — typically both `Authorization: Bearer <token>` and as the `authToken` cookie, since different endpoints may check one or the other.
7. Enumerate reachable endpoints for one that returns elevated-privilege data even without a dedicated `/admin`-prefixed path — the "admin-only" data is often just a flag on an otherwise-shared endpoint (e.g. a ticket/record any authenticated user can technically query).

## Common Mistakes

- Only searching the static `/login`/`/register` page HTML for the signing-logic chunk — it may only be pulled in by a route-based code-split that requires first passing (or bypassing) the auth gate.
- Assuming a per-instance/per-player deployment randomizes the secret — many CTF/lab platforms spawn identical static builds per instance, so a secret recovered once (even from someone else's writeup) may transfer directly; still worth independently verifying by downloading and grepping the live target's own chunk rather than blindly trusting an external source.
- Forgetting that HTTPS with a self-signed certificate on the target may break browser-automation tooling (stuck on the "Privacy error" interstitial) — fall back to scripted HTTP calls (`curl -k`, `requests(verify=False)`) rather than fighting the browser.

## Payload Shapes

```bash
# Force-load a gated route's bundle with a garbage token to find the signing-logic chunk
curl -sk -b 'authToken=dummy' https://<target>/dashboard | grep -o '<script src="[^"]*"'
```

```python
import jwt  # PyJWT
forged = jwt.encode(
    {"userId": user_id, "username": username, "role": "admin", "iat": iat, "exp": exp},
    "<recovered_secret>",
    algorithm="HS256",
)
# send as Authorization: Bearer <forged> and/or Cookie: authToken=<forged>
```

## Related Writeups

- `knowledge/writeups/web/criticalops-client-side-jwt-secret.md`

## Skill Impact

- Related skill: `web-triage` (JWT branch)
- Rule to add or update: when login sets no server-side session artifact but a JWT appears client-side shortly after, immediately search bundled JS/source maps for a hardcoded HS256 secret instead of attempting server-side JWT attacks (alg-confusion, kid injection, etc.) that assume server-side signing.
