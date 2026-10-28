# PWN#Beta

- Plateforme : CTFd auto-hébergé `ctf.bugpwn.com`, compétition **battleCTF Qualifier**.
- Catégorie `pwn`, 192 pts (décroissant, decay=2, min=40), 5 solves au moment de l'analyse.
- Énoncé exact : *"Get a shell on the remote host and read the flag."*
- Cible réseau : `169.58.126.107:5005` (TCP brut).
- `max_attempts: 1` pour la soumission du flag — ne JAMAIS soumettre sans shell confirmé.
- Fichier fourni : `vault` (attachments/vault) — même famille que PWN#Alpha (ARM) et PWN#001 (x86-64) : un serveur "vault keeper" avec prompt nom + message.
