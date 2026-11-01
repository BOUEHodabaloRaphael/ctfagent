---
doc_kind: pattern
title: "Leaked secret unlocks internal-only automation platform (n8n/Jenkins/Airflow) RCE-as-root"
category: misc
slug: internal-automation-api-key-rce-as-root
created: 2026-11-01
status: active
tags:
  - n8n
  - internal-api
  - leaked-api-key
  - privesc
  - automation-platform-abuse
  - webhook-rce
chain_summary: "A secret leaked from the target app (API key, token) often doubles as the auth key for an internal-only automation platform (n8n, Jenkins, Airflow, internal APIs) bound to localhost; authenticate to its API and create a temporary Webhook -> Execute Command (or equivalent) workflow/job, which frequently runs as root inside that service's container/host, giving code execution as root without any further exploit."
---
# Leaked secret unlocks internal-only automation platform (n8n/Jenkins/Airflow) RCE-as-root

## Chain Summary

- One-line chain: A secret leaked from the target app (API key, token) often doubles as the auth key for an internal-only automation platform (n8n, Jenkins, Airflow, internal APIs) bound to localhost; authenticate to its API and create a temporary Webhook -> Execute Command (or equivalent) workflow/job, which frequently runs as root inside that service's container/host, giving code execution as root without any further exploit.
- Typical target shape: a web/pwn/misc target where a prior step (SSTI/LFI env leak, exposed `.env`, config file read, verbose error message, source leak) hands you a token/key named something like `*_API_KEY`, `*_TOKEN`, `*_SECRET` with no obvious consumer visible in the main app's own API surface — check whether it's actually meant for a *different*, internal-only service running alongside the app (low-code/workflow automation like n8n, CI like Jenkins, orchestration like Airflow, or a bespoke internal admin API), usually bound to `127.0.0.1`/localhost and only reachable once you already have some code execution or SSRF primitive on the host.

## Preconditions

- You have at least one of: a shell on the host/container, an SSRF primitive that can reach localhost ports, or a reverse-proxied path that forwards to the internal service.
- A leaked secret whose name/shape suggests it's an API key/token for automation tooling rather than the main app's own session/JWT secret.
- The internal service exposes (or can be made to expose, via its own API) a code-execution-shaped feature: run a script, execute a shell command, trigger a build/job, run a workflow node.

## Cheap Probes

- From a shell: `netstat -lntp` / `ss -lntp` to find localhost-only listening ports, then `curl` each with no auth to see what it is (version banners, default login pages, `/api/v1/...` JSON errors are all informative).
- Try the leaked secret as a bearer token / custom header against the discovered service's REST API — n8n uses `X-N8N-API-KEY`, Jenkins uses API tokens via basic auth, Airflow has its own REST auth scheme; check that service's docs/fingerprint for the exact header/scheme.
- A successful authenticated `GET` against a listing endpoint (e.g. `/api/v1/workflows`, `/api/json`, `/api/v1/dags`) that returns real data (not a 401/403) confirms the key is valid for that service.

## Escalation Order

1. Enumerate localhost-only services from any code-execution foothold.
2. Fingerprint each (banner, default paths, error pages) to identify the product and its API auth scheme.
3. Try the leaked secret against that scheme; confirm with a read-only authenticated call.
4. Use the service's own API to create the smallest possible code-execution primitive it offers: for n8n, POST a workflow JSON with a `Webhook` trigger node wired to an `Execute Command` node, then activate it and hit the webhook URL; for Jenkins, create/trigger a freestyle job or script console call; for Airflow, trigger a DAG run with a bash/python operator.
5. Check the privilege level the execution happens at — these platforms are frequently run as root (or a highly privileged service account) inside their own container/host even when the main web app runs unprivileged, so this step alone can be a full privesc, not just lateral movement.
6. Once code execution is confirmed, immediately use it to enumerate further pivot opportunities (other mounted volumes, other reachable internal services, `/proc/1/mountinfo` for container bind mounts — see `container-bindmount-setuid-escape`), then clean up: deactivate/delete any temporary workflow/job you created.

## Common Mistakes

- Dismissing a leaked token as useless because it doesn't work against the main app's own API — always check whether it's scoped to a different, adjacent internal service instead of discarding it.
- Not checking the privilege level the internal service runs at before treating this as merely "lateral movement" — it is very often the actual privesc-to-root step, especially for workflow/CI automation platforms that commonly run as root for convenience.
- Leaving the created workflow/job active after use — always deactivate and delete temporary automation artifacts as part of cleanup, since they're a persistent backdoor if left in place.

## Payload Shapes

```bash
# n8n: minimal Webhook -> Execute Command workflow
curl -sS -H "X-N8N-API-KEY: $KEY" -X POST --data-binary @- \
  http://127.0.0.1:5678/api/v1/workflows <<'JSON'
{
  "name": "diag",
  "nodes": [
    {"parameters": {"path": "diag", "httpMethod": "GET"}, "id": "wh",
     "name": "Webhook", "type": "n8n-nodes-base.webhook", "typeVersion": 2,
     "position": [200, 300], "webhookId": "diag"},
    {"parameters": {"command": "id; hostname; cat /proc/1/mountinfo"}, "id": "exec",
     "name": "Execute Command", "type": "n8n-nodes-base.executeCommand",
     "typeVersion": 1, "position": [420, 300]}
  ],
  "connections": {"Webhook": {"main": [[{"node": "Execute Command", "type": "main", "index": 0}]]}},
  "settings": {"executionOrder": "v1"}
}
JSON
curl -sS -X POST -H "X-N8N-API-KEY: $KEY" "http://127.0.0.1:5678/api/v1/workflows/$WID/activate"
curl -sS http://127.0.0.1:5678/webhook/diag
```

## Related Writeups

- `knowledge/writeups/web/htb-takeoff-ssti-hmac-forge-n8n-bindmount.md`
- `knowledge/writeups/web/tengu-nodered-rce-root.md` (sibling: Node-RED exposed without auth at all, same "low-code automation = RCE primitive" shape)

## Skill Impact

- Related skill: `web-triage` / `pwn-triage` (add a "leaked secret -> check for internal automation platform" step after any secret-leak primitive, before assuming the secret is dead-ended)
- Rule to add or update: whenever a secret is leaked and doesn't match the main app's own auth scheme, actively scan localhost ports for internal automation/orchestration tooling (n8n, Node-RED, Jenkins, Airflow) and try the secret there — primed for reuse during NCTF26.
