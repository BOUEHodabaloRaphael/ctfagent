"""BitVault treasury co-signer -- settlement RELAY (mock broadcaster).

This is the exact source of the relay that hands a finalized settlement to the
network layer. It takes a co-sign envelope, canonicalizes it, and emits the
deterministic settlement bytes the node then broadcasts.

Canonicalization note (added during the signing-roundtrip work): drafts that
came back from the officers sometimes carried metadata preambles stacked in
front of the real draft, so the relay settles the FINAL envelope segment -- the
freshest one -- rather than whatever happened to lead the blob.
"""

import json

# Wire marker that prefixes every draft segment in a co-sign envelope.
SEGMENT_MARKER = "BVLT-COSIGN/2|"


def last_segment(envelope: str) -> str:
    """Return the final draft segment of a co-sign envelope.

    Canonicalization: strip any accumulated preamble and settle the freshest
    segment the officers handed back.
    """
    return envelope.split(SEGMENT_MARKER)[-1]


def canonical_settlement(draft: dict) -> bytes:
    """Serialize a draft into the deterministic settlement the node broadcasts.

    The relay trusts that the screen already authorized this draft, so it does
    not re-check the payout here -- it just lays out the inputs and outputs in a
    fixed order and ships the bytes.
    """
    lines = [b"SETTLE/2"]
    for sp in draft["spends"]:
        lines.append(
            b"vin " + sp["ref"].encode() + b" " + str(int(sp["sats"])).encode()
        )
    for pay in draft["pays"]:
        lines.append(
            b"vout " + pay["script"].encode() + b" " + str(int(pay["sats"])).encode()
        )
    return b"\n".join(lines)


def relay_settlement(envelope: str) -> bytes:
    """Finalize a co-sign envelope into broadcastable settlement bytes."""
    draft = json.loads(last_segment(envelope))
    return canonical_settlement(draft)
