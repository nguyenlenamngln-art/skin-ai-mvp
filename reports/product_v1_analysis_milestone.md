# Product V1 analysis milestone

## Goal

Turn the working UV research prototype into a clearer beta analysis experience without adding unvalidated measurements.

## Changes

- Four analysis views: Original, Artifact map, Porphyrin map, Combined.
- Correct three-color legend:
  - red = dark hair / ruler artifact
  - green = light / reflective artifact
  - amber = porphyrin fluorescence proxy
- Six result metrics:
  - fluorescent component count proxy
  - fluorescent area fraction
  - red-channel fluorescence intensity proxy
  - dark artifact area
  - light artifact area
  - total excluded artifact area
- Previous-scan comparison for spot count and fluorescent area.
- Improved history rows with artifact percentage and spot-count change.
- Original scan image exposed through the API media contract.
- Inline favicon to remove the browser favicon 404.
- Research-beta language retained; no diagnostic claim added.

## Deliberately deferred

Phone RGB analysis remains labeled as upcoming. It is not simulated with placeholder scores. A separate RGB measurement pipeline should be built and evaluated before enabling that mode.

## Interpretation policy

Artifact pixels are excluded rather than inpainted. Porphyrin outputs remain development proxies and should only be compared across scans captured under similar device, lighting, distance, and anatomical conditions.
