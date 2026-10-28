# VulCreator.sys — HITCON CTF 2026 — Analyse statique (pwn, kernel Windows)

Challenge: `vulcreator` — auteurs crédités Angelboy & TwinkleStar03
Fichier: `workspaces/hitcon-vulcreator/vulcreator/VulCreator.sys`
Méthode: **analyse statique en lecture seule uniquement** (r2/radare2, rabin2, objdump, strings).
Aucune exécution, aucun accès à une machine Windows. Toutes les adresses citées sont des RVA/VA
du fichier tel que chargé par r2 avec base `0x140000000`.

## 1. Identification du binaire

```
VulCreator.sys: PE32+ executable for MS Windows 10.00 (native), x86-64, 8 sections
bits     64        subsys   Native        pic      true
cc       ms        nx       true          signed   true
compiled Mon Oct 19 05:02:52 2026         cmp.csum 0x0000be42
```

Sections (`rabin2 -S`):

| section | vaddr        | taille | perm | rôle |
|---|---|---|---|---|
| `.text`  | 0x140001000 | 0x2000 | r-x | code principal (dispatch IRP) |
| `fothk`  | 0x140003000 | 0x1000 | r-x | thunks CFG (vide / `int3`, pas de dispatch indirect réel observé) |
| `.rdata` | 0x140004000 | 0x1000 | r-- | IAT, chaînes, SDDL |
| `.data`  | 0x140005000 | 0x1000 | rw- | données globales |
| `.pdata` | 0x140006000 | 0x1000 | r-- | unwind info |
| `PAGE`   | 0x140007000 | 0x2000 | r-x | code paginable (helpers secondaires) |
| `INIT`   | 0x140009000 | 0x1000 | r-x | `DriverEntry` (entry0) |
| `.reloc` | 0x14000a000 | 0x1000 | r-- | relocations |

Imports notables (`rabin2 -i`): **`TDI.SYS: TdiRegisterDeviceObject`, `TdiDeregisterDeviceObject`**
+ `ntoskrnl.exe`: `IoCreateDevice`, `ObReferenceObjectByHandle`, `ObfDereferenceObject`,
`IoFileObjectType`, `ExAllocatePool2`, `ExFreePoolWithTag`, `ExInitializeRundownProtection`,
`ExAcquireRundownProtection`/`ExReleaseRundownProtection`/`ExWaitForRundownProtectionRelease`,
`KeInitializeSpinLock`, `KeAcquireSpinLockRaiseToDpc`, `RtlCompareMemory`,
`SeConvertStringSecurityDescriptorToSecurityDescriptor`, `IoCreateDeviceSecure` (string),
`IoValidateDeviceIoControlAccess` (string).

→ **Ce n'est pas un driver WDM classique répondant à `DeviceIoControl()`**. Il importe
`TdiRegisterDeviceObject`/`TdiDeregisterDeviceObject` : c'est un **pseudo-fournisseur TDI
(Transport Driver Interface)**, le mécanisme legacy utilisé par `afd.sys`/`tcpip.sys` avant WSK.
Il crée un device `\Device\VulCreator` et s'enregistre comme transport TDI.

Chaînes clés (`rabin2 -zz`):

```
\Device\VulCreator                                   (nom du device)
D:P(A;;GA;;;SY)(A;;GA;;;BA)(A;;GRGW;;;BU)             (SDDL du device)
ConnectionContext                                     (nom d'EA reconnu)
TransportAddress                                       (nom d'EA reconnu)
IoCreateDeviceSecure
IoValidateDeviceIoControlAccess
```

### SDDL — surface d'attaque pour un utilisateur non privilégié

`D:P(A;;GA;;;SY)(A;;GA;;;BA)(A;;GRGW;;;BU)` :
- `SY` (SYSTEM) et `BA` (Administrateurs) ont `GA` (Generic All)
- **`BU` (Built-in Users, donc *tout* utilisateur authentifié non-admin) a `GRGW`
  (Generic Read + Generic Write)**

→ N'importe quel processus utilisateur non privilégié peut ouvrir `\Device\VulCreator`
(`CreateFileW`) et parler au driver. C'est la condition nécessaire pour une LPE kernel —
confirmée statiquement, pas besoin de dynamique pour ça.

## 2. DriverEntry et table MajorFunction

`entry0` (0x140009000, section `INIT`) appelle `fcn.14000902c` (init runtime) puis
`fcn.1400019b0(DriverObject, RegistryPath)` qui est le vrai `DriverEntry` :

```asm
lea  rdx, [u"\Device\VulCreator"]
call RtlInitUnicodeString                 ; -> var_50h (nom du device)
lea  rdx, [u"D:P(A;;GA;;;SY)(A;;GA;;;BA)(A;;GRGW;;;BU)"]
call RtlInitUnicodeString                 ; -> var_60h (SDDL)
; rep stosq rdi=[DriverObject+0x70] count=0x1c (28) valeur=défaut 0x1400015c0
;   => remplit les 28 entrées MajorFunction[] avec un stub générique par défaut
mov [DriverObject+0x70], 0x140001310      ; MajorFunction[0]  IRP_MJ_CREATE
mov [DriverObject+0x80], 0x140001250      ; MajorFunction[2]  IRP_MJ_CLOSE
mov [DriverObject+0xe8], 0x140001420      ; MajorFunction[15] IRP_MJ_INTERNAL_DEVICE_CONTROL
mov [DriverObject+0x100],0x140001190      ; MajorFunction[18] IRP_MJ_PNP
mov [DriverObject+0x68], 0x140001930      ; DriverUnload
call fcn.14000708c(DriverObject, &nom, &sddl, DeviceType=0x12, ...)  ; IoCreateDeviceSecure
call TdiRegisterDeviceObject(DeviceObject, &var_50h)
```

**Point important : `IRP_MJ_DEVICE_CONTROL` (index 14, offset `+0xE0`) n'est PAS
personnalisé** — il reste sur le stub par défaut (`0x1400015c0`, probablement
`STATUS_INVALID_DEVICE_REQUEST` / passthrough). Un `DeviceIoControl()` « classique »
depuis l'espace utilisateur ne fait donc **rien d'intéressant**.

La vraie « table d'IOCTL » du challenge est en réalité le dispatch
**`IRP_MJ_INTERNAL_DEVICE_CONTROL`** (0x140001420), avec un code de requête lu dans
`IoStackLocation->MinorFunction` (style TDI classique : les clients TDI envoient des
requêtes typées — CONNECT, DISCONNECT, SEND, SET_EVENT_HANDLER, QUERY/SET_INFORMATION,
etc. — via `MinorFunction`, pas via un `IoControlCode` `DeviceIoControl`). Normalement ce
chemin n'est atteignable que depuis le kernel (un vrai client TDI appelant `IoCallDriver`),
pas directement par un `NtDeviceIoControlFile` utilisateur — ce qui suggère que
l'exploit prévu passe soit par un harnais/loader fourni par les organisateurs qui
construit lui-même l'IRP interne, soit par un relais kernel existant (AFD/TDI compat).
Ce point reste à confirmer en dynamique (hors de portée ici).

## 3. Handlers identifiés et structure de contexte par handle

### 3.1 `fcn.140001000` — garde commune (rundown protection)

Utilisée par CREATE/CLOSE/INTERNAL_DEVICE_CONTROL : `lock cmpxchg [DeviceExtension+8],0`
puis `ExAcquireRundownProtection` — protège le `DeviceExtension` contre un déchargement du
driver pendant qu'une requête est en cours. Classique, pas de bug visible ici.

### 3.2 `fcn.140001040(state, size)` — allocateur du contexte par handle

```asm
; size = (size_arg == 0) ? 0xD0 : size_arg + 0xCC
ExAllocatePool2(Flags=0x40, size, Tag='CfTi')
RtlZeroMemory(buf, size)                 ; fcn.140003020 wrapper
buf[0x00] = 'CTDI'                       ; magique
buf[0x04] = state                        ; <-- valeur passée TELLE QUELLE par l'appelant
buf[0xC8] = size_arg                     ; mémorisation de la taille demandée
KeInitializeSpinLock(buf+0x08)
```

Structure récupérée (`Context`, tag pool `'CfTi'`) :

| offset | champ |
|---|---|
| +0x00 | magic `'CTDI'` (0x49445443) |
| +0x04 | `state` (entier, voir ci-dessous) |
| +0x08 | `KSPIN_LOCK` |
| +0x10..+0xB8 | table de 11 slots (index 0..10), 16 octets/slot = `{handler_fn, handler_ctx}` |
| +0xC0 | pointeur d'objet référencé (FILE_OBJECT* d'un endpoint « connecté ») |
| +0xC8 | taille demandée à la création (copie de `size_arg`) |
| +0xCC..+0xCC+size_arg | zone de données (adresse TDI embarquée, voir §4) |

### 3.3 `IRP_MJ_CREATE` (0x140001310) — création d'un endpoint

Lit `IoStackLocation->Parameters.Create.EaLength` et `Irp->AssociatedIrp.SystemBuffer`
(buffer d'EA façon `NtCreateFile` avec `EaBuffer`/`FILE_FULL_EA_INFORMATION`) :

- si `EaLength == 0` → `fcn.140001040(state=3, size=0)` → contexte « neutre » (taille 0xD0,
  state=3, aucune action possible dessus tant qu'il n'a pas été réassocié).
- si `EaLength != 0` → `fcn.14000169c(EaBuffer, EaLength, &outCtx)` (voir §4).

### 3.4 `fcn.14000169c` — parseur d'EA (`ConnectionContext` / `TransportAddress`)

Parse une entrée `FILE_FULL_EA_INFORMATION` (NextEntryOffset@0, Flags@4, EaNameLength@5,
EaValueLength@6, EaName@8, EaValue@8+EaNameLength) et reconnaît deux noms :

- **`"ConnectionContext"`** (17 car.) : exige `EaValueLength == 8`, valeur 8 octets ≠ 0.
  → `fcn.140001040(state=2, size=0)` (taille 0xD0, état 2 → débloque le chemin
  « release / disconnect » du dispatcher, cf. §5).
- **`"TransportAddress"`** (16 car.) : exige `EaValueLength == 0x16 (22)` et un format figé
  (`AddressType==1`, `AddressLength==2`, octets de structure fixes) →
  `fcn.140001040(state=1, size=22)` (taille allouée = `22+0xCC = 0xE2 = 226` octets),
  **puis copie la valeur EA dans le nouveau buffer avec**:
  ```asm
  movups xmm0, [EaValue+0]      ; 16 octets
  movups [NewCtx+0xCC], xmm0
  movsd  xmm1, [EaValue+0x10]   ; 8 octets (SSE2 movsd = 8 octets, pas l'instruction x86 "movs")
  movsd  [NewCtx+0xDA], xmm1
  ```
  → **24 octets copiés** (16+8) dans un buffer dont la zone de données ne contient que
  `size_arg = 22` octets utiles (de `+0xCC` à `+0xCC+22 = 0xE2`, qui est exactement la fin
  de l'allocation). La copie écrit jusqu'à `+0xCC+24 = 0xE4`, soit **2 octets au-delà de la
  fin du chunk pool alloué** (0xE2).
  → état 1 → débloque le chemin « set event handler » du dispatcher (cf. §5).

## 4. VULNÉRABILITÉ PRINCIPALE (statique, vérifiée par désassemblage)

**Débordement de pool kernel de 2 octets (heap overflow) dans la création d'un endpoint
« TransportAddress », causé par une incohérence entre la taille validée de l'EA
(`EaValueLength == 22`, vérifiée strictement à `fcn.14000169c+0x1af`) et la taille réellement
copiée dans le buffer alloué (24 octets, via `movups`+`movsd` à `fcn.14000169c+0x1e1..0x1f3`).**

- Taille allouée pour la zone de données : `size_arg(=22) + 0xCC = 0xE2` octets → la zone de
  données valide va de `Context+0xCC` à `Context+0xCC+0x16 = Context+0xE2` (fin exacte du
  chunk `ExAllocatePool2` tag `'CfTi'`).
- Copie effective : `Context+0xCC` → `Context+0xCC+0x18 = Context+0xE4` (24 octets).
- **Les 2 derniers octets copiés proviennent de données situées juste après la valeur d'EA
  déclarée, dans le buffer d'EA fourni par l'utilisateur** (lu hors-limites côté lecture
  aussi, mais ce buffer appartient à l'attaquant donc il en contrôle totalement le contenu —
  il lui suffit de placer 2 octets arbitraires immédiatement après son EA value de 22 octets
  dans son propre buffer `EaBuffer`).
- Ces 2 octets sont donc **entièrement contrôlés par l'attaquant** et sont écrits dans la
  mémoire kernel **immédiatement après le chunk pool non-paginé `'CfTi'`** — typiquement le
  header du chunk pool suivant (ou du padding d'alignement selon l'allocateur
  Segment Heap / NonPagedPoolNx de Windows 10+), ce qui est le point d'entrée classique
  pour corrompre les métadonnées d'un chunk voisin ou le début des données d'une structure
  adjacente.

### Chemin d'atteinte (reachability), 100% statique

1. Process utilisateur non privilégié (`BU` suffit, cf. SDDL §1) ouvre
   `\Device\VulCreator` via `NtCreateFile`/`CreateFileW` en fournissant un buffer d'EA
   (`FILE_FULL_EA_INFORMATION`) avec `EaName = "TransportAddress"` et
   `EaValueLength = 22`, valeur formatée pour passer les contrôles
   (`AddressType=1`, champ longueur à `2`, offsets `+0xd`/`+0xf` imposés), **et 2 octets
   arbitraires juste après cette valeur de 22 octets dans le buffer EA** (toujours sous
   contrôle utilisateur puisque c'est le même buffer).
2. `IRP_MJ_CREATE` (0x140001310) → `fcn.14000169c` → validation EA → `fcn.140001040`
   alloue 0xE2 octets taggés `'CfTi'`.
3. `fcn.14000169c` copie 24 octets (au lieu de 22) dans la zone de données →
   **2 octets après la fin de l'allocation sont écrasés avec des données attaquant**.

### Primitive secondaire trouvée dans le dispatcher `IRP_MJ_INTERNAL_DEVICE_CONTROL` (0x140001420)

Un deuxième sous-chemin de requête (celui qui exige `Context->state == 1`, donc atteignable
*seulement après* être passé par la création « TransportAddress » ci-dessus) écrit
**deux pointeurs 64 bits totalement contrôlés par l'attaquant** (`handler_fn`,
`handler_ctx`, lus directement depuis les paramètres de la requête, sans aucune validation
d'adresse, de mode d'accès précédent, ni `ProbeForRead`) dans la table de callbacks
`Context+0x10 + index*16` (adresses 0x140001524-0x140001552), avec seulement :
- un contrôle de magique `'CTDI'`,
- un contrôle `state == 1`,
- un contrôle de borne sur l'index (`0 <= index <= 10`),
mais **aucun contrôle sur la valeur des pointeurs eux-mêmes**. C'est une primitive
classique d'« injection de pointeur de callback arbitraire » (CWE-822) : si un des 11 slots
est un jour invoqué par le driver ou par le fournisseur de transport associé (TDI) avec le
pointeur `handler_fn` comme adresse de code, on obtient l'exécution de code en mode noyau.
**Aucun site d'appel indirect (`call reg`/`call [reg]`) n'a été trouvé dans `VulCreator.sys`
lui-même** — recherché systématiquement sur tout le désassemblage (`grep` sur
`call\s+(r[a-z0-9]+|\[r[a-z0-9]+)`, 0 résultat hors imports). L'invocation de ces callbacks
se ferait donc soit par un composant externe (le vrai sous-système TDI, hors de portée de ce
binaire), soit cette table est surtout utile comme **primitive d'écriture arbitraire dans
une zone de pool connue** (16 octets contrôlés, à un offset choisi parmi 11, dans un objet
dont on peut apprendre/forcer l'adresse via le bug de débordement ci-dessus), à combiner
avec le débordement de 2 octets pour une stratégie de *pool grooming* classique.

## 5. Table récapitulative des « codes de requête » du dispatcher interne (0x140001420)

Le code lit `R8 = IoStackLocation` (via `Irp+0xB8`), `FileObject = [R8+0x30]`,
`Context = FileObject->FsContext ([FileObject+0x18])`, vérifie `Context->magic=='CTDI'`,
puis bascule sur `code = IoStackLocation->MinorFunction` (`[R8+1]`) :

| code (`MinorFunction`) | état requis | action | handler |
|---|---|---|---|
| 1 | `Context->state == 1` requis en interne pour le peer | référencer un handle utilisateur (`ObReferenceObjectByHandle`, `IoFileObjectType`), valider que l'objet distant est aussi un endpoint `'CTDI'` du **même DeviceObject**, en `state==1`, puis `cmpxchg Context+0xC0` pour « connecter » les deux endpoints (écrit le `FILE_OBJECT*` distant dans notre `+0xC0`, échoue si déjà connecté) | `fcn.1400010ac` |
| 2 | `Context->state == 2` requis | « déconnecter » : échange `Context+0xC0` avec 0, puis `ObfDereferenceObject()` sur l'ancienne valeur si non nulle | inline (0x14000155b) |
| 11 | `Context->state == 1` requis | **écrit `(handler_fn, handler_ctx)` fournis par l'appelant** dans la table de callbacks `Context+0x10+index*16`, `index` ∈ [0,10], sous spinlock — **aucune validation des pointeurs** (primitive décrite en §4) | inline (0x14000151a) |
| 12 | — | délègue à `fcn.140001810(DeviceExtension, Context, &buf, Irp)` (non entièrement analysé — candidat à une analyse complémentaire) | `fcn.140001810` |
| autre | — | `STATUS_NOT_SUPPORTED` (0xc00000bb) | — |

`IRP_MJ_CLOSE` (0x140001250) : vide `FileObject->FsContext`/`FsContext2`, si `state==2`
relâche l'objet `+0xC0` (même logique que code 2), efface le magique et
`ExFreePoolWithTag(Context,'CfTi')`. Protégé par `ExAcquireRundownProtection` sur le
`DeviceExtension`, pas par un verrou par-contexte — une course entre deux requêtes
*internes* concurrentes sur le même handle et sa fermeture n'est pas formellement exclue
par la seule lecture statique (candidat secondaire à tester en dynamique, confiance plus
faible que le bug de §4).

## 6. Stratégie d'exploitation théorique (nécessite validation dynamique Windows)

1. **Primitive principale** : ouvrir `\Device\VulCreator` avec EA `"TransportAddress"`
   (22 octets de valeur formatés pour passer les checks + 2 octets de bourrage
   arbitraires juste après dans le buffer EA utilisateur) → débordement contrôlé de
   2 octets en fin de chunk `'CfTi'` (0xE2 octets, NonPagedPool).
2. **Pool grooming** : allouer/libérer des objets de taille proche (0xE2, tag/size-class
   partagé) pour positionner un objet cible juste après le chunk `'CfTi'` qu'on va faire
   déborder (technique standard de corruption de pool Windows 10+, Segment Heap/LFH).
   Candidats cibles classiques : header du chunk suivant (`PoolHeader`, pour forcer une
   taille/une libération incohérente → *arbitrary free primitive*), ou les 2 premiers
   octets d'un objet voisin dont la corruption partielle a un effet exploitable
   (ex. un champ de longueur, un flag, le low word d'un pointeur si on dispose d'un leak
   partiel au préalable).
3. **Primitive secondaire (callback table)** : une fois une fuite d'adresse kernel obtenue
   via (2), utiliser le code 11 du dispatcher pour écrire un pointeur de fonction/contexte
   choisi à un offset connu — soit directement si un site d'invocation externe (TDI/AFD)
   existe réellement (à confirmer dynamiquement), soit comme simple primitive d'écriture
   16 octets supplémentaire pour accélérer la construction d'un write-what-where complet.
4. Objectif final typique pour ce genre de challenge kernel HITCON : élévation de
   `_EPROCESS.Token` du processus exploitant vers le jeton `SYSTEM`, ou écrasement d'un
   pointeur de fonction largement invoqué (ex. un callback système) pour obtenir
   l'exécution de code arbitraire en ring 0, puis lecture du flag protégé côté noyau.

## 7. Limites de cette analyse

- Analyse 100% statique (r2/rabin2/objdump), aucune exécution, conforme à la contrainte de
  l'engagement (pas de VM Windows disponible).
- `fcn.140001810` (code de requête 12) n'a pas été entièrement désassemblé — à creuser pour
  compléter la cartographie des primitives disponibles.
- Le mécanisme exact par lequel `IRP_MJ_INTERNAL_DEVICE_CONTROL` est atteint depuis
  l'espace utilisateur (loader fourni par les organisateurs ? composant TDI existant sur la
  VM cible ?) n'a pas pu être confirmé sans le harnais/loader du challenge (absent du
  dossier fourni ici — seul `VulCreator.sys` a été remis). À vérifier en priorité si
  d'autres fichiers d'attachement (loader, client, README du challenge) sont disponibles.
- La mesure exacte de l'exploitabilité du débordement de 2 octets (quel layout pool réel,
  quelle build Windows 10/11 utilisée par les organisateurs) nécessite une VM Windows et le
  binaire `tcpip.sys`/allocator exact de la cible — hors de portée ici.
- Aucun flag n'a été récupéré (attendu : nécessite exploitation dynamique sur Windows).

## 8. Reproduire l'analyse

```bash
rabin2 -I VulCreator.sys                # infos PE
rabin2 -z  VulCreator.sys               # chaînes dans sections connues
rabin2 -zz VulCreator.sys               # chaînes brutes (inclut noms EA, SDDL)
rabin2 -S  VulCreator.sys               # sections
rabin2 -i  VulCreator.sys               # imports (TDI.SYS + ntoskrnl.exe)
r2 -A VulCreator.sys
  afl                                   # liste des fonctions détectées
  pdf @ entry0                          # DriverEntry (wrapper)
  pdf @ fcn.1400019b0                   # DriverEntry réel (table MajorFunction, SDDL, device)
  pdf @ fcn.140001420                   # IRP_MJ_INTERNAL_DEVICE_CONTROL dispatcher
  pdf @ fcn.140001310                   # IRP_MJ_CREATE
  pdf @ fcn.140001250                   # IRP_MJ_CLOSE
  pdf @ fcn.14000169c                   # parseur EA "ConnectionContext"/"TransportAddress" (bug ici)
  pdf @ fcn.140001040                   # allocateur de contexte ('CfTi', magic 'CTDI')
  pdf @ fcn.1400010ac                   # handler "connect" (code 1)
```
