"""BitVault treasury co-signer -- the settlement PIPELINE.

The co-signer never relays a draft it has not screened. `cosign_and_settle`
wires the two halves together: it screens the envelope (treasury_screen) and,
only if the screen authorizes it, finalizes the settlement (settlement_relay)
and returns the exact bytes handed to the node.

The post-incident treasury note is sealed under what the co-signer processed
for the envelope that settled: both the draft the screen authorized and the
settlement the relay emitted feed the keystream, so the note opens only for the
envelope the pipeline actually put through on the night of the incident.
`recover_note` rebuilds that keystream and unseals the note.
"""

import hashlib

from settlement_relay import relay_settlement
from treasury_screen import first_segment, screen_draft

# Domain separator for the note seal keystream.
SEAL_SEP = b"|vault-note-seal"

# The treasury post-mortem note, sealed under BOTH parser views of the winning
# envelope (the screened first segment AND the relayed settlement). It is never
# stored in the clear; the keystream is derived from both views the pipeline
# takes of a given envelope. Regenerate with src/gen.py if the format changes.
SEALED_NOTE_HEX = (
    "3c7cf00ab88d4e4a4988d9e16effa1a80f77e4b674a50ced"
    "c5e5e5ad267512eb5d4de2e6bedfd12bc94328de3158b07d7280114a"
)


class DraftRejected(Exception):
    """Raised when the screen refuses to authorize an envelope."""


def cosign_and_settle(envelope: str) -> bytes:
    """Screen an envelope, then relay it. Settlement is emitted only if the
    screen authorizes the draft."""
    if not screen_draft(envelope):
        raise DraftRejected("treasury screen refused the draft")
    return relay_settlement(envelope)


def _keystream(key: bytes, n: int) -> bytes:
    out = b""
    counter = 0
    while len(out) < n:
        out += hashlib.sha256(key + counter.to_bytes(4, "big")).digest()
        counter += 1
    return out[:n]


def recover_note(envelope: str) -> str:
    """Unseal the treasury note for the envelope the pipeline settled.

    The seal key is derived from what the co-signer processed for this envelope:
    the segment the screen authorized (``first_segment``) and the settlement the
    relay emitted (``cosign_and_settle``). Both must come from the one envelope
    the pipeline actually put through.
    """
    raw = cosign_and_settle(envelope)
    seg0 = first_segment(envelope)
    key = hashlib.sha256(seg0.encode() + b"|" + raw + SEAL_SEP).digest()
    ct = bytes.fromhex(SEALED_NOTE_HEX)
    ks = _keystream(key, len(ct))
    return bytes(a ^ b for a, b in zip(ct, ks)).decode("utf-8", "replace")
