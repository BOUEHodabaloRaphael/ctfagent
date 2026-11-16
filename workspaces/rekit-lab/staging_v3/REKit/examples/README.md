# Examples

- `crackme.c` – the small password-check program used throughout the docs and tests.
- `stripped_crackme_report.html` – `rekit <stripped crackme> --profile ctf --format html`: shows the automatic
  link from "Correct/Wrong password" strings to the validation function in a stripped PIE binary.
- `synthetic_dropper_report.{html,md}` – report for a **synthetic, harmless** PE built by `tests/fixtures.py`
  (UPX-style section names, injection-API imports, Run-key string). It is not real malware; it exists to show the
  report layout.

Build and try it yourself:

```bash
gcc -O2 -pie examples/crackme.c -o crackme && strip crackme
rekit crackme --profile ctf
```
