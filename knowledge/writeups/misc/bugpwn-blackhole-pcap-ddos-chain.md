---
doc_kind: writeup
title: "battleCTF Qualifier (bugpwn) — Operation BLACKHOLE 1-8 (pcap DDoS analysis)"
category: misc
slug: bugpwn-blackhole-pcap-ddos-chain
created: 2026-11-10
status: solved
tags:
  - pcap
  - tshark
  - http-flood
  - network-forensics
  - out-context
source: "ctf.bugpwn.com — battleCTF Qualifier 2026 (BUG|PWN & Cyber.industries), 2026-10-04 to 2026-11-04"
target: "CTF1.pcapng attachment, single HTTP-flood capture shared across all 8 sub-challenges"
---
# battleCTF Qualifier — Operation BLACKHOLE 1-8

## Challenge Summary

- Source: `ctf.bugpwn.com`, category "out context" (bonus, outside the 4 scored categories).
- 8 linked sub-challenges (ids 1-8, 5-30 pts each, raw-value flags — no `CTF{}` wrapper except
  the final one), all built on the **same attached pcap** (`CTF1.pcapng`), each asking one more
  fact about an HTTP-flood attack captured inside it.
- Goal: pure network-forensics reading comprehension of one capture, answered incrementally.

## Initial Signals

- `capinfos CTF1.pcapng` + `tshark -q -z conv,ip` / `-z endpoints,ip` / `-z io,phs` to get an
  overview before answering anything — confirmed a single attacker IP flooding a single victim.
- Victim server banner: `SimpleHTTP/0.6 Python/3.14.7` (Python's built-in `http.server`).
- Targeted URL pattern: `/?debug=N` with `N` incrementing per request (GET flood).

## Exploit Chain (one answer per sub-challenge, same pcap throughout)

1. **#1 — attacker IP**: `tshark -z conv,ip` → `192.168.43.128` (source of the flood).
2. **#2 — target IP**: same conversation table → `192.168.43.1` (victim web server).
3. **#3 — targeted TCP port**: `tshark -Y "ip.addr==192.168.43.1 && tcp"` → port `8000`.
4. **#4 — HTTP method used for flooding**: `tshark -Y http.request -T fields -e http.request.method`
   → all `GET` — flag = `GET`.
5. **#5 — most frequent User-Agent**: the attacker rotates/spoofs UA per request (dozens of
   distinct strings — browsers, Googlebot/bingbot, curl — classic flood-tool fingerprint from one
   source IP), but `tshark -Y http.request -T fields -e http.user_agent | sort | uniq -c | sort -rn`
   still shows one UA ahead of the noise: `curl/8.21.0` (52 occurrences) — flag =
   `curl/8.21.0`.
6. **#6 — attack duration in seconds**: first wrong guess was `79` (the HTTP-request-only span on
   port 8000); correct answer was **`83`**, the **full host-to-host TCP conversation duration**
   from `tshark -z conv,ip` (`192.168.43.128 <-> 192.168.43.1`, 2026-09-17 10:40:33.888Z →
   10:41:57.134Z ≈ 83.2s) — includes the final ACK/teardown beyond the last HTTP packet. Lesson:
   when a "duration" question is ambiguous between a tightly-scoped and a broader time window, the
   platform means the broader conversation-level span.
7. **#7 — total HTTP request count in the capture**: `tshark -r CTF1.pcapng -Y "http.request"` →
   `713` total — **not** just the 668 attacker-originated requests, the question counts every
   legitimate background HTTP request in the capture too.
8. **#8 — flag hidden in an HTTP header**: every attacker GET request carries a crafted `Referer`
   header: `tshark -r CTF1.pcapng -Y http -T fields -e http.request.line -e http.response.line |
   grep -iE "flag|ctf\{"` surfaces
   `Referer: http://ctf.local/CTF{UF0N3t_DD0S_4n4lys1s_2026}` directly.

## Key Evidence

```text
tshark -r CTF1.pcapng -q -z conv,ip
tshark -r CTF1.pcapng -q -z endpoints,ip
tshark -r CTF1.pcapng -q -z io,phs
tshark -r CTF1.pcapng -Y "http.request" -T fields -e http.request.method -e http.user_agent
tshark -r CTF1.pcapng -Y http -T fields -e http.request.line -e http.response.line \
  | grep -iE "flag|ctf\{"
```

## Dead Ends

- Scoping #6's "duration" to the HTTP-request-only time span (`79`) — wrong, one of only two
  incorrect submissions across all 8 sub-challenges (max_attempts was 1 on #3, so this miss on #6
  mattered: always cross-check cached pcap facts before submitting on single-attempt questions).

## Flag / Outcome

- #1 `192.168.43.128` · #2 `192.168.43.1` · #3 `8000` · #4 `GET` · #5 `curl/8.21.0` · #6 `83` ·
  #7 `713` · #8 `CTF{UF0N3t_DD0S_4n4lys1s_2026}`
- All 8/8 solved, 5-30 pts each.

## Reusable Lessons

- One pcap can back a whole chain of incremental questions — run the broad `tshark -z conv/io`
  overview commands **once** up front and cache the facts, instead of re-deriving them per
  sub-question.
- "Duration of the attack" on a flood pcap means the full TCP conversation span (through
  teardown), not the tighter window of just the attack-shaped packets.
- A flag embedded in a header (`Referer`, custom headers, etc.) is a cheap thing to grep for
  across the whole capture (`http.request.line`/`http.response.line`) before assuming it must be
  in the payload body.

## Related

- [`bruteshark-pcap-credential-extraction`](../../patterns/forensics/bruteshark-pcap-credential-extraction.md) —
  complementary tool for the credential-extraction angle on a pcap (not needed here, but the next
  "find the fact in a pcap fast" case).
