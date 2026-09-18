# Phone RGB Analysis V1

## Scope

Phone RGB V1 adds a visible-light analysis path that works from an ordinary front-facing phone photo. It is intentionally a transparent measurement baseline rather than a diagnostic classifier or a synthetic UV/polarized view.

## Pipeline

1. detect the largest frontal face with OpenCV Haar face detection;
2. construct a conservative elliptical facial skin region;
3. exclude eye/brow and mouth regions plus clipped/high-saturation pixels;
4. run capture-quality checks for brightness, blur, face size and clipping;
5. calculate relative visible-light proxies:
   - redness chromaticity/index;
   - local redness area and component count;
   - locally dark/pigmented area and component count;
   - luminance texture index;
6. save original, redness map, pigmentation map and combined overlay;
7. store RGB scans in the same longitudinal database while keeping comparisons modality-specific.

## Product outputs

Phone RGB results expose:

- redness area fraction;
- local redness component count;
- pigmented area fraction;
- local pigmented component count;
- texture index;
- capture quality and quality flags.

The UI supports Original / Redness map / Pigmentation map / Combined views.

## Scientific/product boundaries

These values are **relative phone-RGB proxies** and are intended for longitudinal tracking under similar capture conditions. They are not diagnoses, lesion classifications, or equivalents of polarized/UV imaging. The pipeline does not infer hidden UV fluorescence from RGB.

## Next validation work

- test repeatability under controlled lighting/distance/angle;
- evaluate face-region stability across a more diverse sample of phones and skin tones;
- compare RGB redness/pigmentation proxies against paired polarized imaging when available;
- train learned blemish models only after subject-level labeled data is available;
- add capture guidance before accepting a scan when quality flags are poor.
