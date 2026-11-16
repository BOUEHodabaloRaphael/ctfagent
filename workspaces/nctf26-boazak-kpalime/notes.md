# boazak--kpalime (NCTF26, id=406, crypto, 400pts)

## Statut: RESOLU

## Enonce
RSA e=3, message = prefixe_connu || secret (secret = flag, <=128 bits, en fait 127 bits ici).
c = (prefixe_connu * 2^b + x)^3 mod n, b = suffix_bits = 127.

n = 88278370452871383449505388567128585231475025421947763689182908133039795711134962587740473030102398032046565374500394756563603693611986797335154082903488317728492504262116045192581504265852003276215103312149206097120005463471048316670500865143980657008377798711479339416521468769942015348612122366005999695531
e = 3
c = 29658287612140532234793809379685498587692681110132499738368730011782828405929128092553454107400998446183882624175367666503506998671669496857825021512856333228415626951351622289256316044909153386177883945345852286180243829128439352482876986352767231899683870889334382832936849930377348761236912293426239559038
prefix = "CONFIDENTIAL - access granted for user admin - token = " (ASCII)
suffix_bits (b) = 127

## Approche
Coppersmith univarie, Howgrave-Graham + LLL (fpylll) sur
f(x) = (M + x)^3 - c mod n, M = int(prefix bytes, 'big') * 2^127.
delta=3, bound X=2^127, n~1023 bits -> marge enorme (N^(1/3) ~ 2^341),
donc parametre m=1 (le plus petit lattice, dimension d=6) suffit deja.

Point cle de robustesse: apres LLL, factoriser exactement les polynomes
candidats sur ZZ (sympy `Poly.factor_list()`) pour extraire les racines
rationnelles -- bien plus fiable/robuste que le root-finding numerique
(`nroots`/`all_roots` de sympy bloquent ou timeoutent sur des
polynomes a coefficients tres grands).

## Resultat
x0 = 104029376867290715914428941595048957053 (127 bits exactement)
Verifie: pow(M + x0, 3, n) == c  (True)
bytes(x0) = b'NCTF{SM4LL_R00T}'

## Flag
NCTF{SM4LL_R00T}

## Soumission
`python3 src/tools/ctf/nctf26_client.py submit "boazak--kpalime" "NCTF{SM4LL_R00T}"`
-> Resultat: Correct

## Reutilisable
Script solveur (Coppersmith univarie, fpylll + sympy factor_list) utilise
dans cette session: voir patterns similaires pour tout challenge
"stereotyped message" RSA petit exposant (e=3 ou e=5) avec prefixe/suffixe
connu et partie inconnue petite (< N^(1/e)).
