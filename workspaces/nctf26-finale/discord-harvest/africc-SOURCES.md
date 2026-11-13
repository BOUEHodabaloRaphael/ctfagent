# AFRICC (guild 947089743643037757) — harvest 2026-11-13

African ICC team server. HIGH relevance: it has **real attack-defense practice channels**
(finale = A&D), plus jeopardy category channels and a `resources` channel.

## A&D practice channels (DEEP-READ CANDIDATES — exploit scripts pasted inline)
- `ad-2025-dry-run`, `ad-2025-dry-run-attack`, `ad-2025-dry-run-defend`
- `enowars-9-*` (services seen: `timetype`, `parceroTV`)
- `zerodays-09-08-2025`, `zero-days-21-03-2026`
Concrete A&D artifact seen (ad-2025-dry-run, ! Ax0lotl [OMA], 18/10/2025): a flag
harvest+submit loop:
    import requests, re
    ips = [f"10.3.{i}.2" for i in range(2, 9)]   # per-team target range
    submit_u... (mass exploit across team IPs, auto-submit flags)
=> canonical A&D exploit-loop template. Worth extracting in full for finale tooling.
Also noted: an ImageMagick exploit (jeopardy/crypto chat, 24/10/2025).

## Public writeup/challenge links (agent: fetch + analyze)
- github.com/MemeMasterHacker/vaultic-mememaster — "Vaultic" reverse writeup (leak via
  vault.png in git commit history).
- github.com/UMD-CSEC/UMDCTF-2024-Challenges — full challenge repo.
- github.com/teambi0s/bi0sCTF/tree/main/2022 — full challenge sources.
- UMDCTF 2025 writeup winners:
  - github.com/Lobsterge/CTF-Writeups/tree/main/UMDCTF%202025/literally-1985  (pwn)
  - k3sero.github.io/posts/Gambling2-UMDCTF2025/  (pwn)
  - starglow.net/blog/ctf/prime-sponsorship/  (crypto)
  - booming-lifeboat-071.notion.site/UMDCTF-2025-... (web, "Steve Le Poisson")
  - adrianjunge.de/ctf/umdctf/A%20Minecraft%20Movie  (web)
  - hackmd.io/@aplet123/SJuyjwVlxl  (rev, craziest x86 instructions)

## Searches run: "github" (7 res), "exploit" (21 res). Channels: pwn/web/crypto/forensics/rev/hardware/blue-team exist.
