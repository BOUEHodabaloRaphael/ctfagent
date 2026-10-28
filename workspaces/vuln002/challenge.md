---
doc_kind: challenge
id: vuln002
title: "VULN#002"
category: vuln-research
platform: ctfd
platform_id: 32
url: 169.58.126.107:7026
status: new
tags:
  - dhcpv6
  - dnsmasq
attachments:
  - dnsmasq-src.tar.gz
---
# VULN#002

- ID: vuln002
- Category: vuln-research
- Platform: ctfd
- Platform ID: 32
- URL: 169.58.126.107:7026
- Attachments:
  - dnsmasq-src.tar.gz (downloaded to workspaces/vuln002/attachments/, extracted and
    identified as upstream commit c8168e888eb42870e10e6d9d96609d4c3cf2e06d, "v2.93test6-4-gc8168e8";
    see notes.md for full version-ID and vulnerability analysis)

## Description

Acme Gateway's DHCPv6 relay is built on a real, unmodified, open-source DHCP/DNS forwarder, at a real revision.

Connection: nc 169.58.126.107 7026
Attachment: dnsmasq-src.tar.gz (source tarball, real revision — likely dnsmasq, given "DHCP/DNS forwarder")
Platform challenge id: 32
Points: 136 (decaying), 8 solves at time of this check, max_attempts: 3, not yet solved by us, 0 attempts used.

Working hypothesis (by analogy with VULN#001's libexif pattern): this is a "spot the vulnerable version window"
challenge — diff the attached dnsmasq source tarball against upstream dnsmasq git history to find which exact
known CVE / security fix commit is missing from this exact revision, then craft a trigger for that specific bug
against the live DHCPv6 relay service on port 7026.

## Constraints

- id=32, bugpwn.com, 136pts decaying
- max_attempts=3, do not submit without near-certainty
