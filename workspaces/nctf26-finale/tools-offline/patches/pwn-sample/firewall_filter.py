#!/usr/bin/python3 -u

from sys import stdin
import hashlib

"""
PATCHED firewall for pwn-sample-kun (A&D managed-patch defense).

Contract (unchanged, do NOT break it):
 - read client input line by line; emit exactly ONE verdict line per program fgets:
   "PASS\n" -> wrapper forwards the line to /prog ; "KILL\n" -> wrapper kills the connection.
 - mirror /prog's fgets state machine EXACTLY so verdicts stay aligned (1 output per input line).
 - NEVER throw: an uncaught exception kills this process -> wrapper fails OPEN (all lines pass).
   => whole main loop wrapped in try/except that fails CLOSED (KILL) on any internal error.

Vulns neutralized (see ../README.md for the attacker->flag path of each):
  cmd1 stack_bof : buf[16], fgets 1000   -> KILL if input > 15 bytes
  cmd2 fsb       : printf(buf)            -> KILL if input contains '%'
  cmd4 free      : free w/o alloc check   -> KILL double/invalid free (tracked state)
  cmd5 heap_write: fgets size+1000        -> KILL if data > BUF_SIZE[idx]-1
  cmd7 file_read : "/data/"+name, no val  -> KILL if name has '/', '..', '\\' (path traversal to /flag)
  cmd8 backdoor  : system(cmd) + bof      -> KILL if sha256(pw)==correct_hash OR cmd line > 63 bytes
  cmd3 malloc / cmd6 file_write / cmd9 leak: benign (C already validates) -> PASS, state only.
"""

# from prog.c: correct_hash[] for the admin backdoor (SHA256 of the secret password).
CORRECT_HASH = bytes([
  0x7c,0x92,0xf3,0x37,0x90,0x60,0x85,0x92,0x79,0xf5,0xa0,0xd6,0x98,0x28,0x76,0x49,
  0x9a,0xe9,0xc8,0x4e,0x73,0xa0,0xfc,0x9b,0x48,0x89,0x4f,0x6d,0xf9,0x9a,0x62,0x97])

def PASS(): print("PASS")
def KILL(): print("KILL")

REACHED_EOF = False
# returns (line, newline_appeared) -- mirrors C fgets truncation exactly.
def fgets(buf_size):
  global REACHED_EOF
  buf_size -= 1
  ret = b''
  while True:
    c = stdin.buffer.read(1)
    ret += c
    if c == b'\n':
      return ret, True
    if c == b'':
      REACHED_EOF = True
      return ret, True
    if len(ret) == buf_size:
      return ret, False

def _to_ll(line):
  positive = True
  if line.startswith(b'+'):
    line = line[1:]
  elif line.startswith(b'-'):
    line = line[1:]
    positive = False
  ret = 0
  for c in line:
    if ord('0') <= c <= ord('9'):
      ret = ret*10 + c - ord('0')
    else:
      break
  return -ret if not positive else ret

# benign numeric read: emits PASS itself (used for menu select / malloc / heap idx)
def read_ll():
  line, has_end = fgets(32)
  if has_end:
    PASS()
  return _to_ll(line)

# quiet numeric read: caller decides the verdict (used where idx choice gates an attack)
def read_ll_quiet():
  line, has_end = fgets(32)
  return _to_ll(line), has_end

IS_ALLOCATED = [False for i in range(10)]
BUF_SIZE = [0 for i in range(10)]

def _strip(line):
  return line[:-1] if line.endswith(b'\n') else line

# cmd1 -- KILL if input longer than 15 bytes (buf[16])
def unsafe_stack_bof():
  line, has_end = fgets(1000)
  if len(_strip(line)) > 15:
    KILL()
  elif has_end:
    PASS()
  else:
    KILL()  # no newline within 1000 -> oversized -> block

# cmd2 -- KILL on format specifier
def unsafe_fsb():
  line, has_end = fgets(1024)
  if b'%' in line:
    KILL()
  elif has_end:
    PASS()
  else:
    KILL()

# cmd3 -- benign; track allocation state. idx + size are benign selectors (read_ll auto-PASS).
def do_malloc():
  idx = read_ll()
  if idx < 0 or 10 <= idx:
    return
  size = read_ll()
  if size != 0:
    IS_ALLOCATED[idx] = True
    BUF_SIZE[idx] = size

# cmd4 -- KILL double-free / free of never-allocated chunk
def unsafe_do_free():
  idx, has_end = read_ll_quiet()
  if idx < 0 or 10 <= idx:
    if has_end: PASS()   # out-of-range: C rejects safely, benign
    return
  if not IS_ALLOCATED[idx]:
    KILL()               # free of unallocated/freed chunk -> UAF/double-free
    return
  if has_end: PASS()
  IS_ALLOCATED[idx] = False

# cmd5 -- KILL heap overflow (data longer than the allocation)
def unsafe_heap_write():
  idx = read_ll()                       # idx select: benign
  if idx < 0 or 10 <= idx:
    return
  if not IS_ALLOCATED[idx]:
    return
  line, has_end = fgets(BUF_SIZE[idx]+1000)
  if len(_strip(line)) > BUF_SIZE[idx]-1:
    KILL()
  elif has_end:
    PASS()
  else:
    KILL()

# cmd6 -- benign: C validates name as [A-Za-z] only, writes under /data/. PASS, mirror state.
def unsafe_file_write():
  name, has_end = fgets(94)
  if has_end:
    PASS()
  read_ll()  # idx selector (auto-PASS)

# cmd7 -- KILL path traversal ("/data/"+name, no validation in C). flag is at /flag.
def unsafe_file_read():
  name, has_end = fgets(94)
  s = _strip(name)
  if (b'/' in s) or (b'..' in s) or (b'\\' in s) or (b'\x00' in s) or s == b'':
    KILL()
  elif has_end:
    PASS()
  else:
    KILL()

# cmd8 -- KILL if backdoor password is correct (RCE) OR command overflows command[64].
# Benign wrong-password probes (short command) still PASS -> program prints Nope1.
def unsafe_admin_backdoor():
  password, has_end = fgets(100)
  if has_end:
    PASS()                              # program only stores it; action gated on next line
  command, has_end2 = fgets(104)
  pw_matches = hashlib.sha256(password).digest() == CORRECT_HASH
  if pw_matches or len(command) > 63:   # len incl newline; command[64] overflows at >63
    KILL()
  elif has_end2:
    PASS()
  else:
    KILL()

# cmd9 -- intended feature (address leak). No input consumed here. PASS already emitted
# by the menu read_ll for the "9" selector.
def address_leak():
  pass

def main():
  while True:
    cmd = read_ll()
    if cmd == 1:
      unsafe_stack_bof()
    elif cmd == 2:
      unsafe_fsb()
    elif cmd == 3:
      do_malloc()
    elif cmd == 4:
      unsafe_do_free()
    elif cmd == 5:
      unsafe_heap_write()
    elif cmd == 6:
      unsafe_file_write()
    elif cmd == 7:
      unsafe_file_read()
    elif cmd == 8:
      unsafe_admin_backdoor()
    elif cmd == 9:
      address_leak()
    if REACHED_EOF:
      return

if __name__ == '__main__':
  # Fail CLOSED: any unexpected error emits KILL and exits rather than dying silently
  # (a dead firewall makes the wrapper fail OPEN = all inputs pass unfiltered).
  try:
    main()
  except Exception:
    try:
      KILL()
    except Exception:
      pass
