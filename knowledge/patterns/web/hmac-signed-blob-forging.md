---
doc_kind: pattern
title: "HMAC-signed opaque blob tampering (Gob/JSON framing + leaked key)"
category: web
slug: hmac-signed-blob-forging
created: 2026-11-01
status: active
tags:
  - hmac
  - signature-forging
  - qr-code
  - token-tampering
  - integrity-bypass
chain_summary: "A Base64 opaque blob (QR code, token, ticket) wraps a JSON/structured object between fixed prefix/suffix framing bytes plus a trailing fixed-size HMAC signature; once the signing key leaks (e.g. via an SSTI env-leak), locate the JSON boundary, edit fields while preserving exact byte length (pad with spaces/garbage), and recompute the HMAC to forge an arbitrary valid signed object."
---
# HMAC-signed opaque blob tampering (Gob/JSON framing + leaked key)

## Chain Summary

- One-line chain: A Base64 opaque blob (QR code, token, ticket) wraps a JSON/structured object between fixed prefix/suffix framing bytes plus a trailing fixed-size HMAC signature; once the signing key leaks (e.g. via an SSTI env-leak), locate the JSON boundary, edit fields while preserving exact byte length (pad with spaces/garbage), and recompute the HMAC to forge an arbitrary valid signed object.
- Typical target shape: any "opaque" value the app treats as tamper-proof without a visible crypto scheme in the client — QR codes, "ticket"/ "voucher" tokens, signed cookies/session blobs, deep-link tokens, webhooks payload signatures — especially ones produced by backend languages/serializers with a recognizable binary framing (Go's `encoding/gob`, Java serialization magic bytes, MessagePack, protobuf) wrapping a human-readable JSON/text core.

## Preconditions

- You can obtain at least one legitimate instance of the blob (e.g. your own account's QR/token) to study its structure.
- A signing/HMAC key for the blob has leaked or is guessable/derivable (env var leak via SSTI/LFI, hardcoded default, weak key, key reuse with another leaked secret).
- The blob's integrity check is a symmetric MAC (HMAC-SHA*, or a keyed hash) rather than an asymmetric signature (RSA/ECDSA) you can't forge from a leaked *verification* key alone.

## Cheap Probes

- Base64-decode the blob and eyeball the raw bytes: look for a recognizable binary prefix (Gob starts predictably, Java serialization starts with `\xac\xed`, MessagePack/protobuf have their own tells) and a trailing block whose length matches a known MAC size (16 bytes = MD5/HMAC-MD5, 20 = SHA1, 32 = SHA256, 48 = SHA384, 64 = SHA512).
- Search the decoded bytes for a JSON object start (`{"` or a known field name like `{"PNR"`) to locate the human-readable payload embedded inside the binary framing.
- Once a key is leaked (see `ssti-file-read-proc-environ-secret-leak`), recompute the MAC over the untouched blob and confirm it matches the trailing signature bytes exactly — this proves the key and algorithm guess before attempting any tampering.

## Escalation Order

1. Decode a legitimate blob to bytes; identify prefix framing, the embedded JSON/text payload span, any suffix framing, and the trailing MAC block size.
2. Parse the JSON payload with a streaming/position-aware decoder (e.g. Python `json.JSONDecoder().raw_decode()`) to get its *exact* byte span rather than assuming it runs to end-of-string.
3. Confirm the candidate key reproduces the original MAC over the unmodified bytes (`hmac.compare_digest`) before changing anything.
4. Edit the JSON payload (add/modify fields) and re-serialize it; if the framing requires a fixed total length (common with Gob and other length-prefixed/fixed-slot formats), pad the new JSON with a filler byte (spaces are usually safe and ignored by JSON parsers around tokens, but verify) to exactly match the original byte length — do not change the overall blob length unless you've confirmed the framing tolerates it.
5. Recompute the MAC over `prefix + new_payload + suffix` with the leaked key, append it, Base64-encode, and submit. Verify the recomputed MAC locally with `hmac.compare_digest` before sending.
6. Look for additive fields the backend will trust-and-act-on once the signature check passes — unexpected/undocumented fields (like a `NotifyCmd`-style command/action field) are high-value since they're gated purely by the signature, not by any other authorization check.

## Common Mistakes

- Assuming the JSON payload runs to a fixed offset or to end-of-string instead of actually parsing it, which breaks the framing-length invariant the binary wrapper expects.
- Changing the forged JSON's byte length without padding, corrupting any fixed-size framing (Gob and similar formats often encode lengths elsewhere, so you only get away with this if you independently confirm it).
- Trying asymmetric-signature attacks (key confusion, parameter injection) on what is actually a plain symmetric HMAC — check the MAC's byte length and whether a single symmetric key reproduces it before reaching for heavier algorithm-confusion techniques.
- Forgetting to locally verify the forged MAC (`hmac.compare_digest`) before submitting, which wastes a probe/attempt cycle discovering a byte-counting or key mistake server-side instead of locally.

## Payload Shapes

```python
raw = base64.b64decode(blob)
pos = raw.find(b'{"PNR"')          # locate JSON start by a known field name
tail = raw[pos:-32]                # strip the trailing 32-byte HMAC-SHA256
obj, end = json.JSONDecoder().raw_decode(tail.decode())
old_json = tail[:end]
suffix = tail[end:]                # remaining framing bytes after the JSON

obj['NotifyCmd'] = "<injected action/command>"
new_json = json.dumps(obj, separators=(',', ':')).encode()
assert len(new_json) <= len(old_json), "forged JSON must not exceed original length"
body = raw[:pos] + new_json + b' ' * (len(old_json) - len(new_json)) + suffix

signature = hmac.new(leaked_key, body, hashlib.sha256).digest()
forged = base64.b64encode(body + signature).decode()
```

## Related Writeups

- `knowledge/writeups/web/htb-takeoff-ssti-hmac-forge-n8n-bindmount.md`

## Skill Impact

- Related skill: `web-triage` (add a dedicated "signed opaque blob" branch alongside JWT handling)
- Rule to add or update: whenever a JWT-style or other opaque "signed token" check is in scope, don't assume JWT — inspect raw bytes for non-JWT framing (Gob, Java serialization, custom binary) wrapping a JSON core with a trailing fixed-size MAC, and treat any leaked backend secret as a candidate forging key for it. Primed for reuse during NCTF26.
