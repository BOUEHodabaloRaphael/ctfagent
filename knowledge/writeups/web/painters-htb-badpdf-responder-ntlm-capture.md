---
doc_kind: writeup
title: "Zephyr - Painters.htb - Foothold via BadPDF + Responder NTLM capture"
category: web
slug: painters-htb-badpdf-responder-ntlm-capture
created: 2026-10-29
status: solved
tags:
  - web
  - badpdf
  - responder
  - ntlmv2
  - hashcat
  - initial-access
source: "HTB Pro Lab Zephyr"
target: "painters.htb (nginx, formulaire upload PDF)"
---
# Zephyr - Painters.htb - Foothold via BadPDF + Responder NTLM capture

## Challenge Summary

- Source: HTB Pro Lab Zephyr
- Target: painters.htb (nginx, formulaire upload PDF)
- Goal: Un PDF malveillant (badpdf) force le serveur a faire une requete SMB vers l'attaquant, capturee par Responder, qui recupere le hash NTLMv2.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. nmap ping sweep -> hote trouve.
2. nmap full scan: 22/80/443, redirect vers https://painters.htb.
3. upload PDF malveillant via formulaire Vacancies.
4. Responder capture hash NTLMv2.
5. hashcat -m 5600 casse le hash -> mot de passe.
6. ssh avec les creds obtenues.

## Key Evidence

- Capture Responder montrant le hash NTLMv2-SSP; hashcat confirme Cracked.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
msfconsole auxiliary/fileformat/badpdf, Responder, hashcat -m 5600, ssh.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout (lecture visuelle verifiee).

## Reusable Lessons

- Upload PDF + Responder NTLM capture est un pattern classique de foothold contre portails web avec upload de fichiers.

## Pattern Candidates

- Voir pattern associe de meme slug.
