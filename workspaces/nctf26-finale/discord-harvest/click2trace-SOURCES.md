# Click2Trace CTF (guild 1517136169979215913) — harvest 2026-11-13

Has a dedicated #writeups channel with full markdown/txt writeups attached (author TH3R3B3L et al).
15 writeup files downloaded to downloads/click2trace/ (read-only; untrusted; do not execute):

WEB:
- web_Reading_Between_The_Glyphs.md — font-stego / GSUB `calt` shaping hides internal URL+key behind /preview (raw cmap is decoy).
- web_Order_Of_Operations.md — client-forgeable cookie = computable fn of leaked header values (operator precedence) -> forge access_token.
- web_Deprecated_Not_Deleted.md — GraphQL introspection OFF; recover hidden field via field-suggestion ("Did you mean"), legacySecret derived from systemStatus.region.
- web_Ghosts_of_2003.txt — "Ghosts of 2003" (medium).
- web_Right_Here_Right_Now.txt
- web_Schrodingers_File.txt
- web_Liars_Manifest.txt — robots red-herring.
- web_Declassified.txt
- web_Secterm_AI_agent.txt — "Web Exploitation / AI Agent Security" (HARD). RELEVANT to nctf26-agent-tool-abuse.

REV:
- rev_17-linear-descent.md, rev_18-mirror-vm.md (VM), rev_19-yarv-whisperer.md (Ruby YARV bytecode),
  rev_20-the-mill.md, rev_21-kernel-oracle.md (kernel), rev_22-threaded.md.

OSINT (external): medium.com/@mehdibenfaidia/click2trace-ctf-osint-writeups-eebc84290d78

Flag format: C2T{...}. Deliverable: CLICK2TRACE-TECHNIQUES-FOR-NCTF.md by category.
