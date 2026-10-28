# libexif source version identification

## Version string

`configure.ac` / `NEWS`: `0.6.23.1` (dev snapshot after the 0.6.23 release,
before the 0.6.24 release). All files in the tarball carry mtime
`Nov 1 2021`.

## Exact upstream commit match

Cloned upstream `https://github.com/libexif/libexif.git` and walked the
history between the `0.6.23` tag (`6801b62`) and the `0.6.24` tag (`5bc74ae`).

`diff -rq` of the tarball's `libexif/` directory against upstream commit
`a918830b8830e1e3657b4f36f48571a8d95a4ec8` ("fixed offset for EXIF Header in
App1 Header.", dated 2021-11-01 16:38:58 +0100) comes back **empty** — the
tarball is a byte-for-byte match of `libexif/` at that exact commit. This also
lines up exactly with the tarball's Nov 1 2021 file mtimes, so this is almost
certainly the real build the remote service was compiled from.

## What's missing relative to that commit

Immediately after `a918830`, upstream landed two more commits before the
0.6.24 release, both touching the same function (`exif_data_load_data`,
`libexif/exif-data.c`), both NOT present in the tarball:

- `54461dd` (2021-11-03): "check for len < 2 to avoid it becoming negative."
  — adds a check that the little 2-byte APP1 length field is at least 2
  before using it.
- `4bd5cd6` (2021-11-04): "actually check the length read from the data
  against the data size passed into this function (oss-fuzz)" — adds a
  check that the declared APP1 length does not exceed the actual number of
  bytes available in the input buffer (`ds`).

Both commit messages describe this as an oss-fuzz-found bug. The challenge
source sits in exactly the 3-day window between these two upstream fixes and
the previous commit — i.e. the author picked the precise upstream state that
is vulnerable to the bug these two commits fix, without introducing any
custom code of their own. This strongly confirms the challenge's "exact
source" hint: solve it as "which upstream bug applies to this exact
snapshot", not as a hand-planted backdoor (the libexif/ tree is an unmodified
, exact copy of a real historical commit).

See `notes/vuln.md` for where exactly in `exif_data_load_data` this bites and
how to trigger it.
