---
doc_kind: workspace-notes
id: nctf26-relay
title: "relay (NCTF26 #267)"
category: chains
status: abandoned-solved-by-teammate
tags:
  - nctf26
  - chains
  - team_instance
  - blocked-quota
---
# Notes

**RÉSOLU PAR UN COÉQUIPIER — abandonné sans suite par cet agent (ordre du coordinateur,
2026-11-06 ~20h15). Pas de doublon de travail.**

État où cet agent s'est arrêté (preuve utile si besoin de reprendre plus tard) :

- Challenge lu (`GET /api/v1/challenges/267`) : type CTFd `team_instance` (plugin
  `team_instancer`), flag class `team_hmac`, access mode `https`. Détails complets dans
  `challenge.md`.
- Mécanisme d'instance reverse-engineered depuis les assets JS du plugin (voir
  `artifacts/instancer_status.py` et `artifacts/instancer_spawn2.py`) :
  - `GET /plugins/team_instancer/status?challenge_id=267`
  - `POST /plugins/team_instancer/spawn` avec header `CSRF-Token` + body
    `{"challenge_id":267}`
- Blocage rencontré : spawn renvoyait systématiquement
  `429 {"error":"Maximum 2 instances simultanees par equipe.","success":false}`, alors que
  les 15 challenges `team_instance` visibles dans le catalogue rapportaient tous
  `status:"none"` pour notre équipe (voir `artifacts/instancer_status_scan.py`). Hypothèse
  retenue : un coéquipier avait déjà une instance active sur ce challenge (ou un autre,
  masqué pour moi) — cohérent avec la confirmation reçue que le challenge est résolu côté
  équipe.
- Jamais atteint la page d'accueil du service (protocole TLV/hex, écho) ni construit de
  trame — aucune tentative d'exploitation faite, aucun flag vu.
- Pas de hint déverrouillé par cet agent.

- hypotheses: (abandonnées, cf. ci-dessus)
- validated findings: mécanisme team_instancer confirmé fonctionnel (spawn/status/renew/destroy) ;
  quota de 2 instances/équipe partagé entre tous les challenges `team_instance`.
- dead ends: aucune instance active trouvée dans les 15 challenges connus malgré le quota plein
  -> probablement l'instance du coéquipier qui a résolu le challenge.
