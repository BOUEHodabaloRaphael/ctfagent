# algorithme123--tisserands-dapaong (id 447, stego, 150pts)

Status: SOLVED (flag found, not submitted — central submission policy, main agent submits).

## Files
- README_vitrine.txt — decoy ("Aucun message secret dans ce fichier." — red herring, QR/vitrine unrelated)
- affiche.png — 900x1200 RGB PNG, carries the real payload
- guide-motifs.pdf — decoding key

## Evidence chain

1. `exiftool affiche.png` → Comment field:
   "Note atelier: la fibre primaire (canal rouge) porte le fil du message; longueur puis motifs — voir guide."
   => message is in the RED channel LSBs; a length field comes first, then the message ("motifs").

2. `pdftotext guide-motifs.pdf`:
   ```
   Consonnes et chiffres: glyphe latin (n->N ... s->S r->R b->B).
   Hex a reste une voyelle (glyphe [circle U+25CB] sur l'affiche), pas la lettre B.
   Voyelles: uniquement sur l'affiche officielle.
   Le fil rouge (fibre primaire) porte le message tisse.
   Lecture: longueur uint32 big-endian puis motifs UTF-8.
   ```
   => Read uint32 BE length from red-channel LSB stream (row-major), then that many bytes = UTF-8 message.
   => One decoded character comes back as the glyph "○" (U+25CB) instead of ASCII — the guide explicitly says
      this circle glyph is hex digit `a` kept as a vowel, i.e. decodes to the letter "A" (explicitly NOT "B").

3. Extraction script (`workspaces/nctf26-tisserands/extract_lsb.py`): read every pixel row-major,
   take `R & 1`, pack 8 bits/byte. First 4 bytes (big-endian) = declared length = 39.
   Next 39 bytes decoded as UTF-8:

   ```
   NCTF{D4P40NG_T1SS3R4NDS_29549DB55○2C}
   ```

4. Apply the guide's substitution (○ → "A", per "Hex a reste une voyelle ... pas la lettre B"):

   **Flag: `NCTF{D4P40NG_T1SS3R4NDS_29549DB55A2C}`**

## Raw command outputs (key ones)

`exiftool affiche.png` (excerpt):
```
Comment                         : Note atelier: la fibre primaire (canal rouge) porte le fil du message; longueur puis motifs — voir guide.
Software                        : atelier-tissage-vitrine/0.3
```

`pdftotext -layout guide-motifs.pdf -`:
```
Guide motifs ? Dapaong Terre & Fibres (extrait)
Consonnes et chiffres: glyphe latin (n->N ... s->S r->R b->B).
Hex a reste une voyelle (glyphe ? sur l'affiche), pas la lettre B.
Voyelles: uniquement sur l'affiche officielle.
Le fil rouge (fibre primaire) porte le message tisse.
Lecture: longueur uint32 big-endian puis motifs UTF-8.
```

`python3 extract_lsb.py`:
```
Declared length (bytes): 39
Total available bytes in red channel: 135000
RAW: b'NCTF{D4P40NG_T1SS3R4NDS_29549DB55\xe2\x97\x8b2C}'
UTF-8: NCTF{D4P40NG_T1SS3R4NDS_29549DB55○2C}
```

## Submission attempt 1 (main agent, 2026-11-06) — REJECTED

`NCTF{D4P40NG_T1SS3R4NDS_29549DB55A2C}` → platform replied **"Incorrect"**.

## Re-analysis after rejection

`guide-motifs.pdf` also renders (as raster text on `affiche.png`, not in the PDF)
a line: `Legende voyelles (affiche): a=? e=? i=? o=? u=?` — all five vowel glyphs
render as the *same* pixel-identical tofu/notdef box even at 30x nearest-neighbor
zoom (checked), so the glyph shape itself is a dead end / red herring; it carries
no distinguishing visual signal.

Re-read of the PDF sentence: "Hex a reste une voyelle (glyphe [X] sur l'affiche),
pas la lettre B." — parses as "In Hex[adecimal], 'a' remains a vowel (kept as a
vowel, i.e. **lowercase**, unlike consonants which get uppercased per the b->B
rule given one line above), not the letter B."

Cross-check against the decoded suffix itself: `29549DB55_2C` contains `D` and
`B` — both are hex-alphabet **consonants** (b,c,d,f) and both already appear
**uppercase**, consistent with "consonnes et chiffres: glyphe latin uppercase
(b->B)". The missing glyph sits exactly where a hex **vowel** letter (a or e)
would go. Combined with "a reste une voyelle" (stays as the vowel, i.e. stays
lowercase) and "pas la lettre B" (don't confuse with uppercase), the self-
consistent reading is: hex letter `a`, kept **lowercase**, i.e. the suffix is a
12-hex-nibble string `29549db55a2c` written with case signaling letter type
(digits unchanged, consonant hex-letters uppercase, vowel hex-letters lowercase).

**Corrected flag (not yet submitted): `NCTF{D4P40NG_T1SS3R4NDS_29549DB55a2C}`**
(same as attempt 1 but lowercase `a` instead of uppercase `A`).

One submission used already — confirm this reasoning holds before firing again
(art. 7: no retry spam).

## Submission attempt 2 (main agent, 2026-11-06) — REJECTED

`NCTF{D4P40NG_T1SS3R4NDS_29549DB55a2C}` → **"Incorrect"**.

## Status: blackbox-exhausted (2 reasoned attempts, both rejected)

Both the uppercase and lowercase readings of the vowel-hex hint failed. The
vowel-legend on the poster is confirmed visually undistinguishable (pixel-
identical tofu glyphs across a/e/i/o/u even at 30x zoom), so matching the
embedded `○` (U+25CB) to a specific vowel needs a signal we don't have yet.
Per team instruction, moving on to another challenge rather than guessing a
3rd time. If resumed: try (a) `e` instead of `a` (hex vowel letters are only
a/e, so only two real candidates — e untested), (b) re-check whether the
09-hex-digit prefix `29549DB55` itself needs any case correction too (we
assumed it's all literal/correct because it decoded as clean ASCII, but the
guide's case rule could apply there as well if any of those chars are
secretly consonant-glyphs we didn't notice), (c) ask organizers/Discord hint
channel (human-only channel, out of agent scope).
