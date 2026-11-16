---
doc_kind: workspace-notes
id: sub-wildcard-cloud-aws-oidc
title: "sub-wildcard (cloud/aws/oidc)"
category: cloud
status: solved
tags:
  [aws, oidc, sts, trust-policy, easy]
---
# Notes

## Challenge

NCTF26 jeopardy "sub-wildcard" (id=50, cloud, 150pts, creator hibris/Clawd).
Static handout, 4 files downloaded via signed URLs into `attachments/`:
- `trust-policy.json`
- `role-permissions.json`
- `oidc-token.json` (5 captured tokens)
- `release-secret.json` (sealed)

## Step 1 — trust-policy.json

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::210987654321:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:kekeli-cloud/*"
        }
      }
    }
  ]
}
```

Two conditions must both hold:
- `aud` must equal exactly `sts.amazonaws.com` (`StringEquals`)
- `sub` must match the glob `repo:kekeli-cloud/*` (`StringLike`) — i.e. the literal
  prefix `repo:kekeli-cloud/` followed by anything (AWS `StringLike` wildcard semantics,
  equivalent to shell `fnmatch`, no regex anchoring tricks beyond `*`/`?`).

Critically, the wildcard sits right after the **repository name**, not after a `:ref:`
segment — so this condition only pins down the GitHub *org name* (`kekeli-cloud`), not
which repo in that org, and not which ref/branch. Any repo under `kekeli-cloud`, on any
branch, from any workflow, satisfies it. That's the vulnerability the challenge name
("sub-wildcard") is pointing at.

## Step 2 — role-permissions.json

```json
{
  "RoleName": "ci-deployer",
  "AttachedPolicy": {
    "Statement": [{
      "Sid": "ReadReleaseSecret",
      "Effect": "Allow",
      "Action": ["secretsmanager:GetSecretValue"],
      "Resource": "arn:aws:secretsmanager:us-east-1:210987654321:secret:prod/release-signing-*"
    }]
  }
}
```
Once assumed, `ci-deployer` can read `prod/release-signing-*` from Secrets Manager —
matches `release-secret.json`'s `ARN` (`prod/release-signing-key-a1b2c3`). Confirms the
secret file is the target resource reachable after a successful assume-role.

## Step 3 — oidc-token.json: evaluate all 5 captured tokens against the condition

Checked programmatically with Python's `fnmatch.fnmatchcase(sub, "repo:kekeli-cloud/*")`
(case-sensitive glob — exact AWS `StringLike` semantics) AND `aud == "sts.amazonaws.com"`
for every token:

| # | sub | aud ok | StringLike match | why |
|---|-----|--------|-------------------|-----|
| 1 | `repo:acme-corp/media-svc:ref:refs/heads/main` | yes | **NO** | wrong org entirely |
| 2 | `repo:kekeli-cloud-staging/media-svc:ref:refs/heads/main` | yes | **NO** | look-alike org: after literal `repo:kekeli-cloud` the policy requires `/` next, but this sub has `-staging/` — `-` != `/`, breaks the required prefix `repo:kekeli-cloud/` |
| 3 | `repo:kekeli-cloud/media-svc-fork:ref:refs/heads/feature/x` | yes | **YES** | exact prefix `repo:kekeli-cloud/` present, then `*` matches the rest (`media-svc-fork:ref:refs/heads/feature/x`) — **StringLike `*` imposes no constraint on repo name or ref**, so a fork repo on an attacker's feature branch still matches |
| 4 | `repo:kekelicloud/media-svc:ref:refs/heads/main` | yes | **NO** | missing hyphen — `kekelicloud` != `kekeli-cloud`, prefix fails immediately |
| 5 | `repo:kekeli/cloud-media-svc:ref:refs/heads/main` | yes | **NO** | org path split differently (`kekeli` org, `cloud-media-svc` repo) — `/` appears one segment too early, prefix `repo:kekeli-cloud/` never literally occurs |

Verified in a clean Python (`-I`, isolated) interpreter — see
`attachments/` analysis; all `aud` values are identical (`sts.amazonaws.com`) so `aud`
never discriminates between tokens; the whole puzzle rides on the `StringLike` `sub`
match alone. **Only token #3 satisfies the trust policy.**

This is the intended trap: it *looks* like an attacker/fork token (`actor: mallory`,
branch `feature/x`, repo `media-svc-fork`) and is commented "attacker fork inside the
trusted org" — but because the policy's wildcard sits after the repo-name segment
instead of pinning `ref:refs/heads/main` and the exact repo, this "attacker" token is
exactly the one that legitimately satisfies the condition as written. The real lesson:
a `StringLike` wildcard placed one segment too early turns an org-scoped trust policy
into "any repo, any branch, any workflow in this org."

sub that satisfies the policy:
```
repo:kekeli-cloud/media-svc-fork:ref:refs/heads/feature/x
```

"Showing it can assume the role" = demonstrating this exact `fnmatch`/`StringLike`
match above (no live AWS endpoint in this static challenge — proof is the condition
evaluation, documented above and reproducible with the snippet in Step 3).

## Step 4 — release-secret.json: unsealing

```json
{
  "Name": "prod/release-signing-key",
  "ARN": "arn:aws:secretsmanager:us-east-1:210987654321:secret:prod/release-signing-key-a1b2c3",
  "Note": "SecretString is sealed for this handout: XOR keystream = SHA256(<the OIDC sub that satisfied the trust policy>).",
  "SecretStringCiphertextB64": "UBa/0poXIVt143vUSiSrhIzVi2c0lSuSwbMgzybCknkvfFBvuMcaOw=="
}
```

Ciphertext (base64-decoded) is 40 bytes — longer than a single SHA-256 digest (32 bytes),
so a naive repeating-key XOR over the raw digest produces garbage. The correct keystream
generation is **CTR-style extension**: concatenate successive
`SHA256(digest || counter_as_4_bytes_big_endian)` blocks until there's enough keystream,
then XOR byte-by-byte with the ciphertext.

```python
import base64, hashlib
sub = "repo:kekeli-cloud/media-svc-fork:ref:refs/heads/feature/x"
ct = base64.b64decode("UBa/0poXIVt143vUSiSrhIzVi2c0lSuSwbMgzybCknkvfFBvuMcaOw==")
digest = hashlib.sha256(sub.encode()).digest()

def keystream_ctr(digest, length):
    out, counter = b"", 0
    while len(out) < length:
        out += hashlib.sha256(digest + counter.to_bytes(4, "big")).digest()
        counter += 1
    return out[:length]

ks = keystream_ctr(digest, len(ct))
pt = bytes(c ^ k for c, k in zip(ct, ks))
print(pt.decode())   # NCTF{oidc_sub_wildcard_assumed_the_role}
```

Result decodes cleanly to 40 bytes of printable ASCII in valid `NCTF{...}` format —
confirms both the correct `sub` value and the correct keystream construction (no
truncation/garbage, no padding artifacts).

## Flag

```
NCTF{oidc_sub_wildcard_assumed_the_role}
```

- validated findings:
  - Trust policy `StringLike` wildcard on `sub` is placed right after the repo-name
    segment (`repo:kekeli-cloud/*`), not after a pinned `ref:` — any repo/branch/workflow
    under org `kekeli-cloud` satisfies it.
  - Of 5 captured tokens, only token #3 (`repo:kekeli-cloud/media-svc-fork:ref:refs/heads/feature/x`,
    actor `mallory`) matches via Python `fnmatch.fnmatchcase` (AWS StringLike semantics).
  - Secret unseals with XOR keystream = CTR-chained SHA256(matching sub || counter),
    not a naive repeated single digest.
  - Flag: `NCTF{oidc_sub_wildcard_assumed_the_role}` (NOT submitted — human action).
- dead ends:
  - Naive repeating 32-byte SHA256 digest as XOR key -> garbage (ciphertext is 40 bytes,
    not a multiple of 32).
  - Hex-ASCII of digest as repeating key -> also garbage.
  - Simple hash-chaining (h, sha256(h), sha256(sha256(h)), ...) without counter bytes ->
    also garbage (first block matches raw-digest attempt since it's the same first
    32 bytes, diverges after).
