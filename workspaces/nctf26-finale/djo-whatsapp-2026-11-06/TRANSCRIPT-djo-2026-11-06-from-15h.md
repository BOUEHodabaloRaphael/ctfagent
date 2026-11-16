# WhatsApp — Djo l'indien — transcript à partir du 06/11/2026 15h00

Récupéré 2026-11-15 (demande user « récupère tout à partir de 15h00 »). Scope : 06/11 15:00 → 07/11 02:52
(le burst CTF ; au-delà la conversation repart sur d'autres sujets — dire si tu veux la suite).
⚠️ Contient des identifiants perso du user (gardés hors de ce résumé chat).

## Contexte juste avant (14:29, 06/11) — MISSION MetaCTF
Message user → Djo : CTF MetaCTF 21h–23h (heure Togo). Consigne : « ne crée pas un groupe sur mon
navigateur, connecte-toi à l'URL via navigateur headless via script, solve et soumets le flag vite,
avec mes identifiants. »
- URL : `https://compete.metactf.com/652/?auth=true&uid=1736669&tok=1647c43200f346340f0f8fca9087a61b`
- Identifiants : voir `incoming/CREDENTIALS.txt` (non recopiés ici).

## 15:00 — image (capture terminal « HOME OF THE … ») → `incoming/`

## 22:56 — Writeup RE/pwn complet (Djo) : « bss overflow flip admin »
**Challenge** : ELF 64-bit non strippé, ET_EXEC (pas de PIE → adresses fixes). Strings :
« register your name: », « welcome, admin. », « standard users only. ». Pas de `NCTF` en clair → flag chiffré.

**Vuln (objdump -d -M intel)** — dans main :
- `user = 0x404060` (buffer .bss, taille `0x48` = 72 o)
- `[user+0x40] = 0` → drapeau « admin » à l'offset **64**, init 0
- `read(0, user, 0x80)` → lit jusqu'à **128 o** dans un buffer de 72 → **OVERFLOW**
- `test [user+0x40] != 0` : si non-nul → « welcome, admin. » + `reveal()` ; sinon refus.

**reveal()** : pour i de 0 à 0x22 (35 o) : `out[i] = enc[i] XOR 0x3c` ; `write(1,out,35)` + '\n'.

**Faille** : read 128 o dans buffer 72, drapeau admin à offset 64 → écrire **65 octets** (64 de padding +
1 non-nul sur le drapeau). Pas besoin de contrôler le retour : on écrase une globale adjacente (« bss/flip »).

**Exploit** :
```bash
python3 -c "import sys; sys.stdout.buffer.write(b'A'*72)" | ./chall
# register your name:
# welcome, admin.
# NCTF{bss_overflow_flipped_is_admin}
```
Frontière : 65 o suffisent (welcome, admin.), 64 o échouent (standard users only.).

**Décodage offline** (sans exécuter — enc à `.rodata 0x402040`, `objdump -s -j .rodata`) :
```python
enc = bytes.fromhex('727f687a475e4f4f63534a594e5a50534b635a50554c4c595863554f635d5851555241')
print(bytes(b ^ 0x3c for b in enc).decode())  # NCTF{bss_overflow_flipped_is_admin}
```
**FLAG : `NCTF{bss_overflow_flipped_is_admin}`**

## 07/11 00:09 — eval/SSTI probe
```bash
curl -s -X POST instance -H "Content-Type: application/json" -d '{"expr": "1/0"}'
```
(test d'injection d'évaluation côté serveur — division par zéro pour provoquer une erreur révélatrice.)

## 07/11 00:09 — fichier `koth_persistance.zip` (ZIP, 7 Ko, transféré) → `incoming/`

## 07/11 02:52 — Séquence KoTH / persistence (Djo)
- « envoyé moi les info », « géré ça », « géré agent_tool ….. », « lancer les gars »
- Instructions de déploiement (« ultra simple, depuis une connexion Togo ») :
  ```bash
  # récupérer le dossier deploy/ puis :
  cd deploy
  bash run_koth.sh          # laisser la fenêtre ouverte
  # si le mdp player de Citadel a changé : CITADEL_PW=lemotdepasse bash run_koth.sh ; stop = Ctrl+C
  ```
  Ce que ça fait seul :
  - Tient le **Throne** (claims en continu, ~400 threads).
  - Auto-prise de **Citadel** : dès que l'accès player revient → prend root, nettoie les concurrents,
    plante notre jeton et installe la **persistance** sur le serveur (tient même PC éteint jusqu'au reset).
  - Watchdog : relance le morceau qui tombe. Statut toutes les 20 s (qui est roi + état Citadel).
    Journaux : `throne.log`, `citadel.log`.

## Fichiers KoTH rapatriés (déjà en local depuis le 07/11) — archivés, NON exécutés
`incoming/` : koth_persistance.zip, deploy.zip, run_koth.sh, koth_Th3N00bs_kali.zip. Extraits (inventaire) dans `zip-extract/`.

### koth_persistance.zip — « Garde-Trône » (NCTF26 KoTH « Réseau Fortune »)
- `vps_hold_koth.py`, `deploy_togo.sh`, `demarrer_windows.bat`, `LISEZMOI.txt`.
- **Throne** = service HTTP (`http://13.37.197.230:28493`, aussi 28490) qui n'accepte QUE les **IP togolaises**.
  Principe : pomper des « digits » en continu (8–12 threads) pour rester #1 ; jeton équipe `ee25676dfccd6c21`.
  Hôte togolais **allumé 24/7** requis (Termux sur SIM Togo / Pi / VPS Togo) — pas de persistance serveur possible.
  Log `koth.log` : `ROI(total)=True` = on est #1. Config via env `KOTH_TOKEN/KOTH_BASE/KOTH_THREADS/KOTH_PERIOD`.

### deploy.zip — déploiement 24/7 Throne + Citadel (systemd)
- `throne_takeover.py` (tient le Throne, jeton `8f70fd11fb5bb237`), `citadel_auto.sh` (guette la réouverture SSH),
  `citadel_payload.sh` (sur **Citadel** = SSH port 28491 : root + purge concurrents + plante jeton + **persistance on-box**
  via setsid + cron/@reboot, survit même hôte éteint jusqu'au reset conteneur), `install.sh`, unités systemd, `run_koth.sh`.
- Mot de passe player Citadel paramétrable via `CITADEL_PW`.
- **Règles (du README)** : cibles autorisées uniquement (13.37.197.230 ports 28490/28491), pas de DoS, pas d'attaque
  d'autres équipes, ne jamais toucher au serveur du challenge pour le Throne.

> Reusable pour la finale (format KoTH/A&D) : (1) tenir le point de score en continu multi-thread depuis un hôte
> contraint par géo-IP tenu allumé ; (2) séparer « tenue HTTP sans persistance » vs « persistance on-box SSH qui
> survit au reboot jusqu'au reset ». Voir aussi [[nctf26-finale-ad-playbook]].

## Images non téléchargées (secondaires)
2 captures terminal (06/11 15:00 et 22:59) = screenshots du même travail RE/CTF déjà retranscrit en texte.
Dire si tu veux que je les télécharge aussi.
