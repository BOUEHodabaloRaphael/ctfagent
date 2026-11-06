---
name: pwn-setup
description: Verify pwn tools installation and create exploit development workspace
argument-hint: "[--install]"
allowed-tools: ["Bash", "Write", "AskUserQuestion"]
---

# PWN Setup - Environment Verification

Verify binary exploitation tools are installed and optionally create a workspace structure.

## Execution Steps

### Step 1: Check Core Tools

Verify essential tools:

```bash
# Python and pwntools
python3 --version
python3 -c "from pwn import *; print(f'pwntools {pwnlib.version.__version__}')"

# GDB
gdb --version

# checksec
checksec --version 2>/dev/null || python3 -c "from pwn import *; print('checksec available via pwntools')"
```

### Step 2: Check Recommended Tools

Check additional tools:

```bash
# ROPgadget
python3 -c "import ROPGadget" && echo "ROPgadget: OK" || echo "ROPgadget: MISSING (pip install ROPgadget)"

# ropper
python3 -c "import ropper" && echo "ropper: OK" || echo "ropper: MISSING (pip install ropper)"

# one_gadget
which one_gadget && echo "one_gadget: OK" || echo "one_gadget: MISSING (gem install one_gadget)"

# seccomp-tools
which seccomp-tools && echo "seccomp-tools: OK" || echo "seccomp-tools: MISSING (gem install seccomp-tools)"
```

### Step 3: Check GDB Extensions

```bash
# Check for pwndbg
gdb -q -batch -ex "python import pwndbg; print('pwndbg: OK')" 2>/dev/null || echo "pwndbg: NOT DETECTED"
```

### Step 4: Auto-Install (if --install flag)

If `--install` flag provided and missing tools detected:

```bash
# Install Python packages
pip install pwntools ROPgadget ropper

# Ruby gems (inform user, don't auto-run)
echo "For Ruby tools, run: gem install one_gadget seccomp-tools"
```

### Step 5: Create Workspace (Optional)

Ask user if they want to create workspace structure:

```bash
mkdir -p challenge/{core,libc}
touch challenge/{exploit.py,notes.md,.gdbinit}
```

## Output Format

```
## Environment Setup

### Tool Status
| Tool | Status | Version |
|------|--------|---------|
| Python | OK | 3.11.0 |
| pwntools | OK | 4.11.0 |
| GDB | OK | 13.2 |
| pwndbg | OK | - |
| ROPgadget | OK | - |
| ropper | MISSING | - |
| one_gadget | OK | 2.1.0 |
| seccomp-tools | MISSING | - |

### Missing Tools
- ropper: `pip install ropper`
- seccomp-tools: `gem install seccomp-tools`

### Workspace
Not created (use --install to create)
```
