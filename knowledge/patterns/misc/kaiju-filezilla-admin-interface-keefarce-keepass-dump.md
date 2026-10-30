---
doc_kind: pattern
title: "FileZilla Server: crack interface admin locale + KeeFarceReborn pour dumper KeePass en clair"
category: misc
slug: kaiju-filezilla-admin-interface-keefarce-keepass-dump
created: 2026-10-30
status: active
tags:
  - legacy-memory-migration
  - nctf26-prep
  - kaiju
chain_summary: "Le hash de l'interface admin FileZilla Server (mode hashcat 10900) est souvent faible et crackable; une fois l'admin local atteint, reconfigurer le compte FTP pour un acces disque complet; separement, un plugin KeeFarceReborn accroche l'evenement OnFileOpened de KeePass pour exporter tout le contenu en clair des qu'une base est ouverte."
---
# FileZilla Server: crack interface admin locale + KeeFarceReborn pour dumper KeePass en clair

## Chain Summary

- One-line chain: Le hash de l'interface admin FileZilla Server (mode hashcat 10900) est souvent faible et crackable; une fois l'admin local atteint, reconfigurer le compte FTP pour un acces disque complet; separement, un plugin KeeFarceReborn accroche l'evenement OnFileOpened de KeePass pour exporter tout le contenu en clair des qu'une base est ouverte.

## Preconditions

- Serveur FileZilla Server accessible (meme via un shell limite en localhost); base KeePass (.kdbx) presente mais mot de passe maitre inconnu.

## Cheap Probes

- Chercher le hash admin FileZilla dans install.log ou users.xml (format hashcat mode 10900, PBKDF2-HMAC-SHA256); tester avec une wordlist combinee de tous les indices du challenge (souvent instantane, 'weak password' documente dans le writeup du lab si existant).

## Telltale Evidence

- Interface admin FileZilla ecoute sur un port local (127.0.0.1:<port randomise par instance>) accessible seulement depuis un shell sur la machine, pas depuis l'exterieur.

## Escalation Order

1. Localiser le hash admin FileZilla (users.xml ou install.log, mode hashcat 10900).
2. Cracker avec une wordlist combinee thematique (souvent instantane si le mdp est 'faible' par design).
3. Se connecter a l'interface admin locale (127.0.0.1:<port>) pour reconfigurer le compte FTP avec un acces disque complet (ex. C:\ entier) — c'est souvent le vecteur intendu, pas une misconfiguration accidentelle.
4. Si une base KeePass (.kdbx) est presente sans mot de passe maitre connu: decompiler un stub KeePass.exe remplace (classe type KPTrap) pour comprendre le mecanisme de capture, et deployer le plugin KeeFarceReborn dans Plugins/.
5. Ouvrir la base avec le VRAI mot de passe maitre (connu ou cracke separement) via ligne de commande (KeePass.exe <chemin> -pw:<motdepasse>, pas besoin de GUI si le mdp est deja connu) — declenche l'export cleartext automatique de KeeFarceReborn vers un fichier XML en clair.
6. Noter: si le mot de passe maitre n'est PAS connu, KeeFarceReborn ne sert a rien sans un acteur externe qui ouvre la base avec le vrai mdp — ne pas compter sur un declenchement automatique sans tache planifiee/Run key confirmee.

## Common Mistakes

- Supposer qu'un stub KeePass.exe remplace se declenche automatiquement sans verifier exhaustivement l'absence de taches planifiees/Run keys qui le lanceraient. Confondre un acces disque complet via FTP avec une vraie ACL NTFS equivalente (le FTP peut etre plus permissif que les droits reels d'un shell).

## Payload Shapes

```text
hashcat -m 10900 admin_fz.hash wordlist_combinee.txt ; KeePass.exe base.kdbx -pw:<motdepasse> (avec KeeFarceReborn deja deploye)
```

## Related Writeups

- N/A

## Skill Impact

- Related skill: pwn-triage/AD: ajouter FileZilla admin-hash-crack et KeeFarceReborn comme techniques de credential extraction specifiques, utiles sur tout lab exposant ces logiciels.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
