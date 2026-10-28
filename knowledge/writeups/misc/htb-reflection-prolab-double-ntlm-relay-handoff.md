---
doc_kind: writeup
title: "HTB Pro Lab Reflection (EU Mini Pro Lab 1) - Double NTLM Relay via xp_dirtree (Unsolved, Handoff)"
category: misc
slug: htb-reflection-prolab-double-ntlm-relay-handoff
created: 2026-10-25
status: draft
tags:
  - active-directory
  - pro-lab
  - ntlm-relay
  - xp_dirtree
  - mssql
  - coercion
  - unsolved
  - handoff
source: "HTB Pro Lab - EU Mini Pro Lab 1"
target: "DC01 10.13.38.44 / MS01 10.13.38.45 / WS01 10.13.38.46 (reflection.vl)"
---
# HTB Pro Lab Reflection (EU Mini Pro Lab 1) - Double NTLM Relay via xp_dirtree (Unsolved, Handoff)

## Challenge Summary

- Source: HTB Pro Lab - EU Mini Pro Lab 1, session notes dated 20/10/2026
- Target: DC01 (10.13.38.44, SMB signing False, MSSQL 2019 SQLEXPRESS, WinRM), MS01 (10.13.38.45, same config, share `staging`), WS01 (10.13.38.46, RDP only, no WinRM) — domain `reflection.vl`
- Goal: 3 flags on a small AD lab; **not solved** — this note is a handoff/resume point, not a completed writeup

## Initial Signals

- Entry point: anonymous access to `\\MS01\staging`, containing `staging_db.conf` with `web_staging:Washroom510` credentials for `MS01\SQLEXPRESS`'s `staging` database.
- Visible hints: SMB signing disabled on all three hosts (a precondition for NTLM relay) and `xp_dirtree` enabled on both SQL instances — both strong signals the intended path involves coercion/relay between the two MSSQL instances rather than a direct SQLi/privesc path.
- First confirming probe: the `staging` database's `users` table contains local MS01 accounts (`dev01`/`dev02`, both `Initial123`, both landing as `Guest`) — low-value on their own, but confirmed read access to `staging` and that `xp_dirtree` works from this login.

## Exploit Chain (partial — validated but not completed)

1. Anonymous SMB read of `\\MS01\staging\staging_db.conf` → MSSQL credentials `web_staging:Washroom510`.
2. Authenticate to `MS01\SQLEXPRESS` with those credentials; confirm `xp_dirtree` is callable from this login.
3. **Double-direction NTLM relay, both directions confirmed working**:
   - Relay 1: coerce `REFLECTION\svc_web_staging` (MS01's SQL service account) via `xp_dirtree` pointed at an attacker-controlled SMB share, relay the captured NTLM session into `DC01\SQLEXPRESS` → **succeeds**, yielding `CONNECT SQL` + `VIEW ANY DATABASE` on DC01, but **not** `sysadmin` and no impersonation rights on `sa`; the `prod` database (owned by `web_prod`, `is_trustworthy_on = 0`) remains inaccessible to this relayed session.
   - Relay 2: coerce `REFLECTION\svc_web_prod` (DC01's SQL service account) the same way, relay into `MS01\SQLEXPRESS` → **succeeds**, but yields only bare `CONNECT SQL` with no useful server/database role.
4. Both relayed NTLMv2 hashes were captured but **not cracked** at handoff time.

## Key Evidence

- Both relay directions report `SUCCEED` in the session logs (`rq2.sh` / `rqdc.sh` output), confirming SMB signing is genuinely off and `xp_dirtree`-based coercion between the two SQL service accounts is a real, working primitive here — not a dead theory.
- `DC01`'s `prod` database exists, is owned by a different service account (`web_prod`) than the one coerced from MS01 (`svc_web_staging`), and is marked `is_trustworthy_on = 0` — explains why Relay 1's resulting session (as `svc_web_staging`) cannot reach it even with `VIEW ANY DATABASE`.
- `GetNPUsers`-style enumeration found only 3 Kerberos principals (`administrator`, `svc_web_prod`, `svc_web_staging`) with none AS-REP roastable — ruling out that avenue entirely for this lab.

## Dead Ends

- `OPENROWSET(BULK)` and `xp_regread` both refused on MS01's `staging` context — no file-read/registry pivot available from that session.
- No useful SQLAgent jobs/proxies found on MS01 (unlike the SQLAgent-proxy RCE pattern that worked in Ascension/Offshore — this lab's intended path is evidently different).
- LDAP relay failed (LDAP enforces signing); LDAPS handshake reset by Schannel — ruling out an LDAP-based relay target for this network.
- SMB/RPC/WinRM relay targets were tried and failed up to the point of handoff — MSSQL-to-MSSQL relay (the one that worked) may not be the only intended vector, or `prod` access requires a different relay source account not yet identified.

## Payloads And Commands

```text
# Anonymous share read for initial creds
\\MS01\staging\staging_db.conf  -> web_staging:Washroom510

# Double relay (conceptual, scripts at /tmp/opencode/reflection/):
#   rq2.sh   - double-relay (MS01->DC01 then DC01->MS01) with MSSQL queries
#   rqdc.sh / rq4.sh - relay restricted to DC01 only, avoids interleaved results
# Both use xp_dirtree against an attacker SMB share to coerce outbound auth,
# then ntlmrelayx-style relay of the captured NTLMv2 session into the other
# instance's MSSQL TDS port.
```

## Flag / Outcome

- 0/3 flags captured. State frozen at: both relay directions validated and working, but neither yields a path into the `prod` database or any further privilege.

## Reusable Lessons

- SMB signing disabled + `xp_dirtree` enabled on two or more MSSQL instances that trust each other's service accounts is a strong, concrete signal to test **double-direction** NTLM relay (not just a single relay toward a domain controller) — each instance can potentially be coerced into authenticating to the *other*.
- A relayed session landing only on `CONNECT SQL` with no `sysadmin`/impersonation is not necessarily a dead end — the next step is enumerating what that specific login *can* reach (database ownership, `IMPERSONATE` grants, `msdb` jobs/proxies) rather than abandoning the relay path.
- `is_trustworthy_on = 0` on a target database is a concrete reason a cross-database/cross-login access attempt fails even with `VIEW ANY DATABASE` — worth checking explicitly before assuming a permissions gap is the whole story.
- Recorded priorities for resuming this lab: (1) find a path into DC01's `prod` database — possibly via a different coercion source matching `web_prod`'s actual service account, (2) enumerate DC01's `msdb` (jobs/proxies) more thoroughly via a dedicated relay, (3) retry hash cracking on `svc_web_staging`/`svc_web_prod` with different wordlists/rules, (4) revisit `\\DC01\prod` once any domain credential is obtained.

## Pattern Candidates

- New pattern created: `knowledge/patterns/misc/double-ntlm-relay-xp-dirtree-mssql-coercion.md`
