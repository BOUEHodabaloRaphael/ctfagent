# Knowledge Index
## Writeups

### crypto
- [ADOKPO (LWE toy instance)](knowledge/writeups/crypto/adokpo-lwe-esig.md)
- [Broken](knowledge/writeups/crypto/broken-padding-oracle.md)
- [Twin_Prime](knowledge/writeups/crypto/twin-prime-fermat-rsa.md)

### misc
- [FAFA](knowledge/writeups/misc/fafa-whitespace-stego.md)
- [HTB Pro Lab Ascension - SQLi to SQLAgent RCE to Cross-Forest RBCD (7/7 flags)](knowledge/writeups/misc/htb-ascension-prolab-sqli-rbcd-cross-forest.md)
- [HTB Autopilot (Insane) - Grommunio Webshell to FastCGI Pivot to Postfix SUID Root to AD DA](knowledge/writeups/misc/htb-autopilot-grommunio-fastcgi-postfix-suid-ad.md)
- [HTB Pro Lab Offshore - Cross-Forest AD Compromise (22/38 flags)](knowledge/writeups/misc/htb-offshore-prolab-cross-forest-ad.md)
- [HTB Pro Lab Reflection (EU Mini Pro Lab 1) - Double NTLM Relay via xp_dirtree (Unsolved, Handoff)](knowledge/writeups/misc/htb-reflection-prolab-double-ntlm-relay-handoff.md)
- [HTB Secret Treasures - SPI Flash Read via LCG-Scrambled Addresses](knowledge/writeups/misc/htb-secret-treasures-flash-lcg.md)
- [HTB Touch - Kiosk Breakout to SYSTEM via Plugin DLL Hijack](knowledge/writeups/misc/htb-touch-kiosk-plugin-hijack.md)
- [Audit de surface passive - pentest reel (Laravel/OpenResty)](knowledge/writeups/misc/pennygroupe-recon-passive.md)
- [External reference: SecBlog APT index + Adobe Reader PDF zero-day report](knowledge/writeups/misc/secblog-apt-adobe-reader-zeroday-notes.md)

### pwn
- [PDF Strikes Again - PyMuPDF 1.28.2 Callout Stack Overflow to ROP](knowledge/writeups/pwn/pdf-strikes-again-pymupdf-callout-rop.md)
- [PWN#002 Vault - PIE + Seccomp Stack Overflow, ORW Chain via Unintended pext Gadget](knowledge/writeups/pwn/pwn002-vault-seccomp-orw-pext-gadget.md)
- [PWN#003 - Custom Notes Allocator UAF to system("/bin/sh")](knowledge/writeups/pwn/pwn003-notes-uaf-fakechunk.md)

### web
- [171.80.2.169 18148](knowledge/writeups/web/171-80-2-169-18148.md)
- [Abuivide](knowledge/writeups/web/abuivide-sqli-union.md)
- [ClearHouse - GraphQL IDOR to Path Traversal to js-yaml v3 toJSON RCE](knowledge/writeups/web/clearhouse-graphql-idor-traversal-jsyaml-tojson-rce.md)
- [HTB Criticalops - Client-Side JWT Signing Secret in Frontend Bundle](knowledge/writeups/web/criticalops-client-side-jwt-secret.md)
- [Bug bounty - cyberc4st.com (plugin Mailster WordPress)](knowledge/writeups/web/cyberc4st-mailster-info-leak.md)
- [Edoulooo](knowledge/writeups/web/edoulooo-race-condition.md)
- [HTB Layover (session bloquee, RCE Yii2/Craft non confirmee)](knowledge/writeups/web/htb-layover-blocked-yii2.md)
- [HTB Reactor](knowledge/writeups/web/htb-reactor-nextjs-rce.md)
- [HTB SmartHire (Medium)](knowledge/writeups/web/htb-smarthire-mlflow-rce.md)
- [HTB Stream (htb-airport.htb)](knowledge/writeups/web/htb-stream-xxe-clickhouse.md)
- [Internal Resource Viewer](knowledge/writeups/web/internal-resource-viewer.md)
- [HTB JinjaCare - SSTI in PDF Certificate Generation (Flask render_template_string)](knowledge/writeups/web/jinjacare-ssti-pdf-certificate.md)
- [php2shell (CVE-2026-109618/109619) - Independent HTTP RCE Reproduction with Worker Pinning](knowledge/writeups/web/php2shell-cve-2026-109618-109619-http-reproduction.md)
- [External reference: PHP2Shell core PHP RCE (CVE-2026-109618 / CVE-2026-109619)](knowledge/writeups/web/php2shell-cve-2026-109618-109619-notes.md)
- [Ping Tool Command Injection](knowledge/writeups/web/ping-command-injection.md)
- [SQLite Boolean Blind SQL Injection](knowledge/writeups/web/sqlite-blind-sql-injection.md)
- [SSRF IP Bypass to LFI to Pickle RCE Chain](knowledge/writeups/web/ssrf-ip-bypass-to-lfi-pickle-chain.md)
- [SSRF Proxy to Internal Host](knowledge/writeups/web/ssrf-proxy-to-internal.md)
- [Web XSS Lab - Reflected and DOM XSS](knowledge/writeups/web/web-xss-lab.md)

## Patterns

### crypto
- [LWE avec secret restreint (binaire) bruteforcable](knowledge/patterns/crypto/adokpo-lwe-esig.md)
- [Oracle de padding PKCS7/AES-CBC exploitable sans cle](knowledge/patterns/crypto/broken-padding-oracle.md)
- [RSA close-prime factorisable par methode de Fermat](knowledge/patterns/crypto/twin-prime-fermat-rsa.md)

### misc
- [Cross-Forest AD Pro Lab Escalation: SQLAgent Proxy RCE to Cred Reuse to RBCD/S4U](knowledge/patterns/misc/ad-cross-forest-sqlagent-rbcd-s4u-chain.md)
- [.NET Plugin DLL Hijack (namespace must match filename)](knowledge/patterns/misc/dotnet-plugin-dll-hijack.md)
- [Double-Direction NTLM Relay via MSSQL xp_dirtree Coercion](knowledge/patterns/misc/double-ntlm-relay-xp-dirtree-mssql-coercion.md)
- [Whitespace steganography -> base64 -> ZIP: chaine misc multi-couches](knowledge/patterns/misc/fafa-whitespace-stego.md)
- [Kiosk / Electron Breakout via Crashed Driver Dialog](knowledge/patterns/misc/kiosk-electron-breakout-crash-dialog.md)
- [Brute-force a small PRNG seed using the known flag prefix](knowledge/patterns/misc/known-prefix-seed-bruteforce.md)
- [Malicious PDF: AcroForm-stashed JSFuck payload with layered decode and covert RSS C2](knowledge/patterns/misc/malicious-pdf-js-obfuscation-c2-pattern.md)
- [Checklist recon passive pre-intrusive (pentest web reel)](knowledge/patterns/misc/pennygroupe-recon-passive.md)
- [World-Writable php-fpm Socket: Raw FastCGI Client Pivot](knowledge/patterns/misc/php-fpm-0666-socket-fastcgi-pivot.md)
- [RDP Password Validity Probe via Negotiation Behavior](knowledge/patterns/misc/rdp-password-probe-via-negotiation.md)

### pwn
- [Custom allocator UAF: double-free without null + safe-linking bypass via known key](knowledge/patterns/pwn/custom-allocator-selflink-fakechunk.md)
- [PyMuPDF Callout Overflow: byte-wise BSS write + PyRun_SimpleString ROP](knowledge/patterns/pwn/pymupdf-callout-overflow-pyrun-rop.md)
- [Seccomp-Restricted Pwn: ORW Chain via Unintended Identity-Copy Gadget](knowledge/patterns/pwn/seccomp-orw-unintended-identity-gadget.md)

### web
- [WordPress REST: CPT generique wp/v2 non protege alors que l'API custom du plugin l'est](knowledge/patterns/web/cyberc4st-mailster-info-leak.md)
- [Race condition TOCTOU sur logique de paiement/solde](knowledge/patterns/web/edoulooo-race-condition.md)
- [Node.js --inspect expose en local = privesc root generique](knowledge/patterns/web/htb-reactor-nextjs-rce.md)
- [MLflow creds par defaut -> RCE pickle -> .pth privesc](knowledge/patterns/web/htb-smarthire-mlflow-rce.md)
- [XXE aveugle sans OOB: exfiltration in-band via pipeline aval](knowledge/patterns/web/htb-stream-xxe-clickhouse.md)
- [js-yaml v3 Tag Blocklist Bypass via Verbatim Tag + toJSON RCE Trigger](knowledge/patterns/web/jsyaml-v3-verbatim-tag-tojson-rce.md)
- [JWT Signing Secret Hardcoded in Frontend Bundle (Client-Side Auth)](knowledge/patterns/web/jwt-secret-in-frontend-bundle.md)
- [Obfuscated assert GET RCE](knowledge/patterns/web/obfuscated-assert-get-rce.md)
- [SSRF to LFI to Localhost RCE](knowledge/patterns/web/ssrf-to-lfi-to-localhost-rce.md)
- [SSTI in Server-Side PDF/Document Generation (Jinja2 self.__init__.__globals__)](knowledge/patterns/web/ssti-pdf-generation-jinja-self-globals.md)
