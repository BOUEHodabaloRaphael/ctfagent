---
doc_kind: writeup
title: "TryHackMe KotH H1:Hard — Docker socket host escape + king.txt persistence war"
category: misc
slug: thm-koth-h1hard-docker-sock-host-escape
created: 2026-10-30
status: solved
tags:
  - koth
  - docker-escape
  - nctf26-prep
  - live-round
  - privilege-escalation
source: "TryHackMe King of the Hill (jeu public, machine H1:Hard)"
target: "10.10.124.38 — 4 conteneurs Docker (c1-c4) + hote physique"
---
# TryHackMe KotH H1:Hard — Docker socket host escape + king.txt persistence war

## Challenge Summary

- Source: TryHackMe King of the Hill (jeu public, machine H1:Hard)
- Target: 10.10.124.38 — 4 conteneurs Docker (c1-c4) + hote physique
- Goal: Prendre et tenir la colline face a un adversaire deja engage, en conditions de competition reelle (prep NCTF26).

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Des 'Running': nmap -p- complet -> 7 ports (22,80,81,82,2222,8888,9999), plusieurs non-standards.
2. Port 8888 (Flask/Werkzeug) expose /apps -> enumeration -> app4 nomme '/users' (indice direct) -> GET /users -> credentials en clair davelarkin:totallysecurehuh.
3. SSH sur le port 2222 avec ces creds -> shell utilisateur standard, 1er flag local (container4_flag.txt, world-readable).
4. pkexec version 0.105 (vulnerable PwnKit CVE-2021-4034) -> root confirme via exploit public (berdav/CVE-2021-4034), execute non-interactivement via stdin pipe (le shell spawn attend sur stdin, jamais de timeout si on pipe des commandes + exit).
5. ps aux en root ne montre AUCUN process Apache/nginx local malgre nmap qui identifie ces services sur 80/81/82 -> indice que ce sont des CONTENEURS SEPARES, pas des process locaux.
6. Port 80 (Server Manager Login) et port 81/82 (sites web) deja defaces par l'adversaire ('HACKED BY BLACKLUCIFERTZ... locked down') au moment ou on les teste -> credential reuse SSH echoue sur les IP internes Docker.
7. ls -la /home/davelarkin/ revele /var/run/docker.sock monte en RW dans notre conteneur -> acces direct a l'API Docker via un script Python (socket Unix + http.client), curl absent de la cible.
8. GET /containers/json?all=true sur le socket -> liste les 4 conteneurs du projet docker-compose 'hackerone' (c1=port80, c2=port81, c3=port82, c4=nous) avec leurs IDs complets.
9. docker exec (API POST /containers/{id}/exec puis /exec/{id}/start) dans c1/c2/c3 EN ROOT, contournant completement le 'lockdown' applicatif de l'adversaire (on ne passe pas par son service web patche, on passe par le daemon Docker directement) -> 3 flags supplementaires trouves et extraits.
10. Port 9999 (Golang, affiche le nom du king actuel sur TOUTE route) n'apparait dans AUCUN des 4 conteneurs listes par l'API Docker -> signal qu'un 5e mecanisme existe, probablement sur l'hote physique lui-meme, pas dockerise.
11. Creation d'un NOUVEAU conteneur via l'API Docker avec HostConfig.Binds=['/:/mnt_host'] (bind-mount de la racine de l'hote) -> evasion complete vers le filesystem HOTE PHYSIQUE.
12. Decouverte du vrai mecanisme: /etc/systemd/system/koth.service (ExecStart=/usr/bin/koth, User=root) lit /root/king.txt sur L'HOTE -> ce fichier est totalement invisible/inaccessible depuis les 4 conteneurs applicatifs classiques.
13. Ecriture de /mnt_host/root/king.txt = notre pseudo -> prise de couronne confirmee en live sur le scoreboard ('Changements du roi' incremente, badge Roi change).
14. chattr +i echoue dans le premier conteneur hostescape (capacite CAP_LINUX_IMMUTABLE absente meme en root conteneur) -> verrouillage impossible de notre cote initialement.
15. L'adversaire, lui, reussit a verrouiller /root/king.txt en immutable (acces host reel de son cote) -> nos ecritures suivantes echouent 'Operation not permitted'.
16. Creation d'un conteneur PRIVILEGIE (HostConfig.Privileged=true) via l'API Docker -> toutes les capabilities Linux disponibles, y compris CAP_LINUX_IMMUTABLE -> chattr -i reussit, on reprend le fichier, on le re-verrouille nous-memes avec chattr +i.
17. Boucle de maintien en arriere-plan (reecriture toutes les 20s) pour maximiser le King Time face aux reprises adverses successives ('Changements du roi' est monte a 5 au total).
18. PIEGE operationnel decouvert: un conteneur Docker cree avec Cmd=['sleep','600'] (duree finie) MEURT au bout de 600s, rendant tout exec() ulterieur impossible ('Container is not running') -> toujours utiliser Cmd=['sleep','infinity'] + RestartPolicy=always pour un conteneur de travail de longue duree.
19. Resultat final (etat 'Complete'): 1er au classement avec 450 pts / King Time 30, contre 390 pts / King Time 24 pour l'adversaire, malgre un badge d'affichage instantane qui montrait encore l'adversaire a la toute derniere seconde du round.

## Key Evidence

- API Docker via socket Unix (http.client custom connect()) pour exec/create/start de conteneurs; decouverte de /etc/systemd/system/koth.service + /usr/bin/koth sur l'hote comme vrai mecanisme de verification du king; bataille chattr +i/-i resolue par conteneur privilegie.

## Dead Ends

- Piege 'curl absent sur la cible' -> utiliser python3 http.client/socket natif. Piege conteneur a duree de vie finie (sleep N) qui meurt et bloque tout exec() ulterieur.

## Payloads And Commands

```text
voir src/tools/ctf/koth_auto.sh et les patterns associes pour les scripts
```

## Flag / Outcome

- 5/5 flags trouvees et soumises. Rang final 1/2 (450 pts vs 390), King Time
  30 vs 24. Round termine "Complete" avec nous en tete du classement final,
  malgre un badge "Roi" instantane qui affichait l'adversaire a la toute
  derniere seconde (repris juste apres notre derniere ecriture).

## Reusable Lessons

- Preparation KotH NCTF26 complete: methodologie scan, chasse aux flags, ET maintien de couronne — ce dernier point manquait completement avant cette session et est desormais couvert par 2 nouveaux patterns dedies.

## Pattern Candidates

- docker-sock-mounted-container-host-escape
- koth-continuous-king-reassertion-loop
