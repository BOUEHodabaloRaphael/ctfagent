---
name: pwn-template
description: Generate pwntools exploit template - interactive selector for different exploit types
argument-hint: "[type]"
allowed-tools: ["Read", "Write", "AskUserQuestion"]
---

# PWN Template - Exploit Template Generator

Generate a pwntools exploit template for a specific exploitation technique.

## Execution Steps

### Step 1: Select Template Type

If no type argument provided, ask user to select:

Available templates:
1. **ret2win** - Simple return to win function
2. **ret2libc** - Return to libc with leak
3. **rop** - Generic ROP chain
4. **format-string** - Format string exploitation
5. **shellcode** - Shellcode injection
6. **got-overwrite** - GOT overwrite via write primitive
7. **heap** - Basic heap exploitation
8. **srop** - Sigreturn-oriented programming

### Step 2: Gather Required Information

Based on template type, ask for:

**All templates:**
- Binary name/path
- Offset to return address

**ret2win:**
- Win function address

**ret2libc:**
- Libc path (optional)
- pop_rdi gadget address

**format-string:**
- Format string offset
- Target address to write

**shellcode:**
- Buffer address (or leak method)

### Step 3: Generate Template

Read template from `${CLAUDE_PLUGIN_ROOT}/templates/<type>.py` and customize with provided values.

### Step 4: Save Template

Save customized template to `exploit.py` in current directory.

## Template Descriptions

### ret2win
Simple overflow to call existing win/flag function. Best when PIE disabled and win function exists.

### ret2libc
Two-stage attack: leak libc address, then call system("/bin/sh"). Requires gadgets and partial RELRO.

### rop
Generic ROP chain construction. For complex scenarios requiring multiple gadgets.

### format-string
Arbitrary read/write via printf vulnerability. Includes offset finder and payload generator.

### shellcode
Direct shellcode execution. Requires executable stack (NX disabled).

### got-overwrite
Overwrite GOT entry to redirect execution. Requires partial RELRO and write primitive.

### heap
Basic tcache/fastbin exploitation. Template for common heap scenarios.

### srop
Sigreturn-based exploitation. For minimal gadget scenarios.

## Output

Generated template includes:
- Full pwntools setup with context
- Local/remote/GDB connection toggle
- Commented explanation of each step
- Placeholder values clearly marked with `# TODO`
