---
doc_kind: pattern
title: "Keylogging d'une automatisation SendKeys planifiee (ex: PuTTY auto-login)"
category: misc
slug: rpg-ch2-ignis-putty-keylog-ebowla
created: 2026-10-29
status: active
tags:
  - rocket-chat-mongodb
  - ssh-key-leak
  - ebowla-av-evasion
  - keylogging
  - putty-automation
  - chisel-socks
chain_summary: "Une tache planifiee qui ressaisit automatiquement un mot de passe via SendKeys dans un client distant est capturable par keylogging, a condition de migrer le payload vers un process stable et d'attendre l'intervalle du scheduler."
---
# Keylogging d'une automatisation SendKeys planifiee (ex: PuTTY auto-login)

## Chain Summary

- One-line chain: Une tache planifiee qui ressaisit automatiquement un mot de passe via SendKeys dans un client distant est capturable par keylogging, a condition de migrer le payload vers un process stable et d'attendre l'intervalle du scheduler.
- Typical target shape: Acces a une machine avec une tache planifiee (scheduled task) detectee (ex via winPEAS) qui lance un client (PuTTY, RDP, etc.) et y ressaisit des credentials automatiquement (SendKeys/script).

## Preconditions

- Acces a une machine avec une tache planifiee (scheduled task) detectee (ex via winPEAS) qui lance un client (PuTTY, RDP, etc.) et y ressaisit des credentials automatiquement (SendKeys/script).

## Cheap Probes

- winPEAS ou revue manuelle des taches planifiees pour reperer un script/raccourci lancant un client distant avec des parametres suggérant une authentification automatisee.

## Telltale Evidence

- Une tache planifiee referencant un executable client + un script d'automatisation (AutoIt, SendKeys, etc.).

## Escalation Order

1. Confirmer la tache planifiee et son intervalle d'execution.
2. Deployer un payload (meterpreter ou equivalent) en contournant l'AV si necessaire (obfuscation type Ebowla).
3. Migrer le payload vers un process stable et de confiance (explorer.exe), jamais vers le process client cible lui-meme (le tuerait).
4. Activer le keylogger et attendre le prochain declenchement du scheduler.

## Common Mistakes

- Migrer le payload directement dans le process du client cible (putty.exe), ce qui interrompt la tache avant la saisie du mot de passe.

## Payload Shapes

```text
meterpreter > keyscan_start (apres migration vers explorer.exe)
```

## Related Writeups

- rpg-ch2-ignis-putty-keylog-ebowla

## Skill Impact

- Related skill: pwn-triage/AD: ajouter le keylogging de taches planifiees SendKeys comme technique de credential harvesting post-exploitation Windows.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
