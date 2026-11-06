# Common CTF Libc Versions

Reference for frequently encountered libc versions in CTF challenges.

## Ubuntu Versions

### Ubuntu 18.04 (glibc 2.27)
```
libc6_2.27-3ubuntu1_amd64
libc6_2.27-3ubuntu1_i386

Key offsets (amd64):
  system: 0x4f440
  execve: 0xe4e30
  /bin/sh: 0x1b3e9a
  __free_hook: 0x3ed8e8
  __malloc_hook: 0x3ebc30
  one_gadget: 0x4f2c5, 0x4f322, 0x10a38c
```

### Ubuntu 20.04 (glibc 2.31)
```
libc6_2.31-0ubuntu9_amd64
libc6_2.31-0ubuntu9.7_amd64

Key offsets (amd64):
  system: 0x52290
  execve: 0xe62f0
  /bin/sh: 0x1b45bd
  __free_hook: 0x1eeb28
  __malloc_hook: 0x1ecb70
  one_gadget: 0xe3b2e, 0xe3b31, 0xe3b34
```

### Ubuntu 22.04 (glibc 2.35)
```
libc6_2.35-0ubuntu3_amd64

Key offsets (amd64):
  system: 0x50d70
  execve: 0xeb0f0
  /bin/sh: 0x1d8698
  NOTE: __malloc_hook/__free_hook removed in 2.34+
```

## Debian Versions

### Debian 10 (Buster, glibc 2.28)
```
libc6_2.28-10_amd64

Key features:
  - tcache introduced
  - Hooks still available
```

### Debian 11 (Bullseye, glibc 2.31)
```
libc6_2.31-13_amd64

Similar to Ubuntu 20.04
```

## Alpine (musl libc)
```
Different from glibc!
- Smaller, different internals
- Different exploitation techniques
- No hooks like glibc
```

## Key Version Differences

### Tcache (2.26+)
- Introduced in glibc 2.26
- Per-thread cache for small allocations
- Minimal security checks initially

### Tcache Double-Free Check (2.29+)
```c
// 2.29 added key field check
if (tcache->entries[tc_idx] == e)
    malloc_printerr ("free(): double free detected");
```

### Safe Linking (2.32+)
```c
// fd pointers XOR'd with address
#define PROTECT_PTR(pos, ptr) \
    ((__typeof (ptr)) ((((size_t) pos) >> 12) ^ ((size_t) ptr)))
```

### Hooks Removed (2.34+)
- `__malloc_hook` removed
- `__free_hook` removed
- `__realloc_hook` removed
- Need alternative targets (TLS, _IO structures)

## Version Detection

### From Binary
```bash
strings libc.so.6 | grep "GNU C Library"
# GNU C Library (Ubuntu GLIBC 2.31-0ubuntu9) stable release version 2.31

strings libc.so.6 | grep -E "^[0-9]+\.[0-9]+"
# 2.31
```

### From Symbols
```bash
nm -D libc.so.6 | grep -c tcache
# Non-zero = 2.26+

nm -D libc.so.6 | grep __malloc_hook
# Empty = 2.34+
```

### Build ID
```bash
file libc.so.6
# ... BuildID[sha1]=abc123...

readelf -n libc.so.6 | grep "Build ID"
```

## Quick Offset Lookup

### System Call Setup (x64)
```python
# execve("/bin/sh", NULL, NULL)
# rax = 59, rdi = /bin/sh, rsi = 0, rdx = 0

def get_shell_offsets(libc):
    return {
        'system': libc.symbols['system'],
        'execve': libc.symbols['execve'],
        'bin_sh': next(libc.search(b'/bin/sh')),
        'pop_rdi': libc.search(asm('pop rdi; ret')).__next__(),
    }
```

### Common Function Offsets

```
Function        2.27      2.31      2.35
-----------------------------------------
system          0x4f440   0x52290   0x50d70
execve          0xe4e30   0xe62f0   0xeb0f0
puts            0x80970   0x84420   0x80e50
printf          0x64e10   0x64f00   0x60770
read            0x110020  0x111130  0x114980
write           0x110090  0x1111d0  0x114a20
open            0x10fc40  0x10dce0  0x114690
```

## Testing with Specific Libc

### Using patchelf
```bash
# Download matching ld.so
cp libs/libc6_2.31/ld-linux-x86-64.so.2 ./

# Patch binary
patchelf --set-interpreter ./ld-linux-x86-64.so.2 ./binary
patchelf --set-rpath . ./binary

# Run with libc
LD_PRELOAD=./libc.so.6 ./binary
```

### Using Docker
```bash
# Ubuntu 20.04 environment
docker run -it -v $(pwd):/work ubuntu:20.04 /bin/bash
cd /work
./binary
```

## Exploitation Strategy by Version

| Version | Strategy |
|---------|----------|
| < 2.26 | Fastbin attacks, hooks |
| 2.26-2.28 | Tcache poison, hooks |
| 2.29-2.31 | Tcache with key bypass, hooks |
| 2.32-2.33 | Safe-linking bypass, hooks |
| 2.34+ | TLS attacks, FSOP, no hooks |
