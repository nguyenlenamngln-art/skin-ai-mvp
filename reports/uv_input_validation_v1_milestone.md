# UV Input Validation V1

## Goal
Prevent obvious ordinary RGB/natural photographs from entering the current UV fluorescence analysis pipeline and producing misleading porphyrin/artifact outputs.

## Product behavior
- Validation runs before UV model inference and before persistence.
- Rejected inputs return HTTP 422 and are not saved to History or UV trends.
- The scan screen shows a dedicated **UV input rejected** current-attempt state.
- Accepted UV scans store validator version/profile/score in scan metrics.

## Validator scope
V1 is intentionally conservative and scoped to the current `uvfd_like_closeup_v1` workflow: close-up ultraviolet-induced fluorescence dermatoscopy images similar to the UVFD data used to develop the artifact model.

The validator uses wrong-modality cues such as:
- a large frontal face occupying a substantial portion of the frame,
- natural-scene tonal range/background behavior,
- broad scene contrast,
- scene-detail profile inconsistent with the current close-up dataset.

Passing the validator **does not prove UV illumination**. It only means the input is compatible enough with the supported image profile to continue to the research UV pipeline.

## Development calibration check
Using the previously verified UVFD inspection artifact available during development:
- 20/20 sampled UVFD close-up images passed the V1 rules.
- the normal frontal portrait test was rejected.
- the deliberately dark/blurry frontal portrait test was rejected.

This is a development sanity check, not formal validation. Broader device-specific data are needed before relying on the gate across other UV cameras or capture styles.

## Safety / interpretation
The downstream UV metrics remain research proxies and are not diagnostic. The validator specifically prevents one known failure mode—obvious normal photographs entering UV mode—but cannot authenticate illumination wavelength or capture hardware from pixels alone.
