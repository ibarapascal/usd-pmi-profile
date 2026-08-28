# FreeCADCmd：逐面 tessellation 导出 JSON（供 12_usd_author.py 直写 USD，保面身份）
# 用法: FreeCADCmd 11_face_tess.py <input.stp> <out.json> [accuracy]
import json
import sys

import FreeCAD
import Part

args = [a for a in sys.argv if not a.endswith(("FreeCADCmd", "freecadcmd", ".py"))]
stp, out = args[-2], args[-1]
accuracy = 0.1

shape = Part.Shape()
shape.read(stp)
solid_hashes = set()
for s in shape.Solids:
    for f in s.Faces:
        solid_hashes.add(f.hashCode())
faces = []
for i, f in enumerate(shape.Faces):
    verts, tris = f.tessellate(accuracy)
    faces.append({
        "index": i,
        "surface": type(f.Surface).__name__,
        "free": f.hashCode() not in solid_hashes,
        "verts": [[v.x, v.y, v.z] for v in verts],
        "tris": [list(t) for t in tris],
    })
with open(out, "w") as fh:
    json.dump({"file": stp, "accuracy": accuracy, "n_faces": len(faces), "faces": faces}, fh)
print(f"[11] faces={len(faces)} free={sum(1 for x in faces if x['free'])} tris={sum(len(x['tris']) for x in faces)} -> {out}")
print("[11] DONE")
