# E1 步骤三：writer v2 —— typed PMI 属性 ＋ annotation-to-face associativity（rel pmi:appliesTo → GeomSubset）
# 相对 v1（archive .../pilot/12_usd_author.py）新增：typed 值属性、基准引用、rel 关联、edge 锚定记录、匹配率透传。
# standards-only：UsdGeomSubset / typed attributes / relationship / Scope，无自定义 schema class。
# 用法: .venv/bin/python 15_usd_author_v2.py <faces.json> <graph.json> <match.json> <out.usdc>
import json
import sys

from pxr import Usd, UsdGeom, Sdf, Vt

faces_json, graph_json, match_json, out = sys.argv[1:5]
data = json.load(open(faces_json))
g = json.load(open(graph_json))
match = json.load(open(match_json))
step_to_occ = {int(v): int(k) for k, v in match["occ_to_step"].items()}

stage = Usd.Stage.CreateNew(out)
UsdGeom.SetStageMetersPerUnit(stage, 0.001)
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
part = UsdGeom.Xform.Define(stage, "/Part")
stage.SetDefaultPrim(part.GetPrim())

# ---- 网格＋逐面 subset（同 v1）----
pts, fvc, fvi, face_ranges = [], [], [], []
off = 0
for f in data["faces"]:
    n0 = len(fvc)
    for t in f["tris"]:
        fvc.append(3)
        fvi.extend([t[0] + off, t[1] + off, t[2] + off])
    pts.extend(f["verts"])
    off += len(f["verts"])
    face_ranges.append((f["index"], n0, len(fvc), f["free"], f["surface"]))
mesh = UsdGeom.Mesh.Define(stage, "/Part/Geom")
mesh.CreatePointsAttr(Vt.Vec3fArray([tuple(p) for p in pts]))
mesh.CreateFaceVertexCountsAttr(Vt.IntArray(fvc))
mesh.CreateFaceVertexIndicesAttr(Vt.IntArray(fvi))
for idx, a, b, free, surf in face_ranges:
    sub = UsdGeom.Subset.Define(stage, f"/Part/Geom/face_{idx:04d}")
    sub.CreateElementTypeAttr(UsdGeom.Tokens.face)
    sub.CreateFamilyNameAttr("brepFace")
    sub.CreateIndicesAttr(Vt.IntArray(list(range(a, b))))
    p = sub.GetPrim()
    p.CreateAttribute("pmi:surfaceType", Sdf.ValueTypeNames.Token).Set(surf)
    if free:
        p.CreateAttribute("pmi:freeFace", Sdf.ValueTypeNames.Bool).Set(True)

# ---- PMI scope：typed 属性 ＋ rel 关联 ----
UsdGeom.Scope.Define(stage, "/Part/PMI")
stats = {"annos": 0, "typed_value": 0, "rel_face": 0, "rel_targets": 0,
         "edge_anchored": 0, "face_unmapped": 0}
for rec in g["annotations"]:
    sid = rec["stepId"]
    prim = stage.DefinePrim(f"/Part/PMI/anno_{sid}", "Scope")
    A = prim.CreateAttribute
    A("pmi:type", Sdf.ValueTypeNames.Token).Set(rec["type"])
    A("pmi:stepId", Sdf.ValueTypeNames.String).Set(f"#{sid}")
    if rec.get("raw"):
        A("pmi:step", Sdf.ValueTypeNames.String).Set(rec["raw"])
    if rec.get("value") is not None:
        A("pmi:value", Sdf.ValueTypeNames.Double).Set(float(rec["value"]))
        stats["typed_value"] += 1
    if rec.get("lowerBound") is not None:
        A("pmi:lowerBound", Sdf.ValueTypeNames.Double).Set(float(rec["lowerBound"]))
    if rec.get("upperBound") is not None:
        A("pmi:upperBound", Sdf.ValueTypeNames.Double).Set(float(rec["upperBound"]))
    if rec.get("datumLetter"):
        A("pmi:datumLetter", Sdf.ValueTypeNames.String).Set(rec["datumLetter"])
    if rec.get("datumRefs"):
        A("pmi:datumRefs", Sdf.ValueTypeNames.StringArray).Set(Vt.StringArray(rec["datumRefs"]))
    if rec.get("dimName"):
        A("pmi:dimName", Sdf.ValueTypeNames.Token).Set(rec["dimName"])
    A("pmi:anchorKind", Sdf.ValueTypeNames.Token).Set(rec.get("anchorKind", "none"))
    targets = []
    for fid in rec.get("faceIds", []):
        oi = step_to_occ.get(fid)
        if oi is None:
            stats["face_unmapped"] += 1
        else:
            targets.append(f"/Part/Geom/face_{oi:04d}")
    if targets:
        rel = prim.CreateRelationship("pmi:appliesTo")
        for t in targets:
            rel.AddTarget(t)
        stats["rel_face"] += 1
        stats["rel_targets"] += len(targets)
    if rec.get("nonFaceAnchorIds"):
        A("pmi:edgeAnchorStepIds", Sdf.ValueTypeNames.IntArray).Set(
            Vt.IntArray(rec["nonFaceAnchorIds"]))
        stats["edge_anchored"] += 1
    stats["annos"] += 1
stage.Save()
print(f"[15] faces={len(face_ranges)} " + " ".join(f"{k}={v}" for k, v in stats.items()) + f" -> {out}")
