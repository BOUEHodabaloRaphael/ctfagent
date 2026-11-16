# boazak--niamtougou (crypto, 250pts, id=410)

## Challenge
624 sorties 32 bits de `random.getrandbits(32)` (période complète MT19937), puis flag chiffré
par XOR avec une clé "tirée juste après" les 624 sorties. Fichier `challenge.txt` fourni en
statique (pas de team_instance / VPN requis).

## Solve
1. Téléchargé `challenge.txt` via l'API fichiers signée (token déjà dans l'URL), 624 lignes
   `oN = <uint32>` + `enc = <hex, 49 bytes>`.
2. Untemper chaque sortie `oN` pour reconstruire le mot d'état interne `mt[N]` (inversion des
   4 étapes de tempering MT19937 : `>>18`, `<<15 & 0xefc60000`, `<<7 & 0x9d2c5680` (iteratif),
   `>>11` (iteratif)).
3. Reconstruit un `random.Random()` avec `setstate((3, tuple(mt + [624]), None))` — index 624
   force un retwist au prochain appel, exactement l'état juste après les 624 sorties connues.
4. Génère le flux de clé en consommant des mots 32 bits (`getrandbits(32)`) puis en les
   sérialisant **big-endian**, tronqué à `len(enc)` octets (49). XOR avec `enc` -> flag ASCII
   propre immédiatement (les autres encodages testés — `random.randbytes` (LE natif Python C),
   `getrandbits(8)` par octet, `getrandbits(len*8)` en un seul gros entier — donnaient du
   charabia).
5. Flag : `NCTF{N14M70UG0U_MT19937_5T4T3_R3C0V3RY_483726591}`

## Soumission
```
python3 src/tools/ctf/nctf26_client.py submit "boazak--niamtougou" "NCTF{N14M70UG0U_MT19937_5T4T3_R3C0V3RY_483726591}"
```
Résultat : `Correct`.

## Réutilisable
Pattern générique "624 leaked MT19937 outputs -> clone state -> predict next keystream" :
quand le prochain flux n'est pas directement `random.getrandbits(32)` répétés, essayer les
sérialisations de mots 32 bits en big-endian avant les API Python natives (`randbytes`,
`getrandbits(8)` par octet) — les challenges CTF encodent souvent le mot en big-endian "à la main"
plutôt que d'utiliser l'implémentation C interne de CPython.
