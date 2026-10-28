# VULN#003 (battleCTF 2026 Qualifier, challenge id 28) — working notes

Target: `169.58.126.107:7028` — "A DNS response inspection service parses whatever DNS reply you send it."
Attachment: `c-ares-src.tar.gz` = **c-ares 1.16.1**, byte-for-byte upstream (verified).
Points: 56 (decaying). solves: 23. max_attempts 3, attempts 0.

## Protocol (fully mapped)
- Connect TCP, send **4-byte BE length** + DNS message, then shutdown(WR).
- Reply = exactly `status: <msg>\n` then close (one message per connection).
- Statuses seen: `no effect` (parse OK), `not valid` (parse error),
  `bad length` (framing), `short read` (framing), `rate limited, try again later`.
- `short read` ⇒ the harness reads exactly the declared length ⇒ no length-mismatch vector.
- Message length cap: between ~7197 and ~14365 bytes (not yet pinned).
- Rate limit: ~5 messages per ~5 min window; 95 s retry sleep is not always enough.

## The bug (confirmed by upstream diff, CVE-2020-8277)
`src/lib/ares_parse_a_reply.c:200` (1.16.1):
```c
  if (naddrttls) { *naddrttls = naddrs; }   /* <-- total count, may exceed caller's buffer */
```
upstream 1.17.x fix:
```c
  *naddrttls = (naddrs > *naddrttls) ? *naddrttls : naddrs;
```
⇒ if the reply carries more A (or AAAA) records than the caller's
`addrttls[]` array, `*naddrttls` comes back LARGER than the array ⇒ the
caller's loop `for (i=0;i<naddrttls;i++) addrttls[i]` reads out of bounds.
Same bug in `ares_parse_aaaa_reply.c`.
The write itself is bounded (`if (naddrttls && i < *naddrttls)` at l.168) ⇒ no
OOB write inside c-ares, only the classic caller-side over-read.

⇒ **Trigger = send a reply with MORE A/AAAA records than the harness's buffer.**
We must find that buffer size N: any n > N should flip the status.

## Other candidate bug checked and (mostly) ruled out
`ares_expand_name.c` 1.16.1 writes label bytes raw (embedded NUL ⇒ C-string
truncation). Upstream 1.17.2 (commit c9b6c605b5 "Validate hostnames in DNS
responses and discard from malicious servers (#406)", CVE-2021-3672, XSS-class)
escapes non-printables as `\DDD` and validates the **CNAME target** as a
hostname ([A-Za-z0-9-.]). Locally confirmed the classic spoof:
CNAME target `trusted.example.com\0.attacker.example.com` is truncated to
`trusted.example.com` and the A record for it IS accepted by c-ares.
**Remotely this produced only `no effect`** ⇒ the harness does not detect the
name-spoofing. NUL in question / NUL in owner / invalid char in CNAME target:
all `no effect`. ⇒ hypothesis (6) "harness validates names" is dead.

## Local tooling (rebuild after /tmp wipe)
- `/tmp/opencode/v3_local_build.py` → builds attachment c-ares into `libcares_att.a` + `probe`
  (needs `-D_DEFAULT_SOURCE -D_GNU_SOURCE`, `<netdb.h>`, `<limits.h>` in ares_config.h).
- `/tmp/opencode/v3_local_check.py` → writes candidate replies to /tmp/opencode/v3payloads/*.h
  and runs the probe (status / naddrttls / h_name / addrs).
- `/tmp/opencode/v3_batch.py` → remote runner, rate-limit aware (retries the same
  test after 95 s), log at `/tmp/opencode/v3_results.txt`.
- upstream 1.17.2 tree at `/tmp/opencode/c-ares-cares-1_17_2/` for diffs.

## Remote results so far
| test | result |
|---|---|
| ctrl_chain (normal CNAME→A chain) | no effect |
| cve_nul_cname (canonical CVE-2021-3672) | no effect |
| cve_nul_owner | no effect |
| cve_cname_badchar (`<` in CNAME target) | no effect |
| cve_nul_cname_aaaa | no effect |
| A n=2,4,8,16 (prev session) | no effect |
| AAAA n=4..64 (prev session) | no effect |
| A n≥32, AAAA n≥128 (prev session) | INCONCLUSIVE (rate limited) |

## Plan
1. Sweep n (A records) 17 → 33 → 65 → 129 → 257 → 490 (7869 B) until the status flips.
2. Same for AAAA (max ~280 records within 7869 B; 28 B/record).
3. If it flips: capture the response, look for the flag string, submit via
   `src/tools/platform/ctf_platform_client.py submit --id 28`.
4. Fallback if no flip: other hypotheses (secret name/IP match, crash detection).
