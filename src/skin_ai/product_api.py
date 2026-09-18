from __future__ import annotations
import io, os, uuid
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel
from skin_ai.store import ProductStore
from skin_ai.uv_engine import UVAnalysisEngine

ROOT=Path(__file__).resolve().parents[2]
DATA_DIR=Path(os.environ.get('SKIN_AI_DATA_DIR',ROOT/'data/product'))
MODEL_PATH=Path(os.environ.get('UVFD_MODEL_PATH',ROOT/'models/uvfd_unet_v2_best.pt'))
SCAN_DIR=DATA_DIR/'scans'; DB_PATH=DATA_DIR/'skin_ai.db'; WEB_DIR=ROOT/'web';SCAN_DIR.mkdir(parents=True,exist_ok=True)
app=FastAPI(title='Skin AI Product API',version='0.3.0')
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in os.environ.get('SKIN_AI_CORS','http://localhost:8000').split(',')],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
app.mount('/media',StaticFiles(directory=SCAN_DIR),name='media')
store=ProductStore(DB_PATH); _engine=None

class RoutinePayload(BaseModel):
    morning:list[str]
    evening:list[str]

def get_engine():
    global _engine
    if _engine is None:
        if not MODEL_PATH.exists():
            raise HTTPException(status_code=503,detail={'code':'model_missing','message':'UV model checkpoint is not installed.','expected_path':str(MODEL_PATH)})
        _engine=UVAnalysisEngine(MODEL_PATH)
    return _engine

def public_scan(scan):
    sid=scan['id']
    return {**scan,'media':{
        'original':f'/media/{sid}/original.jpg',
        'overlay':f'/media/{sid}/overlay.png',
        'artifact_mask':f'/media/{sid}/artifact_mask.png',
        'porphyrin_mask':f'/media/{sid}/porphyrin_mask.png',
        'dark_mask':f'/media/{sid}/dark_artifact_mask.png',
        'light_mask':f'/media/{sid}/light_artifact_mask.png'
    }}

@app.get('/health')
def health():
    return {'status':'ok','model_available':MODEL_PATH.exists(),'model_path':str(MODEL_PATH),'data_dir':str(DATA_DIR),'api_version':'0.3.0'}

@app.get('/v1/scans')
def list_scans(limit:int=30):
    return [public_scan(x) for x in store.list_scans(min(max(limit,1),100))]

@app.get('/v1/scans/{scan_id}')
def get_scan(scan_id:str):
    scan=store.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404,detail='Scan not found')
    return public_scan(scan)

@app.get('/v1/trends')
def trends(limit:int=90):
    return store.trends(min(max(limit,1),365))

@app.get('/v1/routine')
def get_routine():
    return store.get_routine()

@app.put('/v1/routine')
def update_routine(payload:RoutinePayload):
    return store.set_routine({'morning':[x.strip() for x in payload.morning if x.strip()][:20],'evening':[x.strip() for x in payload.evening if x.strip()][:20]})

@app.post('/v1/uv/analyze')
async def analyze_uv(image:UploadFile=File(...)):
    raw=await image.read()
    if len(raw)>20*1024*1024:
        raise HTTPException(status_code=413,detail='Image exceeds 20 MB')
    try:
        rgb=np.asarray(Image.open(io.BytesIO(raw)).convert('RGB'))
    except Exception as exc:
        raise HTTPException(status_code=400,detail='Invalid image') from exc
    result=get_engine().analyze_rgb(rgb)
    scan_id=uuid.uuid4().hex[:16]
    created_at=datetime.now(timezone.utc).isoformat()
    out_dir=SCAN_DIR/scan_id
    UVAnalysisEngine.save_result(result,out_dir)
    Image.fromarray(rgb).save(out_dir/'original.jpg',quality=92)
    store.add_scan(scan_id=scan_id,created_at=created_at,modality='uv',source_name=image.filename,metrics=result.metrics,media_dir=str(out_dir))
    scan=store.get_scan(scan_id)
    return public_scan(scan)

if WEB_DIR.exists():
    app.mount('/app',StaticFiles(directory=WEB_DIR),name='app-assets')
    app.mount('/',StaticFiles(directory=WEB_DIR,html=True),name='web')
