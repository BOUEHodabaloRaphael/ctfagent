# CEH M05 - Vulnerability Analysis (synthese offensive)

Source: `CEHv13 - Module 05 - Vulnerability Analysis hide01.ir.pdf` (78 pages), OCR complet.
Theorie d'examen omise volontairement; ne garder que ce qui sert en CTF/pentest reel.

## Workflow pratique en 3 etapes (p.42, Fig 5.6)

1. **Locate nodes** - host discovery (ping sweep, ARP, nmap -sn) pour avoir la liste des hotes vivants.
2. **Service/OS discovery** - sur chaque hote vivant, enumerer ports ouverts + versions + OS (nmap -sV -O, banner grabbing).
3. **Test known vulnerabilities** - comparer chaque service/version identifie contre une base CVE (nmap --script vuln, Nessus/OpenVAS, ou recherche manuelle exploit-db/NVD).

C'est l'ordre a respecter avant de lancer un scanner lourd: ne pas scanner en vuln direct sans avoir d'abord confirme host/port/version, sinon le bruit (faux positifs) explose.

## Active vs passive scanning (p.31)

- **Active**: on envoie des requetes/probes crafted directement au target (bruyant, detectable, mais precis).
- **Passive**: on infere OS/services/version en observant le trafic normal (TCP handshake, timing) sans toucher la cible - utile si furtivite exigee ou IDS/WAF agressif en face.

## Credentialed vs non-credentialed (p.37)

Un scan authentifie (credentials valides fournies au scanner) voit beaucoup plus (configs internes, patchs manquants reels) qu'un scan externe non-authentifie. En engagement CTF/pentest, si on obtient des creds meme low-priv, relancer le scan vuln en mode "credentialed" donne un delta d'info important (ne pas se contenter du scan externe initial).

## Checklist de scan externe (p.34, piege a eviter: oublier une etape = angle mort)

Ordre recommande pour un scan externe (perimetre internet-facing):
1. Regles firewall/routeur externes
2. Devices externes mappes (quels IP/hosts exposes)
3. Ports ouverts + services associes
4. Niveau de patch des devices externes
5. IDS/firewall/WAF en place
6. Info DNS zones (zone transfer, sous-domaines)
7. Apps web (e-commerce, panier) specifiquement

## Checklist de scan interne (p.35)

Ports/services internes -> configs routeur/firewall -> vulns OS/serveur internes -> recherche de trojans deja presents -> niveau de patch interne -> malware/spyware existant -> securite physique -> acces admin distant -> partages fichiers (NFS/SMB/CIFS, souvent mal durcis) -> AV en place.
Point utile en CTF interne/AD: toujours checker les partages SMB/NFS en premier reflex, c'est souvent la porte d'entree la plus rapide.

## Scoring et bases de reference

- **CVSS** (p.28-29): vecteur type `CVSS:3.1/AV:L/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:H` -> score numerique 0-10. Lire le vecteur donne direct la voie d'exploitation (AV:N=reseau, AC:L=facile, PR:N=pas d'auth requise) - un bon triage rapide avant de choisir sa cible dans une liste de CVE.
- **CVE / NVD**: identifiant unique par vuln, cross-reference obligatoire pour confirmer qu'une version de service a un exploit publie.
- Sources vuln research a connaitre: exploit-db.com, packetstormsecurity.com, NVD, MSRC (bulletins Microsoft) (p.29-30).

## Outils et usage concret

- **Nessus / OpenVAS / Qualys / Nexpose / GFI LanGuard**: scanners automatises generalistes (host+network). Nessus Essentials = version gratuite limitee, bon reflexe pour un premier scan large.
- **Nikto**: scanner web GPL, tests de config serveur web (p.2723-2769). Usage typique: `nikto -h <target>`.
- **Skipfish**: crawler+scanner web actif, commande concrete retrouvee dans le module (p.71, Fig 5.29):
  ```
  skipfish -o /tmp/skipfish_output http://testphp.vulnweb.com && firefox /tmp/skipfish_output/index.html
  ```
  `-o <dir>` = dossier de sortie, puis ouverture directe de `index.html` pour lire le rapport. Target de demo utilise dans le cours: `testphp.vulnweb.com` (site de test public, reflexe a connaitre pour s'entrainer).
- **Database scanning**: cibler specifiquement MySQL/MSSQL/Oracle/PostgreSQL pour mauvaise config/injection (p.36) - penser a tester une couche DB a part si l'app en expose une derriere le web.

## Approches d'assessment (p.40) - choix de strategie

- **Tree-based**: un scanner different par type de machine (Windows/DB/web vs Linux) - demande une intelligence de depart (cartographie prealable).
- **Inference-based**: construit d'abord un inventaire des protocoles/ports/services presents sur la machine, puis ne lance QUE les tests pertinents pour ces services detectes. Plus efficace et moins bruyant - c'est le modele que suivent nmap --script vuln et les scanners modernes (ne pas tester un service qui n'existe pas sur la cible).

## Pieges / limites a garder en tete (p.32-33)

- Les scanners ne detectent pas les 0-day (base sur signatures connues uniquement).
- Faux positifs/negatifs frequents -> toujours valider manuellement une vuln critique avant de batir l'exploit dessus (ne jamais faire confiance a 100% a un rapport Nessus/OpenVAS brut).
- Un scan authentifie "domain admin" donne des resultats tres differents d'un scan non-authentifie -> toujours noter le contexte d'execution du scan avant de comparer deux rapports.
- Scanners classiques ne couvrent pas le social engineering ni les tests live applicatifs complexes (logique metier) -> completer par du manuel.

## Lecture de rapport de vuln assessment (p.72-77)

Elements a chercher en priorite dans un rapport fourni (ex: rapport Nessus exporte en CTF/audit):
- Nom + CVE ID + score CVSS de chaque finding
- Severite (Critical/High/Medium/Low) -> trier par la pour prioriser l'exploitation
- Description + impact + PoC fourni (souvent directement exploitable tel quel)
- Services vulnerables par host avec port exact -> cibler directement avec l'exploit correspondant plutot que de re-scanner.

## Resume one-liner

Toujours: locate -> enumerate services/version -> cross-ref CVE/CVSS -> scanner cible (inference-based) -> valider manuellement avant d'exploiter. Nikto/Skipfish pour le web, Nessus/OpenVAS pour le generaliste, et ne jamais sauter l'etape manuelle de validation.
