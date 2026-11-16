# NCTF26 #9 "allowance-drift" (blockchain, 137pts, 14 solves)

## Fichiers
- `DriftToken.sol` (telecharge via API authentifiee, HTTP 200)
- `token_state.json` (telecharge via API authentifiee, HTTP 200)

## Analyse du contrat (DriftToken.sol)

```solidity
function transferFrom(address from, address to, uint256 amount) external {
    require(balanceOf[from] >= amount, "balance");
    require(allowance[from][msg.sender] >= amount, "allowance");
    balanceOf[from] -= amount;
    balanceOf[to] += amount;
    // BUG: allowance[from][msg.sender] is never decremented here.
}
```

Bug confirme et commente par l'auteur du challenge lui-meme : `allowance` n'est
JAMAIS decremente apres un `transferFrom`. Donc une seule approbation (meme
petite) peut etre reutilisee a l'infini : chaque appel ne verifie que
`amount <= allowance` (toujours vrai, l'allowance ne bouge pas) et
`amount <= balance courante`.

## Etat (token_state.json)
- `victim_balance = 1000000`
- `your_allowance = 3000`
- `cipher_hex` = 33 octets (66 hex chars) : note scellee
- champ `note` (indice explicite du challenge) : *"victim state; compute how
  many transferFrom calls fully drain them"*

## Calcul "offline" effectue (exploit resolu)
Pour vider entierement la victime, chaque appel peut transferer au plus
`min(balance_restante, 3000)` (l'allowance ne baissant jamais, on peut
rejouer autant de fois que necessaire). Nombre minimal d'appels :

```
calls = ceil(1000000 / 3000) = 334   (333 appels de 3000 + 1 dernier appel de 1000)
```

Ce calcul est solide et correspond exactement a l'indice fourni par le
challenge ("compute how many transferFrom calls fully drain them").
Valeurs candidates derivees testees comme cle potentielle :
- 334 (nombre d'appels, la reponse a l'indice explicite)
- 333 (floor)
- 997000 (= 1000000 - 3000, le "drift" entre l'allowance unique et le
  montant reellement draine -- correspond au nom du challenge
  "allowance-**drift**")
- 1000000, 3000, 1000 (balance victime / allowance / dernier reliquat)

## Blocage : dechiffrement de cipher_hex NON RESOLU

Le `cipher_hex` (33 octets bruts, `c57fea...3413b`) a ete attaque avec
toutes les valeurs candidates ci-dessus, sous ces constructions (toutes
negatives, aucune n'a produit de sortie imprimable ni de motif `NCTF{`) :

1. XOR repete, cle = octet unique (brute force EXHAUSTIF des 256 valeurs,
   y compris `334 % 256 = 78`) -- aucune sortie entierement imprimable.
2. XOR repete, cle = chaine ASCII decimale/hex des candidats (`"334"`,
   `"997000"`, etc.), cle = entier big/little-endian sur 1/2/3/4/8 octets,
   brute force exhaustif des cles XOR repetees de longueur 1 et 2.
3. AES (CTR/OFB/CFB, IV=0 et IV/nonce preleve dans les 8-16 premiers octets
   du cipher) avec cle = candidat brut, zero-pad 16/32, SHA-256(candidat),
   SHA-256(candidat)[:16], MD5(candidat).
4. ChaCha20 avec nonce preleve dans les 8-12 premiers octets du cipher,
   cle = SHA-256/MD5 des candidats.
5. RC4 avec cle brute/ASCII des candidats.
6. Keystream Python `random.seed(candidat)` + `random.getrandbits(8)` /
   `randbytes()` (pattern frequent pour un chiffre "hand-rolled" en CTF),
   XOR et soustraction mod 256.

Aucune de ces 6 pistes serieuses n'a produit de texte imprimable ou de
`NCTF{`. La longueur de 33 octets (non multiple de 16) exclut ECB/CBC
"purs" ; soit le schema exact de chiffrement est different de ce qui a ete
tente (ex: derivation de cle non testee, encodage different du cipher_hex,
ou une transformation supplementaire avant/apres le XOR/AES), soit la bonne
valeur-cle n'est pas dans la liste de candidats ci-dessus.

## Statut : PISTE PRECISE, exploit logique resolu, dechiffrement final bloque

- Exploit ERC20 (allowance-drift) : **compris et resolu** -- 334 appels de
  `transferFrom` (333x3000 + 1x1000) videntierement la victime, en reutilisant
  la meme allowance de 3000 (bug de non-decrementation).
- Dechiffrement de `cipher_hex` -> note scellee -> flag : **non resolu**
  apres 6 pistes crypto serieuses (XOR brute force, AES/ChaCha stream avec
  plusieurs derivations de cle/nonce, RC4, PRNG Python seede).
- Prochaine piste a tenter (non testee par manque de temps dans cette
  session) : essayer d'autres valeurs derivees de l'exploit comme cle
  (ex: `balanceOf[victime]` final = 0, hash de la sequence complete des 334
  montants, ou une cle textuelle du type "334 calls" / "fully drained"
  plutot qu'un nombre brut), ou chercher si `cipher_hex` est en fait un XOR
  one-time-pad dont la cle est la CONCATENATION des montants des 334 appels
  (keystream = 3000,3000,...,1000 repete en little/big-endian).

Pas de flag a ce stade pour ce challenge.

## Reprise offline 2026-11-07 (session principale, sans acces reseau)

Nouvelle piste testee (crib-dragging connu-plaintext, pas tentee avant) :
XOR du prefixe cipher avec `b"NCTF{"` supposee -> keystream partiel
`[139, 60, 190, 191, 171]` (hex `8b3cbebfab`). Compare a sha256/md5 de tous
les candidats numeriques/textuels deja listes (334, 333, 997000, 1000000,
3000, 1000, "allowance-drift", etc.) et a `random.seed(candidat)` -- **aucune
correspondance**. Donc soit le keystream n'est pas derive d'un hash simple
de ces candidats via XOR classique, soit le plaintext ne commence pas
directement par `NCTF{` (le "cipher_hex" encode peut-etre une note qui
CONTIENT le flag plus loin, pas qui COMMENCE par lui).

Egalement teste et ecarte : AES-GCM (33 octets ne laisse que 17 octets de
texte utile apres un tag 16 octets -- trop court pour un flag, modele
probablement pas authentifie, juste un stream cipher brut).

Statut inchange : blackbox-exhausted. Pas de nouvelle piste sans info
supplementaire (acces reseau pour re-lire la description complete du
challenge, ou hint).
