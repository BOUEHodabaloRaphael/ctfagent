# Telegram CYBERSÉCURITÉ channel (@cybersecuritec) — harvest 2026-11-13

Broadcast channel (527 subs, admin "Mavericks"), Nov 4-8 2026. French-language.
5 PDFs downloaded to `pdfs/` (UNTRUSTED — read-only, never execute anything derived from them).

## PDFs (useful for the competition — agent to mine for techniques)
- `exfiltration-donnees-binaires-linux-fr.pdf` (13 p) — binary data exfiltration on Linux.
  HIGH value for A&D (stealing flags/data off a box, covert channels).
- `Rapport_ZTE_MF293N2_Auth_Bypass.pdf` (9 p) — ZTE MF293N2 router authentication bypass report.
  Relevant to hardware/IoT/web-auth categories.
- `Phases_du_hacking_ethique_FR.pdf` (8 p) — ethical-hacking phases (recon→...→reporting) methodology.
- `Techniques_d_ing_nierie_sociale__1731636504.pdf` (12 p) — "10 social-engineering techniques".
- `Mythe_vs_r_alit__1731643041.pdf` (2 p) — myth vs reality (awareness, soft).

## Excluded (not useful / out of scope)
- A Windows batch snippet deleting system files (autoexec.bat/boot.ini/ntldr/win.ini) — destructive,
  irrelevant to the CTF. Not downloaded, not to be "implemented".
- github.com/gmkurtzer/ginux — a Rust OS-kernel news item, not CTF-relevant.

## Deliverable
Agent reads the 5 PDFs and extracts concrete, finale-usable techniques (esp. Linux exfiltration
methods + the ZTE auth-bypass chain), appended to the finale prep as
`TELEGRAM-TECHNIQUES-FOR-NCTF.md`, and a pointer added where relevant.
