---
doc_kind: pattern
title: "Cheatsheet DFIR multi-plateformes — macOS, Android, Docker, AWS CloudTrail"
category: forensics
slug: cross-platform-dfir-cheatsheet
created: 2026-10-30
status: active
tags:
  - legacy-memory-migration
  - nctf26-prep
  - cross
chain_summary: "Localisations d'artefacts standards par plateforme: mbox macOS, History SQLite (WebKit epoch), docker history pour recouvrer un Dockerfile, CloudTrail JSON pour une intrusion IAM/EC2."
---
# Cheatsheet DFIR multi-plateformes — macOS, Android, Docker, AWS CloudTrail

## Chain Summary

- One-line chain: Localisations d'artefacts standards par plateforme: mbox macOS, History SQLite (WebKit epoch), docker history pour recouvrer un Dockerfile, CloudTrail JSON pour une intrusion IAM/EC2.

## Preconditions

- Challenge forensics fournissant un triage macOS, une image Android, une image Docker, ou des logs CloudTrail AWS.

## Cheap Probes

- Identifier d'abord la plateforme/format de triage avant de choisir l'outil (ex: format LiveResponseData.zip = triage macOS typique).

## Telltale Evidence

- macOS: CopiedFiles/<user>/Mails/.../INBOX.mbox/.../Data/Messages (emails bruts lisibles tels quels) ; Chrome/Default/History (SQLite, timestamp WebKit epoch different d'Unix — convertir via outil dedie, pas diviser par 1e6 a la main) ; ParsingOfUnifiedLogs/Logs.txt (logs unifies Apple, chercher mounted/unmounted/diskarbitrationd pour tracer l'execution d'un .dmg).

## Escalation Order

1. macOS (Autopsy): format triage .zip LiveResponseData -> mails bruts, History SQLite WebKit epoch, logs unifies texte.
2. Android: /data/data/com.android.chrome/.../History (meme schema SQLite que desktop) ; runtime-permissions.xml (permissions accordees) ; shared_prefs/*.xml (config app, souvent ou un malware planque son C2/cles en dur).
3. Docker: docker inspect <image> (metadonnees/layers JSON) ; docker history --no-trunc --format '{{.CreatedBy}}' <image> reconstruit CHAQUE commande RUN/COPY du Dockerfile original, y compris celles non visibles dans inspect — reflexe n1 pour un secret code en dur au build ; dive <image> (TUI exploration layer par layer).
4. Une image Docker fournie reste generalement lancable en isolation (docker run ... /bin/sh en override entrypoint, puis docker exec pour declencher/inspecter le vrai entrypoint via cat /init.sh) plutot que de se limiter a l'inspection statique.
5. AWS CloudTrail: logs en .gz par service/region/date, toujours decompresser avant de grep. Champs cles: userIdentity.arn/userName (qui), eventSource/eventName (quoi — CreateStack+cloudformation pour deploiement auto, RunInstances+ec2 pour compute, AuthorizeSecurityGroupIngress pour firewall), sourceIPAddress (trace l'attaquant a travers plusieurs actions/comptes), requestParameters/responseElements (detail exploitable).
6. Pattern d'intrusion cloud typique a reconnaitre: compte vole -> IaC (CloudFormation/Terraform) pour deployer vite et discretement -> ouverture firewall ciblee sur SON PROPRE CIDR (pas 0.0.0.0/0, pour eviter la detection triviale) -> compte IAM backdoor pour survivre a la revocation du compte initial.
7. Reflexe systematique pour tout hash suspect (APK, ELF, PE): googler directement le SHA-256 avant tout sandbox — MalwareBazaar (abuse.ch) indexe la plupart des samples deja soumis.

## Common Mistakes

- Convertir un timestamp WebKit/Chrome epoch en divisant manuellement par 1e6 au lieu d'utiliser un convertisseur dedie (erreurs d'arrondi frequentes). Se limiter a l'inspection statique d'une image Docker quand le comportement runtime (script d'entrypoint) est ce qui est demande.

## Payload Shapes

```text
docker history --no-trunc --format '{{.CreatedBy}}' <image>  |  gunzip tous les .gz CloudTrail avant grep
```

## Related Writeups

- N/A

## Skill Impact

- Related skill: forensics: cheatsheet multi-plateforme a consulter des l'identification du format de triage fourni.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
