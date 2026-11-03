# CEHv13 Module 08 — Sniffing (technique synthesis)

Source: `CEHv13 - Module 08 - Sniffing hide01.ir.pdf` (112 pages, scanned → OCR).

## 1. Core concept

Sniffing = flip NIC into **promiscuous mode** so it accepts all frames on the segment, not just
ones addressed to it. Works directly on hubs/wireless (broadcast medium); on switches requires
first forcing traffic to the attacker's port (MAC flood, ARP poison, DHCP spoof, port mirror
abuse, STP manipulation) — that's why switch-targeted attacks dominate this module.

Two sniffing classes: **passive** (hub/shared medium, just listen) vs **active** (switched —
must inject traffic to redirect flows first).

## 2. MAC attacks

- **MAC flooding**: flood the switch's CAM table with bogus source MACs until it's full → switch
  fails open and starts behaving like a hub, broadcasting everything to every port.
  ```bash
  macof -i eth0            # dsniff suite; floods LAN with random src MAC/IP packets
  ```
- Countermeasure: enable **port security** (limit learned MACs per port) → switch locks the port
  and sends an SNMP trap when the limit's exceeded.
- **Switch port stealing**: attacker floods the switch with forged gratuitous ARP replies using
  the *victim's source MAC* but the *attacker's own port* → switch's CAM table re-associates the
  victim's MAC to the attacker's port, silently stealing traffic meant for the victim.

## 3. DHCP attacks

- **DHCP starvation**: flood the DHCP server with bogus DISCOVER/REQUESTs (spoofed MACs) until
  its address pool is exhausted → legitimate clients can't lease an address.
  Tool: **Yersinia** (dedicated DHCP-starvation module).
- **Rogue DHCP server** (used together with starvation): once the real server is starved, stand
  up a rogue DHCP server to hand out attacker-controlled gateway/DNS to new clients → sets up a
  full MITM.
- Countermeasures: enable **DHCP snooping** on switches (only trust DHCP replies from configured
  trusted ports), **port security** to rate-limit DISCOVER floods, static IP/ARP binding for
  critical hosts.

## 4. ARP poisoning / spoofing

Send unsolicited/forged ARP replies mapping the gateway's IP to the attacker's MAC (and vice
versa for the victim) → both sides route through the attacker → classic MITM for sniffing,
session hijack, or DoS (drop instead of forward).
```bash
arpspoof -i eth0 -t <victim-ip> <gateway-ip>     # dsniff suite, redirects victim->gateway traffic
```
Tools: **Ettercap**, **bettercap** (both do ARP poisoning + sniffing + DHCP spoofing out of one
tool), **Cain & Abbel** (legacy Windows), arpspoof.

Countermeasures: static ARP entries for critical hosts, **Dynamic ARP Inspection (DAI)** on
switches (validates ARP against DHCP snooping binding table), tools like **XArp** to monitor
MAC/IP pair consistency. Detection: **Wireshark** or **Colasoft Capsa** flag abnormal ARP
request/reply ratios and duplicate IP-to-MAC mappings.

## 5. MAC spoofing / duplicating

Change the NIC's MAC to match a trusted/authorized device to bypass MAC-based ACLs or
impersonate another host on the segment.
```powershell
# Windows 11: Device Manager > NIC > Advanced > Network Address, or via registry NetworkAddress value
```
Tools for MAC spoofing cited generically (Windows/Linux GUI changers). Countermeasure: 802.1X
port-based auth + DHCP snooping binding so a spoofed MAC still can't get a lease/forward.

## 6. VLAN hopping

Goal: reach a VLAN you're not assigned to, from an access port.
- **Switch spoofing**: attacker's host speaks DTP (Dynamic Trunking Protocol) to the switch,
  negotiates itself into trunk mode → now receives tagged traffic for *all* VLANs.
- **Double tagging**: craft a frame with two 802.1Q tags; first switch strips the outer
  (native-VLAN) tag and forwards, exposing the inner tag to hop into a different VLAN —
  works only when attacker is on the native VLAN of the trunk.

Countermeasures: disable DTP/auto-trunking on access ports (`switchport mode access` + `nonegotiate`),
never use VLAN 1 as native/management VLAN, explicitly prune unneeded VLANs off trunks.

## 7. STP attack

Connect a rogue switch advertising a lower bridge priority than the real root bridge → rogue
switch gets elected new STP root → all inter-switch traffic reroutes through the attacker's
box (MITM at L2, network-wide).

Countermeasures: **BPDU Guard** (disables a port the instant it receives a BPDU where none is
expected — on access ports), **Root Guard** (prevents a port from becoming root port, keeps the
real root bridge fixed), network segmentation to cap the blast radius.

## 8. DNS poisoning (4 variants)

- **Intranet DNS spoofing**: on a switched LAN, combine with ARP poisoning to intercept and
  fake DNS replies to internal clients.
- **Internet DNS spoofing**: infect the victim with a Trojan that silently rewrites their DNS
  server IP to an attacker-controlled resolver — works from anywhere, no LAN access needed.
- **Proxy server DNS poisoning**: push a malicious proxy config (e.g. via a fake PAC file or
  DHCP option) onto the victim so all their traffic — including DNS — routes through the
  attacker's proxy.
- **DNS cache poisoning**: inject forged records into a resolver's cache so it returns the
  attacker's IP for a legitimate domain until the TTL expires — widest blast radius since it
  affects every client using that resolver.
Tool cited: **DerpNSpoof**.

Countermeasures: DNSSEC, restrict recursive DNS to trusted clients, randomize query
source-port/transaction-ID, keep resolver software patched (classic Kaminsky-style cache
poisoning depends on predictable query IDs/ports).

## 9. Sniffing tools

| Tool | Role |
|---|---|
| Wireshark | capture/analyze; use "Follow → TCP Stream" to reconstruct a session inline |
| Colasoft Capsa | portable network analyzer, cross-source traffic consolidation |
| LiveAction | network performance + packet analysis |
| dsniff suite (macof, arpspoof, dsniff itself) | MAC flood, ARP spoof, credential sniffing |
| Ettercap / bettercap | ARP poisoning + sniffing + plugins, all-in-one MITM framework |
| Yersinia | L2 attack framework (DHCP starvation, STP, VLAN, etc.) |

### Useful Wireshark filters
```
tcp.flags.reset==1                              # all TCP resets
udp contains 33:27:58                           # raw hex match at any offset
http.request                                    # all HTTP GET requests
tcp.analysis.retransmission                     # retransmissions
(arp or icmp or dns)                            # mask to just these protocols
tcp.port == 4000                                # specific TCP port
tcp.port eq 25 or icmp                          # SMTP + ICMP only
ip.src==192.168.0.0/16 and ip.dst==192.168.0.0/16   # LAN-only traffic
```

## 10. Detecting sniffers on a network

- **Ping method**: send a ping to the suspect IP with a *deliberately wrong* MAC address. A
  normal NIC drops it (MAC mismatch); a NIC in promiscuous mode still answers because it isn't
  filtering on destination MAC.
- **DNS method**: sniffers that resolve captured IPs generate extra **reverse DNS lookup**
  traffic. Monitor the DNS server for unexpected reverse-lookup volume, or send ICMP to a
  non-existent IP and see who performs a reverse lookup on it anyway.
- **ARP method**: send a non-broadcast (unicast, directed) ARP request to one host, then
  broadcast-ping that host's IP with a different MAC. Only a box already caching the correct
  mapping (because it's sniffing/promiscuous) replies; everyone else has to ARP-probe first.
- **Promiscuous-mode detection tools**: **Nmap** (`nmap --script=sniffer-detect`-style checks /
  general NIC-mode probing), **NetScanTools**.

## 11. General sniffing countermeasures

- Prefer switched + segmented networks over hubs/flat broadcast domains; VLAN-segment sensitive
  traffic.
- Use encryption end-to-end (TLS/SSH/IPsec/VPN) so captured packets are useless even if sniffed.
- Static ARP/DHCP bindings for critical infra; DHCP snooping + DAI on all access switches.
- Retrieve MAC addresses directly from NICs/switch configs rather than trusting network-supplied
  values when verifying device identity.
- Run IDS/IPS tuned to flag MAC-address churn, ARP anomalies, and rogue DHCP/STP advertisements.
- Periodically run the detection methods above (ping/DNS/ARP/promiscuous-scan) as an active
  control, not just reactive IDS alerting.

## 12. Pitfalls

- Standalone sniffers that never transmit (true passive capture) leave **no network trace** —
  the ping/ARP detection methods above only catch sniffers that still respond to packets or do
  reverse DNS; a disciplined passive tap is undetectable by traffic analysis alone.
- VLAN double-tagging only works if the attacker sits on the trunk's native VLAN — check native
  VLAN assignment before ruling this vector in or out.
- MAC flooding is loud (huge traffic spike) and will often trip an IDS/port-security alert before
  it finishes — ARP poisoning is the quieter, more reliable way to redirect switched traffic.
