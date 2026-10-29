---
doc_kind: writeup
title: "ZaZamarin (Mobile Reversing)"
category: rev
slug: zazamarin-maui-xamarin-native-flag-commit
created: 2026-10-29
status: solved
tags:
  - android-reverse
  - dotnet-maui
  - xamarin
  - ld-preload
  - bionic-glibc
  - anti-frida
source: HackTheBox
target: "APK .NET MAUI/ex-Xamarin, libflagnative.so"
---
# ZaZamarin (Mobile Reversing)

## Challenge Summary

- Source: HackTheBox
- Target: APK .NET MAUI/ex-Xamarin, libflagnative.so
- Goal: APK .NET MAUI/Xamarin avec flag statique leurre et vrai flag construit nativement puis efface immediatement apres un seul appel flag_commit(), contourne sans Android via dlopen direct sur l'hote Linux.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Extraction archive protegee par bruteforce wordlist courte.
2. Identification .NET MAUI/Xamarin.Android via libmonosgen/libxamarin-app.so ; reperage de libflagnative.so et vault.dat chiffre.
3. Parsing maison de l'assembly store (blob dans une section ELF 'payload') par signatures XALZ et decompression LZ4 bloc par bloc -> 122 DLL, AppCTF.dll identifiee.
4. Decompilation C# ciblee via ICSharpCode.Decompiler (AsyncAwait=false) pour contourner un bug ilspycmd CLI.
5. Identification et rejet du leurre statique DecoyFlagGenerator (XOR no-op, jamais affiche).
6. Reverse de ChainRunner (vault.dat + FNV-1a du blob -> appels natifs P/Invoke + mixage ARX managé) ; flag_commit() ecrit puis efface immediatement le flag.
7. Pas d'emulateur Android (/dev/kvm absent) -> rejeu direct du build x86_64 natif via ctypes/dlopen sur l'hote Linux.
8. Faux libc.so avec --version-script exportant un noeud LIBC retransmettant vers la vraie glibc (incompatibilite bionic/glibc).
9. Interception de flag_commit(buf,len) par LD_PRELOAD avant l'effacement.

## Key Evidence

- "readelf -V | grep LIBC" confirmant le noeud cree ; "[shim] ascii: HTB{wh0_th3_h3ll_st1ll_wr1t3s_1n_x4m4r1n}" capture a l'entree de flag_commit.

## Dead Ends

- Dump memoire post-mortem ne fonctionnait pas car le flag est efface immediatement apres ecriture - il fallait intercepter a l'ENTREE de la fonction, pas apres.

## Payloads And Commands

```text
Lib native rejouee hors device (ctypes.CDLL + LD_PRELOAD shim C) remplacant un hook Frida.
```

## Flag / Outcome

- HTB{wh0_th3_h3ll_st1ll_wr1t3s_1n_x4m4r1n}

## Reusable Lessons

- Un flag natif ecrit puis efface en un seul appel se contourne par interception d'entree de fonction (LD_PRELOAD/Frida) plutot que par dump memoire post-mortem. Une lib native Android sans dependances JNI peut etre rejouee sur un hote Linux glibc via faux libc avec version-script, sans emulateur Android.

## Pattern Candidates

- Nouveau pattern: ld-preload-entry-hook-vs-postmortem-dump
