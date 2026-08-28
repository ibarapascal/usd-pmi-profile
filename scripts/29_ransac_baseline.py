# E9：asset-only 几何分割基线（regime D）——回应外部审计 P0-2：
# 「production 输出无自足测量路径」此前是未经检验的全称否定；本脚本给出 naive 基线的实测下界：
# 不用任何 face identity/subset，仅从网格几何（法线对序贯 RANSAC）枚举圆柱并自拟合半径。
# 评分（post-hoc，允许用源侧名义清单，同 C3 口径）：检出簇的 inlier 点落入名义空间窗口
# （轴向 10% 修边、径向 ±15%，与 A/B 同窗）≥ MIN_PTS 判该孔 recovered；半径误差 = |refit − nominal|。
# 注册/单位与 19 同协议（刚体变换不改变可检出性，仅为评分对齐坐标系）。
# 用法: .venv/bin/python 29_ransac_baseline.py <mesh.usdc> <cylinders.json> <gt.xyz> <out.json>
import json
import os
import sys

import numpy as np
import point_cloud_utils as pcu
from pxr import Usd, UsdGeom

mesh_path, cyl_json, gt_path, out = sys.argv[1:5]
MIN_PTS = 8
WIN_R = 0.15
SURF_N = 40000
INLIER_TOL = 0.15          # mm；tessellation 线偏差 0.1mm 的容差上浮
AX_DOT_MAX = 0.25          # inlier 法线与轴的最大 |cos|
ITERS = 200                # 每轮候选数
MIN_CLUSTER = 15
MAX_ROUNDS = 400
rng = np.random.default_rng(42)

# ---- 网格加载（同 19）----
stage = Usd.Stage.Open(mesh_path)
mpu = UsdGeom.GetStageMetersPerUnit(stage)
verts_l, faces_l, off = [], [], 0
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
            faces_l.append([fvi[k] + off, fvi[k + t] + off, fvi[k + t + 1] + off])
        k += c
    verts_l.append(v)
    off += len(v)
V = np.vstack(verts_l)
F = np.array(faces_l, int)
gt = np.loadtxt(gt_path)[:, :3]

# ---- 单位自校准 + 注册（同 19）----
scales = [1.0] + ([mpu * 1000.0] if mpu else [])
gt_ext = np.linalg.norm(gt.max(0) - gt.min(0))
scale = min(set(scales), key=lambda s: abs(np.linalg.norm(V.max(0) - V.min(0)) * s - gt_ext))
V0 = V * scale

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

sub = gt[rng.choice(len(gt), min(2000, len(gt)), replace=False)]
gt_c = 0.5 * (gt.min(0) + gt.max(0))
Vc = np.ascontiguousarray(V0, np.float64)
Fc = np.ascontiguousarray(F, np.int32)
cands = [("identity", np.eye(3), np.zeros(3))]
for i, Rm in enumerate(rot24()):
    Vr = V0 @ Rm.T
    cands.append((f"rot{i}", Rm, gt_c - 0.5 * (Vr.min(0) + Vr.max(0))))
best = None
for name, Rm, tv in cands:
    q = np.ascontiguousarray((sub - tv) @ Rm, np.float64)
    d, _, _ = pcu.closest_points_on_mesh(q, Vc, Fc)
    med = float(np.median(np.abs(d)))
    if best is None or med < best[0]:
        best = (med, name, Rm, tv)
_, reg_name, Rm, tv = best
Vw = V0 @ Rm.T + tv

# ---- 表面采样（带法线；面积加权，同 B 口径）----
tris = Vw[F]
tn = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
area = 0.5 * np.linalg.norm(tn, axis=1)
ok_t = area > 1e-12
prob = area * ok_t
prob = prob / prob.sum()
ti = rng.choice(len(F), SURF_N, p=prob)
r1, r2 = rng.random(SURF_N), rng.random(SURF_N)
s1 = np.sqrt(r1)
P = (1 - s1)[:, None] * tris[ti, 0] + (s1 * (1 - r2))[:, None] * tris[ti, 1] + (s1 * r2)[:, None] * tris[ti, 2]
Nrm = tn[ti] / np.linalg.norm(tn[ti], axis=1, keepdims=True)

# ---- 序贯 RANSAC 圆柱抽取（无任何 face identity）----
active = np.ones(SURF_N, bool)
detected = []            # (inlier_index_array, axis, point_on_axis, radius)
rounds_dry = 0
for _round in range(MAX_ROUNDS):
    idx = np.flatnonzero(active)
    if len(idx) < MIN_CLUSTER:
        break
    best_cnt, best_sol = 0, None
    pick = rng.choice(idx, size=(ITERS, 2))
    for i1, i2 in pick:
        n1, n2 = Nrm[i1], Nrm[i2]
        a = np.cross(n1, n2)
        na = np.linalg.norm(a)
        if na < 0.08:          # 法线近平行 → 轴不可定
            continue
        a = a / na
        # 在 ⊥a 平面内解两条内法线的交点 = 轴心
        e1 = n1 - (n1 @ a) * a
        e2 = n2 - (n2 @ a) * a
        p1 = P[i1] - (P[i1] @ a) * a
        p2 = P[i2] - (P[i2] @ a) * a
        A2 = np.column_stack([e1, -e2])
        bb = p2 - p1
        try:
            ts, *_ = np.linalg.lstsq(A2, bb, rcond=None)
        except np.linalg.LinAlgError:
            continue
        c0 = p1 + ts[0] * e1
        r0 = 0.5 * (np.linalg.norm(P[i1] - ((P[i1] @ a) * a) - c0) +
                    np.linalg.norm(P[i2] - ((P[i2] @ a) * a) - c0))
        if not (0.2 < r0 < 300):
            continue
        rel = P[idx] - c0 - np.outer((P[idx] - c0) @ a, a)
        dr = np.abs(np.linalg.norm(rel, axis=1) - r0)
        perp = np.abs(Nrm[idx] @ a)
        inl = (dr < INLIER_TOL) & (perp < AX_DOT_MAX)
        cnt = int(inl.sum())
        if cnt > best_cnt:
            best_cnt, best_sol = cnt, (a, c0, r0, idx[inl])
    if best_cnt < MIN_CLUSTER:
        rounds_dry += 1
        if rounds_dry >= 3:
            break
        continue
    rounds_dry = 0
    a, c0, r0, inl_idx = best_sol
    # refine：法线协方差最小特征向量轴 + Kasa 圆（与 C2 同估计器）
    nn = Nrm[inl_idx]
    w, vec = np.linalg.eigh(nn.T @ nn)
    ax = vec[:, 0]
    e1v, e2v = vec[:, 1], vec[:, 2]
    uv = np.column_stack([P[inl_idx] @ e1v, P[inl_idx] @ e2v])
    Amat = np.column_stack([2 * uv, np.ones(len(uv))])
    sol, *_ = np.linalg.lstsq(Amat, (uv ** 2).sum(1), rcond=None)
    cx, cy, cc = sol
    r_fit = float(np.sqrt(max(cc + cx * cx + cy * cy, 0.0)))
    center3 = cx * e1v + cy * e2v          # 轴上一点（⊥轴平面内）
    detected.append({"idx": inl_idx, "axis": ax, "c2d": center3, "r": r_fit})
    active[inl_idx] = False

# ---- post-hoc 评分：名义窗口判据（同 A/B 窗）----
cyls = json.load(open(cyl_json))
rows = []
for c in cyls:
    ctr, ax_n, r_n = np.array(c["center"]), np.array(c["axis"]), c["radius"]
    ax_n = ax_n / np.linalg.norm(ax_n)
    lo, hi = sorted(c["v_range"])
    margin = 0.1 * (hi - lo)
    best_row = None
    for d in detected:
        rel = P[d["idx"]] - ctr
        t = rel @ ax_n
        radial = np.linalg.norm(rel - np.outer(t, ax_n), axis=1)
        inwin = (t > lo + margin) & (t < hi - margin) & (np.abs(radial - r_n) < WIN_R * r_n)
        n_in = int(inwin.sum())
        if n_in >= MIN_PTS:
            err = abs(d["r"] - r_n)
            if best_row is None or n_in > best_row["n"]:
                best_row = {"n": n_in, "abs_err": float(err), "fitted_r": d["r"]}
    rows.append({"face_index": c["face_index"], "nominal_r": r_n,
                 "D_ransac": best_row or {"n": 0, "abs_err": None}})

errs = [r_["D_ransac"]["abs_err"] for r_ in rows if r_["D_ransac"]["abs_err"] is not None]
summary = {"mesh": mesh_path, "reg": reg_name, "scale": scale, "n_cyl": len(rows),
           "n_detected_clusters": len(detected),
           "D_ransac": {"measurable": len(errs), "total": len(rows),
                        "median_abs_err": float(np.median(errs)) if errs else None,
                        "mean_abs_err": float(np.mean(errs)) if errs else None,
                        "max_abs_err": float(np.max(errs)) if errs else None}}
json.dump({"summary": summary, "per_hole": rows}, open(out, "w"), indent=1)
print(f"[29] {os.path.basename(mesh_path)} clusters={len(detected)} "
      f"recovered={len(errs)}/{len(rows)}")
