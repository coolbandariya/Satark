# Release readiness and deployment runbook

This document separates a working hackathon demonstration from a service that is safe for public or sensitive use. Passing CI is necessary, but it is not proof of production readiness.

## Current release posture

- **Hackathon demonstration with synthetic/non-sensitive inputs:** suitable only after the exact deployed revision passes the checks below.
- **Small supervised pilot with non-sensitive content:** conditional on provider, deployment, abuse-control and recovery checks.
- **Public anonymous service using a shared provider key:** **not ready by default**. A shared per-process sliding-window limiter is defense in depth, not a distributed/global quota: multiple workers, replicas or restarts can bypass its aggregate ceiling. A public service still needs gateway/provider-side global quotas, rate limiting, concurrency limits and cost controls.
- **Confidential, regulated or multi-tenant incident evidence:** **not ready** without authenticated access, authorization/tenant isolation, retention and deletion controls, approved provider data handling, durable case storage, and an independently reviewed operational design.
- **Production / high availability:** requires a separate threat model, security review, monitoring, incident response, backup/restore and rollback exercises.

## Before every deployment

1. Record the Git commit SHA, repository, branch, Streamlit entry point and hosting target. Confirm the host deploys the intended repository and branch—not a similarly named fork or stale app.
2. Run the exact-commit CI and CodeQL workflows. Check dependency consistency, Python compilation, unit tests, desktop/mobile browser smoke tests, report download, and the offline sample. Review every new high/critical code-scanning alert on the changed code; do not suppress an alert without a documented, reviewed rationale.
3. Set `GROQ_API_KEY` only in the host's secret manager. Never put real keys in `.streamlit/secrets.toml` committed to Git, source files, screenshots, issue reports or browser code. Rotate any key that may have been exposed.
4. Keep hosted exception details hidden. The repository's Streamlit defaults set `client.showErrorDetails = "none"` and cap a single upload at 50 MB; PDF and image processing have stricter per-format limits. Confirm the host respects these settings and any platform-level request limits.
5. Test without a provider key. The offline sample and deterministic FIRSTLIGHT demo must remain usable, and failed live-provider requests must not be presented as a safe verdict.
6. With a dedicated test key, exercise a successful text scan, vision scan, provider timeout, invalid/revoked key, unavailable model, malformed provider response, and rate-limit response. Verify user-facing errors do not expose secrets, request headers or raw provider payloads.
7. Exercise malformed, encrypted and oversized PDFs; malformed and oversized images; decompression-bomb-like image dimensions; empty and oversized videos; invalid URLs; private/reserved IPs; mixed DNS answers; and redirects to blocked destinations. Confirm rejection is graceful and bounded.
8. Verify the hosting layer enforces request body size, execution timeout, concurrency and outbound network policy. Application URL checks are defense in depth, not a replacement for egress controls.
9. Review the configured AI provider's current data-processing and retention terms before allowing any real user data. Until approved, use synthetic or public non-sensitive content only.
10. Verify the deployed UI, not only local CI: home, FIRSTLIGHT, every scanner mode, session history, PDF export, mobile layout, refresh/restart behavior, logs and resource use.
11. Confirm the privacy notice, acceptable-use language, contact/security-reporting route, data retention/deletion behavior, incident response owner and rollback procedure are current.
12. Record the result, unresolved risks, owner and go/no-go decision. Do not mark a deployment verified unless you actually tested the deployed URL and revision.

## Security and privacy boundaries

- SATARK is a triage aid; scores are not calibrated probabilities, and results do not prove that content is safe or malicious.
- FIRSTLIGHT response actions are simulated. Its in-session audit chain is not durable, independently anchored evidence storage or certified chain of custody.
- Session state is not authenticated case storage and is not tenant isolation. The analysis limiter is process-local; it is not a durable or distributed abuse-control boundary.
- URL fetching uses validated public DNS results, pinned connections and redirect revalidation, but public URL retrieval still requires outbound network restrictions at the hosting layer.
- Upload limits bound input size, but do not guarantee a fixed memory/CPU budget under concurrent workloads.
- Content submitted for AI analysis may leave the host and be processed by the configured provider. Do not submit credentials, OTPs, private keys or sensitive incident data unless the provider and legal basis have been reviewed.
- Do not add analytics, logging or error reporting that captures raw submitted content, provider keys or full sensitive URLs by default.

## Go/no-go record template

- Deployed repository / branch / commit:
- Hosting target / app URL:
- CI run:
- CodeQL run:
- Live provider test:
- File and URL abuse tests:
- Secret and privacy review:
- Resource and concurrency checks:
- Known limitations:
- Rollback path tested:
- Decision / reviewer / date:

A missing answer is an unresolved item, not an implicit pass.