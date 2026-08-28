# S3：逐模型注册表（最优/次优变换、中位距离、差距）——回应内部审 P1-1 与上轮 R4-6。
# 协议同 18（恒等+24 真旋转、bbox 中心平移、2000 点中位判据、pcu 距离），只做选择不做全量测量。
# 用法: .venv/bin/python 23_registration_table.py <out.json>
import glob
import json
import os
import sys

import numpy as np
import point_cloud_utils as pcu
from pxr import Usd, UsdGeom

os.chdir(os.path.join(os.path.dirname(__file__), ".."))
out = sys.argv[1]
ARC = os.environ.get("V1_ARCHIVE", "archive/v1-pilot") + "/pilot/out"

def load_mesh(path):
    stage = Usd.Stage.Open(path)
    mpu = UsdGeom.GetStageMetersPerUnit(stage)
    verts, faces, off = [], [], 0
    cache = UsdGeom.XformCache()
    for p in stage.Traverse(Usd.TraverseInstanceProxies()):
        if not p.IsA(UsdGeom.Mesh):
            continue
        m = UsdGeom.Mesh(p)
        pts = m.GetPointsAttr().Get()
        fvc = m.GetFaceVertexCountsAttr().Get()
        fvi = m.GetFaceVertexIndicesAttr().Get()
        if not pts or not fvc:
            continue
        xf = np.array(cache.GetLocalToWorldTransform(p))
        v = np.array([tuple(x) for x in pts]) @ xf[:3, :3] + xf[3, :3]
        k = 0
        for c in fvc:
            for t in range(1, c - 1):
                faces.append([fvi[k] + off, fvi[k + t] + off, fvi[k + t + 1] + off])
            k += c
        verts.append(v)
        off += len(v)
    return np.vstack(verts), np.array(faces, int), mpu

def rot24():
    mats, seen = [], set()
    axes = [np.eye(3)[i] * s for i in range(3) for s in (1, -1)]
    for x in axes:
        for y in axes:
            if abs(np.dot(x, y)) > 1e-9:
                continue
            Rm = np.column_stack([x, y, np.cross(x, y)])
            if np.linalg.det(Rm) < 0.5:
                continue
            key = tuple(np.round(Rm.flatten(), 6))
            if key not in seen:
                seen.add(key)
                mats.append(Rm)
    return mats

rows = []
for gj in sorted(glob.glob("out/e1/*ap242*.graph.json")):
    b = os.path.basename(gj).replace(".graph.json", "")
    if b == "nist_ftc_08_asme1_ap242-e1-tg":
        continue
    gt = np.loadtxt(f"out/gt_area/{b}.xyz")[:, :3]
    rng = np.random.default_rng(42)
    sub = gt[rng.choice(len(gt), min(2000, len(gt)), replace=False)]
    gt_c = 0.5 * (gt.min(0) + gt.max(0))
    for pl, mp in (("chainA", f"{ARC}/batch_v4/{b}.chainA.usdc"),
                   ("omni", f"{ARC}/batch_v2/omni/{b}.usdc"),
                   ("mayo", f"out/e2_mayo/{b}.usdc"),
                   ("proto", f"out/proto_v2/{b}.usdc")):
        if not os.path.exists(mp):
            print(f"[23] skip {b} {pl}: no mesh")
            continue
        V, F, mpu = load_mesh(mp)
        scales = [1.0] + ([mpu * 1000.0] if mpu else [])
        gt_ext = np.linalg.norm(gt.max(0) - gt.min(0))
        scale = min(set(scales), key=lambda s: abs(np.linalg.norm(V.max(0) - V.min(0)) * s - gt_ext))
        V0 = np.ascontiguousarray(V * scale, np.float64)
        Fc = np.ascontiguousarray(F, np.int32)
        cands = [("identity", np.eye(3), np.zeros(3))]
        for i, Rm in enumerate(rot24()):
            Vr = V0 @ Rm.T
            cands.append((f"rot{i}", Rm, gt_c - 0.5 * (Vr.min(0) + Vr.max(0))))
        meds = []
        for name, Rm, tv in cands:
            q = np.ascontiguousarray((sub - tv) @ Rm, np.float64)
            d, _, _ = pcu.closest_points_on_mesh(q, V0, Fc)
            meds.append((float(np.median(np.abs(d))), name))
        meds.sort()
        best, runner = meds[0], meds[1]
        rows.append({"model": b.replace("nist_", "").replace("_asme1_ap242", ""),
                     "pipeline": pl, "best": best[1], "best_median": round(best[0], 5),
                     "runner_up": runner[1], "runner_median": round(runner[0], 5),
                     "gap_ratio": round(runner[0] / best[0], 1) if best[0] > 0 else None})
        print(f"[23] {b} {pl}: {best[1]} ({best[0]:.4f}) vs {runner[1]} ({runner[0]:.4f})")
json.dump(rows, open(out, "w"), indent=1)
print(f"[23] rows={len(rows)} -> {out}")
