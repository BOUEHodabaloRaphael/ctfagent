---
doc_kind: pattern
title: "BruteShark CLI — extraction automatique de credentials/fichiers/DNS depuis un PCAP"
category: forensics
slug: bruteshark-pcap-credential-extraction
created: 2026-11-10
status: active
tags:
  - pcap
  - network-forensics
  - credential-hunting
  - ntlm
  - helper-tool
chain_summary: "brutesharkcli (apt, deja installe) parse un ou plusieurs .pcap/.pcapng et extrait automatiquement en un seul passage les credentials en clair (IMAP/HTTP Basic/FTP/...), les hashs NTLM/NTLMv2 pretes a crack/relay, les fichiers transferes, la carte reseau et les requetes DNS -- plus rapide qu'un filtrage tshark manuel pour une premiere passe credential-hunting sur un PCAP de challenge forensics/reseau."
---
# BruteShark CLI — extraction PCAP

## Chain Summary

- One-line chain : des qu'un `.pcap`/`.pcapng` est donne (challenge forensics/reseau),
  lancer `TERM=linux brutesharkcli -m Credentials,FileExtracting,NetworkMap,DNS -i
  <fichier> -o <dossier_sortie_existant>` pour une triage rapide avant de plonger
  dans tshark/Wireshark manuellement -- l'outil fait en une commande ce qui prendrait
  plusieurs filtres tshark pour chaque protocole (IMAP, SMB/NTLMSSP, HTTP Basic,
  Kerberos, FTP, VoIP).

## Preconditions

- Fichier(s) `.pcap`/`.pcapng` disponible(s) en lecture locale.
- `bruteshark` installe (paquet apt Kali, deja fait le 2026-11-10 : `sudo apt-get
  install -y bruteshark`, depend de `dotnet-runtime-6.0` deja present).
- **Piege terminfo connu** : lance tel quel, le CLI echoue avec `Fatal Error: The
  terminfo database is invalid.` dans certains environnements (observe dans ce
  sandbox). Fix : prefixer `TERM=linux` (ou `TERM=xterm`) a la commande.
- **Le dossier de sortie (`-o`) doit deja exister** avant de lancer la commande --
  sinon `ERROR: Could not find a part of the path '.../BruteShark Network Map.json'`
  apres un traitement qui semble pourtant reussi (`Finished processing file`). Faire
  `mkdir -p <dossier_sortie>` d'abord.

## Cheap Probes

- `TERM=linux brutesharkcli --help` pour confirmer l'install et lister les modules
  disponibles : `Credentials`, `FileExtracting`, `NetworkMap`, `DNS`, `Voip`.
- Lancer d'abord `-m Credentials` seul sur un petit pcap pour voir rapidement s'il y
  a des credentials en clair avant de lancer les modules plus lourds
  (`FileExtracting` peut extraire beaucoup de fichiers sur un gros pcap).

## Telltale Evidence

- Mode `Credentials` detecte et affiche en direct sur stdout chaque hit trouve,
  format `Found: <Type>: <src>=><dst>(<protocole>) => <valeur>` pour le texte clair
  (ex: IMAP) et `Found: Hash: <src>=><dst> (NTLMSSP) NTLMv2 => <hash complet
  pret pour hashcat/john ou ntlmrelayx>` pour les hashs NTLM captures dans un
  handshake SMB.
- Testé sur un pcap de challenge CTF reel (`black_canal.pcap`, workspace
  ghost_analysis) : traitement correct, export JSON `Network Map` +
  `Network Nodes Data` + dossier `Files/` meme sans credentials presents dans ce
  pcap specifique (confirme que l'absence de hit n'est pas un echec silencieux).

## Escalation Order

1. `mkdir -p out && TERM=linux brutesharkcli -m Credentials -i capture.pcap -o out`
   -- passe rapide, credentials en clair + hashs NTLM seulement.
2. Si rien ou pour une vue plus large : ajouter `NetworkMap,DNS` pour la topologie
   et les requetes DNS (utile pour reperer un C2/exfil sur un challenge malware/forensics).
3. `FileExtracting` seulement si des fichiers transferes (HTTP/FTP/SMB) sont
   plausibles au vu du trafic -- plus lent, genere potentiellement beaucoup de
   fichiers dans `out/Files/`.
4. Un hash NTLMv2 trouve ici va directement dans hashcat (`-m 5600`) ou john
   (`--format=netntlmv2`), ou sert pour un relay NTLM si le contexte le permet (voir
   patterns AD existants, ex. `double-ntlm-relay-xp-dirtree-mssql-coercion.md`).

## Common Mistakes

- Oublier `TERM=linux` -> echec immediat avant meme de lire le pcap, facile a
  confondre avec un probleme d'installation.
- Oublier de creer le dossier `-o` au prealable -> l'outil dit `Finished processing
  file` (donc semble avoir reussi) puis echoue seulement a l'export JSON -- lire le
  message d'erreur en entier, ne pas s'arreter au `Finished processing`.
- Lancer `FileExtracting` sur un tres gros pcap sans besoin reel -> temps de
  traitement et volume de sortie inutiles; reserver aux cas ou un transfert de
  fichier est un hypothese active.

## Payload Shapes

```bash
mkdir -p /tmp/bs_out
TERM=linux brutesharkcli -m Credentials,FileExtracting,NetworkMap,DNS \
  -i capture.pcap -o /tmp/bs_out
# ou sur un dossier entier de captures :
TERM=linux brutesharkcli -m Credentials -d /chemin/vers/pcaps/ -o /tmp/bs_out
```

## Related

- [`ctf-forensics`](../../../.claude/skills/ctf-forensics/SKILL.md) — section
  reseau/PCAP, reference ce pattern pour la premiere passe credential-hunting.
- [`double-ntlm-relay-xp-dirtree-mssql-coercion`](double-ntlm-relay-xp-dirtree-mssql-coercion.md) —
  suite logique si un hash NTLM capture ici mene a un relay.
