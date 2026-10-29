---
doc_kind: pattern
title: "Whitespace steganography -> base64 -> ZIP: chaine misc multi-couches"
category: misc
slug: fafa-whitespace-stego
created: 2026-10-29
status: active
tags:
  - misc
  - steganography
  - whitespace-stego
  - base64
  - zip-cracking
chain_summary: "Texte anodin avec espaces/tabulations invisibles = whitespace stego (snow); decode souvent en base64 vers une archive protegee cassable par dictionnaire."
---
# Whitespace steganography -> base64 -> ZIP: chaine misc multi-couches

## Chain Summary

- One-line chain: Texte anodin avec espaces/tabulations invisibles = whitespace stego (snow); decode souvent en base64 vers une archive protegee cassable par dictionnaire.
- Typical target shape: Challenge misc fournissant un fichier texte qui semble anodin (email, note, poeme) sans indice visuel suspect.

## Preconditions

- Challenge misc fournissant un fichier texte qui semble anodin (email, note, poeme) sans indice visuel suspect.

## Cheap Probes

- `cat -A <fichier>` ou `grep -P '[ \t]+$'` pour reveler des espaces/tabulations invisibles en fin de ligne.

## Telltale Evidence

- Lignes terminees par des sequences d'espaces/tabulations qui ne sont pas du formatage normal.

## Escalation Order

1. cat -A pour detecter whitespace invisible.
2. stegsnow -C (ou -S pour encoder) pour extraire le message cache.
3. Si le contenu extrait ressemble a du base64, decoder et verifier les premiers octets (signature de fichier: PK pour ZIP, etc.).
4. Si ZIP protege, tester fcrackzip ou John avec rockyou avant de chercher un mot de passe custom.

## Common Mistakes

- Ignorer un fichier texte 'anodin' sans l'inspecter en mode brut (cat -A / xxd) juste parce qu'il semble etre du texte normal.

## Payload Shapes

```text
stegsnow -C -p <wordlist?> input.txt ; echo <blob> | base64 -d > out.zip ; fcrackzip -u -D -p rockyou.txt out.zip
```

## Related Writeups

- fafa-whitespace-stego

## Skill Impact

- Related skill: Pas de skill misc-triage dediee actuellement; backlog candidate si un pattern misc recurrent se confirme.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
