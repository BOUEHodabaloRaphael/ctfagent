---
doc_kind: pattern
title: "Holmes CTF 2026 Sherlock 07 - Iron Feather / Mission Vault (drone PX4, dechiffrement ULog)"
category: forensics
slug: ironfeather-sherlock07-px4-ulog-decryption
created: 2026-10-29
status: draft
tags:
  - dfir
  - px4
  - ulog
  - drone-forensics
  - firmware-decryption
  - holmes-ctf
chain_summary: "Drone PX4 recupere avec stockage dataman et journal de vol (.ulg) chiffres; le binaire PX4/px4-dataman stripped fourni comme reference pour reverser le format/mecanisme de chiffrement."
---
# Holmes CTF 2026 Sherlock 07 - Iron Feather / Mission Vault (drone PX4, dechiffrement ULog)

## Chain Summary

- One-line chain: Drone PX4 recupere avec stockage dataman et journal de vol (.ulg) chiffres; le binaire PX4/px4-dataman stripped fourni comme reference pour reverser le format/mecanisme de chiffrement.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- PARTIELLEMENT CONFIRME: hexdump du journal de vol dechiffre commence par le magic "ULog" suivi d'un header version et de champs lisibles (format valide confirme). NON RESOLU pour le fichier dataman (uniquement des zeros observes, cle/algorithme incertain pour ce second blob).

## Escalation Order

1. Reverser le binaire px4-dataman (ELF stripped) pour comprendre le format et le schema de chiffrement cible.
2. Dechiffrer le journal de vol chiffre -> succes confirme par le magic bytes 'ULog' + header valide.
3. Dechiffrer le fichier dataman chiffre -> fichier obtenu mais entierement a zero sur l'echantillon inspecte (dechiffrement incertain).
4. Etape suivante attendue: parser le ULog dechiffre (topics vehicle_gps_position/vehicle_status) pour reconstruire les phases de vol.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Pour tout stockage proprietaire chiffre d'un firmware embarque, reverser le binaire de reference (meme stripped) pour localiser la routine crypto/cle, valider le succes du dechiffrement via le magic bytes attendu du format clair.
```

## Related Writeups

- ironfeather-sherlock07-px4-ulog-decryption

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
