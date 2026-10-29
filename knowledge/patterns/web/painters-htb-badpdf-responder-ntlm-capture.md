---
doc_kind: pattern
title: "Zephyr - Painters.htb - Foothold via BadPDF + Responder NTLM capture"
category: web
slug: painters-htb-badpdf-responder-ntlm-capture
created: 2026-10-29
status: active
tags:
  - web
  - badpdf
  - responder
  - ntlmv2
  - hashcat
  - initial-access
chain_summary: "Un PDF malveillant (badpdf) force le serveur a faire une requete SMB vers l'attaquant, capturee par Responder, qui recupere le hash NTLMv2."
---
# Zephyr - Painters.htb - Foothold via BadPDF + Responder NTLM capture

## Chain Summary

- One-line chain: Un PDF malveillant (badpdf) force le serveur a faire une requete SMB vers l'attaquant, capturee par Responder, qui recupere le hash NTLMv2.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Capture Responder montrant le hash NTLMv2-SSP; hashcat confirme Cracked.

## Escalation Order

1. nmap ping sweep -> hote trouve.
2. nmap full scan: 22/80/443, redirect vers https://painters.htb.
3. upload PDF malveillant via formulaire Vacancies.
4. Responder capture hash NTLMv2.
5. hashcat -m 5600 casse le hash -> mot de passe.
6. ssh avec les creds obtenues.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Upload PDF + Responder NTLM capture est un pattern classique de foothold contre portails web avec upload de fichiers.
```

## Related Writeups

- painters-htb-badpdf-responder-ntlm-capture

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
