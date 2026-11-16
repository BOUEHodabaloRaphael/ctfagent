# NCTF26 #36 imds-ssrf (150pts, cloud/aws/ssrf/imds)

## Status: blackbox-exhausted (notes.enc decryption)

SSRF -> IMDSv2 chain itself is fully understood and already proven in
`artifacts/ssrf-capture.log` (token grab -> role name -> creds via
`/preview?url=`). The remaining blocker is decrypting the sealed operator
note (`artifacts/notes.enc`).

## Evidence confirmed by direct re-read (xxd, full 175 bytes)

```
# operator note (found at /home/ubuntu/notes/handoff.enc)
# sealed: XOR keystream = SHA256(instance role SecretAccessKey)
UaleOfi4jPnGL6ZeGZbuMO2mZa0W5MfTxQ2YBwrYD73PlkP87g==
```
No hidden bytes, extra lines, or trailing garbage after the base64 line
(file ends cleanly with `\n` at offset 0xae). Nothing was missed in the
original text read.

- Ciphertext (base64-decoded): 37 bytes.
- Leaked creds (from `ssrf-capture.log`):
  - AccessKeyId: `ASIAQF4KEKELI0FAKE01`
  - SecretAccessKey: `wJalrFAKEdevSECRETkeyEXAMPLEnotREAL0123456` (**42 chars** — real AWS secret access keys are always exactly **40** base64-alphabet chars; this one is 2 chars long and visibly built from English watermark words: `FAKE`, `SECRET`, `EXAMPLE`, `not`, `REAL`)
  - Token: `IQoJb3JpFAKEdevSESSIONtokenEXAMPLEonly//////////wEXAMPLE==` (real AWS STS session tokens are long opaque base64 blobs; this one also has literal English words spliced in: `FAKE`, `SESSION`, `token`, `EXAMPLE`, `only`)
  - Role: `media-transcoder-role`

## Methods tried (all gave non-ASCII / noise output, scored by printable-ratio heuristic, best result 0.57 vs ~0.95+ needed for real plaintext)

1. XOR with raw `SHA256(secret)` digest, repeated/cycled over 37 bytes.
2. Counter-mode keystream extension: `SHA256(secret + str(i))`, `SHA256(secret + i.to_bytes(4,'big'))`, and a proper HMAC-DRBG-style `HMAC-SHA256(key=SHA256(secret), msg=counter)` chain.
3. Hash chaining: `SHA256(SHA256(secret))`, and a 5-block `SHA256` chain concatenated to cover the full ciphertext length without repetition.
4. `SHA256(secret).hexdigest()` (ASCII hex, both lower/upper case) as the repeated XOR key.
5. All pairwise concatenations tried: `access+secret`, `secret+access`, `secret+token`, `token+secret`, `secret+role`, `role+secret`, `role+"_"+secret`, `role+" "+secret` (literal header phrasing), `access+secret+token`, `access+secret+token+role`, each through SHA256/MD5/SHA1/SHA512, raw digest and hexdigest.
6. `secret` alone, lowercased, uppercased, with trailing digits stripped (`0123456`).
7. `access` alone and `token` alone, hashed with SHA256 (per original ask #5).
8. MD5 as the hash algorithm instead of SHA256, across the same string combinations (per original ask #5) — no improvement, nothing even close.
9. HMAC-SHA256 variants: `key=secret, msg=""`, `msg=access`, `msg=token`, `msg=role`, `msg="handoff.enc"`, `msg="media-transcoder-role"`, and the reverse (`key=access/role/token, msg=secret`).
10. Full AWS SigV4 key-derivation chain (`HMAC(HMAC(HMAC(HMAC("AWS4"+secret, date), region), service), "aws4_request")`) swept over plausible `region` (us-east-1, eu-west-1, ap-southeast-1) x `service` (s3, ec2, sts) x `date` (20260302, 20260101) combos — this was the SigV4-adjacent idea explicitly suggested; none hit.
11. Raw (unhashed) `secret`/`access`/`token` bytes used directly as the repeating XOR key, as a sanity check against a literal misreading of the header.
12. Session token base64-decoded and used directly as key bytes.

None produced printable/ASCII output (all land around 30-57% printable-byte
ratio, i.e. statistical noise — real plaintext recovery should be ~95%+).

## Key suspicion to hand back to the orchestrator

The three leaked credential strings are **not shaped like real AWS secrets**:

- `SecretAccessKey` is 42 chars, not AWS's fixed 40.
- All three values (`AccessKeyId`, `SecretAccessKey`, `Token`) have literal
  English dictionary words (`FAKE`, `SECRET`, `EXAMPLE`, `REAL`, `SESSION`,
  `TOKEN`, `ONLY`, `DEV`, `NOT`) spliced directly into otherwise
  base64/alphanumeric-looking strings — this is the classic shape of a
  **placeholder/template value that was never filled in with real captured
  data**, not an obfuscation or a genuine redaction pattern a CTF author
  would normally use.
- This exact wording also closely mirrors AWS's own public documentation
  example key (`wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`), reinforcing that
  this looks like a stock "EXAMPLE" placeholder rather than a
  challenge-specific secret.

I confirmed this is exactly what's on disk in `artifacts/ssrf-capture.log`
(re-read directly, not relayed) — so if these are genuinely template
placeholders rather than the actual challenge-specific creds, no XOR/HMAC/
SHA256 derivation over them will ever produce the real keystream. **Before
spending more cycles on crypto variants, it's worth re-confirming that
`ssrf-capture.log` really is the authentic capture and not a sanitized/
templated sample** — e.g. by re-running the SSRF chain live against the
actual challenge instance to pull a fresh, non-placeholder-looking
`SecretAccessKey`/`Token` pair, then retrying attempt #1 (plain
`XOR(ciphertext, repeated SHA256(SecretAccessKey))`) with the real value.
That single straightforward reading of the header comment is almost
certainly the intended mechanism once the real secret is in hand.

## Next steps if resumed

1. Re-verify/re-pull `SecretAccessKey` from a live IMDSv2 hit on the actual
   target (not a possibly-sanitized log) — AWS temp creds have no English
   words in them and are always 40 chars for `SecretAccessKey`.
2. Retry the single most literal reading of the header first:
   `XOR(ciphertext, SHA256(real_secret) repeated)`.
3. Only fall back to HMAC/SigV4/counter-mode variants (already swept here)
   if the plain repeat with the real secret still fails.
