from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

def assign_subject_splits(df: pd.DataFrame, train=0.70, val=0.15, seed=42) -> pd.DataFrame:
    if train <= 0 or val < 0 or train + val >= 1: raise ValueError('invalid split proportions')
    subjects=np.array(sorted(s for s in df.subject_id.dropna().unique() if s != 'subject_unknown'))
    rng=np.random.default_rng(seed); rng.shuffle(subjects)
    n=len(subjects); n_train=int(round(n*train)); n_val=int(round(n*val))
    train_s=set(subjects[:n_train]); val_s=set(subjects[n_train:n_train+n_val]); test_s=set(subjects[n_train+n_val:])
    out=df.copy()
    def f(s):
        if s in train_s:return 'train'
        if s in val_s:return 'val'
        if s in test_s:return 'test'
        return 'unassigned'
    out['split']=out.subject_id.map(f)
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--manifest',required=True); ap.add_argument('--out',required=True); ap.add_argument('--seed',type=int,default=42)
    args=ap.parse_args(); df=pd.read_csv(args.manifest); out=assign_subject_splits(df,seed=args.seed); out.to_csv(args.out,index=False)
    print(out.groupby(['split','subject_id']).size().groupby(level=0).size())
if __name__=='__main__':main()
