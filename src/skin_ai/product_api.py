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
from skin_ai.rgb_engine import RGBAnalysisEngine

ROOT=Path(__file__).resolve().parents[2]
DATA_DIR=Path(os.environ.get('SKIN_AI_DATA_DIR',ROOT/'data/product'))
MODEL_PATH=Path(os.environ.get('UVFD_MODEL_PATH',ROOT/'models/uvfd_unet_v2_best.pt'))
SCAN_DIR=DATA_DIR/'scans'; DB_PATH=DATA_DIR/'skin_ai.db'; WEB_DIR=ROOT/'web';SCAN_DIR.mkdir(parents=True,exist_ok=True)
app=FastAPI(title='Skin AI Product API',version='0.5.0')
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in os.environ.get('SKIN_AI_CORS','http://localhost:8000').split(',')],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
app.mount('/media',StaticFiles(directory=SCAN_DIR),name='media')
store=ProductStore(DB_PATH); _uv_engine=None; _rgb_engine=None

class RoutinePayload(BaseModel):
    morning:list[str]
    evening:list[str]

def get_uv_engine():
    global _uv_engine
    if _uv_engine is None:
        if not MODEL_PATH.exists():
            raise HTTPException(status_code=503,detail={'code':'model_missing','message':'UV model checkpoint is not installed.','expected_path':str(MODEL_PATH)})
        _uv_engine=UVAnalysisEngine(MODEL_PATH)
    return _uv_engine

def get_rgb_engine():
    global _rgb_engine
    if _rgb_engine is None:
        _rgb_engine=RGBAnalysisEngine()
    return _rgb_engine

def public_scan(scan):
    sid=scan['id']
    if scan['modality']=='rgb':
        media={'original':f'/media/{sid}/original.jpg','skin_region':f'/media/{sid}/skin_region.png','overlay':f'/media/{sid}/rgb_overlay.png','redness_map':f'/media/{sid}/redness_map.png','pigmentation_map':f'/media/{sid}/pigmentation_map.png'}
    else:
        media={'original':f'/media/{sid}/original.jpg','overlay':f'/media/{sid}/overlay.png','artifact_mask':f'/media/{sid}/artifact_mask.png','porphyrin_mask':f'/media/{sid}/porphyrin_mask.png','dark_mask':f'/media/{sid}/dark_artifact_mask.png','light_mask':f'/media/{sid}/light_artifact_mask.png'}
    return {**scan,'media':media}

@app.get('/health')
def health():
    return {'status':'ok','uv_model_available':MODEL_PATH.exists(),'model_available':MODEL_PATH.exists(),'rgb_engine_available':True,'rgb_engine_version':RGBAnalysisEngine.VERSION,'capture_protocol_version':RGBAnalysisEngine.CAPTURE_PROTOCOL_VERSION,'model_path':str(MODEL_PATH),'data_dir':str(DATA_DIR),'api_version':'0.5.0'}

@app.get('/v1/scans')
def list_scans(limit:int=30, modality:str|None=None):
    if modality not in (None,'uv','rgb'): raise HTTPException(status_code=400,detail='modality must be uv or rgb')
    return [public_scan(x) for x in store.list_scans(min(max(limit,1),100),modality=modality)]

@app.get('/v1/scans/{scan_id}')
def get_scan(scan_id:str):
    scan=store.get_scan(scan_id)
    if not scan: raise HTTPException(status_code=404,detail='Scan not found')
    return public_scan(scan)

@app.get('/v1/trends')
def trends(limit:int=90, modality:str|None=None):
    if modality not in (None,'uv','rgb'): raise HTTPException(status_code=400,detail='modality must be uv or rgb')
    return store.trends(min(max(limit,1),365),modality=modality)

@app.get('/v1/routine')
def get_routine(): return store.get_routine()

@app.put('/v1/routine')
def update_routine(payload:RoutinePayload):
    return store.set_routine({'morning':[x.strip() for x in payload.morning if x.strip()][:20],'evening':[x.strip() for x in payload.evening if x.strip()][:20]})

def decode_image(raw:bytes)->np.ndarray:
    if len(raw)>20*1024*1024: raise HTTPException(status_code=413,detail='Image exceeds 20 MB')
    try: return np.asarray(Image.open(io.BytesIO(raw)).convert('RGB'))
    except Exception as exc: raise HTTPException(status_code=400,detail='Invalid image') from exc

@app.post('/v1/uv/analyze')
async def analyze_uv(image:UploadFile=File(...)):
    rgb=decode_image(await image.read()); result=get_uv_engine().analyze_rgb(rgb)
    scan_id=uuid.uuid4().hex[:16]; created_at=datetime.now(timezone.utc).isoformat(); out_dir=SCAN_DIR/scan_id
    UVAnalysisEngine.save_result(result,out_dir); Image.fromarray(rgb).save(out_dir/'original.jpg',quality=92)
    store.add_scan(scan_id=scan_id,created_at=created_at,modality='uv',source_name=image.filename,metrics=result.metrics,media_dir=str(out_dir))
    return public_scan(store.get_scan(scan_id))

@app.post('/v1/rgb/analyze')
async def analyze_rgb(image:UploadFile=File(...)):
    rgb=decode_image(await image.read())
    try: result=get_rgb_engine().analyze_rgb(rgb)
    except ValueError as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc
    q=result.metrics
    if q.get('capture_quality')=='poor':
        raise HTTPException(status_code=422,detail={'code':'capture_quality_failed','message':'Capture quality is too low for a reliable RGB scan. Retake the photo using the guidance below.','capture_quality':q.get('capture_quality'),'capture_quality_score':q.get('capture_quality_score'),'quality_flags':q.get('quality_flags',[]),'quality_guidance':q.get('quality_guidance',[])})
    scan_id=uuid.uuid4().hex[:16]; created_at=datetime.now(timezone.utc).isoformat(); out_dir=SCAN_DIR/scan_id
    RGBAnalysisEngine.save_result(result,out_dir)
    store.add_scan(scan_id=scan_id,created_at=created_at,modality='rgb',source_name=image.filename,metrics=result.metrics,media_dir=str(out_dir))
    return public_scan(store.get_scan(scan_id))

if WEB_DIR.exists():
    app.mount('/app',StaticFiles(directory=WEB_DIR),name='app-assets')
    app.mount('/',StaticFiles(directory=WEB_DIR,html=True),name='web')
