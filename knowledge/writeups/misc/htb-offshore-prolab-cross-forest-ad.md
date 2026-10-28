---
doc_kind: writeup
title: "HTB Pro Lab Offshore - Cross-Forest AD Compromise (22/38 flags)"
category: misc
slug: htb-offshore-prolab-cross-forest-ad
created: 2026-10-25
status: solved
tags:
  - active-directory
  - pro-lab
  - dcsync
  - acl-abuse
  - extrasids
  - golden-ticket
  - nopac
  - ftp-anonymous
  - ssh-pivot
source: "HTB Pro Lab - Offshore (US Offshore 1)"
target: "NIX01 10.10.110.123 / CORP.LOCAL / DEV.ADMIN.OFFSHORE.COM / ADMIN.OFFSHORE.COM / LAB.OFFSHORE.LOCAL"
---
# HTB Pro Lab Offshore - Cross-Forest AD Compromise (22/38 flags)

## Challenge Summary

- Source: HTB Pro Lab - Offshore (US Offshore 1), FR writeup by KevineCharles, 20/10/2026
- Target: Entry point NIX01 (10.10.110.123 / 172.16.1.23); four AD zones: CORP.LOCAL (172.16.1.0/24), DEV.ADMIN.OFFSHORE.COM (172.16.2.0/24), ADMIN.OFFSHORE.COM (172.16.3.0/24), and a separate forest LAB.OFFSHORE.LOCAL (172.16.1.0/24, different VLAN)
- Goal: Compromise as much of the multi-domain/multi-forest lab as possible and collect flags (22/38 flags captured across 8 hosts)

## Initial Signals

- Entry point: SSH private key for NIX01 root (`/tmp/nix01_root_id_rsa`) — direct unauthenticated-looking pivot box with a double NIC into CORP.LOCAL.
- Visible hints: NIX01 bridges the external lab network and the internal 172.16.1.0/24 CORP segment — classic Pro Lab "jump box" pattern.
- First confirming probe: SSH as root to NIX01, then enumerate CORP.LOCAL via chisel/proxychains tunnels (netexec/impacket/BloodHound).

## Exploit Chain

1. **Pivot vers NIX01** via clé SSH root — accès direct à 172.16.1.0/24 (CORP.LOCAL).
2. **Énumération CORP.LOCAL** (MS01, DC01, WEB-WIN01, SQL01, FS01, WS02, WSADM) via netexec/BloodHound par proxychains/chisel.
3. **Compromission CORP — DCSync** via le compte de service `svc_opmanager` / `Manage my engine 123!` (credentials faibles trouvées en énumération) → droits DCSync sur `CORP Admin` et `krbtgt` (NTLM hashes récupérés).
4. **Accès DEV.ADMIN.OFFSHORE.COM** via abus d'ACL découvert avec BloodHound (chemin non détaillé dans le PDF au-delà du résultat : accès obtenu à DC02/WS03).
5. **Escalade vers ADMIN.OFFSHORE.COM** via abus **child → parent trust (ExtraSids)** + **Golden Ticket** forgé avec Rubeus (en utilisant le hash krbtgt de CORP pour franchir la confiance parent/enfant) → accès DC03/WS04.
6. **Pivot DC02 → WS04** via `netsh portproxy` (contournement de restriction réseau entre segments).
7. **Forêt séparée LAB.OFFSHORE.LOCAL** : identifiants `joe:Dev0ftheyear!` valides, puis **noPac (CVE-2021-42278 / CVE-2021-42287)** sur DC0 (172.16.1.200) pour obtenir un accès privilégié sur ce DC indépendant.
8. **JOE-LPTP** : FTP anonyme (révèle des fichiers sensibles / un flag) puis WinRM avec les creds `joe`/`joe_adm` (adminCount=True) récupérées dans LAB.

## Key Evidence

- `svc_opmanager` credentials (`Manage my engine 123!`) donnaient directement les droits DCSync sur CORP.LOCAL — mot de passe faible/prévisible trouvé en énumération classique (pas de technique exotique).
- `krbtgt` NTLM hash de CORP (`cba2ed22077aa56ae957bcf43a8d82f8`) a permis de forger un Golden Ticket, puis d'utiliser l'attribut **SIDHistory / ExtraSids** pour traverser la confiance child→parent sans nouvelle compromission du domaine ADMIN.
- Relation **FOREST_TRANSITIVE** entre les domaines/forêts du lab (voir pattern dédié) — la confiance d'authentification n'implique pas automatiquement l'administration, mais permet la réutilisation d'identifiants et l'abus de délégation.
- `noPac` fonctionnel sur DC0 de LAB.OFFSHORE.LOCAL confirme une mauvaise gestion de la création de comptes machine (`sAMAccountName` spoofing + certificat PKINIT/Kerberos classique CVE-2021-42278/42287).

## Dead Ends

- Rien d'explicitement documenté comme échec dans ce writeup condensé (c'est un résumé d'engagement, pas un journal pas-à-pas) — 16/38 flags du lab restent non trouvés, suggérant des chemins d'attaque supplémentaires (probablement sur FS01, SQL01, WS02, WSADM) non explorés ou non documentés ici.

## Payloads And Commands

```bash
# Tunnels SSH/chisel depuis NIX01 vers les segments internes
# Forwards observés :
# 127.0.0.1:30088 (KRB), 30389 (LDAP), 30445/31445 (SMB LAB),
# 31585/32585 (WinRM JOE-LPTP), 44030 (MS01 SMB)

# Outils utilisés : netexec/nxc, impacket, noPac, proxychains4, chisel, BloodHound, Rubeus

# Exemple logique Golden Ticket + ExtraSids (reconstruit, pas verbatim du PDF) :
# Rubeus.exe golden /rc4:<krbtgt_hash> /domain:corp.local /sid:<CORP_SID> \
#   /sids:<ADMIN.OFFSHORE.COM_Enterprise_Admins_SID> /user:Administrator /ptt
```

## Flag / Outcome

- 22/38 flags capturés, répartis sur WSADM, WS03 (DEV), JOE-LPTP FTP/SSH (LAB), NIX01, SQL01, WEB-WIN01, FS01, MS01, MS01 (MS01), DC02 (DEV), DC01, DC03 (ADMIN), WS04 (ADMIN).
- Exemples de flags : `OFFSHORE{4t_y0ur_5erv1ce}` (WSADM), `OFFSHORE{l@zy_adm1ns_ru1n_th3_p4rty}` (DC02/DEV), `OFFSHORE{w@tch_th3_for3st_burn}` (WS04/ADMIN), `OFFSHORE{r3pl1cation_@ll0w_l1st}` (DC01).

## Reusable Lessons

- Un Pro Lab multi-forêt/multi-domaine suit presque toujours le même squelette : (1) pivot via une machine double-NIC, (2) DCSync via des creds de service faibles, (3) abus d'ACL/délégation pour traverser domaines enfants, (4) ExtraSids/Golden Ticket pour sauter une confiance de forêt child→parent, (5) WMI/DCOM ou portproxy quand SMB est filtré entre segments, (6) vérifier systématiquement noPac si une forêt séparée gère la création de comptes machine de façon permissive.
- FTP anonyme et WinRM restent des vecteurs d'accès initial très communs sur les machines "fin de chaîne" (ici JOE-LPTP) dans les labs HTB — toujours les tester même après une longue chaîne AD.
- Documenter précisément les SID/Enterprise Admins SID de chaque forêt avant de forger un ticket ExtraSids — l'attaque échoue silencieusement si le SID cible est incorrect.

## Pattern Candidates

- New pattern created: `knowledge/patterns/misc/ad-cross-forest-sqlagent-rbcd-s4u-chain.md` (chaîne générique cross-forest observée aussi dans Ascension : abus de confiance + élévation + pivot quand SMB filtré)
