---
name: pwn-recon
description: Run reconnaissance phase on a binary - checksec, file analysis, strings, symbols
argument-hint: "<binary>"
allowed-tools: ["Bash", "Read", "Grep"]
---

# PWN Recon - Binary Reconnaissance

Execute the reconnaissance phase on a target binary to gather essential information before exploitation.

## Execution Steps

### Step 1: Validate Binary

```bash
file <binary>
```

Verify binary exists and is an ELF executable.

### Step 2: Check Protections

```bash
checksec --file=<binary>
```

Or via Python if checksec not available:

```bash
python3 -c "from pwn import *; print(ELF('<binary>').checksec())"
```

Document all protections: RELRO, Canary, NX, PIE, FORTIFY.

### Step 3: Extract Strings

```bash
strings -n 8 <binary> | head -50
strings <binary> | grep -iE '(flag|password|secret|admin|shell|/bin|system)'
```

### Step 4: Analyze Symbols

```bash
# If not stripped
nm <binary> 2>/dev/null | grep -E ' [TtWw] ' | head -30

# Check for win functions
nm <binary> 2>/dev/null | grep -iE '(win|flag|shell|backdoor)'

# PLT entries
objdump -d <binary> | grep '@plt>:' | head -20
```

### Step 5: Check for Seccomp

```bash
seccomp-tools dump <binary> 2>/dev/null || echo "No seccomp or seccomp-tools not installed"
```

## Output Format

```
## Reconnaissance

### Findings
- Architecture: ELF 64-bit LSB executable, x86-64
- Linking: dynamically linked
- Stripped: No (symbols available)
- Protections:
  - RELRO: Partial
  - Stack Canary: No
  - NX: Enabled
  - PIE: Disabled
- Interesting strings: "/bin/sh", "flag.txt"
- Key symbols: main, vuln, win
- Dangerous PLT: gets@plt, printf@plt

### Commands Run
- `file ./binary` → ELF 64-bit LSB executable...
- `checksec --file=./binary` → [output]
- `strings ./binary | grep flag` → flag.txt

### Implications
- No PIE: Fixed addresses for ROP
- No Canary: Direct buffer overflow possible
- NX enabled: Cannot execute stack shellcode
- gets@plt: Likely buffer overflow vector
- win function: Possible ret2win target

### Next Steps
1. Disassemble vuln() to find buffer size
2. Disassemble win() to understand requirements
3. Calculate offset to return address
```
