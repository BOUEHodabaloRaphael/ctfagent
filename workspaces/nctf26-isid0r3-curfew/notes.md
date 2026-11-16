# isid0r3--curfew (web, 100pts) — blackbox-exhausted

## Challenge
App "Curfew" (gestion de sessions/postes scolaires). JWT cookie `curfew_session`
(HS256, claims: sub, jti, iat -- pas de claim role). Dashboard affiche role
"depuis la session active associee au jeton, pas depuis le contenu du jeton".
`/admin` existe, retourne 403 pour role=user.

## Pistes testees (negatif)
- Logout ne revoque PAS reellement le token server-side (vieux cookie
  fonctionne encore apres logout) -- confirme, mais pas d'escalade trouvee
  via ce biais seul.
- Compteur de session global (jti/session# s'incremente a chaque login,
  teste jusqu'a #9) -- role reste "user", pas de seuil d'escalade observe.
- Race condition sur /register avec username="admin" existant (15 requetes
  concurrentes, TOCTOU pendant hashing mot de passe) -- mot de passe non
  ecrase, login admin/hacked123 toujours "Identifiants invalides".
- Crack du cookie Flask `session` (itsdangerous, {"captcha_answer":N}) via
  flask-unsign wordlist par defaut (~56k mots) -- echec, pas de match.
- Endpoints API devinés (/api/me, /api/sessions, /profile, /settings,
  /account, /revoke, /kick, /postes...) -- tous 404.
- Mass assignment (role=admin, is_admin=true dans /register) -- pas teste
  proprement (erreur PATH locale a corriger si repris), mais `/admin`
  reste 403 avec compte normal donc peu probable.

## Hypothese non testee
Le flavor text insiste sur "reconnexion avec privileges toujours plus
eleves" -- suggere une escalade PROGRESSIVE, pas un bypass direct. Piste
a explorer si repris : regarder si plusieurs sessions ACTIVES simultanees
(pas juste sequentielles) du MEME compte changent le comportement, ou si
un parametre cache existe sur /login (ex: ?remember=1, ?device=).

Statut : blackbox-exhausted apres ~3 rounds sans fait nouveau. Instance
fermee. Pas de flag trouve.
