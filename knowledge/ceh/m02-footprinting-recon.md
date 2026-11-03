# CEH M02 - Footprinting and Reconnaissance (synthese offensive)

Source: `CEHv13 - Module 02 - Footprinting and Reconnaissance hide01.ir.pdf` (158 pages), OCR
complet 158/158. Page = pagination du module ("Module 02 Page NNN", commence a 121). Theorie
d'examen/countermeasures omise sauf reutilisable offensivement. Beaucoup de pages sont des
captures d'ecran d'outils web (Shodan/Censys/Netcraft) sans commande CLI - resume a l'usage
plutot que transcrit.

Structure: Footprinting concepts -> Search engines/Google dorks -> Website/Email footprinting
-> Whois -> DNS footprinting -> Network footprinting -> Social engineering/social media OSINT
-> outils automatises (Recon-ng, OSINT Framework, Maltego, SpiderFoot, Recon-Dog, BillCipher).

## 1. Google Hacking / dorks

Operateurs cles: `site:`, `intitle:`, `intext:`, `inurl:`, `filetype:`.
```
site:vpn.*.*/ intitle:"login"                     # pages de login VPN exposees
site:sftp.*.*/ intext:"login" intitle:"server"    # portails SFTP exposes
site:microsoft.com -inurl:www                      # enumere les sous-domaines hors www
"John Doe" site:facebook.com OR site:linkedin.com  # OSINT personne cible
filetype:pdf site:onion                            # recherche de documents sur le dark web (via proxy)
inurl:config filetype:txt                          # fichiers de config exposes
filetype:sql site:onion dump                        # dumps de bases de donnees
filetype:xml inurl:config server                    # fichiers config serveur exposes
filetype:key site:onion private                      # cles privees exposees
filetype:txt inurl:exploit                           # PoC/exploits indexes
```
Piege/usage: combiner `-inurl:www` pour forcer Google a lister les sous-domaines plutot que la
page principale; combiner `filetype:` + `site:onion` necessite un proxy Tor pour suivre le lien.

## 2. Whois

- Interroge le Whois database du registrar pour obtenir: coordonnees admin/technique,
  serveurs de noms, dates de creation/expiration, infos reseau (netblocks).
- Reflexe CLI: `whois <domaine>` (non explicitement montre en CLI dans le module, qui pousse
  vers des services web type whois.domaintools.com) - a utiliser en premier, zero bruit genere
  sur la cible.

## 3. DNS footprinting / enumeration

```
# Enumerer toutes les IP associees aux NS d'un domaine (sub-domain/A-record sweep)
dig +short google.com NS | xargs -I{} dig +nocmd +noall +answer @{} google.com A +noall +answer

# Enumeration de sous-domaines automatisee
sublist3r -d eccouncil.org -o eccouncil_subdomains.txt

# DNS enum complet (SOA/NS/MX/TXT/AAAA...) via dnsrecon
sudo apt-get install -y dnsrecon && dnsrecon -d certifiedhacker.com -t std

# Reverse DNS lookup par brute-force sur une plage IP (PTR records)
dnsrecon -r 162.241.216.0-162.241.216.255
```
- Autres outils DNS cites (web/GUI): **SecurityTrails** (DNS mapping historique), **Fierce**,
  **DNSChecker**, **zdns**, **puredns**, **Reverse IP Domain Check**.
- Piege defense a connaitre offensivement: si le **zone transfer (AXFR)** n'est pas restreint
  sur le DNS cible, il dump l'intégralite de la zone en une requete - toujours tenter avant
  l'enumeration brute-force (plus bruyant).

## 4. Moteurs de recherche IoT/infra (Shodan, Censys, Netcraft, ZoomEye)

```
# Exemples de requetes Shodan (web UI, pas de CLI native montree)
shodan.io/search?query=SCADA
shodan.io/search/facet?query=google.com&facet=os
shodan.io/host/<IP>                                  # fiche detaillee d'un host (ports, OS, certif TLS)
```
- Shodan/Censys/ZoomEye renvoient: fabricant, localisation geo, IP, hostname, ports ouverts,
  banners de service, OS fingerprint, certificats TLS, meme sur des devices **SCADA/ICS/OT**
  (pertinent pour pivoter vers M18) - beaucoup de ces devices sont sans authentification ou en
  creds par defaut.
- **Netcraft** (web): `sitereport.netcraft.com/?url=<domaine>` pour OS fingerprint + liste de
  sous-domaines; `searchdns.netcraft.com/?host=*.<domaine>` pour lister tous les hosts connus
  d'un domaine.
- **Censys** (censys.io): recherche d'infra par certificat TLS, port, service; fiche host avec
  historique Whois integre.
- **Wappalyzer**: detection de 1000+ technologies front/back (stack fingerprint rapide avant de
  choisir l'angle d'attaque).

## 5. Email footprinting

```
# theHarvester: recolte emails/employes via moteur de recherche/LinkedIn
theHarvester -d microsoft -l 200 -b linkedin                       # enumere les employes LinkedIn
theharvester -d microsoft.com -l 200 -b baidu                       # emails via moteur Baidu
theHarvester -d microsoft.com -l 200 -b baidu -f Microsoft_emails.xml   # export XML
```
- `-d` domaine cible, `-l` limite de resultats, `-b` moteur/source (google, bing, linkedin,
  baidu, etc.), `-f` fichier de sortie.
- **Email header analysis**: remonter le header complet d'un mail recu donne la route des
  serveurs relais + IP source -> geolocalisable.
- **Email tracking tools**: eMailTrackerPro, MxToolbox, IP2LOCATION Email Header Tracer,
  Holehe (verification d'email sur de multiples services), DNS Checker Email Header Analyzer,
  Social Catfish. Usage: extraire IP/geoloc de l'expediteur, identite, serveur mail.

## 6. Website footprinting (metadonnees, archives, extraction)

- **Metadonnees de documents publics**: FOCA, Metagoofil, ExifTool - extraient auteur,
  logiciel, chemins internes, emails, versions depuis les PDF/DOCX/XLSX publics du site cible
  (tres rentable en reconnaissance, zero interaction directe avec l'infra).
- **Archives historiques** (versions passees d'un site, souvent avec infos retirees depuis):
  `archive.org` (Wayback Machine), Common Crawl, WebCite, Wayback Machine Chrome Extension,
  Waybackpack (CLI pour scripter l'extraction d'URLs archivees).
  ```
  # Recuperer les URLs archivees d'un site cible via archive.org
  # (commande exacte dependante de l'outil - waybackpack <domaine> en pratique)
  ```
- **Mirroring local** pour analyse offline/diffing: pas de commande explicite dans ce module,
  mais reflexe standard = `wget -m -k <url>` ou HTTrack.

## 7. Social engineering / OSINT social media

- Recherche ciblee par dork: `"Prenom Nom" site:facebook.com`, `site:scholar.google.com`,
  `site:example.com "employee directory"` -> identifie des employes, leurs roles, relations.
- Objectif offensif: construire une liste de cibles de phishing/vishing qualifiee (nom, role,
  reseau social, habitudes) avant la phase social engineering (cf M09 dans l'autre groupe).

## 8. Frameworks d'automatisation (reflexe "pas le temps de tout faire a la main")

- **Recon-ng**: framework modulaire (workspace + modules marketplace) - decouverte de repos de
  code source publics, enumeration de sous-domaines, etc. en une session scriptable.
- **Maltego**: cartographie de relations OSINT (domaines <-> IP <-> personnes <-> organisations)
  en graphe visuel - utile pour la synthese finale d'une recon large.
- **OSINT Framework** (site web, arbre de liens par categorie: domaines, personnes, images,
  dark web...) - bon point d'entree quand on ne sait pas par ou commencer.
- **Recon-Dog**: tout-en-un base sur API (Censys lookup, NS lookup, port scan commun, detect
  CMS, Whois, detect honeypot via shodan.io, find subdomains via findsubdomains.com, reverse IP
  lookup, detect technologies via wappalyzer.com) - bonne option "un seul outil, plusieurs
  fonctions" en CTF.
- **BillCipher**: DNS lookup + Whois + port scan + zone transfer + host finder + reverse IP en
  un seul tool Python/Ruby.
- **SpiderFoot**: automatisation OSINT large spectre (non detaille avec commandes dans l'OCR
  recupere, mais cite comme reference standard).

## Ordre de sonde recommande (non-intrusif -> de plus en plus actif)

1. Whois + DNS passif (dig/dnsrecon en lecture, pas de zone transfer encore) - zero trace cote
   cible.
2. Moteurs OSINT (Shodan/Censys/Netcraft/Google dorks) - toujours passif, aucune requete
   directe vers l'IP cible si elle n'est pas deja indexee.
3. Website/email footprinting (metadonnees documents, archive.org, theHarvester) - toujours
   passif.
4. DNS actif (sublist3r, tentative de zone transfer AXFR, reverse DNS sweep) - premiere
   interaction directe, encore discrete.
5. Social engineering recon (profils sociaux, org chart) - prepare la phase suivante (M09) sans
   toucher l'infra.

Cet ordre maximise l'information avant le premier paquet qui pourrait logguer/alerter la
cible, coherent avec la posture "evidence-first" du profil solveur.
