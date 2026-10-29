---
doc_kind: pattern
title: "ThunderCipher StegoVault - FTP anonyme, steghide passphrase vide puis GTFOBins docker"
category: forensics
slug: stegovault-ftp-steghide-empty-pass-docker
created: 2026-10-29
status: active
tags:
  - steghide-empty-passphrase
  - ftp-anonymous
  - gtfobins-docker
  - mount-escape
chain_summary: "Un FTP anonyme expose un JPEG contenant des donnees stegano extractibles avec une passphrase steghide vide, revelant des creds SSH; sudo NOPASSWD docker permet un montage complet du disque."
---
# ThunderCipher StegoVault - FTP anonyme, steghide passphrase vide puis GTFOBins docker

## Chain Summary

- One-line chain: Un FTP anonyme expose un JPEG contenant des donnees stegano extractibles avec une passphrase steghide vide, revelant des creds SSH; sudo NOPASSWD docker permet un montage complet du disque.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Extraction reussie avec passphrase vide confirmee par la sortie de steghide; flag lu via montage docker.

## Escalation Order

1. FTP anonyme -> recuperation d'un JPEG.
2. steghide extract -sf <image> -p '' -> fichier de creds (passphrase vide, premier reflexe).
3. ssh avec les creds extraites -> flag user direct.
4. sudo -l -> NOPASSWD /usr/bin/docker.
5. docker run -v /:/mnt --rm <image> cat /mnt/root/root.txt -> flag root.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
Toujours tester steghide extract -p '' (passphrase vide) en premier reflexe sur tout JPEG suspect; sudo docker NOPASSWD = root trivial via montage -v /:/mnt.
```

## Related Writeups

- stegovault-ftp-steghide-empty-pass-docker

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
