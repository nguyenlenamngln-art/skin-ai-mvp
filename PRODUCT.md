# Skin AI Product V0

Product V0 wraps the research UV analysis engine in a usable local web application.

## What works

- Responsive web UI served directly by FastAPI.
- UV image upload/camera capture on supported mobile browsers.
- Real V2 artifact segmentation and artifact-aware porphyrin proxy analysis.
- Overlay/mask result visualization.
- Scan persistence to SQLite.
- Scan history and longitudinal trend visualization.
- Editable AM/PM skincare routine.
- Explicit research-beta/non-diagnostic labeling.

Phone RGB analysis is intentionally shown as **coming next** because it has not yet been validated in this project.

## Install the selected V2 checkpoint

Place the checkpoint at:

```bash
models/uvfd_unet_v2_best.pt
```

or point the app to another location:

```bash
export UVFD_MODEL_PATH=/absolute/path/to/uvfd_unet_v2_best.pt
```

## Run the product

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH="$PWD/src"
uvicorn skin_ai.product_api:app --reload --port 8000
```

Open:

```text
http://localhost:8000
```

Scans, generated masks, and SQLite state are stored under `data/product/` by default.

## Current boundaries

The current fluorescence and porphyrin outputs are research/development proxies. They are not diagnostic measurements and are not claimed to be equivalent to Visiopor, VISIA, or a dermatologist assessment.

Before public deployment, add authentication, encrypted object storage, consent/privacy flows, production database migrations, rate limits, telemetry, and external validation.
