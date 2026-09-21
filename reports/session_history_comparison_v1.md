# Session History & Comparison V1

## Goal
Treat a completed guided scan visit as a first-class historical record instead of forcing users to interpret five individual scan rows.

## Product behavior
- History defaults to **Sessions**.
- Completed sessions appear as one visit-level row with subject, modality, timestamp, capture count, and whether an earlier compatible visit exists.
- Opening a session shows all planned regions together.
- The compare selector defaults to the latest earlier compatible session when one exists.
- Users can switch back to **Individual scans** at any time.

## Comparison integrity
A region pair is compared only when:
- both scans belong to the same structured tracking series (same subject + same region),
- the previous session is earlier than the current session,
- UV scans share the same `uv_comparison_key`, or RGB scans share the same RGB engine version,
- both scans remain longitudinally eligible under their modality-specific quality rules.

Regions that fail compatibility are shown as **Not comparable** rather than receiving a numerical delta.

## Display states
Per-region visit comparison uses the existing research-measurement language:
- Stable
- Higher measured signal
- Lower measured signal
- Mixed change
- Not comparable

The UV display thresholds remain 1 spot and 0.5 percentage points of fluorescent area. RGB uses 0.5 percentage points for redness/pigmentation area. These thresholds reduce visual noise; they are not clinical significance thresholds.

## Scope / limitations
- V1 uses the existing `/v1/sessions` read contract; no database migration is required.
- This is a local single-user research beta; it is not authentication or multi-tenant profile isolation.
- Session comparison is non-diagnostic and does not claim improvement, worsening, disease state, bacteria count, or treatment effect.
