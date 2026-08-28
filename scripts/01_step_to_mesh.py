# FreeCADCmd 脚本：STEP → OBJ（管线档）+ STL（ground-truth 密集采样档）
# 用法: FreeCADCmd 01_step_to_mesh.py <input.stp> <outdir>
# 管线档 = 模拟转换器典型 tessellation（LinearDeflection 0.5mm）
# GT 档  = 高密度采样（LinearDeflection 0.01mm），作为 B-rep 的网格代理参照
import sys
import os

import FreeCAD
import Part
import Mesh
import MeshPart

inp, outdir = sys.argv[-2], sys.argv[-1]
os.makedirs(outdir, exist_ok=True)
stem = os.path.splitext(os.path.basename(inp))[0]

doc = FreeCAD.newDocument("pilot")
shape = Part.Shape()
shape.read(inp)
print(f"[01] STEP read: faces={len(shape.Faces)} edges={len(shape.Edges)} solids={len(shape.Solids)} volume={shape.Volume:.3f}")

for tag, deflection in [("pipeline", 0.5), ("gt", 0.01)]:
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=deflection, AngularDeflection=0.5, Relative=False)
    out = os.path.join(outdir, f"{stem}.{tag}.{'obj' if tag == 'pipeline' else 'stl'}")
    Mesh.Mesh(mesh.Topology).write(out)
    print(f"[01] {tag}: deflection={deflection} verts={mesh.CountPoints} tris={mesh.CountFacets} -> {out}")

print("[01] DONE")
