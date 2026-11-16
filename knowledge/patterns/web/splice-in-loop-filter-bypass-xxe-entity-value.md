---
doc_kind: pattern
title: "Array splice()-in-loop skips validation -> XXE via entity-value injection"
category: web
slug: splice-in-loop-filter-bypass-xxe-entity-value
created: 2026-11-16
status: active
tags:
  - xxe
  - filter-bypass
  - logic-bug
  - nodejs
  - libxmljs
  - splice
chain_summary: "A validation loop that splice(i,1)+continue's on some items skips the item shifted into index i; smuggle an unvalidated item carrying an XXE payload injected INTO the server-built <!ENTITY value, even when SYSTEM/<!/ENTITY are blacklisted on validated input"
---
# Array `splice()`-in-loop skips validation → XXE via entity-value injection

## Chain Summary

- One-line chain: a server validates a list of objects in a `for (i…) { …checks…; if (drop) { arr.splice(i,1); continue; } }`
  loop, then uses every surviving item. Because `splice(i,1)` shifts the array left while `i` still
  increments, **the item that moves into index `i` is never validated**. Put an attacker item right
  after a "to-be-dropped" item → it bypasses the input filter entirely → carry an XXE payload that is
  interpolated raw into a server-built `<!ENTITY …>` and parsed with entity expansion on.
- Typical target shape: Node/Express endpoint taking a JSON array, a per-item blacklist
  (`sanitizeInput` rejecting `<!`, `SYSTEM`, `ENTITY`, `DOCTYPE`…), a "skip these items" rule
  implemented with `splice`+`continue`, and XML built by string-interpolating item fields into a DTD
  then `libxmljs.parseXml(xml, { replaceEntities: true })` (NOENT = external entities load).

## Preconditions

- A collection is validated and mutated in the **same** index-based loop with `splice(i,1); continue;`
  (or any removal that shifts indices) — classic off-by-one that skips the next element.
- Surviving items reach a sink. Here the sink is XML: user fields are placed **inside** an
  `<!ENTITY name "…">` literal in a DTD the server constructs, and parsed with `replaceEntities:true`
  (libxmljs 0.x/1.x) or any libxml2 NOENT mode.
- A readable target file (`/flag.txt`, `/etc/passwd`) and the parsed text is echoed back (or usable
  blind/OOB).

## Exploit Steps

1. **Spot the loop bug.** Look for `arr.splice(i, 1)` / `arr.splice(i,1); continue;` inside a
   `for (var i=0; i<arr.length; i++)` that ALSO does the validation. Every element directly after a
   spliced one is validation-skipped. (Also triggers when a map/filter mutates the backing array.)
2. **Find the splice trigger.** Some attacker-controllable condition decides the drop (here:
   `artist` contains `drake`/`drizzy`). You control it, so you choose which element gets dropped and
   thus which neighbour is skipped.
3. **Lay out the array** so a dropped item sits immediately before the malicious item:
   `[ {drop-trigger}, {PAYLOAD}, {filler}, {filler} ]`. Keep `length >= min` after the splice; make
   every *validated* item clean (they still hit the blacklist).
4. **Inject into the entity value.** The server writes `<!ENTITY artist "<YOURFIELD>">`. Break out of
   the literal and declare an external entity; let the server's own trailing `">` close your SYSTEM
   literal (watch the quote accounting — see Pitfalls):
   - `songName`: `pwn`
   - `artist` : `pwn"><!ENTITY xxe SYSTEM "file:///flag.txt`   ← NO closing quote; template adds `">`
   - `thoughts`: `&xxe;`   ← a referenced entity whose value expands the external one
   Server builds: `<!ENTITY artist "pwn"><!ENTITY xxe SYSTEM "file:///flag.txt"> … <!ENTITY thoughts "&xxe;">`
   Body `<thoughts>&thoughts;</thoughts>` → `&xxe;` → file contents, returned in the echoed field.
5. **Auth if needed, then read back.** If JWT secret is randomized (no forgery), just register a
   normal user for a valid token, POST the payload, then GET the listing endpoint that returns the
   stored/parsed value.

## Pitfalls

- **Quote accounting is the #1 failure.** The template appends `">` after your field. If your payload
  also ends with `"`, you get `…flag.txt"">` → `xmlParseEntityDecl: entity … not terminated`. End your
  SYSTEM literal payload WITHOUT the closing quote and let the template's `">` close it.
- **Which entity is echoed.** You usually can't edit the XML body, only entity values. Declare the
  external entity in one field (e.g. `artist`) and set a body-referenced field (e.g. `thoughts`) to
  `&yourentity;` so expansion lands in a value the response returns.
- **Blacklist only covers validated items.** `<!`, `SYSTEM`, `ENTITY`, `DOCTYPE` are fine in the
  smuggled item precisely because it skips `sanitizeInput`. Don't waste time on encoding bypasses if
  the logic bug hands you an unfiltered field.
- **`replaceEntities:true` is the enabler.** Without NOENT, external entities aren't loaded. Confirm
  the parse options; libxmljs `parseXml(xml,{replaceEntities:true})` and libxml2 `XML_PARSE_NOENT` both
  do it.
- **Generalizes beyond XXE.** The splice-skip primitive smuggles ANY unvalidated item to ANY sink
  (SQLi, command build, template). The XML part is just this challenge's sink.

## Related

- [[htb-stream-xxe-clickhouse]] — other XXE-to-file-read on HTB (different injection point).
- Writeup: `knowledge/writeups/web/htb-xoxo-exploit-splice-bypass-xxe.md`
