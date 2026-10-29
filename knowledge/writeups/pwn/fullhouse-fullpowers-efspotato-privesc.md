---
doc_kind: writeup
title: "FullHouse - Ce qui a ete perdu (FullPowers + EfsPotato pour restaurer SeImpersonate)"
category: pwn
slug: fullhouse-fullpowers-efspotato-privesc
created: 2026-10-29
status: solved
tags:
  - seimpersonate
  - fullpowers
  - efspotato
  - quote-escaping
  - token-duplication
source: "HTB Pro Lab FullHouse"
target: "Shell service NT AUTHORITY\\LOCAL SERVICE sans SeImpersonate"
---
# FullHouse - Ce qui a ete perdu (FullPowers + EfsPotato pour restaurer SeImpersonate)

## Challenge Summary

- Source: HTB Pro Lab FullHouse
- Target: Shell service NT AUTHORITY\LOCAL SERVICE sans SeImpersonate
- Goal: Le shell service tourne sans SeImpersonatePrivilege; FullPowers restaure le privilege sur un nouveau process, permettant ensuite a EfsPotato d'escalader a SYSTEM.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. EfsPotato.exe echoue directement: privilege non detenu.
2. Chainer FullPowers -c EfsPotato.exe casse a cause de niveaux de guillemets imbriques multiples.
3. Solution: ecrire la commande cible dans un .bat pour eliminer tout guillemet.
4. FullPowers.exe -c EfsPotato.exe <script.bat> -> nouveau token avec SeImpersonate -> EfsPotato reussit -> SYSTEM.
5. Copie directe du flag Administrator vers un dossier accessible, nettoyee apres lecture.

## Key Evidence

- sortie FullPowers confirmant un nouveau token avec SeImpersonate, suivie du succes EfsPotato.

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
chaine d'outils de duplication de token (FullPowers puis EfsPotato) + fichier .bat intermediaire.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Quand un compte de service a ete depouille de SeImpersonatePrivilege, FullPowers le restaure sur un nouveau process (ne change pas l'identite); quand une chaine de commandes multi-niveaux casse sur des guillemets imbriques, ecrire la commande finale dans un script .bat/.ps1 intermediaire.

## Pattern Candidates

- Nouveau pattern: fullhouse-fullpowers-efspotato-privesc
