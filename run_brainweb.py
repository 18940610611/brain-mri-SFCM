from pathlib import Path
from itertools import product
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / ".deps"))
import argparse, gzip, time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
from fcm_core import fcm

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "brainweb"
SHAPE = (181, 217, 181)
LABELS = {1: "CSF", 2: "GM", 3: "WM"}

def raw_bytes(path):
    path = Path(path)
    if path.suffix == ".gz":
        with gzip.open(path, "rb") as f: return f.read()
    return path.read_bytes()

def load_volume(path):
    path = Path(path)
    if ".nii" in path.name or path.suffix == ".mnc":
        import nibabel as nib
        return np.asarray(nib.load(str(path)).get_fdata())
    b = raw_bytes(path)
    expected = int(np.prod(SHAPE))
    if len(b) != expected:
        raise ValueError(f"{path.name}: {len(b)} bytes, expected {expected}. Check format/dimensions.")
    return np.frombuffer(b, dtype=np.uint8).reshape(SHAPE, order="F")

def get_slice(vol, axis, index):
    return np.take(vol, index, axis=axis)

def align_labels(pred, gt, mask, n=3):
    cost = np.zeros((n, n), dtype=np.int64)
    for p in range(n):
        for g in range(n): cost[p, g] = -np.sum((pred[mask] == p) & (gt[mask] == g))
    rows, cols = linear_sum_assignment(cost)
    out = np.full(pred.shape, -1, dtype=np.int16)
    for p, g in zip(rows, cols): out[pred == p] = g
    return out

def scores(gt, pred, mask):
    dice, iou = [], []
    for k in range(3):
        a=(gt==k)&mask; b=(pred==k)&mask; inter=np.logical_and(a,b).sum()
        dice.append(2*inter/(a.sum()+b.sum()+1e-12)); iou.append(inter/(np.logical_or(a,b).sum()+1e-12))
    return {"dice_csf":dice[0],"dice_gm":dice[1],"dice_wm":dice[2],
            "mean_dice":np.mean(dice),"mean_iou":np.mean(iou),
            "ari":adjusted_rand_score(gt[mask],pred[mask]),
            "nmi":normalized_mutual_info_score(gt[mask],pred[mask])}

def run_one(image, truth, axis, index, method, seed, m=2, alpha=1.5, window=3):
    img=get_slice(image,axis,index).astype(float); lab=get_slice(truth,axis,index).astype(int)
    mask=np.isin(lab,[1,2,3]); gt=lab-1
    vals=img[mask]; lo,hi=np.percentile(vals,[1,99]); img=np.clip((img-lo)/(hi-lo+1e-12),0,1)
    start=time.perf_counter(); maps=None; centers=None; hist=None
    if method=="K-Means":
        km=KMeans(3,n_init=10,random_state=seed).fit(img[mask,None])
        pred=np.full(img.shape,-1,dtype=np.int16); pred[mask]=km.labels_; centers=km.cluster_centers_[:,0]
    elif method=="FCM": pred,centers,maps,hist,_=fcm(img,mask,m=m,alpha=0,seed=seed)
    else: pred,centers,maps,hist,_=fcm(img,mask,m=m,alpha=alpha,window=window,seed=seed)
    elapsed=time.perf_counter()-start
    pred=align_labels(pred,gt,mask)
    out=scores(gt,pred,mask); out["seconds"]=elapsed
    return out,(img,gt,pred,mask,centers,maps,hist)

def check_files():
    names=["t1_icbm_normal_1mm_pn0_rf20.rawb.gz","t1_icbm_normal_1mm_pn3_rf20.rawb.gz","t1_icbm_normal_1mm_pn5_rf20.rawb.gz","t1_icbm_normal_1mm_pn9_rf20.rawb.gz","t1_icbm_normal_1mm_pn3_rf0.rawb.gz","t1_icbm_normal_1mm_pn3_rf40.rawb.gz","phantom_1.0mm_normal_crisp.rawb.gz"]
    missing=[n for n in names if not (DATA/n).exists()]
    if missing: raise FileNotFoundError("Missing:\n"+"\n".join(str(DATA/n) for n in missing))
    for n in names: load_volume(DATA/n); print("OK",n)

def main():
    global DATA
    ap=argparse.ArgumentParser(); ap.add_argument('--check-only',action='store_true'); ap.add_argument('--suite',choices=['noise','rf','params'])
    ap.add_argument('--data-dir',default=str(DATA),help='BrainWeb data directory')
    ap.add_argument('--image'); ap.add_argument('--label'); ap.add_argument('--axis',type=int,default=2); ap.add_argument('--slice',type=int,default=90)
    ap.add_argument('--slices',nargs='*',type=int,default=[70,80,90,100,110]); ap.add_argument('--repeats',type=int,default=5); ap.add_argument('--quick',action='store_true')
    a=ap.parse_args(); DATA=Path(a.data_dir)
    if a.check_only: check_files(); return
    label=Path(a.label) if a.label else DATA/'phantom_1.0mm_normal_crisp.rawb.gz'; truth=load_volume(label)
    if a.suite=='noise': cases=[('N0',DATA/'t1_icbm_normal_1mm_pn0_rf20.rawb.gz'),('N3',DATA/'t1_icbm_normal_1mm_pn3_rf20.rawb.gz'),('N5',DATA/'t1_icbm_normal_1mm_pn5_rf20.rawb.gz'),('N9',DATA/'t1_icbm_normal_1mm_pn9_rf20.rawb.gz')]
    elif a.suite=='rf': cases=[('RF0',DATA/'t1_icbm_normal_1mm_pn3_rf0.rawb.gz'),('RF20',DATA/'t1_icbm_normal_1mm_pn3_rf20.rawb.gz'),('RF40',DATA/'t1_icbm_normal_1mm_pn3_rf40.rawb.gz')]
    else: cases=[('preview',Path(a.image) if a.image else DATA/'t1_icbm_normal_1mm_pn3_rf20.rawb.gz')]
    outdir=ROOT/'results'/(a.suite or 'preview'); outdir.mkdir(parents=True,exist_ok=True)
    if a.suite == 'params':
        vol=load_volume(cases[0][1]); rows=[]
        for m,alpha,window in product([1.5,2.0,2.5],[0.5,1.0,1.5,2.0],[3,5,7]):
            sc,_=run_one(vol,truth,a.axis,a.slice,'SFCM',0,m=m,alpha=alpha,window=window)
            rows.append({'m':m,'alpha':alpha,'window':window,**sc})
        pd.DataFrame(rows).to_csv(outdir/'parameter_sensitivity.csv',index=False)
        print(pd.DataFrame(rows).sort_values('mean_dice',ascending=False).head(10)); return
    rows=[]
    slices=[a.slice] if (a.quick or not a.suite) else a.slices
    repeats=1 if a.quick else a.repeats
    for cname,p in cases:
        vol=load_volume(p)
        for idx in slices:
            for seed in range(repeats):
                for method in ['K-Means','FCM','SFCM']:
                    sc,art=run_one(vol,truth,a.axis,idx,method,seed)
                    rows.append({"case":cname,"slice":idx,"seed":seed,"method":method,**sc})
                    if idx==slices[0] and seed==0:
                        img,gt,pred,mask,centers,maps,hist=art
                        plt.imsave(outdir/f'{cname}_{method}_slice{idx}.png',np.where(mask,pred+1,0),cmap='viridis')
                        if method=='SFCM' and maps is not None:
                            ent=-np.sum(maps*np.log(np.maximum(maps,1e-12)),axis=-1)/np.log(3)
                            plt.imsave(outdir/f'{cname}_SFCM_entropy_slice{idx}.png',ent,cmap='inferno')
    df=pd.DataFrame(rows); df.to_csv(outdir/'raw_metrics.csv',index=False)
    num=[c for c in df.columns if c not in ['case','method','slice','seed']]
    summary=df.groupby(['case','method'])[num].agg(['mean','std']); summary.to_csv(outdir/'summary.csv')
    print(summary[['mean_dice','mean_iou','ari','nmi','seconds']])

if __name__=='__main__': main()
