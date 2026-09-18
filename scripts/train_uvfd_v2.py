from __future__ import annotations

import argparse, csv, json, random, re
from pathlib import Path
import numpy as np
from PIL import Image, ImageEnhance, ImageOps

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler


def source_group(key: str) -> str:
    m = re.match(r"^crop_\d+_(.+)$", key, re.I)
    if m: return m.group(1)
    m = re.match(r"^(image\d+)_crop_\d+$", key, re.I)
    if m: return m.group(1)
    return re.sub(r"_crop_\d+$", "", key, flags=re.I)


def classify(path: Path) -> str:
    q = "/" + path.as_posix().lower().strip("/") + "/"
    if "/black_masks/" in q: return "black_mask"
    if "/white_masks/" in q: return "white_mask"
    if "/images/" in q: return "image"
    return "other"


def pair_key(path: Path) -> str:
    parts = list(path.parts); low = [x.lower() for x in parts]
    for folder in ("images", "black_masks", "white_masks"):
        if folder in low:
            i = low.index(folder)
            return Path(*parts[i+1:]).with_suffix("").as_posix()
    return path.stem


def build_pairs(root: Path):
    by = {}
    for p in root.rglob("*.png"):
        k = classify(p.relative_to(root))
        if k not in {"image","black_mask","white_mask"}: continue
        key = pair_key(p.relative_to(root))
        by.setdefault(key,{})[k]=p
    rows=[]
    for key,d in sorted(by.items()):
        if "image" not in d or ("black_mask" not in d and "white_mask" not in d): continue
        rows.append({
            "key":key, "source_group":source_group(key),
            "image":str(d["image"]),
            "black_mask":str(d.get("black_mask","")),
            "white_mask":str(d.get("white_mask","")),
            "has_black":int("black_mask" in d),
            "has_white":int("white_mask" in d),
        })
    return rows


def assign_splits(rows, seed=42):
    groups=sorted({r["source_group"] for r in rows})
    rng=random.Random(seed); rng.shuffle(groups)
    n=len(groups); ntr=round(n*.70); nv=round(n*.15)
    tr=set(groups[:ntr]); va=set(groups[ntr:ntr+nv]); te=set(groups[ntr+nv:])
    for r in rows:
        g=r["source_group"]
        r["split"]="train" if g in tr else "val" if g in va else "test"
    return rows


class DS(Dataset):
    def __init__(self, rows, size=256, augment=False, seed=42):
        self.rows=rows; self.size=size; self.augment=augment; self.seed=seed
    def __len__(self): return len(self.rows)
    def _mask(self,p):
        return Image.open(p).convert("L") if p else Image.new("L",(512,512),0)
    def __getitem__(self,i):
        r=self.rows[i]
        x=Image.open(r["image"]).convert("RGB")
        b=self._mask(r["black_mask"]); w=self._mask(r["white_mask"])
        if self.augment:
            rng=random.Random(random.randint(0,2**31-1)+i+self.seed)
            if rng.random()<.5:
                x=ImageOps.mirror(x); b=ImageOps.mirror(b); w=ImageOps.mirror(w)
            if rng.random()<.5:
                x=ImageOps.flip(x); b=ImageOps.flip(b); w=ImageOps.flip(w)
            k=rng.randrange(4)
            if k:
                a=90*k; x=x.rotate(a); b=b.rotate(a); w=w.rotate(a)
            if rng.random()<.8:
                x=ImageEnhance.Brightness(x).enhance(rng.uniform(.85,1.15))
            if rng.random()<.8:
                x=ImageEnhance.Contrast(x).enhance(rng.uniform(.85,1.15))
        x=x.resize((self.size,self.size),Image.Resampling.BILINEAR)
        b=b.resize((self.size,self.size),Image.Resampling.NEAREST)
        w=w.resize((self.size,self.size),Image.Resampling.NEAREST)
        xa=np.asarray(x,dtype=np.float32)/255.
        ya=np.stack([
            (np.asarray(b)>127).astype(np.float32),
            (np.asarray(w)>127).astype(np.float32)
        ])
        return torch.from_numpy(xa.transpose(2,0,1)), torch.from_numpy(ya), r["key"]


class Block(nn.Module):
    def __init__(self,a,b):
        super().__init__()
        self.net=nn.Sequential(
            nn.Conv2d(a,b,3,padding=1,bias=False),nn.BatchNorm2d(b),nn.SiLU(inplace=True),
            nn.Conv2d(b,b,3,padding=1,bias=False),nn.BatchNorm2d(b),nn.SiLU(inplace=True))
    def forward(self,x): return self.net(x)


class UNet(nn.Module):
    def __init__(self,base=16):
        super().__init__()
        self.e1=Block(3,base); self.e2=Block(base,base*2); self.e3=Block(base*2,base*4)
        self.p=nn.MaxPool2d(2); self.b=Block(base*4,base*8)
        self.u3=nn.ConvTranspose2d(base*8,base*4,2,2); self.d3=Block(base*8,base*4)
        self.u2=nn.ConvTranspose2d(base*4,base*2,2,2); self.d2=Block(base*4,base*2)
        self.u1=nn.ConvTranspose2d(base*2,base,2,2); self.d1=Block(base*2,base)
        self.out=nn.Conv2d(base,2,1)
    def forward(self,x):
        e1=self.e1(x); e2=self.e2(self.p(e1)); e3=self.e3(self.p(e2)); b=self.b(self.p(e3))
        d3=self.d3(torch.cat([self.u3(b),e3],1))
        d2=self.d2(torch.cat([self.u2(d3),e2],1))
        d1=self.d1(torch.cat([self.u1(d2),e1],1))
        return self.out(d1)


def focal_bce(logits,target,gamma=2.0):
    bce=F.binary_cross_entropy_with_logits(logits,target,reduction="none")
    p=torch.sigmoid(logits)
    pt=torch.where(target>0.5,p,1-p)
    return (((1-pt)**gamma)*bce).mean()


def focal_tversky(logits,target,alpha=.3,beta=.7,gamma=.75,eps=1.):
    p=torch.sigmoid(logits); dims=(0,2,3)
    tp=(p*target).sum(dims); fp=(p*(1-target)).sum(dims); fn=((1-p)*target).sum(dims)
    t=(tp+eps)/(tp+alpha*fp+beta*fn+eps)
    return ((1-t)**gamma).mean()


def loss_fn(logits,target):
    # Slightly emphasize sparse light-artifact channel.
    weight=torch.tensor([1.0,1.35],device=logits.device).view(1,2,1,1)
    return .35*focal_bce(logits*weight,target) + .65*focal_tversky(logits*weight,target)


@torch.no_grad()
def metric_at_thresholds(model,loader,device,thresholds):
    model.eval()
    tp=np.zeros(2); fp=np.zeros(2); fn=np.zeros(2)
    th=torch.tensor(thresholds,device=device).view(1,2,1,1)
    for x,y,_ in loader:
        x=x.to(device); y=y.to(device)>0.5
        p=torch.sigmoid(model(x))>=th
        for c in range(2):
            pc=p[:,c]; tc=y[:,c]
            tp[c]+=(pc&tc).sum().item(); fp[c]+=(pc&~tc).sum().item(); fn[c]+=(~pc&tc).sum().item()
    dice=(2*tp+1)/(2*tp+fp+fn+1); iou=(tp+1)/(tp+fp+fn+1)
    precision=(tp+1)/(tp+fp+1); recall=(tp+1)/(tp+fn+1)
    return {
        "dark_dice":float(dice[0]),"light_dice":float(dice[1]),"macro_dice":float(dice.mean()),
        "dark_iou":float(iou[0]),"light_iou":float(iou[1]),"macro_iou":float(iou.mean()),
        "dark_precision":float(precision[0]),"light_precision":float(precision[1]),
        "dark_recall":float(recall[0]),"light_recall":float(recall[1]),
    }


@torch.no_grad()
def tune_thresholds(model,loader,device):
    grid=[.15,.2,.25,.3,.35,.4,.45,.5,.55,.6,.65,.7]
    best=[(.5,-1),(.5,-1)]
    for c in (0,1):
        for t in grid:
            th=[.5,.5]; th[c]=t
            m=metric_at_thresholds(model,loader,device,th)
            d=m["dark_dice"] if c==0 else m["light_dice"]
            if d>best[c][1]: best[c]=(t,d)
    return [best[0][0],best[1][0]],{"dark_val_dice":best[0][1],"light_val_dice":best[1][1]}


def save_samples(model,loader,device,thresholds,out,limit=12):
    out.mkdir(parents=True,exist_ok=True); n=0
    th=torch.tensor(thresholds,device=device).view(1,2,1,1)
    model.eval()
    with torch.no_grad():
        for x,y,keys in loader:
            prob=torch.sigmoid(model(x.to(device))); pred=(prob>=th).cpu().numpy(); ya=y.numpy()
            xx=(x.numpy()*255).clip(0,255).astype(np.uint8)
            for i,key in enumerate(keys):
                img=xx[i].transpose(1,2,0); gt=np.zeros_like(img); pr=np.zeros_like(img)
                gt[...,0]=(ya[i,0]*255).astype(np.uint8); gt[...,1]=(ya[i,1]*255).astype(np.uint8)
                pr[...,0]=pred[i,0].astype(np.uint8)*255; pr[...,1]=pred[i,1].astype(np.uint8)*255
                canvas=Image.new("RGB",(img.shape[1]*3,img.shape[0]))
                canvas.paste(Image.fromarray(img),(0,0)); canvas.paste(Image.fromarray(gt),(img.shape[1],0)); canvas.paste(Image.fromarray(pr),(img.shape[1]*2,0))
                safe=re.sub(r"[^A-Za-z0-9_.-]+","_",key)[-100:]
                canvas.save(out/f"{n:03d}_{safe}.png"); n+=1
                if n>=limit:return


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",required=True); ap.add_argument("--out",default="artifacts/uvfd_train_v2")
    ap.add_argument("--size",type=int,default=256); ap.add_argument("--batch",type=int,default=8)
    ap.add_argument("--epochs",type=int,default=6); ap.add_argument("--base",type=int,default=16)
    ap.add_argument("--lr",type=float,default=1e-3); ap.add_argument("--seed",type=int,default=42)
    ap.add_argument("--light-oversample",type=float,default=3.0)
    args=ap.parse_args()

    random.seed(args.seed); np.random.seed(args.seed); torch.manual_seed(args.seed)
    torch.set_num_threads(max(1,min(4,torch.get_num_threads())))
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)

    rows=assign_splits(build_pairs(Path(args.root)),args.seed)
    with (out/"manifest.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    tr=[r for r in rows if r["split"]=="train"]; va=[r for r in rows if r["split"]=="val"]; te=[r for r in rows if r["split"]=="test"]
    train_ds=DS(tr,args.size,True,args.seed); val_ds=DS(va,args.size); test_ds=DS(te,args.size)
    weights=[args.light_oversample if r["has_white"] else 1.0 for r in tr]
    sampler=WeightedRandomSampler(weights,num_samples=len(tr),replacement=True)
    train_dl=DataLoader(train_ds,batch_size=args.batch,sampler=sampler,num_workers=2)
    val_dl=DataLoader(val_ds,batch_size=args.batch,shuffle=False,num_workers=2)
    test_dl=DataLoader(test_ds,batch_size=args.batch,shuffle=False,num_workers=2)

    device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model=UNet(args.base).to(device); opt=torch.optim.AdamW(model.parameters(),lr=args.lr,weight_decay=2e-4)
    sched=torch.optim.lr_scheduler.CosineAnnealingLR(opt,T_max=args.epochs)
    history=[]; best=-1.; best_path=out/"uvfd_unet_v2_best.pt"

    for epoch in range(1,args.epochs+1):
        model.train(); losses=[]
        for x,y,_ in train_dl:
            x=x.to(device); y=y.to(device); opt.zero_grad(set_to_none=True)
            logits=model(x); loss=loss_fn(logits,y); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(),1.0); opt.step(); losses.append(float(loss.item()))
        sched.step()
        th,tuned=tune_thresholds(model,val_dl,device)
        vm=metric_at_thresholds(model,val_dl,device,th)
        rec={"epoch":epoch,"train_loss":float(np.mean(losses)),"thresholds":th,**{f"val_{k}":v for k,v in vm.items()}}
        history.append(rec); print(json.dumps(rec))
        if vm["macro_dice"]>best:
            best=vm["macro_dice"]
            torch.save({"model_state":model.state_dict(),"config":vars(args),"thresholds":th,"classes":["dark_hair_ruler","light_hair_uv_particles"],"best_val_macro_dice":best},best_path)

    ckpt=torch.load(best_path,map_location=device); model.load_state_dict(ckpt["model_state"]); th=ckpt["thresholds"]
    val=metric_at_thresholds(model,val_dl,device,th); test=metric_at_thresholds(model,test_dl,device,th)
    save_samples(model,test_dl,device,th,out/"sample_predictions",12)

    counts={s:{"samples":len([r for r in rows if r["split"]==s]),"groups":len({r["source_group"] for r in rows if r["split"]==s})} for s in ("train","val","test")}
    result={"device":str(device),"counts":counts,"thresholds":th,"validation":val,"test":test,"history":history,
            "note":"Development benchmark. Split is held out by inferred source photograph group; not external clinical validation."}
    (out/"metrics.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=="__main__": main()
