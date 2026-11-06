#!/bin/bash
# Full Reconnaissance Script
# Runs complete recon suite on a binary
# Usage: ./full-recon.sh <binary>

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

if [ $# -lt 1 ]; then
    echo "Usage: $0 <binary> [libc]"
    exit 1
fi

BINARY="$1"
LIBC="${2:-}"

if [ ! -f "$BINARY" ]; then
    echo -e "${RED}Error: Binary '$BINARY' not found${NC}"
    exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      PWN RECONNAISSANCE REPORT         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Target:${NC} $BINARY"
echo -e "${YELLOW}Date:${NC} $(date)"
echo ""

# File information
echo -e "${GREEN}[*] File Information${NC}"
echo "────────────────────────────────────────"
file "$BINARY"
echo ""

# Checksec
echo -e "${GREEN}[*] Security Protections${NC}"
echo "────────────────────────────────────────"
if command -v checksec &>/dev/null; then
    checksec --file="$BINARY" 2>/dev/null || python3 -c "from pwn import *; print(ELF('$BINARY', checksec=False).checksec())" 2>/dev/null
elif python3 -c "from pwn import *" &>/dev/null; then
    python3 -c "from pwn import *; print(ELF('$BINARY', checksec=False).checksec())"
else
    echo "checksec not available"
fi
echo ""

# Symbols
echo -e "${GREEN}[*] Interesting Symbols${NC}"
echo "────────────────────────────────────────"
if nm "$BINARY" &>/dev/null; then
    nm "$BINARY" 2>/dev/null | grep -iE '(main|win|flag|shell|vuln|backdoor|secret|system|exec)' || echo "No notable symbols found (may be stripped)"
else
    echo "Binary is stripped"
fi
echo ""

# Dangerous functions
echo -e "${GREEN}[*] Dangerous Functions (PLT)${NC}"
echo "────────────────────────────────────────"
objdump -d "$BINARY" 2>/dev/null | grep -E '@plt>:' | grep -iE '(gets|strcpy|strcat|sprintf|scanf|printf|read|write|system|exec)' || echo "None found"
echo ""

# Interesting strings
echo -e "${GREEN}[*] Interesting Strings${NC}"
echo "────────────────────────────────────────"
strings -n 6 "$BINARY" 2>/dev/null | grep -iE '(flag|password|secret|admin|shell|/bin|key|token|hack|win)' | head -20 || echo "None found"
echo ""

# Format string indicators
echo -e "${GREEN}[*] Format String Indicators${NC}"
echo "────────────────────────────────────────"
strings "$BINARY" 2>/dev/null | grep -E '%[0-9]*\$?[sxnp]' | head -10 || echo "None found"
echo ""

# GOT/PLT entries
echo -e "${GREEN}[*] GOT/PLT Entries${NC}"
echo "────────────────────────────────────────"
objdump -R "$BINARY" 2>/dev/null | head -30 || readelf -r "$BINARY" 2>/dev/null | head -30
echo ""

# If libc provided
if [ -n "$LIBC" ] && [ -f "$LIBC" ]; then
    echo -e "${GREEN}[*] Libc Information${NC}"
    echo "────────────────────────────────────────"
    file "$LIBC"
    strings "$LIBC" | grep -E "GNU C Library" | head -1
    md5sum "$LIBC"
    echo ""
fi

# ROP gadgets preview
echo -e "${GREEN}[*] ROP Gadgets Preview${NC}"
echo "────────────────────────────────────────"
if command -v ROPgadget &>/dev/null; then
    ROPgadget --binary "$BINARY" 2>/dev/null | grep -E "pop (rdi|rsi|rdx|rax)" | head -5 || echo "No common gadgets found"
    ROPgadget --binary "$BINARY" 2>/dev/null | grep -E "syscall|int 0x80" | head -3 || true
else
    echo "ROPgadget not installed"
fi
echo ""

# Seccomp check
echo -e "${GREEN}[*] Seccomp Filter Check${NC}"
echo "────────────────────────────────────────"
if command -v seccomp-tools &>/dev/null; then
    timeout 2 seccomp-tools dump "$BINARY" 2>/dev/null || echo "No seccomp filter detected (or binary requires input)"
else
    # Check for seccomp in strings
    if strings "$BINARY" | grep -qi seccomp; then
        echo "Seccomp references found in binary (install seccomp-tools for analysis)"
    else
        echo "No obvious seccomp usage detected"
    fi
fi
echo ""

# Summary
echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║            RECON SUMMARY               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"

# Parse checksec output for summary
echo -e "${YELLOW}Protection Analysis:${NC}"
if python3 -c "from pwn import *; e=ELF('$BINARY',checksec=False); print('RELRO:',e.checksec()['RELRO'])" 2>/dev/null; then
    python3 << EOF
from pwn import *
context.log_level = 'error'
e = ELF('$BINARY', checksec=False)
c = e.checksec()

relro = c.get('RELRO', 'Unknown')
canary = c.get('Canary', 'Unknown')
nx = c.get('NX', 'Unknown')
pie = c.get('PIE', 'Unknown')

print(f"  RELRO:  {relro}")
print(f"  Canary: {canary}")
print(f"  NX:     {nx}")
print(f"  PIE:    {pie}")

# Suggest techniques
print("\n\033[1;33mSuggested Techniques:\033[0m")
if relro == 'Partial':
    print("  - GOT overwrite possible")
if canary == 'No':
    print("  - Direct buffer overflow to return address")
if nx == 'Disabled':
    print("  - Shellcode injection possible")
if pie == 'No':
    print("  - Fixed addresses, direct ROP possible")
if canary != 'No' and 'Yes' in str(canary):
    print("  - Need to leak or bypass canary")
if pie != 'No' and 'PIE' in str(pie):
    print("  - Need to leak binary base address")
EOF
fi

echo ""
echo -e "${GREEN}Recon complete!${NC}"
