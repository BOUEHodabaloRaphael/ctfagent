---
doc_kind: writeup
title: "HTB Endgame RPG — Ch.2 pivot Ignis + keylogging PuTTY"
category: misc
slug: rpg-ch2-ignis-putty-keylog-ebowla
created: 2026-10-29
status: solved
tags:
  - rocket-chat-mongodb
  - ssh-key-leak
  - ebowla-av-evasion
  - keylogging
  - putty-automation
  - chisel-socks
source: "HackTheBox Endgame RPG"
target: "Rocket.Chat/MongoDB + session PuTTY automatisee (machine Ignis/Lux)"
---
# HTB Endgame RPG — Ch.2 pivot Ignis + keylogging PuTTY

## Challenge Summary

- Source: HackTheBox Endgame RPG
- Target: Rocket.Chat/MongoDB + session PuTTY automatisee (machine Ignis/Lux)
- Goal: Pivot via un binaire .NET vers Rocket.Chat/MongoDB non protegee, exfiltration d'une cle SSH, puis capture du mot de passe root via keylogging d'une session PuTTY automatisee (AV contourne par Ebowla).

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Extraction d'une URL d'API Rocket.Chat depuis les strings d'un binaire .NET trouve sur un partage SMB.
2. Acces direct a la base MongoDB exposant une cle SSH privee pour un utilisateur d'Ignis.
3. Regeneration de la cle publique manquante (ssh-keygen -y) pour contourner un format invalide.
4. Lecture des messages Rocket.Chat en base revelant le mot de passe par defaut de l'entreprise et un compte admin reassignable.
5. Tunnel SOCKS (chisel) vers le reseau interne, crackmapexec confirme WinRM -> connexion avec le mot de passe d'entreprise.
6. winPEAS detecte un PuTTY automatise (tache planifiee se connectant en root) ; Meterpreter obfusque Ebowla (AV), migration vers explorer.exe.
7. Keylogging de la session SendKeys automatisee -> capture du mot de passe root en clair.

## Key Evidence

- "db.rocketchat_message.find() -> ...mot de passe par defaut..."; keylog capture du mot de passe root; connexion SSH root reussie -> flag lu.

## Dead Ends

- Migration Meterpreter directe vers putty.exe tue le shell - fallait migrer vers explorer.exe (process stable, pas le client cible).

## Payloads And Commands

```text
Payload Meterpreter obfusque (Ebowla) + keylogger Metasploit migre sur explorer.exe.
```

## Flag / Outcome

- Flag obtenu via lecture SSH root.

## Reusable Lessons

- Une automatisation planifiee ressaisissant un mot de passe via SendKeys dans un client distant (PuTTY) est capturable par keylogging process-level, en migrant vers un process stable (pas le client cible) et en patientant l'intervalle du scheduler.

## Pattern Candidates

- Nouveau pattern: scheduled-sendkeys-keylog-capture
