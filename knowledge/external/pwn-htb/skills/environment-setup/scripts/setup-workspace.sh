#!/bin/bash
# PWN Workspace Setup Script
# Creates a standardized workspace for binary exploitation
# Usage: ./setup-workspace.sh <challenge-name> [binary]

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

if [ $# -lt 1 ]; then
    echo "Usage: $0 <challenge-name> [binary-path]"
    echo "Example: $0 pwn_challenge ./vuln"
    exit 1
fi

CHALLENGE_NAME="$1"
BINARY="${2:-}"

echo -e "${BLUE}Setting up PWN workspace: ${CHALLENGE_NAME}${NC}"
echo ""

# Create directory structure
mkdir -p "$CHALLENGE_NAME"/{core,libc,notes}
cd "$CHALLENGE_NAME"

echo -e "${GREEN}[+] Created directory structure${NC}"
echo "    $CHALLENGE_NAME/"
echo "    ├── core/       (for core dumps)"
echo "    ├── libc/       (for libc files)"
echo "    └── notes/      (for analysis notes)"

# Copy binary if provided
if [ -n "$BINARY" ] && [ -f "$BINARY" ]; then
    cp "$BINARY" ./
    BINARY_NAME=$(basename "$BINARY")
    chmod +x "./$BINARY_NAME"
    echo -e "${GREEN}[+] Copied binary: $BINARY_NAME${NC}"
fi

# Create exploit template
cat > exploit.py << 'EXPLOIT_EOF'
#!/usr/bin/env python3
"""
Exploit for: CHALLENGE_NAME
Author:
Date: DATE_PLACEHOLDER
"""
from pwn import *

# === CONFIGURATION ===
BINARY = './binary'  # TODO: Update binary name
LIBC = './libc/libc.so.6'  # If provided
OFFSET = 0  # TODO: Find offset with cyclic pattern

HOST = 'target.htb'
PORT = 1337

# === SETUP ===
context.log_level = 'info'

if os.path.exists(BINARY):
    elf = ELF(BINARY)
    context.binary = elf

if os.path.exists(LIBC):
    libc = ELF(LIBC)
else:
    libc = elf.libc if 'elf' in dir() else None

def conn():
    if args.REMOTE:
        return remote(HOST, PORT)
    elif args.GDB:
        gdbscript = '''
        b main
        c
        '''
        return gdb.debug(BINARY, gdbscript)
    else:
        return process(BINARY)

def main():
    io = conn()

    # TODO: Implement exploit
    # 1. Leak addresses if needed
    # 2. Build payload
    # 3. Send and get shell

    io.interactive()

if __name__ == '__main__':
    main()
EXPLOIT_EOF

# Replace placeholders
sed -i.bak "s/CHALLENGE_NAME/$CHALLENGE_NAME/g" exploit.py 2>/dev/null || sed -i '' "s/CHALLENGE_NAME/$CHALLENGE_NAME/g" exploit.py
sed -i.bak "s/DATE_PLACEHOLDER/$(date +%Y-%m-%d)/g" exploit.py 2>/dev/null || sed -i '' "s/DATE_PLACEHOLDER/$(date +%Y-%m-%d)/g" exploit.py
rm -f exploit.py.bak

chmod +x exploit.py
echo -e "${GREEN}[+] Created exploit.py${NC}"

# Create GDB init file
cat > .gdbinit << 'GDB_EOF'
# Project-specific GDB configuration
# Disable ASLR for local testing
set disable-randomization on

# Follow child on fork
set follow-fork-mode child

# Useful settings
set print pretty on
set print array on

# Common breakpoints (uncomment as needed)
# b main
# b *vuln
# b *0x401234

# Define useful commands
define hook-stop
    # Uncomment for auto context
    # context
end

# Auto-load binary (update name)
# file ./binary
GDB_EOF
echo -e "${GREEN}[+] Created .gdbinit${NC}"

# Create notes template
cat > notes/analysis.md << 'NOTES_EOF'
# Challenge Analysis

## Overview
- **Name**: CHALLENGE_NAME
- **Category**: PWN
- **Points**:
- **Difficulty**:

## Binary Information
```
file ./binary
checksec --file=./binary
```

## Protections
- RELRO:
- Stack Canary:
- NX:
- PIE:

## Vulnerability
<!-- Describe the vulnerability found -->

## Exploitation Strategy
<!-- Step by step exploitation plan -->

1.
2.
3.

## Key Addresses
```
win function: 0x
buffer:       0x
offset:
```

## Payload Structure
```
[padding] + [gadgets/addresses] + [shellcode if needed]
```

## Notes
<!-- Additional observations -->

## Flag
```
HTB{...}
```
NOTES_EOF

sed -i.bak "s/CHALLENGE_NAME/$CHALLENGE_NAME/g" notes/analysis.md 2>/dev/null || sed -i '' "s/CHALLENGE_NAME/$CHALLENGE_NAME/g" notes/analysis.md
rm -f notes/analysis.md.bak
echo -e "${GREEN}[+] Created notes/analysis.md${NC}"

# Create solve script template
cat > solve.py << 'SOLVE_EOF'
#!/usr/bin/env python3
"""
Clean solution script (for submission/writeup)
"""
from pwn import *

BINARY = './binary'
HOST = 'target.htb'
PORT = 1337

context.binary = ELF(BINARY)

def exploit(io):
    # Clean exploit code here
    pass

if __name__ == '__main__':
    if args.REMOTE:
        io = remote(HOST, PORT)
    else:
        io = process(BINARY)

    exploit(io)
    io.interactive()
SOLVE_EOF
chmod +x solve.py
echo -e "${GREEN}[+] Created solve.py (clean solution)${NC}"

# Enable core dumps
ulimit -c unlimited 2>/dev/null || true

echo ""
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        Workspace Ready!                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Directory: $(pwd)${NC}"
echo ""
echo "Files created:"
echo "  exploit.py  - Main exploit script"
echo "  solve.py    - Clean solution script"
echo "  .gdbinit    - GDB configuration"
echo "  notes/      - Analysis notes"
echo ""
echo "Next steps:"
echo "  1. Copy binary to this directory"
echo "  2. Run ./full-recon.sh <binary>"
echo "  3. Update exploit.py with findings"
echo "  4. python3 exploit.py        # Local test"
echo "  5. python3 exploit.py GDB    # Debug"
echo "  6. python3 exploit.py REMOTE # Remote"
