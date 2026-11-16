# KoTH finale toolkit (NCTF26) — prêt à brancher

Préparé 2026-11-15 pour la finale (KoTH ouvre **jeudi 19 nov 10:00, Lomé**, sur `arena.ctf.tg`).
Tout est **paramétré par variables d'env, zéro secret en dur**. Rien ne tourne avant l'ouverture.

## Fichiers
- **`run_hold.sh`** ← **TU lances ÇA** sur ton terminal et tu laisses tourner. Watchdog intégré (relance si
  ça tombe), tient la colline jusqu'à la fin, log dans `koth.log`.
- `hill.env.example` → l'agent le copie en `hill.env` et le remplit à l'ouverture (endpoints réels).
- `recon_koth.py` → l'agent le lance à t+0 pour **découvrir** les vrais endpoints de la colline (en observant
  le trafic XHR de la page KOTH) + notre identifiant d'équipe + les IP d'instances.
- `hold_hill.py` — moteur : N threads de CLAIM en continu + poll STATUS (« suis-je roi ? »). Auth via les
  cookies de `../nctf26_storage_state.json` et/ou `KOTH_AUTH`.
- `recon_target.sh` — recon rapide d'une box (ports → versions → énum HTTP/SSH) pour accélérer la prise :
  `bash recon_target.sh <IP> [ports]`.
- `onbox_persist.sh` — persistance **on-box** si on a un shell sur la box et que le score = un « king file ».

## Déroulé à l'ouverture (jeu 19 nov 10:00)
**Moi (agent), ~2 min :**
```bash
cd src/tools/ctf/koth_finale
python3 recon_koth.py            # dump KOTH + team + instances, repère claim/status + notre team-id
cp hill.env.example hill.env     # puis je remplis KOTH_CLAIM_PATH/METHOD/BODY, KOTH_STATUS_PATH, KOTH_OUR_ID…
```
**Toi, une seule commande (et tu oublies) :**
```bash
cd src/tools/ctf/koth_finale
bash run_hold.sh                 # calibre (probe) puis tient la colline en continu ; Ctrl+C pour arrêter
tail -f koth.log                 # (optionnel) surveiller ROI(nous)=True
```
→ Le holder tourne tout seul sur ton terminal ; **toi et l'agent on se concentre sur Défense + challenges.**

**Prise de box** : `recon_target.sh <IP>` → exploiter → **root** (cheatsheet rapide :
`knowledge/patterns/misc/linux-privesc-quick-wins.md`).

**Si on prend un shell sur la box de la colline** (score = king file) → persistance qui survit au reboot :
```bash
KOTH_TOKEN=<notre_jeton> KING_FILE=/koth/king KING_FILE2=/king/king.txt bash onbox_persist.sh
```

## Notes / réalité
- Les **chemins d'API et le format de claim ne sont PAS connus** avant l'ouverture → le probe sert à les
  confirmer en 1 requête. Le squelette gère POST/GET, body JSON, cookies, header Authorization.
- Contrainte géo-IP possible (comme au préqual « IP togolaise ») → lancer depuis un hôte in-country.
- Méthode complète : `knowledge/patterns/misc/koth-hold-the-hill-continuous-and-onbox-persistence.md`.
  Template historique (préqual) : `workspaces/nctf26-finale/djo-whatsapp-2026-11-06/zip-extract/`.
- **Règles** : colline in-scope uniquement, pas de DoS, pas d'attaque des autres équipes / de l'infra orga.
