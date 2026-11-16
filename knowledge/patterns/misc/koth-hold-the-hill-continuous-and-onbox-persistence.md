# Pattern — KoTH : tenir la colline en continu + persistance on-box (jusqu'à la fin)

**Quand :** round **King-of-the-Hill** (un point de score unique que toutes les équipes se disputent en
continu ; le score = temps passé #1, ou un compteur/économie, ou un « king file » sur une box). Objectif :
**prendre et garder** la 1ʳᵉ place **du début à la fin**, même machine éteinte, même adversaire botté.

Source/template (code à adapter, PAS à rejouer tel quel — tokens/IP/clé HMAC propres au round) :
`workspaces/nctf26-finale/djo-whatsapp-2026-11-06/zip-extract/{koth_persistance,deploy}/`
(`vps_hold_koth.py`, `throne_takeover.py`, `citadel_payload.sh`, services systemd).

## D'ABORD : quel modèle de KoTH ? (détecte-le à t+0)
Deux familles, outils différents :
- **Own-the-box / own-the-file (le plus courant, dont CTFd standard)** : un **agent sur la box cible**
  reporte le propriétaire (`/status` → `{"data":{"identifier":"<équipe>"}}`) ou vérifie qui possède un
  fichier (ex. `0xThiebaut/ctfd-koth`) ; le scoreboard sonde et donne les points au propriétaire à chaque
  tick. → **Tenir = contrôler la box** : exploiter → root → planter notre id dans le king file → persister
  (la persistance tient TOUTE SEULE jusqu'au reset, aucun terminal requis). Outil : `onbox_persist.sh`.
- **HTTP-claim / éco applicative** (ex. "Réseau Fortune/Throne" NCTF préqual) : un endpoint qu'il faut
  marteler/exploiter en continu depuis un hôte allumé. → Outil : `hold_hill.py` (claim multi-thread).
Indice : si la colline pointe vers une IP:port cible (instance/VPN) = own-the-box ; si c'est un endpoint
in-platform = claim. Dans le doute, observer le trafic de la page KoTH (`recon_koth.py`).

## Dès le début du round (checklist)
1. **Identifier le canal de score** : endpoint de claim HTTP ? fichier roi sur une box SSH
   (`/koth/king`, `/king/king.txt`) ? économie à exploiter (commissions/refund) ? socket signé ?
2. **Tenir en continu, en parallèle** (un mono-thread perd contre un bot) :
   - N pompes/claims parallèles (threads/comptes distincts → ~Nx le débit), watchdog + relance auto,
     report de statut périodique (« suis-je #1 ? marge ? »).
   - Démarrer un **hôte toujours allumé** (VPS/Pi/Termux) ; `setsid nohup ... &` pour survivre à la
     fermeture du terminal ; cron `@reboot` pour survivre au reboot de l'hôte.
3. **Contrainte géo-IP** fréquente : le service n'accepte qu'une zone (ex. IP nationale) → lancer depuis
   un hôte dans cette zone (SIM nationale via Termux, Pi local, VPS local), pas depuis un VPN étranger.
4. **Si on obtient un shell sur la box de la colline** (SSH/RCE) → persistance **on-box** (survit même si
   NOTRE machine s'éteint, jusqu'au reset du conteneur) :
   - privesc (tester `sudo -n /usr/bin/env true`, SUID, etc.) → root ;
   - **purge des persistances concurrentes** (leurs cron/`/etc/cron.d/*`, binaires cachés `/usr/lib/.*`,
     `authorized_keys`, `sudoers.d`) — in-scope uniquement ;
   - **restaurer notre accès** (reset mdp player par défaut, notre clé) ;
   - **boucle de maintien** détachée qui ré-écrit le king file en boucle :
     `setsid /bin/sh /usr/lib/.hold &` + `/etc/cron.d/*` avec `* * * * *` et `@reboot` ;
   - si plusieurs scoreboards, tenir aussi les autres **depuis cette box** (son IP est déjà autorisée).

## Économie-KoTH (exploit de scoring applicatif, vu sur « Réseau Fortune »)
Si le KoTH est une appli (MLM/wallet) : chercher une boucle qui **compose** —
ex. login filleul sans OTP → achat VIP → parrain +20% commission → **refund** rend 100% au filleul
**sans reprendre la commission** → ré-injecter → le solde du parrain explose. Paralléliser sur N filleuls.

## Règles (ne jamais enfreindre)
Cibles **autorisées uniquement** ; **pas de DoS**, pas d'attaque des autres équipes ni de leur infra ;
ne pas toucher au serveur du challenge hors de ce que le scoring permet. La persistance on-box ne vise
que la box de la colline in-scope.

## Séparation clé à retenir
- **Score HTTP/claim** : AUCUNE persistance serveur → il FAUT un hôte à nous allumé 24/7 qui claim.
- **Score = king file sur box SSH** : persistance on-box (setsid + cron @reboot) → tient même nous éteints,
  jusqu'au reset. Poser les DEUX dès que possible.

Voir aussi [[nctf26-finale-ad-playbook]], [[ctf-attack-defense-tooling-reference]].
