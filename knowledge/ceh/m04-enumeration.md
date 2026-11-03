# CEH M04 - Enumeration (synthese offensive) - COMPLET

Source: `CEHv13 - Module 04 - Enumeration hide01.ir.pdf` (120 pages, OCR integral).
Format: techniques offensives concretes (payloads, commandes, outils, ordre de sonde, pieges).
Theorie d'examen/reformulations pedagogiques EC-Council ignorees sauf quand utile a la comprehension
d'une commande. Watermark OCR "hide01.ir" et artefacts de capture d'ecran ignores.

## Definition et portee (p.5)

Enumeration = creer des connexions actives avec la cible + requetes directes pour extraire: ressources
reseau, partages, tables de routage, parametres audit/service, infos SNMP/FQDN, noms de machine,
users/groupes, applications/banners. Fonctionne typiquement en intranet (contrairement au scan
externe pur).

Piege a noter: un partage IPC$ (Windows) trouve lors de l'enum peut etre sonde davantage via
brute-force des credentials admin pour recuperer le listing complet du filesystem partage - ne pas
s'arreter a la simple detection du partage.

## Techniques generiques d'extraction (p.6-7)

- **Usernames via email**: format `username@domainname` - toute adresse mail collectee = username
  candidat direct.
- **Default passwords**: toujours checker les creds par defaut constructeur avant tout brute-force.
- **Brute-force Active Directory via "logon hours"**: si la feature "logon hours" est active sur
  l'AD, les tentatives d'authentification renvoient des messages d'erreur differents selon que le
  username existe ou non -> permet l'enumeration de usernames valides avant un brute-force de mots
  de passe cible.
- **DNS Zone Transfer**: si le DNS server est mal configure et autorise le transfert de zone, il
  livre TOUT en clair (hosts, sous-zones, IPs). Outils: `nslookup`, `dig`. Reflexe systematique a
  tester en premier sur tout domaine cible (AXFR).
- **SNMP community strings**: souvent devinables en lecture (public) ou ecriture -> extraction de
  usernames et de toute la topologie reseau via la MIB tree.

## Table des ports a enumerer (p.7-9) - reference rapide

| Port | Protocole | Interet offensif |
|---|---|---|
| TCP/UDP 53 | DNS | Zone transfer (AXFR) si mal configure; UDP par defaut, bascule TCP si reponse tronquee (>512 octets) |
| TCP/UDP 135 | MSRPC Endpoint Mapper | Messages malformes -> DoS possible; sert a localiser les autres services RPC |
| UDP 137 | NetBIOS Name Service (NBNS/WINS) | Cible privilegiee en premier pour l'attaquant (resolution noms<->IP) |
| TCP 139 | NetBIOS Session (SMB over NetBIOS) | Null session + partages fichiers - port a restreindre en priorite cote defense |
| TCP/UDP 445 | SMB direct over TCP | Remplace 139 sur OS recents, meme classe de risque (partages, null session) |
| UDP 161/162 | SNMP (agent/trap) | 161 = requetes vers l'agent, 162 = notifications/traps vers le manager |
| TCP/UDP 389 | LDAP | Annuaire AD - cible de choix pour enum users/groupes |
| TCP 2049 | NFS | Si mal configure: controle du systeme distant, privesc, depot de backdoor |
| TCP 25 | SMTP | Commandes utiles: `HELO`, `MAIL FROM:`, `RCPT TO:`, `VRFY <string>`, `EXPN <string>` -> VRFY/EXPN servent a l'enumeration d'adresses/utilisateurs valides si le serveur ne les desactive pas |
| UDP 500 | ISAKMP/IKE (IPsec) | Negociation SA/VPN |
| TCP 22 | SSH/SFTP | Brute-force creds SSH; SFTP enum via meme port (users, perms fichiers, config serveur) |
| TCP/UDP 111 | RPC portmapper | Localise endpoints RPC/NFS; souvent filtre mais scanner wide-range si suspecte |
| UDP 2000/2001/5060/5061 | SIP (VoIP) | Enumeration gateways/PBX/user-agents |

Point tactique SMTP: toujours tester `VRFY` et `EXPN` en premier sur un service SMTP expose - c'est
la methode d'enumeration d'utilisateurs la plus rapide si le serveur ne les a pas desactivees
(config par defaut sur de vieux serveurs).

## NetBIOS enumeration (p.12-24)

NetBIOS est a tester en premier reflex sur une cible Windows: il expose beaucoup (liste machines du
domaine, partages, policies/passwords) et tourne par defaut meme non utilise. Ports: UDP 137 (name
service), UDP 138 (datagram), TCP 139 (session). Un port 139 ouvert = check immediat des partages
accessibles. Note: Microsoft ne supporte pas la resolution de noms NetBIOS en IPv6.

### Table des codes NetBIOS (p.13, a memoriser)

| Nom | Code | Info obtenue |
|---|---|---|
| `<hostname>` | `<00> UNIQUE` | Hostname |
| `<domain>` | `<00> GROUP` | Nom de domaine |
| `<hostname>` | `<03> UNIQUE` | Messenger service (machine) |
| `<username>` | `<03> UNIQUE` | Messenger service (user loggue) |
| `<hostname>` | `<20> UNIQUE` | Server service actif |
| `<domain>` | `<1D> GROUP` | Master browser du subnet |
| `<domain>` | `<1B> GROUP` | PDC du domaine (domain master browser) |
| `<domain>` | `<1E> GROUP` | Elections browser service |

### Commandes

```
nbtstat -a <IP distante>        # table de noms NetBIOS complete de la machine distante
nbtstat -A <IP distante>        # idem mais par adresse IP explicite
nbtstat -c                      # cache local des noms NetBIOS deja resolus
nbtstat -r                      # compte des noms resolus par broadcast/WINS
nbtstat -R                      # purge le cache + recharge les entrees #PRE du fichier Lmhosts
nbtstat -S                      # sessions NetBIOS actives avec IP

nmap -sV -v --script nbstat.nse <target IP>     # NSE - augmenter verbosite pour tous les noms, pas juste l'user courant
nbtscan <target IP>                              # alternative rapide, un seul host ou range
nmblookup -A <target IP>                         # equivalent Samba/Linux, affiche les noms associes

net view \\<computername>              # liste les partages d'un host distant
net view \\<computername> /ALL        # inclut les partages caches
net view /domain                       # liste tous les partages du domaine
net view /domain:<domain name>         # liste les partages d'un domaine specifique
```
Outils GUI cites: NetBIOS Enumerator (scan range IP -> noms/usernames/domaine/MAC), Global Network
Inventory, Advanced IP Scanner, Hyena, Nsauditor.

### Enumeration d'utilisateurs via PsTools suite (p.17-19)
Suite Sysinternals pour controle/enum a distance sans installer de client sur la cible:
- `PsExec` - execution de process distant (quasi-remplacement Telnet), lance des shells interactifs.
- `PsFile` - liste/ferme les fichiers ouverts a distance sur un systeme.
- `PsGetSid` - traduit SID <-> nom de compte, fonctionne a distance.
- `PsKill` - termine un process local ou distant par PID ou nom.
- `PsInfo` - info systeme distante (build OS, RAM, date d'install, etc.).
- `PsLoggedOn` - liste les users loggues localement + via resources partagees (scan HKEY_USERS +
  NetSessionEnum API).
- `PsLogList` - dump a distance de l'Event Log (contourne les restrictions de credentials locales).
- `PsPasswd` - change un mot de passe de compte local/distant sans transmettre en clair (API Windows
  dediee).
- `PsShutdown` - shutdown/reboot distant sans client installe.

## SNMP Enumeration (p.25-36)

SNMP = protocole UDP (port 161 agent, 162 traps) gere par community strings: **read** (publique,
souvent devinable "public") et **read/write** (privee, souvent "private"). Toute community string
laissee par defaut = acces en lecture/ecriture a la MIB complete (hosts, routeurs, ARP tables,
routing tables, traffic stats).

```
snmpwalk -v1 -c public <Target IP>                              # dump complet via MIB tree, v1
snmpwalk -v2c -c public <Target IP>                              # idem SNMPv2c
snmpwalk -v2c -c public <Target IP> hrSWInstalledName            # liste logiciels installes
snmpwalk -v2c -c public <Target IP> hrMemorySize                 # quantite de RAM
snmpwalk -v2c -c public <Target IP> sysContact <New Value>       # ECRITURE si community write dispo - modifie l'OID sysContact

nmap -sU -p 161 --script=snmp-processes <Target IP>              # liste processus + ports via NSE
nmap -sU -p 161 --script=snmp-sysdescr <Target IP>               # type serveur SNMP + OS
nmap -sU -p 161 --script=snmp-win32-software <Target IP>         # liste applis installees (cibles Windows)

snmp-check <Target IP>                                            # tool dedie, sortie lisible: contact, hardware,
                                                                    # interfaces reseau, routing, TCP connections,
                                                                    # user accounts, uptime, etc.
```
Outils GUI: SoftPerfect Network Scanner (ping/port/shares/WMI/SNMP/HTTP/SSH/PowerShell combine).
Autres: Network Performance Monitor, OpUtils, PRTG Network Monitor, Engineer's Toolset.

MIB utiles: DHCP.MIB (trafic DHCP), HOSTMIB.MIB (ressources host), LNMIB2.MIB (workstation/server
services), MIB_II.MIB (TCP/IP), WINS.MIB. Acces via navigateur: `http://IP/Lseries.mib`.

## LDAP Enumeration (p.37-44)

Port 389 (LDAP) / 636 (LDAPS). Client se connecte au DSA et envoie une requete (format BER/RFC 4515).
Une requete anonyme peut deja fournir usernames/adresses/departements/noms de serveurs.

### Enumeration manuelle via Python (p.38-40)
```python
pip3 install ldap3
import ldap3
server = ldap3.Server('Target IP', get_info=ldap3.ALL, port=389)
connection = ldap3.Connection(server)
connection.bind()                      # True si succes (bind anonyme)
server.info                            # recupere domain name / naming context (ex: DC=CEH,DC=com)
connection.search(search_base='DC=DOMAIN,DC=DOMAIN',
                   search_filter='(&(objectClass=*))', search_scope='SUBTREE', attributes='*')
connection.entries                     # dump tous les objets de l'annuaire
# variante cible mot de passe (si attribut lisible / mal protege):
connection.search(search_base='DC=DOMAIN,DC=DOMAIN',
                   search_filter='(&(objectClass=person))', search_scope='SUBTREE',
                   attributes='userPassword')
```

### ldapsearch (p.42-43)
```
ldapsearch -h <Target IP> -x                                         # bind simple, verifie la connexion
ldapsearch -h <Target IP> -x -s base namingcontexts                   # recupere le naming context (ex: DC=htb,DC=local)
ldapsearch -h <Target IP> -x -b "DC=htb,DC=local" "(objectClass=Employee)"   # objets d'une classe precise
ldapsearch -x -h <Target IP> -b "DC=htb,DC=local" "objectclass=*"      # dump complet de l'arbre
ldapsearch -h <Target IP> -x -b "DC=htb,DC=local" \
  '(objectClass=Employee)' sAMAccountName sAMAccountType              # liste cible d'attributs (users)
```

### Automatise / NSE
```
nmap -p 389 --script ldap-brute --script-args ldap.base='"cn=users,dc=CEH,dc=com"' <Target IP>
```
Outils GUI: Softerra LDAP Administrator (browse/enum username+email+departement), AD Explorer,
LDAP Admin Tool, LDAP Account Manager, LDAP Search.

## NTP Enumeration (p.45-51)

Port UDP 123. Permet d'obtenir: liste de hosts connectes au serveur NTP, IP clients + OS, et IP
internes si le serveur NTP est en DMZ (fuite de topologie interne).

```
ntpdate -d <Target IP>                       # mode debug, affiche precision/delay/offset et confirme le serveur NTP
ntptrace [-n] [-m maxhosts] <server/IP>      # remonte la chaine de serveurs NTP jusqu'a la source primaire (stratum)
ntpdc -c listpeers <host/IP>                 # liste des peers connus (equivalent -l)
ntpdc -c peers <host/IP>                     # peers + resume d'etat (equivalent -p)
ntpq -c peers <host/IP>                      # monitore ntpd, liste des peers avec etat
ntpq> version / host / ?                     # commandes interactives utiles pour reconnaissance
```
Note: beaucoup de distributions Linux recentes remplacent `ntpd` par `chronyd` - verifier la presence
de l'un ou l'autre avant de conclure a une absence de service NTP.
Outils: PRTG Network Monitor, Nmap, Wireshark, udp-proto-scanner, NTP Server Scanner.

## NFS Enumeration (p.52-55)

NFS utilise RPC pour router les requetes clients/serveur. `/etc/exports` cote serveur liste les
clients autorises (authentification = IP du client uniquement sur NFS <v4 -> IP spoofing possible
pour contourner).

```
rpcinfo -p <Target IP>                     # scanne portmapper (111), revele le port NFS reel (souvent 2049) + services RPC actifs
showmount -e <Target IP>                   # liste les repertoires exportes/partages
python3 rpc-scan.py <Target IP> --rpc      # RPCScan - enumere services RPC actifs + misconfigs NFS
./superenum                                 # SuperEnum - script qui prend un fichier Target.txt et enum tous ports ouverts (dont 2049/NFS)
```
Apres identification d'un share mal configure: spoofer l'IP d'un client autorise pour obtenir un
acces complet (lecture/ecriture selon permissions) au systeme de fichiers partage.

## SMTP Enumeration (p.56-67)

Port 25 (ou 2525/587). Trois commandes integrees exploitables pour enum users:

```
telnet <Target IP> 25
HELO x
VRFY <username>        # 250 = user existe / 550 = user inconnu
EXPN <username>        # 250 = affiche l'adresse de livraison reelle (alias/listes) / 550 = inconnu
MAIL FROM: <addr>
RCPT TO: <username>    # 250 Recipient ok = user existe / 550 = inconnu
```

### Automatisation
```
nmap -p 25,465,587 --script=smtp-commands <Target IP>          # liste les commandes SMTP disponibles
nmap -p 25 --script=smtp-open-relay <Target IP>                 # detecte un relai ouvert (spam/spoofing possible)
nmap -p 25 --script=smtp-enum-users <Target IP>                 # enum tous les users mail via VRFY/EXPN/RCPT
```

### Metasploit (module dedie, workflow complet p.60-62)
```
msf > use auxiliary/scanner/smtp/smtp_enum
msf auxiliary(smtp_enum) > set RHOSTS <Target IP>
msf auxiliary(smtp_enum) > set USER_FILE <wordlist perso>   # defaut: /usr/share/metasploit-framework/data/wordlists/unix_users.txt
msf auxiliary(smtp_enum) > run                               # valide chaque user via VRFY et liste les matches
```

### smtp-user-enum (pentestmonkey, p.63-64)
```
smtp-user-enum.pl -M VRFY -U users.txt -t <Target IP>      # mode VRFY par defaut (-M EXPN|RCPT disponibles)
smtp-user-enum.pl -M RCPT -u <user> -t <Target IP> -f attacker@example.com
```
Autres outils: NetScanTools Pro (SMTP Email Generator + log complet des headers), Nmap, Metasploit.

## DNS Enumeration (p.68-86)

### Zone Transfer (AXFR) - toujours tester en premier
```
dig ns <target domain>                                    # liste les name servers du domaine
dig @<nameserver> <target domain> axfr                     # tente le transfert de zone complet

nslookup
> set querytype=soa
> <target domain>                                           # recupere infos SOA admin
> server <domain nameserver>
> ls -d <target domain>                                      # tente transfert de zone (Windows nslookup)

dnsrecon -t axfr -d <target domain>                          # AXFR automatise, teste tous les NS
```

### DNS Cache Snooping (p.72-74) - reveler les sites visites recemment via le cache DNS
```
dig @<DNS server IP> <target domain> A +norecurse    # non-recursif: NOERROR sans reponse = site NON visite/cache
dig @<DNS server IP> <target domain> A +recurse       # recursif: comparer le TTL retourne au TTL initial
                                                        # TTL faible (deja decremente) = site EN cache = visite recemment
                                                        # TTL eleve (= valeur initiale) = pas en cache
```

### DNSSEC Zone Walking (p.75-77) - contourne un DNS mal configure meme avec DNSSEC
```
ldns-walk @<IP DNS server> <target domain>        # enumere tous les records via NSEC chaining
dnsrecon -d <target domain> -z                      # zone enumeration incluant NSEC
```
Contre-mesure a connaitre (donc limite attendue): NSEC3 hash les noms de record pour empecher ce
zone-walking - si NSEC3 est en place, l'enumeration via marche de zone echoue.

### OWASP Amass
```
amass enum -d <Target Domain>                                        # subdomains, IP, SSL/TLS, HTTP, APIs, certs
amass enum -passive -d <Target Domain> -src                           # passif uniquement (pas de requetes directes a la cible)
amass enum -active -d <Target Domain> -brute -w /usr/share/wordlists/amass/all.txt   # brute-force actif
amass track -config /root/amass/config.ini -dir amass4owasp -d <Target Domain> -last 2  # compare 2 derniers scans
amass viz -d3 -dir amass4owasp                                        # graphe HTML D3 des resultats
```

### Nmap DNS/DNSSEC NSE
```
nmap --script=broadcast-dns-service-discovery <Target Domain>        # services annonces sur le domaine
nmap -T4 -p 53 --script dns-brute <Target Domain>                     # brute-force de sous-domaines (output inclut wildcard A/AAAA)
nmap -Pn -sU -p 53 --script=dns-recursion <Target IP>                 # check si la recursion DNS est activee (amplification DoS potentiel)
nmap -sU -p 53 --script dns-nsec-enum --script-args dns-nsec-enum.domains=<domain> <target>  # enum DNSSEC NSEC
```
Autres outils de sous-domaines: Knock, Raccoon, Subfinder, Turbolist3r.

## IPsec Enumeration (p.89-94)

La plupart des VPN IPsec utilisent ISAKMP (port UDP 500, partie d'IKE) pour negocier les SA et cles.

```
nmap -sU -p 500 <Target IP>                           # detection presence gateway VPN (ISAKMP)
nmap -sU -p 500 --script=ike-version <Target IP>       # version IKE via NSE
ike-scan -M <target gateway IP>                         # fingerprint avance: discovery + UDP backoff + Vendor ID fingerprinting
```
Capacites avancees de `ike-scan`: enumeration des transform attributes (algo chiffrement/hash phase
1), enumeration d'usernames VPN valides sur certains systemes, et cracking offline de pre-shared key
en mode Aggressive via `psk-crack` (fourni avec le package ike-scan).

## VoIP Enumeration (p.94-96)

SIP (Session Initiation Protocol) sur UDP/TCP 2000, 2001, 5060, 5061.

```
svmap <target network range/IP>          # identifie devices SIP/PBX (ports par defaut et non-standard), peut "ring" tous les telephones via INVITE
```
Metasploit: module SIP Username Enumerator pour scanner les extensions/usernames numeriques des
telephones VoIP. Information extraite utile pour DoS, session hijacking, caller ID spoofing,
eavesdropping, SPIT (spam over Internet Telephony), vishing.

## RPC Enumeration (p.96-98)

Portmapper ecoute TCP/UDP 111, mappe les endpoints RPC. Souvent filtre par les firewalls -> scanner
une plage de ports large pour trouver les services RPC exposes directement.

```
nmap -sR <target IP/network>              # scan RPC dedie
nmap -T4 -A <target IP/network>            # scan combine qui remonte aussi les infos RPC/LDAP/SMB
```
Outil GUI: NetScanTools Pro RPC Info (detecte le portmapper daemon sur *nix, port 111).

## Unix/Linux User Enumeration (p.99-101)

```
/usr/bin/rusers [-a] [-l] [-u] [-h] [-i] [Host ...]     # users loggues sur le LAN; -a=meme sans users, -h/-u/-i=tri
rwho [-a]                                                 # users loggues sur hosts locaux (daemon rwho requis); -a inclut sessions idle
finger [-l] [-m] [-p] [-s] [user ...] [user@host ...]    # infos user: login, nom reel, tty, idle, login time, phone
                                                           # -l affiche aussi home dir/.plan/.project/.pgpkey/.forward
finger                                                     # sans argument: liste tous les users loggues localement
finger <user>                                              # details complets sur un user precis
```

## SMB Enumeration (p.101-104)

Port 445 (direct TCP) ou via NetBIOS (137/138/139). Permet banner grabbing (OS + version services) ->
base pour SMB relay attacks et brute-force.

```
nmap -p 445 -A <target IP>                                  # OS detection + version + scripts + traceroute via SMB
nmap -p 445 --script smb-protocols <Target IP>               # protocoles/versions SMB supportes
nmap -p 139 --script smb-protocols <Target IP>                # idem via NetBIOS
nmap -p 445 --script smb-enum-shares <Target IP>              # liste les shares SMB exposes
```
Outils complementaires (cites mais non detailles dans l'OCR): SMBMap, enum4linux, nullinux,
SMBeagle, NetScanTools Pro.

## IPsec/VoIP/RPC/Unix/SMB - script d'automatisation enumeration complete (p.106-110, pour reference)

```bash
#!/bin/bash
target_range="10.10.1.0/24"
nmap -sn $target_range -oN ~/enumeration_results/ping_sweep.txt
nmap -T4 -F $target_range -oN ~/enumeration_results/quick_scan.txt
nmap -T4 -A $target_range -oN ~/enumeration_results/detailed_scan.txt
nmap -sV $target_range -oN ~/enumeration_results/version_detection.txt
```
Enchainement logique reutilisable: ping sweep -> quick scan (top ports) -> scan detaille (-A) ->
version detection (-sV), chaque etape loggee dans un fichier separe pour analyse differee.

## Enumeration Countermeasures (connaissance defensive utile pour anticiper le blocage et confirmer un vecteur) (p.111-120)

- **SNMP**: desactiver le service si possible; sinon changer les community strings par defaut,
  upgrader en SNMPv3 (chiffrement), restreindre via ACL, bloquer port 161 si inutilise, segmenter
  sur VLAN dedie. -> Si SNMPv1/v2c "public" fonctionne encore, c'est un signe fort de mauvaise
  hygiene globale sur la cible (chercher d'autres defauts similaires).
- **LDAP**: trafic non chiffre par defaut -> SSL/STARTTLS attendu en environnement durci; bind
  anonyme souvent desactive -> tester le bind anonyme en premier reste gratuit et rapide.
- **NFS**: `root_squash` cense etre actif (empeche un client root d'avoir les droits root sur le
  serveur) - verifier explicitement si ce n'est pas le cas (`no_root_squash` = vecteur de privesc
  direct).
- **SMTP**: VRFY/EXPN/RCPT TO souvent desactives sur serveurs modernes -> si actifs, cible
  probablement mal maintenue ou legacy.
- **SMB**: SMBv1 cense etre deprecie (vulnerable, ex. EternalBlue) -> verifier activement la version
  SMB supportee via `smb-protocols`, c'est un signal tres fort si SMBv1 repond encore.
- **DNS**: zone transfer cense etre restreint aux secondaires connus -> tester systematiquement car
  tres souvent encore ouvert sur domaines mal geres; DNSSEC avec NSEC (pas NSEC3) reste zone-walkable.
