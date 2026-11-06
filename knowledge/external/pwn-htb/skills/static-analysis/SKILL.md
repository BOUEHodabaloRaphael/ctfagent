---
name: PWN Static Analysis
description: This skill should be used when the user asks to "disassemble binary", "analyze functions", "find vulnerability", "reverse engineer", "identify buffer size", "find dangerous functions", "analyze stack layout", or needs to perform static code analysis on a binary. Provides methodology for identifying vulnerabilities through disassembly.
version: 1.0.0
---

# PWN Static Analysis

## Overview

Static analysis examines the binary without execution to identify vulnerabilities, understand program flow, and map out exploitation targets. This phase focuses on disassembly, dangerous function identification, and vulnerability pattern recognition.

## Analysis Targets

1. Main function and program flow
2. Vulnerable functions (user input handlers)
3. Buffer sizes and stack layouts
4. Dangerous function calls
5. Potential write primitives
6. Leak opportunities

## Step 1: Disassemble Key Functions

### Using objdump

```bash
# Disassemble specific function
objdump -d ./binary | grep -A 50 '<main>:'

# Disassemble all with Intel syntax
objdump -d -M intel ./binary > disasm.txt
```

### Using radare2

```bash
# Quick analysis
r2 -A ./binary -c 'pdf @ main' -q

# Full function list
r2 -A ./binary -c 'afl' -q
```

### Using pwntools

```python
from pwn import *
elf = ELF('./binary')
print(disasm(elf.read(elf.symbols['main'], 100)))
```

## Step 2: Identify Dangerous Functions

### Buffer Overflow Sources

| Function | Risk | Pattern |
|----------|------|---------|
| `gets()` | Critical | No bounds checking |
| `scanf("%s")` | Critical | No width specifier |
| `strcpy()` | High | No length check |
| `strcat()` | High | Can overflow dest |
| `sprintf()` | High | No bounds on output |
| `read()` | Medium | Check size vs buffer |

Search for dangerous calls:

```bash
objdump -d ./binary | grep -E 'call.*<(gets|strcpy|sprintf|strcat|scanf)@plt>'
```

### Format String Vulnerabilities

Check for user-controlled format strings:

```bash
# Look for printf-family calls
objdump -d ./binary | grep -E 'call.*<(printf|fprintf|sprintf|snprintf)@plt>'
```

Red flags in disassembly:
- `printf` called directly after user input
- No format string argument (just buffer)
- User buffer passed as first argument to printf

## Step 3: Calculate Buffer Sizes

### From Disassembly

Look for stack allocation patterns:

```asm
; x86_64
sub    rsp, 0x40        ; 64 bytes allocated
lea    rax, [rbp-0x30]  ; Buffer at rbp-0x30 (48 bytes from rbp)

; x86
sub    esp, 0x28        ; 40 bytes allocated
lea    eax, [ebp-0x20]  ; Buffer at ebp-0x20 (32 bytes from ebp)
```

### Calculate Offset to Return Address

```
For x86_64:
- Buffer starts at [rbp - offset]
- Return address at [rbp + 8]
- Offset = offset + 8

For x86:
- Buffer starts at [ebp - offset]
- Return address at [ebp + 4]
- Offset = offset + 4
```

## Step 4: Map Function Call Graph

For small binaries, understand the call flow:

```bash
# Using radare2
r2 -A ./binary -c 'agC' -q

# Or manual grep
objdump -d ./binary | grep 'call' | sort | uniq -c | sort -rn
```

## Step 5: Identify Write Primitives

### GOT Overwrite Targets

If Partial RELRO:

```python
from pwn import *
elf = ELF('./binary')
# Overwrite exit@got with win function
print(f"exit@got: {hex(elf.got['exit'])}")
print(f"win: {hex(elf.symbols['win'])}")
```

### Stack-based Targets

- Return addresses
- Function pointers on stack
- Saved base pointers (for stack pivoting)

## Step 6: Find Leak Opportunities

### Format String Leaks

If format string vulnerability exists:
- `%p` leaks stack values
- `%s` leaks strings at stack addresses
- Calculate offset to leak canary, libc, PIE base

### puts/printf on Stack Data

Look for functions that print stack buffers - may leak canary or addresses.

## Vulnerability Patterns

### Pattern 1: Simple Buffer Overflow

```c
void vuln() {
    char buf[64];
    gets(buf);  // Overflow here
}
```

Disassembly shows:
- `sub rsp, 0x50` (stack allocation)
- `call gets@plt` with buffer on stack

### Pattern 2: Off-by-One

```c
void vuln() {
    char buf[64];
    for(int i = 0; i <= 64; i++)  // <= instead of <
        buf[i] = getchar();
}
```

Can overwrite least significant byte of saved RBP.

### Pattern 3: Format String

```c
void vuln() {
    char buf[64];
    read(0, buf, 64);
    printf(buf);  // No format specifier
}
```

Allows arbitrary read/write via format string.

## Output Format

```
## Static Analysis

### Findings
- Vulnerability: Buffer overflow in vuln() via gets()
- Buffer size: 64 bytes at [rbp-0x40]
- Offset to RIP: 72 bytes (64 + 8 for saved RBP)
- Win function: 0x401234 (win)
- Dangerous calls: gets@plt at 0x401186

### Disassembly Highlights
```asm
vuln:
    push   rbp
    mov    rbp, rsp
    sub    rsp, 0x40         ; 64 byte buffer
    lea    rax, [rbp-0x40]   ; Buffer address
    mov    rdi, rax
    call   gets@plt          ; VULNERABLE
```

### Implications
- Direct ret2win possible (no PIE, no canary)
- Payload: 72 bytes padding + address of win()

### Next Steps
1. Confirm offset with cyclic pattern
2. Craft payload: b'A'*72 + p64(0x401234)
3. Test locally before remote
```

## Quick Reference

```bash
# Full static analysis one-liner
objdump -d -M intel ./binary | grep -E '(main>:|vuln|gets|strcpy|printf|system|call|ret|leave)'
```

## Additional Resources

### References

- **`references/vulnerability-patterns.md`** - Common vulnerability patterns in CTF binaries
- **`references/stack-layout.md`** - Detailed stack frame layouts for x86/x64
- **`references/gadgets.md`** - Common ROP gadget patterns
