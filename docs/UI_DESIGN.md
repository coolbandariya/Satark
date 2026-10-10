# SATARK UI design notes

SATARK is an evidence-first security workspace, not a marketing-only demo. Visual polish should help users understand the next action without making the analysis appear more certain than it is.

## Design principles

- **Hierarchy before decoration:** FIRSTLIGHT is the primary incident workspace; individual scanners remain easy to reach but secondary.
- **Evidence before verdict:** separate observable signals, AI interpretation, uncertainty and recommended actions.
- **Quiet confidence:** dark, high-contrast surfaces, restrained lilac/cyan/mint accents, readable body copy and consistent borders.
- **Useful motion only:** brief entrance transitions and small hover responses; no motion that blocks input, hides state or implies an analysis is running when it is not.
- **Responsive by default:** layouts collapse from multi-column desktop views to a single-column mobile flow. Avoid fixed-width controls and horizontal overflow.
- **No hidden work:** provider calls, file parsing and analysis begin only after the user explicitly starts the action.

## React Bits inspiration

The project references [React Bits](https://github.com/DavidHDev/react-bits) for design inspiration—particularly layered backgrounds, subtle component motion, interaction feedback and adaptable component composition. SATARK does not copy/paste a React Bits runtime into Streamlit. The current implementation uses project-owned CSS and native Streamlit controls to avoid adding another client runtime, a CDN dependency or an unnecessary JavaScript bundle to the security-analysis path.

## Motion and accessibility

- Honor `prefers-reduced-motion: reduce`; all decorative entrance/hover animations must be disabled or reduced.
- Keep keyboard focus visible. Never remove the browser outline without providing a stronger replacement.
- Use semantic headings and descriptive button labels for key actions.
- Do not communicate risk through color alone; include text labels and explanatory context.
- Do not use animation to suggest a provider connection, scan completion or live threat feed unless that state is real.
- Prefer CSS-only effects over heavy canvas/WebGL effects for the default workspace.

## Performance

- Keep decorative effects bounded and pointer-events disabled.
- Avoid loading third-party JavaScript/CDNs in the critical path.
- Keep uploads and remote URL responses bounded before expensive processing.
- Make the user trigger costly analysis explicitly; do not analyze on page load or merely because a widget rerendered.
- Validate desktop and narrow mobile layouts with the browser smoke suite.

## Verification

Run the CI checks from the repository root:

```bash
python -m pip check
python -m compileall -q .
python -m unittest discover -s tests -v
python tests/e2e_smoke.py
```

The browser suite starts a local Streamlit app in CI, checks the editorial home layout at desktop/mobile sizes, exercises scanner selection and navigation, and validates the sample PDF download. It does not replace a manual test of a deployed host or live provider-backed analysis.
