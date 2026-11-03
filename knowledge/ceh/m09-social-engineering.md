# CEHv13 Module 09 — Social Engineering (technique synthesis)

Source: `CEHv13 - Module 09 - Social Engineering hide01.ir.pdf` (86 pages, scanned → OCR).

## 1. Psychological levers (pretext design)

Exploit one of: authority, fear, scarcity, urgency, familiarity/liking, trust, greed, helpfulness,
curiosity, moral obligation. These justify every pretext below — pick the lever before the story.

## 2. Attack lifecycle

Research (OSINT/dumpster diving/company site/employee details) → select target (receptionist,
help desk, IT support, system admin, third-party vendor, disgruntled employee) → build
relationship/pretext → exploit (extract info or access) → cover tracks.

## 3. Human-based techniques

| Technique | Mechanism |
|---|---|
| Impersonation | pose as: legit end-user, important user, tech-support agent, internal employee/client/vendor, repairman, third-party-authorized person, trusted authority. Classic: call help desk claiming forgotten password/urgent access need, abuse their over-helpfulness |
| Vishing | voice/VoIP phishing — spoof caller ID, pre-recorded "bank" prompts, trick victim into reading out OTP/card data over the phone |
| Eavesdropping / shoulder surfing | observe PIN/password entry or overhear conversations in person |
| Dumpster diving | retrieve policy manuals, org charts, calendars/logs, discarded printouts — directly maps to recon phase |
| Reverse social engineering | attacker creates the problem (e.g. sabotage something), then offers to "fix" it, gaining trusted access when the victim calls them |
| Piggybacking | tailgate into a secured area *with* consent of an authorized person (they hold the door) |
| Tailgating | enter a secured area *without* consent, slipping in behind someone badge-swiping |
| Diversion theft | reroute a delivery/shipment to a different address/address under attacker control |
| Honey trap | romantic/sexual pretext to extract info or access |
| Baiting / bait-and-switch | leave infected USB drives, or offer a "free" download/ad swapped for malware |
| Quid pro quo | offer a service/favor in exchange for credentials or access |
| Elicitation | structured conversation designed to extract info without the target noticing they're being pumped |
| Deepfake video creation | synthesize a trusted exec's face/voice to authorize a fraudulent transfer or request |

## 4. Computer-based techniques

- **Phishing** — spoofed email mimicking a trusted brand, link to a cloned login page.
  Types: **spear phishing** (targeted, personalized), **pharming** ("phishing without a lure" —
  DNS cache poisoning or hosts-file modification redirects even a correctly-typed URL),
  **clone phishing** (near-identical resend of a legit previous email with a swapped malicious
  link), **e-wallet phishing** (targets crypto/e-wallet users), **consent phishing** (OAuth
  consent-screen abuse — victim grants a malicious app real API/account access, no password
  stolen, no credential-based detection triggers), **tabnabbing** (inactive tab silently rewritten
  to a phishing page via JS while the user is away from it).
- **Spimming** — spam over IM.
- **Scareware** — fake "your system is infected" popups pushing rogue AV/payment.
- **SMiShing** — SMS phishing, often fake delivery/bank alerts with a shortened malicious link.
- **QR code phishing ("quishing")** — malicious QR swapped in on posters/menus/parking meters;
  tools: QR Code Generator, QR Code KIT (used defensively to spot/compare legit codes too).
- **AI-assisted phishing**: use an LLM to (1) draft a convincing phishing email body, (2) generate
  a realistic sender persona/sounding domain, (3) clone a known contact's writing style for BEC.

## 5. Tools cited

| Tool | Role | Source |
|---|---|---|
| Social-Engineer Toolkit (SET) | Python framework, categorizes attacks by vector (email/web/USB); menu-driven credential harvester + payload delivery | trustedsec.com |
| ShellPhish | Credential phishing templates for IG/FB/Twitter/LinkedIn, logs victim IP/browser/hostname/geolocation | github.com |
| Gophish | Phishing campaign management (also used defensively for awareness testing) | getgophish.com |
| King Phisher | Phishing campaign toolkit | github.com |
| Zphisher, BLACKEYE, Dark-Phish, SocialFish | Credential-harvesting page generators (Termux/Linux) | github.com |
| Modlishka | Reverse-proxy phishing (bypasses some 2FA by relaying live sessions) | github.com |
| Trape | People/session tracking via injected tracking links | github.com |
| LUCY SECURITY | Phishing simulation platform | lucysecurity.com |
| Deepfakes Web, Vidnoz, Hoodem, Synthesia | Deepfake video/voice generation | respective sites |

## 6. Insider / physical vectors worth probing in an engagement

- Target roles: receptionists (org chart/visitor info), help desk (password resets — the
  classic easy win), system admins (highest access, worth the longest pretext), disgruntled
  employees (willing informants/insiders without any technical attack needed).
- Identity theft as an access vector: steal/clone an employee ID or badge to gain *physical*
  building access (impersonation escalated to a credential level, not just info gathering).
- Physical recon signals that enable the above: company swag/uniforms visible in public,
  job postings revealing internal tech stack, social media oversharing by staff, improperly
  shredded documents in dumpsters.

## 7. Countermeasures (condensed)

- **Password policy**: periodic rotation, block on repeated failed attempts, 8+ chars with mixed
  classes, no sharing/reuse/writing down, never given over phone/email/SMS, lock screen on
  walk-away.
- **Physical policy**: ID cards/uniforms, visitor escort, access-area restriction, document
  shredding, security personnel, badge-reader tailgating awareness.
- **Program-level**: mandatory security-awareness training with signed acknowledgment, defined
  consequences for policy violation, background checks + clean offboarding/termination process,
  least-privilege access, 2FA everywhere, documented change management, timely patching,
  periodic simulated social-engineering campaigns + gap analysis + remediation tracking.
- **Phishing-email tells to train staff on**: sender display-name vs actual domain mismatch,
  generic greeting ("Dear user"), urgency/fear framing, mismatched hover-link vs displayed URL,
  unexpected/odd-format attachments, missing full signature, requests for PII/credentials,
  too-good offers (lottery/prize/job).
- **Anti-phishing tooling**: Netcraft Toolbar (community-reported phishing DB), PhishTank
  (open collaborative phishing clearinghouse + API), VirusTotal / e.Veritas for link/attachment
  triage before clicking.

## 8. Pitfalls

- Pharming and consent-phishing both bypass the classic "check the URL carefully" advice — DNS/
  hosts-level redirection and OAuth consent abuse don't show a spoofed domain at all.
- Reverse social engineering is slow to set up (attacker must first manufacture the "problem")
  but is the hardest variant to detect, since the victim initiates contact with the attacker.
- A social-engineering engagement is as much a physical-security test as a phishing test —
  don't stop at email; tailgating/piggybacking and dumpster diving are often the faster win.
