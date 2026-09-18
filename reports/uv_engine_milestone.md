# UV Analysis Engine milestone

## Model selection

V2 was selected over V1 on the same held-out source-image groups.

| Metric | V1 | V2 |
|---|---:|---:|
| Dark artifact Dice | 0.483 | 0.552 |
| Light/reflective artifact Dice | 0.299 | 0.443 |
| Macro Dice | 0.391 | 0.497 |

V2 therefore provides a materially stronger artifact mask, especially for the light/reflective class.

## V2 caveat

The validation/test gap for the light-artifact class is large (validation Dice ~0.084 vs test Dice ~0.443). The model is useful as a development baseline, but this split is not enough evidence for a stable production estimate. Grouped cross-validation remains required before relying on the segmentation metrics themselves.

## Combined engine

The new `UVAnalysisEngine` performs the following sequence:

1. resize the supplied UV/UVA image to the model's 256x256 input;
2. predict dark and light artifact masks using the V2 U-Net;
3. combine those masks into an exclusion region;
4. calculate porphyrin fluorescence only from observed non-artifact pixels;
5. return component count, fluorescence area fraction, red intensity proxy, artifact fractions, model metadata, and component coordinates;
6. optionally save artifact masks, porphyrin mask, overlay, and metrics JSON.

Artifact pixels are **excluded**, not inpainted. The system never invents replacement fluorescence values.

## HTTP API

`POST /v1/uv/analyze` accepts one uploaded image and returns JSON metrics. `GET /health` reports whether the configured model checkpoint exists.

Set the checkpoint path before starting the server:

```bash
export UVFD_MODEL_PATH=/absolute/path/to/uvfd_unet_v2_best.pt
uvicorn skin_ai.api:app --host 0.0.0.0 --port 8000
```

## Local smoke test result

The engine was tested locally using the V2 checkpoint and a held-out UVFD example. The API returned HTTP 200 and produced:

- artifact area fraction: ~0.0467
- dark artifact area fraction: ~0.0238
- light artifact area fraction: ~0.0228
- valid observed area: ~0.9533
- porphyrin component proxy count: 2
- porphyrin area fraction over valid pixels: ~0.0128

These are development proxy values, not diagnostic measurements.

## Next milestone

The next scientific milestone is to evaluate whether artifact exclusion improves porphyrin agreement with Dryad TPC/PSV on data where comparable artifact behavior exists, and then run grouped cross-validation for V2 segmentation stability. After that, the same API can be connected to the phone/web application.
