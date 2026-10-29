---
doc_kind: pattern
title: "Checklist recon passive pre-intrusive (pentest web reel)"
category: misc
slug: pennygroupe-recon-passive
created: 2026-10-29
status: active
tags:
  - web
  - recon-passive
  - security-headers
  - server-status
  - spf-dkim-dmarc
  - pentest-reel
chain_summary: "Avant toute phase active, auditer en passif: fingerprint pile, en-tetes de securite absents, /server-status + fichiers sensibles connus, DNS SPF/DKIM/DMARC, TTFB repetes."
---
# Checklist recon passive pre-intrusive (pentest web reel)

## Chain Summary

- One-line chain: Avant toute phase active, auditer en passif: fingerprint pile, en-tetes de securite absents, /server-status + fichiers sensibles connus, DNS SPF/DKIM/DMARC, TTFB repetes.
- Typical target shape: Mandat de pentest ou phase 1 limitee au non-intrusif (scope contractuel ou legal restreint).

## Preconditions

- Mandat de pentest ou phase 1 limitee au non-intrusif (scope contractuel ou legal restreint).

## Cheap Probes

- curl -sSI <url> ; dig TXT <domain> (SPF) ; dig TXT default._domainkey.<domain> (DKIM) ; dig TXT _dmarc.<domain> ; curl <url>/server-status ; curl <url>/.env /.git/HEAD /telescope /ignition.

## Telltale Evidence

- En-tetes de securite manquants; code de reponse different de 404 sur des chemins sensibles connus (403 au lieu de 404 = module present mais restreint); enregistrements DNS laxistes.

## Escalation Order

1. Fingerprint la pile technique (serveur web, langage, framework) via headers/cookies/erreurs.
2. Verifier les 6 en-tetes de securite HTTP recommandes.
3. Tester les endpoints de diagnostic connus (/server-status, /.env, /.git, /telescope, /ignition) sans y entrer activement.
4. Auditer SPF/DKIM/DMARC pour le risque de spoofing email.
5. Mesurer le TTFB plusieurs fois pour detecter une instabilite/degradation preexistante (baseline avant toute phase active).

## Common Mistakes

- Lancer des scans actifs/intrusifs avant d'avoir etabli cette baseline passive, surtout hors du scope autorise.

## Payload Shapes

```text
curl -sSI https://target/ ; dig TXT target ; curl -I https://target/server-status
```

## Related Writeups

- pennygroupe-recon-passive

## Skill Impact

- Related skill: web-triage: ajouter cette checklist recon-passive comme etape 0 avant toute probe active sur un engagement reel avec contraintes de scope.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
