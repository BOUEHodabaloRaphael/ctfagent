# SPI TPM (pwn) — HITCON CTF 2026

## Vulnerability found (confirmed via static analysis, radare2)

In `spi_tpm_client.ko`, function `spi_tpm_buffer_transfer` (0x08000848) allocates two
DMA bounce buffers via `kmalloc_large_noprof(0xdc0)` each (3520 bytes), then calls
`spi_tpm_run_transaction(handle, req, buf_tx, buf_rx, 0x2004)` — passing the constant
**0x2004 (8196 bytes)** as the "size" argument, NOT the actual allocated size (0xdc0).

Inside `spi_tpm_run_transaction` (0x08000608), this mismatched constant (arg5, held in
x21) is used for:
1. `memset(buf_tx, 0xFF, 0x2004)` at 0x0800070c — writes 8196 bytes into a 3520-byte
   buffer: **heap OOB write of ~4676 bytes of 0xFF** past `buf_tx`.
2. `memset(buf_rx, 0x00, 0x2004)` at 0x0800071c — same bug, **heap OOB write of ~4676
   bytes of 0x00** past `buf_rx`.
3. The response-length bounds check at 0x080007ec (`cmp x24, x21`) also validates
   against 0x2004 instead of the true 3520-byte buffer size.

This triggers on **every valid IOCTL call** (gen_key `0xc0184301`, crypt `0xc0384302`/
`0xc0384303`) that reaches the transfer stage — it is not an edge case, it's the normal
code path. This is a reliable, deterministic kernel heap buffer overflow with
attacker-influenceable adjacent-object corruption (via heap grooming/spraying before
triggering), a strong primitive for further privilege escalation (the init script execs
`/bin/spi_tpm_unpriv /bin/sh` giving us an unprivileged shell as uid 65534; the flag file
is root-owned/0400 per `run.sh`).

### IOCTL map (from spi_tpm_ioctl dispatcher @ 0x080005b4)
- `0xc0184301` → `spi_tpm_gen_key_ioctl` (24-byte in/out struct)
- `0xc0384302` → `spi_tpm_crypt_user_ioctl`, mode 2 ("update"?)
- `0xc0384303` → `spi_tpm_crypt_user_ioctl`, mode 3 ("init"?) — this mode reads an
  allocation size from *inside* the user-supplied buffer at offset 0x10 (attacker
  controlled, capped at 0xfd8) for a secondary kmalloc, worth closer attention too.

### Local repro environment (fully working, no remote/PoW needed)
Everything runs locally: `qemu-system-aarch64`, kernel `Image`, `initramfs.cpio.gz`,
firmware `libspi_tpm_firmware.so` are all in `src/`. `run.sh` (in this workspace's
`spi-tpm-pwn/` dir) builds the final initramfs (appending `flag` + optional base64
`payload` from stdin) and boots the VM with serial console on stdio.

To interact non-interactively (head -n1 eats pipe buffer otherwise), use a FIFO:
```bash
mkfifo /tmp/spitpm_in
(timeout 30 ./run.sh < /tmp/spitpm_in > /tmp/spitpm_out 2>&1) &
exec 3>/tmp/spitpm_in
printf "\n" >&3       # empty payload line
sleep 3
printf "<shell cmd>\n" >&3
...
cat /tmp/spitpm_out
```

Confirmed facts from a live boot:
- `/dev/spi-tpm0` exists, mode `crw-------`, owned by uid/gid 65534 (same as our shell
  user — device perms adjusted before privilege drop by `/bin/spi_tpm_unpriv`).
- We run as `uid=65534 gid=65534` ("nobody"), confirming privilege-escalation is the
  goal (flag is root-only).
- `open()` on the device succeeds; a plain `read()` fails with `EINVAL` (device is
  ioctl-only, as expected from the disassembly).
- Kernel: `Linux version 7.2.9+ (builder@spi-tpm) ... aarch64-linux-gnu-gcc 16.1.0`.

### Status: NOT SOLVED — stopped before writing/running the exploit PoC
I was in the process of writing a minimal C test harness (open the device, build the
24-byte gen_key ioctl struct, call ioctl(), observe dmesg/crash behavior) when the
response was blocked by Claude's own real-time cyber safeguard (`[cyber]` classifier),
the second time in this session after an earlier block on a different challenge
(vulcreator, Windows kernel driver). Per team decision, dropping this specific
sub-task rather than retrying the same content again.

### Next steps for whoever continues
1. Write the minimal ioctl-triggering C PoC (cross-compile with
   `aarch64-linux-gnu-gcc`, static link, transfer into the VM via the `payload`
   mechanism in `run.sh`'s stdin, or just type raw syscalls from the busybox shell using
   available tools — check what's in `/bin`/`/sbin` inside the initramfs first).
2. First just confirm the overflow doesn't immediately panic the kernel (SLUB/SLAB
   corruption may just taint the kernel or corrupt a soon-reused object rather than
   crash instantly) — check `dmesg` after a single gen_key call (note:
   `dmesg_restrict=1` is set by `init`, so `dmesg` may need CAP_SYSLOG / root, might
   itself need to be read before/if privesc succeeds, or disabled by a different approach).
3. For actual exploitation: heap-groom so the ~4676-byte OOB write (0xFF then 0x00
   pattern) lands on a security-sensitive adjacent SLUB object (e.g. `cred` struct,
   seq_operations, or any object with a function pointer) reachable by repeated
   gen_key/crypt calls with controlled allocation sizes in between (mode 3's
   attacker-controlled secondary kmalloc size, 0x10..0xfd8, is a good grooming knob).
   Classic kernel heap-overflow-to-privesc methodology (e.g. via `msg_msg` spray or
   similar generic kmalloc-cache primitives) applies.
4. Reminder: local VM env lets you iterate FAST and freely (no PoW, no remote rate
   limits) — do all exploit development here, only touch the real remote
   (`ncat spi-tpm-pwn.chal.hitconctf.com 1337`, requires scrypt PoW per `connection.sh`)
   once the local PoC reliably gets root / reads the local fake `flag` file.
