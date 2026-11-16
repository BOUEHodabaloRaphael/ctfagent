from pwn import *
import re
context.log_level = "info"

HOST="10.100.16.100"; PORT=9999

p = remote(HOST, PORT)
p.recvuntil(b"cmd> ")
p.send(b"DEBUG\n")
data = p.recvuntil(b"Password: ")
print(data.decode(errors="ignore"))
p.send(b"wrongpass\n")
try:
    out = p.recvall(timeout=5)
    print("AFTER WRONG PASS:", out.decode(errors="ignore"))
except Exception as e:
    print("exc", e)
p.close()
