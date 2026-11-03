# Category Switching Cues

Use this file when the initial classification is weak.

## Web -> Backdoor / RCE

Look here when:

- the page is blank or nearly blank
- a very small number of parameters exist
- old PHP versions are present
- source suffixes like `.phps` or debug leftovers appear

Cheap probes:

- short parameter names
- `phpinfo();`
- `sleep(3);`
- simple file reads

## Web -> SSRF / source-read

Look here when:

- one input resembles a fetcher, previewer, or URL reader
- responses embed fetched content
- internal or localhost wording appears

Cheap probes:

- external URL fetch
- `file://`
- app source read

## Web -> LFI

Look here when:

- parameters smell like `file`, `page`, `lang`, `template`, `include`
- stack traces or warnings imply include paths
- wrapper behavior differs

Cheap probes:

- `../../`
- double-encoding
- wrapper reads

## Binary -> Pwn

Look here when:

- remote socket service exists
- malformed input changes process behavior
- protections and memory layout matter

Cheap probes:

- `file`
- `checksec`
- `strings`
- crash reproduction

## Binary -> Rev

Look here when:

- there is no live network surface
- challenge behavior is local and deterministic
- logic extraction matters more than memory corruption

Cheap probes:

- strings
- functions
- control-flow landmarks

## Text / Data -> Crypto or Encoding

Look here when:

- content has constrained alphabets
- structure suggests base encodings, XOR, block boundaries, or classical ciphers
- there is no executable surface at all

Cheap probes:

- alphabet analysis
- byte frequency
- length and padding checks

## External Technique Reference (CEH/AFRICC)

Once a category is confirmed above, before improvising, pull extra probe ideas / exact
payload strings from the condensed CEHv13 + AFRICC technique notes in `knowledge/ceh/`:

| Category | File |
|---|---|
| Recon/scan | `knowledge/ceh/m03-scanning.md` |
| Enumeration | `knowledge/ceh/m04-enumeration.md` |
| Vuln analysis / triage order | `knowledge/ceh/m05-vuln-analysis.md` |
| Web (LFI/XXE/SSRF/IDOR/OAuth) | `knowledge/ceh/m14-web-apps.md` |
| SQLi | `knowledge/ceh/m15-sql-injection.md` |
| Crypto (hashcat recipes, RSA, padding oracle, cryptanalysis catalog) | `knowledge/ceh/m20-cryptography.md` |
| System hacking / privesc / post-exploit | `knowledge/ceh/m06-system-hacking.md` |
| Quick online tools (dCode, CyberChef, RsaCtfTool, quipqiup, CrackStation) | `knowledge/ceh/africc-links.md` |

Other modules (malware, sniffing, social engineering, DoS, session hijacking, IDS/firewall
evasion, web servers, wireless, mobile, IoT/OT, cloud) land in `knowledge/ceh/` progressively —
check the directory listing if the category isn't in the table yet.

For the active event, a condensed cross-category cheat sheet also lives at
`workspaces/nctf26/prep-ceh-africc-cheatsheet.md` — read it once the category is confirmed,
it links back to the full files above per section.
