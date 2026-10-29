---
doc_kind: writeup
title: "Endgame XEN - Breach (phishing SMTP vers portail Citrix)"
category: web
slug: xen-breach-smtp-phishing-citrix
created: 2026-10-29
status: solved
tags:
  - citrix
  - phishing
  - smtp-enum
  - netscaler
  - ad
  - swaks
source: "HTB Endgame XEN"
target: "Citrix NetScaler Gateway /remote"
---
# Endgame XEN - Breach (phishing SMTP vers portail Citrix)

## Challenge Summary

- Source: HTB Endgame XEN
- Target: Citrix NetScaler Gateway /remote
- Goal: Enumeration SMTP RCPT TO pour recuperer des adresses valides, puis email de phishing usurpant l'IT pour faire cliquer un bot interne qui poste ses creds Citrix en clair vers un listener controle.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. nmap -sT -p- puis -sV -sC sur 25/80/443; 80 redirige vers le vhost principal.
2. gobuster sur le vhost revele /remote (portail Citrix NetScaler Gateway).
3. smtp-user-enum -M RCPT valide des adresses (it@, legal@, marketing@, sales@).
4. swaks usurpe it@ vers sales@ avec un lien citrix vers un nc -lnvp 80 controle.
5. Un bot interne clique et poste en clair LoginType=Explicit&user=...&password=...&domain=HTB.LOCAL.
6. Connexion au portail Citrix /remote avec les creds recuperees -> bureau virtuel -> flag.

## Key Evidence

- requete POST /remote/auth/login.aspx capturee en clair sur nc -lnvp 80 contenant les credentials.

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
email HTML/texte phishing (swaks --body) + capture HTTP brute (nc listener).
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Sur un entry point Citrix/NetScaler, l'enum SMTP RCPT TO fournit la liste de cibles de phishing; un lien citrix generique suffit si un bot/utilisateur interne clique automatiquement; recuperer les creds par capture HTTP brute plutot que par credential harvesting applicatif.

## Pattern Candidates

- Nouveau pattern: xen-breach-smtp-phishing-citrix
