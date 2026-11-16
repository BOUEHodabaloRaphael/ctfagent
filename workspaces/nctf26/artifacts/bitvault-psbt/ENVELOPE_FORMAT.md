# BVLT-COSIGN/2 envelope format

The BitVault treasury co-signer passes drafts around as **co-sign envelopes**.
An envelope is one or more _draft segments_, each introduced by the wire marker:

```
BVLT-COSIGN/2|
```

A draft segment is a JSON object:

```json
{
  "spends":       [ { "ref": "<txid>:<vout>", "sats": <int> }, ... ],
  "pays":         [ { "script": "<scriptPubKey hex>", "sats": <int> }, ... ],
  "endorsements": [ "<desk endorsement token>", ... ],
  "tag":          "<free-text label>"
}
```

- `spends` — the UTXOs the settlement consumes (outpoint + value in sat).
- `pays` — the settlement outputs (output script + value in sat).
- `endorsements` — the desk officers' co-sign tokens. A valid treasury draft
  carries at least two (2-of-2).
- `tag` — an operator label; ignored by the settlement bytes.

## Wire form

An envelope is the marker followed by the first segment, optionally followed by
more marker+segment pairs:

```
BVLT-COSIGN/2|{...segment 0...}BVLT-COSIGN/2|{...segment 1...}...
```

A normal, well-formed draft is a **single** segment. Multi-segment envelopes
only ever appeared internally during the signing roundtrips, when drafts picked
up metadata preambles on their way back from the officers.

## Pipeline

A draft travels through two co-signer components before it hits the network:

1. **screen** (`treasury_screen.py`) authorizes the envelope against the
   approved payout and the endorsement quorum.
2. **relay** (`settlement_relay.py`) canonicalizes the envelope and emits the
   deterministic settlement bytes the node broadcasts.

`cosigner.py` wires them together (`cosign_and_settle`): nothing is relayed
unless the screen authorizes it first.
