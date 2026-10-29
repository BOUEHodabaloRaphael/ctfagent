---
doc_kind: pattern
title: "Node.js --inspect expose en local = privesc root generique"
category: web
slug: htb-reactor-nextjs-rce
created: 2026-10-29
status: active
tags:
  - web
  - nextjs
  - rce
  - prototype-pollution
  - nodejs-inspector
  - privesc
chain_summary: "Un process root lancé avec --inspect sur 127.0.0.1 est un primitive RCE root dès qu'on a un shell local, via tunnel SSH + node inspect + exec()."
---
# Node.js --inspect expose en local = privesc root generique

## Chain Summary

- One-line chain: Un process root lancé avec --inspect sur 127.0.0.1 est un primitive RCE root dès qu'on a un shell local, via tunnel SSH + node inspect + exec().
- Typical target shape: Shell obtenu sur une box; un process root tourne avec --inspect ou --inspect-brk sur localhost (visible via ss -tlnp/netstat).

## Preconditions

- Shell obtenu sur une box; un process root tourne avec --inspect ou --inspect-brk sur localhost (visible via ss -tlnp/netstat).

## Cheap Probes

- `ss -tlnp` ou `netstat -tlnp` après tout premier shell; chercher un port de debug Node (souvent 9229) lié à un process root.

## Telltale Evidence

- Process root avec --inspect=127.0.0.1:PORT dans `ps aux`/`ss -tlnp`.

## Escalation Order

1. Confirmer le port du debugger Node root via ss -tlnp.
2. Tunneliser le port via SSH local forward (-L localport:127.0.0.1:PORT).
3. Se connecter avec `node inspect localhost:localport` ou un client Chrome DevTools Protocol.
4. Injecter du JS qui appelle require('child_process').execSync(cmd) pour RCE root.

## Common Mistakes

- Chercher la privesc uniquement via sudo -l/SUID classique sans vérifier les ports de debug exposés.

## Payload Shapes

```text
require('child_process').execSync('chmod +s /bin/bash')
```

## Related Writeups

- htb-reactor-nextjs-rce

## Skill Impact

- Related skill: pwn-triage / web-triage: ajouter 'ss -tlnp pour debugger Node root' à la checklist de privesc post-shell.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
