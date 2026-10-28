---
doc_kind: pattern
title: "Kiosk / Electron Breakout via Crashed Driver Dialog"
category: misc
slug: kiosk-electron-breakout-crash-dialog
created: 2026-10-04
status: active
tags:
  - windows
  - kiosk
  - electron
  - gui-breakout
  - rdp
chain_summary: "Trigger a background hardware-driver process to crash (often via an exposed admin API toggling device power) so Windows shows a native error dialog with a clickable support link; click it to spawn a full, unconfined browser outside the kiosk shell."
---
# Kiosk / Electron Breakout via Crashed Driver Dialog

## Chain Summary

- One-line chain: Trigger a background hardware-driver process to crash (often via an exposed admin API toggling device power) so Windows shows a native error dialog with a clickable support link; click it to spawn a full, unconfined browser outside the kiosk shell.
- Typical target shape: an Electron (or browser-kiosk-mode) full-screen app on a Windows box reachable via RDP, paired with a separate admin/management web panel that controls simulated or real peripherals (scanner, printer, badge reader, POS hardware...).

## Preconditions

- RDP (or local console/VNC) access to the kiosk session, even as a restricted/unprivileged user.
- A companion admin interface (often a separate port, e.g. an HTTP panel) that can toggle a device's "powered" state or otherwise interrupt a driver the kiosk depends on.
- Devtools, right-click menu, Alt+F4, Win key, and Ctrl+Alt+Del are all disabled/intercepted by the kiosk shell (otherwise just use those directly — this pattern is for when they're locked down).

## Cheap Probes

- `Alt+Tab` once or twice — kiosk watchdogs sometimes leave a launcher `cmd.exe` window reachable (often itself in a busy loop, not directly useful, but confirms other windows exist behind the kiosk).
- Read any discoverable admin panel's client-side JS for device-control endpoints (`/api/.../power`, `/api/.../restart`, etc.).
- Trigger any kiosk action that depends on the toggled device (e.g. "scan" / "print" / "test") right after disabling it via the admin API.

## Telltale Evidence

- A native Win32 `MessageBox`-style dialog appears, often titled "<Vendor> <Product> - Error" with text like "has stopped responding", an error code, and — critically — a **blue underlined hyperlink** to a "support"/"troubleshoot" page.
- The dialog may itself become permanently "Not Responding" (frozen bitmap) after this — that's fine, it's independent from the browser it spawns; don't waste time trying to close it, just alt-tab past it.

## Escalation Order

1. Enumerate the admin/management interface available alongside the kiosk (often a separate port) and authenticate if a password was given/discoverable.
2. Read its client-side JS/API to find device power-toggle or similar disruptive-but-authorized endpoints.
3. Power off the relevant device(s) via the API.
4. From the kiosk GUI, trigger the action that depends on that device (scan, print, badge check...).
5. A native Windows error dialog pops up with a clickable link — click it.
6. The OS launches the **default browser** (Edge/Chrome) to handle the link — this browser is a full, unconfined application, not sandboxed by the kiosk.
7. From that browser: `file:///C:/...` to read files directly with no shell; `Ctrl+S` (Save As) or `Ctrl+O` (Open) to reach a **real common file dialog**, then click the target folder's "open in Explorer" icon (not just type a path — modern Explorer common dialogs route plain text typed in the path box into a *search* box, not a navigation/run box) to get a genuine Explorer window, then navigate/search for `cmd.exe` and double-click to launch an interactive shell.
8. If blind-driving this over RDP from a non-GUI attacker host: `Xvfb :99` + `xfreerdp ... /sec:rdp` (older DeviceHub-style servers often refuse TLS/NLA — the negotiation log will say `SSL_NOT_ALLOWED_BY_SERVER`; force `/sec:rdp` to fall back to plain RDP security) + `xdotool` for mouse/keyboard + `import -window root` for screenshots to "see" the remote screen turn by turn.

## Common Mistakes

- Clicking directly in a Save-As dialog's breadcrumb/search box and typing a command — modern Windows common file dialogs treat free text there as a *search query*, not a Run command; this does not execute anything (unlike very old Windows versions). Use the real Explorer window reachable via the folder-shortcut icon instead.
- Assuming disabling a device is purely cosmetic — on a kiosk built around simulated/virtual hardware, "powering off" a device is often exactly what makes its driver process throw an unhandled exception and pop the native dialog you need.
- Giving up after the first device-disable attempt does nothing visible — the crash may require the kiosk to actively *try to use* the device afterward (e.g. navigate to the scan/badge screen and tap "scan"), not just the power-off call itself.

## Payload Shapes

```bash
# Headless, blind RDP automation from a Linux attacker box
Xvfb :99 -screen 0 1280x800x24 &
DISPLAY=:99 xfreerdp /v:TARGET /u:USER /p:'PASS' /cert:ignore /sec:rdp /w:1280 /h:800 +clipboard -wallpaper &
DISPLAY=:99 xdotool mousemove X Y click 1
DISPLAY=:99 import -window root screenshot.png   # then view the PNG to decide the next click
```

## Related Writeups

- `writeups/misc/htb-touch-kiosk-plugin-hijack.md`

## Skill Impact

- Related skill: `browser-automation` (blind RDP driving loop is a reusable technique, not currently documented there) and a potential future `windows-kiosk-breakout` skill.
- Rule to add or update: when facing a locked-down Windows kiosk with no obvious breakout, check for an adjacent admin/device-management interface first — disrupting a peripheral it controls is a reliable way to surface a native OS dialog with a browser-launching hyperlink.
