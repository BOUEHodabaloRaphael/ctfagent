# Stack Frame Layouts

Understanding stack layouts for exploitation.

## x86_64 (64-bit) Stack Frame

```
High addresses
+------------------+
| Return Address   |  [rbp + 8]
+------------------+
| Saved RBP        |  [rbp]
+------------------+
| Local var 1      |  [rbp - 8]
+------------------+
| Local var 2      |  [rbp - 16]
+------------------+
| ...              |
+------------------+
| Buffer           |  [rbp - X]
+------------------+
| Stack canary     |  [rbp - 8] (if enabled)
+------------------+
Low addresses (RSP)
```

### Offset Calculation (x64)
```
Buffer at [rbp - 0x40] (64 bytes)
Saved RBP at [rbp]
Return address at [rbp + 8]

Offset to return = 0x40 + 8 = 72 bytes
```

### With Canary (x64)
```
Buffer at [rbp - 0x48]
Canary at [rbp - 0x8]
Saved RBP at [rbp]
Return address at [rbp + 8]

Offset to canary = 0x48 - 0x8 = 64 bytes
Offset to return = 0x48 + 8 = 80 bytes
```

## x86 (32-bit) Stack Frame

```
High addresses
+------------------+
| Arguments        |  [ebp + 12], [ebp + 8]...
+------------------+
| Return Address   |  [ebp + 4]
+------------------+
| Saved EBP        |  [ebp]
+------------------+
| Local variables  |  [ebp - 4], [ebp - 8]...
+------------------+
| Buffer           |  [ebp - X]
+------------------+
Low addresses (ESP)
```

### Offset Calculation (x86)
```
Buffer at [ebp - 0x20] (32 bytes)
Saved EBP at [ebp]
Return address at [ebp + 4]

Offset to return = 0x20 + 4 = 36 bytes
```

## Finding Buffer Offset from Disassembly

### Method 1: Look at sub rsp
```asm
push   rbp
mov    rbp, rsp
sub    rsp, 0x40      ; 64 bytes allocated
```

### Method 2: Look at lea for buffer
```asm
lea    rax, [rbp-0x30]  ; Buffer at rbp-0x30 (48 bytes from rbp)
mov    rdi, rax
call   gets@plt
```

Offset = 0x30 (to RBP) + 8 (to return) = 56 bytes

## Cyclic Pattern Verification

### Generate Pattern
```python
from pwn import *
pattern = cyclic(100)
# Send to crash the binary
```

### Find Offset
```python
# From core dump or crash info
crash_value = 0x61616168  # 'haaa' in little endian
offset = cyclic_find(crash_value)
print(f"Offset: {offset}")
```

### GDB Method
```bash
# In GDB after crash
x/wx $rsp  # See what's at stack pointer
# Or
info frame  # See return address
```

## Stack Pivoting Layout

When you can't reach return address directly:

```
+------------------+
| leave; ret       | <- Overwritten return
+------------------+
| Fake RBP         | <- Points to controlled area - 8
+------------------+
| Buffer           | <- Contains ROP chain
+------------------+

leave = mov rsp, rbp; pop rbp
ret   = pop rip

Result: RSP now points to your ROP chain
```

## Common Stack Sizes

| Allocation | Typical Use |
|------------|-------------|
| 0x10 (16)  | Small struct |
| 0x20 (32)  | Name buffer |
| 0x40 (64)  | Standard buffer |
| 0x80 (128) | Large buffer |
| 0x100 (256)| File path |
| 0x400 (1024)| Large I/O buffer |

## Register Preservation

### Caller-Saved (x64)
- RAX, RCX, RDX, RSI, RDI, R8-R11
- May be modified by called function

### Callee-Saved (x64)
- RBX, RBP, R12-R15
- Restored before function returns
- Often pushed to stack at function start
