# VULN#003 — Handoff / state

## Challenge
- battleCTF Qualifier, `VULN#003`, category "Vuln Research", id 28, value 82, max_attempts 3, attempts used 0.
- Description: "A DNS response inspection service parses whatever DNS reply you send it. You are given the exact source tree the target binary is built from."
- Target: `169.58.126.107:7028` (raw TCP).
- Attachment: `workspaces/vuln003/attachments/` = **pristine c-ares 1.16.1** source tree
  (verified byte-for-byte vs upstream; not modified by the author).

## Protocol (empirically mapped)
- Connect, send `[4-byte BE length][DNS message]`; exactly one message per connection.
- Service replies `status: <msg>\n` then closes.
- Statuses seen:
  - `no effect`  -> c-ares parsed the message successfully (ARES_SUCCESS/ENODATA etc.)
  - `not valid`  -> c-ares parse error (EBADRESP/EBADNAME/...)
  - `bad length` -> declared length < ~12 or > cap. Cap is between 1629 and 16029 bytes
                     (16029/32029/64029 all rejected).
  - `short read` -> declared length > bytes actually sent, then EOF
  - `rate limited, try again later`
- Rate limit: ~3-4 messages per 70-95 s. Probe first; `sleep 80` when limited; ~16 s between sends.

## Local reproduction (NEW — do not lose)
- Built the attachment's real c-ares 1.16.1 into a static lib + probe:
  - builder: `/tmp/opencode/v3_local_build.py`
  - config headers written by hand: `/tmp/opencode/v3lib/ares_config.h`,
    `/tmp/opencode/v3lib/ares_build.h` (copied from `include/ares_build.h.dist`)
  - probe binary: `/tmp/opencode/v3lib/probe` (reads a hex file, calls
    `ares_parse_a_reply`, prints status/naddrttls/h_name/addresses)
  - payload gen + hex: `/tmp/opencode/v3_gen_payloads.py`, `/tmp/opencode/v3payloads/*.h`
- NOTE: `/tmp/opencode` is wiped on date rollover; the builder + config are
  re-creatable from this note (see "Rebuild" below).

### Local results (ground truth)
For question `[4]good[5]ev\0il` + answer owner `[4]good[2]ev`:
- `ares_parse_a_reply` -> status=0, **h_name="good.ev" (strlen 7)** (NUL-truncated),
  addresses resolved (wrong-match via strcasecmp).
- Same for the *control* (clean question, owner=pointer) — h_name still "good.ev".
- AAAA query with only A answers -> status=0, naddrttls=0, h_name="good.ev".
- **Every variant returns `status=0`.** Nothing here changes the success/error
  outcome, which is why the remote always says `no effect`.

## Bug inventory (c-ares 1.16.1, all present)
1. **CVE-2021-3672** — embedded NUL in a hostname => C-string truncation.
   Confirmed locally (h_name truncated). Harness did NOT react to it (see tests).
2. **CVE-2020-8277** — `ares_parse_a_reply.c:200` / `ares_parse_aaaa_reply.c`
   set `*naddrttls = naddrs` (TOTAL), can exceed caller's `addrttls[]` buffer
   -> caller-side OOB read. Internal arrays are sized correctly (no write overflow).
3. No internal OOB found in any parser: every `ares_parse_*` checks
   `aptr + rr_len > abuf + alen`; `ares_expand_name`/`name_length` proxy-check
   all reads against `alen`. So c-ares never reads past the *message* buffer.

## Tests already sent (all `no effect` unless noted)
- valid A/AAAA/CNAME/PTR/TXT/MX/SOA/NAPTR — owner==question -> `no effect`
- null byte in question, owner==question -> `no effect`
- **wrong-match**: question `good.evil\0...`, A owner `good.ev` -> `no effect`
- CNAME target with NUL -> `no effect`
- 100 A records -> `no effect`
- A -> service self-IP 169.58.126.107 -> `no effect`
- header only (ANCOUNT=0) -> `no effect`
- malformed -> `not valid`; declared=0/huge -> `bad length`; declared>sent -> `short read`

## Unknowns / next ideas
- The harness clearly does NOT mirror c-ares's output (else the NUL truncation
  or wrong-match would have shown). It also is not a plain crash-detector on
  the parse path (nothing crashes). => It likely checks a SPECIFIC VALUE
  (hostname / IP / ID / qname) we haven't guessed, OR a specific CVE-2020-8277
  boundary.
- Untested: `ares_parse_aaaa_reply` many-record boundary; authority/additional
  sections; non-IN class; unusual flags/rcode/opcode; response IDs 0/1.

## Rebuild recipe (after /tmp wipe)
1. `mkdir -p /tmp/opencode/v3lib`; write `ares_config.h` (Linux macros; include
   `<limits.h>`; MUST define `HAVE_RECVFROM`, `HAVE_SEND`, and the
   `*_TYPE_ARG*` families — `setup_once.h` emits `Error Missing_definition_*`
   otherwise).
2. `cp attachments/include/ares_build.h.dist /tmp/opencode/v3lib/ares_build.h`
3. run `/tmp/opencode/v3_local_build.py` (compiles `src/lib/*.c` -> archive +
   probe `main.c` with `-D_DEFAULT_SOURCE -D_GNU_SOURCE`, `#include <netdb.h>`).
