# HITCON CTF 2026 - mathclipse

## Service

- Remote: `nc mathclipse.chal.hitconctf.com 16767`
- Local source: `mathclipse/src/server.py` (26 lines), run under `socat TCP-LISTEN:16767,...,fork EXEC:"python3 -B -u /app/server.py,pipes,stderr"` (see `mathclipse/Dockerfile`).
- Important deployment detail: socat's `EXEC` target includes `,pipes,stderr` — **both stdout and stderr of the Python process are relayed to the socket.** Any uncaught Python exception (traceback + message) is sent straight to the client. The script itself never prints anything on success; the only two things a client ever sees are the initial prompt and, on error, an exception traceback.
- `flag.txt` is copied into the image and made world-readable-by-root/444, but `server.py` never opens or reads it. Whatever the intended solution is, it must get the flag out indirectly (e.g. by reaching the file through some descriptor/loader object, or by leaking process memory/state through a crafted exception), not through an explicit `open("flag.txt")` call in the script.

## Step 1 — What server.py does

### Imports
- `json` — to parse the single line of user input.
- `math` — used only as the **root object** of an attribute/item-traversal graph; none of its math functionality is actually used for computation.

### Input
- One line read via `input("> ")`, parsed as JSON into `pairs = json.loads(...)`.
- Expected shape, enforced by a single `assert`:
  - `pairs` is a list of exactly **2 "pair"s**.
  - Each pair is a list of exactly **2 "path"s** (call them `a` and `b`).
  - Each path is a list of **1 to 6 "steps"**.
  - The **total** number of steps across all 4 paths (2 pairs × 2 paths) must be **≤ 19**.
- So the attacker fully controls: how many hops each of the 4 paths takes (up to 6 each, 19 total), and the content of every hop.

### Core logic — `one()` and `slot()`

```python
def one(step):
    if type(step) is not list or len(step) != 1 or type(step[0]) not in (str, int):
        raise ValueError("bad step")
    return step[0]

def slot(path):
    obj = math
    for step in path[:-1]:
        obj = getattr(obj, step) if type(step) is str else obj[one(step)]
    key = one(path[-1])
    return obj, key, obj[key]
```

- `slot(path)` walks a path **starting from the `math` module object**.
- Each intermediate step in the path is either:
  - a plain **string** → resolved via `getattr(obj, step)` (attribute access), or
  - a **single-element list** `[x]` (x being a `str` or `int`) → resolved via `obj[x]` (item/subscript access, i.e. `__getitem__`), unwrapped by `one()`.
- The **last** step of the path must be the `[x]`-wrapped form (plain string is not accepted there, because `one(path[-1])` requires a one-element list) — it is kept as a `key` rather than immediately resolved, so the function can return the *container*, the *key*, and the *current value* (`obj, key, obj[key]`) instead of just the value.
- In short: `slot()` is a **generic "resolve an arbitrary attribute/item chain reachable from `math`, and hand back a writable (container, key) pair"** primitive, entirely driven by attacker-supplied JSON.

### The actual computation / "evaluation" step

```python
resolved = [(slot(a), slot(b)) for a, b in pairs]

for (x, i, u), (y, j, v) in resolved:
    x[i], y[j] = v, u
```

- For each of the 2 pairs, both paths `a` and `b` are resolved via `slot()`, giving `(x, i, u)` and `(y, j, v)` — i.e. two (container, key, current-value) triples.
- Then `x[i], y[j] = v, u` performs a **swap**: it writes `y`'s old value into `x[i]`, and `x`'s old value into `y[j]`, via `__setitem__` on whatever `x`/`y` turned out to be.
- Nothing is printed afterward. The entire "output" of a successful run is... nothing. The program just exits after swapping two values somewhere in the object graph reachable from `math`.

### Output
- Only the literal prompt string `"> "` is ever printed on success.
- On any `assert`/`ValueError`/`AttributeError`/`TypeError`/`KeyError`/`IndexError` raised while parsing/resolving/swapping, the interpreter's default traceback handler prints the exception (type + message + traceback) to **stderr**, which socat forwards to the client. This is the only other channel of information back to the player.

## Step 2 — Observing the live prompt

Connected read-only to `mathclipse.chal.hitconctf.com:16767` with a plain Python `socket` (no payload sent, connection closed immediately after one `recv`):

```
RECEIVED: b'> '
```

This matches `input("> ")` exactly — confirms the deployed binary matches the provided source, and that the service is up and reachable.

## Step 3 — Where user input drives an "evaluation", and the unintended-computation angle

**The vulnerable point is `slot()` (lines 9–14), feeding the swap assignment on line 26.**

Concretely:

1. `slot()` never restricts *which* attribute names or item keys can be requested. Every string step is a live `getattr(obj, step)` call, and every `[x]`-wrapped step is a live `obj[x]` call, chained up to 6 times per path. This turns the player's JSON into a **generic, attacker-steered object-graph walk starting at the `math` module** — effectively an arbitrary-read gadget over anything transitively reachable from `math` via attributes/items (not restricted to numbers — `math`'s module object itself exposes things like `__loader__`, `__spec__`, `__class__`, `__dict__`, `__builtins__`-adjacent machinery, etc., all accessible with plain string steps).
2. The trailing `x[i], y[j] = v, u` is a generic **arbitrary-write gadget**: whatever object `slot()` resolved as the *container* (`x` or `y`) gets one of its items overwritten via `__setitem__`, with the value taken from the *other* resolved slot. Because `obj` can be *any* Python object encountered along the walk (not just `math`'s own numeric constants), this isn't limited to corrupting `math` — if a path walks into, say, a module's real `__dict__` (a plain, mutable `dict`, unlike a class's read-only `mappingproxy`), the write primitive can overwrite entries in that namespace.
3. Because `getattr`/`__getitem__` are the only operations used, there's no explicit `eval`/`exec`/function call in the script — but attribute access on certain objects (e.g. `property` descriptors, or plain Python functions reached via `_frozen_importlib`'s loader classes, which — unlike `math` itself — are pure-Python and therefore expose a real `__globals__` dict) can be chained to pivot off `math` into interpreter-wide state: e.g. `math.__loader__` (the frozen-importlib loader class) → one of its Python-level methods (a function object) → `__globals__` (that function's module namespace, a real dict) → `["sys"]` (dict item access) reaches the live `sys` module object. From `sys`, `sys.modules["__main__"]` reaches the running script's own module, whose `__dict__` holds the script's live globals (`pairs`, `resolved`, `one`, `slot`, `math`, `json`, `__builtins__`, ...).
4. All of that is reachable within the allowed budget (≤6 hops per path, ≤19 steps total across the 4 paths), since each hop above is a single string or `[x]` step.
5. This gives the player a **swap-based write into effectively arbitrary mutable containers reachable from `math`**, including (plausibly) the running interpreter's own globals/builtins dicts — i.e. a classic "pyjail"-style object-graph pivot, but constrained to a *swap* rather than a free-form write, and with **no re-entrant execution point afterward** (the script ends right after the `for` loop — there is no subsequent `print`, `eval`, or second `input()` that would make a corrupted value "fire").

**What's still open (not yet solved, flagged for the exploit-dev step):**
- Since nothing executes after the swap and no code ever reads `flag.txt`, the win condition is presumably not "overwrite a value and have it get used" in the normal sense. The two most promising directions to investigate next:
  - **Crash-for-leak**: craft a path whose resolution (the `obj[key]` read inside `slot()`, which happens *before* any swap) raises an exception whose default traceback/`repr()` prints sensitive interpreter state (recall stderr is forwarded to the socket). E.g. resolving a path that lands on a secret-bearing object and triggers a `TypeError`/`KeyError` whose message embeds `repr(obj)` or `repr(value)`.
  - **Descriptor side-effect during resolution**: if a `getattr` step lands on a `property`, the `fget` runs implicitly as part of simply resolving the path (a real function call without using `()` in the JSON). If some reachable property's getter does file I/O or returns secret data (unlikely for `math`-reachable builtins, but worth checking via frozen-importlib / loader internals, or any `property`-based descriptor on reachable C-extension types), reading that attribute alone (even just to compute `u`/`v`, without ever using it in the final swap) could be enough to leak something through a crafted exception message.
  - Needs an interactive Python 3.14 REPL to literally walk `math.__loader__`, `__spec__`, class `__mro__`s, etc., and verify which hops are real objects of the hypothesized types in this exact Python build, since dunder-attribute availability on `math` (C extension vs. possibly statically linked, `__file__` presence, `__loader__` class identity) is Python-build-dependent and must be confirmed before trusting the hop-chain above.

## Step 4 — Exploit development and live testing (2026-10-23, follow-up session)

### Local confirmation of the escalation chain

Built a byte-for-byte local copy of `slot()`/`one()`/the assert, and tested the hypothesized pivot chain (`math` → `__loader__` → a Python-level method → `__globals__` → `["sys"]` → `"modules"` → `["os"]`) under the exact interpreter the target uses (`python:3.14-slim` base → local `python3.14.6`, close enough; both are CPython 3.14 with the same `_frozen_importlib`/`_frozen_importlib_external` internals).

Key correction versus the Step-3 hypothesis: `math` itself is **not subscriptable** (`obj["pi"]` raises `TypeError: 'module' object is not subscriptable`), so even reaching `math.pi` as a `(container,key,value)` triple needs 2 hops (`"__dict__"`, then `["pi"]`), not 1 — `slot()`'s final step is *always* an **item** access, never a plain `getattr`, because `one(path[-1])` requires a one-element list. Every "leaf" value must be fetched by first landing on something genuinely subscriptable (a real `dict`, not a module/class whose namespace is a read-only `mappingproxy`).

Verified locally and **on the live remote service** (`mathclipse.chal.hitconctf.com:16767`) that this exact 12-step, 2-pair payload resolves and swaps cleanly with **no exception** (confirms the chain is real, reachable, and the remote binary matches the local source):

```json
[[["__dict__", ["pi"]], ["__dict__", ["tau"]]],
 [["__loader__", "create_module", "__globals__", ["sys"], "modules", ["os"]], ["__dict__", ["e"]]]]
```
- Pair 1 swaps `math.pi` ↔ `math.tau` (sanity check, via `math.__dict__`).
- Pair 2 swaps `sys.modules["os"]` ↔ `math.e` — i.e. it reaches the **live `os` module object** through `math.__loader__.create_module.__globals__["sys"].modules["os"]` (6 hops, the max allowed in one path) and successfully swaps it with `math.e`. No exception on either run (local or remote) → object graph pivot confirmed working end-to-end against the real target.

To fingerprint the remote build and confirm it is literally running the same `server.py` we were given, sent a deliberately-wrong module name (`sys.modules["definitely_not_a_module_xyz"]`) and got back, verbatim:
```
Traceback (most recent call last):
  File "/app/server.py", line 23, in <module>
    resolved = [(slot(a), slot(b)) for a, b in pairs]
                 ~~~~^^^
  File "/app/server.py", line 14, in slot
    return obj, key, obj[key]
                     ~~~^^^^^
KeyError: 'definitely_not_a_module_xyz'
```
This confirms: (1) stderr really is forwarded to the socket as predicted, (2) line numbers match our local copy exactly — the deployed `server.py` is identical to the one we analyzed, (3) `KeyError`'s default message only echoes back the *key we supplied*, never surrounding dict contents — so this exception type cannot be used to enumerate or leak unknown data, only to confirm/deny presence of a guessed name (existence oracle).

### Why the escalation chain does **not** reach a file-read or code-execution primitive

I systematically tried to extend the confirmed pivot (`math` → `sys` → `sys.modules[...]`) into something that could actually read `/app/flag.txt` or an environment variable, and hit a hard structural wall:

1. **Every path is capped at 6 hops, independently of the 19-step total budget.** The 19-step cap is never the binding constraint (our deepest payload used 8 of them); the per-path cap of 6 is.
2. **Reaching any "fresh" module object (`sys`, `os`, `_imp`, `_bootstrap_external`, …) from `math` costs a fixed minimum of 4 hops** (`"__loader__"` → a Python-level function/method → `"__globals__"` → `[modname]`), because `math` itself is a C extension with no Python-level function anywhere in its own namespace that exposes a `__globals__`; the *only* route to a real, mutable namespace dict is via `_frozen_importlib.BuiltinImporter`'s pure-Python methods (`create_module`, `exec_module`).
3. That leaves only **2 more hops** per path: one more traversal step (e.g. `"modules"`, or `"FileLoader"`), then the mandatory final **item** access. So the deepest thing reachable in one path is "one attribute of a module reached via the pivot, then one key out of that". Concretely reachable, confirmed: `sys.modules[X]` for any `X` already in `sys.modules` (os, posix, io, builtins, math, json, re, __main__, …, as plain object references — not their contents), `sys.__dict__[X]` (any direct `sys` attribute: `argv`, `path`, `flags`, `version`, …), `_frozen_importlib`'s own globals dict entries (`_imp`, `_bootstrap_external`, `_thread`, `_warnings`, `_weakref`, `__builtins__`, assorted internal functions), and `_bootstrap_external.__dict__[X]` (its classes: `FileLoader`, `SourceFileLoader`, `PathFinder`, …, and a module-local `_os` reference — still just the `os` module object itself, not `os.environ`).
4. **`os.environ` and `sys.modules["__main__"].__dict__` (the running script's own globals) are both one hop too deep** — reaching the `os`/`__main__` module object already costs the full 6-hop budget, and getting one of *their* attributes needs 2 more hops (attribute name + final key) = 8 total. Not reachable in a single path, and there is no shortcut: nothing in `_frozen_importlib`'s or `_frozen_importlib_external`'s own namespace is a *shorter* route to `os`/`environ`.
5. **No function call is ever possible** through this primitive — `getattr`/`__getitem__` are the only operations used, and I could not find any implicit-call gadget hiding behind them:
   - **No module-level `__getattr__` hooks** (PEP 562) on any reachable module. Checked `os`, `sys`, `posix`, `_frozen_importlib`, `_frozen_importlib_external`, `io`, `_io`, `builtins`, `_imp`, `_thread`, `_warnings`, `_weakref`, `time`, `types`, `marshal`, `zipimport`, `stat`, `posixpath`, `genericpath`, `errno`, `codecs` — none define one.
   - **No exploitable `__class_getitem__`.** The final step of a path is a plain `obj[key]`; if `obj` happens to be a *class* (not instance), that syntax falls back to `obj.__class_getitem__(key)` — a genuine implicit call. Checked every class reachable within budget (`BuiltinImporter`, `FrozenImporter`, `ModuleSpec`, `_BlockingOnManager`, `_DeadlockError`, `_DummyModuleLock`, `_ImportLockContext`, `_List`, `_ModuleLock`, `_ModuleLockManager`, `_WeakValueDictionary`, and from `_bootstrap_external`: `AppleFrameworkLoader`, `ExtensionFileLoader`, `FileFinder`, `FileLoader`, `NamespaceLoader`, `PathFinder`, `SourceFileLoader`, `SourceLoader`, `SourcelessFileLoader`, `WindowsRegistryFinder`, `_LoaderBasics`, `_NamespaceLoader`, `_NamespacePath`, `_code_type`). Only `_List` (`= list`) has one, inherited from `list`, and it only builds a harmless `types.GenericAlias` — no side effect.
   - Standard exception messages for every container type reachable here (`dict`, `list`, `module`-not-subscriptable, `mappingproxy`-not-writable) never embed `repr()` of the *value* being written — only type names or the literal key we supplied — so there is no "crash-for-leak" channel either, because there is nothing secret already resolved in memory to leak in the first place (flag.txt is never opened, and the one secret-shaped thing we could imagine reaching, `os.environ`, is unreachable per point 4).
6. Since the swap primitive never performs a call, and the script has **no code at all after the `for` loop** (no `print`, no second `input()`, no re-entrant use of a corrupted value), a corrupted builtin/module entry can never be "fired" — the process simply exits right after the two writes.

### Conclusion of this round

The arbitrary attribute/item traversal-and-swap vulnerability in `slot()`/the final assignment is real and was demonstrated working end-to-end against the live service (pivoting from `math` to the interpreter's own `sys`/`os` module references). However, I was **not able to escalate it into either a file read of `/app/flag.txt` or any form of code execution**, because of a hard, measured 6-hops-per-path ceiling that keeps every reachable target to "one hop past a freshly-pivoted-to module", which structurally excludes `os.environ`, the running script's own globals, and any descriptor/hook that would perform real file I/O. I did not find any implicit-call gadget (`__getattr__` hook, informative `__class_getitem__`, or value-echoing exception) that would change this conclusion.

**No flag was obtained.** I am reporting this honestly rather than guessing one. The two payloads above were the only things sent to the remote service; nothing destructive or bulk-probing was attempted beyond those two single requests plus the banner-only read from Step 2.

### Possible next directions (not yet attempted, likely needs a different technique/skill)
- A genuine CPython **type-confusion / memory-corruption** angle (rather than pure object-graph traversal) — e.g. finding a container where `__setitem__` skips a type check that the C layer assumes holds, corrupting an internal structure badly enough to affect *already-open* file descriptors or buffers (none currently exist for `flag.txt`, so this would need to first get such a descriptor created, which itself needs a call — circular, but worth a dedicated low-level pass if this is pursued further).
- Re-verify assumptions against the **actual production image** rather than `python:3.14-slim` + local packages, in case the real build has an extra import, an env var, or a different `_frozen_importlib` internal layout that shortens the path to `os.environ` or adds a usable gadget. (The KeyError fingerprint test above at least confirms the deployed `server.py` source is identical to ours; it does not confirm the Python *build* is bit-for-bit identical to my local 3.14.6.)
- Reconsider whether the "two independent swaps, no code after" structure might support a **blind, multi-connection oracle attack** (existence/absence via `KeyError` vs. clean exit) to map out `sys.modules` keys or similar — demonstrated feasible as a primitive (see the fingerprint test) but not pursued further since it cannot, by itself, read file content or env vars (same 6-hop wall applies to every connection).
