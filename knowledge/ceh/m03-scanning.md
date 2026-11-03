# CEH M03 - Scanning Networks (synthese offensive) - COMPLET

Source: `CEHv13 - Module 03 - Scanning Networks hide01.ir.pdf` (144 pages, OCR integral).
Format: techniques offensives concretes (payloads, commandes, outils, ordre de sonde, pieges).
Theorie d'examen/reformulations pedagogiques EC-Council ignorees sauf quand utile a la comprehension
d'une commande. Watermark OCR "hide01.ir" et artefacts de capture d'ecran ignores.

## Objectifs du scan reseau (p.5-6)

But: decouvrir hosts vivants + IP + ports ouverts -> OS/architecture (fingerprinting) -> services/versions
ecoutant -> vulnerabilites associees -> topologie reseau. Toujours dans cet ordre, apres la phase de
footprinting.

Types de scan a distinguer: **port scanning** (services par port), **network scanning** (hosts actifs),
**vulnerability scanning** (faiblesses connues).

## TCP flags utiles pour le scan (p.8-11)

- SYN = etablissement connexion (handshake 3-voies: SYN -> SYN/ACK -> ACK).
- RST = reset immediat sur erreur - **exploite par les attaquants pour detecter les ports ouverts**
  (une RST en reponse = port ferme, pas de reponse ou SYN/ACK = port ouvert selon le type de scan).
- ACK scan: utile pour sonder la presence d'un firewall stateless vs stateful (un firewall simple
  laisse passer les paquets ACK, un firewall stateful bloque).
- SYN scanning repose sur SYN/ACK/RST specifiquement.

## Nmap (intro, p.12-14)

Syntaxe de base: `nmap <options> <Target/IP>`
Exemple concret du cours (scan complet Windows cible via Zenmap):
```
nmap -p 1-65535 -T4 -A -v 10.10.1.11
```
`-p 1-65535` = tous les ports, `-T4` = timing agressif, `-A` = detection OS+version+scripts par defaut,
`-v` = verbose. Resultat type observe: FTP 21 (Microsoft ftpd), HTTP 80 (IIS 10.0), RPC 135,
netbios-ssn 139, microsoft-ds 445, RDP 3389 -> fingerprint Windows Server immediat via les banners.

## Hping3 - reference de commandes (p.14-18, complet)

Hping3 sert a sonder un host meme quand il bloque ICMP (via TCP/UDP), tester des regles de firewall,
et faire du scan furtif/manuel.

```
hping3 -1 10.0.0.25                        # ICMP ping scan (echo request/reply, -1 ou --icmp)
hping3 -A 10.0.0.25 -p 80                  # ACK scan port 80 - teste presence/regles firewall:
                                            #   firewall simple = laisse passer -> RST recu
                                            #   firewall stateful = bloque -> pas de reponse
hping3 -2 10.0.0.25 -p 80                  # UDP scan port 80 (-2/--udp): ICMP port-unreachable = ferme, pas de reponse = ouvert/filtre
hping3 192.168.1.103 -Q -p 139             # Collecte des sequence numbers TCP (-Q) du target
hping3 -S 72.14.207.99 -p 80 --tcp-timestamp   # Bypass firewalls qui dropent les paquets sans option TCP timestamp; permet aussi de deviner l'uptime
hping3 -8 50-60 -S 10.0.0.25 -V            # SYN scan sur plage de ports 50-60 (-8/--scan + -S)
hping3 -F -P -U 10.0.0.25 -p 80            # FIN+PUSH+URG scan port 80: pas de reponse = port ouvert, RST = ferme
hping3 -1 10.0.1.x --rand-dest -I eth0     # Ping sweep ICMP sur tout un /24 (destinations aleatoires) via une interface donnee
hping3 -9 HTTP -I eth0                     # Mode listen: intercepte tout trafic contenant la signature HTTP sur l'interface
hping3 -S 192.168.1.1 -a 192.168.1.254 -p 22 --flood   # SYN flood avec IP source spoofee (-a) = DoS
```

Point tactique: l'ACK scan (`-A`) et le FIN/PUSH/URG scan (`-F -P -U`) sont les deux techniques a
tester quand un scan SYN classique est bloque/filtre - elles donnent une info differentielle sur le
type de firewall en face (stateless vs stateful) sans forcement declencher les memes alertes.

## Metasploit (mention, p.18-19)

Signale comme outil de scan de ports/services + exploitation + pivoting + reporting, approche
modulaire exploit/payload.

## Host discovery - techniques de ping scan (p.21-39)

Ordre logique: ARP (sur meme LAN, toujours prioritaire car fiable meme derriere firewall) -> ICMP
(ECHO/Timestamp/AddressMask) -> UDP -> TCP SYN/ACK -> IP Protocol ping.

```
nmap -sn -PR <Target IP>        # ARP ping scan - LAN local, ignore les firewalls (resout via ARP, pas IP)
nmap -sn -PU <Target IP>        # UDP ping scan - port UDP par defaut 40125 (hautement inhabituel)
nmap -sn -PE <Target IP>        # ICMP ECHO ping - ne marche pas sur Windows si ICMP broadcast bloque
nmap -sn -PE <IP Range>         # ICMP ECHO ping SWEEP sur une plage
nmap -sn -PP <Target IP>        # ICMP Timestamp ping - alternative quand ECHO est bloque
nmap -sn -PM <Target IP>        # ICMP Address Mask ping - alternative quand ECHO est bloque
nmap -sn -PS <Target IP>        # TCP SYN ping (port 80 par defaut); plage: -PS22-25,80,113,1050,35000
nmap -sn -PA <Target IP>        # TCP ACK ping (port 80 par defaut) - contourne les firewalls qui bloquent SYN
nmap -sn -PO <Target IP>        # IP Protocol ping - envoie ICMP(1)/IGMP(2)/IP-in-IP(4) par defaut
nmap --disable-arp-ping -sn -PE <Target IP>  # force a desactiver l'ARP ping par defaut de Nmap
```

Pieges/astuces:
- `-sn` = disable port scan (juste host discovery).
- TCP SYN ping: avantage majeur = aucune connexion etablie (scan parallelisable + logs minimaux cote
  cible, trace reduite).
- TCP ACK ping: utile en complement du SYN ping car certains firewalls bloquent le SYN mais laissent
  passer l'ACK (configuration par defaut la plus repandue).
- ICMP ECHO ne marche pas sur Windows (TCP/IP stack ne repond pas aux probes ICMP broadcast) mais
  fonctionne sur UNIX/Linux/BSD.
- IPv6: espace d'adressage trop vaste (2^64 hosts/subnet) pour un ping sweep exhaustif -> harvester
  les adresses IPv6 depuis trafic/logs/entetes email plutot que bruteforcer.

Ping sweep tools cites: Angry IP Scanner (multithreade, un thread par IP, export CSV/TXT/XML),
SolarWinds Engineer's Toolset, NetScanTools Pro, Colasoft Ping Tool, Advanced IP Scanner, OpUtils.

Prompts IA (reference rapide, pour pipeline scripte, p.34-38): un prompt de type "scan X for active
hosts" se traduit typiquement en `nmap -sn 10.10.1.0/24 -oG - | awk '/Up$/{print $2}' > scan1.txt`,
puis un scan de suivi `nmap -T4 -iL scan.txt -oN scan2.txt -v0`, puis `nmap -sn -PE 10.10.1.0/24`.

## Port and service discovery - types de scan par protocole (p.40-68)

Categories: TCP Scanning (open/stealth/third-party-spoofed), UDP Scanning, SCTP Scanning,
SSDP/List Scanning, IPv6 Scanning.

### Table de reference ports/services cles (p.41-43, extrait offensif)

| Port | Service | Note offensive |
|---|---|---|
| 21/tcp | ftp | anonymous login a tester systematiquement |
| 22/tcp | ssh | brute-force creds, version banner |
| 23/tcp | telnet | clair -> interception creds |
| 25/tcp | smtp | VRFY/EXPN/RCPT TO -> enum users |
| 53/tcp,udp | dns | zone transfer AXFR |
| 69/udp | tftp | souvent sans auth |
| 79/tcp | finger | enum users legacy |
| 80/443 | www | fingerprint serveur web |
| 88/tcp,udp | kerberos | AD/domain |
| 111/tcp,udp | sunrpc | portmapper -> enum RPC |
| 135/tcp,udp | msrpc | endpoint mapper RPC |
| 137-139 | netbios | name service/datagram/session |
| 161-162/udp | snmp | community strings par defaut |
| 389/tcp,udp | ldap | enum AD |
| 445/tcp,udp | microsoft-ds | SMB direct, cible n°1 Windows |
| 500/udp | isakmp/ike | VPN IPsec gateway |
| 512-514 | exec/login/shell | r-services BSD (rexec/rlogin/rsh) sans auth forte |
| 1433/tcp,udp | ms-sql-s | SQL Server |
| 2049/tcp,udp | nfs | exported shares |
| 3389 | ms-wbt-server | RDP |
| 5060/udp,tcp | sip | VoIP enumeration |

### Scans TCP ouverts et stealth (p.44-67)

```
nmap -sT -v <Target IP>        # TCP Connect/Full-Open: handshake complet, logge cote cible, pas de privileges requis
nmap -sS -v <Target IP>        # Stealth/Half-Open (SYN scan): envoie SYN seul, RST pour couper avant handshake complet
nmap -sF -v <Target IP>        # FIN scan (inverse flag): pas de reponse=ouvert, RST=ferme; UNIX/BSD only, Windows ignore -> faux "tout ouvert"
nmap -sN -v <Target IP>        # NULL scan: aucun flag; meme limite Windows
nmap -sX -v <Target IP>        # Xmas scan: FIN+URG+PSH; meme limite Windows (toujours "tout ouvert" = signe fiable qu'on scanne du Windows)
nmap -sM -v <Target IP>        # Maimon scan: probe FIN/ACK; BSD-specifique, port ouvert si paquet drop sans reponse
nmap -sA -v <Target IP>        # ACK flag probe scan: analyse TTL/WINDOW du RST pour determiner ouvert/filtre (exploite bug stacks BSD-derivees)
nmap -sI <Zombie> <Target> -Pn -p-  # IDLE/IPID scan: scan 100% blind via un host "zombie" - voir detail ci-dessous
```

Detail **IDLE/IPID scan** (p.56-59) - technique de spoofing complet, tres utile pour rester invisible:
1. Sonder l'IPID courant du zombie en lui envoyant un SYN+ACK inattendu -> il repond RST, on lit l'IPID (ex: 31337).
2. Envoyer un SYN au target en spoofant l'IP source = celle du zombie.
   - Si port ouvert sur target: target envoie SYN+ACK au zombie (qui ne l'attend pas) -> zombie
     repond RST -> IPID du zombie incremente de 1.
   - Si port ferme: target envoie RST direct au zombie, qui ne repond rien -> IPID du zombie inchange.
3. Re-sonder l'IPID du zombie: si delta = +2 depuis l'etape 1 -> port etait ouvert; si delta = +1 ->
   port ferme. Cela permet d'attribuer le scan entierement au zombie dans les logs de la cible.
   Choisir un zombie idle (peu de trafic propre, incrementation IPID globale previsible).

**ACK flag probe scan** - deux sous-variantes utiles quand tous les ports renvoient le meme TTL:
- TTL-based: TTL du RST < 64 -> port ouvert (plusieurs milliers de probes ACK, comparer TTL par port).
- Window-based: Window field du RST != 0 -> port ouvert (`nmap -sW`); utile exactement quand le TTL ne
  discrimine pas.
- Meme technique sert a detecter un firewall stateful: ACK avec sequence number aleatoire -> pas de
  reponse = stateful firewall present; RST recu = pas de firewall.

### UDP / SCTP / SSDP / List / IPv6 scanning (p.60-68)

```
nmap -sU -v <Target IP>         # UDP scan: ICMP port-unreachable=ferme, pas de reponse=ouvert|filtre (lent, rate-limite par l'OS cible)
nmap -sY -v <Target IP>         # SCTP INIT scan: equivalent SYN scan pour SCTP (VoIP/SS7/SIGTRAN); differencie clairement open/closed/filtered
nmap -sZ -v <Target IP>         # SCTP COOKIE-ECHO scan: plus furtif que INIT (contourne regles non-stateful) mais ne distingue pas open de filtered
nmap -sL -v <Target IP>         # List scan: ne scanne rien, juste resolution DNS inverse + sanity check de la cible/plage
nmap -6 <Target IP/Domain>      # Scan IPv6 de base
nmap -6 -O <target>             # OS discovery IPv6 (18 probes specifiques: S1-S6, IE1/IE2, NI, NS, U1, TECN, T2-T7)
```

Piege UDP: la rate-limitation ICMP (RFC 1812 4.3.2.8) rend le scan tres lent sur Linux/BSD mais
Windows ne rate-limite pas -> scan UDP bien plus rapide sur cibles Windows.

## Service/version detection et optimisation du temps de scan (p.74-78)

```
nmap -sV <Target IP>            # Version detection: interroge la base service-probes de Nmap
nmap -sV --reason -v -sT <Target IP>   # combo utile: raison de l'etat du port + verbose + connect scan
```
Techniques pour reduire le temps de scan (utile sur CTF/time-boxed engagement):
- Omettre les tests non-critiques: `-sn` seul si juste host discovery necessaire; eviter `-sC -sV -O
  --traceroute -A` si non requis; desactiver la resolution DNS (`-n`) quand inutile.
- `-T<0-5>` pour ajuster l'agressivite du timing (T4/T5 sur reseau peu filtre).
- Separer scans TCP et UDP (profils de performance differents, UDP plus sensible au rate-limit ICMP).
- Paralleliser plusieurs instances Nmap sur sous-groupes d'IP plutot qu'un seul run sur tout le /16.
- Scanner depuis un point reseau favorable (interne > externe) sauf objectif explicite de tester le
  firewall perimetrique.

## OS discovery / banner grabbing (p.79-96)

Deux approches:
- **Active**: paquets TCP malformes envoyes et reponses comparees a une base de signatures
  (9 tests Nmap: SYN+ECN sur port ouvert, NULL sur port ouvert, URG+PSH+SYN+FIN sur port ouvert,
  ACK sur port ouvert, SYN sur port ferme, ACK sur port ferme, URG+PSH+FIN sur port ferme, UDP vers
  port UDP ferme (PU), TSeq = pattern ISN/IPID/timestamp sur 6 SYN).
- **Passive**: sniffing du trafic cible (Wireshark) + lecture TTL, TCP window size, bit DF, TOS.
  Egalement: erreurs de serveur (banniere du type serveur/OS/outil SSL), extensions de page
  (`.aspx` -> IIS/Windows).

### Table TTL/Window par OS (p.84-85, a memoriser pour fingerprint rapide)

| OS | TTL | TCP Window |
|---|---|---|
| Linux | 64 | 5840 |
| FreeBSD | 64 | 65535 |
| OpenBSD | 255 | 16384 |
| Windows | 128 | 65535-1Go |
| Cisco Routers | 255 | 4128 |
| Solaris | 255 | 8760 |
| AIX | 255 | 16384 |

Commandes:
```
nmap -O <Target IP>                                     # OS discovery actif (device type + OS CPE + confidence)
nmap -sV -v --script nbstat.nse <Target IP>              # alternative: fingerprint via NetBIOS (module 04)
nmap --script smb-os-discovery <Target IP>               # NSE: OS via protocole SMB
nmap -6 -O <target>                                      # IPv6 fingerprinting (voir section precedente)
ping -c 1 <IP> ; # lire le TTL dans la reponse -> Linux/Unix=64, Windows=128
unicornscan <Target IP> -I                                # lire TTL dans le resultat pour deduire l'OS
```
Piege important: les outils qui forgent eux-memes leurs paquets (Nmap, Hunt, Nemesis) n'ont pas la
meme signature que l'OS -> le fingerprinting passif peut se tromper sur une machine qui scanne
elle-meme. Egalement, TTL/window/DF/TOS sont modifiables manuellement par un defenseur avise.

## Scanning Beyond IDS and Firewall - evasion (p.100-129)

Techniques, dans l'ordre de sophistication croissante:

### Packet fragmentation + SYN/FIN scan via fragments (p.102-103)
Decoupe l'entete TCP en plusieurs petits paquets IP pour que l'IDS/firewall base sur signature ne
reconnaisse pas le pattern de scan (le filtrage/reassemblage coute cher en CPU, beaucoup d'IDS skip
les paquets fragmentes). Nmap: `-f` (fragmente), combinable: `nmap -sS -T4 -A -f -v <Target IP>`.
Attention: peut provoquer crash/reboot sur des stacks IP fragiles cote cible (effet de bord DoS
non-intentionnel a connaitre).

### Source routing (p.104)
Manipuler le champ IP Options pour forcer le paquet a suivre une route choisie par l'attaquant
(loose/strict source routing), evitant ainsi les routeurs ou sont configures le firewall/IDS.

### Source port manipulation (p.105-106)
Exploite les firewalls qui font confiance aveuglement aux ports source "connus" (HTTP/DNS/FTP).
```
nmap -g 80 <Target IP>            # --source-port 80 - fait croire que le trafic vient du port 80
nmap --source-port 53 <Target IP> # idem avec DNS
```

### IP Address Decoy (p.107-109)
Noie le scan reel parmi plusieurs IP decoy pour rendre l'attribution difficile dans les logs IDS.
```
nmap -D RND:10 <target>                                   # 10 decoys generes aleatoirement, IP reelle placee au hasard
nmap -D decoy1,decoy2,decoy3,ME,decoy5 <target>           # decoys manuels; ME place l'IP reelle a une position choisie
```
Limite: inefficace contre un defenseur qui fait du path-tracing actif ou du response-dropping; trop
de decoys ralentit et degrade la precision du scan.

### IP Address Spoofing (p.110-111)
```
hping3 www.target.com -a 7.7.7.7      # -a = spoof l'adresse source
```
Note critique: impossible de completer un handshake TCP complet avec une IP spoofee (la reponse
SYN/ACK part vers l'IP spoofee, pas vers l'attaquant) -> utile pour DoS / probing one-way, pas pour
une connexion complete.

### MAC Address Spoofing (p.112-114)
```
nmap -sT -Pn --spoof-mac 0 <Target IP>          # MAC aleatoire generee automatiquement
nmap -sT -Pn --spoof-mac <Vendor> <Target IP>   # MAC d'un vendor choisi (ex: Apple, Cisco...)
nmap -sT -Pn --spoof-mac <MAC> <Target IP>      # MAC manuelle precise
```
Utile pour contourner un filtrage MAC et ne pas laisser la vraie MAC dans les logs du firewall local.

### Creation de paquets custom (p.115-117)
Outils: Colasoft Packet Builder (templates TCP + edition decodeur/hex/ASCII, checksum auto, envoi
direct sur le wire, controle de l'intervalle entre paquets/loop), NetScanTools Pro. Usage offensif:
construire des paquets fragmentes specifiques pour bypasser firewall/IDS, ou flooder une victime
(DoS) avec un volume de paquets customises.

### Randomizing host order + bad checksums (p.118-120)
```
nmap --randomize-hosts <target range>    # melange l'ordre de scan par groupe de 16384 hosts -> moins reperable par les IDS/firewalls
nmap --badsum <Target IP>                # envoie des checksums TCP/UDP/SCTP invalides
```
`--badsum`: une vraie pile IP ignore/drop silencieusement un paquet a checksum invalide; si on recoit
une reponse quand meme, cela trahit un IDS/firewall qui ne verifie pas le checksum (signature utile
pour fingerprinter le dispositif de securite lui-meme).

### Proxy servers / proxy chaining / anonymizers (p.121-129)
- Proxy chaining: faire transiter la requete a travers N proxies (chaque proxy retire l'info
  d'identification precedente) -> plus de proxies = plus d'anonymat mais plus de latence.
- Outils cites: Proxy Switcher, CyberGhost VPN, Burp Suite (comme proxy), Tor, Hotspot Shield,
  Proxifier, IPRoyal Residential Proxy.
- Anonymizers: networked (multi-noeuds, traffic analysis complexe mais risque de compromission a
  chaque noeud) vs single-point (plus simple, moins resistant a l'analyse de trafic sophistiquee).
  Outils: Whonix (Debian durci + Tor, VMs isolees), Tails (OS live USB, zero trace disque), Psiphon,
  TunnelBear, I2P, AstrillVPN, Bright Data Proxy API.
- Usage offensif direct: configurer un anonymizer comme proxy HTTP/FTP/Gopher permanent dans la
  config de l'outil d'attaque pour masquer systematiquement toutes les activites.

## Contremesures (utiles offensivement pour anticiper/tester l'evasion) (p.130-144)

### Ping sweep countermeasures (p.131)
Blocage ICMP echo entrant depuis sources non fiables, IDS/IPS (Snort), limite de connexion apres
10 requetes ICMP ECHO d'un meme host, DMZ n'autorisant que ECHO_REPLY/HOST_UNREACHABLE/TIME_EXCEEDED,
rate limiting ICMP, segmentation reseau, NAT pour masquer les IP internes.
-> Implication offensive: si le ping sweep classique echoue, basculer immediatement sur TCP
SYN/ACK ping ou scan direct de ports connus (80/443/22) sans phase de host-discovery ICMP.

### Port scanning countermeasures (p.132-133)
Firewall/IDS inspectant le contenu des paquets (pas juste l'entete TCP), ports filtres: 135-159,
256-258, 389, 445, 1080, 1745, 3268; blocage ICMP type-3 unreachable sortant; anti-source-routing;
honeypots sur ports scannes; port knocking; NAT; egress filtering; VLANs.
-> Implication offensive: s'attendre a des honeypots sur les ports "faciles" ouverts — valider les
services decouverts avant d'investir du temps d'exploitation (banner trop generique = suspect).

### Banner grabbing countermeasures (p.134-135)
- Apache: `ServerSignature Off` et `ServerTokens Prod` dans httpd.conf; mod_headers pour renommer le
  serveur.
- IIS: `RemoveServerHeader=1` dans UrlScan.ini; `AlternateServerName` pour tromper l'attaquant;
  retrait du header `X-Powered-By` via `<customHeaders>` dans web.config.
- Masquage des extensions de fichiers (`.asp` -> `.htm`/`.foo` via mod_negotiation) pour ne pas
  reveler la techno serveur.
- Desactivation des methodes HTTP risquees: CONNECT, PUT, DELETE, OPTIONS.
-> Implication offensive: ne pas se fier uniquement a la banniere HTTP/FTP/SSH affichee — confirmer
via comportement (fingerprint TTL/window, erreurs specifiques, timing) si la banniere semble
modifiee/generique.

### Detection de l'IP spoofing - techniques utiles pour valider sa propre furtivite (p.136-139)
- **Direct TTL Probes**: comparer le TTL d'un paquet suspect avec le TTL d'une reponse directe au
  host legitime; mismatch = spoofe. Marche surtout si l'attaquant est sur un subnet different de la
  victime.
- **IP Identification Number**: sonder l'IPID de la source pretendue et comparer avec l'IPID du
  paquet suspect (doit etre proche/legerement superieur); fiable meme sur meme subnet.
- **TCP Flow Control Method**: un attaquant spoofant ne recoit jamais le SYN-ACK donc ne peut pas
  reagir aux changements de fenetre de congestion -> si le flux continu apres epuisement de la
  fenetre initiale, c'est probablement du spoofing.
-> Implication offensive: ces 3 methodes sont exactement ce qu'un defenseur utilisera pour detecter
un decoy scan ou un IP spoofing — en tenir compte en evaluant le risque de detection reel d'une
technique d'evasion avant de la deployer sur une cible surveillee.

### IP spoofing countermeasures + outils de detection de scan (p.140-143)
Chiffrement du trafic (IPsec/TLS/SSH/HTTPS), multi-firewall en profondeur, pas d'authentification
IP-only, ISN aleatoires, ingress/egress filtering sur routeurs. Outils de detection de scan cites:
ExtraHop (visibilite temps reel + decouverte auto des devices/IoT), Splunk Enterprise Security,
Scanlogd, Vectra Detect, IBM Security QRadar XDR, Cynet 360 AutoXDR.
