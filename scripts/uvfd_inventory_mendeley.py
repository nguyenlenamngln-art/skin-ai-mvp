from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

DATASET_ID = "wvmw7p76t8"
VERSION = "2"
BASE = f"https://data.mendeley.com/public-api/datasets/{DATASET_ID}"
OUT = Path(os.environ.get("UVFD_OUT", "artifacts/uvfd_inventory"))
OUT.mkdir(parents=True, exist_ok=True)

ENDPOINTS = {
    "files_root": f"{BASE}/files?folder_id=root&version={VERSION}",
    "files_all": f"{BASE}/files?version={VERSION}",
    "folders": f"{BASE}/folders?version={VERSION}",
    "folders_root": f"{BASE}/folders?folder_id=root&version={VERSION}",
    "dataset": f"{BASE}?version={VERSION}",
}

def fetch_json(name: str, url: str):
    req = urllib.request.Request(url, headers={"User-Agent":"skin-ai-mvp/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            status = getattr(r, "status", 200)
            ctype = r.headers.get("content-type")
    except Exception as e:
        payload = {"ok": False, "url": url, "error": repr(e)}
        (OUT / f"{name}.json").write_text(json.dumps(payload, indent=2))
        print(f"[{name}] ERROR {e}")
        return None
    text = raw.decode("utf-8", errors="replace")
    try:
        data = json.loads(text)
    except Exception:
        data = {"_raw_text": text[:200000]}
    wrapper = {"ok": True, "url": url, "status": status, "content_type": ctype, "data": data}
    (OUT / f"{name}.json").write_text(json.dumps(wrapper, indent=2))
    kind = type(data).__name__
    size = len(data) if hasattr(data, "__len__") else None
    print(f"[{name}] status={status} type={kind} len={size}")
    if isinstance(data, list) and data:
        print(f"[{name}] first keys={sorted(data[0].keys())}")
        for i, item in enumerate(data[:5]):
            print(f"[{name}] sample {i}: name={item.get('name')} id={item.get('id')} size={item.get('size')} folder_id={item.get('folder_id')} keys={sorted(item.keys())}")
    elif isinstance(data, dict):
        print(f"[{name}] keys={sorted(data.keys())}")
    return data

responses = {}
for name, url in ENDPOINTS.items():
    responses[name] = fetch_json(name, url)

# Build a compact summary of anything that looks downloadable.
downloadables = []
for source, data in responses.items():
    candidates = data if isinstance(data, list) else []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        cd = item.get("content_details") or {}
        url = cd.get("download_url") if isinstance(cd, dict) else None
        if url:
            downloadables.append({
                "source": source,
                "id": item.get("id"),
                "name": item.get("name"),
                "size": item.get("size"),
                "folder_id": item.get("folder_id"),
                "download_url": url,
            })

(OUT / "downloadables.json").write_text(json.dumps(downloadables, indent=2))
print(f"downloadable entries discovered: {len(downloadables)}")
for x in downloadables[:20]:
    print(" -", x["name"], x["size"], x["folder_id"])

summary = {
    "dataset_id": DATASET_ID,
    "version": VERSION,
    "endpoint_status": {
        k: ("ok" if v is not None else "failed") for k, v in responses.items()
    },
    "downloadable_count": len(downloadables),
}
(OUT / "summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
