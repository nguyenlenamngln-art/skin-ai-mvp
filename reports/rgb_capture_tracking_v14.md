# RGB Capture & Tracking V1.4

## Scope

This milestone changes capture/tracking behavior only. RGB measurement remains V1.1.

## Changes

- Separates advisory quality warnings from blocking failures.
- High-scoring captures with only advisory warnings can be `good` and longitudinally eligible.
- Severe exposure, blur, extreme framing, lighting mismatch, or severe segmentation remain blockers.
- Standard standalone Phone RGB scans default to `My profile` + `Full face` when no structured tracking context was explicitly selected.
- Adds `/v1/rgb/capture-check`, a non-persistent low-resolution face-size endpoint using the same OpenCV face detector as RGB analysis.
- Live guidance displays `Move closer`, `Distance good`, `Move back`, or `Center face` from that server-side check.
- Preview frames used by the distance check are not written to the scan store or media directory.

## Safety / interpretation

Phone RGB outputs remain visible-light research proxies, not diagnoses and not equivalent to polarized or UV imaging. Longitudinal comparisons still require compatible RGB analysis versions and a structured tracking series.
