# HTB Challenge: Last Call (pwn, Easy, 260 XP)

- Target: 154.57.164.69:38699
- Scenario: "leaderboard only has 10 slots... firmware ancient... nobody double-checked where
  slot 10 actually points." -> strongly hints at an off-by-one / out-of-bounds write on a
  high-score array (classic index-10-into-a-10-slot-array bug).
- Binary: last_call, ELF64 LSB PIE, x86-64, static-pie linked, NOT stripped, has debug_info.
- Local flag.txt (bundled, fake): HTB{f4k3_fl4g_4_t3st1ng} -- NOT the real flag, just for local
  testing. Real flag is on the remote service.

## SOLVED ✅ — Flag: HTB{th3_l3ad3rb04rd_w4s_n3v3r_th3_p01nt}

### Root cause
`cabinet` is a global array of 10 entries (idx 0-9), each 0x30 (48) bytes:
`struct { char name[32]; int32 score; char pad[4]; void(*jingle)(void); };`
Immediately after the array in .bss sits an unrelated global `vault_t` struct:
`struct { int open_flag; char pad[4]; void(*jingle_fn_ptr)(void); char buf[0x40]; };`

Both `submit_score` and `view_slot` validate the user-supplied index with `idx <= 10` (should be
`idx <= 9`) -- classic off-by-one. Index 10 computes to `cabinet + 10*0x30 = cabinet + 0x1E0`,
which is exactly the start of `vault_t`. So:
- `view_slot(10)` performs an **arbitrary read** of `vault_t`'s raw bytes (printed as a hex dump:
  "XX XX XX ..." text, 16 bytes per line, NOT raw binary over the socket).
- `submit_score(10)` performs an **arbitrary 48-byte write** onto `vault_t` via a single
  `fread(entry_ptr, 1, 0x30, stdin)` call (prompt: "send exactly %zu raw bytes (name[32] +
  score[4] + jingle_ptr[8]): ").
- Menu option `3` ("Closing time" / `closing_time()`) does: `if (vault_t.open_flag) vault_t.
  jingle_fn_ptr(); else closing_jingle();` -- i.e. calls our hijacked pointer directly.
- `open_vault_for_real()` (offset 0x89cd in the binary) is the actual win function: it
  `fopen("flag.txt")`s and prints its contents.

Byte offsets within the 48-byte submit_score(10) payload that land on vault_t fields:
- [0:4]  = vault_t.open_flag   -> set to 1 (nonzero)
- [8:16] = vault_t.jingle_fn_ptr -> set to PIE_base + 0x89cd (open_vault_for_real)
- rest: don't care

### PIE bypass (no stack leak needed at all)
`view_slot(10)` BEFORE touching anything leaks the **original** `vault_t.jingle_fn_ptr` value,
which is initialized by `init_cabinet()` to `closing_jingle` (offset 0x89b3 in the binary). So:
`PIE_base = leaked_ptr - 0x89b3`, then `target = PIE_base + 0x89cd`.
No canary, NX, RELRO, or CET (SHSTK/IBT) bypass was needed -- the bug is a global-struct index
confusion, entirely independent of stack protections. Static-PIE base landed in the ~0x7f...
mmap-style region (not the usual 0x5555... dynamic-PIE range), consistent with how the kernel
loads ET_DYN static-PIE executables.

### Exploit
Script: `workspaces/lastcall/exploit.py`. Usage: `python3 exploit.py [host] [port]`
(defaults to 154.57.164.69 38699). One-shot, no brute force, ~0.5s runtime.

Key gotcha during development: the socket output for "raw dump" is a **text hex dump**
("XX XX XX ... \n", 16 bytes/line), not raw binary bytes -- must parse as hex tokens, not slice
the byte string directly.
