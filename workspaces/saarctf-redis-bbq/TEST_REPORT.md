---
doc_kind: test-report
title: "saarCTF redis-bbq — service de vraie competition A&D, popé + branché sur le toolkit maison"
created: 2026-11-12
status: validated
---
# saarCTF 2023 "redis-bbq" — test de bout en bout

## Pourquoi

Suite a la recherche sur les labs A&D existants (2026-11-12), qui concluait
qu'aucun framework ne se monte en quelques minutes sans friction, decision
de quand meme TENTER un vrai service de competition (pas juste notre lab
custom `workspaces/ad-lab/`) pour valider le toolkit contre quelque chose
de plus realiste qu'un Flask jouet.

## Source

`git clone --depth 1 --branch master https://github.com/saarsec/saarctf-2023.git`
(clone dans `saarctf-2023-src/`, non commite -- voir `.gitignore` de ce
workspace). Service choisi : `redis-bbq` -- Redis modifie par un module C
(`http`) qui ajoute des commandes HTTP custom (GET/POST sur des cles),
avec un vrai bug de permission documente dans son propre README.

## Obstacles reels rencontres (et resolus)

1. **Deux images Docker de base indisponibles via Docker Hub direct**
   (`node:lts-bullseye`, `saarsec/saarctf-ci-base:bookworm`) -- meme
   probleme que pour `ad-lab` (registry Docker Hub bloque depuis cet
   environnement). Resolu en repointant les deux `FROM` vers
   `mirror.gcr.io/library/node:lts-bullseye` et
   `mirror.gcr.io/saarsec/saarctf-ci-base:bookworm` -- **l'image custom de
   l'organisateur elle-meme existe sur le mirror GCR**, preuve que ce
   contournement marche meme pour des images non-officielles rares.
2. **Build multi-stage reel** (frontend npm + compilation du module C Redis
   + un faux "systemd" Python qui emule des services dans le conteneur) --
   a pris plusieurs minutes, lance en arriere-plan le temps du build.
3. **Base de donnees vide au demarrage** (pas de vrai gameserver qui seed
   les utilisateurs/flags) -- seede manuellement via les memes commandes
   Redis que le vrai checker (`NEWUSER`, `AUTH`, `SETNX user:<u>:dishes
   <flag>`, `LPUSH newest:users <u>`), en lisant `checkers/connectors.py`
   du depot pour reproduire exactement son protocole.

## Resultat

- **L'exploit de demo officiel du depot** (`exploits/exploit_get.py`,
  ecrit par les organisateurs saarCTF eux-memes) a fonctionne tel quel
  contre le vrai binaire compile, sans authentification : lecture du
  `dishes` de n'importe quel utilisateur via la commande Redis brute `GET`
  (non filtree par permissions, contrairement a `LEGACY_GET`) --
  exactement la Vulnerabilite 1 documentee dans le README du service.
- **Exploit adapte pour notre toolkit**
  (`src/tools/ctf/attack_defense_toolkit/exploits/saarctf_redisbbq.py`,
  derive de l'exploit officiel) branche sur `exploit_runner.py` : trouve le
  flag en 1 passage (`-> 1 flag(s)`), tente la soumission HTTP (echoue
  seulement par mismatch de format de flag entre deux fixtures de test
  differentes -- `SAAR{...}` du service reel vs `NCTF{...}` du faux
  gameserver de `ad-lab`, pas un bug du toolkit).

## Conclusion

Le toolkit maison fonctionne aussi contre un **vrai service de competition
A&D** (pas seulement notre jouet Flask), construit depuis les sources
officielles d'une vraie edition saarCTF, avec son vrai bug documente et son
vrai exploit officiel. Ca renforce la confiance deja etablie par
`workspaces/ad-lab/TEST_REPORT.md` sans la remplacer.

## Nettoyage

Service arrete et conteneur supprime (`docker compose down`). Le clone
source (`saarctf-2023-src/`) reste sur disque pour reference future mais
n'est pas commite (voir `.gitignore`). `config.py` du toolkit sauvegarde
avant le test, restaure a l'identique apres (verifie par `git diff` vide).

## Related

- [`workspaces/ad-lab/TEST_REPORT.md`](../ad-lab/TEST_REPORT.md) — premier
  test de bout en bout, sur un service custom minimal.
- [`ctf-attack-defense-tooling-reference`](../../knowledge/patterns/misc/ctf-attack-defense-tooling-reference.md)
