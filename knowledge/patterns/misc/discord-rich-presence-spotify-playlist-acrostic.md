# Pattern — Discord rich-presence → Spotify playlist acrostic (MISC/OSINT)

**Quand :** challenge MISC/OSINT dont les hints parlent d'« écouter », de musique (`♪`, « Listen me »,
« la clé » = clé/clef), ou « What does Discord say I'm doing? » / « find me ». Format typique scène
africaine (HackerLab `HLB2026{...}`, NCTF `NCTF{...}`).

**Mécanisme :**
1. L'auteur a un **rich presence Discord** (statut « Écoute Spotify… / Playing… / custom status »).
   Trouver l'auteur sur le serveur du CTF (liste des membres) → ouvrir son **profil** → lire l'**activité**.
2. Le morceau Spotify affiché est souvent **figé** (progress bloqué) = un **pointeur vers une playlist**,
   pas le flag lui-même.
3. Ouvrir la **playlist publique** (`open.spotify.com/playlist/<id>`, aucun login requis) et lire les
   **titres dans l'ordre**. Le flag est en général un **acrostiche** = 1ʳᵉ lettre/caractère de chaque titre.
   Les accolades/chiffres du flag sont fournis par des titres choisis (`{...}` en début de titre,
   titres commençant par `0/3/...` pour le leet `0=O, 3=E, 1=I, 4=A, 5=S`).

**Pièges :**
- La liste Spotify est **virtualisée** : scroller pour charger TOUS les titres (le compteur « N titres »
  donne le total). La section **« Recommandés »** sous la playlist n'en fait PAS partie — ne pas l'inclure.
- Le rich presence Discord peut afficher une valeur **en cache** dans la liste des membres différente de
  l'activité réelle du popout → se fier au **popout de profil** (voire au DOM via read_page).
- Essayer les variantes de format si rejet : avec/sans l'année du préfixe, avec/sans underscores entre mots.

**Outillage (browser automation) :** Discord web (profil → activité), puis `open.spotify.com/playlist/<id>`
+ `get_page_text` pour extraire les titres ordonnés.

**Cas source :** [[hackerlab-welcome-back-discord-spotify-acrostic]] (HackerLab 2026 « Welcome Back »,
`HLB{W3LC0M3T0TH3DDONJOONLA}`).
