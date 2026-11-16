# REKit report — malware

- **Target:** `/tmp/ex_dropper.exe`
- **Date UTC:** 2026-10-30T08:23:58.660574+00:00
- **Type:** PE/DOS — PE 64-bit x86_64 (executable)
- **Size:** 1556 bytes
- **SHA-256:** `10d3731ffffad2acb31f73411761d3405c8af3ee263f0a378a40bb17381394d8`
- **MD5:** `98a9c5902e46467df869913196f881db`
- **Entropy:** 2.18139
- **imphash:** `bd9987ccee71eae7ce6ec03554f0245c`

> Static triage results are indicators, not proof that a file is benign or malicious.

## Summary

| high | medium | low | info |
|---|---|---|---|
| 1 | 3 | 3 | 7 |

**Suggested next steps**

- `rekit unpack <file>`

## Structure

PE 64-bit, x86_64, executable; entry `0x140001000`

| # | name | vaddr | size | flags | entropy |
|---|---|---|---|---|---|
| 0 | `UPX0` | `0x140001000` | 512 | rwx | 0.2209 |
| 1 | `UPX1` | `0x140002000` | 512 | r-- | 4.0855 |

## Findings

### [HIGH] Process injection primitives

Strong combination of related APIs. Indicators are not a verdict: benign software can show any of these behaviours.

- ID: `MAL-CAP-INJECT` — Confidence: **high** — ATT&CK hints: T1055
- Evidence:
  - `imports: CreateRemoteThread, VirtualAllocEx, WriteProcessMemory`
- Limitations:
  - Static presence only; reachability and arguments are unknown.

### [MEDIUM] Writable and executable section(s)

UPX0

- ID: `MAL-PE-RWX` — Confidence: **medium**
- Limitations:
  - Structural oddity; legitimate software can trigger it.

### [MEDIUM] Packer detected: UPX

Packed code hides the real logic from static analysis.

- ID: `MAL-PACK-001` — Confidence: **medium**
- Evidence:
  - `UPX (medium): section name(s): UPX0, UPX1`
- Next steps:
  - `rekit unpack <file>`
- Limitations:
  - Section names can be forged; entropy and structure were also checked.

### [MEDIUM] Run-key persistence

Related APIs or strings are present. Indicators are not a verdict: benign software can show any of these behaviours.

- ID: `MAL-STR-RUNKEYPERSISTENCE` — Confidence: **medium** — ATT&CK hints: T1547.001
- Evidence:
  - `strings: currentversion\run`
- Limitations:
  - Static presence only; reachability and arguments are unknown.

### [LOW] Non-standard section names

UPX0, UPX1

- ID: `MAL-PE-ODD-SECT` — Confidence: **medium**
- Limitations:
  - Structural oddity; legitimate software can trigger it.

### [LOW] Dynamic API / library resolution

Strong combination of related APIs. Indicators are not a verdict: benign software can show any of these behaviours.

- ID: `MAL-CAP-DYNAPI` — Confidence: **medium** — ATT&CK hints: T1027.007
- Evidence:
  - `imports: GetProcAddress, LoadLibraryA`
- Limitations:
  - Static presence only; reachability and arguments are unknown.

### [LOW] Network communication

Strong combination of related APIs. Indicators are not a verdict: benign software can show any of these behaviours.

- ID: `MAL-CAP-NETWORK` — Confidence: **high** — ATT&CK hints: T1071
- Evidence:
  - `imports: connect, recv, send, socket`
- Limitations:
  - Static presence only; reachability and arguments are unknown.

### [INFO] Overlay data after the last section

20 bytes at 0x600 (installers, appended payloads, or signatures).

- ID: `MAL-PE-OVERLAY` — Confidence: **medium**
- Limitations:
  - Structural oddity; legitimate software can trigger it.

### [INFO] Debugger detection / evasion

Related APIs or strings are present. Indicators are not a verdict: benign software can show any of these behaviours.

- ID: `MAL-CAP-ANTIDEBUG` — Confidence: **low** — ATT&CK hints: T1622
- Evidence:
  - `imports: IsDebuggerPresent`
- Limitations:
  - Static presence only; reachability and arguments are unknown.

### [INFO] Memory permission changes (RWX staging)

Related APIs or strings are present. Indicators are not a verdict: benign software can show any of these behaviours.

- ID: `MAL-CAP-MEMPERM` — Confidence: **low** — ATT&CK hints: T1027, T1055
- Evidence:
  - `imports: VirtualAllocEx`
- Limitations:
  - Static presence only; reachability and arguments are unknown.

### [INFO] Potential URLS indicators extracted

Static extraction found 1 candidate urls value(s).

- ID: `MAL-IOC-URLS` — Confidence: **low**
- Evidence:
  - `hxxp[://]79[.]124[.]8[.]24/fetch.sh`
- Limitations:
  - Extracted strings are not proof of network activity or malicious intent; inspect references and context.

### [INFO] Potential IPS indicators extracted

Static extraction found 1 candidate ips value(s).

- ID: `MAL-IOC-IPS` — Confidence: **low**
- Evidence:
  - `79[.]124[.]8[.]24`
- Limitations:
  - Extracted strings are not proof of network activity or malicious intent; inspect references and context.

### [INFO] Potential REGISTRY KEYS indicators extracted

Static extraction found 1 candidate registry_keys value(s).

- ID: `MAL-IOC-REGISTRY_KEYS` — Confidence: **low**
- Evidence:
  - `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run\x`
- Limitations:
  - Extracted strings are not proof of network activity or malicious intent; inspect references and context.

### [INFO] Potential WINDOWS PATHS indicators extracted

Static extraction found 1 candidate windows_paths value(s).

- ID: `MAL-IOC-WINDOWS_PATHS` — Confidence: **low**
- Evidence:
  - `C:\Users\Public\a.exe`
- Limitations:
  - Extracted strings are not proof of network activity or malicious intent; inspect references and context.

## Analysis limitations

- Static triage only; the target is never executed.
- No malware/benign verdict is produced automatically.
- Disassembly-based analysis (xrefs, stack strings, main discovery) covers x86/x86-64 only; other architectures rely on headers, symbols and strings.
