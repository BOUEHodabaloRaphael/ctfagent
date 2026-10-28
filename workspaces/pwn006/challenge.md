---
doc_kind: challenge
id: pwn006
title: "PWN#006"
category: pwn
platform: ctfd
platform_id: "31"
url: "169.58.126.107:5009"
status: new
tags:
  - quickjs
  - js-engine
attachments:
  - attachments/qjs
  - attachments/libc.so.6
  - attachments/libm.so.6
  - attachments/ld-linux-x86-64.so.2
---
# PWN#006

- ID: pwn006
- Category: pwn
- Platform: ctf.bugpwn.com (CTFd), challenge id 31
- Target: 169.58.126.107:5009
- Points: 150 (decaying, min 45), 0 solves at time of pull — just published
- max_attempts: 3

## Description

"Get a shell on the remote host and read the flag."

## Attachments

- `qjs` — stripped x86-64 PIE executable, QuickJS JS engine binary.
- `libc.so.6`, `libm.so.6`, `ld-linux-x86-64.so.2` — matching runtime libraries (stripped).

## Constraints

- `max_attempts: 3` for flag submission — validate locally before any remote submission.
- Prefer short validating probes first.
