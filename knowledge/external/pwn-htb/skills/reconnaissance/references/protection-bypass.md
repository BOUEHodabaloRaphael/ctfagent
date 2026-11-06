# Protection Bypass Techniques

Quick reference for bypassing common binary protections.

## RELRO (Relocation Read-Only)

### Partial RELRO
- GOT is writable
- **Bypass**: Overwrite GOT entries with format string or arbitrary write

```python
# Overwrite puts@got with system
elf.got['puts']  # Target address
libc.symbols['system']  # Value to write
```

### Full RELRO
- GOT is read-only after startup
- **Bypass**: Target other writable areas:
  - `__malloc_hook` / `__free_hook` (glibc < 2.34)
  - `__exit_funcs`
  - Stack return addresses
  - TLS (Thread Local Storage)

## Stack Canary

### Leak Canary
```python
# Format string leak
payload = b'%17$p'  # Adjust offset to hit canary
# Canary usually ends in 0x00

# Array overread
# If you can control array index, read past bounds
```

### Bypass Without Leak
- Brute force (32-bit: 256 attempts per byte)
- Fork server: canary same across forks
- Thread spraying: same canary in all threads

## NX (Non-Executable Stack)

- **Cannot** execute shellcode on stack
- **Bypass**:
  - ROP chains
  - ret2libc
  - ret2csu
  - SROP

## PIE (Position Independent Executable)

### Leak Binary Base
```python
# Format string - leak return addresses
%p.%p.%p...  # Find addresses starting with 0x55 or 0x56

# Calculate base
binary_base = leaked_addr - known_offset
```

### Partial Overwrite
- Only overwrite lower bytes (1-2 bytes)
- Avoids needing full leak
- Works because PIE base is page-aligned

```python
# Overwrite just low 2 bytes of return address
payload = b'A' * offset + p16(0x1234)  # New low bytes
```

## ASLR (Address Space Layout Randomization)

### Leak Addresses
- Format string leaks
- Use-after-free reads
- Uninitialized memory reads
- Info leaks in protocol responses

### Bypass Without Leak
- Brute force (32-bit feasible: 8-12 bits of entropy)
- Return-to-vsyscall (fixed address on older kernels)
- Spray techniques

## FORTIFY_SOURCE

- Replaces some unsafe functions with checked versions
- `__printf_chk`, `__memcpy_chk`, etc.
- **Bypass**: Usually just prevents obvious overflows; find alternative vectors

## Summary Table

| Protection | Detection | Bypass Technique |
|------------|-----------|------------------|
| Partial RELRO | `checksec` | GOT overwrite |
| Full RELRO | `checksec` | Hooks, TLS, stack |
| Stack Canary | `checksec` | Leak, brute force |
| NX | `checksec` | ROP, ret2libc |
| PIE | `checksec` | Leak base, partial overwrite |
| ASLR | OS level | Leak, brute force |
| FORTIFY | `checksec` | Alternative vectors |
