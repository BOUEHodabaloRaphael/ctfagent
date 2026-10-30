---
doc_kind: pattern
title: "KotH: tenir la couronne est un combat CONTINU, pas une ecriture unique — boucle de reassertion + verrouillage"
category: misc
slug: koth-continuous-king-reassertion-loop
created: 2026-10-30
status: active
tags:
  - koth
  - king-time
  - persistence
  - nctf26-prep
  - automation
chain_summary: "Ecrire king.txt une seule fois ne suffit jamais face a un adversaire actif: il faut (1) une boucle de reecriture a intervalle court (15-20s) en arriere-plan, (2) un conteneur de travail PERSISTANT (sleep infinity + restart always, jamais une duree finie), et (3) etre pret a une guerre de verrouillage chattr +i/-i via un conteneur privilegie si l'adversaire a aussi acces a l'hote."
---
# KotH: tenir la couronne est un combat CONTINU, pas une ecriture unique — boucle de reassertion + verrouillage

## Chain Summary

- One-line chain: Ecrire king.txt une seule fois ne suffit jamais face a un adversaire actif: il faut une boucle de reecriture a intervalle court en arriere-plan, un conteneur de travail persistant, et une guerre de verrouillage chattr si l'adversaire a aussi acces host.

## Preconditions

- Format KotH ou le King Time (duree cumulee de detention de la colline) compte dans le score final, avec un ou plusieurs adversaires actifs en parallele qui peuvent reprendre la colline a tout moment.

## Cheap Probes

- Des la premiere prise de couronne confirmee (badge 'Roi' + 'Changements du roi' incremente sur le scoreboard), verifier IMMEDIATEMENT si le fichier king peut etre verrouille (chattr +i) -- et si l'adversaire peut potentiellement le reprendre, mettre en place une boucle de reecriture avant de passer a autre chose.

## Telltale Evidence

- Le badge 'Roi' affiche de maniere instantanee peut montrer l'adversaire meme quand le TABLEAU DE CLASSEMENT final (King Time cumule, Points) nous donne gagnant -- ne pas paniquer sur l'affichage temps reel seul, suivre le tableau de points qui est ce qui compte reellement au final.

## Escalation Order

1. Des la premiere prise confirmee, lancer une boucle en arriere-plan (ex. Bash run_in_background) qui re-ecrit le fichier king toutes les 15-20 secondes -- jamais une seule ecriture one-shot, le temps de detention cumule (King Time) est ce qui determine le classement final, pas l'instant de prise initial.
2. Si le mecanisme de prise necessite un conteneur de travail (ex. via docker exec), le creer avec une commande qui ne meurt JAMAIS (Cmd=['sleep','infinity'], PAS Cmd=['sleep','600'] ou toute duree finie) + RestartPolicy=always -- un conteneur a duree de vie finie va mourir en plein milieu de la boucle et faire echouer silencieusement toutes les reecritures suivantes ('Container is not running').
3. Surveiller le log de la boucle (ou son equivalent) periodiquement, pas juste la lancer et l'oublier -- une erreur 'Operation not permitted' sur une ecriture signale typiquement que l'adversaire a verrouille le fichier (chattr +i) avec un acces plus privilegie que le notre.
4. Si le fichier king devient verrouille (lsattr montre le flag immutable 'i') et qu'on ne peut pas le lever avec les droits courants, escalader vers un contexte avec plus de capabilities (ex. conteneur Docker --privileged si docker.sock est accessible) pour pouvoir faire chattr -i, reprendre, puis RE-verrouiller nous-memes avec chattr +i -- la guerre de verrouillage se gagne par qui a le plus haut niveau de privilege, pas par la vitesse seule.
5. A l'approche de la fin du round (dernieres minutes), augmenter la frequence de verification manuelle et refaire une reecriture immediate a chaque check -- les dernieres secondes sont souvent les plus disputees et peuvent faire basculer le classement final.

## Common Mistakes

- Considerer la prise de couronne comme 'terminee' apres une seule ecriture reussie, et passer a autre chose sans boucle de maintien -- c'est exactement ce qui permet a un adversaire de reprendre la colline en quelques secondes sans qu'on s'en aperçoive. Utiliser une duree de conteneur finie (sleep N) pour un processus cense tourner toute la duree du round.

## Payload Shapes

```text
while true; do <commande de reecriture + relock> ; sleep 20; done  (en arriere-plan, avec log pour diagnostiquer les echecs)
```

## Related Writeups

- thm-koth-h1hard-docker-sock-host-escape

## Skill Impact

- Related skill: ctf-solver-profile / pwn-triage: le pattern koth-methodology-thm-validated.md existant couvrait la PRISE de la colline (phase 1/2) mais pas son MAINTIEN -- ce pattern comble ce manque explicitement identifie lors d'un round NCTF26 de preparation.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
