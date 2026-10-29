---
doc_kind: pattern
title: "Interception d'entree de fonction (LD_PRELOAD) pour un secret ecrit-puis-efface"
category: rev
slug: zazamarin-maui-xamarin-native-flag-commit
created: 2026-10-29
status: active
tags:
  - android-reverse
  - dotnet-maui
  - xamarin
  - ld-preload
  - bionic-glibc
  - anti-frida
chain_summary: "Quand un secret natif est ecrit en memoire puis efface immediatement par la meme fonction, intercepter l'ENTREE de cette fonction (LD_PRELOAD/Frida hook) plutot que tenter un dump memoire post-mortem qui arrivera toujours trop tard."
---
# Interception d'entree de fonction (LD_PRELOAD) pour un secret ecrit-puis-efface

## Chain Summary

- One-line chain: Quand un secret natif est ecrit en memoire puis efface immediatement par la meme fonction, intercepter l'ENTREE de cette fonction (LD_PRELOAD/Frida hook) plutot que tenter un dump memoire post-mortem qui arrivera toujours trop tard.
- Typical target shape: Binaire natif (ELF/so) dont une fonction identifiee ecrit un secret puis l'efface avant de rendre la main; pas d'acces direct au secret en memoire persistante.

## Preconditions

- Binaire natif (ELF/so) dont une fonction identifiee ecrit un secret puis l'efface avant de rendre la main; pas d'acces direct au secret en memoire persistante.

## Cheap Probes

- Reverse la fonction suspecte pour confirmer le pattern write-then-wipe (souvent via memset/memcpy suivi d'un memset(0) juste apres un appel externe/retour).

## Telltale Evidence

- Un dump memoire pris apres l'execution de la fonction ne contient jamais le secret, alors que la logique source le manipule bien en clair a un instant precis.

## Escalation Order

1. Identifier precisement la fonction qui manipule le secret en clair (symboles ou reverse du binaire).
2. Si pas d'environnement cible natif (ex: pas d'Android/emulateur), evaluer si la lib native peut etre rejouee sur un autre hote compatible (meme ABI, dependances minimales) via dlopen/ctypes.
3. Ecrire un shim LD_PRELOAD qui intercepte l'appel cible et logue les arguments avant l'execution originale.
4. Si la lib s'attend a un environnement different (bionic vs glibc), fournir un faux libc.so avec un version-script exportant les symboles necessaires en relais vers la vraie libc.

## Common Mistakes

- Chercher le secret par dump memoire/strings post-mortem alors que la fonction l'efface deja avant de rendre la main.

## Payload Shapes

```text
LD_PRELOAD=./shim.so ./target  (shim.so hooke la fonction cible via dlsym(RTLD_NEXT,...))
```

## Related Writeups

- zazamarin-maui-xamarin-native-flag-commit

## Skill Impact

- Related skill: rev-triage: ajouter 'secret write-then-wipe -> hook d'entree LD_PRELOAD/Frida, pas dump post-mortem' comme heuristique anti-anti-debug.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
