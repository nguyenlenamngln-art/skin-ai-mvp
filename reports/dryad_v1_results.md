# Dryad CAP Acne — V1 fluorescence baseline

## Dataset inventory

The uploaded Dryad release contains an outer archive with `CAP_acne.html`, `README.md`, and a nested `Raw_images_files_of_measurements_Dryad.zip`.

After extraction and removal of macOS metadata:

- 1,622 JPEG files.
- 813 unique JPEG byte streams.
- 809 exact duplicate pairs.
- The duplicate pattern is deliberate: original `IMG_####.jpg` files are copied under anatomical names.
- 580 labeled Visiopor screenshots are available after retaining only `M`, `RC`, `RF`, `LF`, and `LC`.
- 40 participants have baseline Visiopor images.
- 39 participants have week-6 images.
- 37 participants have week-10 images.
- The study HTML contains 115 visit-level TPC/PSV ground-truth rows: 39 baseline, 39 endpoint, and 37 follow-up.

## Baseline method

The Visiopor images in this release are photographs of the instrument software, not direct raw sensor exports. The current baseline therefore:

1. crops the processed-image panel using normalized screenshot coordinates;
2. computes red/orange fluorescence excess relative to the local panel background;
3. applies a robust median/MAD threshold;
4. counts connected fluorescent components;
5. sums the five regional counts to create a visit-level spot-count proxy.

No OCR is used. Ground-truth TPC/PSV values are read directly from the HTML statistical table.

## Development results

Across 115 labeled visits:

- spot-count proxy vs TPC: Pearson **0.924**, Spearman **0.929**.
- spot-count proxy vs PSV: Pearson **0.885**, Spearman **0.898**.

Five-fold grouped cross-validation, with participant ID as the grouping unit:

| Target | R² | MAE | RMSE | Pearson | Spearman |
|---|---:|---:|---:|---:|---:|
| TPC | 0.849 | 22.99 | 36.70 | 0.921 | 0.927 |
| PSV | 0.777 | 3.33 | 4.51 | 0.881 | 0.895 |

## Interpretation

This is a strong enough development signal to continue: the visible fluorescence in the screenshots contains information that tracks the instrument's reported porphyrin endpoints.

It is **not** external or clinical validation. The threshold was developed while inspecting this dataset, and the source files are photographs of software screens. A future validation stage should freeze the method and evaluate against a separate fluorescence dataset or newly acquired paired device data.

## Next milestone

1. improve panel localization so it does not depend on fixed screenshot coordinates;
2. extract per-region measurements, not only visit aggregates;
3. test a small learned segmentation model against the transparent baseline;
4. preserve subject-grouped cross-validation;
5. later validate on true exported UV/UVA images or paired 365-nm device captures.
