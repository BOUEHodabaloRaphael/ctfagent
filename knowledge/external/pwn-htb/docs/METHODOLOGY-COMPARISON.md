# Methodology Comparison: EXP-301 vs pwn-htb Plugin

This document compares the OffSec EXP-301 (OSED) Windows exploitation methodology with the pwn-htb plugin's Linux exploitation methodology.

## Overview

| EXP-301 (Windows) | pwn-htb (Linux) | Coverage |
|-------------------|-----------------|----------|
| WinDbg + x86 Architecture | GDB/pwndbg Setup | ✅ Full |
| Crash Application | Binary Reconnaissance | ✅ Full |
| Control EIP (cyclic pattern) | Dynamic Analysis (cyclic) | ✅ Full |
| **Bad Character Detection** | **Bad Character Detection** | ✅ Added |
| Find Return Address (JMP ESP) | Find Gadgets (ROPgadget) | ✅ Full |
| Generate Shellcode | Shellcode/Payload Templates | ✅ Full |
| Get Shell | Exploit Development | ✅ Full |

## Detailed Phase Comparison

### Phase 1: Environment Setup

| EXP-301 | pwn-htb |
|---------|---------|
| Install WinDbg | Verify pwntools, GDB, pwndbg |
| Configure debugging symbols | Configure context and terminal |
| Set up Kali VM | Auto-install missing pip packages |

**pwn-htb Command:** `/pwn-setup`

### Phase 2: Initial Analysis / Reconnaissance

| EXP-301 | pwn-htb |
|---------|---------|
| file, strings on binary | file, checksec, strings |
| Identify crash trigger | Identify dangerous functions |
| Note DEP/ASLR/CFG status | Note RELRO/Canary/NX/PIE status |

**pwn-htb Command:** `/pwn-recon <binary>`

### Phase 3: Controlling Execution (EIP/RIP)

| EXP-301 | pwn-htb |
|---------|---------|
| msf-pattern_create | pwntools cyclic() |
| msf-pattern_offset | pwntools cyclic_find() |
| Binary tree analysis | GDB cyclic -l command |

**pwn-htb Skill:** `dynamic-analysis` (Step 2)

### Phase 4: Bad Character Detection

| EXP-301 | pwn-htb |
|---------|---------|
| Send all chars 0x00-0xFF | Send all chars (bytes range) |
| Examine with WinDbg `db` | Examine with GDB `x/256bx` |
| Remove bad chars iteratively | Document in BAD_CHARS variable |

**pwn-htb Skill:** `dynamic-analysis` (Step 5 - NEW)

### Phase 5: Finding Return Address / Gadgets

| EXP-301 | pwn-htb |
|---------|---------|
| Find JMP ESP in loaded modules | ROPgadget --binary |
| Check for ASLR-disabled DLLs | Check for non-PIE binary |
| Mona.py for gadget search | ropper for alternative search |

**pwn-htb Command:** `/pwn-static <binary>` + ROPgadget usage

### Phase 6: Shellcode / Payload Generation

| EXP-301 | pwn-htb |
|---------|---------|
| msfvenom for shellcode | pwntools shellcraft |
| Custom shellcode creation | Template-based generation |
| Encoder for bad char avoidance | Shellcode encoding options |

**pwn-htb Commands:** `/pwn-shellcode`, `/pwn-ret2libc`, `/pwn-rop`, etc.

### Phase 7: Final Exploitation

| EXP-301 | pwn-htb |
|---------|---------|
| Combine all components | Combine all components |
| Test locally then remote | Local/Remote/GDB toggle |
| Adjust for environment | Libc identification for remote |

**pwn-htb Command:** `/pwn-exploit`

## Protection Bypass Mapping

| EXP-301 Protection | pwn-htb Equivalent |
|--------------------|-------------------|
| DEP (Data Execution Prevention) | NX (No-eXecute) |
| ASLR | ASLR + PIE |
| SafeSEH / SEHOP | Stack Canary |
| CFG (Control Flow Guard) | FORTIFY_SOURCE |
| Full ASLR | Full RELRO + PIE |

## Technique Mapping

| EXP-301 Technique | pwn-htb Template |
|-------------------|------------------|
| JMP ESP / CALL ESP | ret2win |
| ROP Chain | `/pwn-rop` |
| DEP Bypass (VirtualProtect) | ret2libc (mprotect) |
| Egghunter | (Not common in Linux CTF) |
| SEH Overwrite | (Windows-specific) |
| Format String | `/pwn-format-string` |
| Custom Shellcode | `/pwn-shellcode` |

## Key Differences

### Windows (EXP-301)
- SEH-based exploitation (Windows exception handling)
- SafeSEH/SEHOP bypasses
- WinDbg debugging
- PE format binaries
- Windows API shellcode (WinExec, CreateProcess)
- Module-based ASLR bypass (find non-ASLR DLL)

### Linux (pwn-htb)
- GOT/PLT exploitation
- Stack canary bypass via leak
- GDB/pwndbg debugging
- ELF format binaries
- syscall-based shellcode (execve)
- libc-based ASLR bypass (leak libc address)

## Conclusion

The pwn-htb plugin methodology closely follows the EXP-301 structured approach:

1. ✅ **Environment Setup** - Tool verification
2. ✅ **Reconnaissance** - Binary analysis
3. ✅ **Offset Calculation** - Cyclic patterns
4. ✅ **Bad Character Detection** - Added to align with EXP-301
5. ✅ **Gadget Finding** - ROPgadget/ropper
6. ✅ **Payload Generation** - Multiple templates
7. ✅ **Exploitation** - Protection-aware techniques

The main differences are platform-specific (Windows vs Linux), but the core methodology is consistent.
