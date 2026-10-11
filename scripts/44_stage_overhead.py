# T3（R1 修回，2026-10-05）：语义层（brepFace subset＋PMI scope）对 stage 载入时间、内存、文件大小的开销实测，
# 以及「焊接网格上照样可按三角形写 subset」的可行性核验（回应 R1-5b 与 §2 I-3）。
# 每件造 4 个变体（Sdf 层复制后编辑，网格数组逐字不动或仅焊接顶点）：
#   full       现交付 W stage（out/proto_v2）
#   geom       删 /Part/PMI 与全部 brepFace subset（纯几何，同一逐面网格）
#   weld_geom  geom 的顶点按坐标焊接（近似「普通转换器」的共享顶点网格）
#   weld_full  焊接网格＋原 subset（三角形索引不变）＋原 PMI scope
# 每 (变体, 件) 在独立子进程中测 N 次：Stage.Open、全 Traverse、读全部 points/faceVertexIndices/subset indices、
#   BBoxCache 世界包围盒（成像前置的代理量；usd-core 无 Hydra，**不声称测了渲染帧时**）、子进程峰值 RSS（扣 import 基线）。
# 另核：full 与 geom 的 points/indices 逐元素相等；r1 与 v4 冻结 stage 的网格数组逐元素相等（关联修复不动几何）。
# 用法: python 44_stage_overhead.py <proto_v2_dir> <v4_frozen_proto_dir> <out_dir> [reps]
#       python 44_stage_overhead.py --child <usdc|-> （内部用）
import glob
import json
import os
import resource
import statistics
import subprocess
import sys
import time

if sys.argv[1] == "--child":
    t0 = time.perf_counter()
    from pxr import Usd, UsdGeom
    t_imp = time.perf_counter() - t0
    rss0 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    res = {"import_s": t_imp, "rss_after_import": rss0}
    if sys.argv[2] != "-":
        t = time.perf_counter(); st = Usd.Stage.Open(sys.argv[2]); res["open_s"] = time.perf_counter() - t
        t = time.perf_counter(); prims = list(st.Traverse()); res["traverse_s"] = time.perf_counter() - t
        res["prims"] = len(prims)
        t = time.perf_counter()
        nread = 0
        for p in prims:
            if p.IsA(UsdGeom.Mesh):
                m = UsdGeom.Mesh(p)
                nread += len(m.GetPointsAttr().Get()) + len(m.GetFaceVertexIndicesAttr().Get())
            elif p.IsA(UsdGeom.Subset):
                nread += len(UsdGeom.Subset(p).GetIndicesAttr().Get())
            for a in p.GetAuthoredAttributes():
                if a.GetTypeName() in ("string", "token", "double", "string[]", "int[]", "bool"):
                    a.Get()
        res["read_s"] = time.perf_counter() - t
        res["elements_read"] = nread
        t = time.perf_counter()
        UsdGeom.BBoxCache(Usd.TimeCode.Default(), ["default", "render"]).ComputeWorldBound(st.GetPseudoRoot())
        res["bbox_s"] = time.perf_counter() - t
    # macOS ru_maxrss 单位是字节
    res["rss_peak"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(json.dumps(res))
    sys.exit(0)

import numpy as np
from pxr import Sdf, Usd, UsdGeom, Vt

proto_dir, v4_dir, out_dir = sys.argv[1:4]
REPS = int(sys.argv[4]) if len(sys.argv) > 4 else 10
VARIANTS = ("full", "geom", "weld_geom", "weld_full")
for v in VARIANTS:
    os.makedirs(os.path.join(out_dir, v), exist_ok=True)


def mesh_arrays(path):
    st = Usd.Stage.Open(path)
    m = UsdGeom.Mesh(st.GetPrimAtPath("/Part/Geom"))
    return (np.array(m.GetPointsAttr().Get()), np.array(m.GetFaceVertexIndicesAttr().Get()),
            np.array(m.GetFaceVertexCountsAttr().Get()))


def edited(src, dst, do_strip=False, do_weld=False):
    """匿名层打开 src → 编辑 → Export 到全新文件（crate 原地 Save 会追加写，文件大小不可比——首轮实踩）"""
    lay = Sdf.Layer.OpenAsAnonymous(src)
    st = Usd.Stage.Open(lay)
    n, nv, nu = 0, None, None
    if do_strip:
        victims = [p.GetPath() for p in st.Traverse()
                   if p.GetPath() == Sdf.Path("/Part/PMI") or (p.IsA(UsdGeom.Subset) and
                                                               UsdGeom.Subset(p).GetFamilyNameAttr().Get() == "brepFace")]
        for vp in victims:
            st.RemovePrim(vp)
        n = len(victims)
    if do_weld:
        m = UsdGeom.Mesh(st.GetPrimAtPath("/Part/Geom"))
        P = np.array(m.GetPointsAttr().Get())
        I = np.array(m.GetFaceVertexIndicesAttr().Get())
        uniq, inv = np.unique(P, axis=0, return_inverse=True)        # 逐比特相同的 float32 坐标才合并
        m.GetPointsAttr().Set(Vt.Vec3fArray.FromNumpy(uniq.astype(np.float32)))
        m.GetFaceVertexIndicesAttr().Set(Vt.IntArray.FromNumpy(inv.reshape(-1)[I].astype(np.int32)))
        nv, nu = len(P), len(uniq)
    lay.Export(dst)
    return n, nv, nu


def child(path):
    r = subprocess.run([sys.executable, __file__, "--child", path], capture_output=True, text=True, check=True)
    return json.loads(r.stdout.strip().splitlines()[-1])


rows, checks = [], []
base_rss = [child("-")["rss_peak"] for _ in range(REPS)]
for src in sorted(glob.glob(os.path.join(proto_dir, "*ap242*.usdc"))):
    b = os.path.basename(src)[:-5]
    paths = {v: os.path.join(out_dir, v, b + ".usdc") for v in VARIANTS}
    edited(src, paths["full"])                       # 同样经 Export，保证四个变体的写出路径一致
    n_removed, _, _ = edited(src, paths["geom"], do_strip=True)
    _, nv, nu = edited(src, paths["weld_geom"], do_strip=True, do_weld=True)
    edited(src, paths["weld_full"], do_weld=True)
    # 恒等核验
    Pf, If, Cf = mesh_arrays(paths["full"]); Pg, Ig, Cg = mesh_arrays(paths["geom"])
    P4, I4, C4 = mesh_arrays(os.path.join(v4_dir, b + ".usdc"))
    wf = Usd.Stage.Open(paths["weld_full"])
    subs = [UsdGeom.Subset(p) for p in wf.Traverse() if p.IsA(UsdGeom.Subset)]
    nf = len(Cf)
    cover = np.zeros(nf, int)
    for s in subs:
        cover[np.array(s.GetIndicesAttr().Get(), int)] += 1
    fam_ok = UsdGeom.Subset.ValidateFamily(UsdGeom.Imageable(wf.GetPrimAtPath("/Part/Geom")), UsdGeom.Tokens.face,
                                           "brepFace")[0] if subs else None
    checks.append({"model": b, "removed_prims": n_removed,
                   "full_eq_geom": bool(np.array_equal(Pf, Pg) and np.array_equal(If, Ig) and np.array_equal(Cf, Cg)),
                   "r1_eq_v4_mesh": bool(np.array_equal(Pf, P4) and np.array_equal(If, I4) and np.array_equal(Cf, C4)),
                   "verts_per_face_mesh": nv, "verts_welded": nu, "dup_ratio": round(nv / nu, 3),
                   "weld_full_subsets": len(subs), "weld_full_partition_ok": bool((cover == 1).all()),
                   "weld_full_validate_family": fam_ok})
    for v in VARIANTS:
        ms = [child(paths[v]) for _ in range(REPS)]
        agg = {"model": b, "variant": v, "bytes": os.path.getsize(paths[v]), "prims": ms[0]["prims"]}
        for k in ("open_s", "traverse_s", "read_s", "bbox_s"):
            xs = sorted(m[k] for m in ms)
            agg[k + "_med"] = statistics.median(xs)
            agg[k + "_iqr"] = xs[(3 * len(xs)) // 4] - xs[len(xs) // 4]
        agg["rss_delta_med"] = statistics.median(m["rss_peak"] for m in ms) - statistics.median(base_rss)
        rows.append(agg)
    print(f"[44] {b} done", flush=True)

# 汇总：每变体对 full 的比值（逐件）＋全集合计
S = {"reps": REPS, "base_rss_med": statistics.median(base_rss), "checks_all": {
    k: all(c[k] for c in checks) for k in ("full_eq_geom", "r1_eq_v4_mesh", "weld_full_partition_ok")}}
by = {(r["model"], r["variant"]): r for r in rows}
for v in VARIANTS:
    S[v] = {"bytes_total": sum(by[(c["model"], v)]["bytes"] for c in checks)}
    for k in ("open_s_med", "read_s_med", "traverse_s_med", "bbox_s_med", "rss_delta_med"):
        S[v][k + "_sum"] = sum(by[(c["model"], v)][k] for c in checks)
for v in ("geom", "weld_geom", "weld_full"):
    S[f"ratio_full_over_{v}"] = {k: statistics.median(by[(c["model"], "full")][k] / by[(c["model"], v)][k]
                                                      for c in checks if by[(c["model"], v)][k] > 0 and by[(c["model"], "full")][k] > 0)
                                 for k in ("bytes", "open_s_med", "read_s_med", "rss_delta_med")}
json.dump({"summary": S, "checks": checks, "rows": rows}, open(os.path.join(out_dir, "stage_overhead.json"), "w"),
          indent=1)
print(json.dumps(S, indent=1))
