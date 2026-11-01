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

## Exit Conditions

- No unmatched secrets and no exploitable bind mount → fall back to normal
  category-specific privesc/enumeration (SUID binaries, cron jobs, kernel
  exploits, credential reuse).
