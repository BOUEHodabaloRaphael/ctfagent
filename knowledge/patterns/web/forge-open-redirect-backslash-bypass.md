---
doc_kind: pattern
title: "Bypass de sanitizer de redirection par normalisation navigateur (backslash/encodage)"
category: web
slug: forge-open-redirect-backslash-bypass
created: 2026-10-29
status: active
tags:
  - open-redirect
  - url-parsing
  - backslash-normalization
  - oauth-phishing
chain_summary: "Un sanitizer de redirection qui teste startsWith('/') sur la chaine brute sans parser l'URL complete est contournable via des variantes que le navigateur normalise differemment (backslash -> slash, encodage, userinfo @)."
---
# Bypass de sanitizer de redirection par normalisation navigateur (backslash/encodage)

## Chain Summary

- One-line chain: Un sanitizer de redirection qui teste startsWith('/') sur la chaine brute sans parser l'URL complete est contournable via des variantes que le navigateur normalise differemment (backslash -> slash, encodage, userinfo @).
- Typical target shape: Parametre de redirection post-action (returnTo, next, redirect_uri interne) valide par un test de prefixe sur la chaine brute plutot que par un parsing URL complet comparant l'origine finale.

## Preconditions

- Parametre de redirection post-action (returnTo, next, redirect_uri interne) valide par un test de prefixe sur la chaine brute plutot que par un parsing URL complet comparant l'origine finale.

## Cheap Probes

- Tester next=/\\<domaine> et next=/%5C<domaine> en plus du classique next=//<domaine> deja probablement bloque.

## Telltale Evidence

- Le sanitizer accepte la variante backslash/encodee alors qu'il bloque la variante // explicite.

## Escalation Order

1. Identifier le parametre de redirection et son sanitizer (souvent visible par test direct de // qui echoue).
2. Tester les variantes de normalisation navigateur: backslash (/\\), encodage (%5C), userinfo (@).
3. Confirmer sur tous les sinks utilisant ce meme sanitizer (login, register, callbacks OAuth).

## Common Mistakes

- Valider une redirection par test de prefixe sur la chaine brute au lieu de parser l'URL et comparer l'origine finale resolue (comme le fera le navigateur).

## Payload Shapes

```text
?next=/\\evil.com  ou  ?next=/%5Cevil.com
```

## Related Writeups

- forge-open-redirect-backslash-bypass

## Skill Impact

- Related skill: web-triage (open redirect): ajouter la variante backslash/encodage comme test systematique en plus du // classique.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
