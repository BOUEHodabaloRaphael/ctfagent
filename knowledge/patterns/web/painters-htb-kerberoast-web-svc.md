---
doc_kind: pattern
title: "Zephyr - Painters.htb - Kerberoasting + psexec SYSTEM"
category: web
slug: painters-htb-kerberoast-web-svc
created: 2026-10-29
status: active
tags:
  - ad
  - kerberoasting
  - bloodhound
  - psexec
chain_summary: "BloodHound identifie des comptes kerberoastables; GetUserSPNs.py extrait les TGS; hashcat casse le hash du compte de service; psexec reutilise le hash obtenu."
---
# Zephyr - Painters.htb - Kerberoasting + psexec SYSTEM

## Chain Summary

- One-line chain: BloodHound identifie des comptes kerberoastables; GetUserSPNs.py extrait les TGS; hashcat casse le hash du compte de service; psexec reutilise le hash obtenu.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- hashcat confirme le crack; psexec donne un shell SYSTEM.

## Escalation Order

1. Upload SharpHound.exe, collecte BloodHound.
2. GetUserSPNs.py extrait le hash TGS du compte de service.
3. hashcat -m 13100 -> mot de passe.
4. psexec.py sur la machine cible.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Kerberoasting classique: toujours collecter BloodHound tot pour identifier les comptes avec SPN.
```

## Related Writeups

- painters-htb-kerberoast-web-svc

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
