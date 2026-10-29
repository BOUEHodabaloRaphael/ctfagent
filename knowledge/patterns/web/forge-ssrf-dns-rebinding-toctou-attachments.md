---
doc_kind: pattern
title: "SSRF par DNS rebinding TOCTOU (check-then-fetch avec double resolution)"
category: web
slug: forge-ssrf-dns-rebinding-toctou-attachments
created: 2026-10-29
status: active
tags:
  - ssrf
  - dns-rebinding
  - toctou
  - check-then-fetch
chain_summary: "Un garde SSRF qui valide un hostname par une resolution DNS puis laisse une couche de fetch separee re-resoudre independamment ce meme hostname est contournable par DNS rebinding: l'attaquant repond une IP publique au check et une IP interne a la connexion reelle."
---
# SSRF par DNS rebinding TOCTOU (check-then-fetch avec double resolution)

## Chain Summary

- One-line chain: Un garde SSRF qui valide un hostname par une resolution DNS puis laisse une couche de fetch separee re-resoudre independamment ce meme hostname est contournable par DNS rebinding: l'attaquant repond une IP publique au check et une IP interne a la connexion reelle.
- Typical target shape: Service effectuant un fetch d'URL utilisateur-fournie (image, webhook, preview) avec validation d'hostname SSRF separee de la connexion reelle, et controle DNS possible par l'attaquant (domaine propre).

## Preconditions

- Service effectuant un fetch d'URL utilisateur-fournie (image, webhook, preview) avec validation d'hostname SSRF separee de la connexion reelle, et controle DNS possible par l'attaquant (domaine propre).

## Cheap Probes

- Fournir une URL sous un domaine controle par l'attaquant et observer si le garde SSRF et le client HTTP effectuent chacun leur propre resolution DNS independante (plutot que de reutiliser l'IP deja validee).

## Telltale Evidence

- Le garde valide l'hostname (log ALLOWED) et le fetch reussit tout de meme a atteindre une cible interne quand le DNS autoritaire de l'attaquant repond differemment aux deux resolutions.

## Escalation Order

1. Identifier un service de fetch d'URL avec un garde SSRF base sur la resolution du hostname.
2. Heberger un domaine sous controle DNS propre repondant differemment selon le pattern de requete (ou simplement avec un TTL tres court permettant un rebind entre check et connect).
3. Fournir ce hostname comme cible du fetch.
4. Confirmer si la connexion reelle atteint une IP interne malgre la validation initiale.

## Common Mistakes

- Valider un hostname puis laisser une couche HTTP separee (client, proxy) re-resoudre independamment pour se connecter, au lieu de pinner l'IP deja validee pour la connexion reelle.

## Payload Shapes

```text
URL image: http://attacker-controlled-rebinding-domain/ (DNS TTL court, reponses differentes check vs connect)
```

## Related Writeups

- forge-ssrf-dns-rebinding-toctou-attachments, forge-ssrf-window-open-popup-bypass

## Skill Impact

- Related skill: web-triage (SSRF): ajouter le test DNS-rebinding (deux resolutions independantes) comme variante systematique de tout garde SSRF base sur la resolution hostname.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
