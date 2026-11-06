# PWN Tool Installation Guide

Complete setup guide for binary exploitation environment.

## Core Tools

### Python 3 & pip
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-dev

# macOS
brew install python3

# Verify
python3 --version
pip3 --version
```

### pwntools
```bash
pip3 install pwntools

# Verify
python3 -c "from pwn import *; print(f'pwntools {pwnlib.version.__version__}')"
```

### GDB
```bash
# Ubuntu/Debian
sudo apt install gdb

# macOS (via Homebrew)
brew install gdb

# Verify
gdb --version
```

## GDB Extensions

### pwndbg (Recommended)
```bash
git clone https://github.com/pwndbg/pwndbg
cd pwndbg
./setup.sh

# Verify (in gdb)
# Should show pwndbg prompt and context
```

### GEF (Alternative)
```bash
# Install
bash -c "$(curl -fsSL https://gef.blah.cat/sh)"

# Or manual
wget -O ~/.gdbinit-gef.py https://gef.blah.cat/py
echo "source ~/.gdbinit-gef.py" >> ~/.gdbinit
```

### peda (Legacy)
```bash
git clone https://github.com/longld/peda.git ~/peda
echo "source ~/peda/peda.py" >> ~/.gdbinit
```

**Note**: Only use one GDB extension at a time.

## Analysis Tools

### ROPgadget
```bash
pip3 install ROPgadget

# Verify
ROPgadget --version
```

### ropper
```bash
pip3 install ropper

# Verify
ropper --version
```

### one_gadget (Ruby)
```bash
# Install Ruby first
sudo apt install ruby ruby-dev  # Ubuntu
brew install ruby                # macOS

# Install one_gadget
gem install one_gadget

# Verify
one_gadget --version
```

### seccomp-tools (Ruby)
```bash
gem install seccomp-tools

# Verify
seccomp-tools --version
```

### checksec
```bash
# Via apt
sudo apt install checksec

# Or via pwntools (included)
python3 -c "from pwn import *; print('checksec available')"
```

### radare2
```bash
# Ubuntu/Debian
sudo apt install radare2

# macOS
brew install radare2

# From source (latest)
git clone https://github.com/radareorg/radare2
cd radare2
sys/install.sh

# Verify
r2 -v
```

### Ghidra (Optional GUI)
```bash
# Download from https://ghidra-sre.org/
# Requires Java 11+

sudo apt install openjdk-11-jdk
# Extract and run: ./ghidraRun
```

## Binary Utilities

### binutils
```bash
sudo apt install binutils

# Provides: objdump, readelf, nm, strings, etc.
```

### file
```bash
sudo apt install file
```

### patchelf
```bash
sudo apt install patchelf

# For fixing libc/ld issues
```

## Network Tools

### netcat
```bash
sudo apt install netcat-openbsd
# or
sudo apt install ncat  # From nmap
```

### socat
```bash
sudo apt install socat
```

## Docker (For Environment Isolation)

```bash
# Ubuntu
sudo apt install docker.io
sudo usermod -aG docker $USER

# Run Ubuntu container for pwn
docker run -it --privileged ubuntu:20.04 /bin/bash
```

## libc Database

### Local Setup
```bash
git clone https://github.com/niklasb/libc-database
cd libc-database
./get ubuntu  # Download Ubuntu libcs
```

## Virtual Environment (Recommended)

```bash
# Create virtual environment for pwn tools
python3 -m venv ~/pwn-venv
source ~/pwn-venv/bin/activate

# Install tools
pip install pwntools ROPgadget ropper

# Add to .bashrc/.zshrc for auto-activation
echo 'alias pwn="source ~/pwn-venv/bin/activate"' >> ~/.bashrc
```

## Verification Script

Save as `check-pwn-env.sh`:
```bash
#!/bin/bash
echo "=== PWN Environment Check ==="

check() {
    if command -v $1 &>/dev/null || $2 &>/dev/null; then
        echo "[OK] $1"
    else
        echo "[MISSING] $1"
    fi
}

check "python3" "python3 --version"
check "gdb" "gdb --version"
check "ROPgadget" "ROPgadget --version"
check "one_gadget" "one_gadget --version"
check "checksec" "checksec --version"
check "r2" "r2 -v"
check "objdump" "objdump --version"

python3 -c "from pwn import *" 2>/dev/null && echo "[OK] pwntools" || echo "[MISSING] pwntools"
```

## Troubleshooting

### pwntools not finding GDB
```python
# Set terminal for GDB
context.terminal = ['tmux', 'splitw', '-h']
# or
context.terminal = ['gnome-terminal', '--']
```

### Permission Denied on Binary
```bash
chmod +x ./binary
```

### Wrong libc Version
```bash
patchelf --set-interpreter ./ld-linux-x86-64.so.2 ./binary
patchelf --set-rpath . ./binary
LD_PRELOAD=./libc.so.6 ./binary
```

### GDB ptrace Errors
```bash
echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope
```
