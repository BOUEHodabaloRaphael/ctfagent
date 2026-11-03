---
doc_kind: pattern
title: "MD5/SHA1 length-extension attack forging a custom protocol MAC"
category: misc
slug: md5-length-extension-custom-protocol-mac
created: 2026-11-03
status: active
tags:
  - md5
  - sha1
  - length-extension
  - hash-extension-attack
  - custom-protocol
  - mac-forgery
  - merkle-damgard
chain_summary: "A custom binary/text protocol authenticated as MAC = H(secret || message) with a naive Merkle-Damgard hash (MD5/SHA1/SHA256, not HMAC) lets an attacker who captures one legitimate (message, MAC) pair reinterpret the MAC as the hash internal state and resume compression on attacker-chosen appended data, producing a valid MAC for secret||message||glue_padding||appended_data without ever learning secret; unknown secret length is simply brute-forced/bounded by trial."
---
# MD5/SHA1 length-extension attack forging a custom protocol MAC

## Chain Summary

- One-line chain: A custom binary/text protocol authenticated as MAC = H(secret || message) with a naive Merkle-Damgard hash (MD5/SHA1/SHA256, not HMAC) lets an attacker who captures one legitimate (message, MAC) pair reinterpret the MAC as the hash internal state and resume compression on attacker-chosen appended data, producing a valid MAC for secret||message||glue_padding||appended_data without ever learning secret; unknown secret length is simply brute-forced/bounded by trial.
- Typical target shape: a custom binary or text protocol (internal RPC, IoT/pivot protocol, signed webhook, file-signature scheme) that authenticates messages with a hand-rolled `MAC = H(secret || message)` construction using a plain Merkle-Damgard hash (MD5, SHA1, or unpadded SHA256), rather than HMAC.

## Preconditions

- At least one legitimate `(message, MAC)` pair is observable/capturable (network capture, log file, disk artifact, a HELLO/handshake frame, etc.).
- The verifier recomputes `H(secret || message)` itself and compares — i.e. the hash's *internal chaining* is the only thing standing between the attacker and forging new signed data; there is no HMAC-style double-hash or random nonce binding the MAC to a specific session.
- The protocol accepts "message" as effectively attacker-extensible (e.g. a length-prefixed or delimiter-based field the attacker can append to) and doesn't separately validate overall message length/format in a way that rejects the length-extension's glue-padding bytes as garbage.

## Cheap Probes

- Identify the hash algorithm from MAC length (16 bytes = MD5, 20 bytes = SHA1, 32 bytes = SHA256) and from any protocol spec/strings in a reversed binary.
- Check whether a captured MAC, reinterpreted as 4×32-bit (MD5) or similar words, can be fed back into a from-scratch reimplementation of the hash's compression function as a *starting state* and reproduce expected behavior on a zero-length append — confirms the hash construction is naive concatenation, not HMAC.
- If `secret` length is unknown, it's usually small in CTF contexts (bound it by brute-forcing small lengths, e.g. 0-64 bytes, and checking which produces a forged MAC the server accepts).

## Telltale Evidence

- Protocol/binary strings or disassembly show something like `hash(secret + message)` or `hash(key || data)` rather than a named HMAC call — naive concatenation is usually visible directly in reversed code or leaked source.
- A captured legitimate frame includes both the raw message bytes and the MAC in a format where the message's length is also knowable/inferable (needed to compute correct length-padding).

## Escalation Order

1. Capture one legitimate `(message, MAC)` pair (pcap, disk artifact, handshake frame, log) and determine the exact byte length of `message` as the verifier sees it (protocol framing, not just the "visible" payload — include any implicit prefix fields).
2. Reimplement the target hash's compression function manually (readily available pseudocode for MD5/SHA1/SHA256 compression rounds) so it can resume from an arbitrary internal state rather than only from the fixed IV.
3. Compute the hash's own length-padding (`0x80` + zero bytes + 64-bit big/little-endian bit-length, per algorithm) for `secret_len + original_message_len`, where `secret_len` may need to be brute-forced/bounded if unknown — try each candidate length and check which produces a MAC the server accepts on a trivial forged append.
4. Feed `attacker_data` through the compression function starting from the state recovered from the captured MAC (reinterpreted as the hash's internal registers), after first appending the computed glue-padding — this produces `new_mac` valid for `secret || original_message || glue_padding || attacker_data`.
5. Send `original_message || glue_padding || attacker_data` with `new_mac` to the target verifier — it validates successfully without the secret ever being known, because the hash function itself provides no cryptographic separation between "end of message" and "more data appended."

## Common Mistakes

- Using a length-extension helper tool (e.g. `hashpump`) blindly without accounting for the target protocol's own framing — the "message" the hash actually covers often includes protocol-level length/type prefixes not visible in the application-layer payload, and a 1-byte miscalculation anywhere breaks the whole forged MAC.
- Assuming `secret` must be recovered — it never needs to be; only its *length* matters, and that's discoverable by trial (the forge either verifies or it doesn't).
- Reimplementing the compression function with the wrong endianness or initial constant table for the specific hash variant — verify against a handful of known test vectors (e.g. `hashlib.md5(b"").hexdigest()`) before trusting the from-scratch implementation on live protocol data.

## Payload Shapes

```text
# conceptual, hash-agnostic (MD5 shown, same shape for SHA1/SHA256 with their own IV/round tables)
known_mac          = H(secret || known_message)               # captured
state              = reinterpret(known_mac)                   # as internal a,b,c,d (MD5) / h0..h4 (SHA1) etc.
glue_padding        = H.padding_for(len(secret) + len(known_message))   # requires knowing/bruteforcing len(secret)
forged_message      = known_message || glue_padding || attacker_data
new_mac             = H.compress(attacker_data, starting_state=state)   # resumed compression, not from scratch
# send (forged_message, new_mac) to the verifier -> validates without ever learning `secret`
```

## Related Writeups

- [AFRICC 2027 Qualifiers — full writeup](../../writeups/misc/africc2027-quals-full-writeup.md) — "Kaldvik" (Boot2Root, 75pts), stage 4: forging a `KVX1` protocol frame's MD5 MAC to pivot to an internal host.

## Skill Impact

- Related skill: none of the current triage skills cover custom-protocol crypto attacks directly; closest is `web-triage`'s general posture of reading source/protocol before brute-forcing.
- Rule to add or update: if a future challenge exposes a custom signed binary protocol (not plain JWT/HMAC), check for naive `H(secret||message)` MAC construction early — it's a strong, cheap-to-confirm win before investigating more exotic crypto.
