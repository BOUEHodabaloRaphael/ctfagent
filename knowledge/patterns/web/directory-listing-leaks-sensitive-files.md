---
doc_kind: pattern
title: "Directory Listing Leaks Sensitive Files"
category: web
slug: directory-listing-leaks-sensitive-files
created: 2026-11-09
status: active
tags:
  - directory-listing
  - recon
  - backup-file
  - webshell-discovery
chain_summary: "Apache/Nginx Options +Indexes on a backup/upload dir exposes .bak configs, credential notes, or pre-planted webshells without any auth bypass needed"
---
# Directory Listing Leaks Sensitive Files

## Chain Summary

- One-line chain: Apache/Nginx `Options +Indexes` on a backup/upload dir exposes `.bak` configs,
  credential notes, or pre-planted webshells without any auth bypass needed.
- Typical target shape: PHP/Apache app with a `/backup/`, `/uploads/`, `/old/`, `/dev/`, `/files/`-style
  directory that was meant to be private but has no `Options -Indexes` and no index file to mask the
  listing.

## Preconditions

- Apache (or Nginx `autoindex on`) serving a directory with no index file and directory listing not
  explicitly disabled.
- The directory contains something sensitive: a `.bak`/`.old`/`~` backup of source code, a notes file with
  credentials, or files left over from development/a prior compromise.

## Cheap Probes

- Probe common backup/upload directory names directly (don't rely on a generic wordlist alone — think
  about what the app's theme/prompt suggests): `/backup/`, `/backups/`, `/old/`, `/uploads/`, `/files/`,
  `/dev/`, `/private/`, `/config/`, `/.git/` (last one needs a different technique, not listing).
- A `301` response on a bare directory path (no trailing slash) is a strong signal the directory exists —
  follow up with the trailing-slash `GET` to see if listing is on.
- If the app's challenge/prompt text hints at "exposure of configuration data" or similar, go straight for
  this instead of spending time on auth bypass / injection first.

## Telltale Evidence

- Response body starts with `<title>Index of /...</title>` (Apache's default listing page) or equivalent
  Nginx autoindex HTML.
- Listed filenames ending in `.bak`, `.old`, `~`, `.swp`, or just unexpected loose `.php` files that aren't
  linked from the app's UI.

## Escalation Order

1. Enumerate candidate directory names (seeded by the app's theme/prompt wording, not just a blind
   wordlist).
2. On any `301`/`200` hit for a bare directory, re-request with trailing slash to check for listing.
3. Download every listed file; read backup/config files directly; for any stray `.php` file, test common
   webshell params (`?cmd=`, `?c=`) before assuming further exploitation is needed.
4. Any credentials found (DB creds, "backup creds for testing" comments, etc.) — try them against **both**
   the web app login **and** SSH with matching usernames (password reuse is extremely common in these
   exam/CTF boxes).

## Common Mistakes

- Spending time on SQLi/auth-bypass against a login form before checking for this far cheaper recon win —
  when the prompt text mentions "configuration exposure" or similar, that's a direct signal to check this
  first.
- Assuming a stray `.php` file found via listing needs to be exploited (LFI/upload) rather than just
  requested directly with common shell params — it may already be a pre-planted webshell.

## Payload Shapes

```text
GET /backup/              -> Apache "Index of /backup" listing
GET /backup/config.php.bak -> leaked plaintext source (e.g. $db_user/$db_pass)

GET /uploads/              -> "Index of /uploads" listing exposes file.php, credential.php
GET /uploads/file.php?cmd=id -> pre-planted webshell, unauthenticated RCE as www-data
```

## Related Writeups

- [[thundercipher-tcvapt-vault]] — `/backup/config.php.bak` leaked DB creds reused for web login + SSH.
- [[thundercipher-tcvapt-uploadx]] — `/uploads/` listing exposed a pre-planted webshell + a credential
  notes file.

## Skill Impact

- Related skill: `web-triage` / `ctf-web` — recon phase should include directory-listing + backup-file
  probing as a cheap early step, informed by the challenge's own prompt wording, before investing time in
  SQLi/auth-bypass attempts on a login form.
- Rule to add or update: when challenge text mentions "configuration/data exposure" or similar, prioritize
  backup/config file disclosure probes over injection attacks.
