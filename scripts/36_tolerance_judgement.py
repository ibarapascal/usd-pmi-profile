# E11（2026-08-29，v2 重做）：stage-only 判定链闭合演示 —— 把「测出的尺寸」与「管辖它的公差带」
# 在同一单位下对判，全程只读交付的 USD 场景，不回查源 CAD。
#
# ⚠️ 这**不是**对被制造零件的检验：拟合点取自交付网格，网格由源几何镶嵌而来，公差带也解析自同一源。
#    实测拟合值与标称的中位差约 1e-06 mm，而公差带宽 0.05–10.16 mm——判定结果不由制造偏差决定。
#    本实验证明的是**决策链能否闭合**（枚举面→拟合→找到管辖它的标注→解析单位→对判），
#    以及闭不上时能否指出原因；不证明任何关于实物零件的结论。
#
# 口径：
#   - 被判对象 = pmi:surfaceType=="Cylinder" 的 brepFace subset，且其 C3 asset-only 拟合半径存在
#   - 判据来源 = 经 pmi:appliesTo 关联到该面、type=="DIMENSIONAL_SIZE" 且具备**双侧**公差带的标注
#   - 尺寸语义取自 pmi:dimName：'diameter'→2r，'radius'→r，其余名目不判定并计数（不强行套用）
#   - **统计单位是标注（annotation），不是面**：一条标注可关联多个面，按面展开会把近重复样本当独立试验
#   - **数值平局政策**：|measured − band edge| ≤ TIE(1e-5 mm) 判为 at-limit（合格）。理由：该量级
#     远低于拟合自身的精度地板与任何制造相关尺度，把 1e-07 mm 的越界算作超差是记账假象而非判定
#   - 出带者按真因分类：tessellation（镶嵌级）／multi_size_group（一条标注跨不同尺寸的面）／
#     unit_inconsistent_source（组内一致但整体差 ~25.4×＝源侧单位标注缺陷）／other
# 用法: .venv/bin/python 36_tolerance_judgement.py <proto_v2_dir> <hole_dir> <out.json>
import glob
import json
import os
import sys
from collections import defaultdict

from pxr import Usd, UsdGeom

proto_dir, hole_dir, out = sys.argv[1:4]
TIE = 1e-5          # mm，数值平局容差
TESS = 1e-3         # mm，镶嵌级与结构性偏差的分界
INCH = 25.4

rows, groups = [], []
funnel = defaultdict(int)
skipped_dim = defaultdict(int)


def g(prim, n):
    a = prim.GetAttribute(n)
    return a.Get() if a else None


for usdc in sorted(glob.glob(os.path.join(proto_dir, "*ap242*.usdc"))):
    base = os.path.basename(usdc)[:-len(".usdc")]
    hj = os.path.join(hole_dir, base + ".proto.json")
    if not os.path.exists(hj):
        continue
    fitted = {r["face_index"]: r.get("fitted_r")
              for r in json.load(open(hj)).get("c3_rows", []) if r.get("fitted_r") is not None}
    stage = Usd.Stage.Open(usdc)

    # ---- 漏斗：标注总数 → DIMENSIONAL_SIZE → 双侧带 → diameter/radius ----
    sizes = []
    for p in stage.Traverse():
        if not (g(p, "pmi:type")):
            continue
        funnel["annotations_total"] += 1
        if g(p, "pmi:type") != "DIMENSIONAL_SIZE":
            continue
        funnel["dimensional_size"] += 1
        v, lo, hi = g(p, "pmi:value"), g(p, "pmi:lowerBound"), g(p, "pmi:upperBound")
        if v is None or lo is None or hi is None:
            funnel["dropped_no_two_sided_band"] += 1     # 此前从未被计数或披露
            continue
        funnel["two_sided_band"] += 1
        dim = str(g(p, "pmi:dimName") or "").strip().lower()
        if dim not in ("diameter", "radius"):
            skipped_dim[dim or "(unnamed)"] += 1
            continue
        funnel["diameter_or_radius"] += 1
        sizes.append((p, float(v), float(lo), float(hi), dim))

    # ---- 逐标注（组）判定；面只是该组的成员 ----
    for p, v, lo, hi, dim in sizes:
        rel = p.GetRelationship("pmi:appliesTo")
        targets = [str(t) for t in (rel.GetTargets() if rel else [])]
        members = []
        for t in targets:
            try:
                idx = int(t.rsplit("face_", 1)[1])
            except (IndexError, ValueError):
                continue
            r = fitted.get(idx)
            if r is None:
                continue
            members.append((idx, (2.0 * r) if dim == "diameter" else r))
        if not members:
            funnel["group_without_fitted_cylinder"] += 1
            continue
        funnel["groups_judged"] += 1
        lo_b, hi_b = v + lo, v + hi
        band = hi_b - lo_b
        uniform = (max(m[1] for m in members) - min(m[1] for m in members)) <= TESS
        grp_fail = []
        for idx, meas in members:
            excess = max(lo_b - meas, meas - hi_b)          # >0 即越界
            if excess <= TIE:
                verdict, cause = "in", ("at_limit" if excess > 0 else None)
            else:
                verdict = "out"
                if not uniform:
                    cause = "multi_size_group"
                elif abs(v / meas - INCH) < 0.5 or abs(meas / v - INCH) < 0.5:
                    cause = "unit_inconsistent_source"
                elif excess < TESS:
                    cause = "tessellation"
                else:
                    cause = "other"
                grp_fail.append(cause)
            rows.append({"model": base, "stepId": str(g(p, "pmi:stepId")), "face_index": idx,
                         "dimName": dim, "measured": meas, "nominal": v,
                         "band_lo": lo_b, "band_hi": hi_b, "band_width": band,
                         "excess": max(excess, 0.0), "verdict": verdict, "cause": cause,
                         "sourceUnit": str(g(p, "pmi:sourceUnit"))})
        groups.append({"model": base, "stepId": str(g(p, "pmi:stepId")), "dimName": dim,
                       "faces": len(members), "nominal": v, "band_width": band,
                       "uniform": uniform, "clean": not grp_fail,
                       "cause": (grp_fail[0] if grp_fail else None)})

face_in = sum(1 for r in rows if r["verdict"] == "in")
grp_clean = sum(1 for g_ in groups if g_["clean"])
cause_face = defaultdict(int)
for r in rows:
    if r["cause"]:
        cause_face[r["cause"]] += 1
cause_grp = defaultdict(int)
for g_ in groups:
    if g_["cause"]:
        cause_grp[g_["cause"]] += 1

summary = {
    "funnel": dict(funnel), "skipped_by_dimName": dict(skipped_dim),
    "groups": len(groups), "groups_clean": grp_clean,
    "groups_clean_pct": round(100.0 * grp_clean / len(groups), 2) if groups else None,
    "faces": len(rows), "faces_in_band": face_in,
    "faces_in_band_pct": round(100.0 * face_in / len(rows), 2) if rows else None,
    "at_limit_faces": sum(1 for r in rows if r["cause"] == "at_limit"),
    "cause_by_face": dict(cause_face), "cause_by_group": dict(cause_grp),
    "band_width_min": round(min(r["band_width"] for r in rows), 4) if rows else None,
    "band_width_max": round(max(r["band_width"] for r in rows), 3) if rows else None,
    "tie_tolerance_mm": TIE,
}
json.dump({"summary": summary, "groups": groups, "rows": rows}, open(out, "w"), indent=1)
print(f"[36] groups={summary['groups']} clean={summary['groups_clean']} ({summary['groups_clean_pct']}%) "
      f"| faces={summary['faces']} in={summary['faces_in_band']} ({summary['faces_in_band_pct']}%) "
      f"at_limit={summary['at_limit_faces']}")
print(f"     funnel={dict(funnel)}")
print(f"     cause_by_group={dict(cause_grp)}  skipped_dimName={dict(skipped_dim)}")
