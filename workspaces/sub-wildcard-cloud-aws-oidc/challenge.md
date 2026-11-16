---
doc_kind: challenge
id: sub-wildcard-cloud-aws-oidc
title: "sub-wildcard (cloud/aws/oidc)"
category: web
platform: manual
platform_id: ""
url: "N/A (static files)"
status: new
tags:
  []
attachments:
  []
---
# sub-wildcard (cloud/aws/oidc)

- ID: sub-wildcard-cloud-aws-oidc
- Category: web
- Platform: manual
- Platform ID: (not provided)
- URL: N/A (static files)
- Attachments:
  - none

## Description

The ci-deployer IAM role trusts GitHub Actions via OIDC. You have its trust policy, its attached permissions, several captured OIDC tokens presented to it (oidc-token.json), and a release secret whose value is sealed in the handout (release-secret.json). Only one captured token actually satisfies the trust policy. Find it, show it can assume the role, then recover the secret. The flag is the secret. Flag format: NCTF{...}

## Constraints

- none
