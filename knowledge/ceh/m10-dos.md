# CEHv13 Module 10 — Denial-of-Service (technique synthesis)

Source: `CEHv13 - Module 10 - Denial-of-Service hide01.ir.pdf` (80 pages, scanned → OCR).

## 1. Attack vector categories (triage by what's being exhausted)

| Category | Exhausts | Measured in | Examples |
|---|---|---|---|
| Volumetric | network bandwidth | bps | UDP/ICMP flood, PoD, Smurf, pulse wave, NTP amplification |
| Protocol | connection-state tables (load balancers, firewalls, app servers) | pps/cps | SYN/SYN-ACK/ACK flood, fragmentation, spoofed session flood, TCP SACK panic |
| Application (L7) | app/service resources, few machines needed | rps | HTTP GET/POST, Slowloris, UDP app-layer flood, DDoS extortion |

Botnet basics: DDoS = many compromised "zombies" (secondary victims) attack through a C&C
layer; attacker → handler(s) → agents/bots → target. Fewer handlers than agents, so neutralizing
handlers is the efficient kill point.

## 2. Volumetric techniques

- **UDP flood**: spoofed-source UDP packets at high rate to random ports → server burns cycles
  replying ICMP "Destination Unreachable" to every one, bandwidth exhausted.
- **ICMP flood**: mass spoofed ICMP ECHO requests, direct or via reflection → saturates link.
  Defense: cap ICMP to ~1000 pkt/s/zone, drop excess for current+next second.
- **Ping of Death**: single malformed/oversized ping packet (>65,535 bytes, RFC 791 limit) →
  crash on reassembly. Needs only the target IP.
- **Smurf**: spoof source = victim IP, broadcast ICMP ECHO to an IP broadcast network → every
  host on that subnet replies to the victim simultaneously.
- **Pulse wave**: periodic huge bursts (300+ Gbps pulses every ~10 min, campaign lasts hours-days)
  instead of continuous flood — harder to absorb/recover from.
- **NTP amplification**: spoof victim IP, send `monlist` request to NTP servers with monlist
  enabled → large amplified response floods victim.
  ```bash
  nmap -sU -pU:123 -Pn -n --script=ntp-monlist <target>   # enumerate monlist-enabled NTP server
  ```
  Countermeasures: harden/disable monlist, rate-limit NTP, firewall NTP requests.

## 3. Protocol techniques

- **SYN flood**: spoofed SYNs, never ACK → target's listen queue (75s hold per half-open conn)
  fills, legit connections denied. Variants: **SYN-ACK flood** (exploit handshake stage 2),
  **ACK/PUSH-ACK flood** (spoofed ACK/PUSH-ACK mid-session).
  Countermeasures: SYN cookies, SynAttackProtect, shorten SYN-RECEIVED timeout/retransmit count.
- **Fragmentation attack**: flood with randomized-content 1500+ byte fragments at low pps —
  fragments pass most firewalls/IDS uninspected, but reassembly cost crashes the target.
- **Spoofed session flood**: fake TCP sessions via SYN+ACK+RST/FIN combos to slip past
  firewalls that only key on SYN. Variant with SYN packets skipped entirely (ACK+RST/FIN only)
  specifically evades SYN-based firewall detection.
- **TCP SACK panic**: send SACK packets with MSS forced to minimum (48 bytes) → Linux socket
  buffer (max 17 segments) overflows → integer overflow → kernel panic. Works against
  containers/VMs too (kernel-stack bug). Countermeasures: patch kernel, firewall-block requests
  advertising minimal MSS.
- **DRDoS (reflection)**: zombies send spoofed-source (=victim IP) SYNs to uncompromised
  reflectors → reflectors' SYN/ACK floods the victim, who never sent the original SYN → very
  hard to trace back to the attacker. Countermeasure: disable CHARGEN, patch servers.

## 4. Application-layer (L7) techniques

- **HTTP GET attack**: hold connections open with a time-delayed/never-completed header.
- **HTTP POST attack**: complete headers, deliberately incomplete body → server waits forever.
- **Slowloris**: send many partial HTTP requests, each keeping a connection open waiting for
  completion → exhausts max concurrent connections using *perfectly legitimate* traffic (low
  bandwidth, hard to signature-match).
- Flood variants to know: **single-session** (many requests in one HTTP/1.1 session), **single-
  request** (multiple requests packed into one packet — stealthy/anonymous), **recursive GET**
  (crawl-like page/image fetching that's actually a flood), **random recursive GET** (same vs.
  forums/blogs using random page numbers to look organic).
- **UDP application-layer flood**: abuse UDP-based app protocols directly — CHARGEN, SNMPv2,
  QOTD, NTP, RPC, SSDP, TFTP, NetBIOS, Quake protocol, Steam protocol, VoIP, CLDAP.
- **Peer-to-peer attack**: exploit DC++ (Direct Connect) bugs to instruct P2P hub clients to
  disconnect from their swarm and mass-connect to the victim instead — no botnet needed.
  Mitigation: block/restrict the P2P port (e.g. force port 80 only).
- **Permanent DoS (PDoS) / phlashing**: trick victim into installing a fraudulent "firmware
  update" (via email/IRC/social posts) that bricks network hardware (routers, printers) —
  irreversible, requires hardware replacement.
- **DDoS extortion / RDDoS**: ransom note + a small demo DDoS to prove capability, demanding
  payment to avoid the full attack. Response: don't negotiate, report to law enforcement,
  evaluate exposed assets, pre-arrange BGP/DNS swing + always-on protection.
- **Multi-vector**: chain/parallelize volumetric + protocol + app-layer to misdirect defenders.

## 5. Tools cited

| Tool | Notes | Source |
|---|---|---|
| HOIC (High Orbit Ion Cannon) | GUI DDoS, booster scripts | sourceforge.net |
| LOIC (Low Orbit Ion Cannon) | GUI DDoS, classic "volunteer" tool used in HOIC case study | sourceforge.net |
| HULK | HTTP flood | github.com |
| Slowloris | L7 partial-request DoS | github.com |
| UFONet | P2P/botnet-assisted L7 DDoS | ufonet.03c8.net |
| ISB ("I'm So Bored") | HTTP/UDP/TCP/ICMP flood + recon one-click (WHOIS/netstat/traceroute/ping) | sourceforge.net |
| UltraDDOS-v2 | simple GUI: target IP, port, packet count | sourceforge.net |
| Packet Flooder Tool | generic flood | netscantools.com |

Case study mechanism worth remembering: hacker hosts HOIC on a (compromised) web server,
advertises it on social media, volunteers download it and idle in an IRC channel awaiting the
"fire" command against a named target (PayPal/Mastercard-style campaigns).

Real-world reference: **HTTP/2 Rapid Reset** (CVE-2023-44487, CVSS 7.5) — abuses HTTP/2 stream
multiplexing (up to 100 live streams/TCP connection) by opening and immediately RST-ing a rapid
sequence of streams, peaked at 398M req/s against Google.

## 6. Detection techniques

- **Activity profiling**: baseline average packet rate per flow (similar header fields); rising
  entropy/diversity or more distinct clusters = possible attack.
- **Sequential change-point detection**: CUSUM algorithm on traffic time series filtered by
  IP/port/protocol — flags drastic deviation from expected local average; also catches worm scans.
- **Wavelet-based signal analysis**: decompose traffic into frequency components; normal traffic
  is low-frequency, attack traffic raises high-frequency energy.

## 7. Countermeasures / mitigation playbook

Strategic choice: **absorb** (pre-provisioned capacity, costly even when idle) vs **degrade**
(keep only critical services up) vs **shut down** (last resort).

- **Egress filtering**: drop outbound packets whose source doesn't match the internal network —
  blocks spoofed-source traffic leaving, and return-connections from zero-day payloads.
- **Ingress filtering** (ISP-side): block spoofed source IPs from entering, keeps origin traceable.
- **TCP Intercept** (router feature): proxy the handshake — router completes SYN with client and
  separately with server, only joins the two halves once both succeed; blocks pure SYN floods.
- **Rate limiting**: cap in/out traffic on the NIC, typically applied at OSI L4/5 on edge hardware.
- **RFC 3704 filtering**: ACL drop on "bogon list" (unused/reserved IP space) — if ISP doesn't do
  this, maintain your own bogon ACL or switch ISP.
- **Cisco IPS source-IP reputation** (Cisco Global Correlation / SensorBase): drop traffic from
  known botnet/malware-associated IPs before it hits assets.
- **Black hole / RTBH filtering**: route attack traffic to a BGP null0 next-hop in coordination
  with the ISP — traffic silently dropped, source gets no feedback.
- **ISP "clean pipes" / cloud scrubbing**: ISP or third party (Imperva, VeriSign, Cloudflare,
  Akamai) scrubs traffic upstream so the link itself never saturates; can also move the target to
  a new IP via DNS after blocking the old one.
- **Honeypots** (deflect): low-interaction or high-interaction (honeynet) decoys to absorb
  handler/agent installation attempts and harvest attacker TTPs instead of hitting real assets.
- Hygiene checklist: SYN cookies on, disable CHARGEN/echo, kernel + protocol stack patched,
  WPA2/WPA3+AES-256 on wireless, block inbound traffic from known reflector service ports, deny
  external ICMP at the firewall, strict input validation (kill `gets`/`strcpy`-style unbounded
  copies), distributed/colocated server model so no single bottleneck exists.

Commercial protection platforms referenced: Checkpoint Quantum IPS, Cisco Guard/IPS, Fortinet,
A10 Thunder TPS, Huawei AntiDDoS1000, BeeThink, Cloudflare, Akamai.

## 8. Pitfalls / notes

- Blind sequence-number-style tricks don't apply here (that's session hijacking territory) — DoS
  detection's real weakness is distinguishing a flash crowd from an attack; entropy/CUSUM/wavelet
  methods all exist because naive thresholding alone produces too many false positives.
- SYN-skip spoofed-session variants exist *specifically* to dodge firewalls that only pattern-match
  on SYN packets — don't assume "no SYN seen" means "no flood happening."
- PDoS and DDoS-extortion don't require any botnet infrastructure at all — cheapest attacks in
  this module, and the easiest to underestimate during triage.
