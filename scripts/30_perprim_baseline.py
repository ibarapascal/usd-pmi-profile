# E9b：per-prim 几何拟合基线（regime D2，仅对保留逐面 prim 粒度的管线有意义，即 P3）——
# 审稿人可预见的反击：「P3 每面一个 prim，等于白送分割，无需 RANSAC 就能逐 prim 拟合」。
# 本脚本正面做掉：逐 mesh prim 用 C2 同款估计器（法线协方差轴＋Kasa 圆）拟合并按圆柱性
# （径向残差 RMS < RMS_TOL）筛选，评分同 29（名义窗口判据，post-hoc）。
# 结论口径：几何可测性可被 prim 粒度部分恢复；恢复不了的是 identity/PMI 关联（见正文）。
# 用法: .venv/bin/python 30_perprim_baseline.py <mesh.usdc> <cylinders.json> <gt.xyz> <out.json>
import json
import os
import sys

import numpy as np
import point_cloud_utils as pcu
from pxr import Usd, UsdGeom

mesh_path, cyl_json, gt_path, out = sys.argv[1:5]
MIN_PTS = 8
WIN_R = 0.15
RMS_TOL = float(os.environ.get("PRIM_RMS_TOL", "0.05"))  # mm；圆柱性筛选（径向残差；敏感性扫描经环境变量改）
rng = np.random.default_rng(42)

stage = Usd.Stage.Open(mesh_path)
mpu = UsdGeom.GetStageMetersPerUnit(stage)
prims = []               # (verts, faces) per mesh prim
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
    fl, k = [], 0
    for c in fvc:
        for t in range(1, c - 1):
            fl.append([fvi[k], fvi[k + t], fvi[k + t + 1]])
        k += c
    prims.append((v, np.array(fl, int).reshape(-1, 3)))
V = np.vstack([v for v, _ in prims])
offs = np.cumsum([0] + [len(v) for v, _ in prims[:-1]])
F = np.vstack([f + o for (_, f), o in zip(prims, offs)])
gt = np.loadtxt(gt_path)[:, :3]

scales = [1.0] + ([mpu * 1000.0] if mpu else [])
gt_ext = np.linalg.norm(gt.max(0) - gt.min(0))
scale = min(set(scales), key=lambda s: abs(np.linalg.norm(V.max(0) - V.min(0)) * s - gt_ext))

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

V0 = V * scale
sub = gt[rng.choice(len(gt), min(2000, len(gt)), replace=False)]
gt_c = 0.5 * (gt.min(0) + gt.max(0))
Vc = np.ascontiguousarray(V0, np.float64)
Fc = np.ascontiguousarray(F, np.int32)
best = None
cands = [("identity", np.eye(3), np.zeros(3))]
for i, Rm in enumerate(rot24()):
    Vr = V0 @ Rm.T
    cands.append((f"rot{i}", Rm, gt_c - 0.5 * (Vr.min(0) + Vr.max(0))))
for name, Rm, tv in cands:
    q = np.ascontiguousarray((sub - tv) @ Rm, np.float64)
    d, _, _ = pcu.closest_points_on_mesh(q, Vc, Fc)
    med = float(np.median(np.abs(d)))
    if best is None or med < best[0]:
        best = (med, name, Rm, tv)
_, reg_name, Rm, tv = best

detected = []
for v, f in prims:
    if len(f) < 4:
        continue
    vw = (v * scale) @ Rm.T + tv
    tri = vw[f]
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ln = np.linalg.norm(nrm, axis=1)
    nrm = nrm[ln > 1e-12] / ln[ln > 1e-12][:, None]
    if len(nrm) < 3:
        continue
    w, vec = np.linalg.eigh(nrm.T @ nrm)
    ax = vec[:, 0]
    e1v, e2v = vec[:, 1], vec[:, 2]
    pts_c = tri.reshape(-1, 3)
    uv = np.column_stack([pts_c @ e1v, pts_c @ e2v])
    Amat = np.column_stack([2 * uv, np.ones(len(uv))])
    sol, *_ = np.linalg.lstsq(Amat, (uv ** 2).sum(1), rcond=None)
    cx, cy, cc = sol
    r_fit = float(np.sqrt(max(cc + cx * cx + cy * cy, 0.0)))
    rms = float(np.sqrt(np.mean((np.linalg.norm(uv - [cx, cy], axis=1) - r_fit) ** 2)))
    if rms < RMS_TOL and 0.2 < r_fit < 300:
        # 窗口匹配用面上采样点（顶点集中在端环，会被轴向修边全裁——A 口径低可测率的同一机理）
        tarea = 0.5 * np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1)
        if tarea.sum() < 1e-12:
            continue
        nsamp = 2000
        si = rng.choice(len(tri), nsamp, p=tarea / tarea.sum())
        u1, u2 = rng.random(nsamp), rng.random(nsamp)
        su = np.sqrt(u1)
        samp = ((1 - su)[:, None] * tri[si, 0] + (su * (1 - u2))[:, None] * tri[si, 1]
                + (su * u2)[:, None] * tri[si, 2])
        detected.append({"pts": samp, "r": r_fit})

cyls = json.load(open(cyl_json))
rows = []
for c in cyls:
    ctr, ax_n, r_n = np.array(c["center"]), np.array(c["axis"]), c["radius"]
    ax_n = ax_n / np.linalg.norm(ax_n)
    lo, hi = sorted(c["v_range"])
    margin = 0.1 * (hi - lo)
    best_row = None
    for d in detected:
        rel = d["pts"] - ctr
        t = rel @ ax_n
        radial = np.linalg.norm(rel - np.outer(t, ax_n), axis=1)
        inwin = (t > lo + margin) & (t < hi - margin) & (np.abs(radial - r_n) < WIN_R * r_n)
        n_in = int(inwin.sum())
        if n_in >= MIN_PTS:
            if best_row is None or n_in > best_row["n"]:
                best_row = {"n": n_in, "abs_err": float(abs(d["r"] - r_n)), "fitted_r": d["r"]}
    rows.append({"face_index": c["face_index"], "nominal_r": r_n,
                 "D2_perprim": best_row or {"n": 0, "abs_err": None}})

errs = [r_["D2_perprim"]["abs_err"] for r_ in rows if r_["D2_perprim"]["abs_err"] is not None]
summary = {"mesh": mesh_path, "reg": reg_name, "scale": scale, "n_cyl": len(rows),
           "n_prims": len(prims), "n_cyl_prims": len(detected),
           "D2_perprim": {"measurable": len(errs), "total": len(rows),
                          "median_abs_err": float(np.median(errs)) if errs else None,
                          "mean_abs_err": float(np.mean(errs)) if errs else None,
                          "max_abs_err": float(np.max(errs)) if errs else None}}
json.dump({"summary": summary, "per_hole": rows}, open(out, "w"), indent=1)
print(f"[30] {os.path.basename(mesh_path)} prims={len(prims)} cylprims={len(detected)} "
      f"recovered={len(errs)}/{len(rows)}")
