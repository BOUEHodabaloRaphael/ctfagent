# Architecture notes

```
rekit/
  cli.py                 argparse front-end (sub-commands, `rekit FILE` shorthand)
  engine.py              orchestration: read -> parse -> strings -> profiles -> summary
  core/
    binary.py            ParsedBinary / Section / Segment / Symbol + address translation
    elf.py pe.py macho.py  tolerant pure-Python parsers (never raise on hostile input)
    formats.py           magic dispatch -> (parsed | None, error)
    fileinfo.py util.py  hashes, magic, strings, entropy (exact <= 4 MiB, sampled above), hexdump, defang
    iocs.py crypto.py xorscan.py stackstrings.py decoders.py carve.py   evidence extractors
    packers.py capabilities.py   interpretation tables (data-driven)
    xrefs.py disasm.py patch.py diff.py integrations.py   action tools used by the CLI and the CTF profile
    reporting.py         JSON / Markdown / HTML / console renderers
  profiles/              ctf.py, malware.py: turn evidence into Findings
```

## Principles

- **Parsers are total functions**: a corrupt or hostile file yields partial results plus `warnings`, never an
  exception (enforced by the mutation fuzzers in `tests/test_parsers.py` and `tests/test_engine_cli.py`).
- **Evidence over verdicts**: findings carry confidence, limitations, ATT&CK *hints* and next steps. Severity
  rises only on strong, independent combinations. No benign/malicious verdict is produced.
- **One analyzer failing must not abort a run**: profile steps are isolated; failures land in `report.errors`.
- **Shared work is computed once**: xor / carve / crypto results are memoised across profiles (`profiles.common.cached`).
- **Reports are safe to open**: all report text is escaped (HTML), neutralised (Markdown) and indicators are
  defanged. JSON keeps raw values for machines.

## Evidence contract (schema "2")

`Finding`: `id`, `title`, `severity` (info/low/medium/high), `confidence`, `description`, `evidence[]`,
`limitations[]`, `category`, `next_steps[]` (CLI commands), `attack[]` (MITRE ATT&CK technique hints).
`AnalysisReport` adds `schema_version`, `summary` (counts, top findings, suggested next steps) and
`modules.timings_ms`. Prefer `unknown` / `not detected` over guessing.

## Adding an analyzer

1. Write a pure function in `core/` returning plain dicts (offsets, names, evidence).
2. Call it from `profiles/ctf.py` and/or `profiles/malware.py` inside a `try/except`, wrap expensive scans in
   `cached(options, key, fn)`, and emit `Finding`s.
3. Add a fixture-based test in `tests/` (hand-built bytes, or gcc output guarded by `need("gcc")`).

## Dynamic-analysis boundary

No target is executed. A future runner must be a separately designed component with explicit VM/container
isolation, snapshots, resource limits, controlled network policy and observable-event collection. Running a
sample in a plain Docker container must not be treated as sufficient isolation.
