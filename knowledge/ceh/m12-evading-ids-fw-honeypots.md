# CEH M12 - Evading IDS, Firewalls, and Honeypots (synthese offensive)

Source: `CEHv13 - Module 12 - Evading IDS, Firewalls, and Honeypots hide01.ir.pdf` (166 pages),
OCR complet 166/166. Page = pagination du module ("Module 12 Page NNN", commence a 1571).
Theorie d'examen/countermeasures omise sauf reutilisable offensivement.

## 1. Evasion au niveau paquet/reseau (nmap, hping)

- **Tiny fragments**: fragmenter les paquets sortants pour forcer une partie de l'en-tete TCP
  dans le fragment suivant -> casse le pattern-matching de l'IDS si le firewall ne verifie que
  le premier fragment.
- **IP Address Spoofing**: forger l'IP source pour usurper un hote de confiance et bypasser un
  filtrage par IP. Outil cite: **Hping** (creation de paquets personnalises, IP forgee).
- **Source Routing**: le paquet dicte lui-meme sa route (loose: certains relais imposes;
  strict: route complete imposee) pour transiter par des segments moins surveilles.
- **Firewalking**: technique a la Traceroute pour cartographier les regles d'un firewall -
  envoie des paquets avec TTL croissant pour determiner quels ports/protocoles sont autorises
  a travers lui. Outils: **Firewalk**, **script firewalk de Nmap**.
- **Honeypot/decoy detection cote defenseur a connaitre pour l'eviter**: pas de syntaxe
  `nmap -D` explicitement documentee dans ce module (voir section 5 pour la detection de
  honeypot, qui est l'inverse: identifier qu'ON scanne un honeypot).

## 2. Tunneling pour bypass firewall/IDS (le coeur offensif du module)

```
# ICMP tunneling - backdoor shell dans la data des paquets ICMP Echo (souvent autorise en sortie)
# -> tunnel generique via payload ICMP echo request/reply (ex outil: ptunnel / icmptunnel)

# ACK tunneling - paquets avec le flag ACK set (traverse les firewalls stateless qui trustent
# les ACK comme reponse a une connexion deja etablie)
# Outils cites: Hping, Nping pour forger ces paquets ACK porteurs de payload malicieux

# HTTP tunneling - encapsule n'importe quel protocole dans du trafic HTTP (port 80/443 presque
# toujours ouvert en sortie)
# Outils cites: HTTPort, HTTHost, Tunna
# Modes HTTPort: SSL/CONNECT mode, ou remote host mode (tunnel via n'importe quel proxy)

# SSH tunneling - port forwarding via SSH pour faire transiter du trafic non chiffre dans un
# tunnel SSH chiffre, bypass IDS/firewall qui n'inspecte pas le contenu SSH
# Outil cite: Bitvise SSH Server/Client (plusieurs methodes de port forwarding)

# DNS tunneling - encapsule des donnees dans des requetes/reponses DNS (port 53 presque
# toujours autorise, souvent non inspecte en profondeur)
# Outil cite: iodine (tunnel IPv4 complet via un serveur DNS controle par l'attaquant)
```
Piege commun a toutes ces techniques: elles exploitent un **port de confiance** (80/443/53) ou
un **etat de connexion suppose legitime** (ACK) plutot qu'une faille logicielle - le choix du
tunnel depend uniquement de ce qui est autorise en sortie sur la cible.

## 3. Techniques d'evasion IDS plus fines (niveau protocole)

- **Insertion attack**: forcer l'IDS a accepter un paquet invalide (ex: checksum IP corrompu
  volontairement) que la machine cible rejette -> IDS et cible desynchronisent leur vision du
  flux (IDS voit "Atxack", la cible voit "Attack").
- **Evasion attack**: l'inverse - l'IDS rejette des paquets que la cible accepte (ex: donnees
  dans le paquet d'ouverture TCP handshake) -> l'IDS "voit" moins que ce qui arrive reellement.
- **Session Splicing**: decouper le trafic d'attaque en un grand nombre de petits paquets pour
  qu'aucun ne declenche seul une signature; ajouter des delais entre paquets si le timeout de
  reassemblage de l'IDS est connu, pour qu'il abandonne le suivi de session avant la cible.
  Outil cite: **Nessus** pour ce type d'attaque.
- **Unicode evasion**: encoder la payload en UTF-8/UTF-16 (ex `%u2215` pour `/`, `%c2%a0`)
  pour que l'IDS base sur pattern-matching ASCII ne reconnaisse pas la signature, alors que le
  serveur cible (IIS, etc.) la decode normalement.
- **Fragmentation attack (2 scenarios documentes)**:
  - Scenario 1: timeout de reassemblage IDS < timeout cible -> envoyer les fragments avec un
    delai superieur au timeout IDS (mais inferieur a celui de la cible) -> l'IDS droppe, la
    cible reassemble et execute l'attaque sans alerte.
  - Scenario 2: timeout IDS > timeout cible -> envoyer d'abord des fragments avec un **faux
    payload** (frag-2', frag-4') recus par les deux, attendre l'expiration cote cible (qui les
    droppe faute de frag-1/3), puis envoyer frag-1/frag-3 legitimes (la cible les accepte
    seuls), puis renvoyer frag-2/frag-4 **legitimes** - a ce moment l'IDS a deja reassemble et
    jete sa version (avec checksum invalide sur les faux fragments), donc ne revoit jamais la
    version correcte, alors que la cible, elle, accumule tous les bons fragments.
- **TTL attack**: meme logique que la fragmentation mais en jouant sur le TTL d'un fragment
  intermediaire pour qu'il atteigne l'IDS (qui le garde) sans atteindre la cible (route plus
  longue, le routeur le droppe) -> necessite de connaitre la topologie au prealable (obtenue
  via `traceroute`).
- **Urgency Flag (URG)**: placer des donnees "garbage" avant le pointeur d'urgence TCP; un IDS
  qui ignore le flag URG lit tout le flux (y compris le garbage) alors que la cible ne traite
  que les donnees apres le pointeur -> desynchronisation similaire a l'insertion attack.
- **Obfuscating**: encoder la payload (Unicode, steganographie numerique) pour que seule la
  cible puisse decoder, pas l'IDS signature-based. **Polymorphic shellcode**: generer un
  shellcode different a chaque fois pour eviter toute signature fixe.
- **False Positive Generation**: generer volontairement un gros volume d'alertes IDS
  "legitimes mais inoffensives" pour noyer la vraie attaque dans le bruit de logs.
- **DoS contre l'IDS lui-meme**: epuiser CPU/memoire/disque/bande-passante de l'IDS (ou de son
  serveur de logs centralise, si son IP est connue) pour qu'il cesse de logger pendant
  l'attaque reelle.

## 4. Techniques complementaires (citees, moins detaillees)

- **Invalid RST Packets**, **ASCII Shellcode**, **Application-Layer Attacks**,
  **Desynchronization**, **Domain Generation Algorithms (DGA)** (rotation de domaines C2 pour
  echapper au blocklisting DNS/IDS), **Encryption** (chiffrer la payload pour empecher toute
  inspection signature), **Flooding** (saturer l'IDS de trafic benin pour masquer l'attaque).

## 5. Detecter un honeypot avant de s'y faire piquer

```
nmap -sV -p 80 <target_ip>                         # fingerprint du service - incoherences = suspect
nmap -p 80 --scan-delay 1s --max-retries 5 <target_ip>   # latence anormale/variable = suspect
arp-scan --interface=eth0 --localnet               # MAC avec OUI inhabituel = VM/honeypot probable
nmap -p- <target_ip>                                # ports ouverts inattendus (ex: 21/22 ouverts
                                                      # sur un "simple serveur web") = suspect
```
- Methode complementaire: analyser la config systeme/metadata exposee (banners par defaut,
  versions non mises a jour, incoherences) - souvent le honeypot n'implemente pas totalement
  le comportement attendu du service qu'il emule.
- Honeypots courants a reconnaitre dans des bannieres/comportements (pour savoir qu'on est
  face a un piege et pivoter): **HoneyBOT**, **Cowrie** (SSH/Telnet honeypot tres repandu en
  CTF), **Valhala Honeypot**, **Blumira**, **StingBox**, **NeroSwarm**.

## Ordre de sonde recommande

1. Reconnaitre le firewall/IDS en place (banner grabbing, comportement de reponse) avant de
   choisir une technique d'evasion specifique.
2. Tester les tunnels sur les ports presque toujours ouverts en sortie (80/443/53) avant
   d'investir dans de la fragmentation/TTL plus complexe a fiabiliser.
3. Si le trafic doit rester discret cote detection, preferer session splicing/encoding
   (Unicode, chiffrement) a des techniques bruyantes (flooding, false positive generation) sauf
   si l'objectif est justement de noyer une autre action dans le bruit.
4. Toujours valider qu'on ne cible pas un honeypot (section 5) avant d'investir du temps dans
   l'exploitation d'un service qui semble "trop ouvert" ou incoherent.
