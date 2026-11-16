# KOTH — Reconnaissance fraîche 2026-11-07 (4 collines, 13.37.197.230)

Contexte : relance complète demandée pour vérifier des angles pas forcément
couverts avant (headers HTTP complets, TLS/HTTPS, IPv6, UDP, host keys SSH,
OPTIONS/méthodes alternatives, robots.txt/.well-known, CORS). Contraintes
respectées : **aucun bruteforce SSH, aucun `nmap -p-`, aucun scan agressif
(`--min-rate` élevé), aucun flood** — un seul nmap scan ciblé (ports connus),
un seul nmap scan UDP top-20 gentil, le reste en requêtes HTTP/SSH isolées
avec délais de ~2s entre chaque.

Toutes les commandes ci-dessous ont été exécutées une seule fois chacune
(sauf retry explicite signalé), avec `-T2` / `--max-retries 1` / délais
manuels entre requêtes HTTP/SSH.

---

## 1. Nmap ciblé (ports connus, scripts, une seule exécution)

```
nmap -sV -sC -p 28490,28491,28492,28493 \
  --script=ssl-cert,http-headers,http-methods,ssh2-enum-algos -T2 \
  13.37.197.230
```

Résultat brut :
```
PORT      STATE    SERVICE    VERSION
28490/tcp open     unknown
28491/tcp filtered unknown
28492/tcp open     tcpwrapped
28493/tcp open     http       Werkzeug httpd 3.0.3 (Python 3.11.16)
| http-methods:
|_  Supported Methods: GET
```
Durée : 64.68s.

**Constat important (FAUX NÉGATIF nmap, pas un vrai blocage)** : nmap classe
28491 (Citadel) "filtered" et 28492 (Armory) "tcpwrapped" — mais des connexions
TCP directes lancées dans la même minute (juste après le scan) obtiennent la
bannière SSH **instantanément** sur les deux ports (voir §3). Les scripts
`ssl-cert`/`http-headers`/`http-methods` n'ont donc tourné sur AUCUN des 4
ports pour Citadel/Armory (nmap ne les a pas reconnus comme SSH), et
`ssh2-enum-algos` n'a produit aucune sortie. Conclusion : **les probes de
version-detection de nmap (envoi de données non-SSH sur un port SSH) se font
mal interpréter par le service ou par un filtrage applicatif léger**, ce qui
produit un état "filtered"/"tcpwrapped" trompeur — ce n'est PAS le même
phénomène que le cooldown de 20-30min déjà documenté (celui-là persiste après
le scan ; ici le port répond de nouveau immédiatement). **Leçon à ajouter** :
ne pas interpréter "filtered"/"tcpwrapped" sur ces ports comme une preuve de
blocage — toujours revérifier avec une connexion brute directe avant de
conclure.

28490 (Throne) : nmap le voit "open unknown" (ne reconnaît pas le service —
voir §2, c'est un serveur HTTP maison, pas du Werkzeug standard, d'où la
non-reconnaissance). 28493 (Fortune) : correctement identifié comme
Werkzeug/Flask, `http-methods` ne trouve que GET sur `/` (OPTIONS non testé
par ce script car non listé dans `Allow` par défaut — voir tests manuels §2).

### Essai complémentaire ciblé (sans -sV, pour laisser tourner ssh2-enum-algos)
```
nmap -p 28491,28492 --script ssh2-enum-algos -T2 -Pn 13.37.197.230
```
→ ports vus "open unknown" mais le script n'a toujours produit aucune ligne
de sortie (probablement un souci de timing/latence avec le script NSE, pas
un blocage — la négociation SSH manuelle au §3 a fonctionné sans problème).

---

## 2. Throne (28490) et Reseau Fortune (28493) — HTTP/HTTPS, headers, méthodes

### TLS/HTTPS — testé, PAS de TLS sur ces ports
```
openssl s_client -connect 13.37.197.230:28490
openssl s_client -connect 13.37.197.230:28493
```
Les deux renvoient immédiatement :
```
error:0A00010B:SSL routines:tls_validate_record_header:wrong version number
```
→ confirmation que les deux ports ne parlent QUE du HTTP en clair, aucun
service TLS caché derrière le même port (pas de STARTTLS, pas de TLS
sur demande).

### Headers complets (bruts, pas juste le corps)

**Throne `GET /`** :
```
HTTP/1.0 200 OK
Server: Throne/1.0 Python/3.11.16
Date: Sat, 07 Nov 2026 07:30:53 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 454
```
**NOUVEAU détail non documenté avant** : `Server: Throne/1.0 Python/3.11.16`
— un serveur HTTP maison (nom d'app custom "Throne/1.0"), pas du
Flask/Werkzeug. Cohérent avec : réponses en `HTTP/1.0`, `Connection: close`
systématique, erreurs en JSON brut (`{"error": "not found"}` / 
`{"error": "forbidden"}`), **et aucun support d'OPTIONS** (→ 501, voir
ci-dessous) — typique d'un `http.server.BaseHTTPRequestHandler` écrit à la
main (do_GET/do_POST explicites, pas de framework de routing générique).

**Fortune `GET /`** :
```
HTTP/1.1 200 OK
Server: Werkzeug/3.0.3 Python/3.11.16
Date: Sat, 07 Nov 2026 07:31:07 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 8038
Connection: close
```
Flask/Werkzeug standard confirmé (déjà su, mais header complet documenté ici
pour la première fois).

**Throne `GET /status`** (non gaté, déjà connu mais capturé en entier) :
```
HTTP/1.0 200 OK
Server: Throne/1.0 Python/3.11.16
Content-Type: application/json
Content-Length: 85

{"service": "throne", "uptime": 661437, "king": "028809ce…", "claims": 57948189}
```
`claims: 57948189` — confirme le volume adverse écrasant déjà documenté
(colline non gagnable par requêtage).

### Cookies de session — AUCUN sur Throne ni sur Fortune `/`
Vérifié avec `curl -c <jar>` : aucun `Set-Cookie` sur Throne `/` ou `/status`,
ni sur Fortune `GET /` (cohérent avec NOTES.md : le cookie Fortune n'apparaît
qu'après `/api/join`, pas sur la page d'accueil).

### CORS — pas de misconfiguration trouvée
```
curl -H "Origin: https://evil.example.com" .../status   (Throne)
curl -H "Origin: https://evil.example.com" .../          (Fortune)
```
→ Aucun `Access-Control-Allow-Origin` (ni aucun autre header `Access-Control-*`)
dans les deux réponses. Pas de reflet d'Origin, pas de credentials CORS
exposés.

### Méthodes HTTP alternatives

**Throne** — serveur maison, ne connaît que GET/POST explicitement codés :
- `OPTIONS /` → `501 Unsupported method ('OPTIONS')`
- `OPTIONS /throne` → `501 Unsupported method ('OPTIONS')`
- `PUT /`, `DELETE /`, `TRACE /` → `501 Unsupported method (...)`
- `POST /king` (sans body/XFF) → **`404 Not Found`** (route POST non
  déclenchée sans JSON body conforme — voir discussion `/king` plus bas)
- `GET /king` (avec ou sans `X-Forwarded-For: 127.0.0.1`, avec ou sans
  header `X-Hill-Sig` bidon) → **toujours `403 Forbidden`**, identique dans
  tous les cas testés.

**Fortune** — Flask standard :
- `OPTIONS /` → `200 OK`, `Allow: HEAD, GET, OPTIONS`
- `OPTIONS /api/refund` → `200 OK`, `Allow: POST, OPTIONS`
- `PUT /`, `DELETE /`, `TRACE /` → `405 METHOD NOT ALLOWED`, `Allow: HEAD, GET, OPTIONS`
→ Rien d'inattendu : pas de méthode cachée, pas de verbe tunneling possible,
cohérent avec un routing Flask propre (`methods=['POST']` sur `/api/refund`).

### robots.txt / sitemap.xml / .well-known/security.txt — tout 404 des deux côtés
- Throne : les 3 → `404` JSON `{"error": "not found"}` (serveur maison,
  même handler 404 générique que pour toute route inconnue).
- Fortune : les 3 → `404` HTML Flask standard.
→ Rien d'exposé par ce biais.

### Clarification sur `/king` (403 "jamais expliqué" dans les notes précédentes)
Relecture de `EXPLOIT.md` (ligne 16, 19-27) : le PoC fonctionnel appelle
`/king` en **POST** avec un body JSON `{"team", "ts", "sig"}` où `sig` est le
HMAC-SHA1 forgé — **ce n'est PAS un GET, et il n'a jamais été nécessaire de
spoofer `X-Forwarded-For` pour `/king`** (contrairement à `/debug`, qui lui
EST gaté par IP via XFF). Test fait aujourd'hui : un `GET /king` renvoie
toujours `403 forbidden` quel que soit le header XFF ou un header de
signature bidon, **parce que `GET` n'est simplement pas la bonne méthode /
le bon chemin d'authentification** — ce n'est pas un bug de gate IP non
résolu, c'est juste que les tentatives précédentes qui ont noté "403 même
avec XFF" testaient probablement la mauvaise méthode/forme de requête. Le
vrai mécanisme (POST + JSON + HMAC valide) est déjà confirmé fonctionnel
dans `EXPLOIT.md`. **Pas de nouvelle piste ici, juste une clarification d'un
point qui semblait non résolu** — je n'ai pas renvoyé la requête POST avec
une vraie signature forgée (ça rejouerait l'exploit déjà prouvé, inutile et
hors du périmètre "recon").

---

## 3. SSH — Citadel (28491) vs Armory (28492) : host keys

### Bannières (connexion TCP brute, immédiate, juste après le scan nmap du §1)
```
Citadel 28491: SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.17
Armory  28492: SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.17
```
→ Les deux répondent instantanément, confirmant que le "filtered"/
"tcpwrapped" vu dans le scan nmap était un faux négatif (§1), pas un vrai
blocage persistant.

### Host keys (`ssh-keyscan`, puis confirmation individuelle par type)

**Citadel 28491** :
```
ssh-ed25519  AAAAC3NzaC1lZDI1NTE5AAAAIIbSmVhWXDZD5OtXiwlGyBAazQXgDXFAOddQmoXJtpu8
ecdsa-sha2-nistp256  AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBM9ZPmQ9B3jPW5YnUD7JRIu7uSJ+fjxt9r8YNbZwA5PStj6DVkbj7kWsCW1Ki3U74D/YeFE9Ixc1/6N92yZjvWw=
ssh-rsa  AAAAB3NzaC1yc2EAAAADAQABAAABgQDGflQrCSd9NuaksZqqyJzlgsD9QcPWntUP+OCuKGCZJgdFeFU+N2Y9iX7O5lgiNSLl2Z6tuaNMXWabFVJk+kbr5rdTvVKaomWL8QLkEW2+30BRluR5p6dUnz0SK+svvUICtfI0aglaQeIFt2MaIRuqsv7sfFzXEfODbFq43X5wSkxhMdO3Min/+PAzIfM5qTJ8SVgICV9OkDSuvtsgDp8K5j7RZbyQbCxJdKOJhHh24ZRqWRkDUo38UeHw7h6P9ZovWU+1MYm39/Dx4tHVwZ2X+ZejtJPhTot7rIbmcbS2PDJppEghP3H4y0SF+qtfyF4FT7havPijkqIf6B2FhrMX2RH1rmaLAjnI50RrhUgE8mA4v0oHqnMmJvu2eAKJr1rNJBomUJUk4pIkRt54N/G4RT9B2EWRTteI843kvuXiPX+09xyv2uPnQZFvApCvEwTZ34rEZ7cCGVvXxsNL0obZA1pWb2/ZTD2cYJD5F2V4N5CVxx+4TOISQBN2bUXCe/c=
SHA256 fingerprint (ed25519, via ssh -vvv): SHA256:e+BZtSCVbPQ1gqxMTGj8fp8fsrGCSr/lqYodnrwjMWE
```

**Armory 28492** :
```
ssh-rsa  AAAAB3NzaC1yc2EAAAADAQABAAABgQCvK5Tq9otI+i7UB6mu7YQwGfoKtr31jKPSwPYnxPUKUAXSXoqJYlXF7xlIgg9CMPoelU1hF8hp5N5/4SpWiKQ/i8p8dAXWLOxgqX9WTmk7Pww+Vd+XWsDD1QGylVRrq3mg3oZLb2sxp6290jPXpKIghU5U2wza/21rGeG/ndth54FeYRFRVYCZ8jPIaHZJ+na2/YdlvjZB9luK782oTB8dPCkcHw5erbgKKYayNh5za5T9AvjBrS5F7jOynrwVaCOvznYWvnRvB11uhABxtzjNzD6+aErgFbX9HY0FrdqjmszFV0nSpTbg8+LVpiSz8maq/qoFOHXPym19U7CgafZVJ1nN2iYircHrjf3ojFXXqx7PafiJIT9QnXS2vNben39AjQMzwlr138E7fAxx94NrSm+IHTPIGDzzjsMmuJZeNXpLqmhVk809T1MnG9pLyi3vGaTOz0nRpZEzq3KaJYnGeIuT/31JtIrIOlItqDOh3Tlt+aj20UWYsK5mywbKrB0=
ssh-ed25519  AAAAC3NzaC1lZDI1NTE5AAAAIJjFuLR5UynDFXHNwObKoqmxjHTAWpF5StPricZfVDk5
ecdsa-sha2-nistp256  AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBJkAAtKxE+Mv0+9AujWnyAoInTaGhZf8HZtn75N/6vQ7coiAOBnLJOJP9R3cU9W1kIT6jFbo9drRZHgkyza1bJQ=
SHA256 fingerprint (ed25519, via ssh -vvv): SHA256:cKP5YnwSqQgAqxcgMQp6qXh3elAhylodDa72VhPTNvM
```

**→ NOUVEAU résultat confirmé (jamais comparé avant)** : les clés d'hôte
RSA, ECDSA et ED25519 sont **toutes différentes** entre Citadel et Armory,
sur les trois types. **Ce ne sont PAS la même VM/conteneur sous-jacent** —
deux hôtes SSH distincts avec des clés générées indépendamment. Les
algorithmes offerts (KEX, host-key, ciphers) sont en revanche identiques et
standards pour Ubuntu 22.04 / OpenSSH 8.9p1 (rien d'exotique, pas de config
durcie ou affaiblie détectée d'un côté ou de l'autre) :
```
host key algorithms offerts par le serveur (les deux hôtes, identique) :
rsa-sha2-512,rsa-sha2-256,ecdsa-sha2-nistp256,ssh-ed25519
kex négocié : sntrup761x25519-sha512@openssh.com (post-quantum hybride, défaut Ubuntu récent)
cipher : chacha20-poly1305@openssh.com
```
(Capturé via une seule tentative `ssh -vvv` avec `BatchMode=yes` sur un
utilisateur inexistant par hôte — pas de bruteforce, juste la négociation
protocole avant l'échec attendu "Permission denied".)

---

## 4. IPv6

```
dig AAAA ec2-13-37-197-230.eu-west-3.compute.amazonaws.com   → (vide, pas d'enregistrement)
dig A   ec2-13-37-197-230.eu-west-3.compute.amazonaws.com    → 13.37.197.230
dig AAAA arena.ctf.tg                                         → 2606:4700:3032::6815:437f, 2606:4700:3033::ac43:aec9
dig A    arena.ctf.tg                                         → 104.21.67.127, 172.67.174.201
```
→ **La cible KOTH elle-même (hôte EC2 derrière 13.37.197.230) n'a AUCUNE
adresse IPv6** — uniquement de l'IPv4 nu, hébergement AWS direct, pas de
reverse DNS IPv6. Seul `arena.ctf.tg` (la plateforme principale du CTF,
derrière Cloudflare) a des AAAA — mais c'est un domaine/service totalement
différent (le portail jeopardy, pas les hôtes KOTH). **Il n'existe donc pas
de chemin IPv6 alternatif moins filtré vers les 4 collines** — piste
négative mais désormais vérifiée et fermée définitivement.

---

## 5. UDP

```
nmap -sU -T2 --top-ports 20 --max-retries 1 13.37.197.230
```
(scan doux : 20 ports UDP les plus communs seulement, 1 seule tentative par
port, `-T2`, ~29s au total — pas de scan complet UDP).

Résultat : **les 20 ports testés sont tous `open|filtered`** (53, 67, 68,
69, 123, 135, 137-139, 161-162, 445, 500, 514, 520, 631, 1434, 1900, 4500,
49152). `open|filtered` sur TOUT le spectre testé sans aucune exception
signifie qu'il n'y a **aucune différenciation** — c'est le firewall/security
group AWS qui droppe silencieusement tout UDP non explicitement autorisé
(comportement par défaut, pas une preuve de service UDP réel ouvert nulle
part). **Résultat négatif net : aucun service UDP exploitable détecté.**

---

## 6. Synthèse — ce qui est VRAIMENT nouveau vs confirmation de l'existant

### Nouveau (pas documenté avant aujourd'hui)
1. **Citadel et Armory ont des host keys SSH totalement différentes** (RSA/
   ECDSA/ED25519 tous distincts) → confirmation définitive que ce sont deux
   hôtes/conteneurs séparés, pas la même VM. Question explicitement posée
   dans les notes précédentes ("jamais réexpliqué") — **répondue : NON, pas
   partagée.**
2. **Throne tourne sur un serveur HTTP maison** (`Server: Throne/1.0
   Python/3.11.16`, HTTP/1.0, pas de support OPTIONS → 501, erreurs JSON
   génériques) — explique pourquoi nmap ne le reconnaît pas comme un service
   standard et pourquoi son comportement diffère de Fortune (Flask/Werkzeug
   classique, HTTP/1.1, OPTIONS fonctionnel avec `Allow` correct).
3. **Faux négatif nmap sur Citadel/Armory** : `-sV`/`-sC` classe ces ports
   "filtered"/"tcpwrapped" alors qu'une connexion TCP brute immédiatement
   après obtient la bannière SSH sans délai — ne pas confondre avec le vrai
   cooldown de scan complet déjà documenté. Leçon opérationnelle à retenir
   pour les prochaines sessions.
4. **Clarification `/king` 403** : ce n'est pas un bypass IP non résolu,
   c'est juste que `GET /king` n'est pas la bonne méthode — le vrai flux
   (POST + JSON + HMAC) est déjà documenté fonctionnel dans `EXPLOIT.md`, non
   rejoué ici pour rester dans le périmètre recon.
5. **Pas de TLS, pas de CORS ouvert, pas de méthode HTTP cachée, pas de
   robots/sitemap/.well-known, aucune IPv6 sur la cible, aucun service UDP**
   — tous vérifiés et fermés comme pistes pour la première fois aujourd'hui.

### Confirmé mais déjà su (pas de changement)
- `/debug` SSRF via XFF toujours fonctionnel, leak toujours la même forme de
  clé HMAC (`sig_scheme: HMAC_SHA1(HILL_KEY, team+'|'+ts)`).
- `/status` toujours non gaté, `claims` énorme (57 948 189) → colline
  toujours noyée par le volume adverse, cohérent avec la conclusion
  "non gagnable" déjà posée.
- Fortune : `/api/refund` OPTIONS confirme `Allow: POST, OPTIONS` uniquement
  — aucune route GET cachée pour lire/forcer un refund différemment.

### Honnêtement : rien d'actionnable en plus trouvé
Après ce tour complet (headers, TLS, méthodes, robots/.well-known, CORS,
host keys SSH, IPv6, UDP), **aucune nouvelle vulnérabilité ni nouveau vecteur
d'accès n'a été découvert** sur les 4 collines. Les deux pistes déjà connues
(exploit HMAC Throne non gagnable par volume, IDOR refund Fortune sans
bypass supplémentaire) restent dans le même état qu'avant cette session.
Les points listés en "Nouveau" ci-dessus sont des clarifications/fermetures
de pistes (confirmations négatives utiles) et une précision d'architecture
(hôtes SSH distincts, serveur Throne maison), pas des failles.
