from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "work" / "pydeps"))
import numpy as np
from fcm_core import fcm

n=96; y,x=np.mgrid[-1:1:complex(n),-1:1:complex(n)]
gt=np.zeros((n,n),int); gt[(x/0.8)**2+(y/0.9)**2<1]=1; gt[(x/0.55)**2+(y/0.65)**2<1]=2
img=np.array([.15,.5,.82])[gt]+np.random.default_rng(42).normal(0,.08,(n,n)); mask=np.ones_like(gt,dtype=bool)
for name,alpha in [('FCM',0),('SFCM',1.5)]:
    pred,c,u,h,_=fcm(img,mask,n_clusters=3,alpha=alpha,seed=42)
    vals=[]
    for k in range(3):
        a=gt==k; b=pred==k; vals.append(2*np.logical_and(a,b).sum()/(a.sum()+b.sum()))
    print(name,'mean Dice=',round(float(np.mean(vals)),4),'centers=',np.round(c,3),'iterations=',len(h))
