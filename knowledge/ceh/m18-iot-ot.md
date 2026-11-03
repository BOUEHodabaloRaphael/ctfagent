# CEH M18 - IoT and OT Hacking (synthese offensive)

Source: `CEHv13 - Module 18 - IoT and OT Hacking hide01.ir.pdf` (258 pages), OCR complet
258/258. Page = pagination du module ("Module 18 Page NNN", commence a 2767). Theorie
d'examen/countermeasures omise sauf reutilisable offensivement. Module le plus pertinent du
lot pour les challenges OT actifs - traitement prioritaire et detaille.

Structure: IoT concepts/attack surface -> Hacking IoT devices (recon, firmware,
hardware/UART/JTAG) -> IoT attack countermeasures -> OT concepts (Modbus/DNP3/S7/BACnet) ->
Hacking OT (Shodan ICS, Nmap NSE scripts, fuzzing) -> OT countermeasures.

## 1. Reconnaissance IoT/OT - moteurs de recherche specialises

```
# Shodan - devices IoT generiques (webcams, routeurs, home automation)
shodan.io/search?query=webcamxp+country:"US"
webcamxp city:paris
webcamxp geo:-50.81,201.80

# Shodan - ICS/SCADA (le plus directement utile pour OT)
port:502                              # Modbus-enabled ICS/SCADA
"Schneider Electric"                  # par nom de PLC/fabricant (banner)
SCADA country:"US"                    # par geolocalisation
```
- Filtres Shodan complementaires: `net:` (IP/CIDR), `os:`, `port:`, `before:`/`after:` (fenetre
  temporelle).
- **Ports SCADA/ICS a connaitre par coeur** (pivot direct vers un dork Shodan ou un scan cible):
  Modbus **502**, Fieldbus **1089-1091**, DNP **19999**, DNP3 **20000**, Ethernet/IP **2222**/
  **44818**, PROFINET **34962-34964**, EtherCAT **34980**, S7comm **102**, BACnet **47808**,
  Niagara Fox **1911/4911**, ProConOS **20547**, Omron **9600**, PCWorx **1962**, Sielco Winlog
  HMI **46824**.
- Autres moteurs: **Censys**, **FOFA** (en.fofa.info, equivalent chinois de Shodan, scans ZMap/
  ZGrab quotidiens), **ZoomEye**.
- Sniffing passif pour devices non exposes au net mais a portee radio: **Wireshark**,
  **CloudShark**, **Suphacap** (sniffer Z-Wave dedie, fonctionne avec tous les controleurs
  Z-Wave), **Open Sniffer** (capture 802.15.4/Zigbee/6LoWPAN/WirelessHART/ISA100.11a),
  **KillerBee**/**CatSniffer** (attaques Zigbee/802.15.4 - sniffing + injection).

## 2. Scan actif ICS/SCADA avec Nmap (coeur offensif OT)

```
# Recon initiale large - tous les ports ICS/SCADA connus en une passe (discret: scan-delay + 1 thread)
nmap -Pn -sT --scan-delay 1s --max-parallelism 1 -p 80,102,443,502,530,593,789,1089-1091,1911,\
1962,2222,2404,4000,4840,4843,4911,9600,19999,20000,20547,34962-34964,34980,44818,46823,46824,\
55000-55003 <Target_IP>

# Siemens SIMATIC S7 PLC (port 102, S7comm)
nmap -Pn -sT -p 102 --script=s7-info <Target_IP>

# Modbus (port 502) - identifie aussi les Slave IDs
nmap -Pn -sT -p 502 --script modbus-discover <Target_IP>
nmap -sT -Pn -p- 502 --script modbus-discover --script-args='modbus-discover.aggressive=true' <Target_IP>

# BACnet (UDP 47808) - vendor, device name, serial, firmware version + detection des BBMD
nmap -Pn -sU -p 47808 --script bacnet-info <Target_IP>
# enumeration plus poussee: script NSE "BACnet-discover-enumerate.nse"

# EtherNet/IP (UDP 44818, encapsule CIP)
nmap -Pn -sU -p 44818 --script enip-info <Target_IP>

# HMI Sielco Sistemi Winlog
nmap -Pn -sT -p 46824 <Target_IP>

# Niagara Fox (Tridium)
nmap -Pn -sT -p 1911,4911 --script fox-info <Target_IP>

# ProConOS
nmap -Pn -sT -p 20547 --script proconos-info <Target_IP>

# Omron PLC
nmap -Pn -sT -p 9600 --script omron-info <Target_IP>

# PCWorx
nmap -Pn -sT -p 1962 --script pcworx-info <Target_IP>
```
Piege/bonne pratique: **toujours scanner en mode discret** (`--scan-delay`, `--max-parallelism
1`, `-Pn` pour eviter un ping qui peut planter certains PLC fragiles) - un PLC OT n'est pas un
serveur Linux robuste, un scan agressif peut le faire planter/perdre son etat (risque reel de
DoS physique, a documenter dans tout rapport de pentest OT).

## 3. Analyse/MITM de trafic Modbus (Wireshark)

Modbus/TCP n'a **aucun chiffrement ni authentification natifs** - tout attaquant en position
MITM (ARP spoofing, switch compromis) peut lire et falsifier les commandes en clair.
```
# Wireshark avec filtre d'affichage dedie
Modbus/TCP                     # filtre pour isoler le trafic Modbus dans une capture
```
Contenu observable en clair: Transaction ID, Function Code (lecture/ecriture de registres),
adresses et valeurs des registres -> suffisant pour rejouer ou falsifier une commande vers un
automate sans aucun credential.

## 4. Fuzzing des protocoles ICS (Fuzzowski)

```
# Fuzzing BACnet (UDP)
python -m fuzzowski 127.0.0.1 47808 -p udp -f bacnet -rt 0.5 -m BACnetMon

# Fuzzing Modbus (TCP)
python -m fuzzowski 127.0.0.1 502 -p tcp -f modbus -rt 1 -m modbusMon

# Fuzzing IPP (imprimantes reseau, souvent presentes sur VLAN OT/bureau)
python -m fuzzowski printer1 631 -f ipp -r get_printer_attribs --restart smartplug
```
Usage: identifier des crashs/comportements non documentes sur un protocole ICS avant
exploitation - **a ne faire que sur un environnement de test**, un PLC de prod qui crash = arret
de ligne physique.

## 5. Extraction et analyse de firmware (IoT, mais applicable aux devices OT embarques)

Pipeline complet, dans l'ordre:
```
# 1. Identifier le type de fichier
file xyz.bin

# 2. Verifier l'integrite / comparer un hash fourni
md5sum xyz.bin
cat xyz.md5

# 3. Chercher des chaines exploitables (creds, URLs, chemins internes)
strings -n 10 xyz.bin > strings.out
less strings.out

# 4. Inspection hexadecimale rapide (identifie parfois le type de build)
hexdump -C -n 512 xyz.bin > hexdump.out

# 5. Identifier et extraire le(s) systeme(s) de fichiers embarques
binwalk xyz.bin                                   # identifie les offsets/types (squashfs, jffs2, etc.)
dd if=xyz.bin bs=1 skip=922460 count=2522318 of=xyz.squashfs   # extraction manuelle a l'offset trouve

# 6. Monter le filesystem extrait
mkdir rootfs
sudo mount -t ext2 xyz.squashfs rootfs

# 7. Fouiller le filesystem monte
grep -rnw '/chemin/monte/' -e "password"           # creds hardcodes
cat etc/passwd etc/shadow                           # comptes locaux / hashs
find . -name '*.conf' -o -name '*.pem' -o -name '*.crt' -o -name '*.cfg'   # configs/cles privees
# alternative automatisee: Firmwalker (scanne tout ca en un script)

# 8. Emulation dynamique pour tester l'interface web/services sans le hardware physique
file <binaire>; readelf -h <binaire>                # identifier l'architecture CPU cible
qemu-mipsel -L <prefix> <binaire>
qemu-arm -L <prefix> <binaire>
qemu-<arch> -L <prefix> <binaire>
# alternative: copier qemu-<arch>-static dans le rootfs puis chroot pour emuler tout l'OS
```
- **Firmware Mod Kit** (`extract-firmware.sh` / `build-firmware.sh`, + variantes DD-WRT GUI):
  deconstruction/reconstruction automatisee d'images firmware (TRX/uImage, SquashFS/CramFS) -
  extraire, patcher, reconstruire, reflasher.
- **Firmware Analysis Toolkit**, **IoTVAS**: alternatives automatisees au pipeline manuel
  ci-dessus pour scanner rapidement un lot de firmwares.
- Risque a toujours mentionner: reflasher un firmware modifie peut **bricker** le device de
  facon definitive.

## 6. Acces root materiel bas niveau (UART/JTAG/NAND glitching)

Quand aucun acces logiciel n'est possible, passer par le PCB:
```
# Identifier une interface UART sur un PCB inconnu (avec un outil type Bus Auditor)
run busauditor.generic.uartscan -v 3.3 -p /dev/ttyACM0 -s 0 -e 1

# Identifier une interface JTAG
run busauditor.generic.jtagscan -v 3.3 -p /dev/ttyACM0 -s 0 -e 10
# alternative dediee: JTAGulator

# Se connecter en console UART une fois l'interface identifiee et reliee a un adaptateur USB
minicom -D /dev/ttyUSB0 -w -C bootlog.txt
```
**NAND glitching** (obtenir un shell root pendant le boot sans credential):
1. Observer les bootlogs via UART (`minicom`) pour identifier la puce flash et son process de
   boot/backup loader.
2. Court-circuiter brievement (quelques ms) la pin serial I/O de la puce flash memory vers la
   masse pendant le boot -> interrompt le chargement normal, force le fallback vers le backup
   loader.
3. Depuis la console U-Boot recuperee (`=>` prompt), lire les variables d'environnement
   (`printenv`/equivalent) pour recuperer la ligne `bootargs` exacte.
4. Rejouer le boot en injectant un shell racine directement dans les arguments kernel:
   ```
   setenv bootargs 'noinitrd console=ttyAM0,115200 rootfstype=ubifs ubi.mtd=5 root=ubi0:rootfs rw gpmi init=/bin/sh'
   nand read ${loadaddr} app-kernel 0x00400000 && bootm ${loadaddr}
   ```
   `init=/bin/sh` force un shell root au lieu du processus init normal -> acces root complet
   sans aucun credential, directement sur le filesystem reel du device.
- Materiel generique utile pour ce type d'attaque: pince de test + fil pour le court-circuit,
  convertisseur UART-USB, adaptateur JTAG, oscilloscope pour timing precis du glitch.

## 7. Protocoles et surfaces specifiques a connaitre (reference rapide)

- **Modbus/TCP** (502): zero auth/chiffrement natif -> MITM = controle total des registres.
- **S7comm** (102, Siemens): protocole proprietaire, `nmap --script=s7-info` suffit a
  fingerprint le modele exact.
- **BACnet** (UDP 47808): batiments/HVAC, `bacnet-info` + BBMD discovery.
- **EtherNet/IP + CIP** (UDP/TCP 44818): tres repandu industriel US (Rockwell/Allen-Bradley).
- **DNP3** (20000) et **Fieldbus** (1089-1091): SCADA electrique/eau, moins documentes ici mais
  memes principes (zero-auth historique, fuzzing possible).
- **Zigbee/802.15.4**: sniffable/injectable avec KillerBee/Open Sniffer/CatSniffer - cle
  reseau souvent recuperable car echangee en clair lors du provisioning si non securisee.
- **Z-Wave**: sniffable avec Suphacap, meme logique.
- **CoAP**: equivalent HTTP leger pour contraintes IoT - mentionne comme protocole a securiser
  mais pas de commande d'attaque specifique dans ce module (voir outils generiques type
  `coap-client` pour l'interaction manuelle si besoin en dehors de ce module).
- **MQTT**: cite comme protocole a securiser (TLS recommande en countermeasure) mais aucune
  commande d'attaque offensive specifique capturee dans l'OCR de ce module - reflexe standard
  hors-module: `mosquitto_sub -h <broker> -t '#' -v` pour sniffer tous les topics sur un broker
  mal configure (anonymous access autorise), tres frequent sur devices IoT/OT mal durcis.

## Ordre de sonde recommande pour un challenge OT

1. Shodan/Censys/FOFA passif si l'IP/domaine est deja publique - identifie le protocole exact
   et parfois le vendor/firmware avant tout paquet envoye.
2. Nmap cible sur la liste de ports ICS (section 2), **toujours en mode discret**
   (`--scan-delay`, `-Pn`, `--max-parallelism 1`) - un crash de PLC en plein challenge peut
   bloquer le service pour tout le monde.
3. Si un script NSE identifie le protocole (modbus-discover, s7-info, bacnet-info, enip-info):
   capturer le trafic avec Wireshark pour confirmer l'absence d'authentification avant de
   tenter une ecriture de registre.
4. Si acces physique/firmware disponible: pipeline binwalk/strings/grep (section 5) avant tout
   outil lourd - rentable et rapide, souvent des creds hardcodes suffisent.
5. JTAG/UART/NAND glitching (section 6) seulement si le logiciel est verrouille et qu'un acces
   physique au PCB est disponible - dernier recours, plus lent a mettre en oeuvre.

Note pour le solveur: aligne avec le memo HTB Pro Lab existant (`htb-prolab-fullport-scan-
cooldown`) - un scan trop agressif sur un environnement OT/IoT simule peut geler le service
beaucoup plus longtemps qu'un simple `nmap -p-` sur une cible web classique; privilegier la
liste de ports ciblee de la section 2 plutot qu'un scan complet.
