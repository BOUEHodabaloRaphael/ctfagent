---
doc_kind: writeup
title: "BTF — Blue Team Fundamentals (CyberWarFare Labs)"
category: forensics
slug: btf-cwl-dfir-soc-exercises
created: 2026-10-29
status: solved
tags:
  - dfir
  - siem
  - wazuh
  - volatility3
  - pcap
  - soc-quiz
source: "CyberWarFare Labs CyberRange (certification BTF)"
target: "Wazuh/Kibana + Wireshark + Volatility3 (walkthroughs guides)"
---
# BTF — Blue Team Fundamentals (CyberWarFare Labs)

## Challenge Summary

- Source: CyberWarFare Labs CyberRange (certification BTF)
- Target: Wazuh/Kibana + Wireshark + Volatility3 (walkthroughs guides)
- Goal: Certification blue-team avec 5 scenarios DFIR/SOC guides (SQLi, XSS, RFI, C2 reseau, memory forensics), quiz final a 100% requis avec feedback global uniquement.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Decodeur Wazuh web-accesslog sur access.log Apache, filtre data.url pour detecter motifs SQLi (UNION SELECT) avec code HTTP 200 -> IP source via data.srcip.
2. Meme pivot sur /xss_r/ : detection payload onerror=alert(1);document.cookie en code 200.
3. Detection RFI/upload : POST sur /vulnerabilities/upload/, correlation PCAP montrant GET du fichier depose rev.php, confirmation canal reverse shell port 9001.
4. Analyse external.pcapng : filtre tcp.dstport==4444, identification port source ephemere, confirmation canal C2 bidirectionnel.
5. Analyse memoire Volatility3 (pslist/cmdline/netstat) sur suspected.raw : identification processus shell.exe, dump soumis a VirusTotal, netstat confirme C2 etabli.
6. Quiz final 10 questions/100% requis, feedback global seul -> correction ciblee entre tentatives.

## Key Evidence

- "Top values of data.url: /prod/vulnerabilities/sqli/?id=%27+UNION+SELECT..."; PCAP "GET /prod/hackable/uploads/rev.php"; Volatility "TCPv4 ...:49749 -> ...:4444 ESTABLISHED PID 7396 shell.exe"; score final 100% (10/10).

## Dead Ends

- Le 'count' demande dans un quiz DFIR peut etre un sous-total specifique affiche dans une vue, pas le total brut filtre - premiere tentative faussee par cette confusion.

## Payloads And Commands

```text
Requetes SIEM (Kibana Discover) + filtres Wireshark + commandes Volatility3.
```

## Flag / Outcome

- Certification validee a 100%.

## Reusable Lessons

- Methodologie generique DFIR web (decoder+index Wazuh -> filtre URL/code HTTP -> pivot IP source) reutilisable pour toute investigation SOC log-based.

## Pattern Candidates

- Nouveau pattern: wazuh-siem-pivot-dfir-methodology
