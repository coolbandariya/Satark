# Security Policy

## Supported versions

Security fixes are provided for the default branch. This repository may be an academic project or prototype; do not assume it is suitable for production or for handling sensitive data without a separate security review.

## Reporting a vulnerability

Please do not disclose vulnerabilities in public issues. Use GitHub's **Report a vulnerability** feature (Security tab) to send a private report. Include the affected version or commit, steps to reproduce, impact, and any suggested mitigation.

Please allow maintainers reasonable time to investigate and prepare a fix before public disclosure. Do not include real credentials, personal data, or production secrets in reports.

## Deployment checklist

- [ ] Run the CI workflow successfully on the exact commit being deployed.
- [ ] Configure `GROQ_API_KEY` using the hosting provider's secret manager; never place it in source control or a public client bundle.
- [ ] Restrict access to the application if it is not intended for anonymous public use. SATARK does not currently provide application-level user authentication or tenant isolation.
- [ ] Enforce outbound network egress controls at the hosting/network layer. URL fetches now pin each TCP connection to a validated public IP and revalidate each redirect, but network isolation remains important defense in depth.
- [ ] Confirm the repository's 50 MB Streamlit upload cap and per-format PDF/image limits are effective in the deployed host; enforce request and concurrency limits at the proxy/hosting layer and verify resource usage under load.
- [ ] Review provider data handling and avoid sending confidential or regulated content until an approved data-processing design exists.
- [ ] Test the deployed application, including provider errors, rate limits, malformed files, and recovery from interrupted requests.
- [ ] Establish monitoring, dependency update procedures, incident response, and a rollback path.
- [ ] Complete the [release readiness runbook](docs/RELEASE_READINESS.md), record the exact deployed commit, and test the live URL before calling a release verified.

A passing unit-test workflow alone does not establish production readiness. Do not deploy with unresolved CI failures or without a security review appropriate to the data and audience.
