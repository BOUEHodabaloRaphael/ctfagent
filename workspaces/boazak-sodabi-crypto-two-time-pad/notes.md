---
doc_kind: workspace-notes
id: boazak-sodabi-crypto-two-time-pad
title: "boazak-sodabi (crypto two-time-pad)"
category: crypto
status: solved
tags:
  [crypto, xor, two-time-pad, key-reuse]
---
# Notes

## Challenge

NCTF26 jeopardy "boazak--sodabi" (id=413, crypto, 100pts, creator:KodjoDoDjango).
Classic two-time-pad: same XOR keystream reused for two messages. c1 = flag (encrypted),
c2 = public known-plaintext message (also given in the same file).

## Attachment

Downloaded `attachments/challenge.txt`:
```
Two-time pad (XOR key reuse)
============================
Le même flux de clé XOR a chiffré deux messages : le flag et un message public connu.
c1 = 8ffff4c3d0ba362e540bb291cd1af41205cfb7c024dfa86fa3d01c7e086a8e51
c2 = 83d3ceefc49c7446402ae6adef09c83e23dc979b37edfc2ee982432f1f2fcd4e91f47ce4c557f1c6eeb622c686f020ef1f463cc80b42512244cc7c4ee1b695ca453c846a4b78d6583c4c
known = Bonjour, ceci est un message public pour verifier la cle XOR du challenge.
```

So, unlike the generic methodology (crib-dragging), the literal known plaintext for c2
was given directly in the file — no guessing needed.

## Method

- c1 (32 bytes) is shorter than c2 (74 bytes) == len(known) (74 bytes). Same keystream,
  used as a prefix for the shorter message (typical keystream/stream-cipher reuse).
- key = c2 XOR known  (74 bytes recovered)
- flag = c1 XOR key[:32]

## Validated findings

Python (byte-for-byte XOR, run with `python3 -I`):
```python
c1 = bytes.fromhex("8ffff4c3d0ba362e540bb291cd1af41205cfb7c024dfa86fa3d01c7e086a8e51")
c2 = bytes.fromhex("83d3ceefc49c7446402ae6adef09c83e23dc979b37edfc2ee982432f1f2fcd4e91f47ce4c557f1c6eeb622c686f020ef1f463cc80b42512244cc7c4ee1b695ca453c846a4b78d6583c4c")
known = b"Bonjour, ceci est un message public pour verifier la cle XOR du challenge."

key = bytes(a ^ b for a, b in zip(c2, known))
flag = bytes(a ^ b for a, b in zip(c1, key[:len(c1)]))
```

Output:
- `key.hex()` = `c1bca085abe9066a604983ce8629ad4d57fce2f51780995d9ae3244a3f5fb82cfd9d1fc4b53884b4cec047b4ef96498a6d6650a92b213d476494331cc1d2e0ea2654e506271db83f5962`
- Sanity check: decrypting c2 with this key reproduces `known` exactly (`check == known` → True), confirming the key derivation is correct.
- `flag` = **`NCTF{S0D4B1_K3Y_R3U53_129384756}`** — clean ASCII, matches `NCTF{...}` format.

## Submission

Submitted via `nctf26_client.py submit` (see below for exact result).
