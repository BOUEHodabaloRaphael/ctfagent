---
name: pwn
description: Run full binary exploitation methodology - 5 phases with confirmations between each
argument-hint: "<binary> [--remote host:port] [--libc path]"
allowed-tools: ["Bash", "Read", "Write", "Glob", "Grep", "AskUserQuestion"]
---

# PWN - Full Exploitation Methodology

Execute the complete binary exploitation workflow on a target binary. This command runs through all 5 phases sequentially with confirmation between each phase.

## Workflow Phases

1. **Environment Setup** - Verify tools and create workspace
2. **Reconnaissance** - Binary analysis, protections, strings, symbols
3. **Static Analysis** - Disassembly, vulnerable functions, buffer sizes
4. **Dynamic Analysis** - GDB debugging, offset calculation, crash analysis
5. **Exploit Development** - Technique selection, payload construction

## Execution Steps

### Step 1: Parse Arguments

Extract binary path and optional arguments:
- `<binary>` - Required: Path to target binary
- `--remote host:port` - Optional: Remote target for final exploit
- `--libc path` - Optional: Path to libc file

If no binary specified, ask user to provide one.

### Step 2: Environment Verification

Before starting analysis:

1. Check binary exists and is executable:
   ```bash
   file <binary>
   ```

2. Verify essential tools are available:
   ```bash
   which gdb checksec python3
   python3 -c "from pwn import *"
   ```

3. Create workspace if needed:
   ```bash
   mkdir -p pwn_workspace
   ```

### Step 3: Execute Phases Sequentially

For each phase, use the corresponding skill and produce output in this format:

```
## [Phase Name]

### Findings
- Key observations as bullet points

### Commands Run
- Actual commands executed with relevant output

### Implications
- What findings mean for exploitation

### Next Steps
- Recommended actions
```

After each phase, ask user: "Phase complete. Continue to [next phase]?"

### Step 4: Phase-Specific Instructions

#### Phase 1: Environment Setup
- Load `environment-setup` skill
- Verify tools, report missing ones
- Auto-install missing pip packages if user approves

#### Phase 2: Reconnaissance
- Load `reconnaissance` skill
- Run: `file`, `checksec`, `strings`, `nm`
- Document architecture and protections

#### Phase 3: Static Analysis
- Load `static-analysis` skill
- Disassemble main and vulnerable functions
- Identify dangerous function calls
- Calculate buffer sizes from disassembly

#### Phase 4: Dynamic Analysis
- Load `dynamic-analysis` skill
- Generate GDB script for pwndbg
- Calculate offset using cyclic pattern
- Identify register control

#### Phase 5: Exploit Development
- Load `exploit-development` skill
- Select technique based on protections
- Generate pwntools exploit skeleton
- Include educational comments

### Step 5: Generate Final Exploit

After all phases, create complete exploit file:
- Save to `exploit.py` in current directory
- Include all calculated values
- Add local/remote toggle
- Add GDB attach functionality

## Output Format

Each phase produces structured output. Final summary includes:

```
## Exploitation Summary

### Target: ./binary

### Vulnerability
- Type: Buffer overflow via gets()
- Location: vuln() function
- Offset to RIP: 72 bytes

### Protections
- RELRO: Partial
- Stack Canary: No
- NX: Yes
- PIE: No

### Exploitation Technique
- Method: ret2libc
- Gadgets: pop rdi @ 0x401234
- Target: system("/bin/sh")

### Files Generated
- exploit.py - Main exploit script
- .gdbinit - GDB configuration
```

## Error Handling

- If binary not found: Ask user for correct path
- If tools missing: Offer to install or provide instructions
- If analysis fails: Report error and suggest manual steps
- If offset unclear: Offer to help with manual calculation
