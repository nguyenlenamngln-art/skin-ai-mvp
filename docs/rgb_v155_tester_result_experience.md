# RGB V1.5.5 — Tester Result Experience

## Scope

V1.5.5 is a presentation-only milestone for external testers. It does not change the RGB measurement engine, thresholds, masks, capture-quality rules, or longitudinal eligibility logic.

Frozen production behavior:

- RGB engine under test remains V1.5.2;
- Capture Protocol remains V1.4;
- V1.5 redness/pigmentation thresholds remain unchanged;
- V1.5.1 regional trend gate remains unchanged;
- V1.5.2 anatomical-mask stabilization remains unchanged;
- V1.5.3/V1.5.4 validation tooling remains unchanged.

## Tester-facing result hierarchy

For a successful Phone RGB scan, the result screen now prioritizes:

1. **Your skin today** — visible redness area, visible pigmentation area, and texture signal.
2. **Change since last comparable scan** — shown only when a same-version quality-eligible prior RGB scan exists.
3. **What we detected** — Original, Skin region, Redness, Pigment, and Combined views.
4. **Scan quality** — clearly states whether the capture is suitable for longitudinal comparison.
5. **Technical details** — collapsed by default and intended for research/validation review.

## First-scan behavior

A first eligible scan is presented as a baseline. The app does not assign clinical severity labels or compare the tester with a population. Instead, it explains that repeat scans under similar lighting, distance, and angle enable personal longitudinal comparison.

If a scan is saved but not longitudinally eligible, the result remains reviewable but is explicitly described as excluded from trend comparison.

## Repeat-scan behavior

When a same-version quality-eligible previous scan exists, the UI shows direction and percentage-point change for:

- visible redness area;
- visible pigmentation area.

The wording is descriptive only: higher, lower, or stable relative to that tester's prior comparable scan.

## Technical details

The expandable technical section preserves access to:

- RGB engine version;
- Capture Protocol version;
- measurement confidence;
- high-confidence skin coverage;
- pigmentation-ready coverage;
- framing, lighting, and segmentation subscores;
- anatomical outer-boundary stability;
- measured-skin support;
- regional confidence;
- regional trend-gate eligibility;
- measurement warnings.

## Safety / interpretation

V1.5.5 deliberately avoids unvalidated labels such as mild/moderate/severe redness or a healthy-skin score. The result remains framed as a visible-light research measurement for personal longitudinal tracking, not diagnosis and not a substitute for polarized, UV, or clinical skin assessment.
