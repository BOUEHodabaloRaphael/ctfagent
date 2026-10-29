---
doc_kind: writeup
title: "FullHouse - Old Cobol Projects (vol NetNTLMv2 via fichier piege sur partage SMB)"
category: misc
slug: fullhouse-ntlm-theft-smb-share-trap
created: 2026-10-29
status: solved
tags:
  - ntlm-theft
  - responder
  - smb-write-share
  - socat-relay
  - icon-trap
source: "HTB Pro Lab FullHouse"
target: "Partage SMB en ecriture"
---
# FullHouse - Old Cobol Projects (vol NetNTLMv2 via fichier piege sur partage SMB)

## Challenge Summary

- Source: HTB Pro Lab FullHouse
- Target: Partage SMB en ecriture
- Goal: Un credential de domaine fuite via un utilitaire decompile donne acces en ecriture a un partage SMB; un piege .url+desktop.ini capture un hash NetNTLMv2 via Responder relaye depuis l'hote pivot.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Identifiant de domaine trouve dans un utilitaire decompile sur un bureau accessible.
2. crackmapexec smb confirme un acces WRITE sur un partage du DC.
3. Un fichier .scf piege est auto-supprime par l'environnement; bascule vers une paire .url + desktop.ini qui survit.
4. Responder lance dans un conteneur avec acces reseau direct, relaye via socat depuis l'hote pivot pour voir la requete depuis le bon point de vue reseau.
5. Outil de generation de pieges NTLM depose les fichiers via smbclient sur le partage WRITE.
6. Hash NetNTLMv2 capture, casse offline -> acces evil-winrm.

## Key Evidence

- crackmapexec liste explicitement les permissions READ,WRITE du partage pour le compte trouve.

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
fichiers piege Windows (.url + desktop.ini, icone UNC) generes par un outil dedie.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Si un type de piege (.scf) est systematiquement supprime par l'environnement cible, essayer un type equivalent (.url+desktop.ini); relayer Responder via socat depuis un hote pivot permet de capturer des hashs sur un segment reseau non directement accessible.

## Pattern Candidates

- Nouveau pattern: fullhouse-ntlm-theft-smb-share-trap
