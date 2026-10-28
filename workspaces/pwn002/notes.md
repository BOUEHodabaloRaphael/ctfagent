# PWN#002 (pwn, 135 pts) — SOLVED

Flag: `CTF{e0a79830f06dca87a52f8be6d895deae}`

Target: `169.58.126.107:5001`. Binary `vault` (PIE, stripped, Full RELRO, canary, NX, seccomp).
Same `libc.so.6`/`ld-linux-x86-64.so.2` as PWN#001.

## Key differences from PWN#001
- **PIE + stripped** (PWN#001 was non-PIE, non-stripped). No symbol table, had to
  reverse via objdump/readelf, and the vulnerable function (`0x1676`) is
  control-flow-flattened (state machine with jump tables) but structurally
  identical to PWN#001's `vuln()`: same offsets (canary@buf+72, saved-RBP@+80,
  saved-RIP@+88), same `read(0x49)` then `read(0x100)` pattern, same
  `"Hello, "`/puts(buf) echo giving the same canary+partial-RBP overread leak.
- **Self-installed seccomp-bpf filter** (via `prctl(PR_SET_SECCOMP)`, built by hand
  in the binary at ~0x12b1): blocks **only `execve` (59) and `execveat` (322)**,
  allows everything else. So `system("/bin/sh")` / any execve-based shell is a
  dead end — the intended path is direct `open`+`read`+`puts`/`write` syscalls.
- **Free PIE-base leak**: right after the banner, the binary itself prints
  `"Vault seal: %016lx"` with the runtime address of `main+0x11`. Parse this
  line and compute `pie_base = leaked_value - 0x13a6` (0x13a6 = local
  `main`(0x1395)+0x11). No bruteforce/overflow needed for this.
- **Flag path is XOR-obfuscated in the binary** (key `0x5a`, 15 ciphertext bytes
  at `.bss+0x4060`, decoded into `.bss+0x4070` by a startup routine before our
  connection even begins): decodes to **`/flag/flag.txt`**.

## Gadget scarcity (the real puzzle this time)
The binary itself has **no `pop rdi`/`pop rsi`/`pop rdx` gadgets at all** (confirmed via
ROPgadget — only `pop rax;ret`, `pop rcx;ret`, `pop rbp;ret` exist cleanly), and
**no `__libc_csu_init`-style gadget** either (modern GCC 12.2 + glibc 2.42 didn't
emit the classic pattern). BUT there's a gift: an **unintended `pext rdi, rax, rcx ; ret`**
gadget at `0x1529` (from `clc; xor eax,eax; pext rdi,rax,rcx; ret` — jump straight to
the `pext` instruction, skipping the `xor`). With `rcx = 0xFFFFFFFFFFFFFFFF` (all-ones
mask), `pext` becomes an identity copy: **`rdi := rax`**. Combined with the binary's
own clean `pop rax;ret` (0x11e0) and `pop rcx;ret` (0x1210), this gives full RDI
control using only binary-internal gadgets — enough to leak `puts@got` via
`puts(puts@got)` (ret2plt, no libc needed yet).

Once libc_base is known (from that first leak), libc itself has plenty of
**unaligned/overlapping** gadgets (ROPgadget finds them even though they're not at
"natural" instruction boundaries — one byte into an adjacent multi-byte instruction):
- `pop rdi ; ret` @ libc+0x2a9b7
- `pop rsi ; ret` @ libc+0x29e29
- `pop rdx ; ret` @ libc+0x96372
- plain `ret` @ libc+0x2846b (alignment filler)

## Two bugs found and fixed during exploitation (both via core-dump analysis)
1. **SIGBUS, flag content ends up in a weird register** — caused by picking the
   `read()` destination buffer (`SCRATCH`) at `pie_base+0x4020`, which is
   **exactly where the binary's `stdout` global (a `FILE*`) lives** in `.bss`
   (confirmed via `readelf -sW`: `stdout@GLIBC_2.2.5` at `0x4020`). Overwriting it
   with flag bytes corrupts the pointer `puts()`/`vfprintf()` immediately
   dereferences afterward → crash. **The entire `.bss` region is "full"** —
   stdin/stdout/stderr pointers, argc/argv/envp, the XOR ciphertext and the
   decoded flag path all live there with no free space. **Fix: never write the
   read() output to `.bss`. Use stack memory instead** — e.g.
   `leaked_saved_rbp - 0x400` (from the per-round canary-leak technique, which
   already gives a real, writable stack address for free).
2. **Hardcoding `fd=3` for the `read()` call is fragile** and failed silently on
   the *remote* target (worked fine locally where `open()` reliably got fd 3,
   but the remote launcher apparently has different fd bookkeeping). **Fix:
   don't assume the fd — reuse the binary's own `pop_rax`/`pop_rcx`/`pext_rdi`
   gadgets right after the `open()` call (before clobbering `rax`) to copy the
   *real* returned fd from `rax` into `rdi`** for the subsequent `read()`.
3. **Short-leak edge case is worse here than in PWN#001**: during remote testing,
   hit leaks with only 0-1 real RBP bytes (not just the "<7 canary bytes"
   case) multiple times in a row. Needed to raise the retry threshold to
   `len(leaked) >= 12` (not just `>= 7`) to reliably get a believable 4+ byte
   partial stack address before trusting `rbp_full`.

## Final working chain (see `exploit.py` in this workspace)
Stage 1 (leak): `pop_rax(binary); PUTS_GOT; pop_rcx(binary); 0xFFFF...; pext_rdi(binary); puts@plt; LOOP`
→ leak puts@libc → `libc_base = leak - libc.symbols['puts']`.

Stage 2 (read flag): `pop_rdi(libc) FLAG_PATH; pop_rsi(libc) 0; ret; open@libc;
pop_rcx(binary) 0xFFFF...; pext_rdi(binary); pop_rsi(libc) SCRATCH_STACK;
pop_rdx(libc) 0x60; ret; read@libc; pop_rdi(libc) SCRATCH_STACK; ret; puts@libc`

`LOOP` = `pie_base + 0x148a` (main's `call <vuln_func>` site — returning here does a
clean, properly-aligned re-entry into the next round via a real `call`
instruction, same trick as relying on a known-good single-hop return target).

Both `/flag/flag.txt`'s existence and the whole chain were validated **locally
first** (created a fake `/flag/flag.txt`, ran the exploit against
`process(["./ld-linux-x86-64.so.2","--library-path",".","./vault"])`, confirmed
the fake flag came back) before ever touching the remote target — this caught
both bugs above cheaply, without burning remote attempts.
