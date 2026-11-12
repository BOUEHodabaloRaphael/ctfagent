---
doc_kind: test-report
title: "attack_defense_toolkit — validation end-to-end sur lab Docker local"
created: 2026-11-12
status: validated
---
# attack_defense_toolkit — validation end-to-end

## Pourquoi

`attack_defense_toolkit/` (prepare le 2026-09-14 pour AFRICC/ICC) n'avait
**aucune trace d'utilisation en vrai round Attack-Defense** avant ce test
(contrairement a la methodologie KOTH, validee 2/3 rounds TryHackMe). Un
tour de recherche GitHub (2026-11-12) a confirme qu'aucun framework A&D
existant (ENOWARS/EnoEngine, saarCTF+gamelib+Redis, ForcAD, memowotoru) ne
se monte en quelques minutes sans friction pour un test solo -- decision :
construire un lab minimal custom plutot que d'importer un framework lourd.

## Lab construit (`workspaces/ad-lab/`)

- `vulnbox/` : service Flask avec injection de commande deliberee
  (`/ping?host=<param>` interpole dans `ping -c 1 -W 1 <param>` via
  `shell=True`), flag qui tourne toutes les 30s (`FLAG_ROTATE_SECONDS`),
  `/health` pour le monitoring.
- `gameserver/` : faux gameserver Flask minimal (`POST /submit` valide le
  format par regex + dedup, `GET /health`, `GET /stats` pour verifier).
- `docker-compose.yml` : les deux services, ports hote 18080 (vulnbox) et
  19090 (gameserver).
- Base image `python:3.12-slim` indisponible depuis cet environnement
  (Docker Hub direct bloque) -> utiliser `mirror.gcr.io/library/python:3.12-slim`
  a la place (deja le cas dans les Dockerfiles du lab).

## Resultats des 3 outils testes

| Outil | Test | Resultat |
|---|---|---|
| `exploit_runner.py --once` | vol du flag + soumission auto au gameserver | ✅ `-> 1 flag(s)`, `submit ... -> 200 accepted` |
| `submitter.py` (standalone, stdin) | extraction + soumission + dedup local | ✅ flag neuf accepte (200), flag deja vu correctement ignore (aucune re-soumission) |
| `sla_monitor.py` | detection UP/DOWN en continu | ✅ UP (vert) pendant que le conteneur tourne, bascule DOWN (rouge) immediatement apres `docker stop` |

## Bug reel trouve et corrige pendant le test

`src/tools/ctf/attack_defense_toolkit/exploits/ad_lab_vulnbox.py` visait
initialement le port **interne** du conteneur (`8080`) au lieu du port
**expose cote hote** (`18080`, mapping docker-compose) -- `exploit_runner.py`
cible toujours des IP/ports "vus depuis l'exterieur" (equivalent d'une IP
d'equipe adverse en vraie competition), jamais un port interne de
conteneur. Corrige (commentaire ajoute dans le fichier pour ne pas
retomber dans le piege).

## Piege de test (pas un bug de l'outil) : buffering stdout

`sla_monitor.py` ne produisait AUCUNE sortie visible quand lance via
`timeout N ... | capture` ou en arriere-plan tue par `kill` -- confirme que
c'est un artefact de buffering Python (stdout entierement bufferise quand
ce n'est pas un vrai TTY, et un `SIGTERM`/`kill` ne flush pas le buffer C
avant de terminer le process), pas un bug du script. Resolu pour le test
avec `python3 -u`. **Lecon pour la vraie finale** : lancer `sla_monitor.py`
dans un vrai terminal/tmux pane (TTY reel, ligne-bufferise par defaut), pas
redirige/backgrounded sans `-u` -- sinon l'alerte visuelle peut arriver en
retard ou etre perdue si le process est tue brutalement.

## Config.py

Le fichier reel `config.py` (placeholder pour la vraie finale) a ete
sauvegarde avant le test, remplace temporairement par une config pointant
sur le lab local, puis restaure exactement a l'identique apres (verifie via
`git diff` vide sur ce fichier).

## Conclusion

Les 3 scripts du toolkit font bien ce que la doc dit qu'ils font, contre un
service noir-boite reel en Docker, dans une boucle complete
exploit -> soumission -> detection de panne. Le toolkit est maintenant
**eprouve au feu** (pas juste relu), meme si ce n'est toujours pas un vrai
round multi-equipes -- void la mise en garde deja ajoutee dans
`nctf26-finale-trigger-protocol` (memoire) sur les limites de cette
validation solo.

## Related

- [`attack-defense-methodology-toolkit`](../../knowledge/patterns/misc/attack-defense-methodology-toolkit.md)
- [`ctf-attack-defense-tooling-reference`](../../knowledge/patterns/misc/ctf-attack-defense-tooling-reference.md)
