from __future__ import annotations
import io, os, uuid
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel
from skin_ai.store import ProductStore
from skin_ai.uv_engine import UVAnalysisEngine
from skin_ai.uv_input_validator import UVInputValidator
from skin_ai.uv_longitudinal import checkpoint_signature, stamp_uv_longitudinal_metadata
from skin_ai.rgb_engine_v152 import RGBAnalysisEngine
from skin_ai.tracking import get_region, region_options, stamp_tracking_metadata
from skin_ai.session_plan import SESSION_VERSION, next_region, session_plan, session_progress

ROOT=Path(__file__).resolve().parents[2]
DATA_DIR=Path(os.environ.get('SKIN_AI_DATA_DIR',ROOT/'data/product'))
MODEL_PATH=Path(os.environ.get('UVFD_MODEL_PATH',ROOT/'models/uvfd_unet_v2_best.pt'))
SCAN_DIR=DATA_DIR/'scans'; DB_PATH=DATA_DIR/'skin_ai.db'; WEB_DIR=ROOT/'web';SCAN_DIR.mkdir(parents=True,exist_ok=True)
app=FastAPI(title='Skin AI Product API',version='0.8.0')
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in os.environ.get('SKIN_AI_CORS','http://localhost:8000').split(',')],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
app.mount('/media',StaticFiles(directory=SCAN_DIR),name='media')
store=ProductStore(DB_PATH); _uv_engine=None; _uv_validator=None; _rgb_engine=None; _uv_model_signature=None

class RoutinePayload(BaseModel):
    morning:list[str]
    evening:list[str]

class SubjectPayload(BaseModel):
    display_name:str

class SessionPayload(BaseModel):
    subject_id:str
    modality:str

def get_uv_engine():
    global _uv_engine
    if _uv_engine is None:
        if not MODEL_PATH.exists():
            raise HTTPException(status_code=503,detail={'code':'model_missing','message':'UV model checkpoint is not installed.','expected_path':str(MODEL_PATH)})
        _uv_engine=UVAnalysisEngine(MODEL_PATH)
    return _uv_engine

def get_uv_model_signature():
    global _uv_model_signature
    if _uv_model_signature is None:
        if not MODEL_PATH.exists():
            raise HTTPException(status_code=503,detail={'code':'model_missing','message':'UV model checkpoint is not installed.','expected_path':str(MODEL_PATH)})
        _uv_model_signature=checkpoint_signature(MODEL_PATH)
    return _uv_model_signature

def get_uv_validator():
    global _uv_validator
    if _uv_validator is None: _uv_validator=UVInputValidator()
    return _uv_validator

def get_rgb_engine():
    global _rgb_engine
    if _rgb_engine is None: _rgb_engine=RGBAnalysisEngine()
    return _rgb_engine

def resolve_tracking(subject_id:str|None, region_code:str|None, modality:str):
    if not subject_id and not region_code: return None, None
    if not subject_id or not region_code:
        raise HTTPException(status_code=422,detail={'code':'tracking_identity_incomplete','message':'Choose both a subject profile and a scan region, or leave both blank for analysis-only.'})
    subject=store.get_subject(subject_id)
    if not subject:
        raise HTTPException(status_code=422,detail={'code':'subject_not_found','message':'Selected subject profile does not exist.'})
    region=get_region(region_code,modality)
    if not region:
        raise HTTPException(status_code=422,detail={'code':'invalid_region','message':f'Region {region_code!r} is not supported for {modality.upper()} scans.'})
    return subject,region

def resolve_session_tracking(session_id:str|None, modality:str, subject_id:str|None, region_code:str|None):
    if not session_id:
        subject,region=resolve_tracking(subject_id,region_code,modality)
        return None,subject,region,None
    session=store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=422,detail={'code':'session_not_found','message':'Scan session was not found.'})
    if session['status']!='in_progress':
        raise HTTPException(status_code=422,detail={'code':'session_not_active','message':'This scan session is already complete.'})
    if session['modality']!=modality:
        raise HTTPException(status_code=422,detail={'code':'session_modality_mismatch','message':f'This session is for {session["modality"].upper()} scans.'})
    completed=[x['region_code'] for x in session['items']]
    expected=next_region(session['plan'],completed)
    if expected is None:
        raise HTTPException(status_code=422,detail={'code':'session_complete','message':'All regions in this session are already complete.'})
    if subject_id and subject_id!=session['subject_id']:
        raise HTTPException(status_code=422,detail={'code':'session_subject_mismatch','message':'Selected subject does not match the active session.'})
    if region_code and region_code!=expected:
        raise HTTPException(status_code=422,detail={'code':'session_region_mismatch','message':f'The next required region is {expected}.'})
    subject,region=resolve_tracking(session['subject_id'],expected,modality)
    return session,subject,region,session['plan'].index(expected)

def public_scan(scan):
    sid=scan['id']
    if scan['modality']=='rgb':
        media={'original':f'/media/{sid}/original.jpg','skin_region':f'/media/{sid}/skin_region.png','overlay':f'/media/{sid}/rgb_overlay.png','redness_map':f'/media/{sid}/redness_map.png','pigmentation_map':f'/media/{sid}/pigmentation_map.png'}
    else:
        media={'original':f'/media/{sid}/original.jpg','overlay':f'/media/{sid}/overlay.png','artifact_mask':f'/media/{sid}/artifact_mask.png','porphyrin_mask':f'/media/{sid}/porphyrin_mask.png','dark_mask':f'/media/{sid}/dark_artifact_mask.png','light_mask':f'/media/{sid}/light_artifact_mask.png'}
    return {**scan,'media':media}

def public_session(session):
    if not session: return None
    subject=store.get_subject(session['subject_id'])
    completed=[x['region_code'] for x in session['items']]
    progress=session_progress(session['plan'],completed)
    items=[]
    for item in session['items']:
        scan=store.get_scan(item['scan_id'])
        items.append({**item,'scan':public_scan(scan) if scan else None})
    return {**session,'subject':subject,'progress':progress,'items':items}

@app.get('/health')
def health():
    return {'status':'ok','uv_model_available':MODEL_PATH.exists(),'model_available':MODEL_PATH.exists(),'uv_input_validator_available':True,'uv_input_validator_version':UVInputValidator.VERSION,'uv_input_profile':UVInputValidator.PROFILE,'rgb_engine_available':True,'rgb_engine_version':RGBAnalysisEngine.VERSION,'capture_protocol_version':RGBAnalysisEngine.CAPTURE_PROTOCOL_VERSION,'session_version':SESSION_VERSION,'model_path':str(MODEL_PATH),'data_dir':str(DATA_DIR),'api_version':'0.8.0'}

@app.get('/v1/subjects')
def list_subjects(): return store.list_subjects()

@app.post('/v1/subjects')
def create_subject(payload:SubjectPayload):
    clean=' '.join(payload.display_name.strip().split())[:80]
    if not clean: raise HTTPException(status_code=422,detail='Subject name is required')
    return store.create_subject(subject_id=uuid.uuid4().hex[:12],display_name=clean,created_at=datetime.now(timezone.utc).isoformat())

@app.get('/v1/regions')
def regions(modality:str|None=None):
    if modality not in (None,'uv','rgb'): raise HTTPException(status_code=400,detail='modality must be uv or rgb')
    return region_options(modality)

@app.post('/v1/sessions')
def create_session(payload:SessionPayload):
    modality=payload.modality.lower().strip()
    if modality not in ('uv','rgb'):
        raise HTTPException(status_code=422,detail='modality must be uv or rgb')
    subject=store.get_subject(payload.subject_id)
    if not subject:
        raise HTTPException(status_code=422,detail={'code':'subject_not_found','message':'Choose a valid subject profile before starting a session.'})
    plan=session_plan(modality)
    session=store.create_session(session_id=uuid.uuid4().hex[:16],created_at=datetime.now(timezone.utc).isoformat(),subject_id=subject['id'],modality=modality,plan=plan,session_version=SESSION_VERSION)
    return public_session(session)

@app.get('/v1/sessions')
def list_sessions(limit:int=30):
    return [public_session(x) for x in store.list_sessions(min(max(limit,1),100))]

@app.get('/v1/sessions/{session_id}')
def get_session(session_id:str):
    session=store.get_session(session_id)
    if not session: raise HTTPException(status_code=404,detail='Session not found')
    return public_session(session)

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

def comparable_rgb_reference(current_metrics:dict)->dict|None:
    version=str(current_metrics.get('rgb_engine_version'))
    tracking_key=current_metrics.get('tracking_series_key')
    if not tracking_key: return None
    for scan in store.list_scans(limit=100,modality='rgb'):
        m=scan.get('metrics',{})
        if m.get('tracking_series_key') != tracking_key: continue
        if str(m.get('rgb_engine_version')) != version: continue
        if not (m.get('longitudinal_eligible') is True or (m.get('longitudinal_eligible') is None and m.get('capture_quality')=='good')): continue
        if not isinstance(m.get('skin_luminance_median_0_255'),(int,float)): continue
        return m
    return None

@app.post('/v1/uv/analyze')
async def analyze_uv(
    image:UploadFile=File(...),
    subject_id:str|None=Form(None),
    region_code:str|None=Form(None),
    session_id:str|None=Form(None),
    subject_label:str|None=Form(None),
    anatomical_site:str|None=Form(None),
):
    session,subject,region,session_position=resolve_session_tracking(session_id,'uv',subject_id,region_code)
    rgb=decode_image(await image.read())
    validation=get_uv_validator().validate(rgb)
    if not validation.accepted:
        raise HTTPException(status_code=422,detail={'code':'uv_input_validation_failed','message':'This image does not appear compatible with the current UV fluorescence capture workflow. No UV analysis was run and the image was not saved.','uv_input_validation_score':validation.score,'validation_flags':validation.flags,'validation_guidance':validation.guidance,'validation_features':validation.features,'validator_version':validation.validator_version,'profile':validation.profile})
    result=get_uv_engine().analyze_rgb(rgb)
    result.metrics['uv_input_validation_version']=validation.validator_version
    result.metrics['uv_input_validation_profile']=validation.profile
    result.metrics['uv_input_validation_score']=validation.score
    result.metrics['uv_input_validation_flags']=validation.flags
    result.metrics['uv_input_validation_scope']=validation.features.get('validation_scope')
    result.metrics['uv_input_validation_does_not_verify_uv']=True
    stamp_tracking_metadata(result.metrics,subject=subject,region=region)
    legacy_subject=(subject or {}).get('display_name') or subject_label
    legacy_site=(region or {}).get('label') or anatomical_site
    stamp_uv_longitudinal_metadata(result.metrics,subject_label=legacy_subject,anatomical_site=legacy_site,model_signature=get_uv_model_signature(),validator_version=validation.validator_version,validator_profile=validation.profile)
    if not result.metrics.get('tracking_series_key'):
        result.metrics['uv_longitudinal_eligible']=False
        result.metrics['uv_longitudinal_reason']='structured_subject_and_region_required'
        result.metrics['uv_comparison_key']=None
    if session:
        result.metrics['scan_session_id']=session['id']
        result.metrics['scan_session_version']=session['session_version']
        result.metrics['scan_session_position']=session_position
    scan_id=uuid.uuid4().hex[:16]; created_at=datetime.now(timezone.utc).isoformat(); out_dir=SCAN_DIR/scan_id
    UVAnalysisEngine.save_result(result,out_dir); Image.fromarray(rgb).save(out_dir/'original.jpg',quality=92)
    store.add_scan(scan_id=scan_id,created_at=created_at,modality='uv',source_name=image.filename,metrics=result.metrics,media_dir=str(out_dir))
    response=public_scan(store.get_scan(scan_id))
    if session:
        updated=store.add_session_scan(session_id=session['id'],region_code=region['code'],scan_id=scan_id,position=session_position,created_at=created_at)
        response['session']=public_session(updated)
    return response

@app.post('/v1/rgb/analyze')
async def analyze_rgb(
    image:UploadFile=File(...),
    subject_id:str|None=Form(None),
    region_code:str|None=Form(None),
    session_id:str|None=Form(None),
):
    session,subject,region,session_position=resolve_session_tracking(session_id,'rgb',subject_id,region_code)
    rgb=decode_image(await image.read())
    try: result=get_rgb_engine().analyze_rgb(rgb)
    except ValueError as exc: raise HTTPException(status_code=422,detail=str(exc)) from exc
    stamp_tracking_metadata(result.metrics,subject=subject,region=region)
    reference=comparable_rgb_reference(result.metrics)
    if reference is not None:
        RGBAnalysisEngine.apply_reference_capture_quality(result.metrics,reference)
        result.metrics['reference_capture_used']=True
    else:
        result.metrics['reference_capture_used']=False
    if not result.metrics.get('tracking_series_key'):
        result.metrics['longitudinal_eligible']=False
        result.metrics['longitudinal_reason']='structured_subject_and_region_required'
    q=result.metrics
    if q.get('capture_quality')=='poor':
        guidance=q.get('quality_guidance',[]); guidance_text=' '.join(guidance)
        message='Capture quality is too low for a reliable RGB scan.' + (f' {guidance_text}' if guidance_text else ' Please retake the photo.')
        raise HTTPException(status_code=422,detail={'code':'capture_quality_failed','message':message,'capture_quality':q.get('capture_quality'),'capture_quality_score':q.get('capture_quality_score'),'quality_flags':q.get('quality_flags',[]),'quality_guidance':guidance,'quality_subscores':q.get('quality_subscores',{}),'reference_exposure_delta_ev':q.get('reference_exposure_delta_ev')})
    if session:
        result.metrics['scan_session_id']=session['id']
        result.metrics['scan_session_version']=session['session_version']
        result.metrics['scan_session_position']=session_position
    scan_id=uuid.uuid4().hex[:16]; created_at=datetime.now(timezone.utc).isoformat(); out_dir=SCAN_DIR/scan_id
    RGBAnalysisEngine.save_result(result,out_dir)
    store.add_scan(scan_id=scan_id,created_at=created_at,modality='rgb',source_name=image.filename,metrics=result.metrics,media_dir=str(out_dir))
    response=public_scan(store.get_scan(scan_id))
    if session:
        updated=store.add_session_scan(session_id=session['id'],region_code=region['code'],scan_id=scan_id,position=session_position,created_at=created_at)
        response['session']=public_session(updated)
    return response

@app.post('/v1/rgb/capture-check')
async def rgb_capture_check(image:UploadFile=File(...)):
    """Low-resolution, non-persistent face-size check for live RGB guidance."""
    rgb=decode_image(await image.read())
    engine=get_rgb_engine()
    face=engine._detect_largest_face(engine.face_detector,rgb)
    if face is None:
        return {'face_detected':False,'distance_state':'no_face','distance_label':'Center face','face_area_fraction':0.0,'capture_protocol_version':RGBAnalysisEngine.CAPTURE_PROTOCOL_VERSION}
    h,w=rgb.shape[:2]; _,_,fw,fh=face
    area=float((fw*fh)/max(1,h*w))
    if area<0.18: state,label='move_closer','Move closer'
    elif area>0.60: state,label='move_back','Move back'
    else: state,label='good','Distance good'
    return {'face_detected':True,'distance_state':state,'distance_label':label,'face_area_fraction':round(area,4),'capture_protocol_version':RGBAnalysisEngine.CAPTURE_PROTOCOL_VERSION}

if WEB_DIR.exists():
    app.mount('/app',StaticFiles(directory=WEB_DIR),name='app-assets')
    app.mount('/',StaticFiles(directory=WEB_DIR,html=True),name='web')
