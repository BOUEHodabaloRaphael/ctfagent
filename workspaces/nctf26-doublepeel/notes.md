# thierry8petstar--doublepeel (misc, 100pts)

Status: HANDED OFF to user — stopping agent work here per instruction ("laisse
le chall la, je vais m'en charger").

## Challenge
Photo (`Good_Luck.jpg`, 4000x3000, EXIF stripped) of a desk: backlit 60%
keyboard (E-YOOSO), phone, mouse, a "NCTF INVESTIGATE" note, and a biscuit
pack. Story: Grace D. typed her password in "only a few seconds" before an
emergency call — prompt asks whether that proves it was short (implying:
no, think about WHY it was fast instead — e.g. a worn/known key pattern or a
finger-friendly layout, not necessarily few characters).

## Lead found before handoff
Under high zoom (`kb_zoom1.png`), the **R key (between E and T) has no
legend at all** — looks physically worn/blank, unlike every surrounding key
which clearly shows its letter under the backlight. Classic "most-used key
loses its printed legend from friction" tell. Was about to scan the rest of
the board (`kb_zoom2.png`, `kb_zoom3.png` — right half + bottom rows, crops
made but not yet reviewed) for other blank/worn keycaps to build a candidate
character set for the password.

Separate observation, likely a red herring: several keys (5,6,8,-,T,F,G,V,B)
glow visibly dimmer/greyer than the rest under backlight — but this matches
a known mixed-opacity "pudding keycap" batch pattern (same exact cluster
shape), so probably just a keyboard-kit manufacturing artifact, not a clue.

## Artifacts
`workspaces/nctf26-doublepeel/artifacts/`: `Good_Luck.jpg` (original),
`keyboard_crop.png`, `keyboard_enhanced.png`, `kb_zoom1.png`, `kb_zoom2.png`,
`kb_zoom3.png`.

No flag guessed or submitted.
