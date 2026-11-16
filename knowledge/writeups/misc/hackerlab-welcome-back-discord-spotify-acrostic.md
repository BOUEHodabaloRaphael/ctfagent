# HackerLab 2026 — « Welcome Back » (MISC, 100 pts, auteur W1z4rd)

**Flag (acrostiche) :** `HLB{W3LC0M3T0TH3DDONJOONLA}` → à soumettre au format plateforme `HLB2026{W3LC0M3T0TH3DDONJOONLA}`
(statut au 2026-11-15 : dérivé, non encore confirmé accepté par la box ; variantes à tester si rejet : sans `2026`, ou avec underscores `W3LC0M3_T0_TH3_...`).

## Énoncé
- Catégorie MISC, titre « Welcome Back », sous-titre « Here we go again », sous-question « 01 Find me. »
- Hint 1 (gratuit) : « ♪ est la clé. Listen me »
- Hint 2 (gratuit) : « What does Discord say I'm doing ? »

## Chaîne de résolution
1. Les hints pointent vers le **rich presence Discord** de l'auteur (« Écoute Spotify… »).
2. Sur le serveur **HackerLab 2026** Discord → liste des membres → profil **W1z4rd** (`0xw1z4rd`,
   legacy `W1z4rd#4500`) → activité **Spotify figée** sur « 3 Fois Fesse » — *Le Grand Homme*.
   (Le morceau seul n'est pas le flag ; c'est le pointeur vers la playlist.)
3. La **playlist Spotify** liée (`open.spotify.com/playlist/3Jk2gTa7o9Fz90DKfklgjR`, « Welcome » par
   *emperor*, 27 titres) encode le flag en **acrostiche** : la **1ʳᵉ lettre de chaque titre**, dans
   l'ordre des pistes, épelle le flag. Pistes choisies exprès, y compris les accolades :
   - piste 4 `{} tradingplaces` → `{` (accolade ouvrante)
   - piste 27 `}{azy Stars` (artiste `SER}|{O`) → `}` (accolade fermante)
4. Concaténation des 27 initiales :
   `H L B { W 3 L C 0 M 3 T 0 T H 3 D D O N J O O N L A }` = `HLB{W3LC0M3T0TH3DDONJOONLA}`
   (début lisible `HLB{WELCOME TO THE…`, leet `3=E 0=O`).

## Pistes de la playlist (ordre = acrostiche)
1 Had To Leave·2 Low·3 Baba·4 {} tradingplaces·5 Wake Me Up·6 312-391·7 Lie·8 Cœur De Pirate·
9 0 To 100·10 My G·11 3 Strikes·12 TAKE·13 0·14 Thinking out Loud·15 Happier·16 3 Fois Fesse·
17 Darling·18 Dai Dai·19 On n'y va·20 Nobody·21 Jet Lag·22 On s'en ira·23 Ototo·24 Na Scra·
25 La vie qu'on mène·26 Arme de poing·27 }{azy Stars

## Leçons
- « What does Discord say I'm doing? » = **rich presence** (Spotify/jeu/custom status), pas un message.
- Un morceau Spotify figé dans la présence = souvent un **pointeur vers une playlist** ; l'ordre des
  titres (initiales) est le canal. Pattern réutilisable : [[discord-rich-presence-spotify-playlist-acrostic]].
- Outils : lire la liste des membres Discord (web), ouvrir le profil pour l'activité, puis
  `open.spotify.com/playlist/<id>` (public, pas de login) → lire les titres dans l'ordre (attention à la
  virtualisation : scroller pour charger les 27 ; la section « Recommandés » en-dessous n'en fait PAS partie).
