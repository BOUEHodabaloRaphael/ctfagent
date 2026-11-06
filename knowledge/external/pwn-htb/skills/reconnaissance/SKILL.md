---
name: PWN Reconnaissance
description: This skill should be used when the user asks to "analyze binary", "run checksec", "check binary protections", "identify architecture", "find strings in binary", "extract symbols", "recon binary", or needs initial binary analysis before exploitation. Provides methodology for the reconnaissance phase of binary exploitation.
version: 1.0.0
---

# PWN Reconnaissance

## Overview

The reconnaissance phase gathers critical information about a target binary before exploitation. This includes identifying architecture, protections, interesting strings, symbols, and potential libc version.

## Reconnaissance Checklist

1. File type and architecture identification
2. Security protections (checksec)
3. Interesting strings extraction
4. Symbol table analysis
5. Libc identification (if applicable)
6. Seccomp filter detection

## Step 1: File Identification

Identify the binary type and architecture:

```bash
file ./binary
```

Expected output interpretation:

| Output Contains | Meaning |
|----------------|---------|
| ELF 64-bit LSB executable | x86_64 architecture |
| ELF 32-bit LSB executable | x86 (i386) architecture |
| dynamically linked | Uses shared libraries (libc) |
| statically linked | Self-contained, no libc exploits |
| not stripped | Contains debug symbols |
| stripped | No debug symbols |

## Step 2: Security Protections

Run checksec to identify protections:

```bash
checksec --file=./binary
```

Or via pwntools:

```python
from pwn import *
elf = ELF('./binary')
print(elf.checksec())
```

### Protection Analysis

| Protection | Enabled | Exploitation Impact |
|------------|---------|---------------------|
| **RELRO** | Partial | GOT overwrite possible |
| **RELRO** | Full | No GOT overwrite, use other primitives |
| **Stack Canary** | Yes | Must leak or bypass canary |
| **NX** | Yes | No shellcode on stack, use ROP/ret2libc |
| **PIE** | Yes | Must leak binary base address |
| **FORTIFY** | Yes | Some unsafe functions hardened |

## Step 3: Strings Extraction

Find interesting strings:

```bash
strings -n 8 ./binary | grep -iE '(flag|password|secret|admin|shell|bin/sh|/bin)'
```

Look for:
- Format string specifiers (`%s`, `%x`, `%n`)
- Function names (`system`, `execve`)
- File paths (`/bin/sh`, `/flag`)
- Potential passwords or keys

## Step 4: Symbol Analysis

Extract symbols if not stripped:

```bash
nm ./binary | grep -E ' [TtWw] ' | head -30
```

Or use readelf:

```bash
readelf -s ./binary | grep FUNC
```

Key symbols to note:
- `main` - Entry point for analysis
- `win`, `flag`, `shell` - Potential win functions
- `vuln`, `vulnerable` - Obvious vulnerability hints
- PLT entries for dangerous functions

### Check for Win Functions

```bash
nm ./binary | grep -iE '(win|flag|shell|backdoor|secret)'
```

## Step 5: PLT/GOT Analysis

Identify imported functions:

```bash
objdump -d ./binary | grep '@plt>:' | head -20
```

Or via pwntools:

```python
from pwn import *
elf = ELF('./binary')
print("PLT entries:", list(elf.plt.keys()))
print("GOT entries:", list(elf.got.keys()))
```

Dangerous functions to note:
- `gets`, `scanf`, `strcpy`, `sprintf` - Buffer overflow
- `printf`, `fprintf` - Format string (if user-controlled)
- `system`, `execve` - Code execution targets

## Step 6: Libc Identification

If libc is provided:

```bash
strings libc.so.6 | grep -E "^GNU C Library"
file libc.so.6
md5sum libc.so.6
```

Query libc database with known offsets:

```bash
# Using libc-database
./libc-database/find printf <leaked_printf_offset>

# Or online: https://libc.blukat.me/
```

## Step 7: Seccomp Detection

Check for seccomp filters:

```bash
seccomp-tools dump ./binary
```

If seccomp is present, analyze allowed syscalls to determine exploitation constraints (e.g., no execve means ORW - open/read/write approach).

## Output Format

```
## Reconnaissance

### Findings
- Architecture: x86_64, dynamically linked, not stripped
- Protections: Partial RELRO, No Canary, NX enabled, No PIE
- Dangerous functions: gets@plt, printf@plt (potential format string)
- Interesting symbols: main, vuln, win (0x401234)
- Libc: Not provided (infer from remote)

### Commands Run
- file ./binary
- checksec --file=./binary
- strings -n 8 ./binary
- nm ./binary

### Implications
- No PIE: Fixed addresses, direct ROP possible
- NX enabled: Cannot execute shellcode on stack
- gets present: Likely buffer overflow vulnerability
- win function exists: ret2win exploitation possible

### Next Steps
1. Disassemble vuln() and win() functions
2. Identify buffer size in vuln()
3. Calculate offset to return address
4. Craft ret2win payload
```

## Quick Reference Commands

```bash
# All-in-one recon
file ./binary && checksec --file=./binary && nm ./binary 2>/dev/null | head -20

# Find dangerous functions
objdump -d ./binary | grep -E '<(gets|strcpy|sprintf|scanf|printf)@plt>'

# Check for win function
nm ./binary 2>/dev/null | grep -iE 'win|flag|shell' || echo "No obvious win function"
```

## Additional Resources

### References

- **`references/protection-bypass.md`** - Techniques for bypassing each protection
- **`references/libc-database.md`** - Using libc-database for identification

### Scripts

- **`scripts/full-recon.sh`** - Run complete reconnaissance suite
