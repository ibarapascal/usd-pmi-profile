# FreeCADCmd 脚本：B-rep 解析面直接采样点云（GT v2，内核中立——不经 tessellator，评审 P0-2）
# 每个 face 在 UV 参数域打网格，用曲面解析求值 face.valueAt(u,v)，isPartOfDomain 过滤 trimming。
# 采样点是 NURBS/解析曲面上的精确点（浮点精度），不含任何离散化弦差。
# 用法: FreeCADCmd 04_brep_sample.py <input.stp> <out.xyz> [total_points]
import math
import os
import sys

import FreeCAD
import Part

args = [a for a in sys.argv if not a.endswith(("FreeCADCmd", "freecadcmd", ".py"))]
inp, out = args[-2], args[-1]
total_target = 200000

shape = Part.Shape()
shape.read(inp)
faces = shape.Faces
total_area = sum(f.Area for f in faces)
pts = []
for f in faces:
    n_target = max(64, int(total_target * f.Area / total_area))
    grid = max(8, int(math.sqrt(n_target)))
    (u0, u1), (v0, v1) = f.ParameterRange[:2], f.ParameterRange[2:]
    for i in range(grid + 1):
        u = u0 + (u1 - u0) * i / grid
        for j in range(grid + 1):
            v = v0 + (v1 - v0) * j / grid
            if f.isPartOfDomain(u, v):
                p = f.valueAt(u, v)
                pts.append((p.x, p.y, p.z))

with open(out, "w") as fh:
    for p in pts:
        fh.write(f"{p[0]:.9f} {p[1]:.9f} {p[2]:.9f}\n")
print(f"[04] faces={len(faces)} sampled={len(pts)} -> {out}")
print("[04] DONE")
