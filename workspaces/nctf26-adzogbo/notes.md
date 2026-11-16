# 44r0nmeta--adzogbo (id 522, boot2root, 200pts, 0 solves at start)

Status: IN PROGRESS — foothold obtained, no flag yet. Paused to stay responsive
to new challenge drops (team priority); resumable any time.

## Target
Per-team instance via `team_instancer` (challenge_id=522), access="vpn",
reachable directly on our existing WireGuard tunnel (10.100.16.0/24 — unlike
komisergio--kpalime which needs a different, currently-unreachable subnet).
Host: 10.100.16.101. Domain: ADZOGBO.LOCAL. Samba 4.15.13-Ubuntu AD DC
(D3EE8B7402AF).

## Recon
- Targeted nmap (not -p-, learned lesson from HTB Pro Lab / KOTH cooldown):
  53,88,135,139,389,445,464,636,3268,49152-49154 open. Classic DC port set.
- Anonymous SMB + LDAP bind both work. Shares: sysvol, netlogon, public, IPC$
  (all READ for anonymous). `public\welcome.txt` lists 5 named accounts +
  roles (Olympio Corp flavor text):
  a.mensah (Accounting), k.eyadema (IT Support), d.agbeko (Marketing),
  svc-backup (Backup service), j.olympio (Project manager - "Confidential
  access" in his LDAP description).
- Anonymous LDAP full-attribute dump (hint 1: "Anonymous LDAP can reveal more
  than you think") shows svc-backup's `description` field leaks a temp
  password in clear: **svc-backup : Backup2026!** (confirmed working via SMB
  + LDAPS simple bind).
- AS-REP roast: tried all 6 real users, none have UF_DONT_REQUIRE_PREAUTH.
- Kerberoast: no user-owned SPNs (only krbtgt/DC SPNs).
- ACL review (DACLs on domain root, Administrator, j.olympio, Domain Admins,
  svc-backup itself) via ldap3 + impacket SR_SECURITY_DESCRIPTOR over LDAPS:
  svc-backup's SID appears on NO object with a non-default ACE. Only the
  standard built-in SIDs (SELF, SYSTEM, Account Operators, Authenticated
  Users, Domain Admins, Administrators, Cert Publishers, etc.) show up — no
  delegated GenericAll/WriteDacl/WriteOwner/extended-right to svc-backup, no
  group nesting beyond Domain Users (RID 1106, group 0x201 only). So no ACL
  abuse path found from svc-backup to j.olympio/Administrator.
- Hidden-share probing: `confidential` returns **STATUS_ACCESS_DENIED** with
  svc-backup (vs STATUS_BAD_NETWORK_NAME for made-up names like backup/data/
  home/etc.) — the share genuinely exists but svc-backup can't read it.
  Likely needs j.olympio's creds (matches his "Confidential access" note).
  Small themed password-spray against j.olympio (lockoutThreshold=0, confirmed
  via LDAP domain policy, so spraying is safe) — 9 candidates tried, all
  failed. Not a brute force in the art.7 sense (this is host auth, not flag
  submission) but kept deliberately small/themed, not exhaustive.
- DCSync attempt (`impacket-secretsdump -just-dc` / `-just-dc-user
  Administrator`, svc-backup creds): gets through DRSCrackNames (so *some*
  directory-level read succeeds) but DRSGetNCChanges fails — first with a
  spurious `DRSR SessionError: code 0x0 ERROR_SUCCESS` (an impacket
  rpcrt.py bug: it treats ANY non-zero trailing status bytes as an error
  even when the decoded code is 0 — reproduced, traced into rpcrt.py
  `request()`), and after monkey-patching that check off, with
  "DRSGetNCChanges didn't return any object" instead. This looks like a
  genuine impacket<->Samba-DRSUAPI protocol incompatibility (not a rights
  issue — our ACL scan found no DCSync delegation anyway, so this was always
  a long shot). pip has no newer impacket (0.13.1 is current).

## Next steps if resumed
1. Crack `confidential` share access: either find j.olympio's real password
   (current spray list was small/themed — could extend a bit further, still
   safe given lockoutThreshold=0) or find another path to it.
2. If DCSync is truly required: try Kerberos auth (`-k` with a TGT via
   impacket-getTGT) instead of NTLM for the DRSUAPI session — untested, might
   dodge whatever is breaking the NTLM-authenticated DRS channel against
   Samba. Or try a lower DRS protocol version explicitly.
3. Re-read hints with fresh eyes if truly stuck: hint 1 = anonymous LDAP
   description leak (done, got svc-backup's password). Hint 2 = "a service
   account password opens a share, read everything you can access before
   moving on" (done — sysvol/netlogon/public all read, nothing further found
   there). Both hints point at what we've already extracted, so either the
   `confidential` share IS the intended next step (need j.olympio or another
   account) or there's a share/avenue not yet discovered.

No flag submitted — nothing guessed, only confirmed facts recorded above.
