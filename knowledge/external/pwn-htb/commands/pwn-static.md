---
name: pwn-static
description: Run static analysis phase - disassembly, vulnerable functions, buffer sizes
argument-hint: "<binary>"
allowed-tools: ["Bash", "Read", "Write"]
---

# PWN Static - Static Analysis

Perform static analysis on a binary to identify vulnerabilities through disassembly.

## Execution Steps

### Step 1: Disassemble Main Function

```bash
objdump -d -M intel <binary> | grep -A 50 '<main>:'
```

### Step 2: Identify and Disassemble Vulnerable Functions

First find interesting functions:

```bash
nm <binary> 2>/dev/null | grep -iE '(vuln|read_input|get_input|buffer)'
```

Then disassemble each:

```bash
objdump -d -M intel <binary> | grep -A 30 '<vuln>:'
```

### Step 3: Find Dangerous Function Calls

```bash
objdump -d <binary> | grep -E 'call.*<(gets|strcpy|sprintf|strcat|scanf|printf|read)@plt>'
```

### Step 4: Calculate Buffer Sizes

From disassembly, identify:
- Stack allocation: `sub rsp, 0xXX` or `sub esp, 0xXX`
- Buffer location: `lea rax, [rbp-0xXX]` or `lea eax, [ebp-0xXX]`

Calculate offset to return address:
- x86_64: buffer_offset + 8 (saved RBP) = offset to RIP
- x86: buffer_offset + 4 (saved EBP) = offset to EIP

### Step 5: Find Win Functions or Useful Gadgets

```bash
# Win functions
nm <binary> 2>/dev/null | grep -iE '(win|flag|shell|system)'

# Check if system@plt exists
objdump -d <binary> | grep '<system@plt>'

# Basic gadget search
objdump -d <binary> | grep -E '(ret$|pop.*ret)'
```

## Output Format

```
## Static Analysis

### Findings
- Vulnerability: Buffer overflow in vuln() via gets()
- Buffer: 64 bytes at [rbp-0x40]
- Offset to RIP: 72 bytes (64 + 8)
- Win function: 0x401234
- Dangerous calls:
  - gets@plt at 0x401186
  - printf@plt at 0x401190 (check if format string)

### Disassembly Highlights
```asm
0000000000401156 <vuln>:
  401156:    push   rbp
  401157:    mov    rbp,rsp
  40115a:    sub    rsp,0x40          ; 64 bytes
  40115e:    lea    rax,[rbp-0x40]    ; buffer start
  401162:    mov    rdi,rax
  401165:    call   401030 <gets@plt> ; VULNERABLE
  40116a:    nop
  40116b:    leave
  40116c:    ret
```

### Implications
- Direct ret2win: Overflow buffer (72 bytes) + win address
- Stack alignment may be needed (add ret gadget before win)
- No format string (printf has format specifier)

### Next Steps
1. Verify offset with cyclic pattern in GDB
2. Check win() function requirements (arguments?)
3. Craft payload: b'A'*72 + p64(0x401234)
```
