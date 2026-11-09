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
   nctf26-platform-connexion-mecanismes.md` + `prep-ceh-africc-cheatsheet.md` (ce workspace --
   techniques offensives condensees CEHv13+AFRICC par categorie, scan/enum/web/sqli/crypto/
   system hacking) + `prep-arsenal-2026-11-06.md` (routage categorie -> skill profond,
   quickstart RE, etat des outils) + l'etat du dernier round (section "Etat courant"
   ci-dessous) pour savoir ou on s'etait arrete.
3. **Debut par le JEOPARDY** (pas KotH au lancement, sauf si l'utilisateur dit
   explicitement de basculer sur KotH) : lister les challenges non resolus
   (`nctf26_client.py list`, categorie/points/solves), prioriser par
   value/solves/difficulte apparente -- profil `ctf-solver-profile`
   (evidence-first). Une fois la categorie d'un challenge confirmee (web/pwn/
   rev/crypto/system), le routeur de categorie (`web-triage`/`pwn-triage`/
   `rev-triage`/`category-switches.md`) pointe automatiquement vers le fichier
   `knowledge/ceh/mXX-*.md` et/ou `prep-ceh-africc-cheatsheet.md` pertinent --
   le consulter avant d'improviser un payload.
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
- 2026-11-02 : simple check de connectivite (rien d'autre) -- login OK
  (`nctf26_client.py login` -> redirige vers https://arena.ctf.tg/challenges,
  session renouvelee). `list` renvoie encore la page HTML du site (balises
  `<!DOCTYPE html><html lang="fr">...<title>NCTF26</title>`, pas de JSON
  challenges) -> plateforme toujours fermee, rien d'anormal, conforme a
  l'ouverture prevue vendredi 2026-11-06 19h00 Lome. Aucune autre action
  effectuee (pas de soumission, pas de bruteforce, pas de scan).
- 2026-11-02 (suite) : exploration passive "coulisses" demandee par
  l'utilisateur (lecture seule, 1 requete par chemin, espacees ~2-2.5s,
  reutilisation de la session Playwright deja sauvegardee -- pas de
  re-login, pas de .env lu, pas de soumission, pas de scan). Resultats :
  - `/challenges` repond en fait **HTTP 403** (confirme via le log reseau
    de la page, pas juste "page HTML du site" comme note precedemment) et
    sert une page theme "terminal" : `nctf@arena:~$ contrôle d'acces 403
    $ access /challenges [deny] acces refuse NCTF26 has not started yet`
    + un **countdown JS en direct** affiche deux fois ("ouverture dans
    4j 03:14:00" puis "...03:09:54" entre les requetes) -- coherent avec
    l'ouverture vendredi 2026-11-06 19h00 Lome depuis le 2026-11-02 ~15h45.
  - `/api/v1/challenges` -> **403 JSON explicite** `{"message": "NCTF26
    has not started yet"}` (gate cote plateforme, pas une 404 generique).
  - `/api/challenges` -> 404 (route inexistante, seul `/api/v1/...` existe).
  - `/robots.txt` -> 200, `Disallow: /admin` (panneau admin existe, PAS
    visite -- hors perimetre de l'observation passive, volontairement pas
    sonde).
  - `/rules`, `/sitemap.xml` -> 404 (n'existent pas).
  - XHR JS déclenchés par la page `/challenges` elle-meme (observes, pas
    des requetes en plus) : `/plugins/firstblood/api/recent` ->
    `{"data":[],"frozen":false,"success":true}` (aucun first blood) ;
    `/plugins/admin_messages/inbox` -> `{"data":[],"success":true}`
    (aucun message/annonce organisateur) ; `/plugins/release/api/next` ->
    `{"countdown":true,"enabled":false}` (plugin "release"/teaser present
    mais desactive -- rien a debloquer cote client).
  - `/`, `/login`, `/team`, `/scoreboard`, `/teams`, `/users`,
    `/plugins/support/`, `/plugins/writeups/`, `/plugins/defi_gate/` ->
    tous **200**, non gates (seule la liste de challenges elle-meme est
    bloquee avant ouverture).
  - **Page `/team` (notre equipe)** : roster confirme -- equipe
    **"Th3N00bs"**, 5/5 joueurs presents : `Sy5t3mc4ll` (Captain),
    `ryuк`, `nemo`, `d0tn3t`, `12_nad0` -- tous a 0 point, "No solves
    yet". Formulaire d'edition equipe (nom/mdp/site/affiliation/pays)
    deja utilisable avant ouverture.
  - **Page `/scoreboard`** : theme "Grand Prix NCTF" (grille de course),
    bandeau explicite "scores geles jusqu'a la fin de l'epreuve", countdown
    "DEPART DANS 4j 03:11:29", "Aucun score pour le moment".
  - **Pages `/teams` et `/users`** : annuaires publics deja visibles avant
    ouverture -- dizaines d'equipes concurrentes listees (FireTeam,
    Win_cyber, SH4D0W, VortexSec, RootForce, Th3N00bs, etc.) et liste
    joueurs correspondante -- donne une idee de la taille du champ avant
    le debut, aucun score nulle part.
  - **Nouveau decouvert, pas encore documente avant** : plugin
    `/plugins/defi_gate/` ("Défi" dans le nav, distinct de "Challenges")
    -- affiche "Défi #1 -- Le defi n'est pas actif pour le moment". A
    surveiller : mecanique de teaser/pre-challenge separee du jeopardy
    principal, pourrait s'activer avant le 2026-11-06 19h.
  - `/plugins/writeups/` confirme : writeups pas publies, disponibles
    seulement apres cloture de l'epreuve (comportement normal).
  - `/plugins/support/` : simple formulaire de contact/ticket support,
    rien de special.
  - Conclusion : **rien d'exploitable ou d'anormal** -- la plateforme est
    cohérente avec un etat "pas encore ouvert", mais plusieurs pages
    annexes (team roster, scoreboard, teams/users, defi_gate, writeups,
    support) sont deja navigables en lecture et donnent du contexte utile
    (effectif equipe complet, taille du champ, mecanique "Défi" a
    surveiller) avant vendredi.
- 2026-11-03 : tour complet demande par l'utilisateur, focus acces/permissions
  et distinction "Challenges" vs "Défi #1". Reutilisation stricte de la
  session Playwright sauvegardee (pas de re-login), 1 requete par chemin,
  delai ~2.3s, aucune soumission/bruteforce/scan. Resultats :
  - **Page d'accueil `/` enfin lisible en entier** (contenu jamais capture
    avant en detail) : "Présélection en ligne du 6 au 7 novembre (~29h,
    non-stop), finale a Lome les 19-20 novembre. Format des flags :
    NCTF{...}." Chiffres annonces : **370 épreuves, 21 catégories, 300+
    joueurs attendus, 10 équipes en finale**. Categories listees : web,
    pwn, reverse, crypto, forensics, blockchain, cloud, ai/ml, osint,
    "+10 autres".
  - **Nav bar complete confirmee via DOM** : Accès (`/connexion`), Défi
    (`/plugins/defi_gate/`), **KOTH (`/plugins/koth/`) -- lien jamais
    documente avant**, Support, Writeups, Users, Teams, Scoreboard,
    Challenges (`/challenges`), Notifications, Team, Profile, Settings,
    logout.
  - **`/plugins/koth/` (nouveau)** : page "👑 KING OF THE HILL" avec son
    propre countdown, texte explicite **"LES COLLINES OUVRENT AVEC
    L'ÉPREUVE"** + "Ouverture le vendredi 6 novembre à 19:00 (heure de
    Lomé)." + "Les points de King of the Hill s'ajoutent à votre score sur
    le scoreboard principal, tick après tick, tant que vous tenez la
    colline." -> KotH = un MODE DE JEU additionnel au meme jeopardy/meme
    scoreboard, explicitement synchronise sur l'ouverture principale.
  - **`/plugins/defi_gate/` revisite en detail** : contenu TRES minimal,
    inchange depuis le 2026-11-02 -- uniquement "DÉFI #1 / Le défi n'est
    pas actif pour le moment." + le countdown generique du site (identique
    a celui affiche partout ailleurs, pas un countdown propre a Défi).
    Aucune regle, aucune date d'activation propre, aucun format annonce
    (jeopardy single/battle royale/quiz : indetermine), aucune reference a
    un "Défi #2" ou liste de défis. **Contrairement a KOTH, aucune phrase
    n'indique que Défi "s'ouvre avec l'épreuve"** -- absence notable.
  - Pas de page de reglement separee trouvee : `/rules`, `/info`, `/about`,
    `/faq` -> tous **404** (meme page terminal-theme generique
    "ressource introuvable").
  - Aucun message de permission/role different observe sur `/plugins/
    defi_gate/` (page accessible a tout membre connecte, meme etat pour
    tous -- pas de message "equipe incomplete" ou "capitaine seulement").
    Seul etat visible = "pas actif pour le moment", identique a l'etat
    "ferme" des autres sections avant ouverture.
  - `/plugins/support/` et `/plugins/writeups/` : rien de nouveau vs
    2026-11-02, aucune mention de "phases" nommees differemment.

  ### Distinction Challenges vs Défi #1 -- ce qui est confirme vs hypothese
  - **Confirme** : "Challenges" = le jeopardy principal (370 épreuves /
    21 catégories), gate par le countdown global, ouverture vendredi
    2026-11-06 19h00 (debut de la "présélection en ligne" 6-7 nov, ~29h).
  - **Confirme** : "KOTH" = mode de jeu supplementaire au MEME evenement,
    points ajoutes au meme scoreboard, ouverture explicitement
    synchronisee avec l'épreuve (meme heure, texte on-page qui le dit).
  - **Confirme** : "Défi" est un bouton de nav SEPARE et DISTINCT de
    "Challenges", avec sa propre route plugin (`defi_gate`), actuellement
    inactif, contenu minimal, pas de phrase de synchronisation avec
    l'ouverture principale (a la difference de KOTH).
  - **Hypothese, non confirmee** : le plugin "release" (vu le 2026-11-02,
    `/plugins/release/api/next` -> `{"countdown":true,"enabled":false}`,
    teaser/countdown present mais desactive cote client) pourrait etre le
    mecanisme destine a activer Défi independamment de l'ouverture
    principale du vendredi (mini-challenge teaser pre-event). Aucune
    preuve directe -- seulement coherent avec l'absence de synchronisation
    textuelle vue sur KOTH.
  - **Reste ambigu / non tranche** : format exact de Défi (jeopardy a
    challenge unique, battle royale, quiz ?), nombre total de "Défis"
    prevus (seul #1 existe/visible, aucune reference a #2+), et condition
    d'acces/permission eventuelle (aucune difference de permission
    observee pour l'instant -- peut-etre parce que le plugin est
    simplement inactif pour tout le monde, donc rien a distinguer encore).
- 2026-11-03 (suite) : question explicite de l'utilisateur -- "faut-il
  installer quelque chose pour se connecter ?". Lecture passive de
  `/connexion` (jamais explorée en detail avant), `/profile`, `/settings`,
  `/support` et `/writeups` (routes racine, distinctes de `/plugins/
  support/` et `/plugins/writeups/` deja documentees -- celles-ci renvoient
  une page "la page n'existe pas, ou l'épreuve n'est pas encore ouverte",
  pas un vrai support/writeups public). Session Playwright reutilisee
  (`nctf26_storage_state.json`), pas de re-login, 1 requete/page, delai
  ~2.5s, rien soumis. Resultats -- **`/connexion` repond a la question
  en detail, page "SE CONNECTER AUX INSTANCES" avec 3 cas** :
  1. **Challenge web (instance `https://xxxx.t.ctf.tg/`)** : rien a
     installer, juste le navigateur.
  2. **Service reseau (pwn/crypto, `ncat --ssl host 1337`)** : TLS
     obligatoire, port 1337 fixe. Outil recommande = `ncat` (paquet nmap,
     Linux/macOS a installer, fourni avec l'installeur Nmap sous Windows).
     Alternatives explicitement citees si pas de ncat : `openssl s_client
     -quiet -connect host:1337 -servername host` ou pwntools
     `remote(host, 1337, ssl=True, sni=host)`. **Verifie cote agent** :
     `ncat` installe le 2026-11-03 (`sudo apt install ncat`, version 7.991,
     teste `ncat --version` OK) ; `openssl` et `pwntools` (module `pwn`
     importable) deja fonctionnels en fallback. Les 3 methodes citees par
     la plateforme sont desormais disponibles.
  3. **VPN d'equipe (boot2root / admin systeme / multi-ports, reseau prive
     10.100.x.y)** : necessite le client **WireGuard**
     (wireguard.com/install), + un fichier de config personnel
     `nctf-vpn.conf` a telecharger depuis une "page VPN" (bouton
     "Telecharger ma configuration", **un par joueur**, re-telecharger
     annule l'ancien) -- cette page VPN semble liee a un challenge/instance
     specifique (lien pas dans la nav globale), donc **pas encore
     accessible/visitee** (rien a instancier avant ouverture vendredi).
     **Verifie cote agent** : `wg` et `wg-quick` (paquet `wireguard-tools`)
     sont **deja installes** -- pret a importer la config le jour J, il ne
     restera qu'a telecharger le `.conf` personnel une fois un challenge
     a VPN lance.
  - **KOTH ne necessite ni VPN ni installation** : adresses publiques
    directes (web `http://...:port` ou `ssh -p port player@host`),
    confirme sur `/connexion` (coherent avec `/plugins/koth/` deja note).
  - **Precision importante sur "joignable uniquement depuis le Togo"** :
    ce n'est **pas** un VPN fourni par les organisateurs pour acceder
    depuis l'etranger -- c'est l'inverse : "Desactivez tout VPN commercial
    ou proxy etranger" (le filtrage geo veut une IP togolaise native, pas
    un tunnel organisateur). Le seul VPN fourni par la plateforme est le
    WireGuard d'equipe ci-dessus, pour acceder au **sous-reseau prive de
    l'equipe** une fois une instance VPN lancee -- deux choses distinctes.
  - `/profile` et `/settings` : rien d'installation/VPN -- formulaires
    standards (profil equipe/joueur, preferences compte). Aucune
    identifiant VPN pre-rempli ou lien direct vers la page VPN visible
    hors contexte d'un challenge instancie.
  - Conclusion : **rien a installer pour l'instant dans l'absolu** (event
    pas ouvert, aucune instance lancee) ; **cote outillage agent, tout est
    deja pret pour le jour J** sauf `ncat` (facultatif, fallback deja
    fonctionnels dispo) -- `wg`/`wg-quick` presents, `openssl`/`pwntools`
    presents. Seule action potentielle a prevoir vendredi : telecharger le
    `nctf-vpn.conf` personnel depuis la page VPN (visible seulement via un
    challenge a instance VPN) et `wg-quick up` dessus.

- 2026-11-03 (dernier check avant cloture prepa) : check de routine demande par
  l'utilisateur -- login + 2 pages revisitees, rien d'autre. Session
  Playwright reutilisee (pas de .env relu manuellement pour le navigateur,
  `nctf26_client.py login` a bien source `.env`), 1 requete par chemin,
  delai ~2.3s, aucune soumission/bruteforce/scan. Resultats : **rien n'a
  change**.
  - `nctf26_client.py login` -> OK, redirige vers
    `https://arena.ctf.tg/challenges`, session renouvelee.
  - `/plugins/defi_gate/` -> toujours **"DÉFI #1 / Le défi n'est pas actif
    pour le moment."**, countdown generique affiche "ouverture dans 3j
    11:20:50" (coherent avec vendredi 19h -- juste le temps qui avance,
    rien d'anormal).
  - `/challenges` -> toujours **HTTP 403** avec la meme page terminal
    "nctf@arena:~$ ... [deny] acces refuse NCTF26 has not started yet",
    countdown "3j 11:20:47" (meme etat, meme phrase qu'avant).
  - Conclusion : plateforme toujours fermee comme attendu, pas de
    changement a signaler avant l'ouverture de vendredi 2026-11-06 19h00
    Lome.

- 2026-11-06 (prépa arsenal) : intégration massive de skills/RE avant ouverture.
  - `.claude/skills/` : ajout de `ctf-reverse`, `ctf-pwn`, `ctf-web`, `ctf-crypto`,
    `ctf-forensics`, `ctf-misc`, `ctf-malware`, `ctf-osint`, `ctf-ai-ml`,
    `solve-challenge`, `ctf-writeup`, `ctf-similar-search`, `reverse-engineering`,
    `reverse-skill-router`, `r2-reverse`, `ctf-evidence`.
  - `knowledge/external/` : `reverse-skill` (45+ modules), `reverse-skills-p4nda0s`,
    `neurosploit/techniques` (486 fiches), `ctf-arsenal` (commandes/agents),
    `security-skills`, `hacking-skills`, `pwn-htb`, `android-reverse-engineering` ;
    catalogue `knowledge/external/INDEX.md`.
  - Outils installés : `frida`, `vol` (Volatility 3), `capa`, `floss`, `lief`,
    `apktool`, `jq`, `foremost`, `qemu-user-static`, `ltrace`, `unblob`, `cfr`.
    Ghidra 11.4.3 headless via docker (`src/tools/rev/ghidra_headless.sh`, testé OK).
  - Quickstart et tableau de routage : `workspaces/nctf26/prep-arsenal-2026-11-06.md`.
  - Limites connues : `ropper`/`one_gadget` absents (utiliser `ROPgadget`/pwntools) ;
    pas d'IDA/Binja/x64dbg ; MCP `ctf/r2mcp/cyberchef` indisponibles → CLI.
- 2026-11-06 (session prépa finale, matin, ~05h57-06h00 Lomé) : enchaînement
  complet demandé par l'utilisateur — recon externe, fusion skills, vérif
  VPN, vérification finale, revue anti-doublon de l'arsenal. Résultats :
  - **Recon GitHub (2 repos)** : `JoasASantos/NeuroSploit` (commit `92e8959`,
    MIT, rien d'exécuté) exploité → 11 fiches curatées copiées dans
    `knowledge/external/neurosploit/{meta,rev,web}/` et fusionnées dans
    `web-triage` (nouvelle réf `xxe.md` + pointeurs JWT/SSTI/SSRF/deser) et
    `rev-triage` (pointeurs triage binaire statique + obfuscation). Commit
    `733d1b6`. `Durrell-229/hunter-bridge` (commit `f958d2b`) analysé en
    détail et **écarté** : proxy Claude Code vers clés API tierces + tunnel
    public Cloudflare/Chisel exposant le VPN équipe à "n'importe quelle IA
    distante" + stockage du mot de passe sudo en clair — incompatible avec
    l'art. VPN équipe du règlement. Rien copié de ce repo sur le moment.
  - **Arsenal élargi** (commit `83bc501`, fait en parallèle/hors de cette
    session de chat) : 16 skills (`ctf-reverse/-pwn/-web/-crypto/-forensics/
    -misc/-malware/-osint/-ai-ml`, `solve-challenge`, `ctf-writeup`,
    `ctf-similar-search`, `reverse-engineering` [plugin], `reverse-skill-router`,
    `r2-reverse`, `ctf-evidence`) + 8 bibliothèques externes dans
    `knowledge/external/` (voir `INDEX.md` pour provenance/licences). Révision
    anti-doublon faite à la demande de l'utilisateur :
    - `ctf-arsenal/` (ré-import partiel de `hunter-bridge`) vérifié ligne par
      ligne — seulement `agents/*.md`+`commands/*.md`+`plugin.json`, grep
      négatif sur `sudo|chisel|cloudflare|vpn|wireguard|colab` : le risque
      identifié plus haut n'a PAS été réintroduit, seuls les playbooks texte
      ont été repris. `web-triage`/`pwn-triage` notent explicitement d'utiliser
      les équivalents CLI (pas les MCP `ctf`/`r2mcp` absents).
    - `neurosploit/techniques/` (486 fiches brutes) coexiste sans conflit avec
      notre sous-ensemble curaté `meta/rev/web` (redondance de stockage
      inoffensive, pas de contradiction de contenu).
    - Plusieurs bibliothèques RE en parallèle (`reverse-skill/`,
      `reverse-skills-p4nda0s/`, `security-skills/reverse-engineering/`,
      plugin `reverse-engineering`, skill `ctf-reverse`) : pas contradictoires,
      ordonnées par la table de routage de `prep-arsenal-2026-11-06.md` et la
      section "Deep Playbooks" de `rev-triage`/`web-triage`/`pwn-triage`.
    - Conclusion : aucune action corrective nécessaire, arsenal cohérent.
  - **Vérification réseau/VPN** : aucun VPN actif (process/interface/
    NetworkManager), pas de proxy env, IP publique `102.64.168.122`
    géolocalisée Lomé/TG (AS GVA Côte d'Ivoire) — rien à désactiver, pas de
    risque de filtrage géo.
  - **Vérification finale complète** : login OK (session renouvelée),
    `/challenges` toujours 403 "has not started yet" (normal, ~13h avant
    ouverture au moment du check), outillage réseau complet (`ncat 7.991`,
    `openssl`, `pwntools`, `wg`/`wg-quick`), `koth_auto.sh` et
    `parallel_dispatch.py` présents, repo propre.
  - Plugin marketplace Claude Code passé en revue (3922 plugins scannés par
    mots-clés ctf/rev/pwn/ghidra/radare/crackme) : très peu de hits réels ;
    `reverse-engineering@anthropic-plugin-directory` installé (seul candidat
    pertinent trouvé côté marketplace officiel).
  - Page `docsbot.ai/prompts/technical/ctf-reverse-engineering-script` lue
    par un agent : template de prompt marketing générique, aucun contenu
    technique absent de notre `rev-triage` — ignoré, rien fusionné.
- Aucun flag soumis a ce jour.
- Aucune collision coequipier observee (rien a observer avant ouverture).

## Rappels reglement / contraintes

- Art. 7 NCTF26 : pas de bruteforce de soumission, pas de depassement de
  rate-limit -- une seule soumission par flag, jamais de retry automatique.
- Instances joignables uniquement depuis le Togo (desactiver VPN
  commercial/proxy etranger avant de tester une instance).
- Service reseau = TLS obligatoire (`ncat --ssl host 1337`, SNI=host), pas de
  `nc` simple.

## KOTH session 2026-11-06 19:4x — Armory + Citadel (Th3N00bs)

- Armory (13.37.197.230:28492) : nc direct AVANT tout scan -> banniere SSH OK
  ("SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.17"). Puis `koth_auto.sh` phase1 a
  lance un nmap -p- complet -> resultat: SEULEMENT 22/tcp et 443/tcp "open",
  28492 absent du scan. Verif immediate post-scan: nc vers 28492 ->
  "Connection timed out" (avant c'etait instantane). **Le scan -p- a
  lui-meme declenche le blocage du port de service reel**, meme pattern que
  la cooldown HTB Pro Lab deja en memoire (full-port-scan -> blocage
  temporaire 20-30min, independant de l'IP). LECON AJOUTEE : sur
  l'infra NCTF26 KOTH, NE PAS lancer nmap -p- sur les ports connus du
  challenge -- scanner une liste ciblee (ports annonces + quelques communs)
  avec un rate doux, jamais -p- agressif en min-rate 3000.
- Citadel (13.37.197.230:28491) : port verifie toujours reactif juste apres
  l'incident Armory (banniere SSH immediate). Decision : AUCUN scan -p- sur
  Citadel, uniquement sondage cible sur ports precis.

### Conclusion session KOTH 2026-11-06 19:4x-19:5x (Citadel + Armory)

- Aucun acces SSH obtenu sur Citadel (28491) ni Armory (28492). Methodes
  permises testees et toutes rejetees proprement : `PreferredAuthentications=none`
  -> "Permission denied (publickey,password)" (aucun hint, pas de
  keyboard-interactive) ; mot de passe vide (`sshpass -p ''`) -> meme refus ;
  aucune cle par defaut disponible dans le repo/plateforme ; bannière/motd
  pre-auth vide (verbose ssh -vvv, pas de texte additionnel).
- Armory : `Exceeded MaxStartups` observe 2x sur les tentatives de handshake
  -> contention reelle d'autres equipes (204 "retournements" vus sur le
  board, tres dispute), pas un symptome cote nous.
- Aucun port colocalise trouve au-dela de 22/443 (ports plateforme, cert
  CloudFlare Origin -> hors scope, probablement l'infra arena.ctf.tg
  elle-meme partagee sur la meme IP) et des ports specifiques (28005,
  28065, 28268, 28304, 28468, 28483 -- closed, probablement d'autres
  collines/equipes) vus lors du scan complet initial.
- Pas de source/attachment jeopardy pour Citadel/Armory (verifie via
  /challenges -- aucune occurrence "citadel"/"armory"/"hill").
- Pas de distribution de cle SSH trouvee sur la page /plugins/koth/ (pas de
  bouton telechargement, pas de reference .pem/id_rsa/pubkey dans le HTML/JS).
- IMPASSE DOCUMENTEE : blackbox SSH-only exhausted sans bruteforce. Pistes
  restantes NON explorees (hors scope agent, necessitent action humaine) :
  canaux Discord/WhatsApp officiels (hints organisateurs possibles),
  ou attente d'une fuite de creds via un autre vecteur a identifier plus tard.
- Standings a la fin de session : Citadel tenu par B4r0qu3_W0rk5 (regne
  52m45s), Armory tenu par Hello_World!!! (regne 7m15s). Th3N00bs toujours
  a 0 sur Citadel. Aucune boucle --holdking lancee (aucun acces).

## KOTH session 2026-11-06 ~22h00-22h20 — Throne + Reseau Fortune relances, agent boot2root Bassar en parallele

- `throne_hold.py` (exploit HMAC deja prouve, voir `koth/throne/EXPLOIT.md`)
  et `idor_sweeper.py` (IDOR refund, voir `koth/reseau-fortune/NOTES.md`)
  relances en tache de fond (nohup, rythme modere, pas de flood).
- **Decouverte importante (preuve directe) : Le Trone n'est PAS gagnable a
  notre rythme actuel.** Nouvel endpoint `GET /status` (non gate) revele
  **35+ millions de claims totaux** sur cette colline -- nos ~634 claims
  reussis (200/ok confirme) en 15min n'apparaissent dans AUCUN top5 ni le
  fil d'activite plateforme. L'exploit est prouve/fonctionnel mais hors
  de portee sans un debit largement superieur (territoire flood, deja
  bloque une fois par le garde-fou anti-flood de l'environnement sur une
  version multi-threadee -- pas retente sans clarification humaine).
  Script laisse tourner (cout nul, capture opportuniste), mais plus
  presente comme strategie gagnante.
- **Reseau Fortune** : exploration complete de la surface API
  (register/bonus/transfer) -- **aucune 2e faille trouvee**, tout
  correctement valide cote serveur sauf le refund IDOR deja connu. Le
  parrainage/filleul necessite une vraie session de second joueur
  (hors de portee scriptable solo). Sweeper correctement a l'etat
  d'attente (frontiere du compteur global d'order_id, pas un bug) --
  attend simplement qu'une equipe adverse achete quelque chose. 3
  commandes test creees puis remboursees par nous-memes pour verifier le
  mecanisme, effet net nul (etat restaure, verifie via `/api/me`
  avant/apres).
- **Agent sous-traite en parallele** sur un boot2root DISTINCT :
  `komisergio-bassar` (10.100.16.100:9999, pwn/stack overflow, script
  fourni par l'utilisateur), workspace
  `workspaces/komisergio-bassar-boot2root-pwn/` -- NE PAS confondre avec
  `nctf26-komisergio-kpalime` (AD/ADCS, 10.10.20.30, bloque reseau,
  challenge different du meme createur). Statut agent : en cours au
  moment de cette note.

## KOTH tour complet 2026-11-07 ~01h25 — verification etat, aucune nouvelle tentative

Lecture en un appel de `GET /plugins/koth/api/state` (cookies session reutilises,
pas de re-login) + sondes ciblees. Conclusion : **aucun changement de fond**,
toutes les impasses deja documentees restent valides.

- **The Throne** : roi `Hello_World!!!`, regne 7s, 718 takeovers (board tourne
  en boucle de prises <10s, toujours le pattern deja connu). `throne_hold.py`
  (PID 165224) tourne en continu depuis 3h05 sans interruption -- claims
  intermittents reussis (`king=b792a5aa...` = notre token observe dans son
  propre log), mais jamais assez pour tenir face a la contention. Verif
  directe `GET /status` x2 espacees de 6.3s : claims 51642519 -> 51654014,
  soit **~1836 req/s** de trafic adverse cumule -- dans la fourchette
  1000-3000 req/s deja etablie, **PAS de baisse de contention**. Total
  claims maintenant 51.6M (contre 35M+ note le 06/11), donc la colline est
  MEME PLUS disputee qu'avant, pas moins. Conclusion "non gagnable a notre
  rythme" reconfirmee, aucun flood tente.
- **The Citadel** (28491) : roi `Unkn0wn`, regne 9855s (~2h44), seulement 9
  takeovers -- colline stable, peu disputee en ce moment, mais toujours 0
  acces pour Th3N00bs (absent du top5 : B4r0qu3_W0rk5 2120, Unkn0wn 1700,
  Fuller 120, z3n_ 60, Gh0st Pr0t0c0l 5). Sonde cible (nmap -sV, 1 port,
  pas de -p-) : banniere SSH identique a avant (`OpenSSH 8.9p1 Ubuntu
  3ubuntu0.17`), rien de nouveau. Pas de tentative d'acces (impasse
  SSH-only toujours valide).
- **The Armory** (28492) : roi `Hello_World!!!`, regne 68s, 435 takeovers
  (tres disputee, comme Throne). Sonde ciblee -> reponse `Exceeded
  MaxStartups` (confirmee stable sur 2 sondes espacees de 3s) -- **meme
  symptome que le 06/11** (deja note x2), confirme a nouveau : flood SSH
  d'equipes adverses sur le port de service, pas un signal cote nous. Aucun
  acces. Th3N00bs a neanmoins 2 pts au board (`score:2`, 5e du top5) --
  residu d'un gain anterieur (pas nouveau, pas d'action a prendre).
- **Reseau Fortune** : roi `SH4D0W`, regne 10189s (~2h50), 214 takeovers.
  `idor_sweeper.py` (PID 167030) tourne en continu depuis 3h03, **aucun
  redemarrage necessaire**. Etat du wallet stagnant a 25800 (net_gain
  -24200) depuis ~sweep 101 jusqu'a sweep 594 (pres de 500 cycles sans
  variation) -- deux dips transitoires a 20000/21000 en debut de run deja
  corriges. Les order_id continuent de progresser (1124 -> 1185 observes
  pendant la verif) donc le sweeper est actif et voit du trafic, mais
  aucune commande fraiche adverse exploitable recemment (quelques timeouts
  `urlopen error timed out` ponctuels, pas un echec systemique). Th3N00bs
  toujours absent du top5 (SH4D0W 1986, z3n_ 633, hum 492, Fuller 450,
  B4r0qu3_W0rk5 78).

**Aucune opportunite nouvelle trouvee.** Rien a signaler au-dela de la
reconfirmation des impasses/strategies deja en place. Les deux scripts de
fond (`throne_hold.py`, `idor_sweeper.py`) etaient deja actifs, aucun
redemarrage necessaire cette fois.

## Verification connectivite 2026-11-09 17h20 — blocage Cloudflare WAF (pas un gate plateforme)

Check demande par l'utilisateur apres confirmation de qualification en
**finale** (presentiel Lome, 19-20 novembre). Resultat : **la plateforme
bloque toutes les requetes depuis cet environnement**, y compris les pages
publiques non gatees auparavant.

- `curl -sI https://arena.ctf.tg/login` -> **HTTP 403**, page Cloudflare
  "Attention Required! / you have been blocked" (`server: cloudflare`,
  `cf-ray: a57e7cebf97ff8f6-SIN`) -- **different** du 403 JSON
  `"NCTF26 has not started yet"` deja documente le 2026-11-02 (celui-ci
  etait un gate applicatif explicite ; celui du jour est un blocage WAF
  Cloudflare generique sans message plateforme).
- Memes 403 sur `/`, `/challenges`, `/scoreboard`, `/api/v1/challenges`
  (avant, ces pages publiques repondaient 200 meme plateforme fermee).
- Connectivite generale de la machine confirmee normale en parallele
  (`curl https://www.google.com` -> 200), donc pas un probleme reseau local.
- `nctf26_client.py login` echoue avec `Champ nonce introuvable` -- cause
  confirmee : Playwright recoit la meme page de blocage Cloudflare (verifie
  avec et sans le contournement DNS `--host-resolver-rules` deja present
  dans le script -- aucun effet, le blocage n'est pas DNS).
- Pas de tentative de contournement (rotation IP/proxy, user-agent spoof,
  etc.) -- hors perimetre agent, et risque de violer le reglement anti-abus
  de la plateforme pendant une phase sensible (entre-deux presequalif/finale).
- **Hypothese la plus probable** : rate-limit/blocage global cote
  Cloudflare apres la cloture de la phase de preselection (2026-11-06/07),
  possiblement lie a la reputation de l'IP sortante de cet environnement,
  pas specifique a notre equipe.
- **Action recommandee (humaine)** : retester depuis un autre reseau/IP
  (poste perso, VPN equipe) avant la finale du 19-20 novembre pour confirmer
  si c'est global ou local a cet environnement.
