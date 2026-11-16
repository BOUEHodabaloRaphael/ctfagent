# Post-mortem d'équipe — NCTF26 (Th3N00bs)

> À remplir **après la clôture** de l'épreuve. Un post-mortem = des faits, pas des regrets.

## 1. Contexte

- **Événement** : NCTF26 (CERT.tg), jeopardy + KotH
- **Dates** : 2026-11-06 19:00 → 2026-11-0? (heure de Lomé)
- **Équipe** : Th3N00bs (5 membres : …)
- **Classement final** : …e / … équipes — **score** : …
- **Objectif annoncé** : …
- **Résultat vs objectif** : ✅ / ⚠️ / ❌ — pourquoi ?

## 2. Chiffres clés

| Indicateur | Valeur |
|---|---|
| Challenges résolus | … / 61 |
| First bloods | … |
| Points totaux | … |
| Répartition par catégorie | web … / pwn … / crypto … / forensics … / misc … / ai … / blockchain … / boot2root … |
| Temps de résolution moyen | … |

## 3. Timeline

| Heure (UTC) | Événement | Impact |
|---|---|---|
| 19:00 | Ouverture | |
| … | … | … |
| … | Clôture | |

## 4. Ce qui a bien marché

- …
- …

**À reproduire :**
- …

## 5. Challenges « presque » / points laissés sur la table

| Challenge | Catégorie | Statut | Blocage exact | Piste non testée |
|---|---|---|---|---|
| allowance-drift | blockchain | résolu (nemo, 01:14 UTC) | — | — |
| … | … | … | … | … |

## 6. Ce qui a bloqué (analyse, pas excuses)

| Problème | Cause racine | Correctif concret |
|---|---|---|
| … | … | … |
| Partage de creds / session en clair | hygiène opsec | rotation + coffre (voir §9) |

## 7. Techniques & outils réutilisables

- **Web** : …
- **Pwn** : …
- **Crypto** : …
- **Forensics** : …
- **AD / réseau** : …
- **Blockchain / EVM** : …
- **IA / LLM** : …

## 8. Writeups à produire

| Challenge | Auteur du solve | Rédacteur | Échéance | État |
|---|---|---|---|---|
| allowance-drift | nemo | … | … | ☐ |
| byte-drift | … | … | … | ☐ |
| … | … | … | … | ☐ |

Format : 1 fichier `workspaces/nctf26/writeups/<challenge>.md`, avec
contexte → analyse → exploit/PoC → flag (masqué si publication publique) → leçons.

## 9. Hygiène & sécurité (leçons opérationnelles)

- [ ] Mots de passe et cookies **jamais** dans le chat / un ticket / un paste public.
- [ ] Rotation des creds après tout partage accidentel.
- [ ] Un compte de service par usage, pas de réutilisation.
- [ ] Sauvegarde des artefacts (fichiers, tokens de challenge) avant expiration.
- [ ] Notes au fil de l'eau, pas à la fin.

## 10. Actions pour le prochain CTF

| Action | Responsable | Quand |
|---|---|---|
| … | … | … |
| … | … | … |
| … | … | … |

## 11. Ressenti d'équipe (2 lignes chacun)

- …
