FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    SKIN_AI_DATA_DIR=/data/product \
    UVFD_MODEL_PATH=/data/models/uvfd_unet_v2_best.pt

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.deploy.txt ./requirements.deploy.txt
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.deploy.txt \
    && python -m pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY . .
RUN mkdir -p /data/product /data/models

CMD ["sh", "scripts/start_production.sh"]
