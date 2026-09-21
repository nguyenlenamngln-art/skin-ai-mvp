# Phone RGB V1.2 — longitudinal capture quality

This milestone adds a repeatability gate without changing the RGB measurement engine version (still V1.1).

## Capture protocol

The RGB engine now scores:
- lighting / brightness
- sharpness
- face size / framing
- face centering
- highlight / shadow clipping
- left-right luminance symmetry as a coarse pose / lighting consistency signal

It returns a 0–100 `capture_quality_score`, subscores, flags, retake guidance, and `longitudinal_eligible`.

## Persistence policy

- `good`: saved and eligible for same-version longitudinal deltas/trends
- `usable`: saved for review but excluded from longitudinal deltas/trends
- `poor`: rejected before saving with retake guidance

Legacy RGB scans without `longitudinal_eligible` are eligible only when their recorded capture quality is `good`.

## Product boundary

The capture score is a repeatability/research-quality gate, not a clinical image-quality score and not a diagnostic assessment.
