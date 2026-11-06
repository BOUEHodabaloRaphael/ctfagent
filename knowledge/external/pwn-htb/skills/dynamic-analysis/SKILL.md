---
name: PWN Dynamic Analysis
description: This skill should be used when the user asks to "debug binary", "find offset", "calculate padding", "use gdb", "attach debugger", "crash analysis", "cyclic pattern", "test exploit", "bad characters", "find bad chars", or needs to perform runtime analysis of a binary. Provides methodology for dynamic debugging with GDB/pwndbg including bad character detection.
version: 1.0.0
---

# PWN Dynamic Analysis

## Overview

Dynamic analysis involves running the binary under a debugger to observe behavior, calculate offsets, identify crash points, and understand memory layouts at runtime. This phase uses GDB with pwndbg for efficient exploitation research.

## Dynamic Analysis Goals

1. Verify static analysis findings
2. Calculate exact offsets using cyclic patterns
3. Identify register control at crash
4. Find ASLR/PIE base addresses
5. **Detect bad characters** that break payloads
6. Observe stack and heap layouts
7. Test exploit payloads

## Step 1: GDB Setup with pwndbg

### Launch GDB

```bash
# Basic launch
gdb ./binary

# With arguments
gdb --args ./binary arg1 arg2

# Attach to running process
gdb -p $(pidof binary)
```

### Essential pwndbg Commands

| Command | Purpose |
|---------|---------|
| `checksec` | Show binary protections |
| `vmmap` | Show memory mappings |
| `telescope` | Examine stack with dereferencing |
| `context` | Show registers, stack, code |
| `cyclic 200` | Generate cyclic pattern |
| `cyclic -l 0x61616168` | Find offset from pattern |
| `search -s "/bin/sh"` | Find string in memory |
| `rop` | Find ROP gadgets |
| `got` | Show GOT entries |
| `plt` | Show PLT entries |

## Step 2: Calculate Offset with Cyclic Pattern

### Generate Pattern

Using pwntools:

```python
from pwn import *
# Generate 200-byte cyclic pattern
print(cyclic(200))
```

Or in pwndbg:

```gdb
pwndbg> cyclic 200
```

### Find Offset from Crash

Run binary with pattern input, then check crash location:

```gdb
pwndbg> run < <(cyclic 200)
# After crash, check RSP or fault address
pwndbg> cyclic -l $rsp
# Or for specific value
pwndbg> cyclic -l 0x6161616c
```

### Pwntools Method

```python
from pwn import *

io = process('./binary')
io.sendline(cyclic(200))
io.wait()

# Check core dump or use gdb.attach()
# core = Coredump('./core')
# offset = cyclic_find(core.rsp)
```

## Step 3: Breakpoint Strategy

### Common Breakpoints

```gdb
# Function entry
b main
b vuln

# Specific address
b *0x401234

# Before dangerous function
b *gets@plt

# Before return
b *vuln+0x45  # Address of 'ret' instruction

# Conditional breakpoints
b *0x401234 if $rax == 0
```

### Breakpoint on Library Functions

```gdb
# Break on system() calls
b system
b execve

# Break on printf (format string analysis)
b printf
commands
    x/s $rdi    # Print format string (x64)
    continue
end
```

## Step 4: Examine Memory

### Stack Examination

```gdb
# Telescope view (pwndbg)
telescope $rsp 20

# Raw examine
x/20gx $rsp     # 20 quadwords from RSP
x/40wx $esp     # 40 words from ESP (32-bit)

# Examine as string
x/s $rdi

# Examine buffer
x/64bx $rbp-0x40
```

### Find Addresses

```gdb
# Binary base (if PIE)
vmmap
# Look for binary mapping, base is start address

# Libc base
vmmap libc
# Or
info proc mappings

# Stack canary location
canary    # pwndbg command
```

## Step 5: Bad Character Detection

Bad characters are bytes that break or mangle your payload during transmission or processing. Common bad chars include:
- `\x00` (null) - Terminates strings in C
- `\x0a` (newline) - Terminates input in many protocols
- `\x0d` (carriage return) - HTTP field terminator

### Generate All Characters

```python
# Generate all possible bytes (excluding null)
badchars = bytes(range(1, 256))
print(badchars.hex())
```

### Test Bad Characters

```python
from pwn import *

# All bytes except null
all_chars = bytes(range(1, 256))

io = process('./binary')
payload = b'A' * offset + all_chars
io.sendline(payload)
```

### Identify Bad Characters in GDB

After crash, examine memory where payload landed:

```gdb
# Find where chars start in memory
x/256bx $rsp

# Compare against expected sequence
# Look for truncation or mangled bytes
```

### Common Bad Characters by Context

| Protocol/Context | Common Bad Chars |
|-----------------|------------------|
| HTTP | `\x00`, `\x0a`, `\x0d`, `\x25`, `\x26`, `\x3d` |
| Sockets | `\x00`, `\x0a`, `\x0d` |
| strcpy/gets | `\x00` |
| File paths | `\x00`, `\x2f` |

### Pwntools Bad Char Helper

```python
def find_bad_chars(io, send_func, recv_func, offset):
    """Test for bad characters by sending all bytes"""
    all_chars = bytes(range(1, 256))
    send_func(io, b'A' * offset + all_chars)
    received = recv_func(io)
    # Compare and identify missing/changed bytes
```

## Step 6: Test Exploits

### Pwntools GDB Integration

```python
from pwn import *

context.binary = './binary'
context.terminal = ['tmux', 'splitw', '-h']

def conn():
    if args.GDB:
        return gdb.debug('./binary', '''
            b main
            b *vuln+0x45
            c
        ''')
    else:
        return process('./binary')

io = conn()
# Exploit code...
```

### Manual GDB Testing

```gdb
# Set up input file
pwndbg> shell echo -n 'AAAAAAAA...' > /tmp/payload

# Run with payload
pwndbg> run < /tmp/payload

# Or use Python
pwndbg> run < <(python3 -c "print('A'*72 + '\x34\x12\x40\x00\x00\x00\x00\x00')")
```

## Step 7: ASLR and PIE Analysis

### Disable ASLR for Testing

```bash
# System-wide (requires root)
echo 0 | sudo tee /proc/sys/kernel/randomize_va_space

# Per-process in GDB
set disable-randomization on
```

### Leak PIE Base

With format string:

```python
# Leak return address from stack
payload = b'%p ' * 20
io.sendline(payload)
leak = io.recvline()
# Parse to find code address, subtract known offset
```

### Leak Libc Base

```python
# Leak GOT entry (contains libc address)
puts_got = elf.got['puts']
# Use arbitrary read to leak puts@got
# libc_base = leaked_puts - libc.symbols['puts']
```

## GDB Scripts for pwndbg

### Project .gdbinit Template

```gdb
# Disable ASLR
set disable-randomization on

# Load binary
file ./binary

# Common breakpoints
b main
b vuln

# Define useful commands
define hook-stop
    context
end

# Print useful info on run
define pwn-info
    checksec
    got
    vmmap
end
```

## Output Format

```
## Dynamic Analysis

### Findings
- Offset to RIP: 72 bytes (confirmed via cyclic)
- RSP control: Full (can place ROP chain)
- Stack canary: Not present
- ASLR: Enabled (need leak for libc)
- PIE: Disabled (binary at 0x400000)

### Debug Session
```
pwndbg> cyclic -l $rsp
Finding cyclic pattern of 8 bytes: b'haaaaaaa' (hex: 0x6161616161616168)
Found at offset 72
```

### Implications
- 72-byte padding confirmed
- Direct ROP to fixed addresses possible
- For ret2libc: need to leak libc address first

### Next Steps
1. Find ROP gadgets for ret2libc
2. Construct leak payload (puts GOT)
3. Calculate libc base from leak
4. Build system("/bin/sh") payload
```

## Quick Reference

```python
# Pwntools offset finder
from pwn import *
io = process('./binary')
io.sendline(cyclic(200))
io.wait()
# Check crash, find offset with cyclic_find()
```

```gdb
# Quick crash analysis
r < <(cyclic 200)
cyclic -l $rsp
```

## Additional Resources

### References

- **`references/pwndbg-commands.md`** - Complete pwndbg command reference
- **`references/gdb-scripting.md`** - Advanced GDB scripting for exploitation

### Scripts

- **`scripts/gdb-template.gdb`** - Project .gdbinit template
