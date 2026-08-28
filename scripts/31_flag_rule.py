# E10：asset-side 可标记性规则（回应窄审 P0-3：flaggability 不能只断言）——
# 在 W 输出上，逐圆柱 subset 用纯资产侧信息计算角覆盖（fitted 轴/圆心投影后的最大角隙），
# 规则：angular coverage < COV_MIN 判「部分弧，半径不可信」。验证两件事：
# ①该规则是否 a priori 标记 C2/C3 的全部大误差案例（含 ctc_05 的 3.47mm 最大值）
# ②标记率（假阳性代价）。P3 无此规则可用——prim 无「恰为一个 B-rep 面」保证（正文论证）。
# 用法: .venv/bin/python 31_flag_rule.py <out.json>   （输入固定 out/proto_v2 + batch_v3 清单）
import glob
import json
import os
import sys

import numpy as np
from pxr import Usd, UsdGeom

os.chdir(os.path.join(os.path.dirname(__file__), ".."))
out = sys.argv[1]
ARC = os.environ.get("V1_ARCHIVE", "archive/v1-pilot") + "/pilot/out"
COV_MIN_DEG = 60.0

rows = []
for gj in sorted(glob.glob("out/e1/*ap242*.graph.json")):
    b = os.path.basename(gj).replace(".graph.json", "")
    if b == "nist_ftc_08_asme1_ap242-e1-tg":
        continue
    cylf = f"{ARC}/batch_v3/{b}.cylinders.json"
    usdf = f"out/proto_v2/{b}.usdc"
    if not (os.path.exists(cylf) and os.path.exists(usdf)):
        continue
    cyls = {c["face_index"]: c for c in json.load(open(cylf))}
    stage = Usd.Stage.Open(usdf)
    verts_l, faces_l, off = [], [], 0
    subset_tris = {}
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
        if p.IsA(UsdGeom.Subset):
            s = UsdGeom.Subset(p)
            if s.GetFamilyNameAttr().Get() == "brepFace":
                idx = int(p.GetName().split("_")[1])
                subset_tris[idx] = np.array(s.GetIndicesAttr().Get(), int)
    V = np.vstack(verts_l)
    F = np.array(faces_l, int).reshape(-1, 3)
    for idx, c in cyls.items():
        st = subset_tris.get(idx)
        if st is None or len(st) == 0:
            continue
        tri = V[F[st]]
        pts_c = tri.reshape(-1, 3)
        nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        ln = np.linalg.norm(nrm, axis=1)
        nrm = nrm[ln > 1e-12] / ln[ln > 1e-12][:, None]
        if len(nrm) < 3:
            continue
        w, vec = np.linalg.eigh(nrm.T @ nrm)
        e1v, e2v = vec[:, 1], vec[:, 2]
        uv = np.column_stack([pts_c @ e1v, pts_c @ e2v])
        A = np.column_stack([2 * uv, np.ones(len(uv))])
        sol, *_ = np.linalg.lstsq(A, (uv ** 2).sum(1), rcond=None)
        cx, cy, c0 = sol
        r_fit = float(np.sqrt(max(c0 + cx * cx + cy * cy, 0.0)))
        ang = np.sort(np.arctan2(uv[:, 1] - cy, uv[:, 0] - cx))
        gaps = np.diff(np.concatenate([ang, [ang[0] + 2 * np.pi]]))
        coverage = float(np.degrees(2 * np.pi - gaps.max()))
        # 误差（对名义，评分侧）——用于验证 flag 与大误差的关系
        err = abs(r_fit - c["radius"])
        rows.append({"model": b, "face_index": idx, "coverage_deg": round(coverage, 1),
                     "flagged": coverage < COV_MIN_DEG, "abs_err": err,
                     "n_pts": int(len(pts_c))})

flag = [r for r in rows if r["flagged"]]
unflag = [r for r in rows if not r["flagged"]]
errs_u = np.array([r["abs_err"] for r in unflag])
errs_f = np.array([r["abs_err"] for r in flag])
summary = {
    "cov_min_deg": COV_MIN_DEG, "total": len(rows), "flagged": len(flag),
    "flagged_pct": round(100 * len(flag) / len(rows), 1),
    "max_err_unflagged": float(errs_u.max()) if len(errs_u) else None,
    "p99_err_unflagged": float(np.percentile(errs_u, 99)) if len(errs_u) else None,
    "max_err_flagged": float(errs_f.max()) if len(errs_f) else None,
    "top5_errors": sorted(({"model": r["model"], "err": round(r["abs_err"], 4),
                            "coverage": r["coverage_deg"], "flagged": r["flagged"]}
                           for r in rows), key=lambda x: -x["err"])[:5],
}
json.dump({"summary": summary, "rows": rows}, open(out, "w"), indent=1)
print(json.dumps(summary, indent=1))
