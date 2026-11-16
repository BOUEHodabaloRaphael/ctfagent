---
doc_kind: pattern
title: "World-Writable Root Cron Privesc (and /tmp nosuid bypass)"
category: web
slug: world-writable-cron-root-privesc
created: 2026-11-09
status: active
tags:
  - privesc
  - cron
  - persistence
  - nosuid
  - suid
chain_summary: "A root cron job pointing at an attacker-writable script is instant root; if dropping a SUID binary in /tmp silently fails, /tmp is likely mounted nosuid — write/exfiltrate via /opt or another non-nosuid path instead"
---
# World-Writable Root Cron Privesc (and /tmp nosuid bypass)

## Chain Summary

- One-line chain: A root cron job pointing at an attacker-writable script is instant root; if dropping a
  SUID binary in `/tmp` silently fails to actually run as root, `/tmp` is likely mounted `nosuid` — write
  or exfiltrate via `/opt` (or any path not under a `nosuid`/`noexec` mount) instead.
- Typical target shape: any low-privilege shell/RCE (web user, low-priv SSH user) on a box with a
  `root`-owned cron entry pointing at a script that is group/world-writable.

## Preconditions

- Any code-execution primitive as a non-root user (webshell, LFI RCE, SSH shell, etc.).
- A cron entry (`/etc/crontab`, `/etc/cron.d/*`, or a user crontab readable via `crontab -l`) scheduled as
  `root` and pointing at a script file.
- That script (or a directory in its path that would let you replace it) is writable by the current user.

## Cheap Probes

- `cat /etc/crontab` and `ls -la /etc/cron.d/` — always readable by any local user by default on Debian/
  Ubuntu.
- For every root-run script referenced, `ls -la <path>` to check write permissions (`-rwxrwxrwx` or
  group-writable with current user in that group).
- If no file-system write is found, also check `crontab -l -u <user>` is blocked (expected without
  privilege) but `/var/spool/cron/crontabs/` directory permissions are still worth a quick `ls -la`.

## Telltale Evidence

- `-rwxrwxrwx 1 root root ...` (or similar) on a script referenced by a root cron line — this alone is
  enough, no further confirmation needed before exploiting.
- A challenge prompt that frames the box around "suspicious activity" / "has an attacker established
  persistence" is a strong hint to check cron (and systemd timers, `/etc/rc.local`, init scripts) before
  looking for a kernel exploit or SUID misconfig.

## Escalation Order

1. Identify the writable root-cron script and read its current content (so it can be restored afterward).
2. **First attempt** (classic): overwrite it to copy a shell binary and `chmod 4755` it for a SUID root
   shell, e.g. `cp /bin/bash /tmp/rootbash; chmod 4755 /tmp/rootbash`. Wait for the next cron tick (cron
   granularity is usually 1 minute — budget up to 60s).
3. **Verify it actually worked** — don't just assume success because the cron presumably ran. Check
   `ls -la /tmp/rootbash` for the `s` bit and that the file exists; if it's missing or not SUID, run
   `mount | grep /tmp` (or `findmnt /tmp`) to check for `nosuid`. Many modern distros mount `/tmp` as a
   `nosuid,nodev` tmpfs by default (hardening), which lets `chmod 4755` "succeed" with no error while the
   SUID bit is simply never honored at exec time.
4. **If `/tmp` is `nosuid`**, don't fight it — either (a) drop the SUID binary somewhere else writable and
   not `nosuid` (check `mount` for the root filesystem's options; a plain ext4 `/` with `rw,relatime` has no
   such restriction, so a root-owned-but-world-writable directory like `/opt` works if the directory itself
   allows new file creation, or more simply), or (b) skip the SUID-shell approach entirely and have the
   cron script itself perform the privileged action directly and write the result somewhere you can read —
   e.g. `cat /root/root.txt > /opt/out.txt; chmod 666 /opt/out.txt` — since the script already runs as root,
   there's no need to escalate a shell at all if the goal is just reading a specific file.
5. Read the result through whatever access you already have (LFI, webshell, SSH).
6. **Clean up**: restore the cron script to its original content, delete any dropped binaries/output files.

## Common Mistakes

- Assuming `chmod 4755` success == SUID actually works — always test the resulting binary's effective UID,
  don't just trust the exit code.
- Not checking `mount` for `nosuid` before spending a full minute waiting on a cron tick that was doomed to
  fail.
- Forgetting the target directory for the SUID binary must itself allow creating new files as the cron's
  user (root creating it is always fine) — the constraint is on where root writes it, not where the
  low-priv user could have written directly.
- Not restoring the cron script afterward, leaving a backdoor/altered state on the box (bad practice for an
  authorized assessment — always revert what you changed once the proof is captured).

## Payload Shapes

```bash
# classic SUID-shell approach (works only if the destination path is not nosuid)
echo 'cp /bin/bash /tmp/rootbash; chmod 4755 /tmp/rootbash' > /path/to/root_cron_script.sh

# nosuid-safe alternative: have root read the flag directly, no shell escalation needed
printf '#!/bin/bash\ncat /root/root.txt > /opt/out.txt 2>&1; chmod 666 /opt/out.txt\n' > /path/to/root_cron_script.sh
# wait for next cron tick, then read /opt/out.txt through your existing access
```

## Related Writeups

- [[thundercipher-tcvapt-phantom]] — `/opt/backup.sh` was `-rwxrwxrwx root:root`, run every minute by
  root; `/tmp` turned out `nosuid`, pivoted to writing the flag straight to `/opt/out.txt`.

## Skill Impact

- Related skill: `pwn-triage` / `ctf-pwn` privesc checklist, and `web-triage` for web-shell-to-root
  escalation steps.
- Rule to add or update: add "check `/etc/crontab` + `/etc/cron.d/` for writable root scripts" as a
  standard early privesc check (alongside `sudo -l` and SUID enumeration), and add "verify SUID actually
  took effect / check for `nosuid` mounts" as a mandatory follow-up whenever a SUID-drop technique is used
  anywhere (not just via cron — also relevant to writable `/etc/passwd`, LD_PRELOAD tricks dropped in /tmp,
  etc.).
