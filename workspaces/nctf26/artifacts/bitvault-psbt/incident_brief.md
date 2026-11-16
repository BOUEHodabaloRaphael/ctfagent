# Incident brief -- BitVault treasury drain

The BitVault treasury desk approved a single routine payout last cycle (the
payroll batch in `signed_draft.txt`): pay `499990000` sat back to the vault
change script `76a914b0bfa5e2c1d3e4f5a6b7c8d9e0f1a2b3c4d5e6f788ac`, keeping
`10000` sat as the relay fee. Both desk officers endorsed that draft.

What actually settled on-chain was **not** that payout. The co-signer relayed a
settlement that swept the _entire_ draft input value to an address nobody on the
desk recognizes. The payroll draft's two inputs funded it, and there was no
change output -- the fee was taken too.

Forensics recovered the broadcast settlement's single output from the node's
mempool capture:

```
drain_script = 0014deadbeefcafebabe0011223344556677889900ab
drain_sats   = 500000000
```

The desk left a sealed post-mortem note (`SEALED_NOTE_HEX` in `cosigner.py`)
keyed to the settlement the co-signer _actually relayed_, so that only whoever
can reconstruct the drain -- exactly as the co-signer processed it -- can open
it. Reconstruct the envelope that drove that settlement through the pipeline and
recover the note.
