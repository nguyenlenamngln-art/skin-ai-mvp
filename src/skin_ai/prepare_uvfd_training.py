from __future__ import annotations
import argparse, csv, re, zipfile
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

def source_group(key: str) -> str:
    key=str(key)
    m=re.match(r"^crop_\d+_(.+)$",key,re.I)
    if m: return m.group(1)
    m=re.match(r"^(image\d+)_crop_\d+$",key,re.I)
    if m: return m.group(1)
    return re.sub(r"_crop_\d+$","",key,flags=re.I)

def patient_hint(group: str):
    m=re.search(r"(?:^|_)p0?(\d+)(?:_|$)",group,re.I)
    return int(m.group(1)) if m else None

def assign_group_splits(df: pd.DataFrame, seed=42) -> pd.DataFrame:
    groups=np.array(sorted(df.source_group.unique()))
    gss=GroupShuffleSplit(n_splits=1,test_size=0.15,random_state=seed)
    trainval_idx,test_idx=next(gss.split(groups,groups=groups))
    trainval=groups[trainval_idx]; test=set(groups[test_idx])
    gss2=GroupShuffleSplit(n_splits=1,test_size=0.1764705882,random_state=seed+1) # ~15% overall
    tr_idx,val_idx=next(gss2.split(trainval,groups=trainval))
    train=set(trainval[tr_idx]); val=set(trainval[val_idx])
    def f(g):
        if g in train:return "train"
        if g in val:return "val"
        if g in test:return "test"
        raise RuntimeError(g)
    out=df.copy(); out["split"]=out.source_group.map(f)
    return out

def build_manifest(zip_path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path) as z:
        files=[n for n in z.namelist() if not n.endswith("/")]
    def kind(p):
        q=p.lower().replace("\\","/")
        if "/black_masks/" in "/"+q:return "black_mask"
        if "/white_masks/" in "/"+q:return "white_mask"
        if "/images/" in "/"+q:return "image"
        return "other"
    def key(p):
        p=p.replace("\\","/"); parts=p.split("/"); low=[x.lower() for x in parts]
        for folder in ("images","black_masks","white_masks"):
            if folder in low:
                i=low.index(folder)
                return str(Path("/".join(parts[i+1:])).with_suffix("")).replace("\\","/")
        return Path(p).stem
    d={}
    for p in files:
        k=kind(p)
        if k not in {"image","black_mask","white_mask"}: continue
        kk=key(p); d.setdefault(kk,{})[k]=p
    rows=[]
    for kk,x in sorted(d.items()):
        if "image" not in x: continue
        if "black_mask" not in x and "white_mask" not in x: continue
        sg=source_group(kk)
        rows.append({
            "key":kk,"source_group":sg,"patient_hint":patient_hint(sg),
            "image":x.get("image"),"black_mask":x.get("black_mask"),"white_mask":x.get("white_mask"),
            "has_black_mask":"black_mask" in x,"has_white_mask":"white_mask" in x,
        })
    return assign_group_splits(pd.DataFrame(rows))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("zip")
    ap.add_argument("--out",default="data/interim/uvfd_training_manifest.csv")
    args=ap.parse_args()
    df=build_manifest(Path(args.zip))
    Path(args.out).parent.mkdir(parents=True,exist_ok=True)
    df.to_csv(args.out,index=False)
    print("samples",len(df))
    print("source groups",df.source_group.nunique())
    print(df.groupby("split").agg(samples=("key","size"),source_groups=("source_group","nunique")).to_string())
    print("black masks",int(df.has_black_mask.sum()),"white masks",int(df.has_white_mask.sum()))
if __name__=="__main__":main()
