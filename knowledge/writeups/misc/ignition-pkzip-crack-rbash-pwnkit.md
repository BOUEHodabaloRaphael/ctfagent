---
doc_kind: writeup
title: "ThunderCipher Ignition - crack PKZIP, bypass rbash et PwnKit (CVE-2021-4034)"
category: misc
slug: ignition-pkzip-crack-rbash-pwnkit
created: 2026-10-29
status: solved
tags:
  - pkzip-crack
  - rbash-bypass
  - pwnkit-cve-2021-4034
  - shadow-exfiltration
source: thundercipher.in/labs
target: "Archive protegee + shell rbash + pkexec"
---
# ThunderCipher Ignition - crack PKZIP, bypass rbash et PwnKit (CVE-2021-4034)

## Challenge Summary

- Source: thundercipher.in/labs
- Target: Archive protegee + shell rbash + pkexec
- Goal: Une archive protegee est crackee via zip2john/john, revelant un hash shadow exfiltre; le shell SSH obtenu est restreint (rbash), contourne par bash -c, puis PwnKit termine l'elevation.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. zip2john save.zip + john --wordlist rockyou -> mot de passe de l'archive.
2. unzip -> fichier shadow contenant un hash root exfiltre.
3. ssh -> shell restreint rbash.
4. bash -c 'bash -i' -> shell complet (bypass rbash).
5. Exploit PwnKit CVE-2021-4034 contre pkexec -> root shell.

## Key Evidence

- Hash shadow lisible dans l'archive decompressee; shell complet apres bash -c; root shell obtenu via pkexec.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
zip2john + john (craquage PKZIP); bash -c 'bash -i' (bypass rbash); exploit PwnKit (CVE-2021-4034).
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- rbash se contourne systematiquement par toute commande lancant un sous-shell non restreint (bash -c, vim :!bash, scp); PwnKit a tester en premier reflexe sur toute cible Linux avec pkexec present non patche.

## Pattern Candidates

- Voir pattern associe de meme slug.
