from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from PIL import Image
import torch

# Reuse model architecture from the training module.
from scripts.train_uvfd_v2 import UNet

def load_model(checkpoint: Path, device):
    ckpt=torch.load(checkpoint,map_location=device)
    model=UNet(ckpt["config"].get("base",16)).to(device)
    model.load_state_dict(ckpt["model_state"]); model.eval()
    return model,ckpt.get("thresholds",[.5,.5]),ckpt

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("image"); ap.add_argument("--checkpoint",required=True); ap.add_argument("--out-dir",required=True)
    args=ap.parse_args()
    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model,th,ckpt=load_model(Path(args.checkpoint),device)
    size=int(ckpt["config"].get("size",256))
    original=Image.open(args.image).convert("RGB"); resized=original.resize((size,size),Image.Resampling.BILINEAR)
    x=torch.from_numpy((np.asarray(resized,dtype=np.float32)/255.).transpose(2,0,1))[None].to(device)
    with torch.no_grad(): p=torch.sigmoid(model(x))[0].cpu().numpy()
    dark=p[0]>=th[0]; light=p[1]>=th[1]; artifact=dark|light
    # Nearest-neighbor resize of binary masks back to original resolution.
    mask=Image.fromarray((artifact*255).astype(np.uint8)).resize(original.size,Image.Resampling.NEAREST)
    darkim=Image.fromarray((dark*255).astype(np.uint8)).resize(original.size,Image.Resampling.NEAREST)
    lightim=Image.fromarray((light*255).astype(np.uint8)).resize(original.size,Image.Resampling.NEAREST)
    arr=np.asarray(original).copy(); m=np.asarray(mask)>127
    # Cleaning output is conservative: black out artifacts instead of hallucinating skin.
    arr[m]=0
    out=Path(args.out_dir); out.mkdir(parents=True,exist_ok=True)
    mask.save(out/"artifact_mask.png"); darkim.save(out/"dark_mask.png"); lightim.save(out/"light_mask.png")
    Image.fromarray(arr).save(out/"masked_uv.png")
    meta={"thresholds":th,"artifact_area_fraction":float(m.mean()),"policy":"artifact pixels excluded/blackened; no inpainting"}
    (out/"metrics.json").write_text(json.dumps(meta,indent=2)); print(json.dumps(meta,indent=2))

if __name__=="__main__": main()
