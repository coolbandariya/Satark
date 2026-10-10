# Contributing to SATARK

Thanks for helping improve SATARK. Changes should make security decisions more explainable, keep user data bounded, and preserve the distinction between deterministic observations and AI-generated interpretation.

## Before opening a pull request

1. Create a focused branch and describe the user-visible or security impact.
2. Add or update tests for behavior changes. Security-boundary changes need regression tests for both rejected and accepted cases.
3. Keep credentials, real incident artifacts, private URLs and personal data out of commits, screenshots, tests and issue reports.
4. Avoid adding third-party runtime/CDN dependencies to the default UI without a clear need and a documented trade-off.
5. Do not label model output as a verified fact or a calibrated probability.

## Local validation

Use Python 3.10 or newer. Install the pinned runtime dependencies, then run:

```bash
python -m pip install -r requirements.txt
python -m pip check
python -m compileall -q .
python -m unittest discover -s tests -v
```

For browser checks, install Playwright and Chromium, start the app in a separate terminal, and run `python tests/e2e_smoke.py`. CI performs the full browser smoke test automatically.

## Pull request checklist

- [ ] The change has a clear purpose and does not include unrelated refactors.
- [ ] Relevant regression tests were added or updated.
- [ ] Input validation, size limits and error handling remain in place.
- [ ] UI changes work at desktop and mobile widths and respect reduced-motion preferences.
- [ ] Documentation and screenshots (if any) contain no secrets or real sensitive evidence.
- [ ] CI and CodeQL checks have been reviewed.
- [ ] Any deployment-specific limitation is explicitly documented.

## Security reports

Please follow [SECURITY.md](SECURITY.md) for suspected vulnerabilities. Do not publish exploit details or real sensitive evidence in a public issue.
