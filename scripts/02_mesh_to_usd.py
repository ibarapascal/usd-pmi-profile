# Blender headless 脚本：OBJ → USD（开源链 A 的后半段）
# 用法: Blender --background --python 02_mesh_to_usd.py -- <input.obj> <output.usdc>
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
inp, out = argv[0], argv[1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=inp)
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
print(f"[02] imported meshes={len(meshes)} verts={sum(len(o.data.vertices) for o in meshes)}")
bpy.ops.wm.usd_export(filepath=out, export_materials=False)
print(f"[02] USD exported -> {out}")
print("[02] DONE")
