---
doc_kind: pattern
title: "SSTI file-read primitive to /proc/self/environ secret leak"
category: web
slug: ssti-file-read-proc-environ-secret-leak
created: 2026-11-01
status: active
tags:
  - ssti
  - lfi
  - file-read
  - env-leak
  - proc-self-environ
  - secret-harvesting
chain_summary: "A template-injection file-read primitive (any engine: Go text/template .File, Jinja2 self.__init__.__globals__, etc.) reachable via a user-controlled field rendered server-side (notes, ticket, invoice, report) lets you read /proc/self/environ instead of just /etc/passwd, harvesting API keys and HMAC/signing secrets straight out of the process env without needing direct RCE."
---
# SSTI file-read primitive to /proc/self/environ secret leak

## Chain Summary

- One-line chain: A template-injection file-read primitive (any engine: Go text/template .File, Jinja2 self.__init__.__globals__, etc.) reachable via a user-controlled field rendered server-side (notes, ticket, invoice, report) lets you read /proc/self/environ instead of just /etc/passwd, harvesting API keys and HMAC/signing secrets straight out of the process env without needing direct RCE.
- Typical target shape: any "generate a document from my data" feature (ticket/invoice PDF, certificate, report, notification email body) that embeds a user-controlled string into a server-side template renderer, or any endpoint that otherwise exposes a template-injection file-read gadget (SSTI, path-traversal "download template" features, log/report viewers that accept a template string).

## Preconditions

- A user-controlled field reaches a template render call where the engine evaluates expressions in the input, not just substitutes it as plain text (classic SSTI), OR a file-read-shaped primitive exists some other way (arbitrary file read, debug endpoint, LFI).
- The process whose files you're reading is the actual application server process (not a sandboxed renderer subprocess with its own, less interesting environment) — verify this by reading `/proc/self/cmdline` or similar first if unsure.

## Cheap Probes

- Confirm template execution first with a cheap, unambiguous probe for the detected/guessed engine: `{{7*7}}` (Jinja2), `${7*7}` (various JS/Java template engines), `{{.File "/dev/null"}}`-shaped probes for Go `text/template` custom file funcs, etc. Look for the evaluated result (`49`) rather than the literal string.
- Once execution/file-read is confirmed, read `/etc/passwd` first as a zero-risk sanity check that the read primitive actually returns file content end-to-end through whatever extraction pipeline you're using (PDF -> pdftotext, HTML response, JSON error message, etc.).
- Immediately follow with `/proc/self/environ` — do not stop at `/etc/passwd`. This is the single highest-value file to read once any arbitrary-file-read primitive exists against an app server process.

## Telltale Evidence

- The extracted output contains `KEY=value\x00KEY=value\x00...`-shaped NUL-separated env data (typical `/proc/self/environ` format) rather than a file-not-found error or empty string.
- Regex hits for names like `*_TOKEN`, `*_KEY`, `*_SECRET`, `DATABASE_URL`, `*_API_KEY` inside that dump — these are almost always live, usable secrets (HMAC keys, API keys, DB credentials), not placeholders.

## Escalation Order

1. Identify the template engine / file-read mechanism from error messages, framework fingerprinting, or by trying common syntaxes for Jinja2/Go template/Freemarker/Velocity/etc.
2. Confirm with a cheap arithmetic or identity probe.
3. Read `/etc/passwd` to validate the full extraction pipeline works (e.g. the generated PDF really does carry injected file content through to `pdftotext`).
4. Read `/proc/self/environ` and parse it as NUL-separated `KEY=value` pairs; regex for anything token/key/secret-shaped.
5. Treat every extracted secret as a candidate key for any signed/encrypted artifact the app produces (see `hmac-signed-blob-forging`) and as a candidate credential for any internal service the app might talk to (see `internal-automation-api-key-rce-as-root`).

## Common Mistakes

- Stopping at `/etc/passwd` as "proof of LFI" and moving on to brute-forcing other files instead of immediately trying `/proc/self/environ`, which is almost always more valuable and doesn't require guessing a filename.
- Giving up when the primary SSTI gadget chain (e.g. `__class__.__mro__.__subclasses__()` for Jinja2) is filtered, instead of trying a shorter alternative gadget exposed by the same context (e.g. `self.__init__.__globals__.__builtins__`) or checking whether the engine already exposes a dedicated file-read builtin (like Go's custom `.File` func in this case) that needs no gadget chain at all.
- Assuming the file-read happens in the same process as the main web server; if the renderer is a separate sandboxed worker, `/proc/self/environ` may be far less interesting than expected — verify which process you're actually reading from.

## Payload Shapes

```text
# Go text/template custom file-read func (seen in HTB Takeoff)
{{.File "/etc/passwd"}}
{{.File "/proc/self/environ"}}

# Jinja2 — see ssti-pdf-generation-jinja-self-globals.md for the fuller gadget chain
{{ self.__init__.__globals__.__builtins__.__import__('os').popen('cat /proc/self/environ').read() }}
```

## Related Writeups

- `knowledge/writeups/web/htb-takeoff-ssti-hmac-forge-n8n-bindmount.md`
- `knowledge/writeups/web/jinjacare-ssti-pdf-certificate.md`

## Skill Impact

- Related skill: `web-triage` (SSTI branch)
- Rule to add or update: whenever an SSTI/file-read primitive is confirmed, the default next move should be `/proc/self/environ` (not just the flag file or `/etc/passwd`) — primed for reuse during NCTF26 web challenges, since env-leaked secrets commonly chain into signature forging and internal-service RCE (see `hmac-signed-blob-forging`, `internal-automation-api-key-rce-as-root`).
