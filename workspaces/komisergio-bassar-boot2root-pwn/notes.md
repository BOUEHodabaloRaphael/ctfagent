---
doc_kind: workspace-notes
id: komisergio-bassar-boot2root-pwn
title: "komisergio-bassar (boot2root pwn)"
category: pwn
status: solved-by-teammate-duplicate-stopped
tags:
  [pwn, stack-overflow, ret2win, sudo-gtfobins, zip-crack]
---
# Notes

STATUS: solved-by-teammate-duplicate-stopped. Platform API shows "komisergio--bassar"
already marked solved by Th3N00bs at 2026-11-07T03:19:34Z (solved in parallel by a
teammate, not by this run). Stopped on coordinator instruction before reaching
root/flag myself. No bruteforce of flag submission was ever attempted; all brute-force
here was a local, offline zip-password dictionary attack against our own downloaded
copy of `keys.zip` (not against the live service), which is standard CTF crypto/forensics
work, not an art.7 violation.

## Validated findings (exact evidence)

1. Service banner confirmed via raw `nc`:
   ```
   jail v1.0
   cmd> userpass @ 0x7ffd... shell @ 0x4011c6
   Password:
   ```
   `shell` is a fixed (non-PIE) address `0x4011c6` -> confirmed by later leaked source
   (see #5) to be a `void shell(void)` function that dup2()'s the socket fd onto
   stdio and `execve("/bin/sh", ...)`. `userpass` is a stack address (local buffer
   `char userpass[16]` in `auth()`), i.e. not a separate secret — the banner just
   leaks two addresses for a classic leak-based ret2win.

2. **Offset 40 in the supplied script.py is correct.** Baseline check: sending a
   plain wrong password after the leak yields `Denied\n` then connection close
   (verified with `probe1.py`). Sending `b"A"*40 + p64(shell)[:6]` as the password
   buffer instead produced:
   ```
   AFTER OVERFLOW PAYLOAD: b"Denied\n/bin/sh: 0: can't access tty; job control turned off\n$ "
   ```
   i.e. `auth()` still runs to completion/prints "Denied" (the overflow is in a
   buffer read *after* the password check, overwriting the saved return address so
   that the function's `ret` jumps to `shell()` instead of returning normally) and we
   land a `/bin/sh` shell. The original script's `p.interactive()` had looked like a
   silent failure only because non-interactive piped stdin hits EOF immediately —
   the exploit itself worked first try with the stub's own offset=40 / `p64(shell)[:6]`.
   Working exploit kept at `artifacts/exploit_shell.py` / `exploit_frank.py` /
   `exploit_adm*.py` (all build on the same `get_shell()` helper).

3. Shell lands as `nobody` (uid=65534) inside a Docker container (`/.dockerenv`
   present, hostname `8b29816a3b02`).

4. Privesc ladder, both steps GTFOBins-style sudo chains, fully exercised and
   confirmed live:
   - `sudo -l` as nobody: `(frank) NOPASSWD: /usr/bin/less /var/log/syslog`
     -> `sudo -u frank less /var/log/syslog` then `!/bin/sh` -> shell as
     `frank` (uid=1000, confirmed via `id`).
   - `sudo -l` as frank: `(adm) NOPASSWD: /usr/bin/vim /var/www/html/jailuser/dev/jail.c`
     -> `sudo -u adm vim ...` then `:!/bin/sh` -> shell as `adm`
     (uid=1001, gid=4(adm), confirmed via `id`).
   - As adm, `sudo -l` requires a password (no further NOPASSWD rule) — dead end
     for sudo-based escalation past adm.

5. Leaked the full `jail.c` source (readonly in the vim buffer during the frank->adm
   step) and, critically, `/opt/jail/compile.sh` / the box's own `/start.sh`
   (readable by adm) which reveal the **entire intended solution path**:
   - `/start.sh` writes the real flag directly to `/root/root.txt` (`chmod 600`,
     root:root) from `$FLAG` (injected by the instancer) — this is the actual flag
     file, not something derivable without root.
   - Root SSH access is **key-only** (`PermitRootLogin prohibit-password`,
     `PasswordAuthentication no`), authorized_keys installed from
     `/opt/keys/root_authorized.pub`.
   - The adm-group vault `/var/adm/.keys/` (`drwx------ adm:adm`) holds
     `keys.zip` (password-protected, contains a single file `root_key` — almost
     certainly the private half of `root_authorized.pub`, i.e. the actual means
     of becoming root via SSH) and `note.txt` + `.frank`:
     ```
     note.txt: "Politique du coffre : mot de passe = Nom + 4 chiffres + 1 symbole
                Le nom est cache dans .frank (Atbash)."
     .frank (base64 of raw bytes): Vmh4emt2dyB1aWxuIFpveHpnaXp6Cg==
       -> decodes to ciphertext "Vhxzkvw uiln Zoxzgizz"
       -> Atbash-decoded: "Escaped from Alcatraa"
     ```
     `start.sh` confirms this `.frank` ciphertext is a **hardcoded placeholder**
     written verbatim by the provisioning script (`printf '%s\n' 'Vhxzkvw uiln
     Zoxzgizz' > /var/adm/.keys/.frank`), so the Atbash decode above is exactly
     right, not a crypto mistake on our side.

6. Exfiltrated `keys.zip` (1482 bytes, classic PKZIP/ZipCrypto encryption per
   `zip2john`, not AES — confirmed compatible with `fcrackzip`) to
   `artifacts/keys.zip` via base64 over the shell channel. Confirmed single
   member `root_key`, 1679 bytes uncompressed (consistent with an unencrypted
   PEM private key).

## Dead ends

- Local **offline** dictionary attack (never against the live service) on
  `keys.zip` using the "Nom + 4 digits + 1 symbol" policy: tried `Alcatraa` /
  `alcatraa` / `ALCATRAA` / `AlcatraA` and the "intended spelling" `Alcatraz`
  (+ case variants) x all 10000 4-digit combos x ~35 punctuation symbols
  (`wordlist2.txt`, 2.31M candidates) with `fcrackzip -u -D -p` — **no match**.
  Sanity-checked the cracking pipeline itself works (self-test:
  `zip -P 'Alcatraa1234!' test.zip` -> `fcrackzip` found it instantly), so the
  tool/method is sound; the guessed "Nom" value itself is wrong, or the
  digit/symbol placement/charset assumption is wrong.
- Was mid-search for a password-generation script or the original
  `/opt/keys/` source (to read the real zip password or `root_key` directly)
  when the coordinator flagged the challenge as already solved by a teammate
  (platform solve timestamp 2026-11-07T03:19:34Z) and asked to stop duplicate
  work. **Stopped here** — did not reach root, did not read `/root/root.txt`,
  no flag in hand.

## Next angle (if ever resumed, check with team first — may be redundant)

- Check `/opt/keys/` directly as adm (command was queued but not completed)
  for the zip's real password or the plaintext `root_key`.
- Grep the box for the provisioning/generator script that actually picked the
  zip password, rather than re-guessing the "Nom" value.
- Once `root_key` is recovered, `ssh -i root_key root@10.100.16.100` (note:
  challenge's `/start.sh` only opens SSH port 22 inside the container — confirm
  it's exposed before assuming it's reachable from the VPN; service banner so
  far was only ever observed on 9999/tcp).
