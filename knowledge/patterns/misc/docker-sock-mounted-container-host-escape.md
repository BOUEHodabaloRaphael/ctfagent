---
doc_kind: pattern
title: "Socket Docker monte en RW dans un conteneur = evasion complete vers l'hote + tous les conteneurs voisins"
category: misc
slug: docker-sock-mounted-container-host-escape
created: 2026-10-30
status: active
tags:
  - docker-sock
  - container-escape
  - host-escape
  - koth
  - nctf26-prep
  - privilege-escalation
chain_summary: "/var/run/docker.sock accessible en root dans un conteneur permet de parler a l'API Docker du daemon HOTE: lister/exec dans tous les conteneurs voisins, et creer un nouveau conteneur avec bind-mount de / pour une evasion complete vers le filesystem physique."
---
# Socket Docker monte en RW dans un conteneur = evasion complete vers l'hote + tous les conteneurs voisins

## Chain Summary

- One-line chain: /var/run/docker.sock accessible en root dans un conteneur permet de parler a l'API Docker du daemon HOTE: lister/exec dans tous les conteneurs voisins, et creer un nouveau conteneur avec bind-mount de / pour une evasion complete vers le filesystem physique.

## Preconditions

- Acces root (meme local au conteneur, ex. via CVE locale type PwnKit) a une machine ou /var/run/docker.sock existe avec des permissions permettant l'ecriture (souvent srw-rw---- root:docker ou similaire).

## Cheap Probes

- ls -la /var/run/docker.sock apres tout acces root dans un conteneur Linux -- reflexe systematique, ce n'est PAS visible sans le chercher explicitement.

## Telltale Evidence

- La simple presence du fichier socket avec des droits root suffit; curl --unix-socket ou un client HTTP maison via socket.AF_UNIX confirme l'acces en listant GET /containers/json?all=true.

## Escalation Order

1. Verifier la presence de /var/run/docker.sock des qu'un acces root (meme conteneurise) est obtenu.
2. Si curl est absent sur la cible, ecrire un mini client HTTP Python (http.client.HTTPConnection avec connect() surcharge pour utiliser un socket.AF_UNIX) -- aucune dependance externe necessaire.
3. GET /containers/json?all=true pour lister tous les conteneurs du daemon (pas seulement ceux du meme projet docker-compose), avec leurs IDs, IPs internes, et montages.
4. POST /containers/{id}/exec puis POST /exec/{id}/start pour executer des commandes EN ROOT dans n'importe quel conteneur voisin liste -- contourne completement tout 'durcissement' applicatif fait par un adversaire sur ce conteneur, puisqu'on ne passe pas par son service, on passe par le daemon.
5. Pour une evasion complete vers l'HOTE PHYSIQUE (pas juste les conteneurs voisins): POST /containers/create avec HostConfig.Binds=['/:/mnt_host'] (et idealement NetworkMode='host') sur une image deja presente localement, puis start + exec dedans. Tout le filesystem hote devient lisible/ecrivable sous /mnt_host.
6. Chercher immediatement sur l'hote les mecanismes de 'verite' qui ne sont JAMAIS exposes dans les conteneurs applicatifs: fichiers de score/flag directement dans /root, services systemd (/etc/systemd/system/*.service) qui tournent en root et lisent des fichiers locaux.
7. Si une action critique (ex: chattr +i) echoue avec 'Operation not permitted' dans le conteneur bind-mounte standard (capabilities Linux limitees meme en root conteneur), recreer un conteneur avec HostConfig.Privileged=true pour obtenir toutes les capabilities (dont CAP_LINUX_IMMUTABLE).

## Common Mistakes

- Se limiter a explorer uniquement SON PROPRE conteneur une fois root, sans verifier systematiquement la presence de docker.sock -- c'est souvent le vecteur qui donne acces a TOUT le reste de l'infra (conteneurs voisins + hote), bien au-dela de ce que l'enonce/l'app web suggere.

## Payload Shapes

```text
import socket, http.client, json\nclass UnixHTTPConnection(http.client.HTTPConnection):\n    def connect(self):\n        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)\n        self.sock.connect('/var/run/docker.sock')\n# puis GET /containers/json, POST /containers/{id}/exec, POST /containers/create avec Binds=['/:/mnt_host']
```

## Related Writeups

- thm-koth-h1hard-docker-sock-host-escape

## Skill Impact

- Related skill: pwn-triage/web-triage: ajouter 'verifier /var/run/docker.sock des que root est obtenu dans tout environnement suspecte d'etre conteneurise' comme etape reflexe systematique.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
