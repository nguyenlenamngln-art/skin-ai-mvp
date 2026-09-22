#!/bin/sh
set -eu

mkdir -p "${SKIN_AI_DATA_DIR:-/data/product}" "$(dirname "${UVFD_MODEL_PATH:-/data/models/uvfd_unet_v2_best.pt}")"

if [ ! -f "${UVFD_MODEL_PATH:-/data/models/uvfd_unet_v2_best.pt}" ] && [ -n "${UVFD_MODEL_URL:-}" ]; then
  echo "UV checkpoint missing; downloading configured model artifact..."
  UVFD_MODEL_URL="$UVFD_MODEL_URL" UVFD_MODEL_PATH="${UVFD_MODEL_PATH:-/data/models/uvfd_unet_v2_best.pt}" python - <<'PY'
import os
import urllib.request
from pathlib import Path
url=os.environ['UVFD_MODEL_URL']
out=Path(os.environ['UVFD_MODEL_PATH'])
out.parent.mkdir(parents=True,exist_ok=True)
tmp=out.with_suffix(out.suffix+'.part')
urllib.request.urlretrieve(url,tmp)
tmp.replace(out)
print(f'Downloaded UV checkpoint to {out}')
PY
fi

if [ -f "${UVFD_MODEL_PATH:-/data/models/uvfd_unet_v2_best.pt}" ]; then
  echo "UV checkpoint available."
else
  echo "UV checkpoint not configured; starting RGB-capable beta with UV unavailable."
fi

echo "RGB capture protocol V1.3: phone framing and segmentation calibration enabled."
exec python -m uvicorn skin_ai.product_api_mobile_v13:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1
