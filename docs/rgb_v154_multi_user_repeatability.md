# RGB Measurement V1.5.4 — Multi-image / multi-user capture repeatability

## Scope

V1.5.4 expands the V1.5.3 real-image validator into a cohort-level repeatability framework. It is a validation milestone only: the production RGB engine remains V1.5.2, Capture Protocol remains V1.4, V1.5 redness/pigmentation rules stay frozen, and the V1.5.1 regional trend gate is unchanged.

The goal is to distinguish three questions:

1. Does each individual image remain stable under the V1.5.3 photometric perturbations?
2. Does the anatomical outer envelope remain repeatable across multiple captures and sessions for the same participant?
3. Is the cohort large enough to support a multi-user engineering validation claim?

The framework intentionally refuses to mark the cohort as passed when there are too few independent participants or sessions, even if the available images look stable.

## Manifest format

Use pseudonymous identifiers rather than names or other directly identifying information.

CSV columns:

```text
path,participant_id,session_id,capture_id,device_id
captures/P001_S01_C01.jpg,P001,S01,C01,iphone-15-pro
captures/P001_S01_C02.jpg,P001,S01,C02,iphone-15-pro
captures/P001_S02_C01.jpg,P001,S02,C03,iphone-15-pro
```

Required fields: `path`, `participant_id`, `session_id`.

Optional fields: `capture_id`, `device_id`.

A JSON manifest may also be used as either a list of capture objects or an object containing a `captures` list.

## Per-capture validation

Every capture is first evaluated by RGB V1.5.3. This preserves the existing five-variant photometric checks:

- baseline;
- -8% exposure;
- +8% exposure;
- -5% contrast;
- +5% contrast.

The V1.5.3 engineering criteria remain unchanged.

## Cross-capture normalization

For repeatability across independently framed images, V1.5.4 extracts the V1.5.2 anatomical outer envelope, crops it to the detected face box, and resizes the binary envelope to a canonical 192 x 192 grid using nearest-neighbor interpolation.

This normalized mask is used only for repeatability validation. It does not replace the production skin mask and is not used to calculate redness or pigmentation.

## Provisional participant-level criteria

A participant is considered complete when the manifest contains at least:

- 3 captures;
- 2 independent sessions.

The provisional engineering repeatability checks are:

- V1.5.3 per-image pass rate >= 80%;
- median pairwise canonical-mask IoU >= 0.80;
- median session-consensus IoU >= 0.80;
- canonical outer-envelope area coefficient of variation <= 12%;
- anatomical-mask fallback rate <= 20%;
- minimum anatomical skin-support fraction >= 70%.

Session consensus masks are majority-vote masks across valid captures within a session.

These values are engineering gates, not clinical validation thresholds.

## Provisional cohort-completeness criteria

The cohort can pass only when:

- at least 3 participants are present;
- at least 3 participants are complete under the capture/session rules above;
- at least 80% of participants pass the participant-level repeatability checks.

A smaller data set still produces a report, but `cohort_pass` remains false with explicit reasons such as `insufficient_participants` or `insufficient_complete_participants`.

## Current data status

The saved V1.5.3 material includes repeated phone-capture screenshots from one participant. A separate portrait/degraded-portrait pair is also available for engineering smoke testing, but it is not an independent repeated phone-capture session and therefore should not be counted toward completion of the V1.5.4 cohort.

Accordingly, V1.5.4 should be treated as **framework complete / cohort data pending** until original phone JPEG/HEIC captures are collected from multiple independent participants.

## Recommended capture protocol for the first cohort

For each participant, collect at least three frontal RGB captures across at least two sessions. Prefer original camera files rather than screenshots. Keep the phone approximately at the Capture Protocol V1.4 distance and framing, while allowing realistic small variation in pose and lighting.

Record only pseudonymous validation metadata in the manifest. Device model identifiers may be included when useful for engineering stratification.

A practical first cohort is 5–10 participants with 4–6 captures per person across at least two sessions, spanning different lighting environments, camera models, facial-hair states, and visible skin tones. The minimum 3-participant gate exists to prevent accidental overclaiming; it is not a target sample size for external validation.

## Reproduce

```bash
PYTHONPATH=src python -m skin_ai.rgb_repeatability_v154 \
  data/rgb_v154_manifest.csv \
  --output data/interim/rgb_v154_repeatability.json
```

The report contains cohort criteria, participant summaries, per-capture V1.5.3 results, normalized-envelope repeatability metrics, fallback behavior, and skin-support metrics.

Research/wellness use only; no diagnostic claims.
