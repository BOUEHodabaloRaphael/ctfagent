---
doc_kind: pattern
title: "FullPowers pour restaurer SeImpersonate avant un Potato, fichier intermediaire contre les guillemets imbriques"
category: pwn
slug: fullhouse-fullpowers-efspotato-privesc
created: 2026-10-29
status: active
tags:
  - seimpersonate
  - fullpowers
  - efspotato
  - quote-escaping
  - token-duplication
chain_summary: "Quand un service tourne sans SeImpersonatePrivilege (depouille), FullPowers le restaure sur un nouveau process avant qu'un outil Potato (EfsPotato etc.) puisse fonctionner; les chaines de commandes multi-niveaux qui cassent sur des guillemets imbriques se resolvent en ecrivant la commande finale dans un script intermediaire."
---
# FullPowers pour restaurer SeImpersonate avant un Potato, fichier intermediaire contre les guillemets imbriques

## Chain Summary

- One-line chain: Quand un service tourne sans SeImpersonatePrivilege (depouille), FullPowers le restaure sur un nouveau process avant qu'un outil Potato (EfsPotato etc.) puisse fonctionner; les chaines de commandes multi-niveaux qui cassent sur des guillemets imbriques se resolvent en ecrivant la commande finale dans un script intermediaire.
- Typical target shape: Shell de service Windows (LOCAL SERVICE/NETWORK SERVICE) ou whoami /priv montre SeImpersonatePrivilege absent/disabled; un outil Potato classique echoue pour cette raison.

## Preconditions

- Shell de service Windows (LOCAL SERVICE/NETWORK SERVICE) ou whoami /priv montre SeImpersonatePrivilege absent/disabled; un outil Potato classique echoue pour cette raison.

## Cheap Probes

- whoami /priv pour confirmer l'absence de SeImpersonatePrivilege avant de lancer un outil Potato qui echouerait silencieusement sur ce point.

## Telltale Evidence

- Un outil Potato (GodPotato/EfsPotato/etc.) echoue avec une erreur explicite de privilege non detenu.

## Escalation Order

1. Confirmer l'absence de SeImpersonatePrivilege.
2. Lancer FullPowers pour l'obtenir sur un nouveau process.
3. Si la chaine de commande multi-niveaux casse sur des guillemets, ecrire la commande finale dans un .bat/.ps1 et l'appeler sans guillemets imbriques.
4. Lancer l'outil Potato depuis ce nouveau contexte.

## Common Mistakes

- Chainer directement des commandes complexes avec guillemets imbriques sur plusieurs niveaux (bash->SSH->PowerShell->outil->cmd) au lieu d'ecrire un script intermediaire.

## Payload Shapes

```text
FullPowers.exe -c "EfsPotato.exe go.bat" -z   (go.bat contient la commande finale sans guillemets)
```

## Related Writeups

- fullhouse-fullpowers-efspotato-privesc

## Skill Impact

- Related skill: pwn-triage (Windows privesc): ajouter FullPowers comme etape prealable systematique a tout outil Potato quand SeImpersonate est absent.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
