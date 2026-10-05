---
doc_kind: workspace-notes
id: tengu
title: Tengu
category: web
status: new
tags:
  []
---
# Notes

- hypotheses:
- validated findings:
- dead ends:

## Validated findings (facts)

- Entry point 10.13.38.40 is Linux (Ubuntu), SSH OpenSSH 8.9p1 Ubuntu 3ubuntu0.13.
- Full port scan (-p- -sV -T3, no forced min-rate) found exactly one extra port:
  **1880/tcp**, fingerprinted via nmap's 404 probe as an Express.js/Node.js app
  (classic "Cannot GET /nice%20ports%2C/Trinity.txt.bak" nmap-probe response with
  CSP `default-src 'none'`). This matches **TENGU-NODERED** - the lab's Linux
  Node-RED box, and is almost certainly the entry point for this scenario.
- Immediately after the full-port scan, HTTP requests to :1880 hang indefinitely
  (TCP handshake OK, no data ever returned) - same cross-lab pattern seen on
  Alchemy (see workspaces/alchemy/notes.md). Ruled out local cause (conntrack
  healthy). Treating as HTB's scan-triggered cooldown on the target's HTTP service.

## Hypotheses

- 10.13.38.40 = TENGU-NODERED, exposing the Node-RED web UI/editor on 1880 -
  likely entry vector is an exposed/unauthenticated Node-RED editor (known
  pattern: Function node arbitrary code execution) or an app built on top of it.
- TENGU-SQL and TENGU-DC are presumably on an internal segment only reachable
  after pivoting from TENGU-NODERED (matches lab description: "pivoting into
  internal networks").

## Next step

Request a lab redeploy for TENGU-NODERED (same fix that worked for Alchemy's
stuck service) instead of waiting out the cooldown, then retry a single light
curl/browser check on :1880 before doing anything else.
