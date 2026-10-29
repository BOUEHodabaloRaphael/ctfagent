---
doc_kind: pattern
title: "ThunderCipher Ignition - crack PKZIP, bypass rbash et PwnKit (CVE-2021-4034)"
category: misc
slug: ignition-pkzip-crack-rbash-pwnkit
created: 2026-10-29
status: active
tags:
  - pkzip-crack
  - rbash-bypass
  - pwnkit-cve-2021-4034
  - shadow-exfiltration
chain_summary: "Une archive protegee est crackee via zip2john/john, revelant un hash shadow exfiltre; le shell SSH obtenu est restreint (rbash), contourne par bash -c, puis PwnKit termine l'elevation."
---
# ThunderCipher Ignition - crack PKZIP, bypass rbash et PwnKit (CVE-2021-4034)

## Chain Summary

- One-line chain: Une archive protegee est crackee via zip2john/john, revelant un hash shadow exfiltre; le shell SSH obtenu est restreint (rbash), contourne par bash -c, puis PwnKit termine l'elevation.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Hash shadow lisible dans l'archive decompressee; shell complet apres bash -c; root shell obtenu via pkexec.

## Escalation Order

1. zip2john save.zip + john --wordlist rockyou -> mot de passe de l'archive.
2. unzip -> fichier shadow contenant un hash root exfiltre.
3. ssh -> shell restreint rbash.
4. bash -c 'bash -i' -> shell complet (bypass rbash).
5. Exploit PwnKit CVE-2021-4034 contre pkexec -> root shell.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
rbash se contourne systematiquement par toute commande lancant un sous-shell non restreint (bash -c, vim :!bash, scp); PwnKit a tester en premier reflexe sur toute cible Linux avec pkexec present non patche.
```

## Related Writeups

- ignition-pkzip-crack-rbash-pwnkit

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
