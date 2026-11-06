---
name: reverse-skill-router
description: Deep reverse-engineering module library (45+ platform/tool modules) with an evidence-first routing table. Use when `ctf-reverse` or `reverse-engineering` is not enough and you need a platform-specific playbook — APK, .NET, Go/Rust, iOS/macOS, firmware, JS/Electron, thick client, kernel driver, protocol, binary diffing, patch-to-exploit, or a tool-specific workflow (IDA, Ghidra, Binary Ninja, radare2, Frida, Unicorn).
---

# Reverse Skill Router

This skill is a pointer, not a duplicate. The real library lives in
`knowledge/external/reverse-skill/skills/` (copied from `zhaoxuya520/reverse-skill`).

Use it only after the cheap triage has identified the target class. Do not read the
whole tree.

## Entry points

1. Routing table (platform → module, PRIMARY path + one-line justification):
   `knowledge/external/reverse-skill/skills/MASTER-ROUTING.md`
2. Full module index with summaries:
   `knowledge/external/reverse-skill/skills/INDEX.md`
3. Generic pipeline inside that library (triage → static → dynamic → synthesis):
   `knowledge/external/reverse-skill/skills/reverse-engineering/SKILL.md`
4. Case/evidence contract (Evidence → Finding → Path, scope gate):
   `knowledge/external/reverse-skill/skills/case-review/SKILL.md`

## Module map (CTF-relevant subset)

| Target | Module |
|---|---|
| Plain ELF / PE / Mach-O | `reverse-engineering/elf-analysis.md`, `languages-compiled.md` |
| APK / DEX / native `.so` | `apk-reverse/`, `mobile-reverse/`, `.claude/skills/reverse-engineering/references/android.md` |
| .NET / C# / ConfuserEx | `dotnet-reverse/` |
| Go / Rust stripped | `go-rust-reverse/` |
| iOS / macOS | `macos-reverse/`, `mobile-reverse/` |
| Firmware / IoT | `firmware-pentest/`, `hardware-security/` |
| JS / Electron / browser ext | `js-reverse/`, `browser-extension-reverse/` |
| Custom VM / bytecode / anti-debug | `reverse-engineering/patterns-ctf*.md`, `anti-analysis.md` |
| Protocol / file format | `protocol-reverse/` |
| Thick client / game client | `thick-client/` |
| Kernel driver | `reverse-engineering/kernel-driver-reverse.md` |
| Patch diff → N-day exploit | `patch-diff-exploit/`, `binary-diff/` |
| Frida / Unicorn / IDA / Ghidra / r2 | `ida-reverse/`, `ghidra-reverse/`, `radare2/`, `reverse-skills-p4nda0s/rev-frida`, `rev-unicorn-debug` |
| Malware-like loader | `malware-analysis/` |

## Hard rules

- This library is Chinese-language in places. Read the table/matrix sections; the
  command blocks and tool names are language-neutral.
- It assumes an authorized local sandbox — correct for CTF, but never run its
  `case-init`/`master-route` scripts against a remote target without checking what
  they do first. Prefer calling the module `SKILL.md` directly.
- Tool paths in `tool-index.md.template` are placeholders. Verify with `which` first;
  never copy a Windows path.
- Evidence discipline from `ctf-evidence` still applies: no flag claimed without a
  reproducible command and captured output.
