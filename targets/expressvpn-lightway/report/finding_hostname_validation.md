# Finding: TLS server-identity (hostname/CN/SAN) validation is opt-in and off by default in `lightway-client`

**Program**: ExpressVPN Bug Bounty (YesWeHack)
**Scope assets**: `https://github.com/expressvpn/lightway`, `https://github.com/expressvpn/wolfssl-rs`
**Researcher account**: L3_M0z4rt
**Class**: CWE-295 (Improper Certificate Validation) / CWE-297 (Improper Validation of Certificate with Host Mismatch)
**Status**: Confirmed in open-source code via reproducible regression tests. **Not yet confirmed against the production ExpressVPN client/fleet** — see "Open question for the vendor" below.

## Summary

`lightway-client` (and the underlying `lightway-core` / `wolfssl-rs` libraries it is built on) validates that a VPN server's TLS certificate chains to a trusted CA, but **never validates that the certificate's CN/SAN actually matches the server being connected to**, unless the operator explicitly supplies a `server_dn` (CLI flag `--server-dn` / config field `server_dn`). This field is empty by default, and nothing in the codebase warns when it is left unset.

Practical effect: if an attacker holds **any** certificate signed by the trust anchor the client loads — e.g. the private key material for one compromised/rogue node in the server fleet, or any other certificate issued by the same CA — they can present it while impersonating **any other server** in that fleet, and the client will accept it. The chain-of-trust check passes; the "is this specifically the host I meant to reach" check is simply never performed.

## Root cause, with exact locations

1. `lightway-core` exposes server-identity checking as an **opt-in** builder call:
   - `lightway-core/src/connection/builders.rs:172-178`
     ```rust
     /// Enable server domain name validation
     pub fn with_server_domain_name_validation(self, server_dn: &str) -> Self {
         Self { session_config: self.session_config.with_checked_domain_name(server_dn), ..self }
     }
     ```
   - `wolfssl-rs/wolfssl/src/ssl.rs`: `checked_domain_name: Option<String>` on `SessionConfig`; if `None`, no `wolfSSL_check_domain_name`-style check is ever installed.

2. `lightway-client` only calls it conditionally, gated on an `Option`:
   - `lightway-client/src/lib.rs:1503-1506`
     ```rust
     .when_some(server_dn, |b, sdn| {
         b.with_server_domain_name_validation(&sdn)
     })
     ```
   - `server_dn` is threaded through from `lightway-client/src/config.rs:70` (`pub server_dn: String`, CLI `--server-dn`) via:
     - `config.rs:411-412`: `server_dn: (!self.server_dn.is_empty()).then(|| std::mem::take(&mut self.server_dn))`
     - `config.rs:544`: default value `server_dn: String::new()`

   So: **if the operator does not pass `--server-dn`, `server_dn` is `None`, and hostname/identity validation is silently skipped.** `config.rs::validate()` checks many other settings (buffer sizes, GUIDs, queue lengths, etc.) but has no check or warning for a missing `server_dn`.

3. Neither `lightway-core` nor `lightway-client` ever call `with_ssl_verify_mode` / `wolfSSL_set_verify` at all (confirmed by exhaustive grep across both crates) — so TLS verify-mode behavior comes entirely from wolfSSL's own default, which (confirmed empirically below) does enforce CA-chain validation, but — again — chain validation and hostname/identity validation are two independent checks in wolfSSL's API, and only the first one happens unconditionally.

## Proof of Concept

Three new regression tests were added to `wolfssl-rs/wolfssl/src/ssl.rs` (`mod tests`), built and run against the real vendored wolfSSL (via `cargo test`), with no modification to any production code path:

### Test 1 — sanity: chain validation *is* enforced by default (rules out full bypass)
A client context loads a legitimate CA (`CA_CERT`, test fixture) but — matching `lightway-client`'s real code path exactly — never calls `with_ssl_verify_mode`. The server presents a **self-signed certificate from a completely unrelated, attacker-generated CA** (`CN=evil.attacker.example`, generated with `openssl req -x509 ...`, not signed by `CA_CERT` at all).

```
client_err = Some("Fatal: CA cert not available to verify certificate")
client finished = false
```
→ **Correctly rejected.** wolfSSL's default verify mode does enforce chain-of-trust even with no explicit `set_verify` call.

### Test 2 — the actual finding: identity/hostname checking is skipped by default
Same client context (legitimate CA loaded, no verify-mode call). The server now presents `SERVER_CERT`, a certificate **validly signed by the loaded CA** (chain is fine), but whose identity (`CN=www.wolfssl.com`, `SAN=DNS:example.com, IP:127.0.0.1`) matches neither the CN nor any SAN entry of the host the client is supposedly trying to reach. `with_checked_domain_name` is **never called** — mirroring `lightway-client` with an empty/default `server_dn`.

```
client finished (identity mismatch, no domain check requested) = true
```
→ **Handshake completes anyway.** The client has no way to know it is talking to the wrong server.

### Test 3 — control: the feature works correctly when actually enabled
Identical setup to Test 2, except `with_checked_domain_name("attacker-controlled-host.test")` is explicitly set on the client session (i.e. simulating `--server-dn` being passed).

```
client_err (domain check enabled, mismatched name) = Some("Fatal: Domain name mismatch")
```
→ **Correctly rejected.** This confirms the hostname-check mechanism itself is not broken — it is simply off unless explicitly requested, and nothing tells the operator that.

### Reproduction

```bash
git clone https://github.com/expressvpn/wolfssl-rs
cd wolfssl-rs
git submodule update --init --depth 1
# apply the three test functions appended to wolfssl/src/ssl.rs::mod tests
# (see attached patch / diff)
# generate the rogue, unrelated self-signed cert used by test 1:
openssl req -x509 -newkey rsa:2048 -keyout /tmp/rogue_key.pem -out /tmp/rogue_cert.pem \
  -days 365 -nodes -subj "/CN=evil.attacker.example"
# convert to the crate's `include!`-able DER-as-Rust-array fixture format
# and drop at wolfssl/tests/data/rogue_cert_der, rogue_key_der
cd wolfssl
cargo test --lib default_verify_mode_with_rogue_unrelated_cert -- --nocapture
cargo test --lib default_verify_mode_skips_hostname_check_when_not_requested -- --nocapture
cargo test --lib checked_domain_name_rejects_identity_mismatch_when_enabled -- --nocapture
```

Full test source is in the accompanying patch file (`ssl_rs_poc.patch`).

## Impact

- Chain-of-trust (CA) validation: **enforced**, not bypassable by an arbitrary attacker with no relationship to the trusted CA.
- Server-identity validation: **not enforced by default**. Any party holding a certificate signed by the client's trusted CA — for *any* subject — is accepted as *any* server.
- For a VPN provider operating many server nodes under one (or a small number of) issuing CA(s), this means: compromise of **one** node's private key (or any other means of obtaining a validly-signed certificate under that CA, e.g. an insider, a misissuance, or a compromised internal CA-issuance pipeline) is enough to **MITM a client's connection intended for a different, uncompromised node** — without needing to break TLS cryptography, phish a root CA, or compromise the client's actual intended destination at all.
- This degrades the security model from "I am talking to *this specific* server" to "I am talking to *some* server the CA has ever vouched for" — a meaningful weakening for a product whose entire value proposition is "which server traffic goes through" is a trust-sensitive decision.

**Suggested severity**: Medium–High (CVSS 3.1 estimate: **AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:N ≈ 6.5–7.0**, `AC:H` because exploitation requires the attacker to already hold a cert signed by the operator's own CA — this is not an unauthenticated, zero-precondition MITM against arbitrary internet attackers, but it is a real and realistic precondition for an insider, a compromised fleet node, or a CA-issuance-pipeline compromise). Final severity is the vendor's call and depends on the answer to the open question below.

## Open question for the vendor (do **not** assume before reporting)

I cannot verify, from the open-source `lightway-core` / `lightway-client` / `wolfssl-rs` repositories alone, whether the **actual, compiled, distributed ExpressVPN application** (desktop/mobile apps, not the bare `lightway-client` CLI reference implementation) passes `--server-dn` / sets `server_dn` internally when it establishes its own VPN connections. If it does, the shipped product is not exposed despite this gap existing in the open-source reference implementation. If it does not, the shipped product inherits this exact gap. **This is the central question the report should ask, rather than asserting either way.**

## Suggested remediation

1. Make hostname/identity validation **mandatory by default** in `lightway-client` whenever a CA is configured, unless explicitly opted out (invert the default).
2. At minimum, have `Config::validate()` emit a loud warning (or refuse to start, depending on desired strictness) when `ca_cert` is set but `server_dn` is not.
3. Document, in `lightway-core`'s `with_server_domain_name_validation` doc comment and in `wolfssl-rs`'s `checked_domain_name` field doc, that omitting it means the peer's identity is not checked at all (CA-chain validation alone does not imply "this is the right server") — the current doc comments do not make this risk explicit.

## Artifacts

- `ssl_rs_poc.patch` — the three test functions as a unified diff against `wolfssl-rs/wolfssl/src/ssl.rs`
- `rogue_cert.pem` / `rogue_key.pem` — the self-signed, unrelated-CA certificate used in Test 1
- Full `cargo test -- --nocapture` output for all three tests (above)
