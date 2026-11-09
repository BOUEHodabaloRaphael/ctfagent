# Post-Shell Pivot Checklist

Use this once you have any code execution or shell — from an SSTI/RCE chain, a
forged token, or a pwn exploit. It is a short, generic checklist, not a
category skill: the detailed reasoning lives in `knowledge/patterns/`.

Run both checks before reaching for heavier escalation techniques.

## 1. Leaked secret with no obvious consumer?

If a secret leaked earlier (env var, config, source) doesn't match the main
app's own auth scheme, it may belong to an internal-only automation/CI
platform (n8n, Node-RED, Jenkins, Airflow) bound to localhost — these often
run as root and expose a code-execution primitive (Webhook/Execute Command,
freestyle job, DAG task) through their own API.

```bash
ss -lntp 2>/dev/null || netstat -lntp 2>/dev/null
curl -s http://127.0.0.1:<port>/        # fingerprint whatever is listening
```

Full escalation order, probes, and payload shapes:
`knowledge/patterns/misc/internal-automation-api-key-rce-as-root.md`

## 2. Landed inside a container?

Check for host bind mounts before trying kernel exploits or heavier
container-breakout techniques. A mis-scoped bind mount (e.g. container
`/root` mapped to a host user's home dir, no `nosuid`) can turn root-in-
container directly into root-on-host via a planted setuid binary.

```bash
awk '$8 !~ /^(proc|sysfs|tmpfs|devpts|mqueue|cgroup2)$/ {print "target="$5, "root="$4, "fs="$9}' /proc/1/mountinfo
```

Full escalation order, probes, and payload shapes:
`knowledge/patterns/misc/container-bindmount-setuid-escape.md`

## 3. Domain-joined box, or AD-adjacent (boot2root)?

Signals: `klist`/`net config workstation` works, `/etc/krb5.conf` present,
`hostname -d`/`dnsdomainname` returns something, an LDAP/Kerberos/SMB port
(88/389/445/636) is reachable from this shell, or the challenge flavor text
mentions a domain. Before improvising an AD attack path by hand, run
`ctf-file-hunter`/`file-hunter` first (see
[`ctf-file-hunter-sensitive-file-scanner`](../../../../knowledge/patterns/misc/ctf-file-hunter-sensitive-file-scanner.md))
to surface any stray creds/keytabs, then consult the imported AD playbooks —
this is where repeated boot2root blockers (ASREP-roast → ACL abuse → ADCS
ESC1, DCSync vs a Samba DC, delegation/RBCD) have their methodology and
exact tool commands:

- `knowledge/external/claude-ad/skills/ad-methodology/SKILL.md` — phase order
  (enum → collection → exploitation → post), start here.
- `knowledge/external/claude-ad/skills/ad-environment-constraints/SKILL.md` —
  check this **before** assuming a technique is blocked: NTLM disabled,
  AES-only Kerberos, LDAP channel binding, FQDN-vs-short-SPN mismatches have
  all caused false "dead ends" in past sessions.
- `knowledge/external/claude-ad/skills/kerberos-attacks/SKILL.md`,
  `knowledge/external/claude-ad/skills/adcs-attacks/SKILL.md` (ESC1-ESC17,
  exact `certipy` commands), `knowledge/external/claude-ad/skills/acl-abuse/SKILL.md`,
  `knowledge/external/claude-ad/skills/coercion-ntlm-relay/SKILL.md`.
- `knowledge/external/claude-red/privesc/` — detailed Linux/Windows privesc
  if the box turns out not to be domain-joined after all.
- `knowledge/external/claude-red/post-exploitation/` — lateral
  movement/persistence/exfiltration once a foothold is confirmed.
- `knowledge/external/hack-skills/tunneling-and-pivoting/SKILL.md` — pivot
  through this box to reach an AD segment that isn't directly routable.
- `knowledge/external/hack-skills/container-escape-techniques/SKILL.md`,
  `knowledge/external/hack-skills/kubernetes-pentesting/SKILL.md` — if the
  box is a container/K8s node instead of a bare domain member.

If an impacket tool against a Samba-backed DC gives a nonsensical error
(e.g. `DRSR SessionError: code 0x0 ERROR_SUCCESS` from `secretsdump
-just-dc`), that has been a real impacket↔Samba DRSUAPI protocol
incompatibility before, not a rights issue — try `-k`/Kerberos auth instead
of NTLM, or a lower DRS protocol version, before concluding DCSync is
blocked by permissions.

## Exit Conditions

- No unmatched secrets and no exploitable bind mount → fall back to normal
  category-specific privesc/enumeration (SUID binaries, cron jobs, kernel
  exploits, credential reuse).
- Domain-joined/AD-adjacent → work through section 3 above before
  improvising; it already encodes the exact pitfalls that blocked past
  sessions.
