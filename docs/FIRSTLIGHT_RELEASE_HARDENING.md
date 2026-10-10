# FIRSTLIGHT Release Hardening Plan

This checklist is the release gate for the SATARK + FIRSTLIGHT prototype. It separates checks that can run in CI from checks that require a maintainer, hosting access, or real provider credentials. Do not mark a check complete without recorded evidence.

## Release status

- [ ] Resolve and review the open FIRSTLIGHT UI pull request against the current `main` branch.
- [ ] Confirm required CI and CodeQL checks pass on the exact candidate commit.
- [ ] Complete the manual desktop/mobile smoke test.
- [ ] Verify the deployed revision and perform a post-deploy smoke test.
- [ ] Record the tested commit, date, tester, and any known limitations.

## 1. Pull request and source integrity

- [ ] Rebase or merge the latest `main` into the UI branch using a normal Git workflow; resolve conflicts by preserving current security fixes and tests.
- [ ] Review the final diff for accidental unrelated changes, generated artifacts, credentials, tokens, real incident data, and unsafe debug logging.
- [ ] Confirm the README and UI accurately describe FIRSTLIGHT as a synthetic, simulator-only incident workspace.
- [ ] Confirm no action path executes real containment, shell commands, account revocation, or network blocking.
- [ ] Do not merge merely because the branch compiles locally; require the latest CI and CodeQL results.

## 2. Automated validation

Run from a clean environment with the supported Python version:

```bash
python -m pip install --upgrade pip
python -m pip install --only-binary=:all: -r requirements.txt
python -m pip check
python -m compileall -q satark.py ai_provider.py scam_challenge.py video_processing.py reports.py satark_utils.py url_security.py radar_background.py stepper_component.py evidence_engine.py firstlight_engine.py firstlight_ingest.py ui tests
python -m unittest discover -s tests -v
```

- [ ] All commands exit successfully.
- [ ] Browser smoke tests complete at desktop and mobile viewport sizes.
- [ ] Intro loader appears on a fresh session, auto-dismisses, supports skip, and does not persist after dismissal.
- [ ] The offline/sample workflow works without provider credentials.
- [ ] PDF and JSON exports are parseable and contain no secrets.
- [ ] The event-import tests cover malformed JSON/CSV, duplicate IDs, oversized artifacts, excessive rows, invalid timestamps, and rejected-row reporting.
- [ ] URL-fetching tests cover private/reserved addresses, mixed DNS answers, redirects, HTTPS downgrade attempts, timeouts, content-type checks, and response-size limits.
- [ ] Any failure is fixed or explicitly documented with a release-blocking decision; never hide a flaky test by silently skipping it.

## 3. Manual UI acceptance

Test in a fresh browser session and capture screenshots for the release record.

- [ ] Overview and FIRSTLIGHT workspace load without tracebacks.
- [ ] Workspace switching preserves the intended case state and does not show stale content from another section.
- [ ] Long event tables and timelines are only rendered when requested; verify there is no accidental horizontal overflow.
- [ ] The synthetic demo, evidence integrity check, tamper challenge, timeline, evidence gaps, approval/rejection controls, audit trail, and report export work end-to-end.
- [ ] Imported event data is clearly distinguished from the fictional demo.
- [ ] Keyboard navigation has visible focus; form controls have understandable labels; reduced-motion preference is respected, including on the intro loader. The intro should use the arcade-inspired pixel/CRT visual language, animated segmented indicator, rotating safety tips, and a keyboard-accessible skip control.
- [ ] At narrow widths, primary controls remain reachable and do not overlap.
- [ ] Errors are actionable but do not reveal raw provider exceptions, stack traces, or sensitive uploaded content.

## 4. Security and privacy gates

- [ ] No credentials are committed. Configure `GROQ_API_KEY` only in the hosting secret manager when AI workflows are required.
- [ ] Access controls match the intended audience. The current prototype does not provide application-level authentication or tenant isolation; do not expose sensitive cases publicly.
- [ ] Keep real personal, regulated, and confidential incident data out of the prototype until storage, access, retention, and provider-processing controls have been reviewed.
- [ ] Enforce upload/request limits and outbound network egress restrictions at the hosting layer.
- [ ] Treat hashes as integrity checks, not proof of source authenticity or truthfulness. Session-local audit chains are not durable forensic evidence.
- [ ] Confirm response proposals are explicitly simulated and require a deliberate human approval/rejection interaction.
- [ ] Check logs and exported reports for API keys, authorization headers, and unnecessary personal data.

## 5. Deployment verification

- [ ] Record the exact commit SHA selected for deployment.
- [ ] Wait for the hosting platform to finish building that revision; confirm the deployment's source SHA matches.
- [ ] Open the deployed app in a private/incognito window and confirm the expected version is live.
- [ ] Run the offline sample and FIRSTLIGHT investigation flow against the deployed instance.
- [ ] If provider-backed analysis is enabled, test one safe, non-sensitive sample and verify missing-key, rate-limit, and provider-error states without exposing secrets.
- [ ] Check desktop and mobile layouts on the hosted URL, not only localhost.
- [ ] Confirm the rollback path and previous known-good revision before announcing availability.

## 6. Known prototype limitations

- Streamlit is the current runtime. Conditional rendering is not equivalent to route-level JavaScript bundle splitting in a Next.js/React application.
- Evidence and case history are session-scoped, not durable case storage.
- The deterministic rules are intentionally limited and can produce false positives or miss activity.
- AI assessments are advisory, not calibrated probabilities or claim-by-claim verification.
- No real endpoint telemetry collection or incident-response containment is performed.
- Passing automated checks does not by itself establish production readiness.

## Release decision

A maintainer should only mark this prototype ready for a controlled demo when the pull request is conflict-free, required CI/security checks pass on the exact candidate commit, manual smoke tests pass, and the deployed revision is verified. Public or sensitive-data production use requires a separate security and operational review.
