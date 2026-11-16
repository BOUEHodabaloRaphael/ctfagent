# NCTF26 — misc #436 "oxdefault--les-murmures-de-l-omni" (150pts)

Tentative perso (agent principal), en parallèle de l'agent dédié sur allowance-drift.

## Fichier
`message.txt` : `45, 1940, 1932, 127, 165, 93, 1303, 52807, 51852, 348, 1583, 1583, 1496, 1493, 34594, 34595, 1294, 1296, 1583, 1583, 103, 2375, 2365, 93, 110` (25 nombres)

## Piste confirmée solide
`/usr/share/dict/cracklib-small` (54763 lignes, trié ordre ASCII) matche très bien la distribution :
- index ~5000 = début 'b', ~10000 'c', ~20000 'f', ~30000 'l', ~34000 'o', ~40000 'r', ~50000 't', ~52000 'u/v'.
- 34594→"orderly", 34595→"orders", 52807→"violent", 51852→"unpleasantly" : cohérent avec les tranches ci-dessus → **ce dictionnaire est très probablement le bon support du book-cipher**.

## Essais ratés (extraction de lettre)
- Première lettre de chaque mot → quasi tout "a" (la plage basse 93-2375 est entièrement dans la section 'a' du dictionnaire, peu discriminant).
- Dernière lettre de chaque mot → chaîne illisible.
- `chr(n)` direct (Unicode codepoint) → mélange de scripts (coréen/CJK/hébreu/arabe), illisible.
- `n % 26` → lettre → illisible.
- `n % 128` / `n % 95 + 32` (ASCII direct) → illisible.
- Recherche OEIS (la suite ne correspond à aucune séquence connue).

## Observation structurelle notable (piste à creuser si repris)
- Valeur `1583` apparaît EXACTEMENT 2 fois à 2 positions différentes du message (indices 11-12 et 19-20, toujours en PAIRE consécutive) → cohérent avec une lettre doublée dans le texte clair (ex: "LL", "SS") à deux endroits, mappée de façon déterministe au même index chaque fois.
- Paires proches mais pas identiques : (1496,1493), (34594,34595), (1294,1296), (2375,2365) → cohérent avec un book-cipher où chaque lettre est mappée à un index FIXE et déterministe dans le dictionnaire (pas aléatoire), mais where la lettre réelle extraite n'est PAS la première/dernière lettre du mot à cet index (sinon on aurait trouvé un résultat lisible).

## Statut : blackbox-exhausted (pour cette session perso)
Le support (dictionnaire) semble juste, mais la règle d'extraction exacte (quelle partie du mot/quelle transformation donne la lettre réelle) n'a pas été trouvée après ~6 hypothèses raisonnables. Ne pas redevinner au hasard — si repris, essayer : (a) longueur du mot comme valeur plutôt que lettre, (b) position du mot dans une liste TRIÉE PAR LONGUEUR plutôt que par ordre alphabétique, (c) un autre dictionnaire système (`words`, `american-english`, `wordlist-probable.txt`) avec la même méthode de calibration par tranches.
