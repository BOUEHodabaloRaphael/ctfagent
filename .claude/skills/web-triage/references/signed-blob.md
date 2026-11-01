# Signed Opaque Blob Triage (non-JWT)

Use this when a feature carries an "opaque" value the app treats as
tamper-proof but it does not decode as a JWT (no two dots, no `eyJ` header).
Examples: QR code payloads, voucher/ticket tokens, signed cookies produced by
a non-JWT serializer.

Treat it as a short SOP; the full escalation order, probes, and worked
payload shapes live in `knowledge/patterns/web/hmac-signed-blob-forging.md`
— read that first, this file only routes to it.

## Quick Checks

1. Base64-decode the blob and look at the raw bytes for binary framing
   (Go `encoding/gob`, Java serialization `\xac\xed`, MessagePack, protobuf)
   wrapping a JSON/text payload.
2. Measure the trailing byte count after the payload — 16/20/32/48/64 bytes
   strongly suggests a keyed MAC (MD5/SHA1/SHA256/SHA384/SHA512).
3. If any secret has leaked elsewhere in the chain (see
   `knowledge/patterns/web/ssti-file-read-proc-environ-secret-leak.md`),
   try it as the MAC key by recomputing over the untouched blob and
   comparing to the trailing signature.

## When It Matches

Route to `knowledge/patterns/web/hmac-signed-blob-forging.md` for: locating
the JSON span with a streaming decoder, editing fields while preserving the
exact byte length (padding), recomputing the MAC, and re-encoding.

## Exit Conditions

- The value decodes as a standard JWT → use `jwt.md` instead.
- No trailing fixed-size byte block and no recognizable binary framing →
  probably not a signed blob; reconsider the evidence.
