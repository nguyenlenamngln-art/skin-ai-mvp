from __future__ import annotations
import argparse, hashlib, re
from pathlib import Path
from typing import Optional
import pandas as pd
from PIL import Image

IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.tif', '.tiff', '.bmp', '.webp'}
REGIONS = {
    'mentalis': ['mentalis', 'mental', 'chin', '_m_', '-m-'],
    'right_cheek': ['right cheek', 'right_cheek', 'rcheek', '_rc_', '-rc-'],
    'right_forehead': ['right forehead', 'right_forehead', 'rforehead', '_rf_', '-rf-'],
    'left_forehead': ['left forehead', 'left_forehead', 'lforehead', '_lf_', '-lf-'],
    'left_cheek': ['left cheek', 'left_cheek', 'lcheek', '_lc_', '-lc-'],
}
VISITS = {
    'baseline': ['baseline', 'pre', 'visit 1', 'visit_1', 'v1'],
    'week_6': ['week 6', 'week_6', 'post', 'endpoint', 'visit 2', 'visit_2', 'v2'],
    'week_10': ['week 10', 'week_10', 'follow', 'follow-up', 'follow_up', 'visit 3', 'visit_3', 'v3'],
}

def _contains_any(text: str, tokens: list[str]) -> bool:
    return any(t in text for t in tokens)

def infer_visit(text: str) -> Optional[str]:
    t = text.lower().replace('\\', '/')
    for name, tokens in VISITS.items():
        if _contains_any(t, tokens): return name
    return None

def infer_region(text: str) -> Optional[str]:
    t = text.lower().replace('\\', '/')
    for name, tokens in REGIONS.items():
        if _contains_any(t, tokens): return name
    return None

def infer_modality(text: str, dataset_id: str) -> str:
    t = text.lower().replace('\\', '/')
    if any(x in t for x in ['sebum', 'sm815', 'sm 815']): return 'sebumetry'
    if any(x in t for x in ['visiopor', 'fluores', 'porphyr']): return 'uva_fluorescence'
    if any(x in t for x in ['polarized', 'polarised', '/pd/', '_pd_', 'cross-pol', 'cross_pol']): return 'polarized'
    if any(x in t for x in ['365nm', '365 nm', 'uvfd', 'ultraviolet', '/uv/']): return 'uv365'
    if dataset_id == 'mendeley_uvfd_artifacts': return 'uvfd'
    return 'unknown'

def infer_subject(path: Path) -> str:
    joined = '/'.join(path.parts)
    patterns = [r'(?:participant|patient|subject|person|pt)[ _-]*([0-9]{1,4})', r'\bp([0-9]{2,4})\b']
    for pat in patterns:
        m = re.search(pat, joined, re.I)
        if m: return f"subject_{int(m.group(1)):03d}"
    for part in path.parts:
        if re.fullmatch(r'\d{1,4}', part): return f"subject_{int(part):03d}"
    return 'subject_unknown'

def image_size(path: Path):
    try:
        with Image.open(path) as im: return im.width, im.height
    except Exception:
        return None, None

def make_id(dataset_id: str, rel: str) -> str:
    return hashlib.sha1(f'{dataset_id}:{rel}'.encode()).hexdigest()[:16]

def build_manifest(root: Path, dataset_id: str, license_name: str, source_url: str) -> pd.DataFrame:
    rows=[]
    for p in sorted(root.rglob('*')):
        if not p.is_file() or p.suffix.lower() not in IMAGE_EXTS: continue
        rel = p.relative_to(root).as_posix()
        w,h=image_size(p)
        text=rel.lower()
        label_type = 'artifact_mask' if any(k in text for k in ['mask', 'black_masks', 'white_masks']) else None
        rows.append({
            'dataset_id':dataset_id,
            'sample_id':make_id(dataset_id, rel),
            'subject_id':infer_subject(Path(rel)),
            'visit':infer_visit(rel),
            'region':infer_region(rel),
            'modality':infer_modality(rel,dataset_id),
            'path':str(p.resolve()),
            'width':w,'height':h,
            'label_path':str(p.resolve()) if label_type else None,
            'label_type':label_type,
            'license':license_name,
            'source_url':source_url,
            'split':'unassigned',
            'notes':None,
        })
    return pd.DataFrame(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--dataset-id', required=True)
    ap.add_argument('--license', required=True)
    ap.add_argument('--source-url', required=True)
    ap.add_argument('--out', required=True)
    args=ap.parse_args()
    df=build_manifest(Path(args.root),args.dataset_id,args.license,args.source_url)
    Path(args.out).parent.mkdir(parents=True,exist_ok=True)
    df.to_csv(args.out,index=False)
    print(f'wrote {len(df)} image rows -> {args.out}')
    if len(df): print(df['modality'].value_counts(dropna=False).to_string())
if __name__=='__main__': main()
