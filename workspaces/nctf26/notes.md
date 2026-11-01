# NCTF26 — notes & protocole de lancement

## Mot declencheur : "NCTF"

Quand l'utilisateur tape simplement **"NCTF"** (ou une phrase contenant ce mot comme
signal de demarrage, ex. "NCTF go", "c'est NCTF") pendant la fenetre du CTF
(a partir du vendredi 2026-11-06 19:00, heure de Lome), enchainer AUTOMATIQUEMENT,
sans redemander de confirmation, dans cet ordre :

1. **Connectivite** : sourcer `src/tools/ctf/.env` (NCTF_USER/NCTF_PASS), lancer
   `python3 src/tools/ctf/nctf26_client.py login` (reutilise/renouvelle la session
   `nctf26_storage_state.json`). Si echec login -> alerter l'utilisateur
   immediatement, ne pas boucler dessus (anti-bruteforce art.7).
2. **Reprise de contexte** : relire ce fichier + `knowledge/patterns/misc/
   nctf26-platform-connexion-mecanismes.md` + l'etat du dernier round (section
   "Etat courant" ci-dessous) pour savoir ou on s'etait arrete.
3. **Debut par le JEOPARDY** (pas KotH au lancement, sauf si l'utilisateur dit
   explicitement de basculer sur KotH) : lister les challenges non resolus
   (`nctf26_client.py list`, categorie/points/solves), prioriser par
   value/solves/difficulte apparente -- profil `ctf-solver-profile`
   (evidence-first).
4. **Coordination d'equipe (5 joueurs)** : avant de lancer une instance ou de
   s'investir sur un challenge, verifier si un coequipier est deja dessus
   (page Team / activite recente / instance deja demarree visible). Si OUI
   -> NE PAS dupliquer l'effort, passer sur un autre challenge non couvert,
   MEME si cela donne moins de points individuels a l'agent. L'objectif est
   le classement d'EQUIPE (1ere place de la phase), pas le score personnel
   de l'agent.
5. **Feu vert permanent** : l'utilisateur a donne son accord pour toute la
   duree du CTF -- pas de pause de confirmation sur les actions de routine
   (probing, tentative d'exploit, script d'automatisation, UNE soumission de
   flag deja trouve et verifie). Continuer de respecter : pas de bruteforce
   de soumission, pas de depassement de rate-limit, portee strictement les
   assets NCTF26 autorises.
6. **Suivi continu** : mettre a jour la section "Etat courant" ci-dessous a
   chaque session (challenges resolus, flags soumis, instance en cours,
   coequipier croise sur quel challenge) pour qu'une reprise ulterieure (meme
   nouvelle session Claude) retrouve le contexte sans que l'utilisateur ait a
   tout re-expliquer.
7. **KotH** : une fois le jeopardy couvert (ou sur demande explicite de
   basculer), appliquer `knowledge/patterns/misc/koth-methodology-thm-validated.md`
   + `koth_auto.sh` (fichier `king`, jeton d'equipe affiche sur la page KotH,
   double points sur root boot2root, 4-5 joueurs requis presents pour scorer).

## Etat courant (a mettre a jour a chaque session)

- 2026-10-31 : session + creds valides, event pas encore ouvert
  (ouverture confirmee vendredi 2026-11-06 19:00 Lome). Aucun challenge
  jeopardy liste encore (plateforme fermee jusqu'a l'ouverture).
- 2026-11-01 : re-check connexion a la demande de l'utilisateur -- login OK
  (`nctf26_client.py login` -> redirige vers https://arena.ctf.tg/challenges,
  session sauvegardee). `list` renvoie encore la page HTML du site (pas de
  JSON challenges) -> plateforme toujours fermee, rien d'anormal, conforme a
  l'ouverture prevue vendredi 19h. Outillage (client, koth_auto.sh, creds)
  confirme pret.
- Aucun flag soumis a ce jour.
- Aucune collision coequipier observee (rien a observer avant ouverture).

## Rappels reglement / contraintes

- Art. 7 NCTF26 : pas de bruteforce de soumission, pas de depassement de
  rate-limit -- une seule soumission par flag, jamais de retry automatique.
- Instances joignables uniquement depuis le Togo (desactiver VPN
  commercial/proxy etranger avant de tester une instance).
- Service reseau = TLS obligatoire (`ncat --ssl host 1337`, SNI=host), pas de
  `nc` simple.
