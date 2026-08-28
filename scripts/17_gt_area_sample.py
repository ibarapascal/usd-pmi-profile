# E3 步骤一：面积一致 GT 采样（回应 R4-5/R6-1：v1 的 UV 均匀网格非面积均匀）
# 方法：逐面预算 ∝ 精确面积（f.Area）；面内 UV 拒绝采样，权重 = 一阶有限差分 Jacobian |Pu × Pv|，
#      Jmax 在 24×24 粗网格估计 ×1.25 裕度；trimming 用 f.isPartOfDomain。固定种子可复现。
# 输出：文本 xyz（x y z occFaceIdx），单位 = 模型数值单位（OCC 读入后 mm）。
# 用法: freecadcmd 17_gt_area_sample.py <input.stp> <out.xyz> [budget]
import random
import sys

import FreeCAD  # noqa: F401
import Part

args = [a for a in sys.argv if not a.endswith(("FreeCADCmd", "freecadcmd", ".py"))]
budget = 50000
if args and args[-1].isdigit():
    budget = int(args[-1])
    args = args[:-1]
stp, out = args[-2], args[-1]
random.seed(42)

shape = Part.Shape()
shape.read(stp)
areas = [max(f.Area, 1e-12) for f in shape.Faces]
total = sum(areas)

def jac(f, u, v, hu, hv):
    try:
        p0 = f.valueAt(u, v)
        pu = f.valueAt(u + hu, v)
        pv = f.valueAt(u, v + hv)
    except Exception:
        return 0.0
    du = (pu - p0).multiply(1.0 / hu)
    dv = (pv - p0).multiply(1.0 / hv)
    return du.cross(dv).Length

n_out = 0
with open(out, "w") as fh:
    for idx, f in enumerate(shape.Faces):
        n = max(3, int(round(budget * areas[idx] / total)))
        u0, u1, v0, v1 = f.ParameterRange
        du, dv = (u1 - u0) or 1e-9, (v1 - v0) or 1e-9
        hu, hv = du * 1e-5, dv * 1e-5
        jmax = 0.0
        for i in range(24):
            for j in range(24):
                jm = jac(f, u0 + du * (i + 0.5) / 24, v0 + dv * (j + 0.5) / 24, hu, hv)
                jmax = max(jmax, jm)
        jmax *= 1.25
        if jmax <= 0:
            continue
        got, tries = 0, 0
        while got < n and tries < n * 200:
            tries += 1
            u = u0 + du * random.random()
            v = v0 + dv * random.random()
            if not f.isPartOfDomain(u, v):
                continue
            if random.random() * jmax > jac(f, u, v, hu, hv):
                continue
            p = f.valueAt(u, v)
            fh.write(f"{p.x:.7f} {p.y:.7f} {p.z:.7f} {idx}\n")
            got += 1
        n_out += got
print(f"[17] faces={len(shape.Faces)} samples={n_out} budget={budget} -> {out}")
