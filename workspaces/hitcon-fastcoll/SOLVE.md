# FastColl (HITCON CTF 2026, Crypto) — working notes

## Challenge mechanics (confirmed from source)

- `fastcoll/runner.py` is the full judge. Guest WASM exports `xx_hash() -> ()`
  and `memory`; imports **only** `env.xx_hash(ptr:i32, len:i32, out_ptr:i32) -> i32`.
- Each import call: `call_seed = (base_seed + state.calls) & MASK64`, THEN
  `state.calls += 1` — the seed is consumed even for invalid/rejected calls.
- Validation: `256 <= len <= 1024`, `ptr`/`out_ptr` must fit in guest memory
  (`out_ptr` needs 16 free bytes). Invalid calls return `-1` and burn a seed
  but never call the digest function or touch `state.seen`.
- Valid calls: `digest = xxhash.xxh3_128_digest(message, seed=call_seed)`,
  written to `out_ptr` (16 bytes, little endian halves, same layout as
  python `xxhash`). Host also computes `sha256(message)` as a content
  fingerprint and keeps a global dict `digest -> fingerprint` (`state.seen`)
  across **all** calls in the run (not just adjacent ones).
- **Win condition**: any two valid calls (anywhere in the run, any order,
  any distance apart) whose digests are byte-equal AND whose fingerprints
  (i.e. message bytes) differ. First such event sets `fuel=0` so execution
  traps right after; host reports `status: won` and only then reveals the
  flag over HTTP.
- Budget: up to 1,000,000 valid+invalid calls, fuel ~1e14 (effectively not
  binding for anything but a real brute-force), 900s wall clock, 64 MiB
  guest memory, 1 MiB wasm module.
- We get **no mid-run feedback from the HTTP side** — one upload = one
  opaque subprocess run = one JSON result at the end. All adaptivity has to
  happen *inside* the wasm module during that single run (it can read back
  the 16-byte digest the host just wrote into guest memory before making
  its next call, so in principle it's a fully adaptive oracle — but there is
  no way to exfiltrate information to us mid-run to do offline computation
  such as SAT solving).
- No bugs found in `runner.py`/`app.py` validation logic (bounds checks are
  correct, no TOCTOU, no leaked seed/secret in any response, CSP/headers are
  fine, flag only read after `won`). The task is a genuine cryptographic
  attack on XXH3-128 at the judge's forced length range, not an
  implementation bug in the harness.

## Key structural fact (the real lever, not yet turned into a working exploit)

For `xxhash.xxh3_128_digest(msg, seed)` with `seed != 0`, XXH3 does **not**
use the hidden seed as an opaque secret for 240+ byte inputs directly — it
first derives a 192-byte "custom secret" from the public constant table
`kSecret` via (standard, documented, public xxHash internals):

```
for each 16-byte lane i of kSecret (12 lanes total):
    customSecret[16*i : 16*i+8]  = kSecret[16*i : 16*i+8]  + seed   (mod 2^64)
    customSecret[16*i+8:16*i+16] = kSecret[16*i+8:16*i+16] - seed   (mod 2^64)
```

This is **affine in `seed`**. Consequently, for two calls at seeds `s` and
`s+d` (`d` = difference in call index, which *we* fully control since we
choose which call gets which message and seeds strictly increment by 1 per
call, valid or invalid), the difference between their two derived secrets
is a **fixed, publicly known, seed-independent** function of `d` alone
(+`d` on every "low" word of a lane, `-d` on every "high" word) — even
though the absolute secret value is unknown (depends on the unknown
`base_seed`). This is structurally the same lever behind
`github.com/Cyan4973/xxHash#1127` (a fixed message pair colliding across a
uniformly random *single* seed with far-above-ideal probability, confirmed
by the maintainer, **but confirmed not to extend past 240-byte inputs**
because that trick lives entirely in `XXH3_mix16B`, which is only used in
the 17–240-byte path). Our forced range is 256–1024 bytes, i.e. strictly
the **long-input / accumulator path** (`XXH3_accumulate_512` +
`XXH3_mergeAccs`), a different, more complex mixing structure that #1127
explicitly does not cover (verified: issue body states 0 collisions in 2^28
trials at 241 bytes for their pair; issue comments confirm no follow-on
work for the long path).

For `len <= 1024` with the *default* secret size (192 bytes,
`nbStripesPerBlock = 16`, block = 1024 bytes), the whole message fits in a
single block: no intermediate `scrambleAcc` ever runs, only
`XXH3_INIT_ACC` + one pass of `accumulate_512` per 64-byte stripe (using
sequential 8-byte-aligned secret windows) + one "last stripe" pass that
reuses the trailing 64 bytes of input against a secret window starting at
the **non-8-aligned** byte offset `192 - 64 - 7 = 121` (deliberate
misalignment per upstream source comments), + a final `mergeAccs` (4×
`mul128_fold64` over secret windows at offsets 11 and 117) to produce each
64-bit half, each through `XXH3_avalanche`.

This gives real structure to attack (acc[] is additive across stripes;
mergeAccs is only 4 fold terms), but turning it into either (a) a
deterministic construction, or (b) an empirically-measurable
elevated-probability pair/triple `(m1, m2, d)` has **not succeeded yet**
(see below). This is genuinely open cryptanalysis, not a quick lookup.

## What's been tried and ruled out

1. Naive adaptation of the #1127 `w1 = ~w0` / full-complement trick to the
   long path at various byte offsets (0/8/16/.../248), length 256 and 512,
   **independent random seed per trial** (not shifted): 0 collisions over
   ~1.5M total trials (`empirical_search.py`, pre-existing).
2. Same family of constructions but with the seed **shifted by a known
   `d`** between the two messages (`d` in {1,2,4,8,16,2^16,2^32}) instead of
   independent random seeds — this is the mechanically correct model of our
   actual game (two oracle calls at seeds `s` and `s+d` for unknown `s`):
   all-zero message with one 8-byte word set to `0xFF…FF`; all-zero with a
   complementary *pair* of adjacent lanes (`i`, `i^1`) set to `0xFF…FF`;
   single random-lane `XOR 0xFF` flips; full `w1=~w0` + both-words-complement
   pairs at various offsets including the non-aligned last-stripe secret
   offset (121) and the `mergeAccs` secret offsets (11, 117 ⇒ message byte
   offsets tried include 0/64/120/128/192). **0/60000–100000 hits on every
   single construction** (`shift_search.py`). Naive hand-picked patterns do
   not transfer to the long path at all, for any tested `d`.
3. Randomized local search / hill-climbing (`hillclimb.py`): random 256-byte
   base message, random XOR mask (1/2/4/8/16 random bytes set to a random
   non-zero value) applied to produce `m2`, screened against `d=1` with
   4000 trials per candidate, keep-best, iterate for a time budget. Purpose:
   let the computer find any elevated-probability structure instead of
   hand-deriving exact byte/word alignment against the mergeAccs/last-stripe
   secret offsets. **Result: 39,583 random candidates evaluated in 150s;
   best-ever score across all of them was 0/4000 hits.** This rules out any
   construction in this (fairly broad, but still local/random) search space
   with a per-attempt rate above roughly `1/4000 ≈ 2.5e-4`; it does **not**
   rule out a subtler, lower-but-still-useful rate (e.g. ~2^-20, which would
   still be worth 1-5 expected hits swept across ~5x10^5 of our 1,000,000
   calls) — 4000 trials/candidate is too coarse to detect that. Detecting
   it reliably needs either far more trials per candidate (shrinking how
   many candidates fit in a given time budget) or byte-exact targeting of
   the real secret-window offsets (121 for the last stripe, 11/117 for
   `mergeAccs`) derived from the public `kSecret` constant, instead of
   random masks.
4. Confirmed via the GitHub issue thread itself (fetched `issues/1127` body
   + all 6 comments) that **no one in that thread ever extended the result
   past 240 bytes** — maintainer and reporter both explicitly scope the
   finding to the mix16B-based mid-size path. Latest-and-strongest number in
   the thread is 2^-10.47 for a 32-byte pair under the *default secret* with
   `XXH3_64bits_withSeed` (not applicable to us: wrong length range, and
   we need the 128-bit digest to match, which the thread also treats
   separately — 128-bit needs both `w1=~w0` conditions and both halves to
   agree, strictly within the same ≤240-byte path).

## Promising but unfinished angle (if resuming)

The adaptive-oracle angle: because the wasm guest can read back each
16-byte digest the host just wrote (full data, not just the win/lose
signal — the host's own `seen`/win check is a bonus free detector, we don't
need to replicate it), the guest could in principle run a far more
sophisticated in-wasm strategy than any fixed pair:

- It would need to actually implement XXH3-128 (or at least the few
  arithmetic relations that matter) *inside* wasm to do anything smarter
  than blind pattern-matching, since there is no way to exfiltrate
  intermediate digests to us for offline solving (one upload = one opaque
  subprocess run, no mid-run HTTP visibility).
- A full seed-recovery (e.g. treating `base_seed` as a free 64-bit unknown
  and solving via bit-vector/SAT reasoning against one observed digest for
  a known all-zero message, using the public `kSecret` table) is
  theoretically determined (128 bits of output, 64 bits of unknown) but
  would need to be either (a) solved offline with Z3 *before* upload in a
  way that doesn't actually depend on knowing the real seed (impossible —
  the seed is fresh per upload), or (b) implemented as a solver inside the
  wasm module itself, which is a large undertaking (bit-blasted SAT solving
  in hand-written WAT/compiled wasm) and not attempted yet.
- Brute-forcing `base_seed` (64 bits) by recomputing XXH3 in-wasm for each
  candidate is not feasible: fuel budget (~1e14) supports roughly 1e11–1e12
  hash evaluations at best, nowhere near 2^64.
- A pure random birthday search over the full 1,000,000-call budget is also
  not feasible on its own: 1e6 draws against a 128-bit output space is
  nowhere near the ~2^64 birthday bound; it only becomes useful once a
  construction with meaningfully elevated per-attempt probability
  (something like ≥ 2^-20, so that ~1e6 independent-ish attempts give a
  non-negligible expected hit count) is found — which is exactly what steps
  2–3 above were searching for, without success so far.

## Status

No collision found yet. No implementation bug found in the harness. The
structural lever (secret is affine in seed, so the delta between any two
chosen call-seeds is public/known even though the seeds themselves are
not) is real and specific to this challenge's `>240`-byte forced range, but
turning it into a working construction needs either deeper hand-derivation
of the exact `mergeAccs`/last-stripe secret byte offsets (see "misaligned
121 offset" above) or a longer, more systematic empirical/optimization
search than was possible in the time spent so far. Recommend either (a)
continuing the hill-climb search longer / smarter (larger mutation space,
simulated annealing, or targeted mutations at the exact secret-window
byte offsets derived from the public `kSecret` table and the known stripe
layout for len=256), or (b) deprioritizing this challenge if no further
budget is available — this is genuine open cryptanalysis, not a quick
lookup, despite 57 teams having solved it.
