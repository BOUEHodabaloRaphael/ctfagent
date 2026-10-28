---
doc_kind: pattern
title: "World-Writable php-fpm Socket: Raw FastCGI Client Pivot"
category: misc
slug: php-fpm-0666-socket-fastcgi-pivot
created: 2026-10-25
status: active
tags:
  - fastcgi
  - php-fpm
  - privilege-escalation
  - world-writable-socket
  - lateral-movement
chain_summary: "A 0666 php-fpm pool socket lets any local user request code execution as that pool's user by speaking raw FastCGI to it (no HTTP front-end needed); BEGIN_REQUEST must be exactly 8 bytes or php-fpm silently drops the connection with no error at all."
---
# World-Writable php-fpm Socket: Raw FastCGI Client Pivot

## Chain Summary

- One-line chain: A 0666 php-fpm pool socket lets any local user request code execution as that pool's user by speaking raw FastCGI to it (no HTTP front-end needed); BEGIN_REQUEST must be exactly 8 bytes or php-fpm silently drops the connection with no error at all.
- Typical target shape: a Linux host running multiple PHP applications under separate php-fpm pools (different Unix users per pool, e.g. a mail/groupware stack like grommunio where each component runs under its own uid), reached initially via a web RCE as a low-privileged pool's user.

## Preconditions

- Local code execution as *some* user (e.g. `grofiles`, uid 462) already obtained, typically via a web-app-level bug (webshell upload, LFI-to-RCE, etc.).
- `/run/php-fpm/` (or equivalent socket directory) is readable by that user and contains a socket for a **different, more interesting** pool with permissive mode (`0666`/`srw-rw-rw-`).
- A location to write a payload PHP script that the target pool's worker can read (`chmod 0644`, since the worker runs as a different uid than the one writing the file).

## Cheap Probes

- `ls -la /run/php-fpm/` (or search `find / -name '*.sock' -perm -666 2>/dev/null`) from the current low-privileged foothold.
- `stat` each discovered socket to confirm the owning pool and its mode; any socket with world read+write (`0666`) is a candidate.

## Telltale Evidence

- A `.sock` file with mode `srw-rw-rw-` (0666) is directly actionable: php-fpm pools execute scripts as the pool's configured user, and nothing about the Unix socket itself restricts who can connect to it if its permissions are wide open.

## Escalation Order

1. Identify a `0666` (or otherwise group/world-connectable, if the current user happens to be in the right group) php-fpm pool socket belonging to a different, more interesting user than the current foothold.
2. Write a minimal PHP payload script to a world-readable location (`chmod 0644`) — it must be readable by the **target pool's** user, not just the uid that wrote it.
3. Speak raw FastCGI to the socket directly (no HTTP front-end required): send `BEGIN_REQUEST` (role=RESPONDER, exactly **8 bytes**: 2-byte role + 1-byte flags + 5 reserved bytes), then `PARAMS` records setting at minimum `GATEWAY_INTERFACE`, `REQUEST_METHOD`, `SCRIPT_FILENAME` (pointing at the payload script), and `QUERY_STRING` (for passing a command), then an empty `PARAMS` to end params, then `STDIN` records (empty is fine for a GET-style invocation), reading back `STDOUT`/`STDERR` records for the response.
4. If the client appears to hang or returns completely nothing (no error, no output), re-verify the `BEGIN_REQUEST` record is exactly 8 bytes — this is the single most common silent-failure cause.
5. Once code executes as the target pool's user, use that foothold's group memberships (e.g. a config-reading group) to pull further secrets (LDAP/DB credentials in app config files) for the next pivot.

## Common Mistakes

- Sending a `BEGIN_REQUEST` record shorter than 8 bytes (e.g. 7 bytes from an off-by-one in manual packing) — php-fpm drops the connection with **zero** diagnostic output, which looks identical to "the socket doesn't accept connections" or "the payload path is wrong," wasting significant debugging time on the wrong hypothesis.
- Forgetting that the payload script's file permissions must allow the **target pool's user** (not the uid that wrote the file) to read it.
- Assuming a `0666` socket implies the pool runs as root — it almost never does; the escalation is lateral (to the pool's specific configured user) unless that pool happens to be configured to run as root.

## Payload Shapes

```php
<?php
// BEGIN_REQUEST body: role(2) + flags(1) + reserved(5) = 8 bytes, role=1 (RESPONDER)
$begin_request_body = pack('n', 1) . chr(0) . str_repeat("\0", 5);
// ... wrap in an FCGI_BEGIN_REQUEST record header (type=1) and send over the unix socket ...
// PARAMS record: SCRIPT_FILENAME=<world-readable payload path>, QUERY_STRING=c=<command>
```

```text
# Target payload script (must be chmod 0644, owned by whoever wrote it, readable by the pool user)
<?php echo "START\n"; system($_GET['c']); echo "\nEND\n"; ?>
```

## Related Writeups

- `knowledge/writeups/misc/htb-autopilot-grommunio-fastcgi-postfix-suid-ad.md`

## Skill Impact

- Related skill: a dedicated Linux local-privesc/lateral-movement skill does not currently exist in this repo (closest is `pwn-triage`, which is binary-exploitation-focused) — consider proposing a lightweight addition via `skill-maintainer` if this pattern recurs.
- Rule to add or update: during Linux post-exploitation recon, always enumerate `/run/php-fpm/` (and equivalent FastCGI socket directories) for world-writable sockets belonging to other users, and remember the exact 8-byte `BEGIN_REQUEST` framing requirement before writing any raw FastCGI client.
