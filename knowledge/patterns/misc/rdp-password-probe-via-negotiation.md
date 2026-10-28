---
doc_kind: pattern
title: "RDP Password Validity Probe via Negotiation Behavior"
category: misc
slug: rdp-password-probe-via-negotiation
created: 2026-10-04
status: active
tags:
  - rdp
  - credential-validation
  - windows
  - recon
chain_summary: "Use rdesktop under Xvfb to cheaply distinguish valid vs invalid RDP passwords by whether the session log reaches process_pdu_logon, without opening a full interactive GUI session per credential tried."
---
# RDP Password Validity Probe via Negotiation Behavior

## Chain Summary

- One-line chain: Use rdesktop under Xvfb to cheaply distinguish valid vs invalid RDP passwords by whether the session log reaches process_pdu_logon, without opening a full interactive GUI session per credential tried.
- Typical target shape: a Windows RDP target where you have a candidate credential (from an in-game hint, a leaked password list, a guess) and want to validate it before investing in a full GUI session or risking lockout counters.

## Preconditions

- RDP (3389) reachable.
- `rdesktop` (or `xfreerdp`) and `Xvfb`/`xvfb-run` available locally; no GUI needed on the attacker side.
- Server may reject TLS/NLA (older/legacy RDP security config — common on purpose-built CTF boxes) — plain RDP security negotiation still works and is actually what makes this trick easy to read in the logs.

## Cheap Probes

- `xfreerdp ... +auth-only` — in principle designed for exactly this, but unreliable against servers that reject TLS/NLA (`SSL_NOT_ALLOWED_BY_SERVER`) and can give false "exit status" codes that don't actually distinguish good vs bad creds on such servers. Don't trust it blindly — verify against a *known-good* credential first.
- `netexec rdp <target> -u user -p pass` — useful but also assumes NLA; will report `Server refused our connection request! Reason: SSL_NOT_ALLOWED_BY_SERVER` for both good and bad creds on legacy servers, equally unreliable there.

## Telltale Evidence

- With `rdesktop` (which auto-retries with plain RDP security on TLS rejection) run under `xvfb-run -a`, the console log for a **correct** password reaches a line like `Protocol(warning): process_pdu_logon(), Unhandled login infotype 1` (this specific warning is actually good news — it means the logon PDU was received and processed).
- With a **wrong** password, the log stalls permanently right after `Retrying with plain RDP.` and never reaches the logon PDU stage — the process just hangs there until your timeout kills it.
- Always run a **known-good** credential through the exact same harness first as a positive control before trusting a "no" result for an unknown candidate — server-specific negotiation quirks can otherwise look identical to "wrong password" and mislead you.

## Escalation Order

1. Confirm a known-good credential (if you have one) reaches `process_pdu_logon` under this harness — establishes the positive signature for *this specific server*.
2. Run the candidate credential through the identical command.
3. `timeout <sameN> xvfb-run -a rdesktop -u 'USER' -p 'PASS' TARGET 2>&1` — compare whether the log reaches the logon-PDU line before the timeout kills it.
4. Treat "reaches it" as valid, "stalls after `Retrying with plain RDP.`" as invalid.
5. Only then spend the effort to open a full interactive GUI session (e.g. via `Xvfb` + `xdotool` + screenshots) for creds confirmed valid this way.

## Common Mistakes

- Trusting `xfreerdp +auth-only` or `netexec rdp` exit codes/messages at face value against a server that rejects TLS/NLA — both can report the *same* negotiation-level error for correct and incorrect credentials, giving a false "invalid" reading. Always cross-check with the `rdesktop` negotiation-log method, with a positive control.
- Forgetting the positive control: without first confirming a *known-good* credential produces the expected log line on this exact server/build, you can't safely interpret "no logon PDU line" as "wrong password" versus "this server just behaves differently."

## Payload Shapes

```bash
# Positive control (known-good creds) — establishes the signature to look for
timeout 20 xvfb-run -a rdesktop -u 'KnownGoodUser' -p 'KnownGoodPass' TARGET_IP 2>&1
# expect: "...Retrying with plain RDP." followed by
#         "Protocol(warning): process_pdu_logon(), Unhandled login infotype 1"

# Candidate credential under test
timeout 20 xvfb-run -a rdesktop -u 'candidate' -p 'guess' TARGET_IP 2>&1
# valid  -> same process_pdu_logon line appears
# invalid -> log stalls right after "Retrying with plain RDP." until timeout kills it
```

## Related Writeups

- `writeups/misc/htb-touch-kiosk-plugin-hijack.md`

## Skill Impact

- Related skill: none yet directly covers RDP credential validation; worth a line in a future generic Windows-recon reference.
- Rule to add or update: when validating an RDP credential guess cheaply, prefer the `rdesktop`-under-`Xvfb` negotiation-log diffing method over `xfreerdp +auth-only`/`netexec` on any server that rejects TLS/NLA — and always run a known-good positive control first.
