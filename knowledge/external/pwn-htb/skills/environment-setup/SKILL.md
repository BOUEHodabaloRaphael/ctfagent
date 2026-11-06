---
name: PWN Environment Setup
description: This skill should be used when the user asks to "setup pwn environment", "install pwntools", "check pwn tools", "verify exploitation tools", "create exploit workspace", "initialize pwn project", or needs to verify binary exploitation tool availability. Provides guidance for detecting, installing, and configuring pwn tools.
version: 1.0.0
---

# PWN Environment Setup

## Overview

This skill provides methodology for setting up a complete binary exploitation environment, including tool detection, automatic installation of missing dependencies, and workspace organization for exploit development.

## Required Tools

### Core Tools (Must Have)

| Tool | Purpose | Installation |
|------|---------|--------------|
| pwntools | Exploit development framework | `pip install pwntools` |
| gdb | Debugger | System package manager |
| pwndbg | GDB enhancement | `git clone https://github.com/pwndbg/pwndbg` |
| checksec | Binary protection checker | Via pwntools or `apt install checksec` |

### Recommended Tools

| Tool | Purpose | Installation |
|------|---------|--------------|
| ROPgadget | ROP gadget finder | `pip install ROPgadget` |
| ropper | Alternative gadget finder | `pip install ropper` |
| one_gadget | Libc one-shot gadgets | `gem install one_gadget` |
| seccomp-tools | Seccomp filter analyzer | `gem install seccomp-tools` |
| radare2 | Disassembler/debugger | System package manager |

## Environment Verification Process

### Step 1: Check Python Environment

Verify Python 3.8+ is available:

```bash
python3 --version
```

Check if pwntools is installed and functional:

```bash
python3 -c "from pwn import *; print(f'pwntools {pwnlib.version.__version__}')"
```

### Step 2: Check GDB and Extensions

Verify GDB is installed:

```bash
gdb --version
```

Check for pwndbg by looking for its initialization:

```bash
gdb -q -ex "show configuration" -ex "quit" 2>&1 | grep -i pwndbg || echo "pwndbg not detected"
```

### Step 3: Check Binary Analysis Tools

Run the tool verification script at `${CLAUDE_PLUGIN_ROOT}/skills/environment-setup/scripts/check-tools.sh` to verify all tools.

### Step 4: Auto-Install Missing Python Packages

For missing Python packages, install via pip:

```bash
pip install pwntools ROPgadget ropper
```

For Ruby gems (one_gadget, seccomp-tools):

```bash
gem install one_gadget seccomp-tools
```

## Workspace Structure

Create a standard workspace for exploit development:

```
challenge-name/
├── exploit.py          # Main exploit script
├── solve.py            # Alternative/cleaned exploit
├── notes.md            # Analysis notes
├── core/               # Core dumps
├── libc/               # Libc files if provided
└── .gdbinit            # Project-specific GDB config
```

To create this structure:

```bash
mkdir -p challenge-name/{core,libc}
touch challenge-name/{exploit.py,notes.md,.gdbinit}
```

## GDB Configuration for pwndbg

Create a project-specific `.gdbinit`:

```gdb
# Load pwndbg if not auto-loaded
# source ~/pwndbg/gdbinit.py

# Disable ASLR for local testing
set disable-randomization on

# Follow child on fork (useful for some challenges)
set follow-fork-mode child

# Common breakpoints
# b main
# b *vuln_function

# Display useful info on stop
define hook-stop
    info registers
end
```

## Pwntools Context Setup

Initialize pwntools with correct context for the target:

```python
from pwn import *

# Auto-detect from binary
elf = ELF('./binary')
context.binary = elf

# Or manual specification
context.arch = 'amd64'  # or 'i386', 'arm', 'aarch64'
context.os = 'linux'
context.log_level = 'debug'  # 'info', 'warning', 'error'

# For shellcode
context.endian = 'little'
```

## Common Issues and Solutions

### Issue: pwntools not finding GDB

Ensure GDB is in PATH and pwntools can locate it:

```python
context.terminal = ['tmux', 'splitw', '-h']  # or ['gnome-terminal', '--']
```

### Issue: Permission denied on binary

Make binary executable:

```bash
chmod +x ./binary
```

### Issue: libc version mismatch

Use patchelf to set correct interpreter and libc:

```bash
patchelf --set-interpreter ./ld-linux.so.2 ./binary
patchelf --set-rpath . ./binary
```

## Output Format

When reporting environment status:

```
## Environment Setup

### Findings
- Python: 3.11.0
- pwntools: 4.11.0
- GDB: 13.2 with pwndbg
- Missing tools: one_gadget, seccomp-tools

### Actions Taken
- Installed ROPgadget via pip
- Created workspace structure

### Remaining Setup
- Install Ruby gems: gem install one_gadget seccomp-tools
- Configure GDB terminal for pwntools
```

## Additional Resources

### Scripts

- **`scripts/check-tools.sh`** - Verify all pwn tools are installed
- **`scripts/setup-workspace.sh`** - Create standard workspace structure

### References

- **`references/tool-installation.md`** - Detailed installation guides for each tool
- **`references/troubleshooting.md`** - Common setup issues and solutions
