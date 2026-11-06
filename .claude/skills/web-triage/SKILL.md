---
name: web-triage
description: Router for web vulnerability triage. Routes to the appropriate reference workflow based on evidence patterns. Use after ctf-solver-profile when the target is a web challenge requiring vulnerability identification and exploitation.
---

# Web Triage Router

Use this skill after `ctf-solver-profile` when the target is a web challenge.

Treat it as a router: inspect evidence, then jump to the matching reference.

## Routing Table

| Evidence Pattern | Reference |
|------------------|-----------|
| `eyJ...` tokens, `Authorization: Bearer`, JWT claims | [jwt.md](references/jwt.md) |
| `rO0AB`, `gASV`, `O:8:"Class"`, pickle/serialize language | [deserialization.md](references/deserialization.md) |
| SSRF hints, `file://`, internal fetch, localhost pivot | [ssrf.md](references/ssrf.md) |
| Template syntax `{{}}`, `${}`, `<%= %>` evaluating server-side | [ssti.md](references/ssti.md) |
| Parameter affecting rows/errors, `AND 1=1` differential | [sqli.md](references/sqli.md) |
| Reflected input in HTML/attributes, `onerror=alert(1)` | [xss.md](references/xss.md) |
| Opaque Base64 blob (QR, ticket, voucher) that is not a JWT | [signed-blob.md](references/signed-blob.md) |
| XML endpoint, SVG/DOCX/XLSX upload, SAML/RSS/XML-RPC | [xxe.md](references/xxe.md) |

## Quick Decision Flow

1. **See serialized data?** → Check deserialization signatures first
2. **See JWT tokens?** → jwt.md
3. **See URL fetch parameter?** → ssrf.md
4. **See template syntax evaluated?** → ssti.md
5. **See SQL-like parameter influence?** → sqli.md
6. **See reflected HTML with script potential?** → xss.md

## External Technique Reference (CEH/AFRICC)

Before improvising a payload, check the condensed CEHv13 technique notes for extra probe
ideas/exact payload strings:
- SQLi cheat sheet (error/UNION/blind, WAF bypass, NoSQL): `knowledge/ceh/m15-sql-injection.md`
- Web app attacks (LFI, XXE, SSRF/XSPA, IDOR via param pollution, CORS, OAuth/CSRF chain,
  rate-limit bypass via `X-Forwarded-For`): `knowledge/ceh/m14-web-apps.md`
- Quick links/tools (dCode, CyberChef, RsaCtfTool...): `knowledge/ceh/africc-links.md`
- Condensed per-category cheat sheet for the active event: `workspaces/nctf26/prep-ceh-africc-cheatsheet.md`

## External Technique Reference (NeuroSploit)

Compact payload variants not fully covered above — check when the standard reference
doesn't land on the first try:
- JWT `alg` confusion RS256→HS256, `jku`/`x5u`, `kid` injection:
  `knowledge/external/neurosploit/web/jwt_alg_confusion.md`
- SSTI polyglot across engines (Jinja2/Twig/Freemarker/Velocity/Thymeleaf/Pug):
  `knowledge/external/neurosploit/web/ssti.md`
- SSRF with cloud metadata focus (AWS/GCP/Azure):
  `knowledge/external/neurosploit/web/ssrf.md`
- Deserialization payload variants (Java/PHP/Python pickle/YAML):
  `knowledge/external/neurosploit/web/insecure_deserialization.md`
- Recon ordering and proof/false-positive discipline (useful as a second opinion on
  our own workflow): `knowledge/external/neurosploit/meta/recon.md`,
  `knowledge/external/neurosploit/meta/REGISTRY.md` (CWE-indexed catalog)

## Tool Reference

All web tools are now at `src/tools/web/`:

```
src/tools/web/
├── jwt_tool.py           # JWT inspect, forge, bruteforce
├── boolean_probe.py      # SQLi true/false differential
├── sqlite_boolean_extract.py  # Blind SQLite extraction
├── fetch_target.py       # SSRF/file:// request wrapper
├── ssti_probe.py         # Template injection probes
├── xss_probe.py          # XSS reflection probes
├── detect_ser.py         # Serialization format detection
└── gen_payload.py        # Payload generation (Java/Python/PHP)
```

Usage pattern:

```bash
python3 src/tools/web/<tool>.py <command> --target URL --param NAME
```

## Workflow

1. Fingerprint the target (stack, endpoints, auth mechanism)
2. Match evidence to a reference workflow
3. Follow the reference's probe order
4. Verify exploitation before expanding scope
5. Got any shell or code execution? Run [post-shell-pivot.md](references/post-shell-pivot.md) before declaring the chain finished — a leaked secret or a container shell both hide cheap next steps.
6. Save the case with `ctf-knowledge-capture`

## Exit Conditions

Switch to another skill category when:

- Evidence points to crypto, pwn, or reverse engineering
- The target is not a web application
- The vulnerability class is not covered here
