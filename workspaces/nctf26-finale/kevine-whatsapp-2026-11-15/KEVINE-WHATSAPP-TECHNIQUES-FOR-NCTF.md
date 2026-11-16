# Kevine WhatsApp drop — techniques pour NCTF (2026-11-15)

Source: chat WhatsApp **KevineCharles CTF**, lot du jour **09:59–10:06** (pas 14h59 — rien à cette heure).
Fichiers rapatriés dans `incoming/` + `zip-extract/` (archive non fiable, jamais exécutée).
Tout est issu de **HackerLab 2026** (scène africaine, même famille que NCTF) — campagne DFIR/OT
« Opération Tervalis / Designated Survivor » + 2 challenges reverse/crypto/OSINT.

## Fichiers reçus
| Fichier | Type | Contenu |
|---|---|---|
| `Rapport_Designated_Survivor.md` | DFIR | Rapport d'attribution 6 affaires (le plus dense) |
| `GBT_HACKERS_Rapport_Incident_DesignatedSurvivor.pdf` | DFIR | Version 33 p du même rapport (captures) |
| `SH1NY_HUNT3RS_REPORT.pdf` | DFIR | Rapport 18 p d'une autre équipe (angle OT/DNP3 + false-flag) |
| `GBT_HACKERS_Rapport.pdf` | DFIR | Rapport court 6 p |
| `writeup_q1_q6.txt` | multi | HCT Q1–Q6 (Morse, logs, SSTI, systemd, C2, LXC/AppArmor) |
| `writeup_eidolon_q1_q2.md` | OSINT/misc | Watermark audio IA + collision MD5 login |
| `ashen_seal_kit.zip` | reverse/crypto | Kit d'émulation Unicorn + writeup chiffre custom |

---

## Techniques → catégorie NCTF

### Forensics / DFIR (lourd ici — campagne multi-affaires)
- **Attribution par recoupement d'IOC** : même e-mail opérateur (`mateus.varga@varelcorp.var`) à la fois
  expéditeur phishing ET titulaire infra C2 ; même bloc IP (`203.0.113.0/24` = Varelia) sur 3 affaires →
  conclure "campagne unique APT", pas 6 incidents. Garder l'hypothèse **false-flag** comme note (SH1NY insiste :
  les tags `nation:Varelia` sont falsifiables).
- **Phishing — DKIM homographe/punycode** : l'en-tête DKIM `d=` révèle `xn--varelcrp-s4a.var` (= `varelcörp.var`)
  au lieu du domaine affiché légitime → preuve d'usurpation. Toujours comparer **From affiché vs domaine signataire DKIM**.
- **Masquerade de process** : faux `smss.exe` dont le PID/parent ne colle pas (vrai smss déjà actif, enfant de System).
- **Persistance Linux à chercher** : beacon `curl` périodique caché dans `/etc/update-motd.d/*` (motd), cron backdoor,
  compte sudoers illégitime, keylogger, fichiers temp `/dev/shm/.f` `/dev/shm/.editor_swap`.
- **Timeline de logs** : IP source + 1ʳᵉ occurrence (`203.0.113.42 @ 16/Aug/2026:15:58:59`), repérer `/.git/config`,
  `/console` dans les access logs.
- **Signal/radio forensics (OT)** : capture WAVE → **décodage AFSK** → trames télémétrie TLM/EXF (exfil cachée
  dans la télémétrie radio des compteurs). Pré-stage un décodeur AFSK.

### OT / ICS
- **DNP3** : service `dnp3d` sur **tcp/20000** ; parseur réseau accepte une trame forgée → **RCE uid=0** (reverse du binaire).
- **Pivot IT→OT** via historian ; **StrongBox** = coffre de config gateway à chiffrement faible → master key des sous-stations.
- **Session opérateur C2 chiffrée RC4, clé littérale `VARELID`** (C2 `203.0.113.66:8443`). Repérer `RC4(key=...)` dans le pcap.

### Web
- **SSTI Jinja2** `{{7*7}}` → RCE via `POST /espace-usager/reclamation` (route de réclamation usager).
- **CORS mal configuré** : réflexion arbitraire de `Origin` + `credentials:true` → **CSRF authentifié** (virement bancaire
  à l'insu de l'admin via script pub tiers). Tester reflection d'Origin + cookies.
- **CVE-2022-44268** (ImageMagick, lecture de fichier arbitraire via PNG forgé) → accès initial serveur web → vol `.env`.
- **Fuite d'identifiants dans l'historique Git** (`/.git/config` exposé) → accès initial, puis **commit malveillant dans
  le pipeline** = attaque supply-chain logicielle.

### Reverse / Malware  (kit `ashen_seal`)
- **Backdoor supply-chain façon CVE-2024-3094 (xz/liblzma)** : hijack de dépendance sur le serveur DNS AquaWatch.
- **Extraire une clé dérivée par le malware via émulation Unicorn** quand le C2 ne rejoue plus la tâche `encrypt` :
  démarrer à l'entry point (libc statique s'initialise : TLS/tcache), fournir pile+auxv (`AT_RANDOM`), handler de
  syscalls (`getrandom`, `open`/`read` sert le SEED pour `/dev/urandom`), **injecter une réponse C2 forgée**
  `{"op":"encrypt","arg":"<secret>"}` au parseur, hooker les IFUNC PLT (`strstr`/`memcpy`/`sscanf %2hhx`), puis
  **hook sur l'entrée de `encrypt()` → lire `rsi` = pointeur de clé (16 o)**.
- **Chiffre par blocs custom** (aucune lib std) : SPN **4 rounds** `ROTL128(keymix(cumsum(permute(subbytes(x)))), n)`,
  mode **CBC** `IV=SHA256(key[:16])`, tables (S-box/permutation/table4) dérivées d'un **xorshift32 graine fixe `0x4c594e58`**
  (donc indépendantes de la clé, lisibles en RAM). Inversion : capturer le **masque keymix** aux frontières de round
  plutôt que reconstruire l'état interne. → script `femu.py`/`emu.py` réutilisables comme gabarit.

### Misc / OSINT (`writeup_eidolon`)
- **Détection audio généré par IA** : métadonnée ID3 `TSSE: Lavf61.1.100` = signature **FFmpeg/libavformat** (un vrai
  dictaphone Samsung ne la produit jamais) ; puis **watermark AudioSeal (Meta)** détecté sur une **fenêtre courte**
  (slice 0.6–2.6 s → confiance ~99.6 %, le clip entier passe sous le seuil). Contrôle: bruit blanc → confiance 0.
- **Bypass login par collision MD5** : logique `u!=p AND md5(u)==md5(p)` → utiliser la paire de collision publique
  **Wang et al. 2004** (2 blocs 128 o), encodée base64. Accès via **Tor** (`curl --socks5-hostname 127.0.0.1:9050`, .onion).
- **Pyjail/sandbox** container : évasion par **`lxc.apparmor.profile=unconfined`** (désactive AppArmor du conteneur).

### Infra challenge (utile le jour J)
- **HackerLab = instances dynvpn/WireGuard** : `GET /api/v1/dynvpn/config` → `wg-quick up`, route `172.28.0.0/16`,
  SSH challenge type `water_technician@172.28.X.2`. Flags/clés **spécifiques à l'instance** (rotation) → ré-automatiser.
