# Skin AI MVP — dataset and UV fluorescence pipeline

This starter project prepares the data layer for a phone-first skincare app that may later accept true 365-nm UV and cross-polarized images.

## What is implemented

- A provenance registry for four high-value research datasets.
- A unified per-image manifest schema.
- Recursive manifest builder for downloaded archives.
- Subject-level train/validation/test splitting to prevent longitudinal leakage.
- A simple, transparent UV/UVA porphyrin fluorescence baseline that detects warm red/orange fluorescent components from **real fluorescence images**.
- Tests using synthetic fluorescence spots.

## Important scientific boundary

The porphyrin baseline does **not** create UV information from a normal phone image. It analyzes fluorescence images that were actually acquired under UV/UVA illumination. Any future RGB→UV or RGB→polarization model must be labeled as estimated/synthetic unless validated against paired physical measurements.

## Dataset order

1. Dryad CAP acne — 40 participants, baseline/week 6/week 10, five facial regions, fluorescence and sebum measurements; CC0.
2. Mendeley UVFD artifact segmentation — crops from 120 UVFD photos/33 patients, 512×512 masks; CC BY 4.0.
3. Hyper-Skin 2023 — 306 cubes/51 subjects, RGB↔VIS and MSI↔NIR; access requires EULA.
4. Mendeley biopsy-site UVFD/PD — paired polarized dermoscopy and 365-nm UVFD examples; CC BY 4.0.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH="$PWD/src"
```

## Download / place data

Try the Dryad helper:

```bash
python -m skin_ai.download_public_data --dryad --out-dir data/raw
```

If the repository rejects scripted downloads, download the ZIP from the dataset landing page in `configs/datasets.json` and place/extract it under `data/raw/dryad_cap_acne/`.

For Mendeley datasets, use the landing-page Download All control and extract into corresponding directories.

Hyper-Skin requires completion of its EULA/access request.

## Build a manifest

```bash
python -m skin_ai.build_manifest \
  --root data/raw/dryad_cap_acne \
  --dataset-id dryad_cap_acne \
  --license CC0 \
  --source-url 'https://datadryad.org/dataset/doi:10.5061/dryad.12jm63z3t' \
  --out data/interim/dryad_cap_acne_manifest.csv
```

Inspect the manifest before training, because research archives often use inconsistent filename abbreviations.

## Split without participant leakage

```bash
python -m skin_ai.split_manifest \
  --manifest data/interim/dryad_cap_acne_manifest.csv \
  --out data/processed/dryad_cap_acne_manifest_split.csv
```

Never randomly split individual images when multiple visits from the same participant exist.

## Run the porphyrin baseline

```bash
python -m skin_ai.porphyrin_baseline path/to/fluorescence_image.jpg \
  --mask-out data/interim/example_mask.png \
  --json-out data/interim/example_metrics.json
```

The output currently exposes proxies only: component count, fluorescent area fraction, and red-channel intensity. These must be calibrated against the Visiopor outputs/labels before being presented as a clinical or instrument-equivalent measurement.

## Immediate next engineering milestone

After the Dryad ZIP is available:

1. inventory actual filenames/resolutions;
2. map each image to participant, visit, facial region, and modality;
3. compare our fluorescence proxy against published/embedded TPC and PSV values;
4. tune segmentation thresholds only on the training cohort;
5. freeze thresholds/model and evaluate on subject-held-out test participants;
6. then replace the hand-built threshold baseline with a small segmentation network if it improves held-out agreement.
