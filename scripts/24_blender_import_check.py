# E5：Blender headless 导入检查（用法: Blender -b --python 24_blender_import_check.py）
# E5: Blender headless 导入 proto_v2 USD——验证渲染兼容不回退（对象数/顶点数>0 即通过）
import bpy, sys, glob, os
ok, bad = 0, []
for f in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "proto_v2", "*.usdc"))):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        bpy.ops.wm.usd_import(filepath=f)
        meshes = [o for o in bpy.data.objects if o.type == 'MESH']
        nv = sum(len(o.data.vertices) for o in meshes)
        if meshes and nv > 0:
            ok += 1
        else:
            bad.append((f, 'empty'))
    except Exception as e:
        bad.append((f, str(e)[:80]))
print(f"BLENDER_IMPORT ok={ok} bad={bad}")
