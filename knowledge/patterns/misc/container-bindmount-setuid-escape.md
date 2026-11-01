---
doc_kind: pattern
title: "Container bind-mount misconfig to setuid binary host escape"
category: misc
slug: container-bindmount-setuid-escape
created: 2026-11-01
status: active
tags:
  - container-escape
  - bind-mount
  - setuid
  - mountinfo
  - nosuid-missing
  - privesc
chain_summary: "After landing root-equivalent code execution inside a container, inspect /proc/1/mountinfo (or /proc/<pid>/mountinfo) for host bind mounts; a mis-scoped mount (e.g. container /root bound to a host user's home dir, no nosuid) lets you copy a native host binary (bash) through that mount, chown 0:0 + chmod 4755 it from inside the container (as root there), then execute it setuid from the low-privileged host user with `bash -p` to get euid=0 on the host."
---
# Container bind-mount misconfig to setuid binary host escape

## Chain Summary

- One-line chain: After landing root-equivalent code execution inside a container, inspect `/proc/1/mountinfo` (or `/proc/<pid>/mountinfo`) for host bind mounts; a mis-scoped mount (e.g. container `/root` bound to a host user's home dir, no `nosuid`) lets you copy a native host binary (bash) through that mount, `chown 0:0` + `chmod 4755` it from inside the container (as root there), then execute it setuid from the low-privileged host user with `bash -p` to get `euid=0` on the host.
- Typical target shape: a multi-container setup (Docker/Podman/k8s) where one container runs as root for convenience (automation/orchestration tooling, build agents, admin tools) and has a bind mount into a host directory that is also a low-privileged user's home or writable area, without `nosuid` set on that mount.

## Preconditions

- Code execution inside a container, running as root (or a user who can `chown`/`chmod` arbitrary files on at least part of the mounted filesystem) within that container.
- A separate, lower-privileged foothold on the host (SSH as a normal user, another shell) that can reach the same bind-mounted directory from the host side.
- The bind mount is missing the `nosuid` mount option (the default for most manually-specified bind mounts unless explicitly hardened) — `nosuid` alone defeats this entire technique.

## Cheap Probes

- From inside the container (as root): `cat /proc/1/mountinfo` or `mount` to list all mounts; `awk '$8 !~ /^(proc|sysfs|tmpfs|devpts|mqueue|cgroup2)$/ {print "target="$5, "root="$4, "fs="$9}' /proc/1/mountinfo` to filter down to real bind mounts (mountinfo field 4 = root of the mount source relative to its filesystem, field 5 = mount point in the container).
- From the host side (as the low-priv user): `grep ' <mountpoint> ' /proc/mounts` to see the mount options as the host sees it (look for presence/absence of `nosuid`).
- Write a harmless marker file from inside the container at the suspected mount target, then check from the host side whether it appears at the expected host path — confirms the mapping before attempting anything privileged.

## Telltale Evidence

- `/proc/1/mountinfo` (or `mount` output) inside the container shows a bind mount whose container-side target is a sensitive path (`/root`, `/home/<user>`, an app data dir) and whose host-side source (`root=` field, or the fstab/docker-compose volume definition if visible) maps to a directory owned by, or writable by, a lower-privileged host account.
- The host's own `/proc/mounts` entry for that filesystem lacks `nosuid` in its options list.
- A file created with `chown 0:0` + `chmod 4755` inside the container, when `stat`'d from the host side, shows the same `0:0 4755` ownership/mode — confirms the mount is a true bind mount (same inode) and not a copy-on-write/overlay that would silently drop the setuid bit or ownership.

## Escalation Order

1. From root-in-container, enumerate all mounts via `/proc/1/mountinfo`, filtering out standard pseudo-filesystems to find real bind mounts.
2. Cross-check each candidate bind mount's host-side mount options via `/proc/mounts` (from the host foothold) for the absence of `nosuid` (and ideally also check for `noexec`, which would independently block this).
3. Identify (or copy in) a legitimate, working native binary to use as the setuid payload — prefer copying the host's own `/bin/bash` (or similar) rather than a cross-compiled/foreign one, to avoid dynamic-linking/ABI mismatches; verify the copy is byte-identical (`sha256sum`) to the host original if copied via the container.
4. From root-in-container, `chown 0:0` and `chmod 4755` (or `6755` if you also want setgid) the binary at its container-side bind-mount path.
5. From the host's low-privileged account, locate the same file at its host-side path and execute it with a shell flag that preserves the elevated effective UID (bash: `-p`; some other shells need no special flag, others drop privileges by default and need different handling) — confirm with `id`/`whoami` showing `euid=0`/`root` before relying on it for anything else.
6. Clean up: delete the planted setuid binary from both the container and host paths once done, since it's a standing backdoor if left in place.

## Common Mistakes

- Copying a binary into the container filesystem and chmod'ing it there without realizing overlay/union filesystem layers (common in Docker) are copy-on-write and the setuid bit may not persist correctly, or the binary may be dynamically linked against container-only libraries that don't exist on the host — always verify by `stat`/`sha256sum`-checking from the *host* side, and prefer binaries that originated on the host.
- Forgetting `bash -p` (or the equivalent) when invoking the setuid shell — a plain `./binary` invocation of a setuid bash will often drop the elevated privileges it was just granted unless told to preserve them.
- Not checking for `nosuid` before investing time in this path — if present, this entire technique is dead and effort should go elsewhere (container breakout via other means, or a different privesc vector).
- Racing a copy of a binary that's currently in use/mapped (`Text file busy`) — copy to a new filename, or ensure no process currently has the target file open/executing, rather than overwriting a binary in place.

## Payload Shapes

```bash
# Inside the container (root) — find real bind mounts
awk '$8 !~ /^(proc|sysfs|tmpfs|devpts|mqueue|cgroup2)$/ {print "target="$5, "root="$4, "fs="$9}' /proc/1/mountinfo

# Host side (low-priv user) — confirm no nosuid on that filesystem
grep ' /root ' /proc/mounts   # example target path

# Host side — stage a copy of a native binary at a free path within the shared mount
cp /bin/bash /home/<user>/.escape_bash && sha256sum /bin/bash /home/<user>/.escape_bash

# Container side (root) — make it setuid root via the bind-mounted path
chown 0:0 /root/.escape_bash && chmod 4755 /root/.escape_bash

# Host side (low-priv user) — run it, preserving euid
./.escape_bash -p -c "id; whoami"
```

## Related Writeups

- `knowledge/writeups/web/htb-takeoff-ssti-hmac-forge-n8n-bindmount.md`

## Skill Impact

- Related skill: `pwn-triage` / general post-exploitation checklist (add a "container landed -> check /proc/1/mountinfo for host bind mounts" step right after any container shell is obtained, before looking for kernel exploits or other heavier escape techniques)
- Rule to add or update: whenever a shell lands inside what looks like a container (cgroup/namespace indicators, `/.dockerenv`, minimal rootfs), check `/proc/1/mountinfo` for bind mounts into host paths before anything else — primed for reuse during NCTF26, since this is a cheap, high-signal check with no destructive side effects.
