---
doc_kind: pattern
title: "Methodologie King of the Hill — validee (2 victoires / 3 rounds TryHackMe)"
category: misc
slug: koth-methodology-thm-validated
created: 2026-10-30
status: active
tags:
  - koth
  - attack-defense
  - nctf26
  - methodology
  - competition-prep
chain_summary: "Des Status:Running, nmap -p- complet immediat (pas de scan partiel, les vecteurs gagnants vivent sur des ports custom), sonder chaque port non-standard en parallele, soumettre chaque flag des qu'il est trouve, ecrire le fichier king/owner des que root est obtenu."
---
# Methodologie King of the Hill — validee (2 victoires / 3 rounds TryHackMe)

## Chain Summary

- One-line chain: Des Status:Running, nmap -p- complet immediat (pas de scan partiel, les vecteurs gagnants vivent sur des ports custom), sonder chaque port non-standard en parallele, soumettre chaque flag des qu'il est trouve, ecrire le fichier king/owner des que root est obtenu.

## Preconditions

- Challenge KOTH actif (TryHackMe, CTFd King-of-the-Hill plugin, ou mecanisme equivalent NCTF): un timer de round, une IP cible qui apparait au debut du round, un mecanisme de 'prise' de la colline (fichier a ecrire ou process a controler), verifie periodiquement par un agent cote plateforme qui attribue des points a qui detient la cible a cet instant.

## Cheap Probes

- Des que le statut passe a Running/actif, lancer immediatement `nmap -Pn -p- --min-rate 3000 --max-retries 1` (scan complet 65535 ports, PAS un scan partiel) — voir koth_auto.sh (src/tools/ctf/).

## Telltale Evidence

- Round 1 perdu (3e place) a cause d'un retard sur l'enumeration des ports applicatifs custom (9001/9002) pendant qu'un concurrent les trouvait plus vite; rounds 2 et 3 gagnes en appliquant strictement l'ordre ci-dessous des le debut.

## Escalation Order

1. Surveiller le statut du round (scheduling, pas de polling serre tant que 'Scheduled').
2. Des 'Running': recuperer l'IP cible et lancer nmap -p- COMPLET immediatement (les backdoors/vecteurs KOTH vivent systematiquement sur des ports non-standards aleatoires: ex. 9001/9002, 15065/16109/46969, 7824/9576/10514/43316 selon la box — un scan qui s'arrete aux ports 'probables' rate le vecteur principal).
3. Sonder en parallele CHAQUE port non-standard trouve (curl HTTP, banner grab TCP brut, FTP/SMB anonyme) sans attendre la fin du scan -sV -sC complet.
4. Des qu'un acces (RCE web, SSH, SQLi) est obtenu: fouiller systematiquement /home/*, /root, mails locaux, historiques bash/mysql, cron, tous les SUID/SGID (find / -xdev ( -perm -4000 -o -perm -2000 )), bases MySQL non-standard.
5. Soumettre CHAQUE flag DES qu'il est trouve, ne jamais accumuler avant de soumettre — le classement bouge vite, un concurrent peut trouver le meme flag en premier.
6. Une fois root (ou acces suffisant): ecrire son pseudo/nom d'equipe dans le fichier king/owner attendu par le mecanisme de la plateforme (chemin et nom a confirmer: strings sur un binaire demon type koth/agent si le nom exact n'est pas documente — voir koth_auto.sh phase 2 qui tente plusieurs candidats: king.txt, owner.txt, flag.txt dans /root, /opt/koth, /var/koth, /srv/koth). ATTENTION: si l'environnement est conteneurise (ps aux ne montre aucun process pour des services pourtant identifies au nmap sur d'autres ports), le VRAI fichier king peut vivre sur l'hote physique, invisible depuis les conteneurs applicatifs — toujours verifier /var/run/docker.sock (voir docker-sock-mounted-container-host-escape) avant de conclure que le king.txt local trouve est le bon.
7. Des la premiere prise confirmee: NE JAMAIS s'arreter a une seule ecriture — lancer immediatement une boucle de reassertion en arriere-plan (voir koth-continuous-king-reassertion-loop) car le King Time cumule determine le classement final, pas l'instant de prise initial. Etre pret a une guerre de verrouillage chattr +i/-i si l'adversaire a aussi un acces privilegie.
8. Apres soumission d'un flag: toujours re-scroller/re-screenshot la page avant de cliquer Submit si le DOM a bouge (un clic a l'aveugle sur une ancienne coordonnee peut manquer le champ — la position du champ de soumission KotH bouge a chaque rechargement du graphique de score).
9. Entre les rounds: revenir sur la page du jeu et verifier si un round 'Scheduled' existe deja; sinon reprogrammer une verification a intervalle raisonnable (10-25 min).

## Common Mistakes

- Avoir decouvert l'enumeration SMB/FTP en premier et neglige de sonder les ports applicatifs custom des le depart — a coute la 1ere place au round 1 face a un adversaire plus rapide sur ces vecteurs. Corrige des le round 2 en scannant TOUS les ports immediatement.

## Payload Shapes

```text
nmap -Pn -p- --min-rate 3000 -T4 --max-retries 1 <IP>  (scan complet, jamais un -p- partiel ou --top-ports)
```

## Related Writeups

- src/tools/ctf/koth_auto.sh (script d'automatisation adapte au format NCTF26)
- knowledge/writeups/misc/thm-koth-h1hard-docker-sock-host-escape.md (round complet valide le 2026-10-30, 1ere place finale 450 vs 390 pts)
- knowledge/patterns/misc/docker-sock-mounted-container-host-escape.md (PRISE: comment trouver le vrai mecanisme king quand il est hors des conteneurs applicatifs)
- knowledge/patterns/misc/koth-continuous-king-reassertion-loop.md (MAINTIEN: boucle de reecriture + guerre de verrouillage chattr)

## Skill Impact

- Related skill: pwn-triage / web-triage: ajouter 'KOTH actif -> nmap -p- complet immediat, jamais partiel' comme premiere action reflexe. Reglement NCTF26 interdit le bruteforce/DoS: koth_auto.sh ne fait que des sondes anonymes/par defaut, pas de bruteforce de mot de passe. Ce pattern couvrait seulement la PRISE de colline (phases 1-2); le MAINTIEN (King Time) est desormais couvert par les 2 patterns lies ci-dessus, comble suite a un round de prep NCTF26 ou le maintien a ete le facteur decisif.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
