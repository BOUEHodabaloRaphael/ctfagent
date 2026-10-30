---
doc_kind: pattern
title: "Desobfuscation multi-couches CyberChef — methode generale"
category: forensics
slug: cyberchef-multilayer-deobfuscation-chain
created: 2026-10-30
status: active
tags:
  - legacy-memory-migration
  - nctf26-prep
  - cyberchef
chain_summary: "Lire la fonction de desobfuscation custom (JS/VBS obfusque) pour determiner l'ORDRE exact des operations inverses, puis chainer Find/Replace -> Reverse -> From Base64 -> From Hex dans CyberChef, plutot que de deviner."
---
# Desobfuscation multi-couches CyberChef — methode generale

## Chain Summary

- One-line chain: Lire la fonction de desobfuscation custom (JS/VBS obfusque) pour determiner l'ORDRE exact des operations inverses, puis chainer Find/Replace -> Reverse -> From Base64 -> From Hex dans CyberChef, plutot que de deviner.

## Preconditions

- Payload/malware avec une couche d'obfuscation custom non standard (padding repetitif, inversion de chaine, encodages empiles), typiquement vu dans des samples VBS/JS/PowerShell -EncodedCommand.

## Cheap Probes

- Inspecter le code source de la fonction de desobfuscation custom (meme un nom de variable cryptique type 0w0w0) pour voir dans quel ordre elle applique ses transformations — reproduire cet ordre a l'envers dans CyberChef.

## Telltale Evidence

- From Base64 echoue en mode UTF-16LE standard sur un -EncodedCommand PowerShell: certains payloads utilisent du Base64 UTF-8 au lieu de l'UTF-16LE natif de PowerShell — toujours tester les deux encodages avant de conclure a un echec de decodage.

## Escalation Order

1. Identifier et lire le code de la routine de desobfuscation custom pour determiner l'ordre exact des operations.
2. Find/Replace pour retirer un padding repetitif insere par l'obfuscateur (ex. motif type LOPPLPOLPO).
3. Reverse (By Character) si la chaine est inversee.
4. From Base64 avec Remove non-alphabet chars coche pour tolerer le bruit residuel.
5. From Hex si une couche hex additionnelle existe.
6. Tester explicitement le Base64 en UTF-8 ET UTF-16LE si un -EncodedCommand PowerShell ne decode pas normalement.

## Common Mistakes

- Deviner l'ordre des couches de deobfuscation au lieu de lire le code source de la routine custom qui l'implemente deja.

## Payload Shapes

```text
CyberChef recipe: Find/Replace(padding) -> Reverse -> From Base64(remove non-alphabet) -> From Hex
```

## Related Writeups

- N/A

## Skill Impact

- Related skill: Pertinent pour tout challenge forensics/malware-analysis NCTF26 impliquant un payload obfusque custom.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
