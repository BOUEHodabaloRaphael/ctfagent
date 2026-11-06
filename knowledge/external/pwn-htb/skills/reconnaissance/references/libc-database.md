# Libc Database Usage

Identify libc versions from leaked function addresses.

## Online Databases

### libc.blukat.me (Recommended)
1. Get leaked addresses of known functions
2. Note last 3 hex digits (12 bits)
3. Enter at https://libc.blukat.me/
4. Download matching libc

### libc.rip
- Alternative database
- https://libc.rip/

## Local libc-database

### Setup
```bash
git clone https://github.com/niklasb/libc-database
cd libc-database
./get ubuntu  # Download Ubuntu libcs
./get debian  # Download Debian libcs
./get all     # Download all (slow, large)
```

### Search by Symbol
```bash
# Single symbol
./find puts 0x210

# Multiple symbols (more accurate)
./find puts 0x210 printf 0x340 read 0x8a0

# Output: libc6_2.31-0ubuntu9_amd64
```

### Download Identified Libc
```bash
./download libc6_2.31-0ubuntu9_amd64
# Downloads to libs/ directory
```

### Dump Symbols
```bash
./dump libc6_2.31-0ubuntu9_amd64
# Shows offsets for common symbols
```

## Pwntools Integration

### Using libcdb
```python
from pwn import *
from pwnlib.libcdb import search_by_symbol_offsets

# Search
results = search_by_symbol_offsets({
    'puts': 0x875a0,
    'printf': 0x64f00
}, return_as_list=True)

for r in results:
    print(f"Match: {r}")
```

### Auto-fetch libc
```python
# pwntools can auto-fetch from libcdb
libc = ELF('./libc.so.6')
# Or let it search online
```

## Extracting Offsets

Once you have the libc:

```python
libc = ELF('./libc.so.6')

# Common symbols
print(f"system: {hex(libc.symbols['system'])}")
print(f"execve: {hex(libc.symbols['execve'])}")
print(f"/bin/sh: {hex(next(libc.search(b'/bin/sh')))}")
print(f"__free_hook: {hex(libc.symbols['__free_hook'])}")
print(f"__malloc_hook: {hex(libc.symbols['__malloc_hook'])}")
```

## One-Gadget Integration

After identification:
```bash
one_gadget ./libc.so.6
```

Output shows constraints that must be satisfied.

## Tips

1. **Need 2+ leaks** for reliable identification
2. **Check alignment**: libc base should be page-aligned (ends in 000)
3. **Verify match**: Check that calculated offsets work for multiple functions
4. **Version matters**: Even minor versions have different offsets
