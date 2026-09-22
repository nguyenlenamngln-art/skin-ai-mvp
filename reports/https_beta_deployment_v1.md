# HTTPS Beta Deployment V1

## Goal
Deploy the Skin AI research beta on a real HTTPS origin so mobile browsers can use camera APIs and the app can be tested off localhost.

## Deployment contract
- Dockerized FastAPI + static web app.
- Railway listens on `$PORT` through `scripts/start_production.sh`.
- Persistent product data path: `SKIN_AI_DATA_DIR=/data/product`.
- UV checkpoint path: `UVFD_MODEL_PATH=/data/models/uvfd_unet_v2_best.pt`.
- Optional `UVFD_MODEL_URL` can download the checkpoint at boot when the persistent path is empty.
- `/health` is the Railway healthcheck.
- One Uvicorn worker is used because the current store is SQLite-backed.

## Engine availability
The app may start without the UV checkpoint. In that state:
- Phone RGB remains available.
- The UI reports `RGB ready · UV unavailable`.
- The UV mode is disabled.
- No UV capability is claimed until `uv_model_available=true` from `/health`.

When the V2 checkpoint is provisioned at `UVFD_MODEL_PATH`, UV becomes available automatically after restart.

## Persistence requirement
The `/data` path must be backed by a Railway persistent volume before collecting beta data. SQLite, scan images, and the optional UV checkpoint all live under this path.

## Beta boundary
This is still a research/wellness beta. The RGB and UV measurements are image-derived proxies and are not diagnostic outputs.
