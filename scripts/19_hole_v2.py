# E4/E4b：孔径提取 v2（回应 R1/R3-4/R6-2：v1 只用 2000 抽样顶点 → 5% 可测率是方法下界）
# 三种口径并报：
#  A vertex-fit-all —— 全网格顶点（v1 同判据 ≥8 点，去掉抽样瓶颈）
#  B surface-fit    —— 三角面面积加权表面采样（每模型 200k 点，固定种子）后同窗口拟合
#  C subset-fit     —— 仅 proto_v2：GeomSubset 取该面三角形顶点，名义轴已知拟合半径
#  C2 subset-selfcontained —— 仅 proto_v2：轴/半径由 subset 点自拟合（法线特征向量轴＋Kasa 圆）
#  C3 asset-only    —— 仅 proto_v2：**圆柱面枚举也只从 USD 读**（pmi:surfaceType=="Cylinder" 的 subset），
#                      拟合同 C2；源侧 cylinders.json 仅用于评分（名义半径真值）与对齐核对——
#                      修复内部审 P0-1：C2 的枚举/索引取自源侧，「资产自足」声明与实现不一致
# 窗口参数 WIN_R 可由环境变量 HOLE_WIN_R 覆盖（敏感性实验用）
# 注册/单位：与 18 同协议（恒等+24 旋转中位数判据、bbox 单位自校准），本脚本自含实现（独立可审计）。
# 用法: .venv/bin/python 19_hole_v2.py <mesh.usdc> <cylinders.json> <gt.xyz> <out.json> [--subset]
import json
import sys

import numpy as np
import point_cloud_utils as pcu

mesh_path, cyl_json, gt_path, out = sys.argv[1:5]
use_subset = "--subset" in sys.argv
import os
MIN_PTS = 8          # 与 v1 一致的可测判据
WIN_R = float(os.environ.get("HOLE_WIN_R", "0.15"))   # 径向窗口（默认 ±15%，敏感性实验经环境变量改）
SURF_N = 200000
rng = np.random.default_rng(42)

from pxr import Usd, UsdGeom

stage = Usd.Stage.Open(mesh_path)
mpu = UsdGeom.GetStageMetersPerUnit(stage)
verts_l, faces_l, off = [], [], 0
subset_tris = {}  # occFaceIdx -> tri indices（仅 proto）
subset_cyl = set()  # USD 侧自带的圆柱面 subset 集合（C3 枚举源）
cache = UsdGeom.XformCache()
for p in stage.Traverse(Usd.TraverseInstanceProxies()):
    if p.IsA(UsdGeom.Mesh):
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
    if use_subset and p.IsA(UsdGeom.Subset):
        s = UsdGeom.Subset(p)
        if s.GetFamilyNameAttr().Get() == "brepFace":
            name = p.GetName()          # face_XXXX
            idx = int(name.split("_")[1])
            subset_tris[idx] = np.array(s.GetIndicesAttr().Get(), int)
            st_attr = p.GetAttribute("pmi:surfaceType")
            if st_attr and st_attr.Get() == "Cylinder":
                subset_cyl.add(idx)
V = np.vstack(verts_l)
F = np.array(faces_l, int)

gt = np.loadtxt(gt_path)[:, :3]

# ---- 单位自校准 + 注册（同 18 协议）----
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
gt_c = 0.5 * (gt.min(0) + gt.max(0))  # bbox 中心（同 18；质心版使 chainA 全线错位的实测教训）
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
Vw = V0 @ Rm.T + tv                      # 网格顶点（GT/mm 坐标系）

# ---- 表面采样（口径 B）----
tris = Vw[F]
area = 0.5 * np.linalg.norm(np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]), axis=1)
prob = area / area.sum()
ti = rng.choice(len(F), SURF_N, p=prob)
r1, r2 = rng.random(SURF_N), rng.random(SURF_N)
s1 = np.sqrt(r1)
surf = (1 - s1)[:, None] * tris[ti, 0] + (s1 * (1 - r2))[:, None] * tris[ti, 1] + (s1 * r2)[:, None] * tris[ti, 2]

def fit(points, c):
    ctr, ax, r = np.array(c["center"]), np.array(c["axis"]), c["radius"]
    ax = ax / np.linalg.norm(ax)
    rel = points - ctr
    t = rel @ ax
    radial = np.linalg.norm(rel - np.outer(t, ax), axis=1)
    lo, hi = sorted(c["v_range"])
    margin = 0.1 * (hi - lo)
    selm = (t > lo + margin) & (t < hi - margin) & (np.abs(radial - r) < WIN_R * r)
    if selm.sum() < MIN_PTS:
        return None, int(selm.sum())
    return float(abs(radial[selm].mean() - r)), int(selm.sum())

cyls = json.load(open(cyl_json))
res = []
for c in cyls:
    row = {"face_index": c["face_index"], "nominal_r": c["radius"]}
    errA, nA = fit(Vw, c)
    row["A_vertex_all"] = {"n": nA, "abs_err": errA}
    errB, nB = fit(surf, c)
    row["B_surface"] = {"n": nB, "abs_err": errB}
    if use_subset:
        st = subset_tris.get(c["face_index"])
        if st is None or len(st) == 0:
            row["C_subset"] = {"n": 0, "abs_err": None}
        else:
            pts_c = Vw[F[st]].reshape(-1, 3)
            ctr, ax = np.array(c["center"]), np.array(c["axis"])
            ax = ax / np.linalg.norm(ax)
            radial = np.linalg.norm((pts_c - ctr) - np.outer((pts_c - ctr) @ ax, ax), axis=1)
            if len(radial) < MIN_PTS:
                row["C_subset"] = {"n": int(len(radial)), "abs_err": None}
            else:
                row["C_subset"] = {"n": int(len(radial)),
                                   "abs_err": float(abs(radial.mean() - c["radius"]))}
                # C2：轴自拟合（消费端自足口径）——轴 ⊥ 全部三角形法线（法线协方差最小特征向量，
                # 线性且对部分圆弧稳健；此前的非线性最小二乘在小弧面上发散——1866 孔实测 median 2e-6 但
                # mean 被十余个 146/290mm 发散解炸毁的教训），再在 ⊥ 轴平面内 Kasa 圆拟合。
                tri_c = Vw[F[st]]
                nrm = np.cross(tri_c[:, 1] - tri_c[:, 0], tri_c[:, 2] - tri_c[:, 0])
                ln = np.linalg.norm(nrm, axis=1)
                nrm = nrm[ln > 1e-12] / ln[ln > 1e-12][:, None]
                w, vec = np.linalg.eigh(nrm.T @ nrm)
                ax2 = vec[:, 0]                       # 最小特征值方向 = 轴
                e1v = vec[:, 1]; e2v = vec[:, 2]
                uv2 = np.column_stack([pts_c @ e1v, pts_c @ e2v])
                # Kasa 圆拟合: |p-c|^2 = r^2 → 线性
                Amat = np.column_stack([2 * uv2, np.ones(len(uv2))])
                bvec = (uv2 ** 2).sum(1)
                sol2, *_ = np.linalg.lstsq(Amat, bvec, rcond=None)
                cx, cy, c0 = sol2
                r2 = float(np.sqrt(max(c0 + cx * cx + cy * cy, 0.0)))
                rms2 = float(np.sqrt(np.mean((np.linalg.norm(uv2 - [cx, cy], axis=1) - r2) ** 2)))
                row["C2_selfcontained"] = {"n": int(len(radial)), "rms": rms2,
                                           "abs_err": float(abs(r2 - c["radius"]))}
    res.append(row)

# ---- C3：asset-only（枚举只用 USD 侧 subset_cyl）----
c3_rows = []
if use_subset:
    nominal_by_idx = {c["face_index"]: c["radius"] for c in cyls}
    for idx in sorted(subset_cyl):
        st = subset_tris.get(idx)
        if st is None or len(st) == 0:
            continue
        pts_c = Vw[F[st]].reshape(-1, 3)
        if len(pts_c) < MIN_PTS:
            c3_rows.append({"face_index": idx, "n": int(len(pts_c)), "abs_err": None,
                            "in_nominal_list": idx in nominal_by_idx})
            continue
        tri_c = Vw[F[st]]
        nrm = np.cross(tri_c[:, 1] - tri_c[:, 0], tri_c[:, 2] - tri_c[:, 0])
        ln = np.linalg.norm(nrm, axis=1)
        nrm = nrm[ln > 1e-12] / ln[ln > 1e-12][:, None]
        w2, vec = np.linalg.eigh(nrm.T @ nrm)
        e1v, e2v = vec[:, 1], vec[:, 2]
        uv2 = np.column_stack([pts_c @ e1v, pts_c @ e2v])
        Amat = np.column_stack([2 * uv2, np.ones(len(uv2))])
        sol2, *_ = np.linalg.lstsq(Amat, (uv2 ** 2).sum(1), rcond=None)
        cx, cy, c0 = sol2
        r_fit = float(np.sqrt(max(c0 + cx * cx + cy * cy, 0.0)))
        nom = nominal_by_idx.get(idx)
        c3_rows.append({"face_index": idx, "n": int(len(pts_c)), "fitted_r": r_fit,
                        "in_nominal_list": nom is not None,
                        "abs_err": (abs(r_fit - nom) if nom is not None else None)})

def rate(key):
    ok = sum(1 for r_ in res if r_.get(key, {}).get("abs_err") is not None)
    errs = [r_[key]["abs_err"] for r_ in res if r_.get(key, {}).get("abs_err") is not None]
    return {"measurable": ok, "total": len(res),
            "mean_abs_err": float(np.mean(errs)) if errs else None,
            "max_abs_err": float(np.max(errs)) if errs else None}

summary = {"mesh": mesh_path, "reg": reg_name, "scale": scale, "n_cyl": len(res),
           "A_vertex_all": rate("A_vertex_all"), "B_surface": rate("B_surface")}
if use_subset:
    summary["C_subset"] = rate("C_subset")
    summary["C2_selfcontained"] = rate("C2_selfcontained")
    scored = [r_ for r_ in c3_rows if r_["abs_err"] is not None]
    errs3 = [r_["abs_err"] for r_ in scored]
    summary["C3_asset_only"] = {
        "enumerated_from_usd": len(c3_rows),
        "nominal_total": len(cyls),
        "matched_to_nominal": sum(1 for r_ in c3_rows if r_["in_nominal_list"]),
        "measurable": len(scored), "total": len(cyls),
        "mean_abs_err": float(np.mean(errs3)) if errs3 else None,
        "max_abs_err": float(np.max(errs3)) if errs3 else None}
json.dump({"summary": summary, "per_hole": res, "c3_rows": (c3_rows if use_subset else None)}, open(out, "w"), indent=1)
print(f"[19] {mesh_path.split('/')[-1]} cyl={len(res)} "
      f"A={summary['A_vertex_all']['measurable']} B={summary['B_surface']['measurable']}"
      + (f" C={summary['C_subset']['measurable']} C2={summary['C2_selfcontained']['measurable']}"
         f" C3={summary['C3_asset_only']['enumerated_from_usd']}/{summary['C3_asset_only']['nominal_total']}" if use_subset else ""))
