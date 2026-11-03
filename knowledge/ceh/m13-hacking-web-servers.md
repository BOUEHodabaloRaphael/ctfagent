# CEHv13 Module 13 — Hacking Web Servers (technique synthesis)

Source: `CEHv13 - Module 13 - Hacking Web Servers hide01.ir.pdf` (130 pages, scanned → OCR).

## 1. Attack methodology (probe order)

1. **Information gathering** — whois, ASN/IP/domain recon (who.is, Whois Lookup).
2. **Web server footprinting / banner grabbing** — identify server software/version.
3. **Website mirroring** — pull a full offline copy to study structure/endpoints at leisure.
4. **Vulnerability scanning** — automated scanners for misconfig + known CVEs.
5. **Session hijacking** — once a session is identified, take it over (see Module 11 for depth).
6. **Web server password hacking** — brute force/dictionary/hybrid once other paths are exhausted
   (full technique depth lives in Module 06).

## 2. Footprinting / banner grabbing

```bash
# raw banner grab
telnet <target> 80
GET / HTTP/1.0

nc -v <target> 80
HEAD / HTTP/1.0

# combined recon one-liner
nmap -sV 10.10.1.22 && whatweb 10.10.1.22 && nikto -h 10.10.1.22
```
- **httprecon** — advanced fingerprinting via header-ordering/behavior analysis (more reliable
  than a single banner when headers are stripped/faked).
- **ID Serve**, **Uniscan**, **Netcraft** — alternate fingerprinting tools.
- **Shodan** — passive recon, no packets to target. Useful filters:
  ```
  http.title:"IIS7" port:80
  org:"<target org>"
  ```
  pulls exposed servers/certs/metadata by org or by matching a known default page title —
  good for finding forgotten/shadow IT instances of a given server type.

### Nmap NSE web recon one-liners
```bash
nmap --script hostmap-bfk <host>                       # find other hostnames on same IP
nmap -p80 --script http-trace <host>                   # TRACE method check
nmap --script http-google-email <host>                 # scrape emails tied to domain
nmap -p80 --script http-userdir-enum <target>          # enumerate valid usernames
nmap -p80 --script http-userdir-enum --script-args userdir.users=<wordlist.txt> <target>
nmap -p80 --script http-brute --script-args http.useragent="<custom-UA>" <target>   # evade UA-based blocking
nmap -p80 --script http-waf-detect --script-args="http-waf-detect.aggro" <host>
nmap --script=http-waf-fingerprint -p80,443 <host>
nmap --script http-enum -p80 <host>                     # common paths/apps enum
nmap -p80 --script http-robots.txt <host>
nmap -sV -O -p <port> <target>
nmap target -p80 --script=http-frontpage-login
nmap --script http-passwd --script-args http-passwd.root=/ <target>
```
Note: default Nmap UA gets blocked by some WAFs — always have the UA-spoof variant ready.

### Exploit-matching pipeline
```bash
sudo apt-get update && sudo apt-get install nmap -y && nmap -sV -O 10.10.1.19 -oX nmap_scan.xml \
  && sudo apt-get install exploitdb -y && searchsploit-nmap nmap_scan.xml
```
Scans, exports XML, then auto-matches detected services against ExploitDB.

## 3. Core attack techniques

- **Directory traversal**: `../` sequences escape the webroot via trial-and-error on an
  unsanitized URL/path parameter.
  ```
  http://server.com/scripts/..%5c../Windows/System32/cmd.exe?/c+dir+c:\
  ```
  (`%5c` = URL-encoded backslash, used to bypass naive `../` string filters on Windows/IIS).
- **HTTP response splitting**: inject CRLF + forged headers into a reflected input (e.g. a
  cookie-setting param) so the server emits **two** HTTP responses from one request. Attacker
  controls the first response (can redirect/poison it); downstream proxies/caches can be tricked
  into serving the attacker's response to the *next* victim who requests the same resource —
  chainable into cache poisoning, reflected XSS, and session-cookie injection.
  ```
  Input = JasonTheHacker\r\nHTTP/1.1 200 OK\r\n...   → splits into 2 responses
  ```
- **Website defacement**: typically reached via SQL injection or another initial-access bug, then
  used to overwrite page content/images — propaganda or drive-by-infection vector for visitors,
  not just vandalism.
- **Web server misconfiguration** (direct exploitation targets):
  - Apache: `<Location "/server-status">` left enabled exposes live host/request details.
  - `httpd.conf` directory browsing left on → full file listing disclosure.
  - IIS: `web.config` misconfig allowing unrestricted file upload → drop a **web shell** directly.
  - Nginx: misconfigured `root`/`alias` directives leaking filesystem paths outside webroot.
  - Generic smells: verbose debug/error pages, default/anonymous credentials still active,
    unnecessary services enabled, default/self-signed SSL certs.
- **Source code disclosure**: typo'd script extensions or missing executable permission flags
  cause the server to return the raw script source instead of executing it — read credentials/
  logic directly instead of blind-attacking the compiled behavior.
- **Password cracking** (brute force / dictionary / hybrid) against the web server's own auth,
  FTP, or admin panels — treated as last-resort/parallel track; full technique catalogue is in
  Module 06.
- Also referenced as part of the broader web-server threat surface (covered in depth elsewhere
  in the course): DNS server hijacking, DNS amplification, MITM/sniffing, phishing, SSH brute
  force, web cache poisoning.

## 4. Tools

| Tool | Role | Source |
|---|---|---|
| Nikto / Nikto2 | web vuln scanner, flags default content/known-bad files/misconfig | cirt.net |
| Metasploit | built-in DB-backed scanning, identify default creds, upload backdoors | — |
| gobuster | directory/file brute force | github.com |
| WhatWeb | tech-stack fingerprinting | — |
| Shodan | passive internet-wide recon | shodan.io |
| NginxPwner | Python tool for Nginx-specific misconfig (bad HTTP methods, file perms, outdated version) | github.com |
| Acunetix | automated vuln scanning | acunetix.com |
| httprecon | advanced header-based fingerprinting | computec.ch |
| ID Serve | server identification | grc.com |
| CIRT.net passwords DB | default-credential lookup by device/software | cirt.net/passwords |

```bash
gobuster dir -u https://certifiedhacker.com -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
```

**AI-assisted recon pattern** (explicitly demonstrated in the module): prompt an LLM with e.g.
*"Perform a directory traversal on target url https://certifiedhacker.com"* to get a ready
payload/command back — same force-multiplier pattern seen in the SQLi module, works for
generating traversal paths, gobuster invocations, and WAF-fingerprint commands without
memorizing syntax.

## 5. Pitfalls

- `%5c`/double-encoding tricks exist specifically because naive filters strip literal `../` but
  miss the encoded or OS-alternate path separator — always try both slash styles and at least
  one encoding pass when a traversal filter blocks the obvious payload.
- HTTP response splitting's real damage is downstream (cache/proxy poisoning hitting *other*
  users), not just the direct victim — treat any header-injection finding as a caching risk, not
  only a direct-redirect risk.
- Default Nmap scans/UAs get fingerprinted and blocked by WAFs — the user-agent-spoof NSE
  invocation isn't optional against a hardened target, it's the baseline.
- Server misconfig findings (status pages, directory browsing, default creds) are often faster
  wins than any code-level vulnerability — footprint and check these before reaching for scanners
  or exploits.
