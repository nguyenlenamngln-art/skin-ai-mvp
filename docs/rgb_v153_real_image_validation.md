# RGB Measurement V1.5.3 — Real-image anatomical mask validation

## Scope

V1.5.3 is a validation milestone for the existing RGB Measurement V1.5.2 anatomical-mask implementation. It does **not** change redness or pigmentation thresholds, Capture Protocol V1.4, or the V1.5.1 regional trend gate.

The validation harness applies small photometric perturbations to each image and checks whether the V1.5.2 anatomical skin mask remains stable. The production engine under test remains V1.5.2.

## Validation criteria

For each image, the harness evaluates five variants: baseline, -8% exposure, +8% exposure, -5% contrast, and +5% contrast.

A validation image passes when:

- all five variants retain frontal-face detection;
- minimum mask IoU versus baseline is at least 0.85;
- maximum mask-area drift is no more than 12%;
- anatomical-mask fallback rate is no more than 20%;
- minimum anatomical skin-support fraction is at least 70%.

These are engineering repeatability criteria, not clinical validation thresholds.

## Preliminary real-image run

Five recent real phone-capture screenshots were evaluated locally. The screenshots contained real phone RGB captures displayed inside the product UI. No personal image files are committed to the repository.

| Capture | Variants detected | Min IoU | Max area drift | Fallback rate | Min skin support | Baseline added area | Baseline outer holes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| IMG_1410.PNG | 5/5 | 0.9463 | 2.26% | 0% | 98.97% | 0.01% | 0 |
| IMG_1414.PNG | 5/5 | 0.9166 | 6.26% | 0% | 95.15% | 0.67% | 0 |
| IMG_1416.PNG | 5/5 | 0.9407 | 5.35% | 0% | 96.61% | 0.19% | 0 |
| IMG_1419.PNG | 5/5 | 0.9452 | 3.54% | 0% | 94.63% | 0.58% | 0 |
| IMG_1422.PNG | 5/5 | 0.9533 | 2.18% | 0% | 92.45% | 0.64% | 0 |

All five captures meet the preliminary V1.5.3 repeatability criteria. Across this small set, V1.5.2 maintained one stable anatomical component, removed internal feature holes from the outer-envelope metric, used no fallback, and stayed comfortably below the 5% anatomical addition safety limit.

## Limitations

This is a small single-user engineering validation set and the current samples are screenshots of product results rather than original raw camera files. The screenshots still exercise real face geometry and lighting variation, but they are not a substitute for a diverse external validation cohort.

The next validation expansion should use original phone JPEG/HEIC files from multiple people, skin tones, lighting environments, camera models, facial hair states, and framing conditions. Threshold tuning should remain frozen until that broader set shows a reproducible failure mode.

## Reproduce

Run the validator against one or more image files or directories:

```bash
PYTHONPATH=src python -m skin_ai.rgb_validation_v153 path/to/images --output data/interim/rgb_v153_validation.json
```

The output records per-variant face detection, anatomical support, fallback behavior, outer-boundary metrics, mask IoU, and mask-area drift.

Research/wellness use only; no diagnostic claims.
