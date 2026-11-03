---
doc_kind: pattern
title: "SSRF filter bypass via nip.io/sslip.io wildcard DNS"
category: misc
slug: ssrf-bypass-nipio-wildcard-dns
created: 2026-11-03
status: active
tags:
  - ssrf
  - nip.io
  - sslip.io
  - dns-bypass
  - hostname-allowlist
  - boot2root
chain_summary: "A hostname-allowlist SSRF filter that validates the string pattern (e.g. *.internal.local) but resolves DNS normally is bypassed by a nip.io/sslip.io subdomain such as target.internal.local.127.0.0.1.nip.io, which matches the pattern while resolving to an attacker-chosen IP (commonly loopback) to reach internal-only services."
---
# SSRF filter bypass via nip.io/sslip.io wildcard DNS

## Chain Summary

- One-line chain: A hostname-allowlist SSRF filter that validates the string pattern (e.g. *.internal.local) but resolves DNS normally is bypassed by a nip.io/sslip.io subdomain such as target.internal.local.127.0.0.1.nip.io, which matches the pattern while resolving to an attacker-chosen IP (commonly loopback) to reach internal-only services.
- Typical target shape: an endpoint accepting a user-supplied URL/hostname for server-side fetching ("probe", "preview", "fetch", webhook-test), validated by a regex/allowlist against an internal domain pattern (e.g. `*.internal.local`, `*.corp.example.com`) rather than a resolved-IP allowlist.

## Preconditions

- The filter validates the **hostname string** (regex/suffix match) without separately validating the **resolved IP** after DNS lookup — i.e. it trusts "looks like an internal hostname" as equivalent to "actually routes only to internal hosts."
- Outbound DNS resolution from the server is not restricted/pinned (no DNS-level egress filtering), so it will happily resolve an attacker-chosen public wildcard-DNS domain.

## Cheap Probes

- Identify the exact allowlist pattern first (error messages on a plain external URL often reveal the expected suffix, e.g. "only *.internal.local allowed").
- Test `<anything>.<allowed-suffix>.<attacker-ip-with-dots-replaced-by-dashes-or-literal>.nip.io` (or `.sslip.io`, functionally identical free wildcard-DNS services) and confirm via a timing/response difference that the server actually attempted to connect to the resolved IP rather than rejecting the hostname outright.
- `dig +short <constructed-hostname>` locally to confirm it resolves to the intended IP before sending it to the target — avoids wasting probe attempts on a malformed nip.io string.

## Telltale Evidence

- The filter's rejection message is specific to hostname *syntax* (e.g. "must end in .internal.local") rather than a resolved-IP check — a strong signal the validation happens pre-DNS.
- A successful probe against the crafted nip.io hostname returns different timing/content/error than an obviously-external hostname, confirming the server actually made the internal connection.

## Escalation Order

1. Determine the exact allowed hostname suffix/pattern from error messages or source code (if leaked).
2. Craft `<suffix-satisfying-prefix>.<target-internal-ip-with-dots>.nip.io` (nip.io resolves `X-Y-Z-W.nip.io`, `X.Y.Z.W.nip.io`, and `anything.X.Y.Z.W.nip.io` all to `X.Y.Z.W`) so the string both ends in the allowed suffix AND resolves to the attacker's target IP (commonly `127.0.0.1` for same-host internal services).
3. Confirm basic SSRF works against a low-risk internal target first (e.g. the server's own HTTP port) before pivoting to port-scanning or hitting higher-value internal-only services.
4. Use the same SSRF primitive to port-scan the internal network by looping candidate ports through the probe endpoint (watch for distinct response/timing on an open vs. closed/filtered port).
5. Once an internal service is found, treat the SSRF as a fully-controllable HTTP client against it — expect the next stage to be reading internal source/config (if the service serves files) or exploiting that internal service's own vulnerabilities (often the SSRF is just step 1 of a longer chain).

## Common Mistakes

- Only trying `localhost`/`127.0.0.1`/decimal-IP-obfuscation tricks against the filter and giving up when those are explicitly blocked — modern filters often block the obvious bypasses but miss wildcard-DNS services since the hostname *string itself* still satisfies the allowlist regex.
- Forgetting that nip.io/sslip.io resolution needs the target server to actually perform live DNS lookups — if the target's egress is DNS-filtered or uses a static hosts file / internal-only resolver, this bypass won't work and a different SSRF technique (open redirect, DNS rebinding/TOCTOU) should be tried instead.

## Payload Shapes

```text
http://victim.internal.local.127.0.0.1.nip.io/           # resolves to 127.0.0.1, passes a *.internal.local suffix check
http://anything.internal.local.10-0-0-5.nip.io:8081/path # resolves to 10.0.0.5 (dash-separated form also supported)
http://victim.internal.local.127.0.0.1.sslip.io/         # sslip.io equivalent
```

## Related Writeups

- [AFRICC 2027 Qualifiers — full writeup](../../writeups/misc/africc2027-quals-full-writeup.md) — "Kaldvik" (Boot2Root, 75pts), stage 1 of a 5-stage chain.
- [ssrf-to-lfi-to-localhost-rce.md](../../patterns/web/ssrf-to-lfi-to-localhost-rce.md) — related SSRF pattern already in this repo; this one specifically covers the DNS-bypass angle against hostname allowlists.

## Skill Impact

- Related skill: `web-triage` (`references/ssrf.md` — add the nip.io/sslip.io wildcard-DNS bypass as a standard technique to try against hostname-pattern SSRF filters, alongside existing bypass techniques).
- Rule to add or update: `src/tools/web/fetch_target.py` (SSRF probe wrapper) could gain a `--nipio` helper to auto-construct `<suffix>.<ip>.nip.io` candidates from a target suffix + IP list.
