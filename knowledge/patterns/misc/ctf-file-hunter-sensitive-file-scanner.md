---
doc_kind: pattern
title: "CTF-File-Hunter / loot-hunter — scanner recursif de fichiers sensibles (helper, pas un solveur)"
category: misc
slug: ctf-file-hunter-sensitive-file-scanner
created: 2026-11-09
status: active
tags:
  - recon
  - post-shell
  - file-hunting
  - credential-hunting
  - helper-tool
  - loot
chain_summary: "Suite Python zero-dependance (~/tools/CTF-File-Hunter, lanceurs file-hunter/ctf-file-hunter/loot-hunter dans le PATH) qui parcourt recursivement un ou plusieurs repertoires, filtre par extension/nom (.conf/.env/.key/id_rsa/wp-config.php/...) et grep des mots-cles (pass/key/admin/secret/flag/token) dans le contenu lisible, avec SHA256 tronque pour reperer vite les fichiers interessants une fois un acces filesystem obtenu (shell, LFI avec lecture de repertoire, conteneur, etc.)."
---
# CTF-File-Hunter / loot-hunter — scanner recursif de fichiers sensibles

## Chain Summary

- One-line chain: une fois un acces lecture au filesystem obtenu (shell local/distant,
  conteneur, montage), lancer `ctf-file-hunter` (interruptible, zones cle `/home /root
  /var/www /tmp /dev/shm /mnt /opt`) ou `file-hunter <chemin>` (cible precise) pour
  reperer en quelques secondes les fichiers aux extensions/noms sensibles qui contiennent
  des mots-cles type `pass`, `key`, `admin`, `secret`, `flag`, `token`, `id_rsa`,
  `db_password`, avec hash SHA256 tronque pour dedupliquer visuellement.
- `loot-hunter` fait le meme travail mais en version "pentest/post-exploit lourde" et
  n'est **pas interruptible** par Ctrl+C (conçu pour tourner jusqu'au bout) — a reserver
  a un contexte ou on veut un scan complet sans etre tente de l'interrompre, jamais a un
  environnement de prod non autorise.

## Preconditions

- Acces lecture a un filesystem (shell SSH/RCE, conteneur, LFI permettant de lister/lire
  un repertoire, volume monte, etc.). Cet outil ne donne pas d'acces — il accelere la
  triage une fois l'acces obtenu.
- `python3` disponible sur la machine qui execute le scan (zero dependance externe).

## Cheap Probes

- `ctf-file-hunter` (sans argument) : scan automatique + interactif des zones cle du
  systeme (`/home`, `/root`, `/var/www`, `/tmp`, `/dev/shm`, `/mnt`, `/opt`, ou cwd si
  aucune n'existe). Interruptible avec Ctrl+C.
- `file-hunter <chemin>` : scan cible d'un seul repertoire (ex. `file-hunter /home/ubuntu`
  ou un repertoire web uploade/extrait localement).
- `loot-hunter` : meme logique, zero kill-switch, pense pour un pentest reel (scan lourd
  qui va jusqu'au bout).
- Les trois lanceurs sont dans `~/.local/bin/` (donc dans le PATH) et wrappent
  `~/tools/CTF-File-Hunter/{CTF-File-Hunterv1,File-Hunter,loot-hunter}.py`.

## Telltale Evidence

- Table terminal avec colonnes ACC / SHA256 / NOM DU FICHIER / ALERTE, alerte `[!!]`
  listant les mots-cles matches (ex. `PASS, ADMIN` sur un `app.conf`, `FLAG` sur un
  `flag.txt`).
- Extensions ciblees : `.txt .conf .log .key .env .json .bak .sql .db`.
- Noms ciblees : `id_rsa`, `id_dsa`, `wp-config.php`, `config.php`, `.bash_history`,
  `.zsh_history`, `credentials`, `passwd`.
- Exclut automatiquement `/proc /sys /dev .git __pycache__ /var/lib/docker` — donc un
  flag planque dans un de ces chemins ne sera pas vu par l'outil, verifier a la main.

## Escalation Order

1. Une fois un shell/acces filesystem obtenu, lancer `ctf-file-hunter` (ou `loot-hunter`
   en contexte pentest reel) avant de fouiller a la main — ca remplace un premier passage
   `find` + `grep -r` manuel.
2. Pour un repertoire specifique deja identifie comme interessant (ex. webroot extrait,
   home d'un autre utilisateur), utiliser `file-hunter <chemin>` pour un scan plus rapide
   et moins bruyant.
3. Traiter chaque alerte `[!!]` comme un indice a verifier manuellement (lire le fichier
   en entier) — l'outil ne confirme pas qu'un flag est reellement present, il signale
   juste un contenu/nom suspect (cf. Limites).
4. Ne pas oublier les chemins exclus par defaut (`.git`, `/var/lib/docker`, `/proc`) —
   une fouille manuelle complementaire reste necessaire si le challenge pointe vers un
   de ces repertoires.

## Common Mistakes

- Lancer `loot-hunter` sur une cible ou l'on n'est pas certain de vouloir un scan complet
  non interruptible (peut tourner longtemps sur un `/` volumineux) — preferer
  `ctf-file-hunter` en CTF pour pouvoir interrompre.
- Traiter une absence d'alerte comme une preuve qu'aucun fichier sensible n'existe : les
  mots-cles et extensions sont une liste fixe, pas exhaustive (ex. un flag dans un fichier
  `.py` ou `.md` sans mot-cle flag dans le nom passera inapercu de la detection par nom,
  mais sera lu si l'extension n'est pas filtree — verifier la liste `LOOT_EXTENSIONS`
  avant de conclure a un negatif).
- Faire confiance au scan content-based sur un fichier >2 Mo : le grep de mots-cles dans
  le contenu est desactive au-dela de cette taille (seul le hash est calcule).

## Payload Shapes

```text
# Usage rapide une fois un shell obtenu
ctf-file-hunter                 # scan auto des zones cle, interruptible (Ctrl+C)
file-hunter /home/target_user   # scan cible d'un repertoire precis
loot-hunter                     # scan pentest lourd, PAS interruptible — a utiliser a bon escient

# Verifie a la main un hit interessant avant de le considerer comme "probablement le flag"
cat <chemin_signale_par_lalerte>
```

## Related Writeups

- (aucun writeup direct encore — outil ajoute et teste en isolation le 2026-11-09,
  detection confirmee sur `app.conf` -> `PASS, ADMIN` et `flag.txt` -> `FLAG`)

## Skill Impact

- Related skill: [[ctf-forensics]], [[pwn-triage]], [[web-triage]], [[ctf-misc]] —
  mentionner les lanceurs `ctf-file-hunter` / `file-hunter` / `loot-hunter` dans la
  section post-acces/post-shell de chacune pour eviter de re-ecrire un `find`/`grep -r`
  manuel a chaque fois.
- Rule to add or update: garder ce pattern comme reference unique de l'outil ; si un
  faux negatif/faux positif notable est observe en usage reel, l'ajouter ici sous
  "Common Mistakes" plutot que de creer un nouveau fichier.
