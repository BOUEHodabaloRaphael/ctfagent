---
doc_kind: pattern
title: "Extraction mot de passe GNOME (mimipenguin) + deverrouillage keyring par renommage"
category: misc
slug: rpg-ch3-ignis-gnome-keyring-mimipenguin
created: 2026-10-29
status: active
tags:
  - gnome-keyring
  - mimipenguin
  - dbus-unlock
  - linux-post-exploitation
  - credential-dump
chain_summary: "mimipenguin extrait un mot de passe de session GNOME en clair depuis la memoire; les keyrings verrouilles non-login peuvent etre deverrouilles via DBus en les renommant en login.keyring pour simuler une session fraiche."
---
# Extraction mot de passe GNOME (mimipenguin) + deverrouillage keyring par renommage

## Chain Summary

- One-line chain: mimipenguin extrait un mot de passe de session GNOME en clair depuis la memoire; les keyrings verrouilles non-login peuvent etre deverrouilles via DBus en les renommant en login.keyring pour simuler une session fraiche.
- Typical target shape: Acces root/privilégié a une machine Linux avec une session desktop GNOME active pour un autre utilisateur.

## Preconditions

- Acces root/privilégié a une machine Linux avec une session desktop GNOME active pour un autre utilisateur.

## Cheap Probes

- Verifier la presence de process GNOME (gnome-keyring-daemon, gnome-shell) pour un utilisateur cible; localiser ~/.local/share/keyrings/*.keyring.

## Telltale Evidence

- mimipenguin retourne un mot de passe en clair associe a une session GNOME active.

## Escalation Order

1. Lancer mimipenguin en root pour extraire les mots de passe de session en memoire.
2. Copier (non destructivement) les fichiers *.keyring de l'utilisateur cible.
3. Si une collection non-login refuse le deverrouillage DBus direct, la renommer en login.keyring.
4. Deverrouiller via gnome-keyring-daemon --unlock --components=secrets en pipant le mot de passe obtenu.
5. Lire les secrets desormais accessibles (identifiants Wifi, applications, etc.).

## Common Mistakes

- Tenter le deverrouillage DBus direct sur une collection non standard sans passer par le renommage en login.keyring.

## Payload Shapes

```text
echo '<password>' | gnome-keyring-daemon --unlock --components=secrets
```

## Related Writeups

- rpg-ch3-ignis-gnome-keyring-mimipenguin

## Skill Impact

- Related skill: pwn-triage/Linux post-exploit: ajouter mimipenguin + gnome-keyring unlock comme technique de credential harvesting desktop Linux.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
