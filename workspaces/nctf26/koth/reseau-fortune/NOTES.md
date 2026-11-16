# KOTH — Réseau Fortune (http://13.37.197.230:28493)

## Mécanique du site (reconstruite depuis le JS de `/`)
- Session = cookie Flask signé (`{"code":"T002506"}`), obtenue via `/api/join {token:<jeton KotH équipe>}`.
- `/api/buy {product, qty}` -> crée une commande (débite notre propre solde), retourne `order_id`.
- `/api/refund {order_id}` -> **IDOR confirmé** : rembourse N'IMPORTE QUEL `order_id` sur NOTRE solde, sans vérifier qui a payé à l'origine. `order_id` est un compteur global séquentiel partagé par toutes les équipes.
- `/api/register {phone, parrain_code}` -> crée un "filleul" (sous-compte), retourne juste un `code` (ex. `M078503`) — **aucun cookie/session pour ce filleul** n'est renvoyé.
- `/api/bonus/activation {filleul_code}` -> prime si le filleul est "activé" (= a probablement besoin d'acheter lui-même, ce qui requiert SA PROPRE session qu'on n'a pas).
- `/api/transfer {to_code, montant}` -> transfert vers un autre code, correctement validé (montant négatif rejeté, auto-transfert no-op, solde insuffisant bloqué, destinataire inconnu 404).

## Tenté le 2026-11-06 ~22h10-22h20 (preuve directe, pas de résumé)
- `register` avec un nouveau numéro -> `{"code":"M078503","ok":true,"parrain":"T002506"}`, **pas de Set-Cookie** (vérifié via `dict(resp.headers)`), donc impossible d'agir "en tant que" ce filleul (acheter pour lui) juste avec notre cookie jar.
- Paramètres `code`/`for_code`/`as` sur `/api/buy` **ignorés** : la commande est TOUJOURS attribuée au compte de la session appelante (nous), vérifié par la baisse réelle de notre propre `wallet` (26000->24000->22000->20000 sur 3 achats test).
- `bonus/activation` sur un filleul frais -> `400 {"error":"filleul non activé"}` ; sur notre propre code -> `403 {"error":"ce n'est pas votre filleul"}`. Pas de double-encaissement trouvé (rejeté proprement).
- `transfer` : montant négatif rejeté (`400 montant invalide`), auto-transfert accepté mais no-op (solde inchangé), destinataire inconnu `404`, montant > solde `402`. **Rien d'exploitable trouvé ici.**
- **Conclusion honnête : aucune 2e faille trouvée au-delà de l'IDOR refund déjà connu.** Le filleul/parrainage semble conçu pour être activé par un VRAI second joueur avec sa propre session (hors de portée d'un script solo), pas une faille scriptable.
- 3 commandes test créées (`order_id` 19,20,21, produit "booster" 2000 FCFA chacune) puis **remboursées immédiatement par nous-mêmes** pour annuler l'effet -> `wallet` et `net_gain` restaurés à l'état initial (`wallet:26000, net_gain:-24000`), confirmé par `/api/me` avant/après. Aucun gain net laissé par ce test, juste la preuve du mécanisme.
- Le sweeper (`idor_sweeper.py`, tourne en tâche de fond) attend à la frontière réelle du compteur global (`order_id` ~19-22 au moment du check) — **ce n'est pas un bug, c'est l'état normal** : il n'y a simplement pas encore de nouvelle commande d'une autre équipe à voler. Il continuera à avancer automatiquement dès qu'une équipe adverse achète quelque chose.

## Comparaison avec Le Trône
- Pas d'endpoint `/status` équivalent exposant un compteur de "claims" massif ici (`/status` -> 404) — mécanique économique, pas une course de requêtes. Bien plus soutenable qu'une boucle de reclaim pure : 214 retournements totaux vs 476+ sur Le Trône en temps comparable, et SH4D0W tient la colline en continu depuis 21m+ (pas une guerre de débit).
- **Stratégie réaliste restante** : rien d'actionnable de plus côté script solo tant qu'aucune équipe adverse ne crée de nouvelle commande. Pas de piste supplémentaire identifiée au 2026-11-06 22h20.
