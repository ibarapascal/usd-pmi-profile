# E10b：P3 prim 覆盖规则反向验证（配对 scripts/31）——D2 尾部误差是否会被同一 60° 角覆盖规则标出。
# 结论（2026-08-28 实测）：93 个 >0.1mm 误差中仅 6 个被标记；184mm 最坏案例覆盖角 180–350°（prim 合并/错配面，
# 规则失效的机理＝prim 边界无「恰为一个 B-rep 面」保证）。产物 out/e1/flag_rule_p3.json。
# 用法: .venv/bin/python scripts/32_flag_rule_p3.py
import glob, json, os, sys
import numpy as np
sys.path.insert(0,'')
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from pxr import Usd, UsdGeom
ARC=os.environ.get("V1_ARCHIVE", "archive/v1-pilot") + "/pilot/out"
rng=np.random.default_rng(42)
res=[]
for f in sorted(glob.glob('out/e9b/*.mayo.json')):
    b=os.path.basename(f).replace('.mayo.json','')
    d=json.load(open(f))
    errs={r['face_index']:r['D2_perprim'] for r in d['per_hole'] if r['D2_perprim'].get('abs_err') is not None}
    big=[ (fi,r) for fi,r in errs.items() if r['abs_err']>0.1]
    if not big: continue
    # recompute prims with coverage, match by fitted_r to find the culprit prims
    stage=Usd.Stage.Open(f'out/e2_mayo/{b}.usdc'); mpu=UsdGeom.GetStageMetersPerUnit(stage)
    cache=UsdGeom.XformCache()
    for p in stage.Traverse(Usd.TraverseInstanceProxies()):
        if not p.IsA(UsdGeom.Mesh): continue
        m=UsdGeom.Mesh(p); pts=m.GetPointsAttr().Get(); fvc=m.GetFaceVertexCountsAttr().Get(); fvi=m.GetFaceVertexIndicesAttr().Get()
        if not pts or not fvc: continue
        xf=np.array(cache.GetLocalToWorldTransform(p))
        v=np.array([tuple(x) for x in pts])@xf[:3,:3]+xf[3,:3]
        fl=[];k=0
        for c in fvc:
            for t in range(1,c-1): fl.append([fvi[k],fvi[k+t],fvi[k+t+1]])
            k+=c
        F=np.array(fl,int).reshape(-1,3)
        if len(F)<4: continue
        tri=(v*1000.0*mpu if mpu else v)[F] if False else v[F]
        # scale: use mpu*1000 like script 30
        scale=mpu*1000.0 if mpu else 1.0
        tri=tri*scale
        nrm=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]); ln=np.linalg.norm(nrm,axis=1)
        nn=nrm[ln>1e-12]/ln[ln>1e-12][:,None]
        if len(nn)<3: continue
        w,vec=np.linalg.eigh(nn.T@nn)
        e1v,e2v=vec[:,1],vec[:,2]
        pc=tri.reshape(-1,3)
        uv=np.column_stack([pc@e1v,pc@e2v])
        A=np.column_stack([2*uv,np.ones(len(uv))])
        sol,*_=np.linalg.lstsq(A,(uv**2).sum(1),rcond=None)
        cx,cy,c0=sol
        rf=float(np.sqrt(max(c0+cx*cx+cy*cy,0.0)))
        rms=float(np.sqrt(np.mean((np.linalg.norm(uv-[cx,cy],axis=1)-rf)**2)))
        if rms>=0.05 or not (0.2<rf<300): continue
        ang=np.sort(np.arctan2(uv[:,1]-cy,uv[:,0]-cx))
        gaps=np.diff(np.concatenate([ang,[ang[0]+2*np.pi]]))
        cov=float(np.degrees(2*np.pi-gaps.max()))
        for fi,r in big:
            if abs(r['fitted_r']-rf)<1e-6:
                res.append({'model':b,'face':fi,'err':round(r['abs_err'],3),'coverage':round(cov,1),'flag60':cov<60})
out={'n_big':len(res),'flagged':sum(1 for r in res if r['flag60']),'rows':sorted(res,key=lambda x:-x['err'])[:15]}
json.dump(out,open('out/e1/flag_rule_p3.json','w'),indent=1)
print(json.dumps({k:out[k] for k in ('n_big','flagged')},indent=1))
