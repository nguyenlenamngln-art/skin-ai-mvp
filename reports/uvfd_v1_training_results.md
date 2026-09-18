# UVFD Artifact Segmentation — V1 training result

## Training configuration

- Dataset: Mendeley UVFD artifact dataset, version 2
- Usable image/mask pairs: 2,653
- Split unit: inferred original UVFD source-image group (not individual 512×512 crops)
- Train: 1,972 crops / 85 source groups
- Validation: 368 crops / 18 source groups
- Test: 313 crops / 18 source groups
- Input resolution: 128×128
- Architecture: compact two-output U-Net
- Output channel 0: dark hair + ruler artifacts
- Output channel 1: light hair + UV-reflecting particle artifacts
- Loss: balanced BCE + soft Dice
- Epochs: 4
- Runner: GitHub Actions CPU

## Held-out results

| Metric | Dark artifacts | Light/reflective artifacts | Macro |
|---|---:|---:|---:|
| Dice | 0.483 | 0.299 | 0.391 |
| IoU | 0.318 | 0.176 | 0.247 |
| Precision | 0.474 | 0.293 | — |
| Recall | 0.492 | 0.305 | — |

Validation macro Dice was 0.280. Test macro Dice was 0.391.

## Interpretation

V1 confirms that a learned artifact detector is feasible, especially for dark hair/ruler structures. It is **not** yet strong enough to be treated as a final cleaning model.

The light-artifact channel is substantially harder. It is sparse, visually heterogeneous, and has fewer positive examples than the dark-artifact class. The validation/test gap also shows that source-group composition matters, so one split is not enough evidence for a stable production estimate.

## Decision

Keep V1 as the reproducible baseline and checkpoint, but do not wire it into the user-facing porphyrin score yet.

## V2 priorities

1. train at 256×256 rather than 128×128 so thin hairs/particles retain more structure;
2. oversample crops containing white/light masks;
3. use a focal/Tversky-style loss for sparse positives;
4. evaluate multiple group-safe folds rather than one group split;
5. consider separate dark- and light-artifact models if two-channel optimization continues to hurt the light class;
6. tune thresholds per class on validation data only;
7. compare model masking against the transparent rule-based baseline before integrating with porphyrin measurement.

These are development results, not clinical validation.
