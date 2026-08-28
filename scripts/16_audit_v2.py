# E1 步骤四：审计器 v2 —— USD 读回 vs STEP 图解析（graph.json）逐条比对，并逐条判定 profile 一致性条件 CF1–CF7。
# 口径：
#   stage-local（只读 USD，不看源）  CF1 每个 brepFace subset 带 pmi:surfaceType
#                                    CF2 每个 anno prim 带 pmi:type 与 pmi:stepId
#                                    CF3 appliesTo 非空且目标全为 brepFace subset；anchorKind=edge 必带
#                                        pmi:edgeAnchorStepIds；anchorKind=face 必有非空 appliesTo
#                                    CF4 metersPerUnit 与 upAxis 为 authored，且带 typed 长度者必带 pmi:sourceUnit
#   source-relative（需 graph.json / faces.json）
#                                    CF5 面 subset 与源面集合一一对应（需 faces.json）
#                                    CF6 typed 往返等值（value/bounds/datumLetter/datumRefs）
#                                    CF7 源侧 face-anchored 标注在 USD 有 appliesTo、目标合法**且覆盖全部目标面**
# ⚠️ 单位（2026-08-29）：writer 已把数值换算到 stage 单位。本审计器**不读 match.json**——换算系数由 stage 上
#    声明的 pmi:sourceUnit 反查常数表得到，故不依赖 writer 侧簿记（避免 typed 往返变成自证）。
# 审计器与 writer 解耦：只读 USD 与 graph/faces json，不 import writer 代码。
# 用法: .venv/bin/python 16_audit_v2.py <usdc> <graph.json> <out.json> [faces.json]
import json
import re
import sys

from pxr import Usd, UsdGeom

usdc, graph_json, out = sys.argv[1:4]
faces_json = sys.argv[4] if len(sys.argv) > 4 else None
g = json.load(open(graph_json))
stage = Usd.Stage.Open(usdc)

# 换算系数取自**源侧** graph.json 的 unitToMm（解析自 STEP 单位上下文），不取 writer 侧数据；
# 另核对 stage 上自述的 pmi:sourceUnit 名是否与源一致（名/值双向对账）。

subs = {}
for p in stage.Traverse():
    if p.IsA(UsdGeom.Subset):
        s = UsdGeom.Subset(p)
        if s.GetFamilyNameAttr().Get() == "brepFace":
            subs[p.GetPath().pathString] = p

# 按**属性**发现标注（凡带 pmi:type 者即为标注），不依赖 prim 命名或绝对路径：
# 命名不是 profile 的规范要素，若按 anno_* 发现，则「本审计器可评分任何工具产出的 stage」不成立
# （2026-08-29 修正；与 §6.5 独立读取器走同一条发现路径）。
annos_usd = {}
for p in stage.Traverse():
    a = p.GetAttribute("pmi:type")
    if not (a and a.Get()):
        continue
    sid_attr = p.GetAttribute("pmi:stepId")
    sid = None
    if sid_attr and sid_attr.Get():
        m = re.search(r"\d+", str(sid_attr.Get()))
        sid = int(m.group()) if m else None
    if sid is None:                      # 退化路径：无 stepId 时才回落到命名
        m = re.search(r"(\d+)$", p.GetName())
        sid = int(m.group(1)) if m else None
    if sid is not None:
        annos_usd[sid] = p


def attr(p, n):
    a = p.GetAttribute(n)
    return a.Get() if a else None


def near(a, b):
    return a is not None and b is not None and abs(float(a) - float(b)) <= 1e-9 * max(1.0, abs(float(b)))


r = {"n_expected": len(g["annotations"]), "n_usd": len(annos_usd), "survive": 0,
     "typed_eq": 0, "typed_mismatch": [], "rel_ok": 0, "rel_bad_target": [], "rel_missing": [], "rel_incomplete": [],
     "anchor_face_expected": 0, "n_subsets": len(subs),
     "metersPerUnit": UsdGeom.GetStageMetersPerUnit(stage),
     "upAxis": str(UsdGeom.GetStageUpAxis(stage)),
     "cf": {}}

# ---- CF1 / CF2 / CF3 / CF4：stage-local，只读 USD ----
cf1_bad = [q for q in subs if attr(subs[q], "pmi:surfaceType") in (None, "")]
cf2_bad = [sid for sid, p in annos_usd.items()
           if attr(p, "pmi:type") in (None, "") or attr(p, "pmi:stepId") in (None, "")]
cf3_bad = []
for sid, p in annos_usd.items():
    rel = p.GetRelationship("pmi:appliesTo")
    targets = [str(t) for t in rel.GetTargets()] if rel else []
    kind = attr(p, "pmi:anchorKind")
    if rel and (not targets or any(t not in subs for t in targets)):
        cf3_bad.append({"stepId": sid, "err": "appliesTo empty or target not a brepFace subset"})
    elif kind == "face" and not targets:
        cf3_bad.append({"stepId": sid, "err": "anchorKind=face without appliesTo"})
    elif kind == "edge" and not attr(p, "pmi:edgeAnchorStepIds"):
        cf3_bad.append({"stepId": sid, "err": "anchorKind=edge without edgeAnchorStepIds"})
mpu_authored = UsdGeom.StageHasAuthoredMetersPerUnit(stage)   # 区分「已声明」与 fallback 默认值
up_authored = stage.HasAuthoredMetadata("upAxis")
r["cf"]["CF1"] = {"checked": len(subs), "violations": len(cf1_bad), "pass": not cf1_bad}
r["cf"]["CF2"] = {"checked": len(annos_usd), "violations": len(cf2_bad), "pass": not cf2_bad}
r["cf"]["CF3"] = {"checked": len(annos_usd), "violations": len(cf3_bad), "pass": not cf3_bad,
                  "detail": cf3_bad[:20]}
# CF4 第二子句：凡带 typed 长度者必须带 pmi:sourceUnit（且不得为未解析标记）
cf4_missing_unit = []
for sid, p in annos_usd.items():
    if any(attr(p, n) is not None for n in ("pmi:value", "pmi:lowerBound", "pmi:upperBound")):
        su = attr(p, "pmi:sourceUnit")
        if su in (None, "") or str(su).upper() == "UNRESOLVED":
            cf4_missing_unit.append(sid)
r["cf"]["CF4"] = {"metersPerUnitAuthored": bool(mpu_authored), "upAxisAuthored": bool(up_authored),
                  "typed_without_sourceUnit": len(cf4_missing_unit),
                  "pass": bool(mpu_authored and up_authored and not cf4_missing_unit)}

# ---- CF5：面 subset 与源面一一对应（需 faces.json）----
if faces_json:
    src_faces = {f["index"] for f in json.load(open(faces_json))["faces"]}
    usd_face_idx = set()
    for q in subs:
        try:
            usd_face_idx.add(int(q.rsplit("face_", 1)[1]))
        except (IndexError, ValueError):
            pass
    r["cf"]["CF5"] = {"source_faces": len(src_faces), "usd_subsets": len(usd_face_idx),
                      "bijective": src_faces == usd_face_idx, "pass": src_faces == usd_face_idx}
else:
    r["cf"]["CF5"] = {"pass": None, "note": "faces.json not supplied"}

# ---- CF6 / CF7：source-relative，逐条比对 ----
for rec in g["annotations"]:
    sid = rec["stepId"]
    p = annos_usd.get(sid)
    if p is None:
        r["typed_mismatch"].append({"stepId": sid, "err": "anno prim missing"})
        continue
    r["survive"] += 1
    k = float(rec.get("unitToMm") or 1.0)     # 源侧解析出的单位换算，非 writer 侧
    ok = attr(p, "pmi:type") == rec["type"]
    if rec.get("unitName") and str(attr(p, "pmi:sourceUnit") or "").upper() != str(rec["unitName"]).upper():
        ok = False                             # stage 自述单位名与源不一致
    for key, a in (("value", "pmi:value"), ("lowerBound", "pmi:lowerBound"),
                   ("upperBound", "pmi:upperBound")):
        if rec.get(key) is not None and not near(attr(p, a), float(rec[key]) * k):
            ok = False
    if rec.get("datumLetter") and attr(p, "pmi:datumLetter") != rec["datumLetter"]:
        ok = False
    if rec.get("datumRefs") and sorted(attr(p, "pmi:datumRefs") or []) != sorted(rec["datumRefs"]):
        ok = False
    r["typed_eq"] += 1 if ok else 0
    if not ok:
        r["typed_mismatch"].append({"stepId": sid, "type": rec["type"]})
    if rec.get("anchorKind") == "face":
        r["anchor_face_expected"] += 1
        rel = p.GetRelationship("pmi:appliesTo")
        targets = [str(t) for t in rel.GetTargets()] if rel else []
        want = len(rec.get("faceIds") or [])
        if not targets:
            r["rel_missing"].append(sid)     # 缺关联此前落不进任何桶，诊断不可见
        elif not all(t in subs for t in targets):
            r["rel_bad_target"].append(sid)
        else:
            r["rel_ok"] += 1                 # ⚠️ 口径不变：关系存在且目标合法（正文已报告的那个率）
            if want and len(targets) < want:
                # 完整性是**另一个**口径：关系有效但没覆盖源侧全部目标面。
                # 此前 CF7 只查「非空且类型对」，一个 40 面里只解析出 1 面的 stage 也判 pass。
                r["rel_incomplete"].append({"stepId": sid, "got": len(targets), "want": want})

r["cf"]["CF6"] = {"checked": r["n_expected"], "violations": len(r["typed_mismatch"]),
                  "pass": not r["typed_mismatch"]}
r["cf"]["CF7"] = {"checked": r["anchor_face_expected"], "resolved": r["rel_ok"],
                  "bad_target": len(r["rel_bad_target"]), "missing": len(r["rel_missing"]),
                  "incomplete": len(r["rel_incomplete"]),
                  "pass": (r["rel_ok"] == r["anchor_face_expected"]) and not r["rel_incomplete"]}

json.dump(r, open(out, "w"), indent=1)
cf = {k: v.get("pass") for k, v in r["cf"].items()}
print(f"[16] expect={r['n_expected']} survive={r['survive']} typed_eq={r['typed_eq']} "
      f"rel_ok={r['rel_ok']}/{r['anchor_face_expected']} subsets={r['n_subsets']} "
      f"mpu={r['metersPerUnit']} CF={cf}")
