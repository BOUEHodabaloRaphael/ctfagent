---
doc_kind: pattern
title: "Injection shell par cassage explicite de guillemets dans une commande exec() entre guillemets"
category: pwn
slug: thundercipher-dizzy-quote-breaking-shell-injection
created: 2026-10-30
status: active
tags:
  - legacy-memory-migration
  - nctf26-prep
  - thundercipher
chain_summary: "Quand un parametre est insere entre guillemets dans une commande exec'ee (ex. exec('\"$path\" -version')), un simple ; dans la valeur reste a l'interieur des guillemets sans effet — il faut casser explicitement les guillemets dans la valeur injectee elle-meme."
---
# Injection shell par cassage explicite de guillemets dans une commande exec() entre guillemets

## Chain Summary

- One-line chain: Quand un parametre est insere entre guillemets dans une commande exec'ee (ex. exec('"$path" -version')), un simple ; dans la valeur reste a l'interieur des guillemets sans effet — il faut casser explicitement les guillemets dans la valeur injectee elle-meme.

## Preconditions

- Endpoint/service qui construit une commande shell en inserant un parametre utilisateur ENTRE GUILLEMETS dans le template de commande (visible via lecture du code source ou deduit par essai-erreur).

## Cheap Probes

- Tester un ; simple dans le parametre — s'il n'a aucun effet (reste dans une sortie d'erreur generique), suspecter que le parametre est insere entre guillemets dans le template.

## Telltale Evidence

- Un payload ';<cmd>;' simple produit juste 'Error' (reste dans les guillemets), alors qu'un payload qui casse explicitement les guillemets execute reellement la commande.

## Escalation Order

1. Identifier que le parametre est insere entre guillemets dans la commande template (ex: exec("${param}" -version)).
2. Construire un payload qui ferme explicitement le guillemet ouvrant, insere la commande, puis rouvre un guillemet factice pour que le reste du template reste syntaxiquement valide: param = 'true"; <cmd>; true #'.
3. Forcer un ; true final dans le payload si une commande intermediaire (ex: find avec permission denied) pourrait retourner un code de sortie non-nul, ce qui ferait tomber dans un catch generique qui masque le stdout reel.

## Common Mistakes

- Conclure qu'une injection de commande est impossible apres un simple test ';<cmd>' sans effet, sans tester le cassage explicite de guillemets si le parametre est insere entre guillemets dans le template.

## Payload Shapes

```text
param = 'true"; <commande arbitraire>; true #'
```

## Related Writeups

- N/A

## Skill Impact

- Related skill: web-triage/pwn-triage: ajouter le cassage explicite de guillemets comme variante systematique quand un ';' simple dans une injection de commande n'a aucun effet.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
