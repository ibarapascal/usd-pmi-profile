# E2 语义/结构扫描：Mayo→glTF→guc 链输出（out/e2_mayo/*.usdc）的 USD 侧穷尽扫描。
# 与 P1/P2 同口径：①语义 PMI 载体（属性名/customData/prim 名中的 PMI 痕迹）②metersPerUnit 声明
# ③网格结构（Mesh prim 数、GeomSubset 数——对象/面合并判定）④prim 总数。
# 用法: .venv/bin/python 26_e2_scan.py <out.json>
import glob
import json
import os
import sys

from pxr import Usd, UsdGeom

os.chdir(os.path.join(os.path.dirname(__file__), ".."))
out = sys.argv[1]
KEYS = ("pmi", "tolerance", "datum", "gd&t", "gdt", "annotation", "dimension")

rows = []
for p in sorted(glob.glob("out/e2_mayo/*.usdc")):
    b = os.path.basename(p).replace(".usdc", "")
    stage = Usd.Stage.Open(p)
    mpu = UsdGeom.GetStageMetersPerUnit(stage)
    authored_mpu = stage.HasAuthoredMetadata("metersPerUnit")
    n_mesh = n_subset = n_prim = 0
    pmi_hits = []
    for prim in stage.Traverse(Usd.TraverseInstanceProxies()):
        n_prim += 1
        if prim.IsA(UsdGeom.Mesh):
            n_mesh += 1
        if prim.GetTypeName() == "GeomSubset":
            n_subset += 1
        names = [prim.GetName().lower()] + [a.GetName().lower() for a in prim.GetAttributes()]
        cd = prim.GetCustomData()
        if cd:
            names += [str(k).lower() for k in cd.keys()]
        for nm in names:
            for k in KEYS:
                if k in nm:
                    pmi_hits.append(f"{prim.GetPath()}:{nm}")
    rows.append({"model": b, "metersPerUnit": mpu, "authored_units": bool(authored_mpu),
                 "prims": n_prim, "meshes": n_mesh, "subsets": n_subset,
                 "pmi_hits": pmi_hits[:20], "pmi_hit_count": len(pmi_hits)})
    print(f"[26] {b}: mpu={mpu} authored={authored_mpu} meshes={n_mesh} subsets={n_subset} pmi_hits={len(pmi_hits)}")
json.dump(rows, open(out, "w"), indent=1)
print(f"[26] rows={len(rows)} -> {out}")
