---
doc_kind: pattern
title: "DFA (Differential Fault Analysis) sur AES — modele Piret-Quisquater, oracle correct+faute"
category: crypto
slug: aes-dfa-fault-attack-piret-quisquater
created: 2026-10-30
status: active
tags:
  - legacy-memory-migration
  - nctf26-prep
  - aes
chain_summary: "Un service qui fournit systematiquement un chiffrement AES correct ET un chiffrement faute (un octet XORe juste avant MixColumns du round Nr-1) pour le meme plaintext permet de retrouver la cle complete via DFA, sans connaitre le plaintext ni bruteforcer."
---
# DFA (Differential Fault Analysis) sur AES — modele Piret-Quisquater, oracle correct+faute

## Chain Summary

- One-line chain: Un service qui fournit systematiquement un chiffrement AES correct ET un chiffrement faute (un octet XORe juste avant MixColumns du round Nr-1) pour le meme plaintext permet de retrouver la cle complete via DFA, sans connaitre le plaintext ni bruteforcer.

## Preconditions

- Service reseau chiffrant avec AES (souvent tiny-AES-c ou equivalent) qui fournit deux sorties pour le meme plaintext: le chiffrement correct et un chiffrement avec une faute injectee a un endroit fixe du dernier/avant-dernier round.

## Cheap Probes

- Verifier dans le code source fourni (souvent donne) l'endroit exact ou la faute XOR est appliquee dans la boucle de rounds — si c'est juste avant MixColumns du round Nr-1, c'est le modele Piret-Quisquater classique.

## Telltale Evidence

- La faute se diffuse en un bloc de 4 octets (une rangee/diagonale) a l'entree du dernier round, affectant un pattern previsible de positions de sortie.

## Escalation Order

1. Confirmer le modele de faute exact en lisant le point d'injection dans le code source fourni.
2. ATTENTION: des librairies toutes faites pour ce modele (ex. phoenixAES) peuvent echouer SILENCIEUSEMENT (candidats qui ne convergent jamais) si l'implementation cible utilise une convention memoire differente de celle supposee (FIPS column-major vs tiny-AES-c row-major transpose: idx=row*4+col au lieu de idx=row+4*col).
3. Pour diagnostiquer: patcher le binaire fourni pour afficher la vraie cle (recompile), verifier empiriquement que les positions de bytes affectees par la faute matchent l'hypothese sur ~20 echantillons.
4. Si la lib toute faite ne converge jamais, reecrire le solveur DFA a la main a partir des equations physiques: deriver les 4 groupes de positions affectees selon la convention REELLE du binaire, les valider empiriquement, puis pour chaque paire (correct,faulty) d'un groupe, brute-forcer les 4 octets de cle du dernier round via une table precalculee InvSBox(Out_correct[j]^K) XOR InvSBox(Out_faulty[j]^K) indexee par resultat.
5. Accumuler (intersection d'ensembles) les candidats a travers PLUSIEURS echantillons du meme groupe — fonctionne meme avec un plaintext different a chaque round car la cle est fixe.
6. Une fois les 16 octets du dernier round-key recuperes, inverser le key schedule AES pour remonter a la cle maitre.
7. Piege: verifier le nombre REEL de blocs envoyes par le service (diviser la longueur totale par 16), pas seulement ce que suggere une boucle lue dans le code source fourni — le deploiement reel peut avoir un buffer different.
8. Valider le solveur offline (binaire patche affichant la vraie cle) avant d'attaquer le vrai serveur reseau.

## Common Mistakes

- Faire confiance aveuglement a une librairie DFA toute faite (phoenixAES) sans valider empiriquement sa convention memoire contre l'implementation reelle cible — elle peut echouer silencieusement sans message d'erreur clair.

## Payload Shapes

```text
Table precalculee: pour K in 0..255: table[InvSBox(Out_correct[j]^K) XOR InvSBox(Out_faulty[j]^K)] = K
```

## Related Writeups

- N/A

## Skill Impact

- Related skill: Candidat pour un futur crypto-triage dedie: DFA sur AES est une technique avancee mais reconnaissable des qu'un oracle fournit (correct, faulty) pour le meme plaintext.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
