from __future__ import annotations
import argparse, hashlib, re, shutil, zipfile
from pathlib import Path
import pandas as pd

REGIONS={"M":"mentalis","RC":"right_cheek","RF":"right_forehead","LF":"left_forehead","LC":"left_cheek"}

def _visit(path: str):
    s=path.lower()
    if "baseline" in s: return "baseline"
    if "week 6" in s: return "week_6"
    if "week 10" in s: return "week_10"
    return None

def extract_outer_zip(outer_zip: Path, out_dir: Path) -> tuple[Path,Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(outer_zip) as z: z.extractall(out_dir)
    inner=out_dir/"Raw_images_files_of_measurements_Dryad.zip"
    raw=out_dir/"raw_images"
    if raw.exists(): shutil.rmtree(raw)
    raw.mkdir()
    with zipfile.ZipFile(inner) as z: z.extractall(raw)
    return raw, out_dir/"CAP_acne.html"

def build_visiopor_manifest(raw_root: Path) -> pd.DataFrame:
    rows=[]
    for p in raw_root.rglob("*.jpg"):
        if "__MACOSX" in p.parts or "Visiopor" not in str(p): continue
        region=REGIONS.get(p.stem.strip())
        if not region: continue
        m=re.search(r"Pat\s*(\d+)",str(p),re.I)
        if not m: continue
        rows.append({
            "dataset_id":"dryad_cap_acne",
            "sample_id":hashlib.sha1(str(p).encode()).hexdigest()[:16],
            "subject_id":f"subject_{int(m.group(1)):03d}",
            "participant_id":int(m.group(1)),
            "visit":_visit(str(p)),
            "region":region,
            "modality":"uva_fluorescence_screenshot",
            "path":str(p.resolve()),
            "license":"CC0",
        })
    return pd.DataFrame(rows).sort_values(["participant_id","visit","region"]).reset_index(drop=True)

def read_visit_labels(html: Path) -> pd.DataFrame:
    dat=pd.read_html(html)[0]
    rows=[]
    for _,r in dat.iterrows():
        pid=int(r["ID"])
        for visit,suf in [("baseline","Baseline"),("week_6","Endpoint"),("week_10","Follow_up")]:
            tpc=r[f"TPC_{suf}"]; psv=r[f"PSV_{suf}"]
            if pd.notna(tpc) and pd.notna(psv):
                rows.append({"participant_id":pid,"visit":visit,"TPC":float(tpc),"PSV":float(psv)})
    return pd.DataFrame(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("outer_zip")
    ap.add_argument("--work-dir",default="data/interim/dryad_cap_acne")
    args=ap.parse_args()
    work=Path(args.work_dir)
    raw,html=extract_outer_zip(Path(args.outer_zip),work)
    manifest=build_visiopor_manifest(raw)
    labels=read_visit_labels(html)
    work.mkdir(parents=True,exist_ok=True)
    manifest.to_csv(work/"visio_manifest.csv",index=False)
    labels.to_csv(work/"visit_labels.csv",index=False)
    print(f"Visiopor labeled screenshots: {len(manifest)}")
    print(manifest.groupby("visit").size().to_string())
    print(f"Ground-truth labeled visits: {len(labels)}")
if __name__=="__main__": main()
