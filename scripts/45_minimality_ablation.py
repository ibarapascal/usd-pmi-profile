# T11（R1 修回，2026-10-05）：profile 四元素的可执行消融（回应 R2-3「minimal 如何确立」）。
# 对 16 个 W stage 各造 5 个变体（full / −face identity / −typed / −association / −units），
# 用一个只依赖公开 pxr API 与一页约定的独立消费者，逐变体测下游能力是否还在：
#   K1 定位：face-anchored 标注的 appliesTo 目标能解析到存在的 brepFace subset 的比例
#   K2 读值：带值标注能读出数值的比例
#   K3 物理量：value × metersPerUnit 与 full 变体的米制值一致的比例（无声明时按 USD 回退值 0.01 m/unit）
#   K4 反查：面→标注 对（选择往返的反方向）可恢复的比例
#   K5 判定链：stage-only C3 拟合＋带判定（同 36 口径，自足重算，不读预算好的孔 json）能判的组数/合格组数
#   K6 枚举：可从 stage 枚举的圆柱面数（C3 的枚举源）
#   K7 溯源：带值标注带 pmi:sourceUnit 的比例（CF4 第二子句）
# 用法: python 45_minimality_ablation.py <proto_v2_dir> <out_dir>
import glob
import json
import os
import shutil
import sys
from collections import defaultdict

import numpy as np
from pxr import Sdf, Usd, UsdGeom

proto_dir, out_dir = sys.argv[1:3]
ABL = ("full", "no_face_identity", "no_typed", "no_association", "no_units")
TYPED = ("pmi:value", "pmi:lowerBound", "pmi:upperBound", "pmi:dimName", "pmi:datumLetter", "pmi:datumRefs")
TIE, TESS = 1e-5, 1e-3
for a in ABL:
    os.makedirs(os.path.join(out_dir, a), exist_ok=True)


def make(src, dst, abl):
    shutil.copyfile(src, dst)
    st = Usd.Stage.Open(dst)
    annos = [p for p in st.Traverse() if p.GetAttribute("pmi:type") and p.GetAttribute("pmi:type").Get()]
    if abl == "no_face_identity":
        for p in [p for p in st.Traverse() if p.IsA(UsdGeom.Subset)
                  and UsdGeom.Subset(p).GetFamilyNameAttr().Get() == "brepFace"]:
            st.RemovePrim(p.GetPath())
    elif abl == "no_typed":
        for p in annos:
            for n in TYPED:
                if p.GetAttribute(n):
                    p.RemoveProperty(n)
    elif abl == "no_association":
        for p in annos:
            if p.GetRelationship("pmi:appliesTo"):
                p.RemoveProperty("pmi:appliesTo")
    elif abl == "no_units":
        st.ClearMetadata("metersPerUnit")
        for p in annos:
            if p.GetAttribute("pmi:sourceUnit"):
                p.RemoveProperty("pmi:sourceUnit")
    st.GetRootLayer().Save()


def c3_fit(P):
    nrm = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
    ln = np.linalg.norm(nrm, axis=1)
    nrm = nrm[ln > 1e-12] / ln[ln > 1e-12][:, None]
    w, vec = np.linalg.eigh(nrm.T @ nrm)
    pts = P.reshape(-1, 3)
    uv = np.column_stack([pts @ vec[:, 1], pts @ vec[:, 2]])
    A = np.column_stack([2 * uv, np.ones(len(uv))])
    (cx, cy, c0), *_ = np.linalg.lstsq(A, (uv ** 2).sum(1), rcond=None)
    return float(np.sqrt(max(c0 + cx * cx + cy * cy, 0.0)))


def consume(path):
    """独立消费者：只用 pxr 与约定读 stage，返回能力指标的原始计数"""
    st = Usd.Stage.Open(path)
    mpu = UsdGeom.GetStageMetersPerUnit(st)          # 未声明时为 USD 回退值 0.01
    subs = {p.GetPath(): p for p in st.Traverse()
            if p.IsA(UsdGeom.Subset) and UsdGeom.Subset(p).GetFamilyNameAttr().Get() == "brepFace"}
    mesh = next((UsdGeom.Mesh(p) for p in st.Traverse() if p.IsA(UsdGeom.Mesh)), None)
    P = np.array(mesh.GetPointsAttr().Get(), float)
    I = np.array(mesh.GetFaceVertexIndicesAttr().Get(), int).reshape(-1, 3)
    cyl_r = {}
    for sp, p in subs.items():
        a = p.GetAttribute("pmi:surfaceType")
        if a and a.Get() == "Cylinder":
            tri = np.array(UsdGeom.Subset(p).GetIndicesAttr().Get(), int)
            if len(tri) * 3 >= 8:
                cyl_r[sp] = c3_fit(P[I[tri]])
    R = {"mpu": mpu, "annos": 0, "valued": 0, "valued_readable": 0, "face_targets": 0, "face_targets_resolved": 0,
         "phys": {}, "reverse_pairs": 0, "sourceUnit": 0, "cylinders": len(cyl_r),
         "groups_judged": 0, "groups_clean": 0}
    for p in st.Traverse():
        t = p.GetAttribute("pmi:type")
        if not (t and t.Get()):
            continue
        R["annos"] += 1
        sid = str(p.GetAttribute("pmi:stepId").Get())
        step = p.GetAttribute("pmi:step").Get() or ""
        has_val_src = "MEASURE" in step or bool(p.GetAttribute("pmi:sourceUnit"))
        va = p.GetAttribute("pmi:value")
        v = va.Get() if va else None
        if v is not None or has_val_src:
            R["valued"] += 1
        if v is not None:
            R["valued_readable"] += 1
            R["phys"][sid] = float(v) * mpu
        if p.GetAttribute("pmi:sourceUnit") and p.GetAttribute("pmi:sourceUnit").Get():
            R["sourceUnit"] += 1
        kind = p.GetAttribute("pmi:anchorKind")
        rel = p.GetRelationship("pmi:appliesTo")
        tg = list(rel.GetTargets()) if rel else []
        if kind and kind.Get() == "face":
            R["face_targets"] += max(len(tg), 1)
            R["face_targets_resolved"] += sum(1 for x in tg if x in subs)
        R["reverse_pairs"] += sum(1 for x in tg if x in subs)
        # 判定链（同 36：DIMENSIONAL_SIZE＋双侧带＋diameter/radius，按组判）
        if t.Get() != "DIMENSIONAL_SIZE":
            continue
        lo_a, hi_a, dn = p.GetAttribute("pmi:lowerBound"), p.GetAttribute("pmi:upperBound"), p.GetAttribute("pmi:dimName")
        lo, hi = (lo_a.Get() if lo_a else None), (hi_a.Get() if hi_a else None)
        dim = str(dn.Get() if dn and dn.Get() else "").lower()
        if v is None or lo is None or hi is None or dim not in ("diameter", "radius"):
            continue
        mem = [(2 * cyl_r[x] if dim == "diameter" else cyl_r[x]) for x in tg if x in cyl_r]
        if not mem:
            continue
        R["groups_judged"] += 1
        lb, ub = v + lo, v + hi
        if all(max(lb - m, m - ub) <= TIE for m in mem):
            R["groups_clean"] += 1
    return R


rows, tot = [], defaultdict(lambda: defaultdict(float))
for src in sorted(glob.glob(os.path.join(proto_dir, "*ap242*.usdc"))):
    b = os.path.basename(src)[:-5]
    res = {}
    for a in ABL:
        dst = os.path.join(out_dir, a, b + ".usdc")
        make(src, dst, a)
        res[a] = consume(dst)
    ref = res["full"]
    for a in ABL:
        r = res[a]
        phys_ok = sum(1 for k, x in r["phys"].items()
                      if k in ref["phys"] and abs(x - ref["phys"][k]) <= 1e-12 * max(1, abs(ref["phys"][k])))
        row = {"model": b, "ablation": a, "mpu": r["mpu"], "annos": r["annos"],
               "K1_locate": (r["face_targets_resolved"], ref["face_targets_resolved"]),
               "K2_read": (r["valued_readable"], ref["valued_readable"]),
               "K3_phys": (phys_ok, len(ref["phys"])),
               "K4_reverse": (r["reverse_pairs"], ref["reverse_pairs"]),
               "K5_judged": (r["groups_judged"], ref["groups_judged"]),
               "K5_clean": (r["groups_clean"], ref["groups_clean"]),
               "K6_cyl": (r["cylinders"], ref["cylinders"]),
               "K7_sourceUnit": (r["sourceUnit"], ref["sourceUnit"])}
        rows.append(row)
        for k, v in row.items():
            if k.startswith("K"):
                tot[a][k + "_num"] += v[0]
                tot[a][k + "_den"] += v[1]
    print(f"[45] {b}", {a: (res[a]["groups_judged"], res[a]["groups_clean"]) for a in ABL}, flush=True)

S = {a: {k.replace("_num", ""): f"{int(tot[a][k])}/{int(tot[a][k.replace('_num', '_den')])}"
         for k in tot[a] if k.endswith("_num")} for a in ABL}
json.dump({"summary": S, "rows": rows}, open(os.path.join(out_dir, "minimality_ablation.json"), "w"), indent=1)
print(json.dumps(S, indent=1))
