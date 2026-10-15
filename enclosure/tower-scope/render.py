import os, sys, math, numpy as np, cadquery as cq
import tower_scope as t

def head_world(w, tilt):
    w = w.translate((0,0,-t.Z_PIVOT)).rotate((0,0,0),(1,0,0),90).rotate((0,0,0),(1,0,0),-tilt)
    return w.translate((0,t.PED_YC,t.Z_PIVOT_W))

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

def tris(w, tol=0.08):
    v, tri = w.val().tessellate(tol, 0.25)
    V = np.array([[p.x,p.y,p.z] for p in v]); T = np.array(tri)
    return V[T]   # (n,3,3)

def scene(parts, cam, out, size=(1100,900), bg=(0.94,0.95,0.97)):
    pos, foc = np.array(cam[0],float), np.array(cam[1],float)
    f = foc-pos; f/=np.linalg.norm(f)
    up = np.array([0,1.0,0]) if abs(f[2])>0.99 else np.array([0,0,1.0])
    r = np.cross(f,up); r/=np.linalg.norm(r); u = np.cross(r,f)
    dist = np.linalg.norm(foc-pos)
    allp, cols, depth = [], [], []
    light = np.array([-0.4,-0.6,0.8]); light/=np.linalg.norm(light)
    light2 = np.array([0.7,-0.3,0.3]); light2/=np.linalg.norm(light2)
    for w,col in parts:
        T = tris(w)
        n = np.cross(T[:,1]-T[:,0], T[:,2]-T[:,0]); nn = np.linalg.norm(n,axis=1); ok = nn>1e-12
        T, n, nn = T[ok], n[ok], nn[ok]; n/= nn[:,None]
        zz=((T-pos)@f); keep=(zz>5).all(1); T,n=T[keep],n[keep]
        c = T.mean(1); view = pos-c
        front = (n*view).sum(1) > 0
        T, n, c = T[front], n[front], c[front]
        sh = 0.30 + 0.62*np.clip(n@light,0,1) + 0.25*np.clip(n@light2,0,1)
        rel = T - pos
        x = rel@r; y = rel@u; z = rel@f
        fl = dist*1.0
        px = x/z*fl; py = y/z*fl
        P2 = np.stack([px,py],-1)
        allp.append(P2); cols.append(np.clip(np.array(col)[None,:]*sh[:,None],0,1)); depth.append((c-pos)@f)
    P2 = np.concatenate(allp); C = np.concatenate(cols); D = np.concatenate(depth)
    order = np.argsort(-D)
    fig = plt.figure(figsize=(size[0]/100,size[1]/100), dpi=100, facecolor=bg)
    ax = fig.add_axes([0,0,1,1]); ax.set_facecolor(bg); ax.axis("off")
    pc = PolyCollection(P2[order], facecolors=C[order], edgecolors=C[order], linewidths=0.25)
    ax.add_collection(pc)
    lo, hi = P2.reshape(-1,2).min(0), P2.reshape(-1,2).max(0)
    mid=(lo+hi)/2; span=max(hi-lo)*0.55
    ax.set_xlim(mid[0]-span*size[0]/size[1], mid[0]+span*size[0]/size[1]); ax.set_ylim(mid[1]-span, mid[1]+span)
    fig.savefig(out, facecolor=bg); plt.close(fig)

if __name__ == "__main__":
    P = t.build("EHAM","09","52.37N 004.90E")
    os.makedirs("renders", exist_ok=True)
    ped = P["pedestal"].translate((0,t.PED_YC,0))
    base = P["base"]
    GREY=(0.30,0.32,0.35); WHITE=(0.96,0.96,0.94); YEL=(0.95,0.75,0.1); BEZ=(0.12,0.13,0.15); TOWER=(0.82,0.84,0.86); HEAD=(0.2,0.22,0.26)
    def assembled(tilt=20, with_head=True):
        L = [(base,GREY),(P["inlay_white"],WHITE),(P["inlay_yellow"],YEL),(ped,TOWER),(P['pole'].translate((*t.WIND_XY,-9)),(0.7,0.7,0.72)),(P['windsock'].translate((*t.WIND_XY,36)).rotate((*t.WIND_XY,0),(*t.WIND_XY,1),-35),(0.95,0.45,0.1))]
        if with_head:
            L += [(head_world(P["head"],tilt),HEAD),(head_world(P["bezel"],tilt),BEZ)]
        return L
    c=(0,12,55)
    scene(assembled(), ((-150,-190,150),c), "renders/hero.png")
    scene(assembled(), ((130,230,120),c), "renders/rear.png")
    scene(assembled(), ((0,-260,330),(0,5,5)), "renders/top_base.png")
    # exploded
    ex = [(P["plate"].translate((0,0,-40)),GREY),(base,GREY),(P["inlay_white"],WHITE),(P["inlay_yellow"],YEL),
          (ped.translate((0,0,8)),TOWER),
          (head_world(P["head"],0).translate((0,-70,70)),HEAD),(head_world(P["bezel"],0).translate((0,-125,70)),BEZ)]
    scene(ex, ((-260,-330,200),(0,-30,60)), "renders/exploded.png", (1400,950))
    # head only front/back
    hd=[(P["head"],HEAD)]
    scene([(P["head"],HEAD)], ((0,0,-200),(0,0,0)), "renders/head_rear.png", (800,800))
    scene([(P["bezel"],BEZ)], ((0,0,200),(0,0,12)), "renders/bezel_front.png", (800,800))
    scene([(P["head"],HEAD)], ((0,0,200),(0,0,0)), "renders/head_inside.png", (800,800))
