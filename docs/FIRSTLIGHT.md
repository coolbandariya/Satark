# FIRSTLIGHT inside SATARK

FIRSTLIGHT is SATARK's primary incident-response workspace. Existing SATARK text, URL, image, QR, PDF and video analysis remain available as secondary threat-analysis tools.

## Current prototype scope

- Repeatable synthetic account-compromise incident.
- Evidence records sealed with SHA-256 over canonical JSON.
- Deterministic evidence verification and an interactive tamper challenge.
- Evidence-linked detection/correlation/verification workflow.
- Timeline reconstruction with explicit evidence gaps and uncertainty.
- Human approval/rejection for simulated response proposals.
- Hash-chained in-session audit events and JSON report export.

## Safety boundaries

This prototype does not collect live endpoint telemetry, execute shell commands, isolate hosts, revoke real sessions, block network traffic, or claim forensic certification. All response actions are simulated. The sample incident and indicators are fictional.

A hash mismatch indicates that a record differs from the stored baseline; it does not identify who changed it or prove that the original record was truthful. The in-session hash chain is tamper-evident only while its trusted baseline remains protected. Production use requires authenticated access, tenant isolation, durable append-only storage, independently protected/anchored manifests, reliable timestamps, retention policy, secrets management, network egress controls and operational review.

## Local validation

Run:

```bash
python -m unittest tests.test_firstlight_engine -v
```

The main Streamlit app exposes the workspace through its sidebar. JSON/CSV import and the deterministic rule checks do not require an AI API key. Imported data remains in Streamlit session state and is not durable case storage. The artifact hash identifies the exact uploaded bytes but does not authenticate the source, prove truthfulness, or establish forensic chain of custody. Detection rules are intentionally small and can miss activity or produce false positives.
