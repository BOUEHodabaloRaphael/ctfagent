# Source: hack-skills (yaklang)

- URL du dépôt : https://github.com/yaklang/hack-skills.git
- Commit cloné : `6fbf0bc8d5c71830d62543a308d8744606c43d7c` (branche par défaut)
- Date du commit : 2026-09-13
- Clone effectué le 2026-11-09, via un agent de recherche dédié puis import manuel
  (clone temporaire hors repo principal, non committé, dans le scratchpad de session)
- Méthode de récupération : `git clone --depth 1` en lecture seule. Le dépôt contient
  des scripts `.yak` (langage Yaklang) de build du site/zip de skills — **aucun
  exécuté** ; seuls des sous-dossiers `SKILL.md` ont été copiés.

## Licence

MIT License, Copyright (c) 2026 VillanCh.

## Pourquoi cet import

~100 `SKILL.md`, dont une dizaine directement pertinents pour le boot2root/AD. Point
fort unique par rapport à `claude-ad/` et `claude-red/` : l'angle **tunneling/pivoting**
(explicitement absent des deux autres) et **container/Kubernetes escape** pour les
boot2root modernes avec Docker/K8s.

## Ce qui a été copié ici (sous-ensemble curé — le dépôt complet couvre ~80 autres
skills web/crypto/mobile déjà largement couverts par `ctf-web`/`ctf-crypto`)

- `active-directory-acl-abuse/` (+ `BLOODHOUND_PATHS.md`)
- `active-directory-certificate-services/` (+ `ADCS_ESC_MATRIX.md`)
- `active-directory-kerberos-attacks/` (+ `KERBEROS_ATTACK_CHAINS.md`)
- `ntlm-relay-coercion/` (+ `COERCION_METHODS.md`)
- `linux-privilege-escalation/` (+ `KERNEL_EXPLOITS_CHECKLIST.md`,
  `SUID_CAPABILITIES_TRICKS.md`)
- `windows-privilege-escalation/` (+ `TOKEN_POTATO_TRICKS.md`, `UAC_BYPASS_METHODS.md`)
- `linux-lateral-movement/`
- `windows-lateral-movement/` (+ `CREDENTIAL_DUMPING.md`)
- `tunneling-and-pivoting/` — angle pivot, absent de `claude-ad`/`claude-red`.
- `container-escape-techniques/` (+ `DOCKER_ESCAPE_CHAINS.md`)
- `kubernetes-pentesting/`
- `README.md`, `LICENSE`.

## Ce qui n'a PAS été copié (et pourquoi)

- Les scripts `.yak` (`scripts/build-hack-skills-zip.yak`, `scripts/build-skills-index.yak`)
  et tout `site/` (page web statique de présentation du dépôt, assets, CSS/JS, favicons,
  `CNAME`) : purement outillage de publication du dépôt source, aucune valeur pour une
  lecture en référence.
- Les ~80 autres skills (web, mobile, crypto, OSINT, forensics, etc.) : hors périmètre
  de ce besoin précis et déjà largement redondants avec `ctf-web`/`ctf-crypto`/
  `security-skills`/`hacking-skills` déjà importés.

## Risques / code suspect

Aucun dans les fichiers copiés (uniquement Markdown). Les scripts `.yak` non copiés
n'ont pas été audités en détail puisqu'ils ne sont pas repris ici.
