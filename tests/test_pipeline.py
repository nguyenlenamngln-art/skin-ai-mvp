from pathlib import Path
import tempfile
import numpy as np
import cv2
import pandas as pd
from skin_ai.porphyrin_baseline import analyze
from skin_ai.split_manifest import assign_subject_splits

def test_porphyrin_synthetic():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'uv.png'
        im=np.zeros((100,100,3),np.uint8)
        cv2.circle(im,(25,25),5,(0,80,255),-1)
        cv2.circle(im,(75,75),4,(0,40,230),-1)
        cv2.imwrite(str(p),im)
        r=analyze(p)
        assert r['porphyrin_component_count_proxy'] >= 2
        assert r['porphyrin_area_fraction_proxy'] > 0

def test_subject_split_no_leakage():
    rows=[]
    for s in range(20):
        for v in range(3): rows.append({'subject_id':f'subject_{s:03d}','x':v})
    out=assign_subject_splits(pd.DataFrame(rows),seed=7)
    assert out.groupby('subject_id').split.nunique().max()==1
