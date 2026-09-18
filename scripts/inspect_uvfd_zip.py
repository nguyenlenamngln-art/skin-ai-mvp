from __future__ import annotations
import csv, hashlib, json, random, zipfile
from collections import Counter, defaultdict
from pathlib import Path

ZIP=Path("uvfd.zip")
OUT=Path("artifacts/uvfd_inspection")
SAMPLES=OUT/"samples"
OUT.mkdir(parents=True,exist_ok=True); SAMPLES.mkdir(parents=True,exist_ok=True)

def norm(p:str)->str:
    return p.replace("\\","/").strip("/")

def kind(p:str)->str:
    q=norm(p).lower()
    if "/black_masks/" in f"/{q}/" or q.startswith("black_masks/"): return "black_mask"
    if "/white_masks/" in f"/{q}/" or q.startswith("white_masks/"): return "white_mask"
    if "/images/" in f"/{q}/" or q.startswith("images/"): return "image"
    return "other"

def key_for(p:str)->str:
    q=norm(p)
    stem=Path(q).stem
    # Pair by basename first; preserve any nested relative subpath after modality folder if present.
    parts=q.split("/")
    low=[x.lower() for x in parts]
    for folder in ("images","black_masks","white_masks"):
        if folder in low:
            i=low.index(folder)
            rel="/".join(parts[i+1:])
            return str(Path(rel).with_suffix("")).replace("\\","/")
    return stem

with zipfile.ZipFile(ZIP) as z:
    infos=[i for i in z.infolist() if not i.is_dir()]
    rows=[]
    bykey=defaultdict(dict)
    ext_counts=Counter()
    folder_counts=Counter()
    for info in infos:
        p=norm(info.filename); k=kind(p); key=key_for(p)
        ext_counts[Path(p).suffix.lower()]+=1
        folder_counts[k]+=1
        if k in {"image","black_mask","white_mask"}:
            bykey[key][k]=p
        rows.append({"path":p,"kind":k,"key":key,"size":info.file_size,"crc":info.CRC})
    pairs=[]
    for key,d in sorted(bykey.items()):
        pairs.append({
            "key":key,
            "image":d.get("image"),
            "black_mask":d.get("black_mask"),
            "white_mask":d.get("white_mask"),
            "has_image":bool(d.get("image")),
            "has_black_mask":bool(d.get("black_mask")),
            "has_white_mask":bool(d.get("white_mask")),
        })
    good=[p for p in pairs if p["has_image"] and (p["has_black_mask"] or p["has_white_mask"])]
    only_black=[p for p in good if p["has_black_mask"] and not p["has_white_mask"]]
    only_white=[p for p in good if p["has_white_mask"] and not p["has_black_mask"]]
    both=[p for p in good if p["has_black_mask"] and p["has_white_mask"]]
    missing_image=[p for p in pairs if not p["has_image"] and (p["has_black_mask"] or p["has_white_mask"])]
    images_without_mask=[p for p in pairs if p["has_image"] and not (p["has_black_mask"] or p["has_white_mask"])]
    summary={
      "zip_bytes":ZIP.stat().st_size,
      "files_total":len(infos),
      "folder_counts":dict(folder_counts),
      "extensions":dict(ext_counts),
      "unique_keys":len(pairs),
      "usable_pairs":len(good),
      "black_only_pairs":len(only_black),
      "white_only_pairs":len(only_white),
      "both_mask_pairs":len(both),
      "masks_without_image":len(missing_image),
      "images_without_mask":len(images_without_mask),
    }
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2))
    with (OUT/"manifest.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(pairs[0].keys()) if pairs else ["key"])
        w.writeheader(); w.writerows(pairs)
    with (OUT/"all_files.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["path","kind","key","size","crc"])
        w.writeheader(); w.writerows(rows)
    # Deterministic small sample artifact: extract 8 black + 8 white + up to 4 both.
    rng=random.Random(42)
    chosen=[]
    for pool,n in [(only_black,8),(only_white,8),(both,4)]:
        chosen.extend(rng.sample(pool,min(n,len(pool))))
    for idx,pair in enumerate(chosen):
        for k in ("image","black_mask","white_mask"):
            src=pair.get(k)
            if not src: continue
            suffix=Path(src).suffix.lower()
            dest=SAMPLES/f"{idx:02d}_{k}{suffix}"
            with z.open(src) as rf, dest.open("wb") as wf: wf.write(rf.read())
    print(json.dumps(summary,indent=2))
