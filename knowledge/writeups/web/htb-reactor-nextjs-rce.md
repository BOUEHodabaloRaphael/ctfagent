---
doc_kind: writeup
title: "HTB Reactor"
category: web
slug: htb-reactor-nextjs-rce
created: 2026-10-29
status: solved
tags:
  - web
  - nextjs
  - rce
  - prototype-pollution
  - nodejs-inspector
  - privesc
source: HackTheBox
target: "Next.js 15.x App Router + Node.js --inspect"
---
# HTB Reactor

## Challenge Summary

- Source: HackTheBox
- Target: Next.js 15.x App Router + Node.js --inspect
- Goal: RCE pre-auth sur Next.js via CVE-2025-55182 (pollution de prototype dans la deserialisation RSC), pivot via SQLite, privesc root via Node --inspect expose en local.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Nmap: port 3000 Next.js 15.x (App Router + Server Actions/RSC).
2. Exploit public CVE-2025-55182 (payload multipart $1:__proto__:then) -> RCE pre-auth confirme, reverse shell (user node).
3. Lecture reactor.db (SQLite) -> hashs MD5 utilisateurs.
4. Hashcat -m 0 + rockyou -> credential valide, SSH, user flag.
5. ss -tlnp revele 127.0.0.1:9229 = process Node --inspect tournant en root (worker.js).
6. Tunnel SSH -L 9230:127.0.0.1:9229, `node inspect`, injection JS exec() -> child_process.execSync pour lancer un bash SUID.
7. /tmp/rootbash -p -> root.

## Key Evidence

- "Target is VULNERABLE! (command execution confirmed)"; ps aux montrant "root ... node --inspect=127.0.0.1:9229 worker.js"; rootbash-# apres chmod +s.

## Dead Ends

- n/a - chaine lineaire confirmee a chaque etape.

## Payloads And Commands

```text
Payload multipart RSC malformee (prototype pollution __proto__:then); reverse shell mkfifo; script JS inspect-debug exec()->child_process.execSync.
```

## Flag / Outcome

- user + root flags obtenus.

## Reusable Lessons

- CVE-2025-55182 exploitable pre-auth dès que l'app signale App Router + Server Actions (Next.js 15.x). Après tout shell obtenu, verifier systematiquement `ss -tlnp` pour un process root avec --inspect tunnelable en RCE root.

## Pattern Candidates

- Nouveau pattern: nodejs-inspector-root-privesc
