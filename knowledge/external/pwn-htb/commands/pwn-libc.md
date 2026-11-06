---
name: pwn-libc
description: Identify libc version from leaked function addresses
argument-hint: "<function>=<address> [<function>=<address>...]"
allowed-tools: ["Bash", "WebFetch", "Write"]
---

# PWN Libc - Libc Identification

Identify the remote libc version from leaked function addresses.

## Usage

```bash
/pwn-libc puts=0x7f1234567890 printf=0x7f1234512340
```

## Execution Steps

### Step 1: Parse Leaked Addresses

Extract function name and address pairs from arguments.
Calculate the last 12 bits (3 hex digits) for each.

Example:
- `puts=0x7f1234567210` → offset ends in `210`
- `printf=0x7f1234512340` → offset ends in `340`

### Step 2: Query Libc Database

**Option 1: Online (libc.blukat.me)**

Query https://libc.blukat.me/ with the offsets.

**Option 2: libc.rip API**

```bash
curl -s "https://libc.rip/api/find" \
  -H "Content-Type: application/json" \
  -d '{"symbols": {"puts": "210", "printf": "340"}}'
```

**Option 3: Local libc-database**

```bash
cd ~/libc-database
./find puts 210 printf 340
```

### Step 3: Display Results

Show matching libc versions with:
- Libc identifier/name
- Download URL if available
- Key offsets (system, /bin/sh, one_gadget)

### Step 4: Generate Exploit Snippet

Provide code to use the identified libc:

```python
from pwn import *

# Identified libc: libc6_2.31-0ubuntu9_amd64
libc = ELF('./libc6_2.31-0ubuntu9_amd64.so')

# Leaked address
puts_leak = 0x7f1234567210

# Calculate base
libc.address = puts_leak - libc.symbols['puts']
log.success(f"libc base: {hex(libc.address)}")

# Key addresses
system = libc.symbols['system']
bin_sh = next(libc.search(b'/bin/sh'))
```

## Output Format

```
## Libc Identification

### Input
- puts: 0x7f1234567210 (offset: 0x210)
- printf: 0x7f1234512340 (offset: 0x340)

### Matches Found
| Libc | Confidence |
|------|------------|
| libc6_2.31-0ubuntu9.7_amd64 | 2/2 symbols |
| libc6_2.31-0ubuntu9.9_amd64 | 2/2 symbols |

### Recommended: libc6_2.31-0ubuntu9.7_amd64

#### Key Offsets
- system: 0x4fa60
- execve: 0xe62f0
- /bin/sh: 0x1b45bd
- __free_hook: 0x1eeb28
- __malloc_hook: 0x1ecb70

#### One Gadgets
```
0xe3b2e execve("/bin/sh", r15, r12)
  constraints: [r15] == NULL || r15 == NULL, [r12] == NULL || r12 == NULL

0xe3b31 execve("/bin/sh", r15, rdx)
  constraints: [r15] == NULL || r15 == NULL, [rdx] == NULL || rdx == NULL
```

### Download
```bash
# From libc-database
./download libc6_2.31-0ubuntu9.7_amd64

# Or direct URL
wget https://libc.rip/download/libc6_2.31-0ubuntu9.7_amd64.so
```

### Usage Snippet
```python
libc = ELF('./libc6_2.31-0ubuntu9.7_amd64.so')
libc.address = puts_leak - libc.symbols['puts']
system = libc.symbols['system']
bin_sh = next(libc.search(b'/bin/sh'))
```
```

## Tips

- Need at least 2 leaked addresses for reliable identification
- More leaks = higher confidence
- Last 12 bits (3 hex digits) are sufficient for lookup
- Common functions to leak: puts, printf, read, write, malloc, free
