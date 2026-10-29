---
doc_kind: writeup
title: "HTB Layover (session bloquee, RCE Yii2/Craft non confirmee)"
category: web
slug: htb-layover-blocked-yii2
created: 2026-10-29
status: draft
tags:
  - web
  - craft-cms
  - yii2
  - session-bloquee
  - gadget-chain
  - impersonation-blocked
source: HackTheBox
target: "Craft CMS (Yii2) portail editeur, international.htb"
---
# HTB Layover (session bloquee, RCE Yii2/Craft non confirmee)

## Challenge Summary

- Source: HackTheBox
- Target: Craft CMS (Yii2) portail editeur, international.htb
- Goal: STATUT: ECHEC/BLOQUE (aucun flag obtenu). Acces WiFi + auth editeur Craft CMS obtenus, mais la chaine de RCE visee (gadget d'evenement Yii2 via FieldLayout behavior) echoue - write-up source utilise contenait des erreurs.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Connexion WiFi (SSID dedie) -> route vers le reseau interne.
2. Resolution du portail Craft CMS, confirmation HTTP 200.
3. Login reussi en editeur (userId=2), extraction du token CSRF.
4. Tentative d'exploitation d'un gadget Yii2 via element-search/search (manipulation condition FieldLayout + behavior) - oracle base sur le champ JSON 'name' de l'erreur.
5. ECHEC: la cle doit etre 'class' (pas '__class') pour la condition; l'evenement generique 'on *' n'est jamais dispatche par Yii2 Component::trigger() sur ce build; 'on afterInit' s'enregistre mais ne se declenche jamais.
6. Voie 'impersonation admin' testee et fermee: instance Craft en edition Solo (users/impersonate reserve Pro+, erreur 'Wrong edition').

## Key Evidence

- Tableau payload/resultat (condition "class"+fieldLayouts->200 vs "__class"->500; "on afterInit" jamais declenche); 400 "Wrong edition" sur users/impersonate; aucune connexion recue sur les listeners nc/recv.py.

## Dead Ends

- BLOQUE: la chaine de gadget Yii2 visee ne fonctionne pas sur ce build (deux etapes du write-up source etaient erronees). Impersonation admin fermee (edition Solo). Aucun flag obtenu malgre acces editeur confirme.

## Payloads And Commands

```text
Requetes JSON POST vers actions Craft/Yii2 (admin/actions/element-search/search) manipulant la cle 'class'/comportements 'on <event>' pour viser un gadget d'evenement -> call_user_func.
```

## Flag / Outcome

- AUCUN - session bloquee, a ne pas reprendre a l'identique sans nouvelle piste (voir regle blackbox-exhausted de ctf-solver-profile).

## Reusable Lessons

- Ne pas faire confiance a un write-up externe sans verifier chaque etape; utiliser un oracle HTTP base sur le nom court de l'exception JSON renvoyee (400/404/message) pour confirmer l'existence d'une route et affiner un gadget pas-a-pas sans acces au code source.

## Pattern Candidates

- Pas de nouveau pattern (echec, pas de technique confirmee) - uniquement la lecon diagnostic.
