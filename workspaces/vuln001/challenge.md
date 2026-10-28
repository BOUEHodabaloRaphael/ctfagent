# VULN#001 — metadata service

- Platform: ctf.bugpwn.com
- Category: Vuln Research
- Points: 150 (decaying)
- Challenge ID: 24
- max_attempts: 2 (do not submit without near-certainty)

## Description (verbatim)

```
metadata service

The exact source
```

## Connection

```
nc 169.58.126.107 7027
```

## Attachment

`attachments/libexif-src.tar.gz` — source tarball of libexif (C library for
reading EXIF metadata from JPEG/TIFF files).

## Working hypothesis

The description "The exact source" + an attached tarball strongly implies the
remote service links against this *exact* libexif checkout (not a generic
system package), and the task is to diff it against upstream libexif history
to find which exact upstream bugfix commit(s) are *missing* — i.e. the
challenge is "spot the vulnerable version window", not a custom backdoor.

See `notes/version-diff.md` for the diff analysis and `notes/vuln.md` for the
identified bug.
