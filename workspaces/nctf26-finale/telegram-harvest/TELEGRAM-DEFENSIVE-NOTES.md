# Telegram CYBERSÉCURITÉ — notes DÉFENSIVES pour la finale A&D (2026-11-13)

Synthèse orientée détection/défense des 5 PDFs (convertis en .txt dans `pdfs/`). Faits cités
par fichier + ligne. Sections offensives volontairement résumées au niveau "catégorie + détection"
(les commandes brutes restent dans les .txt pour lecture directe). Rien n'est reproduit comme
procédure offensive clé en main.

## A. Inventaire
| Fichier (.txt) | ~lignes | Sujet |
|---|---|---|
| exfiltration-donnees-binaires-linux-fr | 363 | Exfiltration via LOLBins Linux (article public Hacking Articles / GTFOBins) |
| Rapport_ZTE_MF293N2_Auth_Bypass | 322 | Analyse défensive du login web routeur ZTE MF293N2 (challenge-response) |
| Phases_du_hacking_ethique_FR | 78 | Infographie : 5 phases du hacking éthique |
| Techniques_d_ing_nierie_sociale | 158 | Infographie : 10 techniques d'ingénierie sociale |
| Mythe_vs_r_alit | 18 | Sécurité physique (alarme vs vidéosurveillance) — hors CTF |

## B. Résumé par document (fidèle)
- **Exfiltration LOLBins** : article traduit (Raj/Jeenali Kothari, Hacking Articles, source l.362-363,
  renvoie à GTFOBins l.358). Montre comment des binaires Linux légitimes servent à sortir un fichier
  d'une machine vers un attaquant, regroupés en 2 familles : binaires par défaut (l.14) et binaires
  installés via apt (l.16). Canaux : TCP brut, HTTP POST, TLS, serveurs HTTP locaux.
- **ZTE MF293N2** : rapport méthodique (auteur Dan Maluma, matériel perso/LAN, l.1-17). Démontre que
  le mot de passe admin n'est ni en clair (H1 invalidée l.98) ni un simple SHA-256 (H2 invalidée l.152)
  mais un double hachage salé par un nonce de session. Finit sur des recommandations (l.307-317).
- **5 phases** (l.1-64) : Reconnaissance → Analyse → Prise d'accès → Maintien → Dissimulation des traces,
  avec l'insistance sur l'autorisation (l.33-35) et, en éthique, le but = tester détection/réponse (l.56-60).
- **10 techniques d'ingénierie sociale** (l.6-148) : phishing, smishing, vishing, quishing, baiting,
  scareware, quizzing/social-media-mining, tailgating, dumpster diving, scamming.
- **Mythe vs réalité** : sécurité physique (alarme + vidéosurveillance + télésurveillance + contrôle
  d'accès). Non pertinent pour le CTF.

## C. Exfiltration Linux — angle DÉTECTION (le plus utile en défense A&D)
Fait (fichier exfiltration) : la technique repose sur des binaires système légitimes qui, après
lecture d'un fichier sensible, ouvrent une connexion sortante. Familles citées : `wget`/`curl`
(HTTP POST, l.70-78, 221-230), `bash`/`ksh` via `/dev/tcp` (l.120-129, 298-307), `openssl s_client`
(TLS, l.142-152), `nc` (TCP, l.191-200), `whois`/`finger` (l.95-103, 249-258), serveurs locaux
`busybox httpd`/`php -S`/`ruby httpd`/`irb+webrick` (l.168-348).

À surveiller sur TA box (défense) — déductions/recommandations :
- **Processus → réseau anormal** : un binaire comme `nc/curl/wget/openssl/finger/whois` qui ouvre une
  connexion sortante peu après la lecture d'un fichier flag/`/etc/passwd`. (auditd `execve` + `connect`.)
- **`/dev/tcp/<ip>/<port>`** dans une ligne `bash -c`/`ksh -c` = quasi-signature d'exfil/reverse.
- **Listeners inattendus** sur ta box : `busybox httpd`, `php -S`, `ruby -run -e httpd`, webrick,
  `python -m http.server` → `ss -tlnp`/`netstat` ; tout service HTTP non prévu = suspect.
- **Egress** vers IP/port non standard, **HTTP POST avec un corps = contenu de fichier**, pics DNS.
- IoC composite : *lecture fichier sensible* + *spawn d'un client réseau* + *sortie vers IP d'équipe adverse*.
Prévention/réponse A&D : filtrage sortant (n'autoriser que le trafic du checker SLA), règles auditd sur
l'`execve` de ces LOLBins avec arguments réseau, `pcap_watch.py` sur tes propres ports, kill + rotation
si un listener non prévu apparaît. (Ne jamais couper le service légitime attendu par le checker.)

## D. ZTE MF293N2 — angle DÉFENSIF
Nature (fait, fichier ZTE) : interface d'admin web locale accessible sans auth réseau préalable (l.23-27),
servie en **HTTP clair** (port 80, l.84). Le login utilise un **challenge-response** : le client récupère
un nonce `LD` via `GET /goform/goform_get_cmd_process?...cmd=LD` (l.86-89) puis POST
`/goform/goform_set_cmd_process` avec `password` = **SHA256( SHA256(mdp) + LD )** (algorithme exposé
côté client dans `js/service.js`, l.166-201). Le champ `password` fait 64 hex (l.97).
Conditions d'exploitation (faits, l.29-31, 205-216, 291-297) : attaquant **passif sur le LAN**, trafic
en **HTTP non chiffré**, et **mot de passe faible/par défaut** — ici `admin` retrouvé via rockyou
(l.271). Le nonce `LD` empêche le **rejeu** d'un hash d'une session antérieure (l.214) mais pas une
attaque par dictionnaire **hors-ligne** une fois la paire (hash, LD) + l'algo connus. Piège méthodo
(l.249-252) : la **casse hexadécimale** diffère entre le JS (majuscules) et `hashlib` Python (minuscules)
— tester les 4 combinaisons.
Vérification défensive (recommandations, l.307-317) : l'admin est-il en HTTP (pas HTTPS) ? mot de passe
par défaut/faible ? → changer le mdp, activer HTTPS, éviter l'admin via HTTP sur réseau partagé ;
côté fabricant, KDF serveur (PBKDF2/Argon2) au lieu d'un schéma reconstructible côté client.
Classe réutilisable : *auth challenge-response entièrement reconstructible côté client sur canal clair*
→ repérable dès qu'un login web fait du hashing en JS + transporte un nonce ; la vraie protection = TLS
+ KDF serveur + mdp fort.

## E. Indicateurs clés (quoi chercher, pourquoi)
- `/dev/tcp/` dans un process bash/ksh → canal réseau natif sans binaire réseau ⇒ exfil/reverse shell.
- Nouveau **listener** non prévu (httpd busybox/php/ruby/python) ⇒ serveur de fichiers monté par l'adversaire.
- `execve` de `nc/curl/wget/openssl/whois/finger` avec args réseau juste après lecture d'un flag ⇒ exfil.
- Login web qui **GET un nonce** puis **POST un hash 64-hex** sur **HTTP** ⇒ challenge-response en clair, cassable hors-ligne.
- HTTP POST dont le corps = contenu brut d'un fichier ⇒ transfert de données sortant.

## F. Utile pour résoudre/défendre la finale (séparé du bruit)
Actionnable : (1) la **check-list détection exfil** (section C) sur ta propre box = cœur du blue-team A&D ;
(2) la **classe ZTE** = réflexe pour tout login web maison (nonce + hash JS sur HTTP) ; (3) les 5 phases =
cadre de recon rapide sur un service. Bruit/awareness : ingénierie sociale et sécurité physique — hors
format A&D technique, à ignorer pendant le match.

## G. Erreurs d'analyse à éviter
- Conclure "hash non cassable" trop vite : un format propriétaire (bad hash Pcredz, l.100-104) peut juste
  être un wrapper d'algo standard → inspecter le JS, pas seulement lancer John/Hashcat.
- Oublier la **casse hex** (l.249-252) → faux négatifs de cracking.
- Dissocier (hash, LD) : inutilisable séparément (l.211-212).
- En défense : couper un service pour "sécuriser" et faire échouer le checker SLA (ne jamais faire).
- Confondre un listener légitime (service de jeu) avec un listener d'exfil : vérifier le process/propriétaire.

## H. À vérifier dans l'environnement du challenge (le jour J)
- Quels binaires réseau sont présents sur ma box (`which nc curl wget openssl busybox php ruby finger`) ?
- `auditd`/EDR dispo pour tracer `execve`+`connect` ? sinon, `ss -tlnp` + surveillance pcap manuelle.
- Politique d'egress : puis-je bloquer tout sortant sauf le checker ? quelle IP/port est le checker ?
- Mes services web font-ils du hashing côté client / transportent-ils un nonce sur HTTP ?
- Où sont mes flags (chemins montés read-only) et quels process ont le droit de les lire ?
