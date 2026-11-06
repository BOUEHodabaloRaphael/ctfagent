# pwndbg Command Reference

Essential pwndbg commands for binary exploitation.

## Setup

### Installation
```bash
git clone https://github.com/pwndbg/pwndbg
cd pwndbg
./setup.sh
```

### Launch with pwntools
```python
io = gdb.debug('./binary', '''
b main
c
''')
```

## Context Display

### context
Shows registers, disassembly, stack, backtrace automatically on stop.

```
pwndbg> context
# Displays full context

pwndbg> set context-sections regs disasm stack backtrace
# Customize which sections to show
```

## Memory Examination

### hexdump
```
pwndbg> hexdump $rsp 64
# Dump 64 bytes from RSP

pwndbg> hexdump 0x404000 128
# Dump from specific address
```

### telescope / tel
```
pwndbg> telescope $rsp 20
# Show stack with dereferencing (shows what pointers point to)

pwndbg> tel $rsp 10
# Shorthand
```

### search
```
pwndbg> search "/bin/sh"
# Find string in memory

pwndbg> search -x 0xdeadbeef
# Search for hex value

pwndbg> search -p 0x7fff
# Search for pointer pattern
```

## Heap Commands

### heap
```
pwndbg> heap
# Show all heap chunks

pwndbg> heap -v
# Verbose output
```

### bins
```
pwndbg> bins
# Show all free bins (fastbins, tcache, unsorted, small, large)

pwndbg> fastbins
pwndbg> tcachebins
pwndbg> unsortedbin
pwndbg> smallbins
pwndbg> largebins
```

### vis_heap_chunks
```
pwndbg> vis_heap_chunks
# Visual representation of heap

pwndbg> vis 0x555555559000 10
# Show 10 chunks starting at address
```

### malloc_chunk
```
pwndbg> malloc_chunk 0x555555559290
# Parse chunk at address
```

### arena
```
pwndbg> arena
# Show main_arena info

pwndbg> arenas
# Show all arenas
```

## Exploitation Helpers

### checksec
```
pwndbg> checksec
# Show binary protections
```

### rop
```
pwndbg> rop
# Find ROP gadgets in binary

pwndbg> rop --grep "pop rdi"
# Filter gadgets
```

### got
```
pwndbg> got
# Show GOT entries and their values
```

### plt
```
pwndbg> plt
# Show PLT entries
```

### canary
```
pwndbg> canary
# Show stack canary value
```

### vmmap
```
pwndbg> vmmap
# Show memory mappings (permissions, addresses)

pwndbg> vmmap libc
# Filter for libc
```

### procinfo
```
pwndbg> procinfo
# Show process info (pid, etc.)
```

## Breakpoints

### break
```
pwndbg> b main
pwndbg> b *0x401234
pwndbg> b *vuln+42
```

### Conditional breakpoints
```
pwndbg> b *0x401234 if $rax == 0
```

### Watch
```
pwndbg> watch *0x404040
# Break when memory changes

pwndbg> rwatch *0x404040
# Break on read
```

## Cyclic Pattern

### cyclic
```
pwndbg> cyclic 100
# Generate pattern

pwndbg> cyclic -l 0x61616168
# Find offset (lookup)
```

## Disassembly

### nearpc / disasm
```
pwndbg> nearpc 20
# Disassemble 20 instructions near PC

pwndbg> u main 50
# Disassemble 50 instructions from main
```

### pdisass
```
pwndbg> pdisass main
# Disassemble entire function
```

## Registers

### regs
```
pwndbg> regs
# Show all registers

pwndbg> regs rax rbx
# Show specific registers
```

### set
```
pwndbg> set $rax = 0x1234
# Modify register
```

## Execution

### nextcall
```
pwndbg> nextcall
# Continue until next call instruction
```

### nextret
```
pwndbg> nextret
# Continue until next ret instruction
```

### stepret
```
pwndbg> stepret
# Step until current function returns
```

## Tips

### Disable ASLR
```
pwndbg> set disable-randomization on
```

### Follow fork
```
pwndbg> set follow-fork-mode child
```

### Logging
```
pwndbg> set logging on
pwndbg> set logging file output.txt
```

### Useful .gdbinit
```gdb
set disable-randomization on
set follow-fork-mode child
set context-sections regs disasm stack
```
