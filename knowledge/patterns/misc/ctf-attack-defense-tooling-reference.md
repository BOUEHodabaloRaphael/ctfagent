---
doc_kind: pattern
title: "Attack-Defense / KOTH — reference tooling (firegex, CookieFarm, FAUST gameserver, neo)"
category: misc
slug: ctf-attack-defense-tooling-reference
created: 2026-11-09
status: active
tags:
  - attack-defense
  - awd
  - koth
  - exploit-farming
  - hot-patching
  - gameserver
  - reference-only
chain_summary: "Pas un outil a installer dans ce depot: une carte de reference des projets externes qui dominent la scene Attack-Defense/KOTH (firegex pour le patch reseau a chaud, CookieFarm/neo pour la distribution d'exploits sur toutes les cibles, FAUST ctf-gameserver pour heberger un A&D). Aucun 'skill Claude Code' package et mur n'existe pour l'A&D (verifie par recherche le 2026-11-09) -- voir le skill maison `ctf-attack-defense` pour la methodologie, ce fichier ne couvre que les outils tiers."
---
# Attack-Defense / KOTH — reference tooling

## Chain Summary

Recherche GitHub ciblee le 2026-11-09 (requetes "attack-defense ctf claude skill",
"king of the hill claude agent", "awd ctf tool 2026", croisees) : **aucun depot
"Claude Code skill" mur n'existe pour l'Attack-Defense/KOTH**. La scene A&D tourne
sur des outils independants, pas sur des packages de connaissance pour agents LLM.
Ce fichier documente ces outils comme reference d'usage -- pas comme quelque chose
a cloner dans `knowledge/external/`. Pour la methodologie de triage/defense a
appliquer pendant un A&D, voir le skill maison
[`ctf-attack-defense`](../../../.claude/skills/ctf-attack-defense/SKILL.md).

## Outils de reference

### `Pwnzer0tt1/firegex` — https://github.com/Pwnzer0tt1/firegex
AGPL-3.0, ~127 etoiles, actif (dernier push 2026-11-01). Pare-feu applicatif
concu specifiquement pour l'A&D : filtre des paquets a la volee (regex sur
payload TCP/HTTP) pour bloquer l'exploit d'un adversaire **sans arreter le
service** -- c'est la reference de la scene pour le "patch reseau a chaud"
quand on n'a pas le temps de corriger le code source entre deux rounds de
scoring. Usage typique : capturer le payload d'exploit via trafic/alerte,
ecrire une regle firegex qui matche sa signature, la deployer en quelques
secondes.

### `ByteTheCookies/CookieFarm` — https://github.com/ByteTheCookies/CookieFarm
GPL-3.0, ~32 etoiles, actif (2026-10-24). Framework hybride Go+Python
(inspire de DestructiveFarm) pour **distribuer un exploit valide sur toutes
les cibles adverses** en parallele et soumettre automatiquement les flags
recoltes au gameserver. Couvre le cote "farming d'exploits", pas la defense.
Utile une fois qu'on a un exploit fiable sur le service vulnerable et qu'on
veut l'executer contre N adversaires sans script maison.

### `c4t-but-s4d/neo` — https://github.com/c4t-but-s4d/neo
MIT, ~55 etoiles, moins actif (dernier push 2025-11-26, ~1 an). Meme
categorie que CookieFarm (distribution d'exploits A&D) mais moins frais.
A considerer seulement si CookieFarm ne convient pas a l'infra de l'equipe.

### `fausecteam/ctf-gameserver` (FAUST) — https://github.com/fausecteam/ctf-gameserver
ISC, ~127 etoiles, actif (2026-10-11). Le gameserver de reference pour
**heberger** un A&D : checkers de service, calcul de score, SLA/uptime par
equipe. Pertinent seulement si on organise/heberge une competition A&D, pas
si on y joue seulement comme equipe -- mais utile comme reference de
methodologie checker/scoring pour comprendre comment les organisateurs
valident qu'un service est "up and correct" (ca explique pourquoi un patch
trop agressif peut faire tomber le SLA meme si le service repond).

## A eviter explicitement

### `LYiHub/OpenClaw-AWD-Arena`
Seul resultat trouve qui se presente comme un vrai "skill Claude" pour
l'AWD (agents LLM qui s'affrontent en temps reel). **Ne pas importer ni
installer** : audit Snyk CRITICAL, le process d'installation va chercher et
executer du code distant non verifie. Risque d'execution de code arbitraire
non controle.

## Mentionne pour memoire seulement (non verifie)

- "Mahoraga Webapp Defender" (avril 2026, blog/Reddit) : projet hobby de
  "defense auto-reparatrice" (patch autonome en reponse a une attaque live,
  12 flags de test). Concept interessant pour inspiration, aucune metrique
  GitHub solide trouvee -- ne pas traiter comme une source fiable.
- `yaklang/hack-skills` module `http2-specific-attacks` (deja importe dans
  `knowledge/external/hack-skills/`) : va un peu plus loin que les skills
  web generalistes sur HPACK/h2c smuggling/race single-packet si un vrai
  besoin HTTP/2 specifique apparait -- pas une lacune A&D, juste une note
  croisee.

## Preconditions

- Contexte confirme Attack-Defense/KOTH (pas un jeopardy classique) : chaque
  equipe recoit la meme image de service vulnerable, doit a la fois
  l'exploiter chez les adversaires et le defendre chez elle pendant des
  rounds de scoring repetes.

## Cheap Probes

- Avant d'installer firegex/CookieFarm en pleine competition, verifier que
  l'equipe a deja une methode de deploiement (pas le moment de debugger une
  install reseau pendant un round qui tourne).
- Si le format exact du gameserver (soumission de flags, format de checker)
  n'est pas documente par les organisateurs, lire rapidement le code FAUST
  `ctf-gameserver` pour deviner le protocole plutot que de supposer.

## Related

- [`ctf-attack-defense`](../../../.claude/skills/ctf-attack-defense/SKILL.md) —
  skill maison pour la methodologie de detection/triage/patch pendant un
  round A&D (inspire de la methodologie Anthropic
  `defending-code-reference-harness`, adapte, pas copie).
- [`ctf-file-hunter-sensitive-file-scanner`](ctf-file-hunter-sensitive-file-scanner.md) —
  utile une fois un shell obtenu sur le service adverse en phase d'attaque.
