# isid0r3--linkcard (web, ~98pts) — blackbox-exhausted

## Challenge
App "LinkCard" (partage de liens, feed + preview automatique via SSRF).
Description garbled fait reference a klouto ("tu as trouve un truc? il est
temps de creuser plus") -- suggere un lien conceptuel avec klouto (meme
pattern SSRF -> panneau admin "accessible que depuis le serveur").

## Confirme
- Register/login fonctionnels. Session Flask: `{"user_id":1}` (non chiffre,
  signe itsdangerous -- crack flask-unsign wordlist par defaut: ECHEC,
  ~56k tentatives, secret pas dans le wordlist commun).
- SSRF confirme sur /feed (POST content=<url> -> preview avec <title>
  uniquement, pas de corps complet visible).
- **Bypass de filtre SSRF trouve** : le filtre bloque la chaine litterale
  "127.0.0.1"/"localhost" mais PAS les encodages alternatifs :
  `127.1`, `0x7f000001`, `2130706433` (decimal), `0177.0.0.1` (octal),
  `127.0.0.1.` (trailing dot) -- tous atteignent le service interne (port 80,
  titre "LinkCard — Partage de liens entre amis").
- Scan de ports internes via ce bypass (3000/4000/5000/8000/8080/9000) :
  tous "no card" (rien d'autre n'ecoute, ou HTTP non reconnu).
- /admin, /internal, /debug, /secret, /flag, /dashboard, /status, /config,
  /healthz, /internal-admin via bypass IP : tous 404 (route confirmee
  inexistante, pas juste bloquee -- teste aussi en direct + X-Forwarded-For
  spoofe sur l'endpoint externe, meme resultat).
- IDOR teste (/u/<id>, /profile/<id>, /feed/<id>, /api/*) : tous 404,
  aucune route de ce type n'existe.

## Limite de l'oracle SSRF
Le preview ne montre QUE le `<title>` de la page cible, jamais le corps —
meme si on trouvait la bonne route, il faudrait que le flag soit litteralement
dans la balise <title> pour etre visible via ce vecteur seul.

## Statut
Blackbox-exhausted apres recherche approfondie (bypass SSRF reussi mais route
admin introuvable). Pas de flag. Instance pas fermee par moi (lancee par un
coequipier) -- a verifier/fermer si plus utilisee.
