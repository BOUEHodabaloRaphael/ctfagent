"""BitVault treasury co-signer -- draft SCREEN (authorizer).

This is the exact source of the policy screen that runs inside the 2-of-2
treasury co-signer. Before a settlement is ever relayed to the network, the
screen re-reads the draft envelope and confirms the payout still matches the
operation the desk approved (pay the treasury vault, carrying the two required
desk endorsements). Only an approved draft is allowed onward to the relay.

A co-sign envelope is a marker-prefixed concatenation of one or more draft
segments (see ENVELOPE_FORMAT.md). A normal draft is a single segment. The
screen reads the FIRST segment -- that is the draft the desk signed.
"""

import json

# Wire marker that prefixes every draft segment in a co-sign envelope.
SEGMENT_MARKER = "BVLT-COSIGN/2|"

# The operation the treasury desk approved for this co-sign cycle: a single
# payout to the vault's own change script, keeping 10_000 sat as the relay fee.
APPROVED_PAYS = [
    {"script": "76a914b0bfa5e2c1d3e4f5a6b7c8d9e0f1a2b3c4d5e6f788ac", "sats": 499990000}
]

# A treasury draft is only valid once both desk officers have endorsed it.
MIN_ENDORSEMENTS = 2


def first_segment(envelope: str) -> str:
    """Return the first draft segment of a co-sign envelope.

    The desk signs the leading segment, so that is the one the screen trusts.
    """
    return envelope.split(SEGMENT_MARKER)[1]


def screen_draft(envelope: str) -> bool:
    """Authorize a co-sign envelope for settlement.

    Returns True iff the draft pays exactly the approved payout and carries the
    required number of desk endorsements.
    """
    draft = json.loads(first_segment(envelope))
    if draft.get("pays") != APPROVED_PAYS:
        return False
    if len(draft.get("endorsements", [])) < MIN_ENDORSEMENTS:
        return False
    return True
