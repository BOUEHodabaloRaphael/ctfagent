# NCTF26 — Défi d'ouverture misc : "Prends le contrôle de ctf.tg" (500 pts, 0 solve)

Cible autorisée : https://ctf.tg/ (site public racine uniquement — PAS arena.ctf.tg,
PAS l'infra hébergeur). Objectif réel : faire apparaître le nom d'équipe **Th3N00bs**
en grand sur la home page publique, visible par tout visiteur, de façon persistante.

Règles : pas de DoS/flood, pas de bruteforce (flag ou login), pas de scan de port massif,
pas de dirbusting agressif (rate-limité, quelques req/s max), scope strictement ctf.tg.

Démarrage recon : 2026-11-06 19:04 UTC (= 19:04 Lomé, l'épreuve vient tout juste d'ouvrir
à 19:00 Lomé — timing cohérent avec le protocole NCTF26 documenté dans
workspaces/nctf26/notes.md).

Chaque test ci-dessous = requête brute + réponse brute. Pas de résumé sans preuve.

---

## 0. Statut (mis à jour 2026-11-06 ~19:15 UTC/Lomé)

**static-surface-exhausted** (environ 30 min de sondage réel, evidence-first,
voir sections 1-7). `ctf.tg` est un site **100% statique** (HTML/CSS/JS/images),
servi derrière Cloudflare, avec une CSP extrêmement durcie
(`form-action 'none'`, `object-src 'none'`, `frame-ancestors 'none'`,
`script-src 'self' <sha256 unique> + cloudflareinsights`, `connect-src 'self' +
cloudflareinsights`). Aucune surface applicative dynamique trouvée sur ce domaine
precis : pas de formulaire, pas d'API, pas de panneau admin, pas de CMS connu,
pas de fichier de config exposé. Toutes les pistes classiques listées dans la
méthode (SQLi/SSTI/XSS stocké via formulaire/upload/API headless) ne
s'appliquent pas car il n'y a **aucun point d'entrée serveur** sur ce domaine
precis — toute la logique "plateforme" (login, challenges, scoreboard, soumission)
vit sur `arena.ctf.tg`, explicitement hors périmètre de cet exercice.

**Piste la plus prometteuse, NON exécutée (hors du périmètre de cet agent)** :
le minuteur d'ouverture NCTF26 (19:00 Lomé) vient d'expirer pendant ce recon
(session démarrée 19:04 UTC = Lomé). Le workspace `workspaces/nctf26/notes.md`
documente un mécanisme `/plugins/defi_gate/` sur `arena.ctf.tg` affichant
"Défi #1 — le défi n'est pas actif pour le moment" avant l'ouverture, avec un
outillage de session déjà en place (`src/tools/ctf/nctf26_client.py`,
`src/tools/ctf/nctf26_storage_state.json`, session du 2026-11-06 13:47). Il est
très probable que ce "Défi #1" soit précisément ce défi "Prends le contrôle de
ctf.tg" et qu'il vienne de s'activer, avec un **énoncé/brief précis** qui
manque actuellement ici (je travaille en boîte noire pure sur le site public
sans avoir lu l'énoncé officiel du défi). Recommandation forte avant de
pousser davantage de sondage actif sur `ctf.tg` : lire l'énoncé via
`nctf26_client.py` / la page `/plugins/defi_gate/` (lecture seule, pas une
attaque) pour confirmer le vecteur attendu plutôt que deviner en aveugle.

---

## 1. Recon passif DNS / WHOIS

- `whois ctf.tg` : échec résolution `whois.nic.tg` depuis cet environnement
  (pas de serveur whois accessible) — pas de données whois obtenues.
- `dig +short A/AAAA/NS/MX/TXT ctf.tg` (artifacts/dig.log) :
  - A: `104.21.67.127`, `172.67.174.201` (IP Cloudflare anycast, pas l'IP réelle)
  - AAAA: `2606:4700:3032::6815:437f`, `2606:4700:3033::ac43:aec9` (Cloudflare)
  - NS: `wally.ns.cloudflare.com.`, `hal.ns.cloudflare.com.` → **proxy Cloudflare
    complet**, IP d'origine masquée. Conforme à la règle "pas de scan sur
    l'infra hébergeur" — de toute façon inutile ici (CF anycast).
  - MX: `mxa.mailgun.org`, `mxb.mailgun.org` (10) — mail via Mailgun.
  - TXT: `v=spf1 include:amazonses.com include:mailgun.org ~all` +
    `brevo-code:...` (vérifications SPF/Brevo, rien d'exploitable).
  - `www.ctf.tg` A → mêmes IP Cloudflare ; pas de CNAME direct observé.
  - `arena.ctf.tg` A → mêmes IP Cloudflare (même compte CF, confirmé mais pas
    sondé plus — hors périmètre).
- TLS SANs (`openssl s_client` + `x509 -text`, artifacts/tls_sans.log) :
  `DNS:ctf.tg, DNS:*.ctf.tg` — certificat **wildcard générique**, aucun
  sous-domaine distinct révélé par le certificat lui-même.

## 2. Headers HTTP / fingerprint techno

- `curl -I https://ctf.tg/` (artifacts/headers_root.log) → **200**, `server:
  cloudflare`, `content-type: text/html`, `last-modified: Fri, 30 Oct 2026
  10:00:41 GMT`, `accept-ranges: bytes`, `cf-cache-status: DYNAMIC` (pas de
  `cache-control` renvoyé sur `/` — probablement non caché par CF, chaque
  requête retourne à l'origine).
  CSP complète observée (voir note ci-dessus) : extrêmement restrictive.
  `x-frame-options: DENY`, `strict-transport-security`, `nosniff`,
  `permissions-policy` verrouillée, `cross-origin-opener-policy: same-origin`.
  **Aucun cookie posé.**
- `curl -I https://www.ctf.tg/` → **301** vers `https://ctf.tg/` (redirection
  canonique propre).
- `curl -I http://ctf.tg/` (artifacts/http_plain.log) → **301** vers
  `https://ctf.tg/` (pas de service HTTP brut distinct).
- `/robots.txt` → **200**, cache HIT, contenu = politique générique "content
  signals" (AI/search crawling), **aucune ligne `Disallow`** réelle — pas un
  robots.txt "classique" indiquant des chemins cachés.
- `/sitemap.xml`, `/.well-known/security.txt` → **404** / **403** (page 404
  custom "NCTF26" cohérente sur `/sitemap.xml`; **403 avec bannière `nginx/1.27.5`
  brute** sur `/.well-known/security.txt` — fuite mineure confirmant que
  l'origine tourne sous nginx et bloque les chemins "cachés" par une règle
  générique `deny all` (confirmé en section 4, tous les dotfiles → 403 identique
  len=1267, pas un 404 — donc règle de blocage générique, pas une absence de
  fichier).

## 3. Contenu complet de la home page (`artifacts/home.html`)

Page **100% statique**, pas de formulaire (`<form>`), pas de champ `<input>`,
pas d'appel `fetch`/XHR vers une API. Structure :
- `window.NCTF = {...}` : objet de config JS inline (textes, dates, compteurs
  d'épreuves, lien `arena: "https://arena.ctf.tg"`). Purement cosmétique
  (anime l'intro cinématique et le countdown côté client).
- Section `#palmares` (`hidden`) + `<script type="application/json"
  id="palmares-data">` : classement des 3 éditions précédentes (2023-2025),
  rendu côté client par `site.js` (pas de backend, juste du JSON inline
  démasqué en JS).
- Section créateurs : liste de pseudos GitHub/LinkedIn des auteurs d'épreuves
  (`Hibris` = architecte plateforme, lien LinkedIn `hi3ris`).
- Footer : **"Powered by Hibris · ramses.dagban.tg"** — framework/générateur
  de site maison, pas un CMS connu (pas WordPress/Ghost/Next.js — aucune trace
  `_next/`, `wp-content`, `wp-json`, meta `generator`).
- Page 404 custom contient une chaîne octale easter-egg :
  `160157167145162145144...` → décodée = **"powered by h13ris"** (confirmation
  de marque, pas une piste d'exploitation).

## 4. Probing léger config/admin/dotfiles (1 req/~1.2s, GET uniquement)

Résultats (`curl -o /dev/null -w "%{http_code}"`, un par chemin) :

| Chemin | Code | Note |
|---|---|---|
| `/.git/HEAD` | 403 | bloqué par règle générique dotfile, pas exposé |
| `/.git/config` | 403 | idem |
| `/.env` | 403 | idem |
| `/.env.local` | 403 | idem |
| `/.DS_Store` | 403 | idem |
| `/config.json` | 404 | page 404 custom |
| `/package.json` | 404 | — |
| `/humans.txt`, `/ads.txt`, `/security.txt` | 404 | — |
| `/CHANGELOG.md`, `/README.md`, `/version.json`, `/manifest.json` | 404 | — |
| `/_next/static` | 404 | pas Next.js |
| `/admin`, `/wp-login.php` | 404 | pas de panneau admin, pas WordPress |
| `/cdn-cgi/trace` | 200 | trace Cloudflare standard (info réseau CF, pas origine) |

→ Tous les 403 ont le **même corps (len=1267)** = page d'erreur générique,
donc règle de blocage par motif (dotfiles/well-known), pas une fuite
fichier-par-fichier. Aucun fichier de config/CMS/admin exposé.

## 5. Analyse `site.js` (`artifacts/site.js`, 769 lignes)

Grep sur `fetch|XMLHttpRequest|api/|endpoint|admin|auth|token|POST|PUT|PATCH` :
**zéro résultat pertinent** côté réseau. Le fichier est quasi exclusivement une
animation 3D/caméra (effet cinématique d'intro) + gestion `localStorage` pour
ne jouer l'intro qu'une fois par visiteur (`nctf-intro-seen`). Aucun appel
réseau dynamique, aucune route API cliente. Confirme : zéro logique
serveur/applicative pilotée depuis le front sur ce domaine.

## 6. Tests d'injection légers (Host header / cache)

- **SNI=ctf.tg + `Host: evil-test.invalid`** (artifacts/host_tamper.log) →
  **403 immédiat côté edge Cloudflare** (`cf-ray` présent, corps 151 octets,
  générique) — Cloudflare rejette lui-même le mismatch Host avant d'atteindre
  l'origine. Pas de vecteur de cache poisoning par ce biais.
- **`X-Forwarded-Host: evil-test.invalid`** (artifacts/xfh_tamper.log) →
  **200 normal**, `evil-test` absent du corps (grep -c = 0) — header non
  reflété nulle part, pas de SSRF/poisoning via ce header.
- `cf-cache-status: DYNAMIC` sur `/` (vs `HIT` sur `/robots.txt`) confirme que
  la page d'accueil n'est probablement pas mise en cache par CF (ou
  `cache-control: no-store` côté origine) — réduit encore la surface de cache
  poisoning côté edge pour ce chemin précis.

## 7. OSINT passif (zéro requête vers ctf.tg)

- `crt.sh` (CT logs, `%.ctf.tg`) → **502 Bad Gateway** (service tiers
  temporairement indisponible, pas un résultat sur la cible).
- Wayback Machine CDX (`web.archive.org`) → **"Temporarily Offline"** (idem,
  service tiers down, pas de données obtenues).
- Recherche web "ctf.tg Hibris github" + "ramses.dagban.tg github Hibris" →
  pas de dépôt source public trouvé directement lié à `ctf.tg`. Profil
  LinkedIn `hi3ris` = Ramsès Japhet Dagban (Lomé, Togo) confirmé comme
  probable auteur/architecte de la plateforme CTFd-like thémée "Hibris".
  Compte GitHub `ramses26` identifié par recherche mais **0 repo public**
  (`https://api.github.com/users/ramses26/repos` → `[]`). Piste OSINT dans
  une impasse pour l'instant (pas de code source public localisé).

---

## 8. Hypothèse priorisée : domain takeover via CNAME dangling (cf.
   `knowledge/patterns/web/forge-domain-takeover-dangling-cname.md`)

**Conclusion : hypothèse NON confirmée sur `ctf.tg`, probablement écartée.**
Investigation complète (lecture/OSINT uniquement, zéro tentative de
revendication) :

### 8.1 Délégation DNS complète à Cloudflare (pas un simple CNAME tiers)

- `dig NS ctf.tg` (plusieurs résolveurs 1.1.1.1/8.8.8.8/trace) →
  `wally.ns.cloudflare.com.` + `hal.ns.cloudflare.com.` : **la zone entière
  est déléguée à Cloudflare** (NS au registre `.tg`), pas juste un enregistrement
  CNAME ajouté chez un registrar tiers vers `*.pages.dev`/`*.netlify.app`.
  C'est la configuration "full Cloudflare" classique (CDN/WAF devant un
  serveur quelconque), pas le pattern typique des plateformes
  d'hébergement statique où le domaine reste chez un registrar externe avec
  juste un CNAME ajouté.
- Requêtes CNAME directes (`dig @1.1.1.1/@8.8.8.8 ctf.tg CNAME`, DoH JSON
  `https://dns.google/resolve?name=ctf.tg&type=CNAME`,
  `https://cloudflare-dns.com/dns-query?name=ctf.tg&type=CNAME`) → **aucune
  réponse CNAME exposée**, seulement les 2 IP anycast Cloudflare habituelles
  en type A (`104.21.67.127`, `172.67.174.201`). C'est attendu : quand
  Cloudflare est autoritaire ET que le domaine est proxied (orange cloud),
  l'éventuel CNAME interne (ex. vers un projet Pages) est "flatten" et
  invisible depuis l'extérieur — **limite OSINT fondamentale, pas une absence
  de preuve en soi**.
- `dig +trace` confirme la chaîne complète `.` → `tg.` (ns1/ns2.nic.tg,
  ns*.admin.net, tld.cafe.tg) → `ctf.tg.` (NS Cloudflare) → réponse A finale,
  rien d'anormal dans la délégation.

### 8.2 Sous-domaines : aucun CNAME dangling trouvé

Brute-force léger (1 req/sous-domaine, lecture DNS uniquement) sur
`www, mail, staging, dev, preview, api, deploy, admin, mg, smtp, blog, shop,
status, docs, cdn, beta, demo, portal` + `arena` (déjà connu) :
- Seuls `www.ctf.tg` et `mail.ctf.tg` répondent (IP Cloudflare identiques aux
  2 IP anycast de l'apex) — tous les autres : **NOERROR/NODATA** (pas de
  record du tout), confirmé différent d'un vrai NXDOMAIN wildcard (test de
  contrôle sur un sous-domaine aléatoire `zzzqqqnonexistent*.ctf.tg` → même
  NOERROR/NODATA vide, donc ce n'est **pas** un catch-all wildcard : `mail` et
  `www` ont bien des enregistrements intentionnels, les autres n'existent
  juste pas).
- CT logs `crt.sh` (`%.ctf.tg`, retry après 502 initial → 200 OK cette fois) :
  **seulement des certificats wildcard `*.ctf.tg` + `ctf.tg`** (Google Trust
  Services / Let's Encrypt, historique 2026-05 à 2026-11). Aucun certificat
  spécifique à un sous-domaine distinct émis séparément → pas de sous-domaine
  caché révélé par les logs de certificats.
- `mail.ctf.tg` → **HTTP 520** côté Cloudflare ("origin returned unknown
  error"), pas un message "project not found"/"there isn't a site here"
  propre à une plateforme d'hébergement statique. Cohérent avec : même IP
  origin (nginx) que l'apex, mais pas de vhost nginx configuré pour ce
  hostname précis → erreur générique de connexion à l'origine, **pas un
  signal de dangling CNAME sur une plateforme tierce**.

### 8.3 Preuve contraire forte : fingerprint nginx, pas une plateforme statique

- `curl -D - https://ctf.tg/.well-known/security.txt` → **403**, header
  `server: cloudflare` (CF réécrit toujours ce header), MAIS **le corps HTML
  brut contient littéralement `<center>nginx/1.27.5</center>`**
  (artifacts/sec.body, capturé cette session). C'est la page d'erreur nginx
  par défaut, transmise telle quelle par Cloudflare (CF ne réécrit que le
  header `Server`, pas le corps HTML renvoyé par l'origine). **Cloudflare
  Pages / Netlify / Vercel / GitHub Pages ne génèrent jamais ce genre de page
  d'erreur nginx native** — ces plateformes servent leurs propres pages
  d'erreur brandées, sans jamais exposer de bannière nginx versionnée.
- `artifacts/deploy_paths_probe.log` (déjà présent, confirmé cette session) :
  chemins spécifiques à l'écosystème Cloudflare Pages/Workers
  (`/_worker.js`, `/_routes.json`, `/_headers`, `/_redirects`, `/functions/`,
  `/_next`, `/_astro`) renvoient tous **exactement la même page 404 custom
  "NCTF26"** que n'importe quel chemin inexistant — aucun comportement
  spécifique de framework statique détecté.
- Conclusion technique : l'origine réelle derrière le proxy Cloudflare est un
  **serveur nginx classique auto-hébergé** (VPS/dédié), pas une plateforme
  d'hébergement statique multi-tenant à la Pages/Netlify/Vercel/GitHub Pages.
  Le pattern "domain takeover via CNAME dangling" **suppose justement** une
  telle plateforme multi-tenant comme cible — la preuve nginx contredit
  directement cette précondition pour `ctf.tg`.

### 8.4 Point annexe hors-scope (à ne PAS toucher) : `ramses.dagban.tg` sur Netlify

En vérifiant le lien du footer `ctf.tg` ("Powered by Hibris ·
ramses.dagban.tg", le site personnel de l'architecte plateforme), son
`curl -D -` révèle un header `x-nf-request-id` → **ce domaine personnel est
hébergé sur Netlify**. C'est une curiosité OSINT sur l'auteur (il utilise
Netlify pour son propre portfolio), **mais ce domaine est explicitement
hors périmètre** de l'épreuve (scope strict = `ctf.tg` uniquement, pas
l'infra/les comptes personnels de l'architecte) et aucune action n'a été
tentée dessus. Recherche GitHub du compte lié (`hi3ris`, confirmé par le lien
`github.com/hi3ris` dans le footer de son site, 32 repos publics) : **aucun
repo nommé `ctf.tg`, `nctf26`, `Hibris` ou équivalent** — le framework
"Hibris" qui propulse `ctf.tg` reste à code source privé/non localisé. (Note :
le compte `ramses26` évoqué dans une session précédente avec 0 repo est un
compte différent et non confirmé comme lié — `hi3ris` est le compte réellement
lié depuis le footer du site.)

### 8.5 Conclusion de cette piste

**Pas de hostname dangling confirmé sur `ctf.tg`.** La zone est pleinement
déléguée à Cloudflare (pas un simple CNAME ajouté chez un registrar tiers),
aucun sous-domaine ne pointe vers une plateforme d'hébergement statique
connue, et le fingerprint nginx contredit l'hypothèse d'une cible multi-tenant
du type Pages/Netlify/Vercel/GitHub Pages. Recommandation : **ne pas creuser
davantage cette piste sur `ctf.tg`** sauf nouvelle preuve ; le vecteur
"Hibris" (framework interne, source non publique) ou l'énoncé officiel du
défi (section suivante, toujours non lu) restent les pistes les plus
prometteuses.

---

## 9. Chemins de déploiement non-indexés (2026-11-06, agent recon #2)

Test de 18 chemins (`artifacts/deploy_paths_probe.log`), statut + taille + sha256 du
body, débit ~1 req/s :

| Chemin | Code | Taille | Note |
|---|---|---|---|
| `/preview`, `/preview/`, `/rebuild`, `/deploy`, `/api`, `/api/`, `/api/rebuild`, `/api/deploy`, `/_next`, `/_astro`, `/_routes.json`, `/functions/`, `/_headers`, `/_redirects`, `/sitemap.xml` | 404 | 2571 | page 404 custom NCTF26 |
| `/_worker.js` | 404 | 1457 | 404 custom identique (texte), **mais cache-control/HIT** (voir ci-dessous) |
| `/.well-known/security.txt` | 403 | 153 | règle générique dotfile (déjà connu) |
| `/robots.txt` | 200 | 1248 | déjà connu |

**Sha256 variable sur un même chemin rejoué deux fois** (`/preview` : `a67ad29c...`
puis `69418d27...`) → **PAS un signal**. Cause identifiée : Cloudflare injecte un
snippet anti-bot (`__CF$cv$params`, `cf-ray` + timestamp aléatoires) en fin de
`<body>` à chaque requête. Le corps "métier" (titre, texte 404, octal easter-egg,
footer Hibris) est strictement identique partout. **Aucun chemin testé n'est != 404
hormis les 403/200 déjà connus. Aucune fuite de taille/contenu exploitable.**

Investigation complémentaire sur `/_worker.js` (seul à être `cf-cache-status: HIT`,
`cache-control: max-age=14400` au lieu de `DYNAMIC`) : **pas un indice de plateforme**.
Reproduit à l'identique sur des chemins bidon `/qzxcv123.js`, `/qzxcv123.css`,
`/qzxcv123.png` (tous `cache-control: max-age=14400`, `MISS` puis `HIT`) vs
`/qzxcv123.json`, `/qzxcv123` (`DYNAMIC`) → c'est une **règle de cache Cloudflare
générique par extension de fichier statique** (`.js/.css/.png` cachés même en 404),
indépendante de l'origine. Pas un fingerprint Pages/Workers. **Piste invalidée.**

## 10. Fingerprint 404 des hosts `*.pages.dev` — NON EXÉCUTÉ (conflit de règles)

La tâche demandait de sonder `ctf-tg.pages.dev`, `ctf.pages.dev`, `nctf26.pages.dev`,
`hibris.pages.dev`, `hibris-ctf.pages.dev`, `nctf-ctf.pages.dev`, `defi1.pages.dev`.

**Décision : non exécuté, pour deux raisons cumulatives :**
1. Ces hosts sont sur le domaine partagé `pages.dev`, qui appartient à Cloudflare
   (pas à `ctf.tg`) — les règles d'engagement explicites de cette mission disent
   "Cible autorisée : UNIQUEMENT https://ctf.tg lui-même. [...] Rien sur l'infra
   sous-jacente Cloudflare", marquées "à respecter absolument". Deviner et requêter
   des noms de projet sur l'espace de noms public partagé `pages.dev` revient à
   sonder l'infra Cloudflare elle-même (et risque de toucher un projet tiers sans
   rapport si un de ces noms existe déjà pour quelqu'un d'autre), pas `ctf.tg`. Je
   donne la priorité à la règle d'engagement explicite sur l'instruction de tâche.
2. **La prémisse technique est de toute façon invalidée** : la section 8.3
   (ce document, agent précédent) a établi par preuve directe (bannière
   `nginx/1.27.5` brute qui fuite dans le corps HTML d'un 403) que l'origine réelle
   de `ctf.tg` est un **serveur nginx auto-hébergé classique**, pas Cloudflare
   Pages / Workers Static Assets / R2. Chercher un fingerprint "projet Pages" sur
   `*.pages.dev` n'aurait de toute façon rien trouvé de pertinent même sans le
   conflit de règle.

**Signal humain requis si vous voulez lever cette restriction explicitement** (ex.
confirmer que sonder le namespace `pages.dev` est accepté comme "ctf.tg
infrastructure-adjacent OSINT passif" plutôt que "infra Cloudflare") — mais vu le
point 2, l'intérêt pratique de lever cette restriction semble faible.

## 11. Recherche code source public ("Hibris", `ctf.tg`, strings uniques)

Recherches (WebSearch + tentatives grep.app/GitHub code search/Sourcegraph, toutes
passives, zéro requête vers `ctf.tg`) :

- `grep.app` → **HTTP 429** (rate-limited) sur les deux requêtes tentées
  (`cine-stage palmares-data`, `ramses.dagban.tg`), même après backoff de 8s.
- GitHub code search (`github.com/search?type=code`) → page d'accueil "Sign in to
  search code", pas de résultat sans compte authentifié.
- Sourcegraph → requête tronquée côté rendu, aucun résultat exploitable obtenu.
- WebSearch `"Hibris" ctf.tg platform github`, `"ramses.dagban.tg" github`,
  `"ctf.tg" site:github.com`, `"NCTF" "Hibris" dagban github.com OR gitlab.com` →
  **zéro dépôt public trouvé** contenant une chaîne unique de `home.html`/`site.js`
  ou le domaine `ctf.tg` en clair.
- **Trouvaille utile (indirecte)** : profil LinkedIn `hi3ris` (Ramsès Japhet Dagban,
  Lomé) liste un projet "**NCTF25**" décrit comme "plateforme CTFd dockerisée avec
  thème personnalisé 'Hibris' (couleurs togolaises)". Ceci confirme que "Hibris" =
  marque personnelle de l'auteur, appliquée à **CTFd pour la plateforme challenges**
  (= `arena.ctf.tg`, hors périmètre) **et** réutilisée comme signature sur le site
  statique `ctf.tg` (footer "Powered by Hibris"). Ne révèle **aucun dépôt public**
  pour le générateur de site statique de `ctf.tg` lui-même — toujours 0 repo
  `ramses26` et aucun miroir/fork trouvé ailleurs.

**Conclusion tâche 3 : piste code source toujours dans une impasse.** Aucun repo
public, aucune fuite de code via moteurs de recherche de code passifs. Cohérent
avec la section 8.4 (agent précédent) : le compte GitHub réellement lié depuis le
footer (`hi3ris`, 32 repos publics) ne contient lui non plus aucun repo
`ctf.tg`/`nctf26`/`Hibris`.

## 12. DNS/WHOIS complet (retry, 2026-11-06 ~19:25 UTC)

- **WHOIS `.tg` (passif, consultation seule, aucune action)** réussi cette fois
  (`artifacts/whois_full_retry.log`) :
  - Registrar : **NETMASTER SARL**
  - `Activation: 2026-11-06` (= **aujourd'hui**), `Expiration: 2028-06-20`,
    `Status: Activé`, contact intégralement `[PRIVEE]` (whois privacy).
  - Serveurs de noms **déclarés côté registre** : `mia.ns.cloudflare.com`,
    `norman.ns.cloudflare.com` — **différents** de la délégation DNS réellement
    observée en live (`wally.ns.cloudflare.com`, `hal.ns.cloudflare.com`, cf.
    section 1). Les deux sont des NS Cloudflare légitimes (juste une paire
    anycast différente) — pas une anomalie exploitable, probablement une
    resynchronisation registre/zone récente. Le champ `Activation` à la date du
    jour est notable mais **non interprété comme un signal d'attaque** : peut
    correspondre à un renouvellement/sync administratif coïncidant avec
    l'ouverture du CTF, pas à une preuve d'action possible de notre côté (et
    aucune action de renouvellement/transfert n'a été, ou ne sera, initiée —
    conforme à la règle DNS/WHOIS passif).
- **DNS complet** (`dig`, A/AAAA/MX/TXT/CAA/NS/SOA) : cohérent avec section 1.
  **CAA : vide** (aucun enregistrement — n'importe quelle CA publique peut émettre
  pour `ctf.tg`, mais ça ne nous donne aucun levier, juste une absence de
  durcissement mineur côté CA).
- **DMARC** (`_dmarc.ctf.tg` TXT) : `v=DMARC1; p=quarantine; pct=100; adkim=r;
  aspf=r; rua=mailto:...@dmarc-reports.cloudflare.net`. **Pas un DMARC absent ou
  `p=none`** — politique `quarantine` à 100%, alignement `relaxed` : c'est une
  politique **raisonnablement durcie**, pas le signal "misc mail spoofing"
  classique espéré par la tâche. SPF reste en `~all` (softfail) mais DMARC en
  quarantine limite déjà l'usurpation visible côté boîte de réception — piste
  mail spoofing **faible/non concluante**, pas creusée davantage (DKIM selectors
  usuels `mailo/mg/k1/smtp._domainkey` tous vides — énumération exhaustive de
  sélecteurs DKIM écartée pour rester dans la règle "pas de bruteforce actif").
- **Sous-domaines testés en DNS passif** (`mail`, `email`, `mg`, `smtp`, `dev`,
  `staging`, `admin`, `api`, `preview`, `deploy`) : seuls `mail.ctf.tg` (A → IP
  Cloudflare identiques au root, probablement même zone proxée, pas un service
  distinct) et `email.ctf.tg` (CNAME → `mailgun.org`, config SPF/mailgun standard)
  résolvent. Tous les autres : **NXDOMAIN/vide**. Testé une sous-domaine aléatoire
  bidon (`zzzz-random-nonexistent-sub.ctf.tg`) → vide aussi, donc **pas de DNS
  wildcard** sur `*.ctf.tg` (les réponses ci-dessus sont de vrais enregistrements,
  pas un artefact de wildcard).
- **crt.sh retry** (`artifacts/crtsh_retry2.json`, requête `q=ctf.tg` a fonctionné
  cette fois — la requête `q=%25.ctf.tg` avec wildcard a re-timeout) : **76 certs**
  historiques depuis 2023-07-04. Tous les certs récents (2026) sont des wildcards
  `*.ctf.tg` + `ctf.tg` (Let's Encrypt / Google Trust Services) → confirme la
  config actuelle (CF + cert wildcard générique, aucun sous-domaine distinct
  révélé pour l'édition en cours).
  **Trouvaille historique intéressante** : 3 certs cPanel AutoSSL
  (2024-05-22 → 2024-11-10, expirant 2025-02-08) couvrant
  `cpanel.ctf.tg, cpcalendars.ctf.tg, cpcontacts.ctf.tg, webdisk.ctf.tg,
  webmail.ctf.tg` → **le domaine tournait sur un hébergement cPanel classique en
  2024** (probablement pour l'édition NCTF24), avant la migration vers
  Cloudflare + site statique observée aujourd'hui. **Vérifié en DNS passif
  (`dig`) : aucun de ces 5 sous-domaines ne résout plus actuellement** (NXDOMAIN/
  vide) → pas de serveur d'origine cPanel encore joignable, pas de contournement
  Cloudflare possible par ce biais. Piste historique intéressante pour le
  contexte, **mais sans vecteur actif exploitable aujourd'hui**.

## 13. Conclusion actionnable finale (agent recon #2, 2026-11-06 ~19:30 UTC)

(a) **Aucun vecteur d'écriture réaliste trouvé sur `ctf.tg`** à ce stade :
    18 chemins de déploiement testés (§9) → tous 404 identiques (sha256 variable
    uniquement à cause du snippet anti-bot CF, pas du contenu) ou 403/200 déjà
    connus ; origine confirmée **nginx auto-hébergé** via fuite de bannière brute
    `nginx/1.27.5` dans un corps 403 (§8.3, agent précédent) — donc pas une cible
    de type "plateforme d'hébergement statique multi-tenant" (Pages/Netlify/
    Vercel) où un takeover de sous-domaine ou un repo de déploiement public
    serait le vecteur classique ; aucun CNAME dangling (§8) ; aucun dépôt source
    public pour le générateur "Hibris" ni sur `ramses26` ni sur le vrai compte lié
    `hi3ris` (§11) ; aucun ancien sous-domaine cPanel encore joignable pour
    contourner Cloudflare (§12) ; DMARC `p=quarantine` raisonnablement durci, pas
    le signal "mail spoofing" espéré (§12).
(b) **La piste web/infra directe sur `ctf.tg` est morte** avec les méthodes
    passives/légères autorisées : statique pur, CSP durcie, pas de formulaire/API,
    pas de fichier de config exposé, pas de plateforme de déploiement multi-tenant
    révélée, pas de code source public. Reste non exécuté : un sondage actif de
    `*.pages.dev` (hors scope + sans intérêt vu (a)), et surtout **la lecture de
    l'énoncé officiel du défi** (très probablement `/plugins/defi_gate/` sur
    `arena.ctf.tg`, hors périmètre strict de cet agent — outillage déjà en place :
    `src/tools/ctf/nctf26_client.py` + session `nctf26_storage_state.json`), qui
    reste la seule étape non-exploratoire restante avant de confirmer définitivement
    une impasse totale.
(c) Cette conclusion ne recommande aucune action d'abandon — elle indique
    seulement qu'aucun vecteur d'écriture n'a été démontré sur `ctf.tg` par cet
    agent avec les contraintes passives/légères imposées ; la décision de
    continuer, pivoter (lecture de l'énoncé officiel) ou abandonner appartient
    exclusivement à l'équipe humaine.

## 14. Statut : blackbox-exhausted (2026-11-06, ~19h30 Lomé)

Trois rounds de sondage (2 agents + vérification directe de cette session), tous
en lecture/OSINT strict, cible = ctf.tg uniquement, zéro action destructive :

- Site 100% statique, une seule page (tous les href="#..." sont des ancres
  internes à la même page, aucune autre route découverte).
- Origine réelle = nginx auto-hébergé (fuite de bannière `nginx/1.27.5` dans un
  403 brut sur `/.well-known/security.txt`) derrière Cloudflare — pas une
  plateforme multi-tenant Pages/Netlify/Vercel/GitHub Pages => pas de CNAME
  dangling possible.
- Aucun repo source public pour "Hibris"/ctf.tg (compte réel `hi3ris`, 32 repos,
  rien lié).
- Comptes GitHub des créateurs d'épreuves listés en crédits (`Algorithme123`,
  `BoazAK`, `thierry8petstar`, `Oxdefault`, `The-darknova`, `fullaccess5`)
  passés en revue individuellement : `BoazAK/Workers` = app Django "gestion RH"
  sans rapport ; `Oxdefault/ppe-site` = repo GitHub Pages avec CNAME mais pointe
  sur `agridrone.ipnetuniversity.net`, projet scolaire sans rapport. Rien
  d'exploitable.
- DNS/WHOIS complet (NS Cloudflare, DMARC quarantine correct, crt.sh historique
  cPanel 2024 qui ne résout plus, pas de sous-domaine caché).

**Conclusion** : aucun vecteur d'écriture démontré sur ctf.tg avec les méthodes
passives/légères autorisées par les règles d'engagement du défi (cible =
ctf.tg uniquement, pas de DoS/social/bruteforce infra). Marqué
blackbox-exhausted au sens du protocole CTFAgent -- pas de nouvelle piste
technique identifiée sans sortir du périmètre ou passer en actif plus agressif,
ce qui nécessite une décision d'équipe (pas une décision de l'agent seul).
Toujours PAS d'abandon recommandé ni envisagé par l'agent -- décision humaine
exclusivement.
