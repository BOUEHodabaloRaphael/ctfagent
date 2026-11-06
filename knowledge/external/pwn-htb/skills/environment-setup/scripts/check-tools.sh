#!/bin/bash
# Check for required pwn tools
# Usage: ./check-tools.sh

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== PWN Tools Verification ==="
echo ""

check_command() {
    local name="$1"
    local cmd="$2"
    local install_hint="$3"

    if eval "$cmd" &>/dev/null; then
        echo -e "${GREEN}[OK]${NC} $name"
        return 0
    else
        echo -e "${RED}[MISSING]${NC} $name - $install_hint"
        return 1
    fi
}

check_python_module() {
    local name="$1"
    local module="$2"
    local install_hint="$3"

    if python3 -c "import $module" &>/dev/null; then
        echo -e "${GREEN}[OK]${NC} $name"
        return 0
    else
        echo -e "${RED}[MISSING]${NC} $name - $install_hint"
        return 1
    fi
}

missing=0

echo "--- Core Tools ---"
check_command "Python 3" "python3 --version" "Install Python 3.8+" || ((missing++))
check_command "GDB" "gdb --version" "apt install gdb" || ((missing++))
check_python_module "pwntools" "pwn" "pip install pwntools" || ((missing++))
check_command "checksec" "checksec --version 2>/dev/null || python3 -c 'from pwn import *; checksec'" "pip install pwntools" || ((missing++))

echo ""
echo "--- Recommended Tools ---"
check_python_module "ROPgadget" "ROPGadget" "pip install ROPgadget" || ((missing++))
check_python_module "ropper" "ropper" "pip install ropper" || ((missing++))
check_command "one_gadget" "one_gadget --version" "gem install one_gadget" || ((missing++))
check_command "seccomp-tools" "seccomp-tools --version" "gem install seccomp-tools" || ((missing++))
check_command "radare2" "r2 -v" "apt install radare2" || ((missing++))
check_command "objdump" "objdump --version" "apt install binutils" || ((missing++))
check_command "readelf" "readelf --version" "apt install binutils" || ((missing++))

echo ""
echo "--- GDB Extensions ---"
if gdb -q -ex "python import pwndbg" -ex "quit" &>/dev/null; then
    echo -e "${GREEN}[OK]${NC} pwndbg"
elif gdb -q -ex "python import gef" -ex "quit" &>/dev/null; then
    echo -e "${YELLOW}[ALT]${NC} gef (pwndbg preferred)"
else
    echo -e "${RED}[MISSING]${NC} pwndbg - git clone https://github.com/pwndbg/pwndbg && cd pwndbg && ./setup.sh"
    ((missing++))
fi

echo ""
echo "=== Summary ==="
if [ $missing -eq 0 ]; then
    echo -e "${GREEN}All tools available!${NC}"
    exit 0
else
    echo -e "${YELLOW}$missing tool(s) missing or need attention${NC}"
    exit 1
fi
