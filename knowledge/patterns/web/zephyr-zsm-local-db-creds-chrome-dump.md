---
doc_kind: pattern
title: "Zephyr - zsm.local - DB password reuse + hashcat + Chrome creds dump"
category: web
slug: zephyr-zsm-local-db-creds-chrome-dump
created: 2026-10-29
status: active
tags:
  - credential-reuse
  - chrome-dump
  - hashcat
  - enum-chrome
chain_summary: "Un fichier de config revele le mot de passe DB; dump de la table users; hashcat casse un hash bcrypt. Un dump Chrome extrait ensuite des creds stockes utiles plus loin dans le lab."
---
# Zephyr - zsm.local - DB password reuse + hashcat + Chrome creds dump

## Chain Summary

- One-line chain: Un fichier de config revele le mot de passe DB; dump de la table users; hashcat casse un hash bcrypt. Un dump Chrome extrait ensuite des creds stockes utiles plus loin dans le lab.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- hashcat confirme le crack bcrypt; enum_chrome affiche les creds dechiffres avec l'URL associee.

## Escalation Order

1. Lecture du fichier de config -> mot de passe DB.
2. mysql dump table users -> hash bcrypt.
3. hashcat -m 3200 avec rockyou -> mot de passe.
4. Pivot meterpreter+autoroute+socks_proxy.
5. winPEAS trouve un chemin Chrome passwords.
6. post/windows/gather/enum_chrome dump des creds Chrome utiles plus loin dans le lab.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Les fichiers de config applicatifs contiennent souvent des mots de passe reutilises; dump Chrome via module metasploit tres efficace pour recuperer des creds stockes.
```

## Related Writeups

- zephyr-zsm-local-db-creds-chrome-dump

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
