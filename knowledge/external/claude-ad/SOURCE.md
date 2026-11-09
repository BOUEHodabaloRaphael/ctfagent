# Source: Claude-AD (ADScanPro)

- URL du dépôt : https://github.com/ADScanPro/Claude-AD.git
- Commit cloné : `73efec51207f6f740cb398e1c490e5edd60c1113` (branche par défaut)
- Date du commit : 2026-08-24
- Clone effectué le 2026-11-09, via un agent de recherche dédié puis import manuel
  (clone temporaire hors repo principal, non committé, dans le scratchpad de session)
- Méthode de récupération : `git clone --depth 1` en lecture seule. Aucun script exécuté
  (le dépôt n'en contient de toute façon pas — uniquement Markdown/JSON).

## Licence

MIT License, Copyright (c) 2026 ADscan. Pas de restriction de réutilisation/modification
tant que la notice de copyright et la permission sont conservées.

## Pourquoi cet import

Suite à des blocages répétés sur des challenges **boot2root** impliquant une chaîne
Active Directory complète (ASREP-roast → abus ACL → ADCS ESC1 (SAN libre) → certificat
Domain Admin ; DCSync via impacket contre un DC Samba — voir
`workspaces/nctf26-adzogbo/notes.md`, `workspaces/nctf26-komisergio-kpalime/notes.md`),
une recherche GitHub ciblée (agent dédié, 2026-11-09) a identifié ce dépôt comme le plus
pertinent : c'est un plugin Claude Code **packagé exactement comme nos propres skills**
(dossiers `skills/` avec `SKILL.md`, plus `agents/` et `commands/`), entièrement dédié à
l'offensive AD, avec une logique de phases (setup → collection → exploitation → post) et
une attention explicite aux contraintes d'environnement durci (NTLM désactivé, AES-only,
LDAP channel binding, FQDN vs SPN court) — exactement le type de piège qui a bloqué
l'équipe.

## Ce qui a été copié ici (intégralement — contenu déjà focalisé, pas de bloat)

- `skills/ad-methodology/` — méthodologie de phases bout-en-bout.
- `skills/ad-environment-constraints/` — pièges d'environnement AD durci (NTLM/AES/LDAP
  channel binding/FQDN vs SPN).
- `skills/ad-opsec-telemetry/` — Event IDs / télémétrie MDI par technique (OPSEC).
- `skills/kerberos-attacks/` — ASREP-roast, Kerberoasting, delegation.
- `skills/adcs-attacks/` — ESC1 à ESC17 avec commandes `certipy` exactes.
- `skills/acl-abuse/` — GenericAll/WriteDACL et abus d'ACL AD.
- `skills/coercion-ntlm-relay/` — coercition + relais NTLM.
- `skills/compliance-mapping/` — cartographie conformité (moins prioritaire pour nous,
  gardé pour complétude, coût nul).
- `agents/` (ad-enumerator, ad-attack-planner, ad-exploit-operator) — définitions
  d'agents spécialisés, référence de structuration, pas exécutés tels quels.
- `commands/` (ad-scope, ad-recon, ad-attack-paths) — commandes slash de référence.
- `README.md`, `LICENSE`.

## Ce qui n'a PAS été copié

- `.claude-plugin/marketplace.json` et `.claude-plugin/plugin.json` : métadonnées
  d'installation du plugin comme marketplace Claude Code tiers — non pertinent pour un
  usage en lecture seule dans `knowledge/external/` (on ne l'installe pas comme plugin
  actif, on le lit comme référence).

## Risques / code suspect

Aucun. Dépôt intégralement Markdown + JSON de métadonnées, aucun script shell/Python,
aucun binaire, aucun appel réseau caché.
