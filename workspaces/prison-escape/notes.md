# Prison Escape — notes de progression

## État : instance HTB down (connexion refusée depuis ~19:35 UTC). Action requise : **redéployer la cible sur la plateforme HTB**, puis reprendre.

## Résumé de l'avancée

### 1. Archive (`/home/kali/Downloads/a12c73aa-a2bd-4a12-95ba-246a5f41af9c.zip`)
- Mot de passe zip : `hackthebox` (mot de passe par défaut HTB)
- Contient `blueprint.png` (plan drawio, surtout thématique) et `Omega.pdf` (doc protocole RF "Omega", clé)

### 2. Doc Omega.pdf — specs protocole RF
- Bande 433.92 MHz, modulation RF custom
- Alarm Packet types : Suppress=0xF1, Alert=0xA0, Broadcast=0x03
- Laser Packet types : Move left=0x91, Move right=0x53, Turn off=0xFF, Turn on=0xEE
- CRC anti-replay : `initCRC(0x1d0f)`

### 3. Service web (154.57.164.71:42477)
- Flask app, formulaire POST `/transmit` (freq, mod, bits, msg hex)
- `/capture` télécharge une capture IQ brute (.complex, float32) d'un vrai paquet intercepté
- Session cookie Flask (itsdangerous) contient l'état réel en clair (compressé zlib, signé) :
  `{"a1":...,"a2":...,"a3":...,"a4":...,"e1":bool,"e2":bool,"e3":bool,"lock":bool}`
  - a1-a4 = alarmes ("Idle" ou `false`=suppressed)
  - e1-e3 = lasers (true=actif)
  - lock = probablement la porte de sortie

### 4. Reverse engineering RF (via Universal Radio Hacker, installé dans `artifacts/venv_urh`)
- Modulation : **FSK**, 100 samples/symbole, 1 bit/symbole, sample_rate 1MHz
- Format paquet démodulé (hex) : `AAAAAAAA 69781621 [SRC] [TARGET] [TYPE] [CRC16_BE]`
  - Préambule : `AAAAAAAA` (32 bits de sync 0xAA)
  - Header constant : `69781621` (confirmé identique sur 2 captures indépendantes)
  - SRC : 1 octet (semble peu/pas vérifié par le serveur)
  - TARGET : 1 octet — **doit être une adresse valide pour que le serveur accepte le paquet** (Set-Cookie émis seulement si valide)
  - TYPE : 1 octet (semble non vérifié pour les alarmes — n'importe quel TYPE avec un TARGET valide suffit)
  - CRC16 : CRC-CCITT (poly 0x1021, init 0x1d0f, non réfléchi), calculée sur TOUS les octets précédents (y compris le préambule), big-endian

- Fonction Python de construction (confirmée exacte sur 2 paquets réels capturés) :
```python
def crc16_ccitt(data, init=0x1d0f, poly=0x1021):
    crc = init
    for b in data:
        crc ^= (b << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ poly) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc

PREAMBLE = bytes.fromhex('AAAAAAAA')
HEADER = bytes.fromhex('69781621')
def build(src, target, typ):
    body = PREAMBLE + HEADER + bytes([src,target,typ])
    crc = crc16_ccitt(body)
    return (body + bytes([crc>>8, crc&0xFF])).hex().upper()
```
- POST vers `/transmit` : `freq=433.92`, `mod=FSK`, `bits=1`, `msg=<hex ci-dessus>`

### 5. Adressage confirmé par fuzzing (256 valeurs testées pour TARGET)
- **Alarmes : TARGET = 0xA1, 0xA2, 0xA3, 0xA4** → accepté quel que soit le TYPE, met `aN` à `false` (suppressed)
  - ✅ **Les 4 alarmes ont été suppressées avec succès** pendant la session (a1=a2=a3=a4=false)
- **Lasers (E1/E2/E3) : adresse TOUJOURS INCONNUE.**
  - Fuzzing exhaustif de TARGET (0x00-0xFF) avec TYPE=0xFF, 0x91, 0x53, 0xEE : **aucun hit** en dehors de 0xA1-0xA4
  - Fuzzing exhaustif de SRC (0x00-0xFF) avec TARGET=0xE1 fixe : **aucun hit**
  - → La structure/adressage des paquets laser est probablement DIFFÉRENTE de celle des alarmes (champ différent, longueur différente, ou mécanisme différent, p.ex. adressage par fréquence plutôt que par octet TARGET). Hypothèse non testée : peut-être que chaque laser écoute sur une fréquence légèrement différente (`freq` du formulaire) plutôt que via un octet d'adresse.
  - Seule capture RF obtenue = broadcasts d'alarmes (A1, A4) — jamais de paquet laser capturé via `/capture` malgré ~35 téléchargements répétés.

### 6. Pistes explorées et écartées
- Crack de la clé secrète Flask (`flask-unsign`) : liste par défaut épuisée sans succès ; brute-force rockyou trop lent (~20 req/s en Python pur, infaisable en temps raisonnable) — **abandonné**, mais pourrait être retenté avec un outil plus rapide (hashcat) si on obtient un vrai GPU/CPU dédié.
- Forge de cookie sans connaître la clé : rejeté, signature bien vérifiée côté serveur (reset propre à l'état par défaut).
- Pas de leak de code source / stack trace (inputs malformés gérés proprement, toujours 200 + même page).

## Prochaines étapes (reprendre ici)
1. Redéployer la cible HTB (le service ne répond plus : connexion refusée sur 154.57.164.71:42477).
2. Une fois en ligne, ré-suppresser les 4 alarmes (script ci-dessus, boucle a=1..4).
3. Chercher le bon adressage/mécanisme pour les lasers E1-E3 :
   - Tester la variation du champ `freq` du formulaire combinée à différents TARGET/TYPE
   - Télécharger `/capture` en boucle avec des délais plus longs/variés, en espérant capter un paquet laser pour en déduire le vrai format par le même procédé CRC/URH
   - Envisager une structure de paquet à 2 octets de payload (sans SRC) spécifique aux lasers
4. Une fois a1-a4=false ET e1=e2=e3=false (ou si suppress alarmes seul suffit — à vérifier en consultant `/` et `/updates` juste après suppression), vérifier le cookie pour `lock:true` et chercher le flag dans `/updates` (Mission Status) ou ailleurs.

## Outils installés
- `urh` (Universal Radio Hacker) dans `/home/kali/ctfagent/workspaces/prison-escape/artifacts/venv_urh` (venv Python, utilisable en mode headless/bibliothèque sans GUI)
- `flask-unsign` installé globalement (`~/.local/bin/flask-unsign`)
