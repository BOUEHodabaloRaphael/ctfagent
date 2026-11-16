# Essai synchronisé pour The Throne

Ce script est destiné uniquement à un challenge CTF autorisé, dans les limites de son règlement. Il ne contacte aucun serveur par défaut. Le protocole de claim est repris de l'extrait fourni, sans validation en conditions réelles.

## Ce qui est corrigé

Les **0,644 s** du script initial ne sont pas un résidu mesuré : c'est la distance entre une prédiction et un bord de fenêtre d'observation. Le moment réel de l'événement n'est pas connu. La latence de l'API de classement ne calibre pas celle de `POST /throne`. La période **30,3814 s** reste une hypothèse sur peu d'événements.

La version fournie utilise une horloge monotone pour les attentes, refuse une ancre trop ancienne, ignore les créneaux manqués et ne réessaie pas une requête. Un processus réseau distinct permet d'interrompre une tentative qui dépasse son budget. Les redirections et proxys hérités sont désactivés. Le journal ne contient ni clé, ni signature, ni token, ni corps de réponse.

Les plafonds et seuils de fraîcheur sont des **choix de prudence**, pas des résultats statistiques. L'exécution est limitée par défaut à **3 tentatives / 120 secondes**, avec plafonds de **12 tentatives / 420 secondes**. L'âge maximal du modèle, 180 secondes par défaut, peut arrêter l'essai plus tôt. Un arrêt réseau peut avoir lieu après que le serveur a déjà accepté le claim ; il n'y a alors aucun retry.

## Paramètres

`--anchor` doit être un timestamp serveur récent d'un événement dont la relation au scorer est établie. Ne pas remplacer une vieille ancre par l'heure actuelle pour franchir la garde.

`--margin` est une marge expérimentale que Claude doit choisir et justifier. **2,159 s n'est pas une marge validée.** `--clock-offset-s` signifie **heure serveur moins heure locale** ; la valeur zéro suppose des horloges suffisamment synchronisées. Le décalage sert aussi au timestamp signé.

## Utilisation

Les mots en majuscules ci-dessous sont des valeurs à remplacer, pas des paramètres prêts à lancer.

```bash
python3 throne_hold_timed_safe.py \
  --anchor TIMESTAMP_SERVEUR_RECENT \
  --period 30.3814 \
  --margin MARGE_SECONDES \
  --clock-offset-s DECALAGE_SERVEUR_MOINS_LOCAL
```

Cette commande affiche un plan instantanément, sans requête réseau. Pour un essai réel, définir localement `KOTH_HILL_KEY`, `KOTH_TEAM` et `KOTH_URL`, puis ajouter `--execute`. Ne pas publier les valeurs. La clé est encodée comme du texte UTF-8, conformément au `b"..."` du script d'origine : **ne pas la décoder avec `bytes.fromhex()`**.

Le script s'arrête sur 429, autre erreur HTTP, erreur réseau, saut d'horloge ou expiration du modèle. Un HTTP 2xx ne prouve ni prise de possession ni gain de points. L'absence de Th3N00bs dans un top5 ne démontre pas un échec : le résultat reste inconnu sans compteur adéquat. Aucune vérification de score n'est automatisée ici.
