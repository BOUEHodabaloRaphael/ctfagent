# Pattern — Overflow d'un buffer global (.bss/.data) → flip d'un drapeau d'état adjacent

**Quand :** un buffer **global** (en `.bss`/`.data`, adresse fixe si ELF ET_EXEC / no-PIE) est rempli par
une lecture dont la taille **dépasse** la taille du buffer, et une **variable d'état** (drapeau
`is_admin`/`is_auth`/`unlocked`/role) vit juste après dans la même zone, dans la portée de la lecture.

**Reconnaissance :**
- `file` → ET_EXEC (pas de PIE) = adresses fixes, pas besoin de leak.
- `objdump -d -M intel` / Ghidra : repérer `buf = 0x4040xx` global, une init `[buf+off]=0`, un
  `read/fgets/recv(..., N)` avec **N > sizeof(buf)**, puis un `test/cmp [buf+off]` qui débranche vers la
  voie privilégiée (`reveal()`, flag, shell).
- Symboles non strippés : la taille du buffer et l'offset du drapeau se lisent directement.

**Exploit :** écrire `off` octets de padding + ≥1 octet **non-nul** à l'offset du drapeau. Pas de contrôle
de RIP, pas de ROP — on écrase juste une **globale adjacente**. Déterminer la frontière par dichotomie
(off octets échouent, off+1 réussit).
```bash
python3 -c "import sys; sys.stdout.buffer.write(b'A'*OFF + b'\x01')" | ./chall
```

**Variantes :** le drapeau peut être un pointeur de fonction/role global → l'écraser vers une autre valeur ;
ou le flag est chiffré en `.rodata` et révélé seulement après le flip (reproduire la routine de déchiffrement
offline, souvent un simple XOR/clé constante, cf. `objdump -s -j .rodata`).

**Cas source :** [[nctf-bss-overflow-flip-admin-flag]] (buffer `.bss` 72 o, `read(,,0x80)`, drapeau admin
à l'offset 64, flag XOR 0x3c).
