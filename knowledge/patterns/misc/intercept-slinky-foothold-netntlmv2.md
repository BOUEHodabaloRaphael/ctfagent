---
doc_kind: pattern
title: "Fichier Search Connector (slinky) comme piege NTLM alternatif a .lnk/.scf"
category: misc
slug: intercept-slinky-foothold-netntlmv2
created: 2026-10-29
status: active
tags:
  - searchconnector-slinky
  - netntlmv2
  - responder
  - smb-write-share
  - ad-recon-signing
chain_summary: "Un fichier .searchConnector-ms depose sur un partage accessible declenche une connexion sortante automatique quand un utilisateur ouvre le dossier, capturable par Responder - alternative utile quand .lnk/.scf sont filtres/supprimes."
---
# Fichier Search Connector (slinky) comme piege NTLM alternatif a .lnk/.scf

## Chain Summary

- One-line chain: Un fichier .searchConnector-ms depose sur un partage accessible declenche une connexion sortante automatique quand un utilisateur ouvre le dossier, capturable par Responder - alternative utile quand .lnk/.scf sont filtres/supprimes.
- Typical target shape: Acces en ecriture a un partage SMB consulte par d'autres utilisateurs; signature SMB non requise confirmee (sinon le relais echouera plus loin dans la chaine).

## Preconditions

- Acces en ecriture a un partage SMB consulte par d'autres utilisateurs; signature SMB non requise confirmee (sinon le relais echouera plus loin dans la chaine).

## Cheap Probes

- nxc smb <cible> --gen-relay-list ou equivalent pour verifier la signature SMB avant de deployer le piege; nxc ldap <dc> -M ldap-signing pour le channel binding.

## Telltale Evidence

- Signature SMB=False / LDAP signing=None confirmes sur les cibles pertinentes.

## Escalation Order

1. Verifier les conditions de signature SMB/LDAP avant toute chose.
2. Trouver un partage accessible en ecriture consulte par d'autres utilisateurs.
3. Deposer un fichier .searchConnector-ms piege (ou .lnk/.scf si non filtres).
4. Lancer Responder (HTTP desactive si un relais LDAP/SMB est prevu ensuite).
5. Attendre et cracker le hash capture.

## Common Mistakes

- Lancer directement un piege .lnk/.scf classique sans tester s'il est filtre/supprime par l'environnement avant d'essayer l'alternative slinky.

## Payload Shapes

```text
Fichier .searchConnector-ms pointant vers \\<attacker-ip>\share deposé sur le partage writable
```

## Related Writeups

- intercept-slinky-foothold-netntlmv2

## Skill Impact

- Related skill: pwn-triage/AD: ajouter le verification systematique de signature SMB/LDAP (nxc) avant toute chaine de relais, et le piege Search Connector comme alternative a .lnk/.scf.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
