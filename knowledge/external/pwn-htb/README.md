# pwn-htb

A Claude Code plugin for binary exploitation (pwn) exercises, optimized for Hack The Box challenges.

## Features

- **5-Phase Methodology**: Structured approach from environment setup through exploit development
- **Tool Integration**: pwntools, GDB/pwndbg, checksec, ROPgadget, one_gadget, seccomp-tools, ropper
- **8 Exploit Templates**: ret2libc, ROP, format string, shellcode, GOT overwrite, heap, SROP, stack pivot
- **Libc Database Integration**: Identify libc versions from leaked addresses
- **Auto-Detection**: Automatically detects and analyzes ELF binaries on session start
- **Protection-Aware**: Adapts exploitation suggestions based on binary protections

## Prerequisites

### Required Tools
- Python 3.8+
- pwntools (`pip install pwntools`)
- GDB with pwndbg extension
- checksec (`apt install checksec` or via pwntools)

### Optional Tools (auto-installed via pip if missing)
- ropper (`pip install ropper`)
- one_gadget (`gem install one_gadget`)
- seccomp-tools (`gem install seccomp-tools`)
- ROPgadget (`pip install ROPgadget`)

## Installation

```bash
# Clone or copy to your plugins directory
claude --plugin-dir /path/to/pwn-htb

# Or install globally
cp -r pwn-htb ~/.claude/plugins/
```

## Commands

### Main Workflow
| Command | Description |
|---------|-------------|
| `/pwn <binary>` | Run full methodology (all 5 phases with confirmations) |
| `/pwn-setup` | Environment setup and tool verification |
| `/pwn-recon <binary>` | Reconnaissance phase (checksec, file, strings) |
| `/pwn-static <binary>` | Static analysis (disassembly, dangerous functions) |
| `/pwn-dynamic <binary>` | Dynamic analysis (GDB scripts, offset calculation) |
| `/pwn-exploit` | Exploit development guidance |

### Exploit Templates
| Command | Description |
|---------|-------------|
| `/pwn-template` | Interactive template selector |
| `/pwn-ret2libc` | ret2libc/ret2system template |
| `/pwn-rop` | ROP chain construction template |
| `/pwn-format-string` | Format string exploit template |
| `/pwn-shellcode` | Shellcode injection template |
| `/pwn-got-overwrite` | GOT overwrite template |
| `/pwn-heap` | Heap exploitation (tcache/fastbin) template |
| `/pwn-srop` | Sigreturn-oriented programming template |

### Utilities
| Command | Description |
|---------|-------------|
| `/pwn-gdbinit` | Generate project-specific .gdbinit for pwndbg |
| `/pwn-libc <address>` | Identify libc version from leaked addresses |

## Agents

- **binary-analyzer**: Autonomous reconnaissance and static analysis
- **exploit-suggester**: Recommends exploitation techniques based on findings
- **template-generator**: Creates customized pwntools exploit skeletons

## Output Format

Each phase produces structured output:

```
## [Phase Name]

### Findings
- Structured observations from analysis

### Commands Run
- Actual commands with relevant output

### Implications
- What findings mean for exploitation

### Next Steps
- Recommended actions
```

## Usage Example

```bash
# Start a pwn session
claude

# Run full methodology on a binary
> /pwn ./challenge

# Or run individual phases
> /pwn-recon ./challenge
> /pwn-static ./challenge
> /pwn-dynamic ./challenge

# Generate exploit template based on findings
> /pwn-ret2libc

# Identify libc from leak
> /pwn-libc 0x7f1234567890
```

## License

MIT
