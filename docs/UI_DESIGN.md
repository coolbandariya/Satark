# SATARK UI design notes

SATARK is an evidence-first security workspace, not a marketing-only demo. Visual polish should reduce cognitive load and make the next action obvious.

## Information architecture

- **Overview:** one clear headline, a single featured FIRSTLIGHT spotlight, three real calls to action, and a compact scanner directory. It is not a full product manual.
- **FIRSTLIGHT:** the flagship incident workspace. Select a focused work area (Incident, Evidence Integrity, Investigation, Response Center, Audit Trail) rather than rendering every panel at once.
- **Investigate:** one artifact type at a time. Keep input, action, result, evidence ledger and report export in a predictable vertical order.
- **Session history:** completed reports remain in the current session; avoid placing history controls on the home page.

## Visual system

- Use a near-black navy base, restrained periwinkle/lilac for product interaction, mint for verified/positive states, and amber for caution. Red is reserved for danger states.
- Use layered radial gradients and a spotlight preview as visual anchors; avoid excessive gradients on every card.
- Keep content widths bounded, use consistent radii/borders, and preserve whitespace between sections.
- Capability cards are a compact directory, not another wall of copy. Detailed workflows belong on their own page.
- Keep the visual hierarchy: FIRSTLIGHT primary, scanners secondary, learning/sample material tertiary.

## React Bits inspiration

The project references [React Bits](https://github.com/DavidHDev/react-bits) and its [SpotlightCard-style patterns](https://reactbits.dev/showcase) for layered light, hover feedback, restrained motion and composition. The implementation remains project-owned CSS and native Streamlit controls rather than importing a React runtime into the Streamlit app.

The broader UX principles are inspired by current SaaS guidance: clear value proposition, one primary next action, product-led previews, accessible contrast and motion that clarifies state rather than distracting. Sources: [Unbounce SaaS landing-page guidance](https://unbounce.com/conversion-rate-optimization/the-state-of-saas-landing-pages/) and [The Good's SaaS design overview](https://thegood.com/insights/saas-website-design/).

## Motion and accessibility

- Honor `prefers-reduced-motion: reduce`; disable decorative loops and hover transforms.
- Keep keyboard focus visible. Never remove outlines without an equally visible replacement.
- Use semantic headings and descriptive button labels for key actions.
- Do not communicate risk through color alone; include labels and explanatory context.
- Do not use animation to imply a provider connection, scan completion or live threat feed unless that state is real.
- Prefer bounded CSS effects over heavy canvas/WebGL effects for the default workspace.

## Performance and verification

- No third-party JavaScript/CDNs in the critical path.
- Expensive analysis runs only after explicit user action.
- Run `python -m compileall -q .`, `python -m unittest discover -s tests -v`, and `python tests/e2e_smoke.py`.
- Browser tests check desktop/mobile layout, spotlight presence, scanner selection, navigation, FIRSTLIGHT workflows, sample report and PDF download. They do not replace a manual test of deployed hosting or live provider-backed analysis.
