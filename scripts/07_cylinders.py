# FreeCADCmd 脚本：从 B-rep 提取圆柱面清单（名义孔径 ground truth，下游任务锚 P0-5）
# 用法: FreeCADCmd 07_cylinders.py <input.stp> <out.json>
import json
import sys

import FreeCAD
import Part

args = [a for a in sys.argv if not a.endswith(("FreeCADCmd", "freecadcmd", ".py"))]
stp, out = args[-2], args[-1]
shape = Part.Shape()
shape.read(stp)
cyls = []
for i, f in enumerate(shape.Faces):
    if isinstance(f.Surface, Part.Cylinder):
        c = f.Surface
        (u0, u1), (v0, v1) = f.ParameterRange[:2], f.ParameterRange[2:]
        cyls.append({
            "face_index": i, "radius": c.Radius,
            "center": [c.Center.x, c.Center.y, c.Center.z],
            "axis": [c.Axis.x, c.Axis.y, c.Axis.z],
            "v_range": [v0, v1], "area": f.Area,
        })
with open(out, "w") as fh:
    json.dump(cyls, fh, indent=2)
print(f"[07] cylindrical faces={len(cyls)} radii={sorted(set(round(c['radius'],4) for c in cyls))}")
print("[07] DONE")
