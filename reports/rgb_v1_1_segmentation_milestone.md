# Phone RGB V1.1 — facial skin segmentation refinement

## Goal

Refine the Phone RGB analysis region so the product no longer relies on hard rectangular exclusions around the eyes and mouth, while keeping the workflow dependency-light and runnable on the current Mac setup.

## What changed

- Replaced rectangular exclusions with smooth elliptical eye/brow and mouth exclusions.
- Added a smooth face-oval geometry prior.
- Added per-photo adaptive Lab-chroma skin selection seeded from conservative cheek/forehead regions.
- Added a conservative exposure-only fallback if adaptive color estimation has too few seed pixels.
- Added one-pixel boundary erosion before signal extraction to reduce false components created at mask edges.
- Tightened connected-component filtering by area, aspect ratio, and extent.
- Added a dedicated `skin_region.png` visualization showing the exact analyzed region.
- Added an RGB V1.1 UI layer with a **Skin region** result tab.
- Added segmentation diagnostics and engine version metadata to RGB scan metrics.

## Test portrait development check

On the same controlled front-facing development portrait used during V1 testing, the refined pipeline:

- detected the frontal face successfully;
- retained roughly 78% of the conservative face oval as analyzable skin;
- reported capture quality as `good`;
- removed the large black rectangular exclusions visible in V1;
- reduced development red-component count from 12 to about 8 and dark-component count from 47 to about 35 on this single test image.

These counts are **not validation results**. The portrait is a controlled development sample and the metrics remain relative visible-light proxies.

## Scientific boundary

The V1.1 mask is an adaptive color/geometry mask, not anatomical landmark segmentation and not a dermatology model. Redness, pigmentation, texture, and spot counts remain development proxies intended for longitudinal tracking under similar lighting, distance, angle, exposure, and camera processing.

The RGB pipeline must not be described as equivalent to polarized imaging, UV fluorescence imaging, or clinical diagnosis.

## Next validation step

Test V1.1 on a small, diverse set of real phone photos captured under controlled repeat conditions. Review segmentation coverage manually and quantify within-person repeatability before tuning thresholds further or replacing the geometry/color mask with a learned face-parsing model.
