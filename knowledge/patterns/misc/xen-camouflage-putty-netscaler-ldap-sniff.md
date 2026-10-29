---
doc_kind: pattern
title: "Wordlist kwprocessor pour passphrase keyboard-walk + sniff d'appliance en position MITM"
category: misc
slug: xen-camouflage-putty-netscaler-ldap-sniff
created: 2026-10-29
status: active
tags:
  - putty-crack
  - kwprocessor
  - netscaler
  - ldap-cleartext
  - tcpdump
chain_summary: "Une passphrase de forme keyboard-walk (ex: qwerty-like) cede mieux a une wordlist generee par kwprocessor que par rockyou; une appliance reseau transitant du trafic interne merite un sniff tcpdump systematique."
---
# Wordlist kwprocessor pour passphrase keyboard-walk + sniff d'appliance en position MITM

## Chain Summary

- One-line chain: Une passphrase de forme keyboard-walk (ex: qwerty-like) cede mieux a une wordlist generee par kwprocessor que par rockyou; une appliance reseau transitant du trafic interne merite un sniff tcpdump systematique.
- Typical target shape: Cle privee protegee par passphrase dont le format suggere un pattern clavier; acces shell sur un appliance reseau (proxy, gateway) qui route du trafic d'autres utilisateurs.

## Preconditions

- Cle privee protegee par passphrase dont le format suggere un pattern clavier; acces shell sur un appliance reseau (proxy, gateway) qui route du trafic d'autres utilisateurs.

## Cheap Probes

- Tester john/hashcat avec une wordlist kwprocessor en complement de rockyou sur toute passphrase resistante.

## Telltale Evidence

- La wordlist dediee casse la passphrase alors que rockyou seul echoue.

## Escalation Order

1. Generer une wordlist kwprocessor ciblant les patterns clavier courants.
2. Cracker la passphrase avec cette wordlist.
3. Une fois un shell obtenu sur un appliance reseau, lancer tcpdump pour capturer le trafic transitant.
4. Analyser dans Wireshark pour des credentials/flags en clair.

## Common Mistakes

- Se limiter a rockyou pour une passphrase de forme non-dictionnaire (keyboard walk) sans essayer un generateur specialise.

## Payload Shapes

```text
kwp basechars/full-keyboard-without-shift.base -r kwprocessor/resources/keymaps/en-us.keymap kwprocessor/resources/routes/2-to-16-max-3-direction-changes.route
```

## Related Writeups

- xen-camouflage-putty-netscaler-ldap-sniff

## Skill Impact

- Related skill: pwn-triage: ajouter kwprocessor comme alternative a rockyou pour les passphrases suspectees keyboard-walk.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
