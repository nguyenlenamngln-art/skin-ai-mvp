# RGB V1.5.8 — Personal Skin Journey & Simplified UX

V1.5.8 turns the tester-facing beta from a scan-centric research workflow into a small personal skin-tracking product while keeping the measurement stack frozen.

## Product goal

Give testers a reason to return by answering five simple questions:

1. What does my skin look like today?
2. What changed from my own baseline?
3. Can I see the visual difference?
4. What has my progress looked like over time?
5. What routine/context changes do I want to remember?

The primary navigation is intentionally limited to five destinations:

- Today
- Progress
- Scan
- Routine
- Journey

On mobile, these destinations are available in a persistent bottom navigation bar. Important screens are designed to remain within one or two taps.

## Tester experience

### Today

The Today screen shows the latest quality-eligible RGB scan, the tester's own baseline comparison, three visible-light signals, scan eligibility, and a clear next action.

V1.5.8 does not create an overall skin score, population rank, severity grade, or diagnostic interpretation.

### Progress

Progress contains:

- descriptive changes from the tester's own baseline
- redness, pigmentation, and texture trends
- a before/after photo comparison slider
- explicit wording that higher/lower is descriptive rather than good/bad

Only RGB V1.5.2 scans that are eligible for longitudinal comparison are used in these views.

### Scan

The existing capture, quality gate, analysis, Tester Study Mode, and V1.5.5 result experience remain intact. Study identity and access control continue to run through V1.5.7.

### Routine

The existing AM/PM routine editor remains available. V1.5.8 adds a lightweight optional skin diary for context such as a new product, outdoor/sun exposure, shaving, makeup, or poor sleep.

Diary notes are stored in browser local storage in V1.5.8 and are explicitly labeled as device-local. They are not part of the research export and should not be treated as synchronized research records.

### Journey

Journey is a chronological visual timeline of comparable RGB captures. Each item shows the original image and descriptive changes from the tester's baseline, with a direct link back to the full scan result.

## Study Mode integration

V1.5.7 previously hid all navigation except Scan while Study Mode was active. V1.5.8 removes that tester-facing restriction while preserving server-side study access control and data scoping.

A signed-in tester can therefore use Today, Progress, Routine, Journey, and Scan while remaining scoped to only their own study records.

## Measurement stack remains frozen

V1.5.8 does not change:

- RGB engine V1.5.2
- Capture Protocol V1.4
- redness thresholds
- pigmentation thresholds
- V1.5.1 regional trend gate
- V1.5.2 anatomical mask stabilization
- V1.5.3 real-image validation logic
- V1.5.4 repeatability criteria
- V1.5.5 result measurement interpretation
- V1.5.7 study access control

The release is a product/UX layer only.

## Safety / interpretation

Phone RGB values remain relative visible-light proxies for personal longitudinal tracking. The product should not present them as diagnoses, clinical severity, population-normalized health scores, or proof that a routine caused a change.

Before/after imagery can be influenced by lighting, angle, expression, distance, and camera processing; the interface states this explicitly.

## V1.5.8 success signal

The milestone is successful if testers can understand the app without researcher explanation and voluntarily return to inspect their progress rather than only completing requested study captures.
