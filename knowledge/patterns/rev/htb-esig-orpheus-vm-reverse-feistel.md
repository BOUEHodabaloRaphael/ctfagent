---
doc_kind: pattern
title: "ORPHEUS - license manager stripped avec VM bytecode et chiffrement Feistel inversible"
category: rev
slug: htb-esig-orpheus-vm-reverse-feistel
created: 2026-10-29
status: active
tags:
  - vm-bytecode
  - feistel-cipher
  - anti-debug-ptrace
  - decoy-flag
  - static-reverse
  - inversible-crypto
chain_summary: "Binaire avec anti-debug, VM a bytecode custom et un chiffrement par blocs Feistel 12 rounds entierement inversible (pas de bruteforce necessaire), plus un leurre explicite."
---
# ORPHEUS - license manager stripped avec VM bytecode et chiffrement Feistel inversible

## Chain Summary

- One-line chain: Binaire avec anti-debug, VM a bytecode custom et un chiffrement par blocs Feistel 12 rounds entierement inversible (pas de bruteforce necessaire), plus un leurre explicite.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Emulation VM Python confirme la sortie attendue; inversion du Feistel produit bien le bloc cible; CRC32 brut different de la constante du decoy (evite le leurre).

## Escalation Order

1. Recon statique (file/rabin2): imports ptrace+fopen/strstr/strtol suspects, symbole exporte suspect.
2. Oracle de signature teste en faisant varier un octet a la fois -> echec (OR des octets de diff, saturation).
3. Hook LD_PRELOAD + debogueur: l'anti-debug empoisonne silencieusement le calcul sous tracer -> retour a l'analyse statique pure.
4. Dechiffrement des chaines .rodata (XOR+rotation) -> localisation du vrai flux et d'un chemin leurre (decoy flag).
5. Reimplementation Python de la VM bytecode (cle derivee d'un Machine ID) -> calcul de la cible attendue.
6. Chiffrement Feistel 12 rounds bijectif -> inversion analytique (pas de bruteforce) pour retrouver le token valide.
7. Stage 2 (code de confirmation) meme principe, rounds inversibles -> code retrouve par inversion.
8. Soumission token+code -> flag final.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Tester systematiquement si un chiffrement custom dans un crackme est compose uniquement d'operations bijectives (permutation/XOR/rotation/mult impaire): si oui, inverser analytiquement plutot que bruteforcer. Sous anti-debug ptrace/TracerPid, un calcul qui change silencieusement de resultat sous debogueur (au lieu de planter) est un signal qu'il faut repasser en statique pur. Toujours se mefier d'un flag trouve via un chemin alternatif (fonction exportee suspecte) - verifier le format attendu avant de soumettre.
```

## Related Writeups

- htb-esig-orpheus-vm-reverse-feistel

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
