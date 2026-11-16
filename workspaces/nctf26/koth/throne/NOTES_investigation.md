# The Throne — invisibility investigation (2026-11-06, ~22:30-22:50)

Mission: determine why `throne_hold.py` gets consistent `200 {"ok": true}` from
the hill backend (`/throne`) but Th3N00bs never appears in the platform's
"FIL DU TRÔNE" / top5 for **The Throne** specifically, and fix it if it's a
logic bug rather than pure contention.

Background process checked first: `pgrep -af throne_hold.py` → PID 165224,
still running, log `throne_hold_1794020427.log` at claim #1137+ with
continuous `status=200 {"ok": true, "king": "b792a5aa…"}`. Left untouched.

## Test 1 — field format (`team` = token vs literal team name)

Script: `/tmp/.../scratchpad/throne_probe.py` (one-shot probes, token
`b792a5aa3c4babf5`, team name `Th3N00bs`).

| variant | team field | HMAC basis | result |
|---|---|---|---|
| 1a (baseline) | token | token | `200 {"ok": true, "king": "b792a5aa…"}` |
| 1b | literal name | literal name | `200 {"ok": true, "king": "Th3N00bs…"}` |
| 1c | literal name | token | `401 {"error": "bad signature"}` |
| 1d | token | literal name | `401 {"error": "bad signature"}` |

So `/throne` is a dumb opaque-string HMAC check: whatever string you put in
`team`, the signature must be `HMAC_SHA1(hill_key, team+'|'+ts)` over that
*exact same string*, and the backend will happily echo it back as `king`.
It does **not** validate that `team` is a real registered token or name.

**This looked at first like it could support hypothesis 1** (maybe the
platform scorer wants the literal name, not the secret token). It doesn't,
for two independent reasons found below:

1. The platform UI explicitly labels the hex value
   `"VOTRE JETON D'ÉQUIPE (À PLANTER SUR LA COLLINE)"` — *"your team
   TOKEN, to plant on the hill"* — right next to the Throne connection
   info, token `b792a5aa3c4babf5`. This is unambiguous design intent: the
   token is the thing you're supposed to plant.
2. **Direct proof the token format already scores correctly**: the
   platform's `/plugins/koth/` page shows **Th3N00bs already has 2 KOTH
   points on a *different* hill, The Armory** (`#5 Th3N00bs 2`), from an
   earlier one-off exploit (`workspaces/nctf26/koth/armory_phase1.log`)
   that used the same hex-token format. If token-format claims were
   invisible to the official scorer, we could not have scored there either.

**Conclusion: hypothesis 1 (field-format bug) is REFUTED.** `throne_hold.py`
already uses the correct identifier. Switching to the literal team name
would at best do nothing and at worst desync us from the scorer's real
token→team roster lookup. **No change made to `throne_hold.py`.**

## Test 2 — does `/status` ever show our prefix right after an `ok:true`?

Ran immediate `claim()` → `GET /status` with gaps as small as 0.21s, 8
times total across two scripts (`throne_probe.py` T2 block +
`throne_probe2.py` rapid loop). Every single `/throne` call returned
`200 {"ok": true, "king": "b792a5aa…"}` (it always echoes back our own
token — this field is **not** a read of global state, just an ack of what
we sent). The immediately-following `/status` call **never once** showed
our prefix (`b792a5aa`) — saw `899158b8`, `17c044dd`, `ef20d780`,
`8f70fd11`, `028809ce`, etc., 8/8 times.

Example:
```
claim  -> 200 {"ok": true, "king": "b792a5aa…"}          (t=0)
status -> 200 {"service":"throne","king":"899158b8…","claims":36188855}  (t=+0.234s)
```

This is consistent with the volume numbers below, not with a separate/fake
king state: between our claim and the status read, thousands of *other*
teams' claims land first.

## Test 3 — real round-trip latency & claim-volume math

Measured dozens of round trips across both probe scripts: **~0.21s–2.4s
per request**, median ~0.33s, to `13.37.197.230:28490` (AWS eu-west-3).
`throne_hold.py`'s 0.6s sleep + ~0.3-1.4s real RTT means our actual
sequential rate is **~0.7–1.3 claims/s**, not the nominal 1.6/s — the network
RTT itself eats most of the budget.

Far more important finding (not in the original hypothesis list but decisive):
the `/status` `claims` counter jumped **+823 in 0.75s**, **+3435 in 0.22s**,
**+4939 in 2.3s** etc. across consecutive samples — i.e. **roughly
1,000–3,000 claims/second system-wide**, climbing from ~35.2M (22:17) to
~36.5M (22:35) over ~18 minutes, a sustained average of ~1,200/s. Our own
throne_hold.py contributes ~1/s to that. **Our share of total claim volume
on this hill is on the order of 0.05–0.1%.**

## Test 4 — clock-skew boundary (`skew_seconds=45`)

Swept `ts` offset from local clock: `+0,+10,+30,+44` → `200 ok`;
`+46,+50,+90` → `400 "stale claim (ts outside skew window)"`.
`-10,-30` → `200 ok`; `-44,-46,-50,-90` → `400 stale`.

Boundary sits at offset ≈ ±45s as documented, with a small (~2s) asymmetry
between the positive and negative edges (+44 passes, -44 already fails) —
this is just a few seconds of real clock drift between our box and the
remote host, not a bug. **Irrelevant to the actual problem**: our
production script uses `ts=int(time.time())` (offset 0), comfortably
inside the window on every single one of its 1100+ logged claims
(`status=200 ok:true` throughout the whole log). Clock skew is not causing
any of our claims to be silently rejected.

## Test 5 (bonus) — does an invalid signature still bump the counter?

Sent one claim with an all-zero bogus signature → `401 {"error": "bad
signature"}` as expected, with no distinguishable effect isolable from
ambient traffic (counter still climbed ~930 in that window, same order as
background noise). Inconclusive either way and not decisive for the main
question, so not pursued further.

## Overall conclusion: (b), not (a) — confirmed by direct, independent evidence

- The `RETOURNEMENTS` (official flip counter) for The Throne was **483 →
  484 over ~2-3 minutes** of wall time between two page reads — i.e. the
  platform's real scoring ticks land roughly every 30–80s (matches the FIL
  DU TRÔNE event spacing: 15s, 45s, 31s, 30s, 30s, 31s, 30s gaps).
- The hill backend's raw `claims` counter is **not** the same thing as a
  scoring tick — it is incremented on every successful HMAC-valid POST,
  system-wide, at a rate of ~1,000-3,000/s, dwarfing both our own ~1/s and
  the actual tick cadence by 4-5 orders of magnitude.
- At any instant a scoring tick samples the real "current king", our
  chance of being that team is ≈ (our claim rate) / (system-wide claim
  rate) ≈ 1/1500 ≈ 0.07%. Over the ~480 ticks so far, expected wins ≈ 0.3
  — statistically consistent with the observed **zero** appearances in the
  Throne fil/top5.
- The mechanism is proven to work correctly when contention is survivable:
  **Th3N00bs already holds 2 KOTH points on The Armory** using the exact
  same token-based claim format, from a prior lower-volume opportunistic
  claim. The Throne is simply the single most hyper-contested of the four
  hills (compare `RETOURNEMENTS`: Armory 313, Reseau Fortune 214, Citadel
  8, **Throne** climbing from 483→484+ off a claims counter in the tens of
  millions).

**No logic bug found on our side.** The forged-HMAC exploit, the token
format, the timestamp handling, and the claim cadence are all correct and
already proven to score (on Armory). The Throne specifically is not
winnable at our current ~1/s sequential rate against an estimated
1,000-3,000/s of aggregate competing traffic; this is a genuine volume
problem, not a bug to fix.

## Outcome / script status

`throne_hold.py` is **left unchanged** (token format confirmed correct;
0.6s interval kept, no parallelization, consistent with the no-flood
constraint). It remains running in the background as a zero-cost
opportunistic claimer — same honest conclusion as the earlier 22:15 update
in `EXPLOIT.md`, now with the specific hypotheses from this investigation
tested and ruled out individually rather than assumed.

No attempt was made to raise throughput beyond the existing ~1/s given the
explicit instruction not to approach flood territory and the prior history
of the agent sandbox's own anti-flood guard blocking a faster version.
