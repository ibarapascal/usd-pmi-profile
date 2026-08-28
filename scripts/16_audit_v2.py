# E1 步骤四：审计器 v2 —— USD 读回 vs STEP 图解析（graph.json）逐条比对
# 口径：typed 往返等值（value/bounds/datumLetter/datumRefs 逐条 ==）；associativity（rel 目标存在且为
#      familyName=brepFace 的 GeomSubset）；单位声明；面 subset 计数。审计器与 writer 解耦：只读 USD 与
#      graph.json，不 import writer 代码。
# 用法: .venv/bin/python 16_audit_v2.py <usdc> <graph.json> <out.json>
import json
import sys

from pxr import Usd, UsdGeom

usdc, graph_json, out = sys.argv[1:4]
g = json.load(open(graph_json))
stage = Usd.Stage.Open(usdc)

subs = {}
for p in stage.Traverse():
    if p.IsA(UsdGeom.Subset):
        s = UsdGeom.Subset(p)
        if s.GetFamilyNameAttr().Get() == "brepFace":
            subs[p.GetPath().pathString] = p

annos_usd = {}
for p in stage.Traverse():
    path = p.GetPath().pathString
    if path.startswith("/Part/PMI/anno_"):
        annos_usd[int(path.rsplit("_", 1)[1])] = p

def near(a, b):
    return a is not None and b is not None and abs(float(a) - float(b)) < 1e-9

r = {"n_expected": len(g["annotations"]), "n_usd": len(annos_usd), "survive": 0,
     "typed_eq": 0, "typed_mismatch": [], "rel_ok": 0, "rel_bad_target": [],
     "anchor_face_expected": 0, "n_subsets": len(subs),
     "metersPerUnit": UsdGeom.GetStageMetersPerUnit(stage),
     "upAxis": str(UsdGeom.GetStageUpAxis(stage))}

for rec in g["annotations"]:
    sid = rec["stepId"]
    p = annos_usd.get(sid)
    if p is None:
        r["typed_mismatch"].append({"stepId": sid, "err": "anno prim missing"})
        continue
    r["survive"] += 1
    get = lambda n: (p.GetAttribute(n).Get() if p.GetAttribute(n) else None)
    ok = True
    if get("pmi:type") != rec["type"]:
        ok = False
    for key, attr in (("value", "pmi:value"), ("lowerBound", "pmi:lowerBound"),
                      ("upperBound", "pmi:upperBound")):
        if rec.get(key) is not None and not near(get(attr), rec[key]):
            ok = False
    if rec.get("datumLetter") and get("pmi:datumLetter") != rec["datumLetter"]:
        ok = False
    if rec.get("datumRefs") and sorted(get("pmi:datumRefs") or []) != sorted(rec["datumRefs"]):
        ok = False
    if ok:
        r["typed_eq"] += 1
    else:
        r["typed_mismatch"].append({"stepId": sid, "type": rec["type"]})
    if rec.get("anchorKind") == "face":
        r["anchor_face_expected"] += 1
        rel = p.GetRelationship("pmi:appliesTo")
        targets = rel.GetTargets() if rel else []
        if targets and all(str(t) in subs for t in targets):
            r["rel_ok"] += 1
        elif targets:
            r["rel_bad_target"].append(sid)

json.dump(r, open(out, "w"), indent=1)
print(f"[16] expect={r['n_expected']} survive={r['survive']} typed_eq={r['typed_eq']} "
      f"rel_ok={r['rel_ok']}/{r['anchor_face_expected']} subsets={r['n_subsets']} "
      f"mpu={r['metersPerUnit']}")
