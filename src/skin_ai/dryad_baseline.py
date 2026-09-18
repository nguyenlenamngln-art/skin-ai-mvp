from __future__ import annotations
import argparse, re
from pathlib import Path
import cv2, numpy as np, pandas as pd
from scipy.stats import pearsonr, spearmanr
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.model_selection import GroupKFold

def extract_proxy(path: str) -> dict:
    im=cv2.imread(path)
    if im is None: raise ValueError(f"cannot read {path}")
    h,w=im.shape[:2]
    # Stable normalized crop of the Visiopor processed-image panel in the photographed monitor.
    crop=im[int(.14*h):int(.58*h), int(.49*w):int(.90*w)]
    rgb=cv2.cvtColor(crop,cv2.COLOR_BGR2RGB).astype(np.float32)
    R,G,B=[rgb[:,:,i] for i in range(3)]
    excess=R-(G+B)/2
    lum=(R+G+B)/3
    panel=lum<180
    vals=excess[panel]
    if vals.size<100: vals=excess.ravel()
    med=np.median(vals); mad=np.median(np.abs(vals-med))+1.0
    z=(excess-med)/mad
    mask=((z>3)&panel&(R>80)).astype(np.uint8)
    n,_,stats,_=cv2.connectedComponentsWithStats(mask,8)
    areas=stats[1:,cv2.CC_STAT_AREA] if n>1 else np.array([])
    valid=(areas>=3)&(areas<=500)
    return {
        "spot_count_proxy":int(valid.sum()),
        "area_fraction_proxy":float(mask.mean()),
        "p99_red_excess":float(np.quantile(vals,.99)),
    }

def build_visit_features(manifest: pd.DataFrame) -> pd.DataFrame:
    rows=[]
    for _,r in manifest.iterrows():
        f=extract_proxy(r.path)
        f.update({"participant_id":r.participant_id,"visit":r.visit,"region":r.region})
        rows.append(f)
    region=pd.DataFrame(rows)
    return region.groupby(["participant_id","visit"]).agg(
        spot_count_proxy=("spot_count_proxy","sum"),
        area_fraction_proxy=("area_fraction_proxy","sum"),
        p99_red_excess=("p99_red_excess","sum"),
        n_regions=("region","nunique"),
    ).reset_index()

def grouped_cv(df: pd.DataFrame, target: str, folds=5) -> dict:
    X=df[["spot_count_proxy"]].to_numpy(); y=df[target].to_numpy(); g=df.participant_id.to_numpy()
    pred=np.full(len(df),np.nan)
    for tr,te in GroupKFold(n_splits=folds).split(X,y,g):
        m=LinearRegression().fit(X[tr],y[tr]); pred[te]=m.predict(X[te])
    return {
        "r2":r2_score(y,pred),
        "mae":mean_absolute_error(y,pred),
        "rmse":mean_squared_error(y,pred)**0.5,
        "pearson":pearsonr(y,pred)[0],
        "spearman":spearmanr(y,pred)[0],
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest",required=True)
    ap.add_argument("--labels",required=True)
    ap.add_argument("--out")
    args=ap.parse_args()
    man=pd.read_csv(args.manifest); lab=pd.read_csv(args.labels)
    visit=build_visit_features(man)
    df=lab.merge(visit,on=["participant_id","visit"])
    print(f"labeled visits: {len(df)}")
    print("raw spot proxy vs TPC:",pearsonr(df.spot_count_proxy,df.TPC)[0],spearmanr(df.spot_count_proxy,df.TPC)[0])
    print("raw spot proxy vs PSV:",pearsonr(df.spot_count_proxy,df.PSV)[0],spearmanr(df.spot_count_proxy,df.PSV)[0])
    for target in ["TPC","PSV"]: print(target,grouped_cv(df,target))
    if args.out: df.to_csv(args.out,index=False)
if __name__=="__main__": main()
