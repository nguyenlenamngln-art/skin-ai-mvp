# RGB V1.2.1 capture-quality investigation

## Problem observed
A deliberately dark + blurry RGB test capture was correctly excluded from longitudinal trends, but its Lighting subscore was still 100/100. The degraded adaptive skin boundary was also visibly less stable around the eye/cheek region.

## Root cause
Capture Protocol 1.0 used mean HSV V inside the analyzed skin mask as its primary exposure score. On the degraded test image the masked HSV V mean remained about 97, above the full-score threshold of 85, even though grayscale skin luminance was substantially lower.

Development diagnostics on the same portrait:

| Diagnostic | Good reference | Degraded test |
|---|---:|---:|
| masked HSV V mean | ~196 | ~97 |
| masked grayscale median | ~162 | ~75 |
| masked grayscale P25 | ~138 | ~58 |
| Laplacian sharpness variance | ~177 | ~5.7 |
| left/right luminance asymmetry | ~0.165 | ~0.346 |
| skin-mask connected components | 1 | 2 |
| skin-mask holes | 3 | 5 |
| skin-mask perimeter/base ratio | ~1.88 | ~2.22 |

These are development measurements on the supplied test images, not clinical validation.

## Fix: Capture Protocol 1.1

The RGB measurement engine remains `rgb_engine_version = 1.1`; redness/pigmentation/texture extraction is unchanged.

Capture Protocol 1.1:
- replaces HSV V as the primary absolute exposure signal with robust grayscale skin-luminance statistics (median, P25, P90),
- retains broad absolute exposure guards rather than enforcing a narrow universal skin-brightness target,
- compares repeat captures to the nearest prior good, same-engine RGB reference in exposure-value (EV) space when a compatible reference exists,
- flags `lighting_not_comparable` when the capture differs by more than 0.5 EV from the reference,
- adds a segmentation-regularity subscore using mask components, holes, largest-component fraction, and boundary-perimeter ratio,
- flags `segmentation_unstable` when the adaptive mask becomes fragmented/noisy,
- keeps poor captures rejected before persistence and usable captures excluded from longitudinal trends.

## Fairness / interpretation boundary
Absolute skin luminance can differ across people and capture devices, so the protocol deliberately uses broad absolute safety thresholds and prefers within-person reference comparison for longitudinal lighting consistency. Capture quality is a repeatability gate, not a skin-tone score or clinical image-quality score.

## Development check
Using the same two development images with Protocol 1.1:
- the good portrait scored about 96/100 with stable segmentation,
- the degraded portrait was classified `poor`, with blur, uneven-light/pose, and unstable-segmentation flags,
- when compared to the good portrait reference, exposure was about -1.1 EV and the reference lighting subscore fell to 0/100.

The degraded image would therefore be rejected before saving under the revised gate.
