# PWN#Beta — Résumé de transfert (mise à jour après session de reprise)

## Contexte
- Binaire `attachments/vault` : ELF 32-bit **MIPS R3000** (little-endian, O32 ABI, mips32r2), statiquement lié, stripped.
- `checksec` dit "No canary found" — **FAUX**, canari logiciel maison présent.
- Service : `nc 169.58.126.107 5005`. `max_attempts=1` pour le flag.

## Disposition de la pile (fonction vulnérable `fcn.00400a84`)

Offsets relatifs à `fp_orig` = valeur du registre `$fp` **à l'entrée** de `fcn.00400a84` :

```
buffer      = fp_orig + 0x1c      (64 octets)
canary      = fp_orig + 0x5c      (= buffer+64)
saved_fp    = fp_orig + 0x60      (= buffer+68)  <- c'est le $fp DE L'APPELANT (boucle), pas fp_orig !
saved_ra    = fp_orig + 0x64      (= buffer+72)
old_sp      = fp_orig + 0x68      (= buffer+76)  <- sp après "addiu sp,sp,0x68" dans l'épilogue
```

`buf_start = leaked_saved_fp - 0x4c` (fuite via le nom, off-by-one 65/64, cf. version précédente du doc).

### ⚠️ Piège d'arithmétique n°2 (découvert cette session, a fait perdre BEAUCOUP de temps)

Pour un **jump direct** (ra réécrit directement, sans gadget pivot intermédiaire), le `sp` au moment du jump est **`buf_start + 0x4c` (= old_sp), PAS `fp_orig` (= buf_start - 0x1c)** ! L'épilogue original fait `move sp,fp` (avec le VRAI fp_orig, pas encore écrasé) **avant** de charger le nouveau `$fp` depuis `saved_fp`. Toute offset calculée à partir de `fp_orig` pour un gadget atteint SANS passer par un pivot `move sp,fp` est fausse de 0x68 (104) octets. **Toujours utiliser un pivot (`GADGET_PIVOT2`) pour contrôler précisément `sp` avant d'atteindre un gadget qui lit plusieurs registres depuis la pile.**

### ⚠️ Piège n°1 (session précédente, toujours valide)
Ne jamais appeler `struct.pack_into()` deux fois sur le même offset — ça écrase silencieusement le canari si on réutilise l'offset 64 par erreur pour les données d'un gadget suivant.

## `jalr` FONCTIONNE — fausse piste de la session précédente abandonnée

Cette session a prouvé que **`jalr` n'est PAS cassé**. Les échecs précédents venaient à 100% des deux pièges d'arithmétique ci-dessus (écrasement du canari, ou mauvaise base `sp`). Preuve : `MINIMAL_JALR` (`0x4075e8: lw $t9,X($sp); jalr $t9; nop`) atteint via `GADGET_PIVOT2` avec les offsets corrects fonctionne à 100% (`"Enter your name: "` réapparaît).

## Gadgets validés comme FIABLES (testés plusieurs fois, succès reproductible)

```
GADGET_PIVOT2 = 0x400854 :
  move $sp, $fp
  lw   $ra, 0x2c($sp)
  lw   $fp, 0x28($sp)
  addiu $sp, $sp, 0x30
  jr   $ra
```
Chaînable à l'infini via `jr` pur (déjà testé sur 2 hops successifs). Utiliser `$fp` (chargé à l'offset 0x28 de CE hop) pour définir le **prochain** pivot cible, et `$ra` (offset 0x2c) pour le gadget/l'adresse suivante.

```
GADGET4 = 0x408fb8 :
  lw   $a0, 0x3c($sp)
  move $a2, $zero          <- a2 TOUJOURS 0, explicite, fiable
  lw   $t9, 0x24($sp)
  jalr $t9
  move $a1, $s7             <- $s7 NON CONTRÔLÉ (valeur résiduelle, probablement 0 car
                                rien dans la chaîne d'appel ne touche $s7 avant nous —
                                mais 0 == NULL, invalide comme argv pour execve())
```
**Validé fiable pour poser `a0` et `a2=0`.** Reste bloquant : `a1` (= argv pour execve) est forcé à `$s7`, non contrôlable par ce gadget, et NULL/garbage ne fonctionne pas comme argv (`execve` échoue, le process se termine — confirmé par fermeture complète du socket, pas juste un blocage).

## Gadgets testés et qui ÉCHOUENT (cause encore incertaine — PAS un bug d'arithmétique, vérifié)

- `GADGET3 = 0x431f18` (`lw a0,0x54(sp); lw a2,0x50(sp); lw a1,0x58(sp); lw t9,0x2c(sp); sw...; jalr t9; sw...`) — aurait été PARFAIT (a0+a1+a2+t9 tous depuis la pile) mais échoue systématiquement, même testé isolément avec tous les registres à zéro et offsets vérifiés correctement non-conflictuels.
- `GADGET6 = 0x410754` (même famille simplifiée, a0+t9 seulement) — échoue aussi.
- `0x40123c` (a0+a1+t9, mais dépend d'un `$a2` chargé par une instruction PRÉCÉDENT notre point d'entrée — dependency ratée, explique CE cas précis).
- `0x42815c`, `0x4239a0`/`0x423b88` (a1/a2 setters) — clobbers `$a0` en route, ou dépendent d'un `$v0` externe non contrôlé.

**Hypothèse non confirmée** : ces gadgets appartiennent à des fonctions glibc complexes (allocation dynamique, locale/gconv, points d'annulation pthread avec `ll`/`sc`) et pourraient dépendre d'un état de registres (`$s0-$s7`, `$fp`) légitime qu'on ne reproduit pas en sautant au milieu — MAIS `GADGET4` appartient à une fonction qui a EXACTEMENT le même genre de code `ll`/`sc` juste à côté (`0x408e98-0x408eb8`) et fonctionne quand même. La théorie ne tient donc pas complètement. **Piste non explorée : vérifier avec un vrai débogueur (voir plus bas) plutôt que deviner.**

## Bloqueur actuel : poser `a1` (argv) de façon fiable

Aucun gadget trouvé qui pose `a1` depuis la pile sans soit (a) clobber `a0` en route, soit (b) dépendre d'un registre externe non contrôlé, soit (c) appartenir à une des fonctions "qui échouent" ci-dessus pour une raison encore incomprise.

### Piste à tester en priorité en reprise : chaîne à 3 pivots
Utiliser `GADGET_PIVOT2` comme **trampoline rechargeable** (son propre `$fp`, une fois chargé, définit où le PROCHAIN appel à `GADGET_PIVOT2` pivotera) :

1. `GADGET_PIVOT2(P1)` → `$fp` chargé = P2, `$ra` = `GADGET4`
2. `GADGET4` (sp=P1+0x30) : pose `a0="/bin/sh"`, `a2=0`, puis `jalr` → `GADGET_PIVOT2` (atteint via jalr, ce qui est OK, confirmé que ça ne pose pas de problème en soi)
3. `GADGET_PIVOT2` s'exécute À NOUVEAU avec `$fp=P2` (chargé à l'étape 1) → `sp=P2`, charge `$ra` = un gadget "pop a1" (même s'il clobber `a0`, pas grave, on le re-pose après), `$fp` = P3
4. Gadget a1-setter (ex: `0x408f04: lw a1,0x2c(sp); lw t9,0x30(sp); jalr t9; delayslot addiu a0,zero,3`) → pose `a1`, `jalr` → `GADGET_PIVOT2` à nouveau
5. `GADGET_PIVOT2` avec `$fp=P3` → `sp=P3`, charge `$ra` = `GADGET4` à nouveau
6. `GADGET4` RE-pose `a0="/bin/sh"` (écrase le `3` du delay-slot précédent), `a2=0` (redondant), puis `jalr` → **`EXECVE` directement cette fois** (`0x450a7c`)

**Point d'attention** : à l'étape 6, `GADGET4` écrase ENCORE `a1` via son propre delay-slot (`move a1,s7`) ! Il faut soit trouver une variante de `GADGET4` sans cet effet de bord, soit intervertir l'ordre (poser a1 en DERNIER, après le dernier passage par un a0-setter). Pas encore résolu à l'arrêt de cette session.

P1/P2/P3 peuvent tous être des offsets DIFFÉRENTS dans le MÊME buffer de 100 octets (puisque rien ne les écrase entre les étapes, seulement des lectures) — pas besoin de `ret2read` vers `.bss` pour ce plan, sauf si on manque de place.

### Piste alternative : ret2read vers `.bss` confirmée fonctionnelle
Rediriger `saved_ra` vers `0x400b40` (bloc `addiu v0,fp,0x1c; move a1,v0; addiu a2,zero,0x64; move a0,zero; lw t9,-0x7f7c(gp); jalr t9` dans `fcn.00400a84`, utilisé normalement pour lire le "message") avec `fp` pointant vers une zone de notre choix (`TARGET_ADDR - 0x1c`) **FAIT RÉELLEMENT APPELER `read()` avec succès** (le socket reste bloqué en attente, confirmé via `select()`). Permet d'écrire un DEUXIÈME payload de 100 octets n'importe où. Nécessite de restaurer `fp+0x10` = `gp` réel (`0x4a9c60`) pour que le code APRÈS le `read()` (impression + check canari) ne crashe pas — testé, fonctionne SI on reproduit toute la structure canari/fp/ra dans le 2e payload (comme un nouvel overflow "virtuel"). Donne un espace quasi illimité en chaînant plusieurs rounds, si le plan à 3 pivots ci-dessus manque de place.

## Adresses utiles (fixes, no PIE)

| Élément | Adresse |
|---|---|
| Fonction vulnérable `fcn.00400a84` | `0x400a84` |
| Point de ré-entrée boucle (`"Enter your name"`) | `0x400c18` |
| Bloc `read(message)` dans fcn.00400a84 (ret2read) | `0x400b40` |
| `GADGET_PIVOT2` (move sp,fp; ra@0x2c; fp@0x28; frame 0x30) | `0x400854` |
| `GADGET4` (a0@0x3c, a2=0 explicite, t9@0x24 ; a1=s7 forcé) | `0x408fb8` |
| `syscall.execve` wrapper | `0x450a7c` |
| Chaîne `"/bin/sh"` (.rodata) | `0x4729a4` |
| `gp` (constante globale) | `0x4a9c60` |
| GUARD_PTR_SLOT (contient l'adresse réelle du canari) | `0x4a1c80` → valeur fixe `0x49f448` |

## Ce qui est CONFIRMÉ déterministe (pas d'ASLR observée)
`saved_fp` leaké = **toujours `0x40800c48`** sur tous les tests de cette session (dizaines de connexions). Le canari change par contre à chaque connexion (normal, aléatoire par processus) — toujours le relire à chaque tentative.

## Recommandation forte pour la prochaine reprise
**Obtenir un accès GDB réel** (via qemu-system-mips avec un rootfs, ou toute autre méthode) réglerait en quelques minutes ce qui a pris des heures de essais empiriques à l'aveugle. En particulier pour comprendre POURQUOI `GADGET3`/`GADGET6` échouent alors que `GADGET4` (fonction similaire) fonctionne — un simple `info registers` au moment du crash trancherait immédiatement.

## Fichiers
- `attachments/vault` — binaire original.
- `exploit/exploit_beta.py` — script d'exploit (utilise l'ANCIENNE approche GADGET2/GADGET3, À REFAIRE avec GADGET4 + plan à 3 pivots ci-dessus).
- `exploit/probe_offset.py`, `gadget_search.py` — scripts de sondage/recherche de gadgets (toujours valides).

## Ne PAS faire
- Ne pas soumettre de flag sans shell confirmé (`max_attempts=1`).
- Ne pas re-tester `qemu-mipsel` user-mode (déjà testé, échoue systématiquement).
- Ne pas réutiliser le même offset `struct.pack_into` deux fois sans vérifier — toujours imprimer le layout final avant envoi.

## Tentative supplémentaire testée (cette session, sans succès)
- `GADGET4` → `fcn.00450ab0` (helper "/bin/sh -i") avec `a0="-i"`, `a1=$s7` (non contrôlé), `a2=0` : échoue aussi (fermeture socket). `$s7` ne pointe donc probablement pas vers une mémoire valide/déréférençable, ou le crash a une autre cause. **`$s7` doit être fuité/déterminé avec certitude avant de perdre plus de temps à deviner** — par exemple en trouvant un gadget `move $a0,$s7` combiné à un appel d'impression, pour le voir apparaître dans la sortie réseau.

## STATUS CHECK (2026-10-25 15:11 UTC)
- Platform metadata (id=23): value=118 (down from 192 recorded previously — normal decay),
  **solves=42** (up sharply from the "5 solves" recorded at time of earlier analysis — strong
  signal the challenge is solvable and many teams have cracked it since), solved_by_me=False,
  attempts=0, state=visible. connection_info `169.58.126.107 5005` unchanged, no new files.
- Blocker unchanged from `metadata.json`: CFI-like remote landing check blocks jumps to code never
  executed by normal control flow; last working theory needs real GDB/debug access to the deployed
  binary, which we don't have.
- Not re-attempting this session per instructions (blocked 3 sessions already, no obvious new
  lead in HANDOFF beyond "get real debug access"). Given 42 solves now vs 5 before, if the user
  wants to revisit, asking in Discord for a hint/writeup-style nudge (now that many teams solved
  it) is probably higher-value than more blind gadget hunting.
- Most promising next concrete step: ask in the CTF Discord for a nudge now that 42 teams have
  solved it, since that's cheaper than more blind MIPS ROP guessing without a debugger.

## MISE À JOUR MAJEURE (session de reprise #2) — jalr confirmé NON cassé, mystère persiste

### Percée : debug local réel obtenu
`gdb-multiarch` installé + `qemu-mipsel -g <port>` (gdbserver mode) + patch du segment `PT_MIPS_ABIFLAGS`
(mis à `PT_NULL`) permet un VRAI débogage pas-à-pas de ce binaire MIPS, en contournant le stub
d'entrée obfusqué (`entry0`, décode XOR vers une adresse invalide côté qemu local — raison non
élucidée, mais sans rapport avec le reste) en forçant `$pc`/`$t9` directement dans `fcn.00400a84`.

**Découverte critique n°1** : les gadgets `jalr`-based ont souvent une instruction
`lw $gp, OFFSET($sp)` **après** le `jalr`, qui recharge `gp` depuis une case que la fonction
originale aurait remplie à son vrai prologue — case qu'on ne remplit JAMAIS en ROP pur. Pour
`GADGET4` (`0x408fb8`), c'est `lw $gp, 0x18($sp)`, **mais seulement si on repasse par ce point**
(ex: appel à `free()` qui retourne normalement). Si la cible du `jalr` DIVERGE complètement
(ex: `LOOP_REENTRY` à `0x400c18`, qui fait `bal fcn.00400a84` sans jamais revenir), ce rechargement
n'est jamais exécuté et n'a aucune importance.

**Découverte critique n°2 — validée via débogueur réel, pas une supposition** : la chaîne
`GADGET_PIVOT2(0x400854) → GADGET4(0x408fb8, a0/a2 contrôlés, jalr vers LOOP_REENTRY) → bal
fcn.00400a84` **fonctionne mécaniquement à 100%** en local — confirmé en laissant tourner jusqu'au
VRAI crash (pas juste un nombre de pas arbitraire) : le crash observé est à `0x40c574`, profondément
dans le moteur `vsnprintf` interne de glibc, avec `$gp` toujours correct (`0x4a9c60`) — ce crash est
dû à l'absence d'initialisation glibc locale (on a sauté `__libc_start_main`), **pas** à la chaîne
ROP elle-même. Donc : la logique binaire est correcte à 100%.

### Pourtant, en distant, la MÊME chaîne échoue de façon reproductible
Octets envoyés vérifiés byte-par-byte contre la formule attendue — tout correspond exactement.
Testé avec `GADGET4 → free(NULL)` et `GADGET4 → LOOP_REENTRY`, les deux échouent systématiquement
(`"Message received.\n"` puis fermeture du socket), alors que `GADGET_PIVOT2 → LOOP_REENTRY`
**directement en `jr`** (sans passer par `GADGET4`/`jalr`) fonctionne à 100% de façon reproductible.

### Hypothèse restante la plus probable
Un mécanisme de surveillance actif côté infrastructure du challenge (ptrace/seccomp/CFI) qui
détecte et tue les transitions `jalr` "anormales" (cible hors d'un site d'appel légitime connu du
binaire compilé), MAIS laisse passer `jalr` quand il fait partie du code naturel déjà compilé
(ex: `read()` appelé depuis `fcn.00400a84` via son propre `addiu a2,zero,0x64; ...; jalr $t9`
natif — CECI fonctionne de façon confirmée et reproductible, y compris via un hop de pivot `jr`
intermédiaire). Seul point commun des échecs : le `jalr` est exécuté à une adresse où, dans le
flot normal du programme, cette instruction n'aurait jamais été atteinte par CE chemin précis
(même si la fonction elle-même — comme `free()` — est légitimement appelée ailleurs dans le
programme via jalr).

**Ceci n'est PAS confirmé avec certitude absolue** — seule une vraie session de débogage SUR LA
CIBLE DISTANTE (impossible sans accès du challenge) permettrait de trancher définitivement.

### Piste non épuisée pour la prochaine reprise
Le seul mécanisme confirmé qui fonctionne à 100% en distant pour exécuter du code "utile" est
`read()` via son site d'appel naturel dans `fcn.00400a84` (`0x400b40`, le "READ_SETUP"). Toute
exploitation réussie devra probablement passer PAR CE SEUL MÉCANISME (écriture arbitraire limitée
à 100 octets par round, avec la contrainte `fp+0x10` devant contenir `gp` correct — structurellement
impossible pour une cible hors de notre propre pile, voir section précédente) plutôt que par des
gadgets `jalr` assemblés à la main. Explorer si glibc contient un AUTRE site d'appel naturel
(pas forcément dans `fcn.00400a84`) où le code qui suit ne dépend PAS de `gp` du tout avant un
retour — recherche automatisée déjà faite une fois (`0 résultats`), mais avec une fenêtre de
recherche plus large / tolérance différente, ça vaudrait la peine de réessayer.

### Outils de debug local (réutilisables)
```bash
# Patch ABIFLAGS pour contourner le bug de chargement qemu-user (copie jetable seulement) :
python3 -c "
import struct
with open('vault_dbg','r+b') as f:
    data = bytearray(f.read())
    e_phoff = struct.unpack_from('<I', data, 28)[0]
    for i in range(struct.unpack_from('<H', data, 44)[0]):
        off = e_phoff + i*32
        if struct.unpack_from('<I', data, off)[0] == 0x70000003:
            struct.pack_into('<I', data, off, 0)
    f.seek(0); f.write(data)
"
qemu-mipsel -g 1234 ./vault_dbg &
gdb-multiarch -nx -q --batch \
  -ex "set architecture mips" -ex "target remote :1234" \
  -ex "set \$pc = 0x400a84" -ex "set \$t9 = 0x400a84" \
  -ex "set \$gp = 0x4a9c60" -ex "set \$sp = <adresse_libre>" \
  ... (écrire la mémoire via 'set *(int*)(ADDR) = VAL', puis 'continue' ou 'stepi N')
```
Note : `$fp` n'est PAS settable directement dans gdb pour ce contexte (erreur "not an lvalue") —
utiliser `$s8` à la place (nom réel du registre MIPS pour le frame pointer).

## MISE À JOUR (session 2, suite) — hypothèses supplémentaires testées et réfutées

- **Hash du binaire** : re-téléchargé l'attachement via l'API, SHA256 identique bit-à-bit à notre copie
  (`4d51fecb9e1b38daaba1cbbb03688f6c6ac81e660e7cd02f0ee04c053e3741a0`). Le binaire distant servi en
  téléchargement est garanti identique — mais ça ne garantit pas formellement que le PROCESSUS EN COURS
  D'EXÉCUTION sur le serveur utilise exactement ces mêmes octets (reste une hypothèse non 100% exclue,
  mais peu probable sur une plateforme CTFd standard).
- **Hypothèse "jalr autorisé seulement depuis fcn.00400a84"** : testée et RÉFUTÉE — un `jalr` déclenché
  depuis une adresse À L'INTÉRIEUR de `fcn.00400a84` elle-même (`0x400ae8`, où `move $t9,$v0; jalr $t9`
  existe nativement pour l'appel à `read()`), avec `$v0` empoisonné via un gadget multi-registres
  (`0x41fc10`), échoue AUSSI. Donc ce n'est ni la fonction cible ni la localisation du site d'appel qui
  compte isolément.
- **Second stub obfusqué trouvé** (à `0x400c40`, dans le code d'init de la boucle principale) : un
  VRAI algorithme de déchiffrement (substitution par table + XOR multi-rounds, PAS un simple XOR comme
  `entry0`) qui déchiffre des données dans `.bss` à `0x4a27f0`. Dépend de `$s0` = résultat du décodage
  CASSÉ de `entry0` (`0xc8ac9672` dans le fichier statique) comme pointeur de lecture — ce qui FAUTERAIT
  aussi sur toute exécution "normale" avec les octets statiques du fichier. **Confirmé par recherche
  exhaustive : AUCUNE instruction du binaire n'écrit jamais dans `0x4a0300`** (la "clé" lue par `entry0`
  ET ce second stub) — sa valeur est donc nécessairement celle, fixe, du fichier. Si le binaire s'exécute
  "normalement" ET fonctionne (ce qu'on observe sur le serveur), soit (a) ce chemin de code n'est en
  réalité jamais atteint sur l'exécution réelle (peut-être du code mort/leurre anti-désassembleur), soit
  (b) il y a un mécanisme externe (wrapper/chargeur personnalisé) qui patche la mémoire avant `_start` —
  non vérifiable sans accès à l'infrastructure de déploiement. **Piste non terminée** : n'a pas été
  déterminé si ce second payload déchiffré (dans `.bss`) est un leurre ou une fonctionnalité cachée
  utile (ex: backdoor légitime). À explorer en priorité si cette session est reprise : chercher ce qui
  LIT/EXÉCUTE la zone `0x4a27f0`+ après déchiffrement.

### Statut après ~2 sessions intensives sur ce seul challenge
Plus de 15 hypothèses techniques distinctes testées et réfutées empiriquement (certaines avec un vrai
débogueur local). Le blocage `jalr` reste inexpliqué avec les outils disponibles (pas d'accès debug
sur la cible distante). Recommandation : soit obtenir un accès debug réel sur le déploiement du
challenge, soit explorer la piste du second payload déchiffré en `.bss` (non terminée), soit passer
à un autre challenge du CTF.

## DÉCOUVERTE MAJEURE (session 2, suite) — backdoor AES + mprotect intégré au binaire

Le "second stub obfusqué" mentionné plus haut (à `0x400c40`) est en réalité une **vraie implémentation
AES-128 complète en MIPS assembleur** (S-box standard `63 7c 77 7b...`, inverse S-box `52 09 6a d5...`,
RCON `01 02 04 08 10 20 40 80 1b 36...` — tous vérifiés identiques aux tables AES officielles). Elle
déchiffre un bloc de 16 octets puis **appelle `mprotect()` sur la page contenant le résultat avec
PROT_READ|WRITE|EXEC, puis fait `jr $s0`** pour EXÉCUTER le contenu déchiffré comme du code — exactement
le même genre de "stub mprotect" que la version ARM du challenge (PWN#Alpha) que l'utilisateur a
résolue.

**Ce code est INATTEIGNABLE en flot normal** (la boucle principale fait un `b 0x400c18` inconditionnel
qui ne tombe jamais sur `0x400c40`) — c'est un gadget caché par l'auteur du challenge, PAS du code mort
accidentel.

### Primitive exploitée (validée par exécution RÉELLE via gdb local, PAS une simulation)
- `MPROTECT_STUB = 0x40111c` : `and $a0,$s0,-0x1000 ; li $a1,0x1000 ; li $a2,7 ; li $v0,0x101d ;
  syscall ; jr $s0` — ne dépend QUE de `$s0`, aucun `jalr` nulle part.
- En posant `$s0` = adresse d'un shellcode MIPS écrit à la main (encodage manuel de
  `lui/ori/move/addiu/syscall`, voir `exploit/exploit_final.py`) qui fait
  `execve("/bin/sh", {"/bin/sh", NULL}, NULL)`, et en atteignant `MPROTECT_STUB` via `jr` (pas `jalr`) :
  **confirmé en local que `/bin/sh` démarre réellement** (log qemu : `/bin/sh: 0: cannot open G: No
  such file` — c'est la SORTIE D'UN VRAI `/bin/sh` qui vient de remplacer le processus).

### Blocage final restant : poser `$s0` à distance
Le SEUL moyen trouvé de poser `$s0` est un gadget "epilogue universel" (`move sp,fp; lw ra,X(sp);
lw fp,Y(sp); lw s5..s0,...(sp); jr ra`) — **le plus petit existant dans ce binaire restaure au moins
8 registres** (aucune variante à 2-4 registres n'existe pour `$s0` spécifiquement, recherche
exhaustive faite). Ces gadgets multi-registres **fonctionnent parfaitement en local** (testé via
`gdb` avec la chaîne complète partant de l'épilogue réel de `fcn.00400a84`, jusqu'à l'exécution du
shellcode) **mais échouent systématiquement à distance**, avec plusieurs adresses de gadget
différentes testées (`0x439be8`, `0x40e9c8`), plusieurs `SHIFT` (positif et négatif), toujours le
même symptôme : `"Message received.\n"` puis fermeture de la connexion, sans jamais atteindre
`MPROTECT_STUB`.

**Tous les octets envoyés ont été vérifiés manuellement un par un contre la structure attendue
(capture du payload exact via `/tmp/remote_payload_exact.bin`) — aucune erreur d'indexation trouvée.**
Le gadget "universel" à 2 registres (`GADGET_PIVOT2`, fp+ra seulement) fonctionne à 100% de façon
fiable à distance ; dès qu'on passe à 6+ registres restaurés (peu importe lesquels), ça échoue
à distance tout en réussissant en local. Cause exacte non déterminée malgré une vérification
exhaustive (byte-level, debug réel local, plusieurs adresses/gadgets/directions de pivot testés).

### Piste de poursuite la plus prometteuse pour la prochaine reprise
Puisque poser UN SEUL registre supplémentaire (`fp`, via `GADGET_PIVOT2`) fonctionne, et que le
`MPROTECT_STUB` n'a besoin QUE de `$s0` — chercher s'il existe un moyen de poser `$s0`
**indirectement en 2 temps avec seulement des pivots fp/ra validés** : par exemple, un gadget qui fait
`move $s0, $fp` (copie simple, pas de restauration multi-registres) suivi d'un `jr` propre — recherche
faite UNE fois (`0 résultats` pour `move $s0,$fp` strict), mais pas élargie à `move $s0,$v0` ou
`move $s0,$a0` combinés à un pivot fp→v0/a0 préalable (ex: y a-t-il un `move $v0,$fp;...;jr ra` propre
quelque part, qu'on pourrait chaîner avant un `move $s0,$v0;...;jr ra` ?). Non exploré par manque de
temps.

## DÉCOUVERTE MAJEURE (session 3) — le blocage n'est PAS lié à `jalr`, ni au nombre de registres :
## c'est très probablement un contrôle d'intégrité de type CFI/coverage sur la DESTINATION

Cette session a testé méthodiquement, sur le DISTANT, plusieurs variables indépendamment pour isoler
la cause réelle du blocage (jusqu'ici attribué à tort à `jalr` ou au nombre de registres restaurés) :

1. **`MPROTECT_STUB` (0x40111c) atteint EN DIRECT** (un seul `ra` réécrit, AUCUN gadget intermédiaire,
   AUCUN `jalr`, juste l'épilogue original qui fait son `jr ra` normal) → **ÉCHOUE** (`"Message
   received.\n"` puis fermeture). Ceci élimine `GADGET_A`/`jalr` comme causes : le simple fait d'atterrir
   sur le code du stub AES/mprotect échoue, point final.
2. **`GADGET_A` (0x439be8, 8 registres restaurés) avec `ra` final = `LOOP_REENTRY` (donc AUCUN syscall,
   AUCUN mprotect exécuté)** → **ÉCHOUE** quand même. Élimine l'hypothèse "le syscall mprotect est
   bloqué par seccomp" : le simple fait d'ATTEINDRE `GADGET_A` et de laisser ses 8 `lw` s'exécuter
   échoue, même sans rien faire d'autre après.
3. **Passage par un hop `GADGET_PIVOT2` (prouvé fiable) AVANT `GADGET_A`** (au lieu d'un accès direct
   depuis l'épilogue original) → **ÉCHOUE pareil**. Élimine l'hypothèse "c'est la transition depuis
   l'épilogue original qui pose problème".
4. **Gadget intermédiaire à 6 registres** (`0x450b7c` : `move sp,fp; lw ra,0x3c; lw fp,0x38; lw s3,0x34;
   lw s2,0x30; lw s1,0x2c; lw s0,0x28; jr ra; addiu sp,sp,0x40` — famille "late-addiu", `addiu` dans le
   delay-slot APRÈS le `jr`) → **ÉCHOUE** également, atteint directement sans syscall.
5. **Gadget à seulement 3 registres, SANS `move sp,fp`** (`0x40eba8` : `lw ra,0x2c(sp); lw s1,0x28(sp);
   lw s0,0x24(sp); jr ra; addiu sp,sp,0x30`, reste de la famille "late-addiu"), atteint via un hop
   `GADGET_PIVOT2` fiable → **ÉCHOUE encore**. Élimine donc aussi : le nombre de registres restaurés
   (testé 2→3→6→8, tous les cas ≥3 de cette famille échouent, SEULS les gadgets à 2 registres de la
   famille "early-addiu" — `addiu` AVANT le `jr`, pas après — fonctionnent) ; la présence ou non de
   `move sp,fp` ; la présence ou non d'un hop intermédiaire.

### Corrélation la plus solide trouvée (mais PAS prouvée comme causale) :
Les **5 SEULS gadgets "early-addiu" existant dans tout le binaire** (`0x4007c8`, `0x400854`
= `GADGET_PIVOT2`, `0x40093c`, `0x400a38`, `0x400ba8` = l'épilogue réel de `fcn.00400a84` lui-même) —
tous à 2 registres (`ra`,`fp`), tous regroupés dans la toute petite plage `0x4007xx-0x400bxx` — sont
les SEULS qui fonctionnent à distance. Tous les gadgets "late-addiu" testés (quel que soit le nombre
de registres : 3, 6, 8) échouent, y compris des adresses totalement indépendantes du mystère AES
(`0x40eba8`, `0x450b7c`). Tentative de vérifier une théorie de "shadow-stack" (seul un `ra` qui est
réellement l'adresse de retour d'un VRAI `jal`/`bal` exécuté par le programme serait accepté) :
recherche exhaustive de tout `jal`/`bal` dans `.text` dont l'adresse+8 correspond à `0x400854`,
`0x400c18`, `0x439be8`, `0x40111c`, `0x4007c8` → **0 résultat** (donc ce n'est PAS un pur shadow-stack
basé sur les retours de `jal`/`bal` directs — soit c'est basé sur des appels indirects/`jalr` via
table, soit c'est une autre forme de contrôle, p.ex. liée à l'exécution réelle/couverture du programme
plutôt qu'à l'historique des appels).

### Conséquence pratique majeure
**Toute la piste backdoor AES+mprotect (`MPROTECT_STUB`/`GADGET_A`) semble DÉFINITIVEMENT BLOQUÉE** —
pas seulement par un détail d'implémentation (offset, registre, pivot), mais structurellement : le
mécanisme distant empêche d'atteindre CE CODE quel que soit le chemin. Ne plus perdre de temps à
varier `SHIFT`/l'adresse du gadget 8-registres/l'ordre des hops sur cette piste — elle est épuisée.

### Nouvelle direction à explorer en priorité (non testée cette session, juste conçue) :
Utiliser EXCLUSIVEMENT les primitives déjà prouvées fiables à distance :
- `GADGET_PIVOT2` (0x400854), chaînable à l'infini via `jr`.
- `LOOP_REENTRY` (0x400c18) : relance `fcn.00400a84` avec un `fp_orig` NEUF basé sur le `$sp` courant
  au moment du `jr` — donc, en contrôlant précisément `$sp` juste avant ce saut (via un pivot
  `GADGET_PIVOT2`), on contrôle où atterrit le PROCHAIN `buffer` de 64 octets (= nouveau point de fuite
  via l'off-by-one du nom, ET nouveau point d'écriture via les deux `read()`).
- `READ_SETUP` (0x400b40, le site d'appel natif du `read()` du "message") : confirmé (session 1) capable
  d'écrire 100 octets à une adresse arbitraire en pivotant `$fp = TARGET-0x1c`, à condition de
  pré-remplir `TARGET-0xc` avec `gp=0x4a9c60` pour que la suite ne crashe pas.

**Problème ouvert non résolu cette session** : un simple double-pivot `GADGET_PIVOT2` ne suffit PAS à
obtenir un `$sp` final VRAIMENT arbitraire en une seule fois, car `GADGET_PIVOT2` lit son `ra` suivant
depuis `(sp_courant + 0x2c)`, et si `sp_courant` (= notre `fp` choisi) est une adresse qu'on ne
contrôle pas encore en écriture, cette lecture est garbage → crash. Il faut donc soit (a) limiter la
portée de l'arbitraire à des adresses à PORTÉE DE PIED (proches de notre pile existante, où l'on peut
déjà écrire), soit (b) utiliser `READ_SETUP`/ret2read en PREMIER pour pré-écrire la case `ra` à l'adresse
cible choisie AVANT le pivot final, soit (c) marcher progressivement par petits pas (chaque `GADGET_PIVOT2`
nous fait avancer d'un nombre d'octets fixe+contrôlé, en répétant l'opération en remplissant à chaque fois
la case suivante nécessaire via `READ_SETUP`).

**Objectif suggéré pour cette primitive** : scanner/lire la pile RÉELLE vers le HAUT (adresses plus
hautes que notre frame courante — `__libc_start_main`, `argv`, `envp`) à la recherche d'une variable
d'environnement `FLAG=...` injectée par le wrapper du challenge (TRÈS courant dans les setups CTF Docker
pour les services réseau type "nc"), ce qui donnerait le flag SANS avoir besoin d'exécution de code —
contournant complètement le blocage CFI/dead-code ci-dessus. Vérifié : **aucune chaîne "flag" n'est
présente en dur dans le binaire** (`strings` négatif), donc si le flag est accessible sans exec, c'est
forcément via `envp` ou un fichier ouvert dynamiquement (aucun syscall `open` trouvé dans `.text` non
plus — donc `envp` est la piste la plus probable restante pour une victoire SANS exécution de code).

## MISE À JOUR (session 3, suite) — primitive "frame virtuelle via ret2read" RE-CONFIRMÉE fonctionnelle (connexion reste vivante sur 2 rounds), mais limite exacte non identifiée

Test de contrôle : `ra` (offset72 du premier overflow) → `READ_SETUP` (0x400b40) avec `fp_for_read =
TARGET - 0x1c` et `TARGET = buf_start` (donc on réécrit littéralement le MÊME buffer) → puis un
DEUXIÈME payload de 100 octets contenant son propre `canary`(offset64, valeur réelle leakée)/`fp`
(offset68)/`ra`(offset72=`LOOP_REENTRY`) → **SUCCÈS COMPLET** : on reçoit `"Message received.\n"` (fin
du round 1) PUIS `"Enter your name: "` (le round 2 a réussi tout le chemin : read() → print() → check
canari → épilogue → `LOOP_REENTRY` → nouvelle itération). **La connexion reste ouverte** (`io.connected()
== True`), contrairement à TOUTES les tentatives sur du "dead code". Ceci confirme : la primitive
ret2read + frame virtuelle n'est PAS bloquée par le même mécanisme CFI — elle est 100% dans le flot réel
du programme (read()/print() naturels), donc autorisée.

**Mais** : la MÊME technique avec `TARGET = buf_start + 0x60` (donc on écrit 96 octets plus loin, et on
pré-remplit manuellement la case `fp_for_read+0x10` avec `gp=0x4a9c60` à l'offset calculé dans le
PREMIER payload) **échoue** (EOF immédiat après le round 2, sans même un `"Message received."` pour le
round 2). Piste à investiguer en priorité à la prochaine reprise : pourquoi `+0x60` échoue alors que `+0`
réussit — hypothèses non testées : (a) `TARGET+0x60` déborde de la frame actuelle de `fcn.00400a84`
(qui se termine à `old_sp = buf_start+0x4c`, donc `+0x60` écrit DANS la frame du CALLER — peut-être que
cela corrompt une variable que le chemin `read()→print()→canary-check` du round 2 utilise ENCORE,
contrairement à `+0`) ; (b) erreur de calcul d'offset côté script (`gp_slot_idx` à revérifier avec un vrai
dump mémoire plutôt qu'un calcul manuel) ; (c) le chevauchement partiel entre la fin du buffer du round 1
(octets 96-99) et le début de la fenêtre d'écriture du round 2 (`TARGET`+0..3) altère quelque chose
d'important. **Prochaine étape concrète recommandée** : refaire ce test avec des décalages INTERMÉDIAIRES
(`+0x10`, `+0x20`, `+0x30`, `+0x40`, `+0x4c` = exactement la limite de la frame actuelle, `+0x50`) pour
localiser précisément le seuil de rupture, plutôt que de sauter direct à `+0x60`.

### Seuil identifié : AUCUN décalage non-nul ne fonctionne (testé 0x4,0x8,0xc,0xd,0xe,0xf,0x10,0x20,
0x30,0x40,0x4c,0x50,0x60 — TOUS échouent, SEUL `OFF=0` réussit). La variable `gp` au slot calculé a été
correctement positionnée pour 0xc-0x60 et ça échoue quand même — donc ce n'est PAS un problème de `gp`.
**Conclusion : la primitive ret2read ne permet d'écrire QUE EXACTEMENT au même endroit que le buffer
existant** (ce qui n'apporte rien de nouveau par rapport à l'overflow normal) — **PAS une primitive de
marche arbitraire sur la pile**. La piste "lire `envp` en remontant la pile" est donc ABANDONNÉE :
techniquement irréalisable avec les primitives actuelles. Cause exacte du échec à tout décalage non-nul
non déterminée (nécessiterait un vrai débogueur distant) mais le comportement est 100% reproductible et
déterministe.

## STATUT FINAL SESSION 3 — toutes les pistes connues sont maintenant épuisées ou mortes

Résumé des pistes testées et leur statut après cette session :
1. **ROP `jalr` à la main** → mort (bloqué par mécanisme type CFI, confirmé sur de multiples adresses).
2. **Backdoor AES-128 + `mprotect`+shellcode** → mort (même mécanisme bloque `MPROTECT_STUB` même atteint
   directement, sans aucun gadget intermédiaire).
3. **Marche arbitraire sur la pile via ret2read répété** → mort (ne fonctionne qu'à décalage ZÉRO).
4. **Chaînage `GADGET_PIVOT2` x2 pour sp arbitraire** → mort en théorie (nécessite d'écrire au préalable
   à une adresse qu'on ne contrôle pas encore — dépendance circulaire non résolue).
5. **Flag en dur dans le binaire ou lu depuis un fichier** → absent (vérifié par `strings`, aucun syscall
   `open` dans `.text`).

**Seules primitives encore fonctionnelles confirmées** : `GADGET_PIVOT2`/`GADGET1` (chaînable à l'infini
via `jr`), `LOOP_REENTRY`, `READ_SETUP` (ret2read vers la MÊME adresse uniquement). Aucune de ces
primitives seules ne permet, à ce stade, d'atteindre un objectif utile (fuite du flag ou exécution de
code) sans un AUTRE angle non encore identifié.

### Note (session 3, piste `entry0` re-vérifiée EMPIRIQUEMENT, pas juste en statique)

Hypothèse testée : peut-être que les chaînes du programme ("Enter your name", etc., **absentes du
binaire en clair**, vérifié par `strings`/recherche brute sur tout le fichier) sont décodées par un
mécanisme caché similaire au backdoor AES, et que ce mécanisme révèle une nouvelle primitive. En
remontant jusqu'à `entry0` (0x401140, le VRAI point d'entrée ELF, confirmé via `readelf -h`) :
```
lui t1,0x4a; addiu t1,t1,0x300   # t1 = 0x4a0300
lw t0,(t1)                       # t0 = valeur statique du fichier = 0x8ac3f100
lui t2,0x426f; ori t2,t2,0x6772  # t2 = 0x426f6772 (constante immédiate)
xor t3,t0,t2                     # t3 = 0xc8ac9672
jr t3                            # saut vers une adresse INVALIDE
```
**Confirmé cette fois via exécution RÉELLE sous `qemu-mipsel -g` + `gdb-multiarch`** (pas une simulation
manuelle) : `t0=0x8ac3f100`, `t3=0xc8ac9672`, et le `stepi` suivant le `jr` donne bien
`"Cannot access memory at address 0xc8ac9672"` — **le binaire, exécuté tel quel depuis son VRAI point
d'entrée, crashe immédiatement, sans aucune intervention manuelle pour "sauter" ce stub** (contrairement
aux sessions précédentes qui forçaient `$pc` manuellement AU-DELÀ de ce point sans vérifier ce qu'il se
passait réellement). Ceci confirme that le fichier `vault` téléchargé, pris isolément et exécuté
directement (`./vault` ou `qemu-mipsel ./vault`), **ne peut pas fonctionner tel quel** — alors que le
service réel sur `169.58.126.107:5005` fonctionne parfaitement (prompts corrects, logique confirmée
des centaines de fois). Conclusion : le déploiement réel utilise forcément soit (a) un wrapper/loader
qui patche la mémoire avant `entry0`, soit (b) un binaire légèrement différent sur le serveur (malgré
le hash SHA256 identique de l'ATTACHEMENT téléchargeable — rien ne garantit que c'est le MÊME fichier
que celui réellement exécuté). **Dans les deux cas, ce détail est hors de portée de l'analyse statique/
locale et n'offre aucune nouvelle primitive exploitable.** Piste clôturée, ne pas ré-explorer sauf accès
serveur réel.

**Recommandation forte, inchangée depuis session 2** : un accès debug réel sur le déploiement distant
(ou au moins des logs d'erreur serveur) réglerait ce blocage en quelques minutes. Sans cela, continuer
à deviner des variations de gadgets a un rendement décroissant très fort après ~3 sessions et >25
hypothèses testées et réfutées. À la prochaine reprise, envisager sérieusement : (a) redemander à
l'utilisateur un accès/indice supplémentaire sur l'infrastructure du challenge, ou (b) basculer l'effort
sur un autre challenge du CTF et revenir à PWN#Beta plus tard avec un œil neuf.

## SESSION 4 — une hypothèse de plus testée et éliminée : PAS un filtre statique sur les octets

Hypothèse testée (non couverte par les 3 sessions précédentes) : le blocage pourrait être un filtre
réseau/IDS basique qui reconnaît la simple PRÉSENCE de certains octets (l'adresse d'un gadget
"late-addiu" connu pour échouer) n'importe où dans le flux TCP, indépendamment de toute exécution.

**Test** (`exploit/probe_byte_filter.py`) : chaîne connue-fiable (`GADGET_PIVOT2` → `LOOP_REENTRY`,
qui boucle normalement), avec l'adresse `0x450b7c` (gadget "late-addiu" confirmé bloqué quand utilisé
comme cible de saut) injectée comme **donnée inerte** à un offset du buffer jamais lu ni exécuté par
cette chaîne.

**Résultat** : la boucle réussit dans les deux cas (avec et sans l'octet suspect présent comme pure
donnée) — `looped_back=True` pour les deux tests, confirmé en direct contre `169.58.126.107:5005`.

**Conclusion** : ce n'est **pas** un filtre de contenu statique sur le flux réseau. Le blocage nécessite
que l'adresse soit réellement **utilisée comme cible d'exécution** (`jr`/`jalr` vers elle) pour se
déclencher — ceci renforce (sans le prouver formellement) l'hypothèse CFI/coverage déjà posée en
session 3, et élimine définitivement la piste "WAF réseau basique sur les octets".

### Statut : toujours bloqué, aucune nouvelle piste ouverte par ce test
Ce test ferme une hypothèse de plus mais n'ouvre pas de nouveau chemin. Reste valable : la
recommandation de session 3 (accès debug réel sur le déploiement distant, ou œil neuf avec un angle
non envisagé). Pause sur ce challenge pour privilégier d'autres cibles du CTF (VULN#001).

## COMPLÉMENT SESSION 3 (fin) — derniers tests avant pause, tout consigné pour ne rien reperdre

### Re-vérification maximale de l'échec de `GADGET_A` (pour exclure un bug de script, pas un vrai blocage)
Test refait avec TOUS les registres du gadget (s0-s5, fp, ra) explicitement remplis avec des valeurs
SAINES (pas de zéro non-initialisé par accident), buffer rempli de `'A'` pour détecter tout chevauchement
visuellement via hexdump vérifié à la main avant envoi, `fp` posé à une valeur raisonnable (`buf_start`)
au lieu de laisser 0. **Échec identique** (`"Message received.\n"` puis EOF dès le prochain `send`/`recv`
— `io.connected()` peut mentir temporairement tant qu'aucune I/O n'a retenté la socket, piège déjà
rencontré : toujours vérifier avec un envoi/réception supplémentaire avant de conclure "ça marche").
**Conclusion : pas un bug de script, le blocage est réel et reproductible même avec une entrée parfaite.**

### Recherche EXHAUSTIVE finale de gadgets "early-addiu" (ceux qui marchent) de tout le binaire
Recherche élargie (sans exiger un `move sp,fp` en tête, juste `addiu sp,sp,FRAME` suivi d'un ou
plusieurs `lw ...(sp)` puis `jr ra`, AVANT le `jr` et non dans son delay-slot) sur la TOTALITÉ de
`.text` : **confirme qu'il n'existe que 5 gadgets de ce type dans tout le binaire, tous à 2 registres
(`ra`,`fp`), tous regroupés entre `0x4007c8` et `0x400ba8`** (`0x4007c8`, `0x400854`=`GADGET_PIVOT2`,
`0x40093c`, `0x400a38`, `0x400ba8`=l'épilogue réel de `fcn.00400a84`). Plusieurs faux positifs détectés
et écartés (`0x42edb8`, `0x430b68`, `0x411bbc` : le "addiu" trouvé juste avant appartenait en fait au
delay-slot d'un `jr`/`b` PRÉCÉDENT et sans rapport, pas au gadget lui-même — ces trois sont en réalité
de la famille "late-addiu" qui échoue). Un seul gadget supplémentaire trouvé, `0x42d7a0` (1 seul
registre `ra`, famille early) — sans intérêt, n'apporte rien de plus que `GADGET_PIVOT2`.
**Il n'existe donc structurellement AUCUN gadget "qui marche" avec plus de 2 registres utiles dans ce
binaire.** Piste de recherche de gadgets déclarée définitivement épuisée.

### Cartographie complète des sites d'appel LÉGITIMES (réellement exécutés) de `fcn.00400a84` et de
l'init de la boucle
Désassemblage complet (au lieu de fragments) de `fcn.00400a84` + le code d'init de la boucle juste
avant `LOOP_REENTRY`. Tous les `bal`/`jalr` réellement exécutés à chaque connexion :
- `bal 0x409590` (×3) — wrapper `printf`/fortify (impression "Hello, X", "Leave a message...", etc.)
- `bal 0x40ff60` — impression "Message received."
- `jalr t9` (×2, dans `fcn.00400a84`) — les deux `read()` (nom, message)
- `bal 0x4006f0` — fonction d'init appelée UNE FOIS par connexion, qui fait 3 `mprotect()` sur
  `0x4a0c28`/`0x4a0af8`/`0x4a09c8` (**PAS** la même région que le backdoor AES à `0x400c40`/`0x40111c` —
  vérifié, confusion possible à éviter) puis saute à `0x4005f8`. C'est très probablement le DÉCODEUR
  des chaînes du programme (qui sont absentes en clair du fichier, vérifié par recherche brute —
  "Enter your name", "Hello,", "Message received.", "vault keeper" n'apparaissent NULLE PART dans le
  fichier statique, ni dans `.rodata` ni ailleurs). Non élucidé en détail (le code de décodage précis
  après le saut à `0x4005f8` n'a pas été tracé) mais confirmé **sans rapport avec le backdoor AES déjà
  documenté** (adresses `.data` différentes).
- `bal 0x400954` — fonction qui imprime la bannière d'accueil (plusieurs appels à `0x40086c`, un
  wrapper `write()`, avec `a0`=pointeur dans la zone `0x4a0314`+ et `a1`=longueur) — appelée UNE FOIS
  avant le début de la boucle de lecture nom/message.
- `bal 0x400a84` (×N, dans la boucle = `LOOP_REENTRY`) — l'appel répété à la fonction vulnérable.

**Aucun autre site d'appel utile trouvé** (pas de `system`/`execve`/`popen` appelé légitimement nulle
part dans ce chemin). Cette cartographie est complète pour la partie "connexion réseau" — il reste
possible qu'il y ait AUTRE CHOSE dans l'init globale du processus (`main()`/constructeurs globaux) non
tracé en détail, mais peu probable que ça aide puisque ce code tourne AVANT toute donnée attaquant.

### Sondage protocole (aucune fonctionnalité cachée trouvée)
- Mots-clés testés comme nom/message (`flag`, `admin`, `debug`, `unlock`, `vault`, `secret`, `password`,
  `root`, `sudo`) → comportement IDENTIQUE à n'importe quelle autre chaîne, aucun easter egg/commande
  cachée.
- Canari délibérément FAUX envoyé dans le champ message → échec silencieux identique (`"Message
  received.\n"` puis fermeture), AUCUNE sortie supplémentaire (pas de message "stack smashing" visible
  côté client, pas de fuite d'info sur le mismatch).
- Le protocole est strictement : `"Enter your name: "` → écho `"Hello, X\n\nLeave a message for the
  vault keeper: "` → `"Message received.\nEnter your name: "` (boucle). Rien d'autre.
- Challenge CTFd : pas de hints disponibles (`hints: []`), description = `"Get a shell on the remote
  host and read the flag."` (rien d'indicatif). **6 autres équipes ont déjà résolu ce challenge**
  (confirmé via l'API `/api/v1/challenges/23` → `solves: 6`) — donc une solution existe forcément,
  l'blocage constaté est réel mais pas insurmontable en principe.

### Conclusion de session 3 (pour la prochaine reprise)
Après ~3 sessions et probablement 40+ hypothèses testées et réfutées (certaines avec débogueur local
réel, byte-level verification, cartographie complète du call-graph légitime), **aucune nouvelle piste
d'analyse statique/réseau ne reste à explorer sans information supplémentaire**. Les deux options
restantes sont : (a) obtenir un accès/indice supplémentaire sur le déploiement (debug réel, logs,
accès infra du CTF), ou (b) qu'un œil complètement neuf (humain ou IA) trouve un angle non envisagé
dans cette série de sessions — relire ce HANDOFF en entier avant de recommencer permettrait d'éviter de
refaire le même travail.

## SESSION 5 — DEUX NOUVELLES PRIMITIVES DÉCOUVERTES, exploitation pas encore terminée

Reprise suite à la consigne utilisateur "il y a plusieurs solves, concentre-toi". Relecture complète
du HANDOFF, puis deux angles **jamais testés dans les sessions 1-4** ont été explorés avec succès
partiel.

### NOUVELLE PRIMITIVE #1 (confirmée fiable à distance) : lecture/écriture arbitraire via
### `GADGET_PIVOT2 → LOOP_REENTRY(sp=TARGET)` — PAS limitée à offset 0, contrairement à ce que
### concluait la section "ret2read" ci-dessus (qui ne testait qu'une AUTRE primitive : le ret2read
### dans la MÊME frame via READ_SETUP, qui elle reste limitée à offset 0)

Technique : `GADGET_PIVOT2` (fiable, déjà connu) avec `fp` pivoté vers **n'importe quelle adresse
inscriptible `TARGET`** et `ra = LOOP_REENTRY` (0x400c18, fiable, déjà connu). Au lieu de rejouer la
MÊME frame (comme `READ_SETUP`), ceci relance un **appel complet et neuf** à `fcn.00400a84` via son
propre `bal` natif (`bal fcn.00400a84` à l'intérieur de `LOOP_REENTRY`, qui recharge `$gp`
correctement via son propre `$t9` — **c'est pourquoi ça marche à n'importe quel offset**, contrairement
à `READ_SETUP` qui saute au MILIEU de la fonction et hérite d'un `$gp` déjà établi par le round
précédent, dont la cohérence casse si on s'éloigne).

**Testé et confirmé en direct contre `169.58.126.107:5005`** : `delta` = 0, 0x100, 0x400, 0x1000,
0x4000, 0x100 (walking) — **tous réussissent** (`"Message received.\nEnter your name: "` revient à
chaque fois, la connexion reste vivante, le round complet — y compris le PRINT "Hello, X" normal et
le check canari — se déroule sans erreur).

Mécanique exacte :
```
fp_new (du round neuf) = TARGET - 0x68
nom_buffer (contrôlé, 64+1 octets)  = TARGET - 0x4c
canary slot (du round neuf)         = TARGET - 0xc
saved_fp slot (du round neuf)       = TARGET - 0x8
saved_ra slot (du round neuf)       = TARGET - 0x4
```
(ces offsets viennent directement du prologue natif de `fcn.00400a84` : `addiu sp,sp,-0x68; sw
ra,0x64(sp); sw fp,0x60(sp); move fp,sp`, avec `sp` au moment du `bal` = notre `TARGET` choisi.)

⚠️ **Piège découvert** : le payload du round neuf n'a PAS besoin de faire 65 octets (le seuil du
leak/off-by-one classique) — on peut envoyer **aussi peu que 4 octets** pour une écriture ciblée
précise, évitant de toucher les octets suivants. Mais la fonction écrit AUSSI, **via son propre
prologue natif**, `ra`/`fp`/`gp` à `TARGET-0x4c+0x64=TARGET+0x18`, `TARGET-0x4c+0x60=TARGET+0x14`,
et `TARGET-0x4c+0x10=TARGET-0x3c` (sauvegarde du `$gp` courant, pour restauration après un `bal`
imbriqué) — **CES TROIS ÉCRITURES SONT AUTOMATIQUES ET INÉVITABLES**, même si on n'envoie que
4 octets de "nom". Si `TARGET` est choisi dans une zone dense de pointeurs GOT-style (voir primitive
#2 ci-dessous), ces 3 écritures collatérales **peuvent corrompre un autre slot critique** (confirmé :
a fait planter le round en cours lors du test de la primitive #2).

### PISTE DU MYSTÈRE CFI, reformulée plus précisément après cette session
L'hypothèse "CFI/coverage sur la destination" (section précédente) reste correcte en apparence, MAIS
avec un angle plus simple et jamais testé avant cette session : si le filtre ne regarde QUE l'adresse
d'où part un `jr`/`jalr` (ou sa destination directe lue depuis UN registre que NOUS venons de poser
via ROP) et ignore les valeurs **chargées depuis la mémoire .data/.bss juste avant un `jalr` qui, lui,
fait partie du flot natif déjà chaud** — alors on peut contourner tout le problème en corrompant la
**DONNÉE** (le pointeur de fonction stocké dans la table GOT-style) au lieu d'introduire un nouveau
site de saut. **Cette idée n'apparaît nulle part dans les sessions 1-4** (qui ont uniquement testé des
variations de gadgets ROP, jamais une corruption de pointeur de données utilisé par un `jalr` déjà
légitime).

### NOUVELLE PRIMITIVE #2 (partiellement testée, résultat encourageant mais incomplet) :
### corruption de pointeur GOT-style au lieu de hijack de `ra`/`jr`

Repérage de la table de pointeurs GOT-style (tous `gp`-relatifs, `gp = 0x4a9c60` fixe) utilisée par
`fcn.00400a84` :
```
gp-0x7fe0 = 0x4a1c80 : GUARD_PTR_SLOT (pointeur vers la vraie valeur du canari — déjà dans le tableau
                       d'adresses utiles plus haut dans ce doc)
gp-0x7fdc = 0x4a1c84 : pointeur de BASE pour les format strings printf (utilisé comme
                       `a1 = *(gp-0x7fdc) + OFFSET_FIXE` à chaque site d'appel printf, OFFSET_FIXE
                       variant par site : 0x314 pour "Hello, %s...", etc.)
gp-0x7f90 = 0x4a1cd0 : pointeur vers le handler d'échec du check canari (jalr t9 déclenché si
                       mismatch)
gp-0x7f80 = ~0x4a1ce0: pointeur vers printf/vfprintf (utilisé via jalr t9 pour TOUS les printf)
gp-0x7f7c = 0x4a1ce4 : pointeur vers read() (utilisé via jalr t9 pour LES DEUX read() de
                       fcn.00400a84 — nom ET message, a0=0 fixe dans les deux cas, donc pas un bon
                       site pour rediriger vers execve avec un chemin contrôlé)
```
**Idée testée** : écrire `(0x4729a4 - 0x314) = 0x472690` dans le slot `0x4a1c84` (base format-string),
pour que le PROCHAIN `printf("Hello, %s", name)` imprime en fait la chaîne à `slot+0x314 =
0x4729a4` = `"/bin/sh"` littéralement (le format string devient "/bin/sh", sans `%s`, donc `name` est
ignoré et "/bin/sh" est juste affiché tel quel — un test d'abord **safe/non-destructif** pour valider
le mécanisme avant de viser plus agressif, ex. écraser le pointeur `printf`/`read` lui-même avec
l'adresse d'`execve`).

**Résultat** : l'écriture de l'écho du round EN COURS confirme bien nos 4 octets reçus
(`"Hello, \x90&G"` = `0x472690` en little-endian — preuve que l'écriture arrive au bon endroit). MAIS
**le round a planté en essayant de compléter le champ "message"** juste après (`status=FIN` après
l'envoi du message) — très probablement parce que les 3 écritures collatérales AUTOMATIQUES du
prologue (`ra`/`fp`/`gp` sauvegardés à `TARGET+0x14`, `TARGET+0x18`, `TARGET-0x3c` — voir primitive #1
ci-dessus) sont tombées sur un AUTRE slot critique de cette même table dense (peut-être `gp` lui-même,
ou le pointeur `read()`), cassant le reste de l'exécution de CE round avant même d'atteindre le round
SUIVANT où le hijack aurait dû se manifester.

### Piste concrète à poursuivre en priorité à la prochaine reprise
1. **Choisir un `TARGET` qui isole le slot visé des 3 écritures collatérales du prologue.** Puisque
   les offsets collatéraux sont fixes relativement à `TARGET` (`TARGET+0x14`, `TARGET+0x18`,
   `TARGET-0x3c`), il faut soit (a) viser une zone où CES TROIS offsets tombent dans du `.bss` inutile
   (pas dans la table GOT dense), soit (b) accepter la corrruption collatérale POUR CE ROUND mais
   s'assurer qu'elle ne touche RIEN utilisé par LE RESTE DE CE MÊME ROUND (seulement par un round
   FUTUR, qu'on n'a pas besoin de faire aboutir normalement si on compte enchaîner directement un
   AUTRE hijack ou un reset de connexion).
2. **Cible plus directement utile que le format-string** : écraser le pointeur `read()`
   (`0x4a1ce4`) ou `printf`/`vfprintf` (`~0x4a1ce0`) avec l'adresse d'`execve` (`0x450a7c`) ou de
   `system()` (si le symbole existe — à vérifier, pas encore fait). Problème identifié : le site
   d'appel `read()` a toujours `a0=0` (fd fixe), donc `execve(0, ...)` échouerait silencieusement
   (pas un crash, juste un retour d'erreur, le round continuerait normalement avec un buffer non
   rempli) — **pas nécessairement un échec total, à retester pour voir si ça permet au moins de
   confirmer le hijack sans planter**, avant de chercher un site d'appel où `a0` est DÉJÀ un pointeur
   intéressant (ex: le site d'appel printf avec `a0=FILE*` fixe — pourrait valoir la peine d'examiner
   la structure `FILE*` de `stdout`, si ses premiers octets sont interprétables comme une commande
   shell valide, peu probable mais pas vérifié).
3. **Site le plus prometteur pas encore essayé** : le slot `gp-0x7f90` (handler d'échec du canari,
   `0x4a1cd0`) — si on PEUT DÉLIBÉRÉMENT faire échouer le check canari (en envoyant un canari faux
   dans un round normal) APRÈS avoir hijacké ce pointeur vers une fonction utile, le handler
   d'échec est appelé avec des arguments qu'il faudrait examiner (`a0`/`a1` au moment de cet appel,
   pas encore tracés dans ce HANDOFF) — pourrait être plus simple à exploiter que `read`/`printf`
   si ses arguments naturels sont plus proches de ce dont `execve`/`system` a besoin.
4. **Ne pas oublier** : la primitive #1 (écriture arbitraire via `LOOP_REENTRY(sp=TARGET)`) reste
   valable et fiable MÊME sans le hijack GOT — elle peut aussi servir à écrire un **shellcode MIPS**
   quelque part en mémoire `.bss` inscriptible choisie à l'écart de toute table critique, pour
   ensuite (séparément) chercher un moyen de rediriger `$pc`/`t9` vers CE shellcode d'une façon qui
   passe le filtre (ex: via le même mécanisme de corruption de pointeur GOT plutôt qu'un `jr`/`jalr`
   direct sur une adresse introduite par ROP).

### Test du hijack du pointeur `read()` vers `execve` — résultat AMBIGU, pas une confirmation
Écrasé le slot `0x4a1ce4` (pointeur `read()`) avec l'adresse d'`execve` (`0x450a7c`), 4 octets
seulement (pas de débordement). L'écriture elle-même confirmée correcte (écho `"Hello, |\nE"` =
`0x450a7c` en little-endian, tronqué au premier octet nul). Puis envoi d'un message normal pour
déclencher le SECOND appel `read()` du round (celui du champ "message"), qui utilise CE MÊME
slot fraîchement corrompu — donc `execve(a0=0, a1=message_buf_ptr, a2=0x64)` aurait dû s'exécuter
à la place de `read()`.

**Résultat obtenu** : `"Message received.\n"` puis fermeture (`FIN`). **Mais c'est EXACTEMENT la
même signature que tous les échecs "CFI" déjà documentés plus haut** (ex: le test
`GADGET_A`/adresse garbage de cette même session a produit `resp=b'Message received.\n'` suivi de
`FIN` aussi) — donc **ce résultat ne prouve NI un contournement réussi NI un blocage par le même
mécanisme CFI** : il est tout aussi cohérent avec un `execve(NULL, ...)` qui échoue proprement
(retourne -1, le programme continue, imprime "Message received." normalement car le code ne
vérifie pas la valeur de retour de ce "read", puis plante PLUS TARD pour une raison différente -
peut-être le buffer "message" jamais rempli, utilisé ensuite de façon incohérente). **Ambigu,
non concluant, à ne pas interpréter comme un échec confirmé du contournement "corruption de
données" — seulement comme non-concluant avec les informations actuelles.**

### Test de suivi : hijack vers `exit(0)` (0x4012a8 : move a0,zero; li v0,0xfa1; syscall) —
### résultat NÉGATIF et INEXPLIQUÉ, nécessite un vrai débogueur pour trancher
Même technique (écrire 4 octets dans le slot `read()` à `0x4a1ce4`, valeur = `0x4012a8`), mais
cette fois en envoyant ENSUITE un vrai message ("HELLOFROMMESSAGE\n") pour le second `read()` du
round. **Résultat : le second `read()` a WOW fonctionné NORMALEMENT** (`"Message received.\n"`
imprimé, confirmant que NOTRE message a bien été consommé par un VRAI `read()`, PAS redirigé vers
`exit()`) puis EOF juste après (crash normal de fin de fonction, sans rapport).

**Analyse qui ne colle pas** : le calcul montre que `fp+0x1c` (buffer "nom", où notre écriture de
4 octets atterrit) est bien **= `0x4a1ce4` = exactement le même slot que `-0x7f7c(gp)` utilisé par
le DEUXIÈME `read()`** (vérifié par désassemblage exact des DEUX sites d'appel, immédiat identique
`-0x7f7c` aux deux endroits, confirmé octet par octet). Rien d'identifié entre les deux appels
n'écrit à cette adresse. **Le slot de sauvegarde de `gp`** (`fp+0x10 = 0x4a1cd8`) a aussi été
vérifié comme n'chevauchant aucun autre slot connu. Donc, sur le papier, le deuxième `read()`
AURAIT DÛ charger notre valeur corrompue — mais empiriquement, ça ne se produit pas.

**Conclusion honnête** : soit (a) il y a une erreur de calcul d'adresse encore non identifiée
(malgré plusieurs vérifications), soit (b) il y a un mécanisme non compris (peut-être lié au
même "CFI"/filtre déjà documenté, qui empêcherait spécifiquement l'ÉCRITURE à cette zone-là
silencieusement, ou qui restaurerait la valeur d'une façon non visible dans le désassemblage
statique), soit (c) autre chose de non envisagé. **Ceci NE PEUT PAS être tranché de façon fiable
sans un vrai débogueur** (comme celui utilisé avec succès en session 2 : `qemu-mipsel -g` +
`gdb-multiarch`, voir la section "Outils de debug local" plus haut) — poser un breakpoint sur
`0x400b50` (le second `lw v0,-0x7f7c(gp)`) et inspecter `$gp`/la mémoire à `0x4a1ce4` juste avant
cette instruction trancherait la question en quelques minutes, au lieu de deviner.

### Bilan honnête de cette session (session 5)
Deux primitives nouvelles et une piste de contournement solide sur le papier ont été découvertes
et ne figuraient dans AUCUNE des 4 sessions précédentes :
1. **Écriture arbitraire fiable à n'importe quel offset** via `GADGET_PIVOT2 → LOOP_REENTRY(sp=
   TARGET)` — confirmée, reproductible, utilisable pour d'autres tentatives futures.
2. **Idée de corruption de pointeur GOT-style au lieu de hijack `ra`/`jr` direct** — théoriquement
   solide (contourne le filtre en gardant le MÊME site de saut légitime, en changeant seulement
   la valeur qu'il charge), mais **le test empirique n'a pas confirmé que l'écriture elle-même
   atteint sa cible de façon durable** pour une raison non élucidée. Ni confirmée ni réfutée avec
   certitude — nécessite un vrai débogueur pour la prochaine reprise plutôt que plus de essais à
   l'aveugle (qui ont une valeur marginale décroissante très forte à ce stade, cohérent avec le
   constat des sessions précédentes).

**Recommandation inchangée et renforcée** : un accès debug réel (local, via `qemu-mipsel -g`) sur
CE scénario précis (écriture au slot GOT, puis inspection de la mémoire juste avant le 2e `read()`)
est le chemin le plus rapide vers la résolution. Sans cela, le defi reste bloqué après 5 sessions
intensives — decision à prendre : (a) investir le temps d'une session dédiée au débogueur local sur
CE nouveau scénario précis (probablement < 30 min avec les outils déjà réutilisables documentés
plus haut), ou (b) laisser ce challenge de côté définitivement au profit d'autres cibles du CTF.

### Scripts de cette session (réutilisables)
- `/tmp/test_loop_reentry_arbitrary.py` — confirme la primitive #1 (lecture/écriture arbitraire à
  tout offset via `LOOP_REENTRY`).
- `/tmp/scan_stack.py` — scanner générique pour sonder un intervalle d'adresses avec la primitive #1
  (attention : la portion "leak" qu'il affiche est en réalité auto-référentielle — voir piège
  ci-dessous — ne pas réutiliser tel quel pour chercher `envp`/argv sans le corriger).
- `/tmp/test_fmt_hijack.py` — test (partiellement concluant) de la primitive #2.

### ⚠️ Piège découvert cette session : le "leak" après l'écho du round `LOOP_REENTRY` n'est PAS
### une fuite de mémoire préexistante
Les octets lus juste après notre entrée de 64+1 octets dans un round `LOOP_REENTRY(sp=TARGET)` sont
le `canary`/`saved_fp` **que CE round vient tout juste d'écrire lui-même** via son propre prologue
(`sw ra,0x64(sp); sw fp,0x60(sp)`), PAS des données préexistantes à `TARGET`. Donc **cette primitive
ne donne PAS un "arbitrary read" de mémoire inconnue** telle quelle (contrairement à ce qui a été
supposé initialement dans cette session avant de comprendre le mécanisme) — seulement une
**écriture arbitraire fiable**. Pour une vraie lecture arbitraire, il faut une approche différente
(ex: primitive #2, hijack d'un pointeur consommé par un `printf`/`write` déjà chaud, pour faire
imprimer du contenu choisi par l'attaquant).

## SESSION 6 (2026-10-22) — AMBIGUÏTÉ DE LA PRIMITIVE #2 TRANCHÉE AU DÉBOGUEUR RÉEL : le mécanisme
## tient parfaitement, la piste GOT-hijack est quand même MORTE (même mur CFI/coverage, pas un bug)

### Méthode : vrai débogage local, pas de supposition
Repris exactement là où la session 5 s'était arrêtée (ambiguïté sur le hijack du slot `read()` à
`0x4a1ce4` = `gp-0x7f7c`). Utilisé `qemu-mipsel -g 1234 ./vault_dbg` (déjà patché ABIFLAGS, aucun
re-patch nécessaire) + `gdb-multiarch` piloté via un script Python gdb (pas de commandes `-ex`
manuelles cette fois — besoin de breakpoints avec callback programmatique).

**Obstacle technique rencontré et résolu** : entrer directement dans `fcn.00400a84` (comme en
session 2) fait toujours planter sur le TOUT PREMIER `bal 0x409590` (prompt "Enter your name"),
précisément à `0x40c574` (même adresse que le crash documenté en session 2) — **PAS parce que les
chaînes de format sont du garbage** (vérifié : même en forçant `$a0`/`$a1` vers une chaîne ASCII
valide connue, ça plante identiquement) **mais parce qu'il manque l'init glibc/stdio** (confirme la
théorie de session 2, cette fois vérifiée en isolant la variable argument). Contournement : chaque
site `bal 0x409590`/`bal 0x40ff60` est équipé d'un breakpoint GDB dont le callback Python force
`$pc = site+8` (sauter le `bal` ET son delay-slot) avant de laisser continuer — aucune écriture dans
`.text` nécessaire (de toute façon refusée par qemu-user, page non-writable), uniquement des
écritures de registres.

**Second obstacle** : `read()` lui-même plante aussi localement (`SIGSEGV` à `0x427798`, instruction
`lw v0,-29920(v1)` avec `$v1=0`) — **un point d'annulation pthread MIPS qui déréférence un pointeur
TLS jamais initialisé** (puisqu'on saute `__libc_start_main`/`__libc_setup_tls`). Contournement :
remplacer chaque site d'appel `read()` (`jalr t9` à `0x400aec` et `0x400b58`) par un breakpoint dont
le callback écrit directement nos octets choisis dans `$a1` (le buffer destination), pose
`$v0 = len`, puis saute `pc = site+8` — simule un `read()` réussi sans jamais exécuter le vrai libc
`read()`. Ces deux contournements n'affectent QUE notre répro locale, ils ne changent rien à
l'exploit distant.

### Résultat n°1 (le plus important) : la primitive #2 TIENT, mécaniquement, à 100%
Test : écrire directement `mem[0x4a1ce4] = 0x4012a8` (adresse du stub `exit()`, même valeur que le
test ambigu de session 5) via `gdb`, PUIS dérouler un ROUND normal complet (nouvelle itération via
`LOOP_REENTRY` avec `fp=buf_start` — mécanique confirmée séparément, voir plus bas), jusqu'au
breakpoint exact sur `lw v0,-0x7f7c(gp)` à `0x400b50` (second site d'appel `read()`, confirmé par
désassemblage réel que son adresse EST `0x400b50`, pas juste une estimation du HANDOFF).

**Observé, instruction par instruction (`stepi`)** :
```
pc=0x400b50 (avant le lw)  : mem[0x4a1ce4] == 0x4012a8  -- le slot tient encore, intact.
pc=0x400b54 (après le lw)  : $v0 = 0x4012a8             -- chargé correctement depuis le slot.
pc=0x400b58 (après move)   : $t9 = 0x4012a8             -- propagé correctement.
pc=0x4012a8 (après jalr)   : le jalr a RÉELLEMENT sauté là -- on exécute le VRAI stub exit()
pc=0x4012ac                : "li v0,0xfa1" (SYS_exit)   -- code du stub, pas une coïncidence.
pc=0x4012b0                : $v0=0xfa1, sur le point de faire le syscall exit(0).
```
**Rien n'écrase le slot entre notre écriture et sa lecture.** Le `jalr t9` utilise fidèlement la
valeur empoisonnée. Mécaniquement, `LOOP_REENTRY`/corruption de pointeur de données consommé par un
`jalr` déjà "chaud" fonctionne EXACTEMENT comme imaginé en session 5 — **ce n'est PAS un bug
d'arithmétique, PAS une restauration invisible, PAS un artefact du débogueur.**

### Résultat n°2 : donc l'ambiguïté de session 5 (le hijack vers `exit()` semblait ne "pas tenir" en
### distant) n'était PAS un problème mécanique local — c'est (très probablement) le MÊME mur CFI/
### coverage déjà documenté en sessions 3-4, qui s'applique aussi à ce vecteur
Conclusion logique (pas testable sans accès debug sur le serveur distant lui-même, mais cohérente
à 100% avec TOUTES les >40 hypothèses déjà réfutées) : si le mécanisme de filtrage distant regarde
la **DESTINATION réelle d'un `jr`/`jalr`** (indépendamment de QUI a chargé cette destination — un
gadget ROP à la main OU une donnée `.bss`/`.data` corrompue consommée par un `jalr` natif) et la
compare à l'ensemble des adresses qui sont *réellement atteintes par ce type d'instruction* dans un
flot d'exécution normal du programme, alors :
- `GADGET_PIVOT2`, `LOOP_REENTRY`, l'épilogue réel (`0x400ba8`) marchent car ce sont des destinations
  **toujours** couvertes (every single connection).
- `MPROTECT_STUB`, `GADGET_A`, tout gadget "late-addiu", `exit()` (`0x4012a8`), `execve` (`0x450a7c`)
  échouent car ce sont des destinations **jamais** atteintes par un `jr`/`jalr` dans le programme réel
  (confirmé par la cartographie exhaustive de session 3 : aucun `system`/`execve`/`popen`/`exit` n'est
  jamais appelé légitimement).
- La primitive #2 (corruption de donnée) ne change RIEN à cette équation : elle ne fait que changer
  *comment* on arrive à poser une mauvaise destination dans `t9` avant un `jalr` — mais la
  DESTINATION finale (`0x4012a8`) reste tout aussi "jamais légitimement atteinte" qu'avec n'importe
  quel ROP à la main. **Si le filtre est destination-based (toute la preuve accumulée sur 5 sessions
  dit qu'il l'est), ce vecteur n'apporte donc AUCUN contournement — il est juste une façon
  différente d'arriver au même mur.**

### Piste n°3 explorée brièvement (handler d'échec canari, `gp-0x7f90` = `0x4a1cd0`)
Déclenché un VRAI mismatch de canari localement, breakpoint sur le `jalr` du handler (`0x400ba0`).
Résultat : `$a0`/`$a1` à ce point ne sont QUE des restes de registres du `printf("Message received")`
précédent (pas un appel dédié avec des arguments spécifiques au handler — aucune instruction entre le
`beq` du check canari et le `jalr` du handler ne pose `a0`/`a1` spécifiquement), ce qui est cohérent
avec un handler de type `__stack_chk_fail`-like qui ignore ses arguments. Le pointeur lui-même
(`0x4a1cd0`) vaut actuellement `0x42b7f0` (la vraie fonction de handling, jamais tracée en détail).
Ce slot EST un site légitimement couvert (il est réellement `jalr`-é chaque fois qu'un canari est
cassé, ce qui arrive normalement si/quand l'attaquant envoie un mauvais canari) — mais le rediriger
vers une destination UTILE (execve/shellcode) retombe exactement dans le même problème que ci-dessus :
la NOUVELLE destination choisie ne serait, elle, toujours pas "légitimement couverte". Pas de nouvelle
piste ouverte par ce test ; cohérent avec un dead-end structurel, pas juste un détail d'implémentation.

### Conclusion de session 6 — recommandation
Le mécanisme de la primitive #2 est **confirmé mécaniquement parfait** (le débogueur tranche cette
question sans ambiguïté), mais ceci ferme la piste plutôt que de l'ouvrir : la seule explication
restante pour l'échec distant (observé en session 5 et cohérent avec 40+ tests antérieurs) est un
filtre CFI/coverage **basé sur la destination réelle de `jr`/`jalr`**, qui bloque TOUTE redirection
vers une adresse jamais naturellement atteinte par ce type d'instruction dans le programme — qu'elle
soit introduite par un gadget ROP classique OU par une donnée corrompue consommée par un `jalr`
déjà légitime. Comme sessions 1-5 l'ont déjà établi de façon exhaustive, **aucune adresse utile
(shell, flag, execve, system) n'est jamais légitimement atteinte par ce programme** — donc ce
vector-là n'a abouti à aucune primitive exploitable supplémentaire.

**Recommandation finale après 6 sessions intensives et 45+ hypothèses testées et réfutées (certaines
avec débogueur réel, byte-level, exécution instruction-par-instruction) : arrêter ce challenge.** Le
rendement est maintenant nul — chaque nouvelle piste retombe systématiquement sur le même mur
destination-based CFI, confirmé cette fois sans la moindre ambiguïté. Les seules voies qui
restent en théorie (obtenir un accès/indice sur l'infrastructure du challenge, ou une fuite de
`envp`/argv — déjà explorée et fermée en session 3) ne sont pas actionnables sans information
externe supplémentaire. Basculer définitivement sur un autre challenge du CTF.

---

## SESSION 7 (2026-10-25) — BREAKTHROUGH : le mur n'est PAS "destination-based CFI" au sens
## "adresse jamais légitimement atteinte" — c'est une granularité de PAGE (4 KiB), et un nouveau
## gadget déjà DANS la bonne page a été trouvé et CONFIRMÉ fonctionnel en direct

### Contexte de reprise
Statut plateforme re-vérifié via l'API (`ctf_platform_client.py show-challenge --id 23`) :
**rien n'a changé** depuis la session 6 — description, `connection_info`
(`169.58.126.107 5005`), fichier unique `vault`, `solves=42`, pas de hints, pas de solution
visible. Le saut 5→42 solves ne vient donc PAS d'une modif de l'énoncé ; il reste un signal
externe pur ("c'est faisable, quelqu'un a trouvé la bonne technique").

Avant toute nouvelle tentative réseau, relecture complète du HANDOFF (6 sessions, 45+ hypothèses)
puis **analyse statique repartie de zéro avec `capstone`** (l'`objdump` local n'a AUCUN support
MIPS — `objdump -i` ne liste même pas `mips` ; c'est pourquoi les sessions précédentes travaillaient
surtout par désassemblage manuel/radare2/gdb). Script réutilisable :
`exploit/disas_capstone.py 0xVMA [0xLENGTH]` (lit directement `attachments/vault`, corrige
`file_offset = vma - 0x400000`, valide uniquement pour `vma >= 0x4002c0`).

### Re-lecture de la corrélation "early-addiu vs late-addiu" (session 3) — elle confond DEUX variables
La session 3 avait trouvé que les 5 seuls gadgets qui marchent à distance sont tous "early-addiu"
(`addiu sp,sp,FRAME` AVANT le `jr`, pas dans son delay-slot) ET tous regroupés dans
`0x4007c8-0x400ba8`. Elle en a déduit une corrélation causale sur le PATTERN D'INSTRUCTION. Mais
**ces deux propriétés (pattern d'instruction ET localisation mémoire) n'ont jamais été testées
indépendamment** — tous les gadgets "late-addiu" testés dans les 6 sessions précédentes
(`0x40eba8`, `0x450b7c`, `0x439be8`, `0x40111c`...) se trouvaient TOUS dans des pages mémoire
*différentes* de celle des 5 gadgets qui marchent. Aucun gadget "late-addiu" **à l'intérieur de la
même page** n'avait jamais été testé.

### Nouveau gadget trouvé par balayage statique de la page 0x400000 (jamais cherché ainsi avant)
Désassemblage complet de `0x4002c0` à `0x400ffc` (la page de 4 KiB qui contient `fcn.00400a84`,
`LOOP_REENTRY`, `GADGET_PIVOT2`, et le point d'entrée d'une fonction glibc interne à `0x4002c0`)
a révélé un gadget jusqu'ici invisible parce qu'il ne matche pas le pattern "early-addiu" recherché
par la session 3, mais qui est dans la MÊME page :

```
GADGET_S0 = 0x400698 :
  lw  $ra, 0x1c($sp)
  lw  $s0, 0x18($sp)
  jr  $ra
  addiu $sp, $sp, 0x20      ; delay-slot -> famille "late-addiu", restaure $s0 (jamais testé)
```
Il appartient à la fonction glibc interne qui commence à `0x4002c0` (pattern `ll`/`sc`/`rdhwr`,
probablement un helper d'init avec verrou — PAS `fcn.00400a84` elle-même, mais dans la même page).

### Test en direct, CONFIRMÉ réussi contre `169.58.126.107:5005`
Chaîne testée (une seule connexion, un seul payload d'overflow, script
`exploit/test_gadget_s0_CONFIRMED_WORKING.py`) :
```
overflow original : saved_fp = buf_start-0x20 ; saved_ra = GADGET_PIVOT2 (0x400854)
GADGET_PIVOT2      : sp = buf_start-0x20 ; ra = mem[buf_start+0xc] = GADGET_S0 (0x400698)
                      sp -> buf_start+0x10
GADGET_S0          : s0 = mem[buf_start+0x28] = 0x41424344 (marqueur, non déréférencé)
                      ra = mem[buf_start+0x2c] = LOOP_REENTRY (0x400c18)
```
Résultat réel observé :
```
resp: b'Message received.\nEnter your name: '
looped_back: True
confirm_echo: b'Hello, CCCCH\nLeave a message for the vault keeper: '
still_alive: True
```
**La boucle survit, confirmé par un ROUND SUPPLÉMENTAIRE (piège `io.connected()` évité).** Ceci
RÉFUTE directement la théorie "early-addiu = pattern qui marche" de la session 3 : ce gadget est
"late-addiu", restaure un registre jamais testé (`$s0`), et **fonctionne quand même**, simplement
parce qu'il est physiquement dans la même page que `GADGET_PIVOT2`/`LOOP_REENTRY`.

### Théorie révisée et consolidée : granularité de PAGE (4 KiB), pas d'adresse exacte
- Tous les gadgets connus pour MARCHER (`0x4007c8`, `0x400854`, `0x40093c`, `0x400a38`, `0x400ba8`,
  `0x400698`=nouveau, `LOOP_REENTRY`, `fcn.00400a84`) sont dans la page **`0x400000-0x400fff`**.
- Tous les gadgets/adresses connus pour ÉCHOUER (`0x40111c`=MPROTECT_STUB, `0x439be8`=GADGET_A,
  `0x450b7c`, `0x40eba8`, `0x4012a8`=exit(), `0x450a7c`=execve) sont dans des pages **différentes**
  (`0x401000`, `0x439000`, `0x450000`, `0x40e000` respectivement) — AUCUNE de ces pages n'est
  "réchauffée" par le flot d'exécution légitime d'une connexion normale.
- Hypothèse "allow-list = valeurs statiques présentes dans `.got`" **testée et réfutée** :
  `0x450a7c` (execve) EST une valeur présente dans `.got` (679 valeurs uniques dans la section
  `.got`, probablement coïncidence sur un binaire de 660 Ko) mais échoue quand même à distance —
  donc ce n'est pas un simple "allow-list de valeurs GOT", c'est bien la PAGE de la destination qui
  compte, pas sa présence dans une table de pointeurs.
- Mécanisme plausible (toujours une hypothèse, pas confirmée avec certitude absolue sans accès
  infra) : un moniteur externe (ptrace/qemu-plugin) qui autorise `jr`/`jalr` vers une page dès que
  cette page a été "vue" par `$pc` pendant le flot d'exécution réellement exercé par CE process
  (pages touchées : `0x400000` car `fcn.00400a84`/boucle y vivent ; `0x409000` car le vrai
  `printf`/`vfprintf` (`0x409590`) y est appelé par `bal` direct à chaque round ; `0x40f000` car
  `"Message received."` y est imprimé (`bal 0x40ff60`) ; `0x427000` car le vrai `read()` (voir
  ci-dessous) y est appelé par `jalr` à chaque round. Les pages jamais naturellement visitées
  (`0x401000`, `0x439000`, `0x450000`, `0x40e000`...) restent bloquées, quel que soit le gadget.

### Pages "GOT" réelles identifiées (dump statique des slots `.got`, `.got` = VMA `0x4a1c70`,
### fichier offset `0x91c70`, section réelle du binaire, PAS une table custom de l'auteur)
```
GUARD_PTR_SLOT       gp-0x7fe0 = 0x4a1c80 -> valeur 0x0049f448 (page 0x49f000)
FMT_BASE             gp-0x7fdc = 0x4a1c84 -> valeur 0x004a0000 (page 0x4a0000, .bss, chaînes décodées)
CANARY_FAIL_HANDLER  gp-0x7f90 = 0x4a1cd0 -> valeur 0x0042b7f0 (page 0x42b000)
PRINTF/VFPRINTF      gp-0x7f80 = 0x4a1ce0 -> valeur 0x00409590 (page 0x409000) *** APPEL DIRECT PAR
                     `bal`, PAS par `jalr` -- corrompre ce slot ne change RIEN au flot réel, $t9
                     n'est chargé que par convention ABI cpic, jamais utilisé pour calculer la
                     destination du saut. Explique pourquoi toute idée de hijack "printf GOT" serait
                     un cul-de-sac, même sans mur CFI.
READ                 gp-0x7f7c = 0x4a1ce4 -> valeur 0x00427770 (page 0x427000) *** APPEL RÉEL PAR
                     `jalr $t9` à CHAQUE round (2x : lecture nom + lecture message) -- SEUL slot
                     dont la valeur influence réellement la destination du saut.
```
`READ` est bien syscall `read` (0xfa3 = 4003 décimal, confirmé par désassemblage du vrai code à
`0x427770`, wrapper glibc avec point d'annulation pthread).

### DÉCOUVERTE CLÉ : `write()` existe dans LA MÊME PAGE que `read()` (0x427000), jamais vérifié
### dans les 6 sessions précédentes (qui ne visaient que execve/exit, tous deux dans des pages FROIDES)
Balayage de toute la page `0x427000` (desassemblage capstone complet) : 16 instructions `syscall`
trouvées (glibc y regroupe visiblement plusieurs petits wrappers syscall). Parmi elles :
```
WRITE_REAL = 0x427890 :
  (même structure que read() à 0x427770 : lui gp,8; addiu gp,...; addu gp,gp,t9;
   addiu sp,sp,-0x30; sw gp,s2,s1,s0,ra...)
  ...
  0x4278c4: addiu $v0, $zero, 0xfa4   ; 0xfa4 = 4004 = sys_write, confirmé
  0x4278c8: syscall
```
`write(a0=fd, a1=buf, a2=len)` prend ses arguments directement depuis les registres appelants
(`a0`/`a1`/`a2`), exactement comme `read()`. **`0x427890` est dans la page `0x427000`, qui est
PROUVÉE "chaude" puisque c'est la page du vrai `read()` déjà appelé à chaque round.**

### Piste actionnable identifiée (NON encore tentée en direct — nécessite de résoudre un point
### mécanique avant d'y aller, voir ci-dessous) : fuite mémoire arbitraire via hijack `READ -> WRITE`
Si on écrit `WRITE_REAL` (`0x427890`) dans le slot `READ` (`0x4a1ce4`, au lieu d'y écrire
`exit()`/`execve()` comme les sessions 5-6 l'avaient tenté — ces deux cibles étaient dans des pages
FROIDES, ce qui explique rétrospectivement leur échec sans contredire le mécanisme découvert cette
session), alors le PROCHAIN appel au site "lecture du message" (`0x400b50-0x400b58`, qui fait
`a0=0 (fixe) ; a1=fp+0x1c ; a2=0x64 ; jalr $t9[slot corrompu]`) appellerait en réalité
**`write(fd=0, buf=fp+0x1c, len=100)`** au lieu de `read()`. Puisque `fd=0` (stdin) est
vraisemblablement `dup2`-é sur le MÊME socket que `stdout` pour ce service "nc"-style (lecture ET
écriture fonctionnent déjà sur ce même fd dans le protocole observé), ceci devrait **renvoyer 100
octets de mémoire à l'adresse `fp+0x1c` directement sur le socket**, où `fp` est le `$fp` du round
EN COURS. **Combiné avec la primitive #1 de la session 5 (`GADGET_PIVOT2 -> LOOP_REENTRY(sp=TARGET)`,
qui permet de choisir `fp_new = TARGET-0x68` donc `fp+0x1c = TARGET-0x4c` arbitraire), ceci donnerait
une PRIMITIVE DE LECTURE MÉMOIRE ARBITRAIRE complète** — la pièce manquante documentée comme
"piste la plus prometteuse" en session 3 pour chercher `envp`/`FLAG=` sans exécution de code.

### Point mécanique NON résolu avant de tenter ceci en direct (à vérifier en priorité à la reprise)
Pour écrire à l'adresse `0x4a1ce4` (le slot `READ`) via la primitive #1, il faut que
`GADGET_PIVOT2` atterrisse avec `sp = 0x4a1ce4` (ou proche), ce qui exige que
`mem[(0x4a1ce4-0x30)+0x2c] = mem[0x4a1ce0]` contienne déjà une adresse "chaude" valide pour le
second `jr` interne à `GADGET_PIVOT2` — **`mem[0x4a1ce0]` est justement le slot `PRINTF/VFPRINTF`,
valeur fixe connue `0x409590`** (donc PAS de crash garanti à cette étape précise, contrairement à
une adresse `.bss` aléatoire), mais atterrir en plein milieu de `printf()` avec un `$t9` non
cohérent (donc un `$gp` recalculé faux dans son prologue `addu gp,gp,t9`) **crashera probablement
au premier accès `gp`-relatif à l'intérieur de `printf`**, avant même d'avoir pu écrire quoi que ce
soit d'utile. La session 5 affirme avoir fait marcher ce pivot pour des deltas jusqu'à `0x4000`
depuis `buf_start`, mais **le mécanisme exact qui évite ce crash n'est pas ré-expliqué avec une
certitude suffisante dans le HANDOFF existant** (hypothèse la plus probable : à petite distance du
`buf_start` réel, `mem[TARGET-4]` tombe encore dans de la VRAIE pile du processus contenant
d'authentiques anciennes adresses de retour légitimes de la chaîne d'appel réelle
`_start -> __libc_start_main -> main -> ... -> LOOP_REENTRY`, qui sont elles-mêmes des adresses
"chaudes" par définition puisqu'elles ont RÉELLEMENT été exécutées comme cibles de retour — mais
ceci n'a pas été vérifié empiriquement cette session, et `0x4a1ce4` est ~0xA0000 octets plus loin
que `buf_start` (~`0x408xxxxx`), bien au-delà de ce qu'un "walk" à petits pas peut couvrir sans
dizaines d'aller-retours réseau, ce qui violerait la consigne de ne pas flooder le service).

**Recommandation concrète pour la prochaine reprise (dans cet ordre) :**
1. **Avant tout nouvel essai réseau**, reproduire le pivot `GADGET_PIVOT2(sp=0x4a1ce4)` **en local**
   via `qemu-mipsel -g` + `gdb-multiarch` (outils déjà présents et documentés plus haut dans ce
   HANDOFF) pour vérifier si l'atterrissage sur `printf()` avec un `$gp` recalculé faux crashe
   réellement ou pas, SANS consommer de tentative réseau.
2. Si ça crashe localement : il faut alors soit (a) trouver une adresse plus proche de `buf_start`
   qui contient déjà, de façon stable et naturelle (donc pas aléatoire par connexion), une valeur
   "chaude" utilisable comme tremplin intermédiaire vers `0x4a1ce4` (chercher dans les VRAIES
   anciennes frames de la pile, visibles via le même gdb local), soit (b) accepter un walk
   multi-round mais le minimiser en sautant par les PLUS GROS pas sûrs possibles (tester en local
   le plus grand delta qui ne crashe pas, pas juste reprendre `0x4000` sans vérification).
3. Une fois le slot `READ` (`0x4a1ce4`) atteint en écriture de façon fiable (confirmé en local
   d'abord), écrire `WRITE_REAL` (`0x427890`) dedans, PUIS dans un round séparé utiliser la
   primitive #1 pour poser `fp+0x1c` = adresse à fuiter (commencer par des adresses PROCHES de la
   pile existante — au-dessus de `buf_start`, où `argv`/`envp`/`__libc_start_main`'s saved registers
   vivent généralement sur MIPS/Linux — avant d'élargir la recherche).
4. Garder `exploit/test_gadget_s0_CONFIRMED_WORKING.py` et `exploit/disas_capstone.py` comme base :
   le premier prouve le mécanisme de pivot double-hop fonctionne pour fixer un registre ET rejoindre
   `LOOP_REENTRY` en toute sécurité ; le second permet de ré-explorer statiquement n'importe quelle
   page du binaire sans dépendre d'un `objdump` qui ne supporte pas MIPS sur cette machine.

### Bilan honnête de cette session (session 7)
**Pas de flag, pas de shell.** Mais une avancée réelle et vérifiée en direct, contrairement aux
sessions 3-6 qui avaient déclaré le challenge "définitivement mort" :
1. La théorie du "mur CFI" des sessions 3-6 est **affinée et corrigée** : ce n'est pas un pattern
   d'instruction ni une liste d'adresses individuelles, c'est une granularité de PAGE mémoire
   (4 KiB), confirmée par un test en direct qui réussit avec un gadget jamais essayé auparavant.
2. Un chemin concret et plausible vers une **primitive de lecture mémoire arbitraire** (via
   `READ`-GOT-slot hijack vers `write()`, les deux dans la même page chaude `0x427000`) est
   identifié, avec un point de blocage mécanique clairement isolé (pivot vers une adresse distante)
   et une méthode de résolution proposée (vérification locale au débogueur AVANT tout essai réseau).
3. Deux connexions réseau seulement consommées cette session (le test `GADGET_S0`, espacé, pas de
   flood). Le flag n'a pas été soumis (aucun shell confirmé, conformément à la règle `max_attempts=1`).
4. **Ne PAS répéter** : la piste `execve`/`exit()` GOT-hijack (sessions 5-6) est bien morte, mais
   maintenant on SAIT pourquoi (pages froides) au lieu de l'attribuer à un vague "mur CFI"
   insondable — ça change la stratégie de recherche pour la suite (chercher des primitives dans les
   pages déjà chaudes, pas dans tout le binaire au hasard).

## SESSION 8 (2026-10-25) — VÉRIFICATION LOCALE (qemu-mipsel + gdb-multiarch, AUCUN essai réseau) du
## pivot longue-distance `GADGET_PIVOT2` vers le slot GOT `READ` (0x4a1ce4) : **MORT, confirmé par
## exécution réelle, pour DEUX raisons mécaniques distinctes et indépendantes, aucune des deux
## liée au "mur CFI par page"**

### Méthode
Reprise de l'outillage documenté en session 2 (`qemu-mipsel -g 1234 ./attachments/vault_dbg` +
`gdb-multiarch -nx -q --batch -x script.gdb`, `$fp` réglé via `$s8`). Trois scénarios testés en
positionnant directement les registres/mémoire à l'état voulu (pas besoin de piloter le vrai
`read()` réseau — on injecte l'état "juste après l'overflow" directement en mémoire, ce qui est
équivalent et strictement plus rapide pour ce genre de vérification mécanique).

### Résultat n°1 (décisif) : la primitive #1 documentée en session 5 ne fait PAS ce que le HANDOFF
### affirme — le registre `$fp` chargé par `GADGET_PIVOT2` est **jeté sans effet**
Test : `GADGET_PIVOT2` entré avec `$fp=F0=0x4a3000` (zone `.bss` scratch, sans rapport avec la
cible), avec `mem[F0+0x28]=FPNEW=TARGET-0x68` et `mem[F0+0x2c]=LOOP_REENTRY`. Trace réelle,
pas-à-pas :
```
Après GADGET_PIVOT2  : sp=0x4a3030 (=F0+0x30)  ra=0x400c18(LOOP_REENTRY)  fp=0x4a1c7c(=FPNEW, chargé OK)
Après LOOP_REENTRY/bal: sp=0x4a3030 (INCHANGÉ — LOOP_REENTRY ne touche jamais $sp)  t9=0x400a84(correct)
Après prologue fcn.00400a84 :
  gp = 0x4a9c60 (recalculé CORRECTEMENT via t9, donc gp n'est PAS le problème)
  sp (après addiu sp,sp,-0x68) = 0x4a2fc8  = (F0+0x30) - 0x68   <-- dérivé de F0, PAS de FPNEW !
  fp_orig_new (après move fp,sp) = 0x4a2fc8  <-- toujours près de F0, FPNEW/TARGET n'a JOUÉ AUCUN RÔLE
```
**Conclusion empirique sans ambiguïté** : `fcn.00400a84` adresse son buffer/canari/saved_fp/saved_ra
via **`$sp`**, pas via `$fp` (le `$fp` qu'on charge dans `GADGET_PIVOT2` est sauvegardé puis
immédiatement écrasé par `move fp,sp` — il ne sert jamais à rien). Et `$sp` au moment du `bal` est
hérité tel quel de `GADGET_PIVOT2` (`sp = F0+0x30`), lui-même dérivé de l'**entrée** `$fp` de
`GADGET_PIVOT2` (ce qu'on appelle ici `F0`, réglé directement et sans aucune contrainte de distance
depuis le `saved_fp` de l'overflow ORIGINAL), **pas** de la valeur chargée À L'INTÉRIEUR de
`GADGET_PIVOT2`. Donc la section "primitive #1 : fp_new = TARGET-0x68 contrôle où atterrit le round
neuf" (session 5) décrit un mécanisme qui **n'existe pas** — ce qui contrôle réellement la
destination, c'est `F0` (l'entrée de `GADGET_PIVOT2`), pas le `fp` qu'il charge.

### Résultat n°2 (décisif) : utiliser directement `F0` proche de la cible pour que `GADGET_PIVOT2`
### atterrisse près du GOT fait planter **`GADGET_PIVOT2` lui-même**, par **NX (page non-exécutable)**
### — PAS par un filtre CFI, PAS par une page non mappée
Puisque c'est `F0` qui compte, pour que le buffer du round neuf tombe exactement sur le slot `READ`
(`0x4a1ce4`), il faut `F0 = 0x4a1d00` (calcul : `fp_orig_new = F0-0x38` ; `buffer = fp_orig_new+0x1c
= F0-0x1c` ; `F0-0x1c = 0x4a1ce4` → `F0 = 0x4a1d00`). Mais `GADGET_PIVOT2` lit `mem[F0+0x2c]`
comme **prochain `$ra`** AVANT même d'atteindre `LOOP_REENTRY`. Valeur réelle, lue directement dans
le fichier (binaire statique, pas d'ASLR/PIE, adresses fixes identiques en local et en distant,
hash SHA256 déjà vérifié identique en session 2) : `mem[0x4a1d2c] = 0x0049f444`.

Test en direct (gdb, exécution réelle, pas une déduction) : `$pc=0x400864` (le `jr $ra` de
`GADGET_PIVOT2`) → `jr` vers `0x49f444` → **`SIGSEGV` immédiat, confirmé par le débogueur**
(`Program received signal SIGSEGV, Segmentation fault. 0x0049f444 in ?? ()`).

**Cause exacte, vérifiée via `readelf -lW`** : `0x49f444` tombe dans le **second segment `LOAD`**
du binaire (`VirtAddr=0x49d2e8, MemSiz=0x83f8, Flags=RW` — **PAS de bit `E`**, contrairement au
premier segment `LOAD` qui contient `.text` avec `Flags=R E`). Toute la zone `.got`/`.data`/`.bss`
(`0x49d2e8`-`0x4a56e0`, qui contient le slot `READ` `0x4a1ce4` ET tout ce qui est "proche" de lui)
est mappée **non-exécutable**. Donc **n'importe quelle valeur lue depuis cette zone et utilisée
comme cible de `jr`/`jalr` provoquera un fault NX**, indépendamment de la théorie "granularité de
page" de la session 7 (qui ne s'applique qu'aux pages du premier segment, exécutable). Ce n'est
donc PAS "le mur CFI qui bloque une page froide" — c'est une violation NX basique, déterministe,
identique en local et en distant puisque les permissions de segment viennent du fichier ELF
lui-même, pas d'un moniteur externe.

**Conséquence** : AUCUNE valeur de `F0` qui place le buffer du round neuf à l'intérieur de
`.got`/`.data`/`.bss` ne peut fonctionner via `GADGET_PIVOT2`, parce que `GADGET_PIVOT2` a besoin de
lire un `$ra` valide et EXÉCUTABLE à `F0+0x2c`, et cette zone ne contient que des pointeurs de
DONNÉES (valeurs typiques `0x49xxxx`/`0x4axxxx`, hors de la zone `.text` `0x400000-0x470c70`), pas
des adresses de code. Le pivot longue-distance "~0xA000 octets" **est mort, point final**, pas
seulement "à vérifier avant d'essayer en direct" — vérifié.

### Résultat n°3 (sur la piste alternative, documentée en session 3/HANDOFF l.84-85) : le
### ret2read direct (`READ_SETUP`, sans `GADGET_PIVOT2`) PEUT écrire au slot GOT, mais crashe 2
### instructions après, avant de pouvoir être réexploité sur la même connexion
Piste alternative testée : au lieu de passer par `GADGET_PIVOT2` (donc sans le problème NX
ci-dessus), rediriger directement `$fp` (réglable sans AUCUNE contrainte de distance depuis
l'overflow ORIGINAL, puisque c'est juste une valeur 32 bits qu'on écrit) vers `fp = TARGET-0x1c =
0x4a1cc8`, pour que le site d'appel natif `read()` (`0x400b40`/`0x400aec`, les DEUX sites — "nom" ET
"message" — ont la MÊME structure) calcule `a1 = fp+0x1c = 0x4a1ce4` = le slot `READ` exactement.
Le `read()` lui-même (`jalr` vers le VRAI `read()`, site déjà chaud, aucun problème NX/CFI puisque
ce n'est qu'une écriture de données, pas un saut) **écrirait réellement nos octets contrôlés
(`WRITE_REAL = 0x427890`) directement dans le slot GOT `READ`** — ce point n'a même pas besoin
d'être re-vérifié, c'est juste un `read(0, 0x4a1ce4, 0x64)`, mécaniquement garanti de fonctionner.

**Mais** juste après le retour du `jalr` (`0x400b5c`/`0x400af0`), l'instruction suivante
(`0x400b60`/`0x400af4` : `lw $gp, 0x10($fp)`) recharge `$gp` depuis `fp+0x10 = TARGET-0xc =
0x4a1cd8`. Valeur réelle à cette adresse (lue directement dans le fichier ET confirmée par
lecture mémoire en direct sous gdb) : **`0x00400000`**, pas `0x4a9c60` (le vrai `$gp`). Test en
direct (gdb, registres réglés pour reprendre exactement à `0x400b60` avec `$gp=0x4a9c60` correct
AVANT cette instruction, pour isoler précisément ce qui casse) :
```
0x400b60 lw gp,0x10(fp)   -> gp devient 0x00400000 (confirmé par lecture registre après stepi)
0x400b64 lw v0,-0x7fdc(gp) -> adresse calculée = 0x400000-0x7fdc = 0x380024
Program received signal SIGSEGV, Segmentation fault. 0x00400b64 in ?? ()
```
**Cause exacte** : `0x380024` est SOUS la plus basse adresse mappée du binaire (`0x400000`, premier
`LOAD`) — accès forcément non mappé, `SIGSEGV` immédiat et déterministe, confirmé par exécution
réelle. **La même structure existe au DEUX sites d'appel natifs `read()`** (nom ET message,
vérifié par désassemblage des deux : `0x400af4` et `0x400b60` font toutes les deux `lw gp,0x10(fp)`
immédiatement après leur `jalr`), donc rediriger l'un ou l'autre ne change rien à ce problème.

**Pourquoi la primitive "ret2read vers .bss" documentée comme fonctionnelle (HANDOFF l.84-85, et la
"frame virtuelle" de la session 3) ne souffre PAS de ce crash** : dans ces cas-là, `TARGET` était
choisi PRÈS du buffer existant (voire = `buf_start` exactement, le seul offset confirmé marcher en
session 3), donc `TARGET-0xc` (le slot `gp` à restaurer) tombe DANS la zone que l'attaquant
contrôle déjà (son propre payload), qui pré-écrit `0x4a9c60` au bon endroit **dans le MÊME envoi**.
Pour une cible VRAIMENT distante comme le GOT, ceci est **structurellement impossible en un seul
coup** : le slot à restaurer (`fp+0x10 = TARGET-0xc`) se trouve TOUJOURS 0x10 octets AVANT le début
de la fenêtre réellement écrite par ce même appel (`a1 = fp+0x1c = TARGET`, octets `[TARGET,
TARGET+0x63]`) — `TARGET-0xc` n'est JAMAIS inclus dans `[TARGET, TARGET+0x63]`. Un
pré-remplissage par un appel SÉPARÉT préalable retomberait exactement dans le même piège de façon
récursive (ce second appel a lui-même besoin que SON PROPRE `fp'+0x10` soit déjà correct).
Recherche exhaustive de la constante `0x4a9c60` dans tout le fichier (`grep` binaire des 4 octets
LE) : **une seule occurrence, dans l'en-tête ELF (`0x400144`), aucune dans `.got`/`.data`/`.bss`** —
donc aucun "ancrage naturel" n'existe nulle part dans le binaire pour casser la récursion.

### Bilan de session 8 — recommandation claire pour la prochaine reprise
1. **Le pivot `GADGET_PIVOT2` longue-distance vers le GOT (`0x4a1ce4`) est définitivement mort,
   vérifié par exécution réelle locale (SIGSEGV reproductible, cause = NX sur le segment
   `.got`/`.data`/`.bss`, pas un mur CFI).** Ne plus y consacrer d'essai réseau.
2. **La réécriture directe du slot `READ` via redirection de `$fp` (sans `GADGET_PIVOT2`) PEUT
   écrire la valeur voulue dans le GOT, mais le process meurt 2 instructions après, avant qu'on
   puisse réutiliser la connexion pour déclencher le `write()` voulu.** Vérifié par exécution
   réelle locale (SIGSEGV reproductible à `0x400b64`/équivalent, cause = mauvais rechargement de
   `$gp` depuis une zone qu'on ne contrôle pas).
3. **Piste non testée cette session, à explorer avant tout nouvel essai réseau** : la question de
   savoir si le process du challenge est **mono-processus persistant servant plusieurs connexions
   TCP successives sans ré-exec** (xinetd/socat en mode "fork" vs un vrai service qui boucle sur
   `accept()` dans le MÊME process). Si c'est le cas, corrompre le slot `READ` puis crasher
   N'EMPÊCHERAIT PAS forcément d'exploiter la corruption sur une **connexion suivante** (le GOT
   resterait corrompu en mémoire pour tout le process). Si au contraire chaque connexion est un
   process/exec frais (très probable pour un setup CTF "nc"-style standard), la primitive #3
   ci-dessus est un **cul-de-sac définitif**, pas seulement "à corriger" — la corruption ne
   survivrait jamais assez longtemps pour être réutilisée. Ceci N'A PAS besoin d'un essai qui
   "risque" quoi que ce soit : un simple test (se connecter, forcer un crash bénin ANYWHERE,
   puis immédiatement se reconnecter et lire la zone `.got` via le leak existant) répond à la
   question sans jamais tenter le hijack réel — recommandé comme SEULE prochaine étape utile
   avant d'abandonner définitivement la piste READ→WRITE GOT-hijack.
4. **Aucun essai réseau n'a été consommé cette session** (vérification 100% locale, qemu-mipsel +
   gdb-multiarch, conformément à la consigne). Les scripts gdb utilisés ne sont pas conservés
   (one-shot, triviaux à reproduire depuis ce texte si besoin), mais la méthode (régler
   `$s8`/`$pc`/`$gp`/`$t9` + mémoire directement à l'état voulu, `stepi` pas-à-pas, `--batch` mode
   pour éviter un prompt interactif bloquant) est réutilisable pour toute future question
   mécanique de ce genre, sans dépendre du vrai chemin réseau `read()`.

## SESSION 9 (2026-10-25) — PROBE DISTANTE MINIMALE (3 connexions) : la piste READ→WRITE GOT-hijack
## est maintenant morte sur DEUX fronts indépendants — même si le crash mécanique de session 8
## n'existait pas, la corruption ne survivrait jamais d'une connexion à l'autre

### Contexte
Suite à la recommandation de fin de session 8 ("un simple test répond à la question sans jamais
tenter le hijack réel"), exécution de ce test exact, en direct, sur `169.58.126.107:5005`
(`connection_info` re-vérifié via `ctf_platform_client.py show-challenge --id 23` juste avant :
inchangé, `solves=42`, aucun hint, aucune solution visible). Script :
`exploit/test_persistence_check.py`. **3 connexions au total, espacées de 3s puis 5s**, aucune
soumission de flag, aucune nouvelle primitive destructive tentée (réutilise uniquement le leak
standard et le crash "garbage ra → GADGET_A" déjà documentés et exercés des dizaines de fois sans
incident depuis la session 3).

### Méthode et résultat exact
```
[A] OK en 0.58s  canary=0x7b10cf00  saved_fp=0x40800c48
[A] payload message avec ra=GADGET_A (0x439be8, gadget mort/page froide, canary correct) envoyé
[A] post-crash resp: b'Message received.\n'   (signature de crash déjà documentée, attendue)
--- attente 3s ---
[B] OK en 0.63s  canary=0x6e961100  saved_fp=0x40800c48
    canary identique à A ? NON   saved_fp identique à A ? OUI
--- attente 5s ---
[C] OK en 0.94s  canary=0xb0826b00  saved_fp=0x40800c48
    canary identique à A ? NON   saved_fp identique à A ? OUI
```
**Les connexions B et C se comportent EXACTEMENT comme des sessions neuves** : prompt `"Enter your
name: "` réapparaît immédiatement, timing normal (<1s, pas de délai/interruption détectable),
leak fonctionne normalement. **Le canari change à chaque connexion** (ré-aléatoirisé, cohérent
avec un nouveau process — mais pas une preuve absolue à lui seul, un process persistant pourrait
aussi re-tirer un canari par connexion). **`saved_fp` reste `0x40800c48` à l'identique**, cohérent
avec les dizaines d'observations déjà documentées dans ce HANDOFF (adresses fixes, pas d'ASLR) —
également pas discriminant à lui seul (un process persistant en boucle `accept()` aurait aussi un
`$fp` de pile inchangé entre itérations).

### Interprétation (raisonnement, pas juste l'observation brute)
Le signal le plus fort n'est PAS le canari ou `saved_fp` individuellement, mais **l'absence totale
de toute interruption/latence/échec de connexion après le crash de A**. Si le binaire vulnérable
tournait comme **un seul process persistant partagé** entre connexions (ex: boucle `accept()`
mono-thread ou multi-thread DANS le même process), le `SIGSEGV` provoqué par le `jr` vers
`GADGET_A` (adresse morte, cf. sessions 3-8) **tuerait ce process au niveau du noyau** — ce qui
couperait IMMÉDIATEMENT toute connexion en cours ET empêcherait d'en accepter de nouvelles, SAUF
si un superviseur externe (systemd/Docker restart/boucle shell/xinetd) relance une instance
fraîche — ce qui, dans TOUS les cas, repartirait avec une **mémoire neuve** (donc là non plus
aucune corruption GOT ne pourrait survivre). Le fait que B arrive **0.63s seulement après la
fermeture de A, sans aucun signe de redémarrage de service (pas de timeout, pas de refus de
connexion, comportement 100% identique à une connexion normale)** est le plus cohérent avec une
architecture **fork/exec-par-connexion** (type `xinetd`/`socat fork`), où le crash de A n'affecte
QUE le process isolé de A — le "service" (listener parent) n'a jamais été interrompu parce qu'il
ne partage JAMAIS sa mémoire de travail avec les process enfants qui traitent chaque connexion.

### Conclusion définitive pour cette piste
**Toute la famille d'idées "GOT-hijack" (sessions 5 à 8, y compris toute variante future de ce
même principe)  est un cul-de-sac, confirmé maintenant sur DEUX fronts indépendants** :
1. **Mécanique (session 8)** : la primitive elle-même plante avant de pouvoir être réexploitée
   SUR LA MÊME connexion (NX sur le pivot longue-distance, mauvais rechargement de `$gp` sur la
   réécriture directe).
2. **Architecture (session 9, cette probe)** : même si (1) n'existait pas, une corruption GOT ne
   survivrait de toute façon PAS d'une connexion à l'autre — chaque connexion repart d'une mémoire
   vierge, confirmé par le comportement 100% normal et immédiat de 2 connexions consécutives
   juste après un crash délibéré.
**Recommandation** : ne plus investir de temps sur CETTE piste (READ→WRITE GOT hijack, ou tout
hijack de pointeur GOT visant à persister un état entre connexions). Si PWN#Beta est repris, se
concentrer uniquement sur des primitives exploitables **en une seule connexion continue** (la
seule piste encore vivante documentée : poser `a1`/argv pour `execve` via la chaîne à 3 pivots de
la section "Bloqueur actuel", ou chercher un AUTRE site d'appel natif gp-relatif encore inexploré
dans les pages déjà chaudes). Sinon, dépriorisation raisonnable de ce challenge au profit d'autres
cibles du CTF — 7+ sessions et 2 pistes majeures (AES/mprotect backdoor, GOT-hijack) maintenant
confirmées mortes avec des causes mécaniques précises plutôt que de vagues "murs CFI".
3 connexions utilisées cette session, aucune soumission de flag.
