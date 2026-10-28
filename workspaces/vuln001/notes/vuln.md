# Vulnerability: unchecked APP1 length field in `exif_data_load_data`

File: `libexif/exif-data.c`, function `exif_data_load_data()`.

## Code path (as shipped in the challenge tarball)

When the raw input does not start directly with the 6-byte `Exif\0\0`
signature, the function scans forward through JPEG markers (skipping `0xFF`
padding, `SOI`, and non-APP1 `APPn` segments) looking for an `APP1` marker
(`0xE1`) that is immediately followed by `Exif\0\0`. Once that marker is
found, it breaks out of the scanning loop and does:

```c
if (ds < 3) { LOG_TOO_SMALL; return; }
d++;                       /* skip the 0xE1 marker byte */
ds--;
len = (((unsigned int)d[0]) << 8) | d[1];   /* 2-byte big-endian APP1 length */
d += 2;
ds = len - 2;               /* <-- no validation of len at all */
```

`len` is attacker-controlled (it is the 2-byte length field of the APP1
segment in the submitted file) and is used completely unvalidated:

- No check that `len >= 2` (upstream commit `54461dd` adds this). If
  `len` is 0 or 1, `len - 2` underflows in unsigned arithmetic to a huge
  value (`0xFFFFFFFE` / `0xFFFFFFFF`), so `ds` becomes ~4 billion.
- No check that `len <= ds_available` — i.e. that the declared length does
  not exceed the number of bytes actually still present in the buffer the
  caller handed to `exif_data_load_data` (upstream commit `4bd5cd6` adds
  this, citing oss-fuzz).

After this, `ds` (now huge/bogus) is treated as the trusted size of the
remaining EXIF TIFF body and is handed to the IFD/tag parsing routines
(`exif_data_load_data_content` → `exif_data_load_data_entry` etc.), which
will walk tag offsets/counts against this inflated `ds` and read well past
the end of the actual heap allocation that held the uploaded file — a
classic heap buffer over-read. Depending on heap layout this can leak
adjacent heap memory (if the service echoes parsed tag values back to the
client) or crash the process (DoS) on an unmapped page.

## Trigger shape

A minimal JPEG-ish buffer:

```
FF D8                      ; SOI
FF E1 00 00  'E' 'x' 'i' 'f' 00 00   ; APP1 marker, length=0x0000, Exif header
<arbitrary trailing padding depending on service input format>
```

With `len = 0x0000`: `ds = len - 2 = 0xFFFFFFFE`. Any subsequent IFD entry
that encodes a huge tag "count" or "offset" field will now read far outside
the real buffer bounds, because the length sanity check that upstream later
added is absent here.

## Exploitation strategy for this service

Goal is info leak (read the flag out of adjacent memory) rather than code
execution, since this is a single missing bounds check, not a write
primitive. Plan:
1. Confirm protocol via light probing (see HANDOFF.md).
2. Send a crafted JPEG/EXIF blob that sets the APP1 length field to 0 or 1,
   forcing `ds` to underflow.
3. Follow with a minimal IFD (TIFF header `II`/`MM` + offset to IFD0) whose
   first entry claims a tag count/offset that reaches past the legitimate
   buffer, inside the region the service allocated right before/after the
   upload buffer — the exact exploitability (what's adjacent in memory,
   whether the service echoes field values back) can only be determined by
   probing the live service's response format.
4. If the service echoes decoded EXIF tag values (e.g. a "comment"/"user
   comment"/"maker note" string) back to the client, use an ASCII-type tag
   with a huge declared component count to read adjacent heap bytes and
   leak them through that echoed value — iterating/adjusting offsets to
   search for flag-shaped data if it sits in nearby heap/service state.
