# T12（R1 修回，2026-10-05）：组合安全的实测（回应 R1-2；把 Table 3「Composition-safe: Yes」从断言变实测）。
# 建装配 stage：以 reference 引入 16 个 W stage（各在 /Asm/<件>，带不同 Xform），其中 2 件各再引一次（不同 Xform）；
# 对 ①组合 stage ②Flatten() 导出后重开的扁平 stage，逐件复跑 stage-local 条件 CF1–CF4 的读取路径：
#   CF1 每个 brepFace subset 带 pmi:surfaceType；CF2 每个标注 prim 带 pmi:type/stepId；
#   CF3 appliesTo 目标全部解析为**同一实例下**的 brepFace subset（关系目标随 reference 做命名空间映射）；
#   CF4 metersPerUnit 声明（装配层声明 0.001；被引用层的层级 metadata 不随 reference 进入——这是 USD 语义，如实记录）
# 断言：每个实例的标注数、subset 数、rel 目标数与单件 stage 相同；跨实例零串号；ValidateFamily(brepFace) 通过。
# 另跑 UsdUtils.ComplianceChecker 于单件与扁平装配。
# 用法: python 46_composition_check.py <proto_v2_dir> <out_dir>
import glob
import json
import os
import sys

from pxr import Gf, Sdf, Usd, UsdGeom

proto_dir, out_dir = sys.argv[1:3]
os.makedirs(out_dir, exist_ok=True)
srcs = sorted(glob.glob(os.path.join(os.path.abspath(proto_dir), "*ap242*.usdc")))
DOUBLE = [srcs[0], srcs[5]]                              # 两件各再引一次


def scan(stage, root):
    """在 root 子树内按约定读取；返回计数与违例"""
    rp = stage.GetPrimAtPath(root)
    subs = {p.GetPath() for p in Usd.PrimRange(rp)
            if p.IsA(UsdGeom.Subset) and UsdGeom.Subset(p).GetFamilyNameAttr().Get() == "brepFace"}
    r = {"subsets": len(subs), "annos": 0, "rel_targets": 0, "cf1_bad": 0, "cf2_bad": 0, "cf3_bad": 0,
         "foreign_targets": 0}
    for p in Usd.PrimRange(rp):
        if p.GetPath() in subs:
            a = p.GetAttribute("pmi:surfaceType")
            r["cf1_bad"] += not (a and a.Get())
        t = p.GetAttribute("pmi:type")
        if not (t and t.Get()):
            continue
        r["annos"] += 1
        s = p.GetAttribute("pmi:stepId")
        r["cf2_bad"] += not (s and s.Get())
        rel = p.GetRelationship("pmi:appliesTo")
        if rel:
            tg = rel.GetTargets()
            r["rel_targets"] += len(tg)
            r["cf3_bad"] += any(x not in subs for x in tg) or not tg
            r["foreign_targets"] += sum(1 for x in tg if not x.HasPrefix(Sdf.Path(root)))
    meshes = [UsdGeom.Imageable(p) for p in Usd.PrimRange(rp) if p.IsA(UsdGeom.Mesh)]
    r["validate_family"] = all(UsdGeom.Subset.ValidateFamily(m, UsdGeom.Tokens.face, "brepFace")[0] for m in meshes)
    return r


single = {}
for s in srcs:
    st = Usd.Stage.Open(s)
    single[s] = scan(st, "/Part")

asm_path = os.path.join(out_dir, "assembly.usda")
asm = Usd.Stage.CreateNew(asm_path)
UsdGeom.SetStageMetersPerUnit(asm, 0.001)
UsdGeom.SetStageUpAxis(asm, UsdGeom.Tokens.z)
root = UsdGeom.Xform.Define(asm, "/Asm")
asm.SetDefaultPrim(root.GetPrim())
inst = []
for i, s in enumerate(srcs + DOUBLE):
    name = os.path.basename(s)[:-5].replace("-", "_") + ("" if i < len(srcs) else "_copy")
    x = UsdGeom.Xform.Define(asm, f"/Asm/{name}")
    x.AddTranslateOp().Set(Gf.Vec3d(400.0 * (i % 6), 400.0 * (i // 6), 0.0))
    x.AddRotateZOp().Set(30.0 * i)
    x.GetPrim().GetReferences().AddReference(s)
    inst.append((f"/Asm/{name}", s))
asm.GetRootLayer().Save()

res = {"instances": len(inst), "composed": {}, "flattened": {}}
flat_path = os.path.join(out_dir, "assembly_flat.usdc")
asm.Flatten().Export(flat_path)
for tag, st in (("composed", Usd.Stage.Open(asm_path)), ("flattened", Usd.Stage.Open(flat_path))):
    agg = {"mismatch_vs_single": [], "foreign_targets": 0, "cf_bad": 0, "validate_family_fail": 0,
           "annos": 0, "subsets": 0, "rel_targets": 0, "metersPerUnit": UsdGeom.GetStageMetersPerUnit(st),
           "mpu_authored": UsdGeom.StageHasAuthoredMetersPerUnit(st)}
    for path, s in inst:
        r = scan(st, path)
        ref = single[s]
        for k in ("subsets", "annos", "rel_targets"):
            agg[k] += r[k]
            if r[k] != ref[k]:
                agg["mismatch_vs_single"].append({"inst": path, "key": k, "got": r[k], "want": ref[k]})
        agg["foreign_targets"] += r["foreign_targets"]
        agg["cf_bad"] += r["cf1_bad"] + r["cf2_bad"] + r["cf3_bad"]
        agg["validate_family_fail"] += not r["validate_family"]
    res[tag] = agg

cc = {}
try:
    from pxr.UsdUtils.complianceChecker import ComplianceChecker
except ImportError:
    ComplianceChecker = None
for tag, path in (("single_" + os.path.basename(srcs[0]), srcs[0]), ("assembly_flat", flat_path)):
    if ComplianceChecker is None:
        cc[tag] = "ComplianceChecker unavailable in this usd-core build"
        continue
    ck = ComplianceChecker()
    ck.CheckCompliance(path)
    cc[tag] = {"errors": len(ck.GetErrors()), "failed_checks": len(ck.GetFailedChecks()),
               "warnings": len(ck.GetWarnings()), "first": (ck.GetErrors() + ck.GetFailedChecks())[:3]}
res["compliance"] = cc
res["expected_totals"] = {k: sum(single[s][k] for _, s in inst) for k in ("subsets", "annos", "rel_targets")}
res["expected_cf_bad"] = sum(single[s]["cf1_bad"] + single[s]["cf2_bad"] + single[s]["cf3_bad"] for _, s in inst)
res["pass"] = all(not res[t]["mismatch_vs_single"] and res[t]["foreign_targets"] == 0
                  and res[t]["cf_bad"] == res["expected_cf_bad"]
                  and res[t]["validate_family_fail"] == 0 for t in ("composed", "flattened"))
json.dump(res, open(os.path.join(out_dir, "composition_check.json"), "w"), indent=1, default=str)
print(json.dumps(res, indent=1, default=str))
