---
doc_kind: pattern
title: "Gestionnaire wp_ajax_* oublie lors d'un correctif de controle d'autorisation"
category: web
slug: zoom-wp-plugin-vczapi-sync-user-missing-auth
created: 2026-10-29
status: active
tags:
  - missing-authorization
  - cwe-862
  - wordpress-ajax
  - broken-access-control
  - privilege-check-omission
  - incomplete-patch
chain_summary: "Apres un correctif de securite WordPress ajoutant des controles de capacite/nonce a certains gestionnaires AJAX, un gestionnaire voisin du meme plugin peut avoir ete oublie et rester exploitable par un role faible (Subscriber)."
---
# Gestionnaire wp_ajax_* oublie lors d'un correctif de controle d'autorisation

## Chain Summary

- One-line chain: Apres un correctif de securite WordPress ajoutant des controles de capacite/nonce a certains gestionnaires AJAX, un gestionnaire voisin du meme plugin peut avoir ete oublie et rester exploitable par un role faible (Subscriber).
- Typical target shape: Plugin WordPress avec plusieurs actions wp_ajax_*/wp_ajax_nopriv_* enregistrees, et un changelog recent mentionnant un correctif d'autorisation sur CE plugin.

## Preconditions

- Plugin WordPress avec plusieurs actions wp_ajax_*/wp_ajax_nopriv_* enregistrees, et un changelog recent mentionnant un correctif d'autorisation sur CE plugin.

## Cheap Probes

- Lister toutes les actions wp_ajax_* enregistrees par le plugin (grep add_action dans le code si accessible, ou enumeration des actions connues); tester chaque action avec un compte de role minimal (Subscriber) sans nonce correct.

## Telltale Evidence

- Une action du meme plugin repond avec succes (donnees ou effet de bord) a un compte de role minimal alors que d'autres actions voisines renvoient une erreur d'autorisation/nonce.

## Escalation Order

1. Identifier toutes les actions AJAX enregistrees par le plugin cible.
2. Tester chacune avec le role le plus faible possible (Subscriber) et sans nonce valide si possible.
3. Comparer les reponses entre actions: celles qui echouent (controle present) vs celles qui reussissent (controle oublie).
4. Documenter precisement l'action et le parametre declenchant l'effet de bord (lecture de donnees sensibles, creation de contenu, etc.).

## Common Mistakes

- Tester uniquement l'action principale documentee dans un rapport de vuln existant sans auditer les actions AJAX voisines du meme plugin apres un correctif partiel.

## Payload Shapes

```text
POST /wp-admin/admin-ajax.php  action=<plugin_action>&type=<check|sync>&user_id=me
```

## Related Writeups

- zoom-wp-plugin-vczapi-sync-user-missing-auth

## Skill Impact

- Related skill: web-triage (WordPress): ajouter 'auditer systematiquement tous les hooks wp_ajax_* d'un plugin apres un changelog de securite partiel' comme etape de reconnaissance.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
