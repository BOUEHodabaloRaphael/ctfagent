---
doc_kind: workspace-notes
id: alchemy
title: Alchemy
category: pwn
status: new
tags:
  []
---
# Notes

## Validated findings (facts)

Full /24 sweep (top-200 ports, -Pn) + full-port/version scan on ICMP responders.
Only 4 hosts on 10.10.110.0/24 show real (non-filtered) services; everything else
returns "all ports filtered" noise from -Pn on non-existent/firewalled IPs — treated
as a dead end, sweep killed early once pattern was clear.

| IP | Hostname | Ports | Notes |
|---|---|---|---|
| 10.10.110.1 | - | 22/tcp ssh OpenSSH 9.4, 443/tcp ssl/https nginx | Likely jump/edge host or lab infra, not in the named machine list -> investigate HTTPS vhost |
| 10.10.110.2 | firewall.dante.local | 4000/tcp closed "remoteanything" | rDNS = firewall.dante.local -> strong match for **ALCHEMY-FW** (FreeBSD). "Dante" = Dante SOCKS proxy, FreeBSD-native. Port 4000 closed (not open) so likely not directly useful yet. |
| 10.10.110.21 | - | 22/tcp ssh OpenSSH 7.6p1 Ubuntu, 80/tcp http "Rocket", 3000/tcp http Golang net/http | Candidate for **ALCHEMY-WEB01** or **WEB02**. Port 3000 is a custom Go web app - error leaked a Go template panic: `template: base/footer:15:47: executing "base/footer" at <.PageStartTime>: invalid value; expected time.Time` -> custom app, worth source/behavior probing. Port 80 "Rocket" server banner (Python framework, e.g. Bottle/CherryPy-family) -> separate app on same host. |
| 10.10.110.100 | - | 22/tcp ssh OpenSSH 8.4p1 Debian, 1194/tcp openvpn? | Debian host running OpenVPN -> candidate OT/IT bridge or secondary VPN endpoint (ALCHEMY-EW "engineering workstation"/edge?), needs confirmation. |

## Hypotheses

- 10.10.110.2 = ALCHEMY-FW (FreeBSD firewall/perimeter, Dante SOCKS).
- 10.10.110.21 = a WEB0x box exposing two distinct web apps (port 80 Python/Rocket, port 3000 Go) -> entry point for web-triage.
- 10.10.110.100 = possible OT-facing pivot (OpenVPN) or secondary access path, not yet explored.
- 10.10.110.1 is unaccounted for in the named machine list from the lab page; could be the HTB lab gateway itself rather than a scored machine - verify before spending time on it.

## Dead ends

- Full /24 top-200-port sweep with -Pn: beyond the 4 ICMP-responding hosts, every other IP returns "all ports filtered (no-response)" - artifact of -Pn against addresses with no real host/firewalled, not useful signal. Killed scan early, no further blind /24 sweeping planned.
- Port 4000/tcp on firewall.dante.local (10.10.110.2) is closed, not open - no immediate path there.

## Next step

Switch to `web-triage` on 10.10.110.21:80 and :3000 (two separate web stacks on one box) - this is the strongest, cheapest next probe per ROE ("no fuzzing" applies to PLCs, not web triage).

## Dead end / lab mechanic (2026-10-05 ~12:20 UTC)

After the earlier `-p- --min-rate 1000` full-port scan against 10.10.110.21, all subsequent
HTTP requests to ports 80 and 3000 on that host hang indefinitely (TCP handshake completes,
no data ever returned) - raw `nc`, `curl` (multiple UAs/HTTP versions), and even a fresh
`nmap -sV` on just those 2 ports all hang/timeout. ICMP ping to the same host still works
fine (~105ms RTT), so this is not a routing/VPN issue - it looks like an IPS/fail2ban-style
temporary source-IP blacklist on the HTTP service triggered by the aggressive scan rate.
Lesson for future recon in this lab: avoid `-p- --min-rate` full-port blasts against a single
host; prefer `--top-ports` / slower `-T2`/`-T3` timing once a host is already known to be
interesting. Waiting out the blacklist before retrying lightly (single curl, no further scans).

Retry at ~12:32 UTC (single curl, no scanning): still CODE:000 / full 10s timeout on both
80 and 3000. Block has not expired yet or lasts longer than ~12 min. Not re-scanning;
just waiting longer before the next single-request check.

Ruled out source-IP blacklist theory: reconnected VPN to a fresh IP (10.10.14.32,
confirmed via `ip route get`), hang persisted identically on .21:80, .21:3000, AND
.1:443. Meanwhile SSH banners and ICMP on the same hosts respond instantly on the
new IP too. Conclusion: this is a server/service-side hang (very likely caused by our
own `-p- --min-rate 1000` full-port scan sending malformed probes into the Go app on
.21:3000, and possibly a shared L7 component in front of .1/.2/.21), NOT a firewall
rule keyed on our client IP. Decision: request an HTB Lab Reset rather than keep
waiting or scanning more - zero flags captured so no progress lost, and a reset is
the reliable fix for a service we likely broke ourselves.

LESSON (-> candidate for ctf-knowledge-capture / skill-maintainer later):
Never run `nmap -p- --min-rate 1000 -sV` against unknown/custom web apps (esp. Go/
custom stacks already showing template panics) in a single aggressive pass. Prefer
`--top-ports 1000 -T2/-T3` first, then a light manual curl/browser check, before any
full 65535-port version-detection scan. Full -p- scans here caused what looks like a
persistent app-level hang requiring a lab reset.

CONFIRMED CROSS-LAB (2026-10-05, Tengu Pro Lab): the exact same symptom reproduced on
a totally different HTB Pro Lab (Tengu, 10.13.38.40, TENGU-NODERED/Node-RED on 1880)
with a fresh VPN session/source IP, immediately after a plain `nmap -sV -T3 -p-` scan
(no forced --min-rate this time, so it's not about scan speed). Local conntrack table
checked and healthy (276/262144, 0 entries for the target) - ruling out a local cause.
This is very likely a deliberate HTB Pro Lab anti-scan mechanic: a full port/version
scan against a target puts its HTTP service into a cooldown/quarantine state for an
extended period (25+ min observed on Alchemy before giving up), independent of client
source IP, while SSH/ICMP stay unaffected. STRONG RULE GOING FORWARD: avoid `-p-`
full-port scans on HTB Pro Lab targets entirely when possible; a `--top-ports` scan
already revealing the interesting service is enough evidence - don't escalate to -p-
just to be thorough, it reliably costs 20-30+ min of blocked HTTP access per target hit.
If a target's HTTP stops responding after any scan, go straight to requesting a
per-machine redeploy ("Unresponsive Machine") rather than waiting it out or fiddling
with the VPN - waiting and VPN reconnects were already proven not to help.
