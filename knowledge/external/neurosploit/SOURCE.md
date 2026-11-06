# Source: NeuroSploit

- URL du dépôt : https://github.com/JoasASantos/NeuroSploit.git
- Commit clonné : `92e8959f4ea17bddaa0436505edcddf98f7d6b16` (branche `main`, tag/version README `v4.4.0`)
- Date du commit : 2026-10-19 (clone effectué le 2026-11-06)
- Clone temporaire source : `/tmp/recon_neurosploit/` (hors du repo principal, non committé)
- Méthode de récupération : `git clone --depth 1` en lecture seule. Aucun script du dépôt
  n'a été exécuté (pas de `setup.sh`/`install.ps1`, pas de build Rust, pas de run réseau).

## Licence

MIT License, Copyright (c) 2026 Joas A Santos & Red Team Leaders. Pas de restriction de
réutilisation/modification/redistribution tant que la notice de copyright et la permission
sont conservées. Compatible avec une réutilisation interne dans CTFAgent (prépa NCTF26),
y compris adaptation des extraits markdown ci-dessous.

## Ce qui a été copié ici et pourquoi

NeuroSploit est un harnais Rust de pentest autonome orienté **web/API/cloud/Active
Directory/mobile appsec** (bug bounty / red team), pas un solveur de CTF pwn/rev classique.
Sa valeur réutilisable pour nous tient dans sa bibliothèque de ~486 "agents" markdown
(playbooks méthodologiques courts, format `## User Prompt` / `## System Prompt`), pas dans
du code exécutable. Sous-ensemble copié (texte brut, aucun binaire) :

- `meta/recon.md` — méthodologie de cartographie de surface d'attaque (fingerprint → endpoints
  → auth/état → APIs → recon_json). Utile pour enrichir l'étape recon de nos skills
  `ctf-solver-profile` / `web-triage`.
- `meta/orchestrator.md` — boucle recon → sélection → exploitation → validation → score →
  rapport. Référence de structuration d'un run, pas un outil à exécuter.
- `meta/REGISTRY.md` — catalogue indexé des agents/CWE couverts (table des matières utile
  pour retrouver rapidement une technique par CWE).
- `web/ssti.md` — détection/fingerprint multi-moteurs SSTI (Jinja2/Twig/Freemarker/Velocity/
  Thymeleaf/Pug) avec polyglotte unique et critères de preuve/faux-positif.
- `web/jwt_alg_confusion.md` — technique RS256→HS256 (récupération clé publique, forge HMAC,
  critères d'acceptation serveur).
- `web/ssrf.md`, `web/xxe.md`, `web/insecure_deserialization.md` — méthodologies condensées
  par classe de vulnérabilité, avec critères explicites de preuve/faux-positif.
- `rev/static_binary_triage.md` — triage statique ELF/Mach-O/PE (file, readelf, checksec,
  r2/Ghidra headless, détection packer/obfuscation) — directement applicable à notre
  `rev-triage`.
- `rev/obfuscation_analysis_deobfuscation.md` — classification des techniques d'obfuscation
  (renommage, chiffrement de chaînes, aplatissement de flux, API-hashing, packing) et pistes
  de désobfuscation statique/dynamique (Frida hook, re-implémentation du décrypteur).

## Ce qui n'a PAS été copié (et pourquoi)

- Le code Rust du harnais (`neurosploit-rs/app/`, `neurosploit-rs/crates/harness/`) : logique
  d'orchestration propre à leur produit, pas un script autonome réutilisable tel quel pour
  notre usage CTF.
- Les scripts d'installation (`setup.sh`, `setup.bat`, `install.ps1`, `env.sh`) : spécifiques
  à l'installation de leur binaire, sans valeur pour notre prépa, et volontairement non
  exécutés.
- `neurosploit-rs/tools/laya_shim.py` : shim HTTP local pour un moteur de décision tiers
  (Laya), hors-sujet pour un CTF (pas d'exploitation, pas de RE/pwn).
- Les ~470 autres fichiers `agents_md/vulns/*.md` et `agents_md/infra/*.md` (AD, cloud
  AWS/GCP/Azure, k8s, containers) : pertinents pour du pentest d'infrastructure réelle
  mais hors du périmètre typique d'un CTF jeopardy/KOTH (web/pwn/rev/crypto/forensics/osint).
  À revisiter ponctuellement si une épreuve NCTF26 touche à l'AD ou au cloud.

## Mise à jour 2026-11-06 — copie intégrale des fiches

Ajout de `techniques/` : les **486 fiches `agents_md/`** du dépôt, copiées telles quelles
en préservant l'arborescence (`vulns/`, `recon/`, `chains/`, `code/`, `infra/`,
`container/`, `ai/`, `meta/` + `REGISTRY.md`). Les fiches curatées listées plus haut
restent à la racine pour un accès rapide ; `techniques/` sert de référence exhaustive
(recherche par CWE via `techniques/REGISTRY.md`). Ce sont des playbooks markdown, aucun
code exécutable, même périmètre de licence (MIT) et mêmes précautions.

## Risques / code suspect

Aucun. Le dépôt ne contient aucun script réseau exécuté lors de cette revue, aucune
obfuscation de code, aucun appel réseau caché détecté dans les fichiers inspectés
(`setup.sh`, `install.ps1`, `laya_shim.py`). Les playbooks markdown eux-mêmes insistent sur
un cadre "AUTHORIZED engagement" / non-destructif / preuve avant rapport — posture cohérente
avec notre propre `ctf-solver-profile`. Seul bémol : `setup.sh` télécharge un binaire
précompilé depuis les releases GitHub du projet si on l'exécute un jour — à ne faire que
depuis une machine jetable, comme pour tout binaire tiers téléchargé.
