---
name: pwn-gdbinit
description: Generate project-specific .gdbinit file for pwndbg debugging
argument-hint: "<binary> [--breakpoints func1,func2]"
allowed-tools: ["Bash", "Read", "Write"]
---

# PWN GDBInit - Generate GDB Configuration

Create a project-specific .gdbinit file optimized for pwndbg exploitation.

## Execution Steps

### Step 1: Analyze Binary

```bash
file <binary>
nm <binary> 2>/dev/null | head -20
```

Identify key functions for breakpoints.

### Step 2: Generate .gdbinit

Create `.gdbinit` in current directory with:
- ASLR disabled
- Common breakpoints
- Useful pwndbg commands
- Custom helpers

## Generated .gdbinit

```gdb
# ===========================================
# PWN Challenge GDB Configuration
# Target: <binary>
# Generated for pwndbg
# ===========================================

# === BASIC SETUP ===
set disable-randomization on
set follow-fork-mode child
set pagination off

# Load target binary
file ./<binary>

# === BREAKPOINTS ===
# Main entry
b main

# Vulnerable function (update as needed)
# b vuln
# b *vuln+0x30  # Before ret

# Library functions
# b *gets@plt
# b *printf@plt
# b *system@plt

# === CUSTOM COMMANDS ===

# Show useful info
define pwn-info
    echo \n=== Binary Info ===\n
    checksec
    echo \n=== Memory Map ===\n
    vmmap
    echo \n=== GOT Entries ===\n
    got
end

# Examine stack around RSP
define pwn-stack
    echo \n=== Stack ===\n
    telescope $rsp 20
end

# Examine heap (if applicable)
define pwn-heap
    echo \n=== Heap ===\n
    heap
    bins
end

# Find offset from cyclic pattern
define pwn-offset
    echo \n=== Cyclic Offset ===\n
    cyclic -l $rsp
end

# Run with pattern input
define pwn-pattern
    shell python3 -c "from pwn import *; open('/tmp/pattern','wb').write(cyclic(200))"
    run < /tmp/pattern
end

# === HOOKS ===

# Show context on every stop
define hook-stop
    context
end

# === ALIASES ===
alias pinfo = pwn-info
alias pstack = pwn-stack
alias pheap = pwn-heap
alias poff = pwn-offset
alias ppat = pwn-pattern

# === STARTUP ===
echo \n[*] PWN GDB config loaded\n
echo [*] Commands: pinfo, pstack, pheap, poff, ppat\n
echo [*] Run 'ppat' to test with cyclic pattern\n\n
```

## Usage

```bash
# Start GDB with config
gdb -q ./binary
# Config auto-loads from .gdbinit

# Or specify explicitly
gdb -q -x .gdbinit ./binary

# Commands available:
# pinfo  - Show checksec, vmmap, got
# pstack - Telescope RSP
# pheap  - Show heap state
# poff   - Find cyclic offset from crash
# ppat   - Run with cyclic pattern
```

## Breakpoint Tips

```gdb
# Break on function entry
b function_name

# Break at specific address
b *0x401234

# Break at offset from function
b *main+0x50

# Conditional breakpoint
b *0x401234 if $rax == 0

# Temporary breakpoint (one-time)
tb main

# Break on library function
b puts
b system
```
