# PWN Troubleshooting Guide

Common issues and solutions during binary exploitation.

## Binary Execution Issues

### "Permission denied"
```bash
chmod +x ./binary
```

### "No such file or directory" (on ELF)
Usually wrong architecture or missing interpreter:
```bash
# Check architecture
file ./binary
# ELF 32-bit... -> Need 32-bit libs

# Install 32-bit support
sudo dpkg --add-architecture i386
sudo apt update
sudo apt install libc6:i386

# Or wrong interpreter
patchelf --set-interpreter /lib64/ld-linux-x86-64.so.2 ./binary
```

### Segfault Before Main
```bash
# Check for missing libraries
ldd ./binary

# Set correct libc
patchelf --set-interpreter ./ld-linux-x86-64.so.2 ./binary
patchelf --set-rpath . ./binary
LD_PRELOAD=./libc.so.6 ./binary
```

## GDB Issues

### "ptrace: Operation not permitted"
```bash
# Temporary fix
echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope

# Permanent fix
sudo nano /etc/sysctl.d/10-ptrace.conf
# Set: kernel.yama.ptrace_scope = 0
```

### GDB Not Attaching from pwntools
```python
# Set correct terminal
context.terminal = ['tmux', 'splitw', '-h']
# or for gnome
context.terminal = ['gnome-terminal', '--', 'bash', '-c']
# or for iTerm2 on mac
context.terminal = ['osascript', '-e', 'tell app "iTerm" to ...']
```

### Symbols Not Loading
```bash
# In GDB
set debug-file-directory /usr/lib/debug
directory /path/to/source

# For libc
set solib-search-path /path/to/libc/
```

### pwndbg/GEF Not Loading
```bash
# Check .gdbinit
cat ~/.gdbinit

# Should contain something like:
# source ~/pwndbg/gdbinit.py

# Reload
gdb -nx -x ~/.gdbinit ./binary
```

## pwntools Issues

### Connection Timeout
```python
# Increase timeout
io = remote('target', 1337, timeout=30)

# Check connectivity first
import socket
s = socket.socket()
s.connect(('target', 1337))
s.close()
```

### "Could not find module"
```bash
# Reinstall pwntools
pip3 uninstall pwntools
pip3 install pwntools

# Or in virtualenv
python3 -m venv pwn-env
source pwn-env/bin/activate
pip install pwntools
```

### ELF Load Warnings
```python
# Disable checksec on load for speed
elf = ELF('./binary', checksec=False)

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')
```

### Wrong Architecture Context
```python
# Explicitly set
context.arch = 'amd64'
context.os = 'linux'

# Or from binary
context.binary = ELF('./binary')
```

## Exploit Issues

### Payload Works Locally, Fails Remote

1. **Different libc version**
```python
# Find remote libc
# Leak addresses, use libc-database
```

2. **ASLR differences**
```bash
# Local ASLR
cat /proc/sys/kernel/randomize_va_space
# 0 = off, 2 = full

# Disable for testing
echo 0 | sudo tee /proc/sys/kernel/randomize_va_space
```

3. **Environment differences**
```python
# Remove env vars that change stack layout
env = {}
io = process('./binary', env=env)
```

4. **Timing issues**
```python
# Add delays
io.sendline(payload)
sleep(0.1)
io.recv()
```

### SIGSEGV on movaps (x64)
Stack not 16-byte aligned:
```python
# Add ret gadget before function call
ret = elf.search(asm('ret')).__next__()
payload = b'A' * offset
payload += p64(ret)  # Alignment
payload += p64(target)
```

### Shell Spawns But Dies Immediately
```python
# Use interactive mode
io.interactive()

# Or keep stdin open
io.sendline(b'cat flag.txt')
print(io.recvall())
```

### "Got EOF while reading"
```python
# Binary crashed - debug with GDB
io = gdb.debug('./binary', 'b main\nc')

# Or add error handling
try:
    io.recv()
except EOFError:
    print("Connection closed")
```

## Shellcode Issues

### Bad Characters Breaking Payload
```python
# Test for bad chars
def find_bad_chars(io):
    for b in range(256):
        test = bytes([b])
        io.send(test)
        resp = io.recv()
        if test not in resp:
            print(f"Bad char: {hex(b)}")

# Use encoder
from pwn import *
shellcode = asm(shellcraft.sh())
encoded = encode(shellcode, avoid=b'\x00\x0a\x0d')
```

### Shellcode Too Long
```python
# Use shorter shellcode
# x64 execve - 23 bytes
shellcode = asm('''
    xor rsi, rsi
    push rsi
    mov rdi, 0x68732f2f6e69622f
    push rdi
    push rsp
    pop rdi
    push 59
    pop rax
    cdq
    syscall
''')
```

## Heap Issues

### Heap Corruption Detected
```bash
# Debug with MALLOC_CHECK_
MALLOC_CHECK_=3 ./binary

# In GDB
set environment MALLOC_CHECK_=3
```

### Can't Find Heap Base
```python
# Leak from unsorted bin
alloc(0, 0x420)
alloc(1, 0x20)  # Guard
free(0)
leak = read(0)  # UAF
heap_base = leak - offset
```

## Libc Issues

### "version `GLIBC_X.XX' not found"
Use patchelf:
```bash
patchelf --set-interpreter ./ld-2.31.so ./binary
patchelf --set-rpath . ./binary
```

### Multiple Libc Matches
Leak more functions:
```python
# Leak puts AND printf
puts_leak = leak_got('puts')
printf_leak = leak_got('printf')
# Use both for identification
```

## Network Issues

### "Connection refused"
- Check if service is running
- Verify port number
- Check firewall

### Unstable Connection
```python
# Retry logic
for _ in range(3):
    try:
        io = remote('target', 1337)
        # exploit
        break
    except:
        sleep(1)
```

## General Debugging Tips

1. **Add logging**
```python
context.log_level = 'debug'
```

2. **Save core dumps**
```bash
ulimit -c unlimited
./binary
# Core dumped to ./core
gdb ./binary ./core
```

3. **Test incrementally**
```python
# Test each stage
io.sendline(stage1)
io.interactive()  # Check state
# Then add stage2
```

4. **Compare local vs remote**
```python
# Log all I/O
io = process('./binary')
io = remote('target', 1337)
# Compare recv outputs
```
