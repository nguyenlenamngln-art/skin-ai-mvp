from __future__ import annotations
import argparse, json
from pathlib import Path
import cv2
import numpy as np

def porphyrin_mask_bgr(img: np.ndarray, min_sat: int=75, min_val: int=45, hue_lo: int=0, hue_hi: int=25) -> np.ndarray:
    hsv=cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h,s,v=cv2.split(hsv)
    warm=((h>=hue_lo)&(h<=hue_hi)&(s>=min_sat)&(v>=min_val)).astype(np.uint8)*255
    kernel=np.ones((2,2),np.uint8)
    return cv2.morphologyEx(warm, cv2.MORPH_OPEN, kernel)

def connected_components(mask: np.ndarray, min_area: int=3, max_area: int=5000):
    n, labels, stats, cent=cv2.connectedComponentsWithStats((mask>0).astype(np.uint8), 8)
    comps=[]
    for i in range(1,n):
        area=int(stats[i,cv2.CC_STAT_AREA])
        if min_area<=area<=max_area:
            comps.append({'x':float(cent[i][0]),'y':float(cent[i][1]),'area_px':area})
    return comps

def analyze(path: Path):
    img=cv2.imread(str(path),cv2.IMREAD_COLOR)
    if img is None: raise ValueError(f'cannot read image: {path}')
    mask=porphyrin_mask_bgr(img)
    comps=connected_components(mask)
    coverage=float((mask>0).mean())
    rgb=cv2.cvtColor(img,cv2.COLOR_BGR2RGB).astype(np.float32)/255.0
    red=rgb[:,:,0]
    intensity=float(red[mask>0].mean()) if np.any(mask>0) else 0.0
    return {'image':str(path),'width':img.shape[1],'height':img.shape[0],
            'porphyrin_component_count_proxy':len(comps),
            'porphyrin_area_fraction_proxy':coverage,
            'porphyrin_red_intensity_proxy':intensity,
            'components':comps}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('image'); ap.add_argument('--json-out'); ap.add_argument('--mask-out')
    args=ap.parse_args(); result=analyze(Path(args.image)); print(json.dumps(result,indent=2))
    if args.json_out: Path(args.json_out).write_text(json.dumps(result,indent=2))
    if args.mask_out:
        img=cv2.imread(args.image); cv2.imwrite(args.mask_out,porphyrin_mask_bgr(img))
if __name__=='__main__':main()
