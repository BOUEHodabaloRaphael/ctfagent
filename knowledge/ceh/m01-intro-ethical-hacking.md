# CEHv13 Module 01 — Introduction to Ethical Hacking (concept synthesis)

Source: `CEHv13 - Module 01 - Introduction to Ethical Hacking hide01.ir.pdf` (137 pages, scanned
→ OCR). Mostly exam-theory; keeping only what's actionable for pentest framing/reporting.

## 1. Five hacking phases (the actual probe order used across every other module)

1. **Reconnaissance** — passive (OSINT, no target interaction) vs active (direct interaction,
   e.g. port probing). Treated as the prep phase for everything downstream.
2. **Scanning** — logical extension of active recon; deeper probing (open ports, services,
   live hosts) — some treat it as a sub-phase of active recon rather than separate.
3. **Gaining access** — exploit to get OS/app-level control, usually starting with a low-priv
   account (privilege escalation happens later — full depth in Module 06).
4. **Maintaining access** — backdoors/rootkits/trojans to retain access across reboots/patches.
5. **Clearing tracks** — remove logs/evidence (full technique depth in Module 06).

## 2. Cyber Kill Chain (7 phases — intelligence-driven defense framing, maps directly onto the
above 5 but splits weaponization/delivery/C2 out explicitly — useful for report narrative)

| Phase | Adversary activity |
|---|---|
| Reconnaissance | OSINT, social engineering, Whois/DNS/network footprinting, port/service scan |
| Weaponization | pick/build payload (malware + exploit + backdoor) tailored to recon findings |
| Delivery | phishing email, malicious USB, watering-hole site, vulnerable web app |
| Exploitation | trigger the payload against the actual OS/app/server vulnerability |
| Installation | drop persistent backdoor, start spreading to other hosts, hide from AV/firewall |
| Command & Control | 2-way channel to attacker infra (web/email/DNS as cover channel), privesc |
| Actions on Objectives | exfil, disruption, destruction, or pivot to launch further attacks |

## 3. MITRE ATT&CK (Enterprise) — 14 tactics, maps to kill-chain's later stages at finer grain

Reconnaissance → Resource Development → Initial Access → Execution → Persistence → Privilege
Escalation → Defense Evasion → Credential Access → Discovery → Lateral Movement → Collection →
Command and Control → Exfiltration → Impact.

Use cases worth citing in a report: compare adversary TTPs against a common reference, identify
detection/mitigation coverage gaps per tactic, link specific mitigations to specific techniques
rather than vague "improve security" recommendations.

## 4. Diamond Model of Intrusion Analysis

Four meta-features of every intrusion event, useful as a reporting/triage template:
**Adversary** (who) — **Victim** (where/what was exploited) — **Capability** (how: malware,
exploit, tool used) — **Infrastructure** (what the adversary used to reach the victim: C2
servers, compromised sites, email infra). Extended model adds socio-political motive +
technology context. Practical use: when writing up a finding, filling these four fields forces
a complete causal chain instead of just "found XSS here."

## 5. Attacker classes (useful for threat-modeling / report framing, not pure trivia)

| Class | Notes |
|---|---|
| Script kiddie | runs others' tools/scripts without deep understanding — high volume, low sophistication |
| Gray hat | switches between offensive and defensive work; may disclose vulns without full authorization |
| Hacktivist | ideologically motivated — DDoS, defacement, leaking confidential data to make a point |
| State-sponsored | well-resourced, skilled, government-directed — long-term, stealthy |
| Cyber terrorist | motivated by ideology/religion/politics, aims for fear/disruption at scale |
| Suicide hacker | no concern for getting caught/punished — targets critical infra, high-risk/high-impact ops |
| Insider threat | abuses *already-granted* privileged access — no exploit needed, often the fastest path in; commonly a disgruntled or just-terminated employee |

## 6. Attack surface categories to check (TTP-level framing)

- **OS-level attacks**: unpatched OS vulnerabilities, default configs, service misconfig.
- **Application-level attacks**: input validation gaps, business-logic flaws, auth bugs — same
  territory covered in depth by the web-app/web-server/SQLi modules.
- **Shrink-wrap code attacks**: exploiting default/unmodified library or off-the-shelf component
  code shipped with an app — check for default settings/sample scripts left in place.
- **Misconfiguration attacks**: default credentials, debug endpoints left on, excessive
  permissions — the single most common finding category across every module in this course.
- Insider attacks: privileged-access abuse, bypasses the entire external kill chain.

## 7. Information security controls worth keeping as checklist language for reports

- **Defense-in-depth**: layered controls so no single control failure = full compromise —
  frame remediation recommendations in terms of which layer was missing, not just "add a WAF."
  - Rationale cited in the module for actually doing penetration testing: an org wants (1) to
    prevent attackers from gaining access in the first place, and (2) to get real evidence of
    what a determined attacker *could* reach, obtained by actually attempting the intrusion —
    not just by combining vuln-scanner output and assumptions.
- **Risk management**: identify → assess → treat → monitor — ties directly to how findings
  should be prioritized in a report (likelihood × impact, not just CVSS alone).
- **Cyber threat intelligence**: gather + analyze threat data into actionable insight — in
  practice: check what TTPs/IOCs are already known for the client's sector before testing blind.
- **Threat modeling**: identify assets, enumerate threats per asset, rank by risk, *then* test —
  this is the "pick targets before firing" discipline that should precede any engagement.
- **Incident management process**: preparation → identification → containment → eradication →
  recovery → lessons learned — useful vocabulary when writing the "detection & response" section
  of a pentest report.

## 8. Pitfalls / notes

- Scanning vs active recon is a fuzzy line in the source material itself — don't over-index on
  the taxonomy, the *order* (recon → scan → exploit → persist → cover tracks) is what matters.
- Insider threats bypass the entire kill-chain/ATT&CK framing built around external intrusion —
  any threat model that only covers external vectors is incomplete by design.
- Module explicitly notes ethical hackers should only run DoS-style tests with *prior written
  agreement* — scope/ROE boundaries matter even when a technique is technically available.
