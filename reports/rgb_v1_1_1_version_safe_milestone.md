# Phone RGB V1.1.1 — version-safe longitudinal comparison

This milestone prevents longitudinal UI from comparing RGB scans created by different analysis engines.

## Behavior

- Every current RGB scan already stores `rgb_engine_version` in its metrics.
- Older RGB scans with no version are treated as `legacy-v1` in the UI.
- Result deltas only use the nearest older RGB scan with the same engine version.
- Overview metric deltas use the same version-safe rule.
- RGB trend charts only include scans with the same engine version as the selected scan.
- If an older RGB scan exists but was created with another version, the result is labeled `New baseline after analysis update` and cross-version deltas are suppressed.
- History rows show the RGB engine version for transparency.
- UV comparison behavior is unchanged.

## Why

V1.1 changed the analyzed skin region and component filtering, so its redness/pigmentation metrics are not directly comparable with V1 metrics. Version-safe baselines avoid presenting algorithm changes as biological change.

## Scientific boundary

Phone RGB outputs remain relative visible-light research proxies intended for repeated measurements under similar capture conditions. They are not diagnostic measurements and are not equivalent to polarized or UV imaging.
