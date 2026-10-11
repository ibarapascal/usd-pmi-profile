# R1 T8c（回应 R2-9）：扫描 P2（hoops_core）convertMetadata=true 产物里的 PMI 相关内容，并与默认配置产物逐件 diff。
# 输入由 49_p2_metadata.ps1 在 Windows 工作站产出后拷回；默认配置对照可用同会话重转（batch-default-r1）或 7 月存档
# （archive/v1-pilot/pilot/out/batch_v2/omni/）。
# 扫描面（比 09/26 宽，回应 R2-9「inspection criteria」）：全部 prim 的 authored 属性（名＋类型＋值样例）、
#   prim metadata（customData、assetInfo、其余非默认键）、layer customLayerData、关系名与目标、GeomSubset。
# 判定（逐属性）：PMI 相关＝名或字符串值命中关键词/符号；typed＝值为数值类型且语义可归为公差/尺寸/基准；
#   面关联＝属性所在 prim 是 GeomSubset 或有关系指向面集合（否则只是挂在 prim 上的字符串 metadata）。
# 用法: .venv/bin/python 49_p2_metadata.py <meta_dir> <default_dir> <out.json>
#   meta_dir 下文件名形如 <name>.meta.usdc；default_dir 下 <name>.default.usdc 或 <name>.usdc（7 月存档名）。
import glob
import json
import os
import re
import sys

from pxr import Sdf, Usd, UsdGeom

KW = re.compile(r"toleran|datum|dimension|pmi|annotat|gd&?t|gdt|flatness|perpendicular|parallel|"
                r"position|profile|runout|concentric|symmetr|cylindricity|straightness|angularity|"
                r"±|Ø|⌀|⌖|⏥|⌓", re.I)   # ± Ø ⌀ ⌖ ⏥ ⌓
NUMERIC = {"double", "float", "half", "int", "uint", "int64", "uint64", "double[]", "float[]", "int[]"}
BIG = {"points", "normals", "faceVertexIndices", "faceVertexCounts", "primvars:st", "extent",
       "primvars:normals", "indices", "primvars:displayColor"}


def sample(v, n=160):
    s = repr(v)
    return s if len(s) <= n else s[:n] + "…"


def scan(path):
    st = Usd.Stage.Open(path)
    lay = st.GetRootLayer()
    rec = {"file": os.path.basename(path), "bytes": os.path.getsize(path),
           "customLayerData": {k: sample(v) for k, v in (lay.customLayerData or {}).items()},
           "prims": 0, "meshes": 0, "subsets": 0, "attrs": {}, "rels": [], "prim_meta": [],
           "pmi_hits": []}
    for p in st.Traverse(Usd.TraverseInstanceProxies(Usd.PrimAllPrimsPredicate)):
        rec["prims"] += 1
        if p.IsA(UsdGeom.Mesh):
            rec["meshes"] += 1
        is_subset = p.IsA(UsdGeom.Subset)
        rec["subsets"] += int(is_subset)
        md = p.GetAllAuthoredMetadata()
        for k in ("customData", "assetInfo"):
            if k in md and md[k]:
                rec["prim_meta"].append({"prim": str(p.GetPath()), "key": k, "value": sample(md[k], 400)})
                if KW.search(json.dumps(md[k], default=str)):
                    rec["pmi_hits"].append({"prim": str(p.GetPath()), "where": f"metadata:{k}",
                                            "value": sample(md[k], 400)})
        for r in p.GetAuthoredRelationships():
            rec["rels"].append({"prim": str(p.GetPath()), "name": r.GetName(),
                                "targets": [str(t) for t in r.GetTargets()][:5]})
        for a in p.GetAuthoredAttributes():
            nm, tn = a.GetName(), str(a.GetTypeName())
            key = (str(p.GetPath()), nm)
            v = None if nm in BIG else a.Get()
            rec["attrs"][f"{key[0]}.{nm}"] = {"type": tn, "custom": a.IsCustom(),
                                             "value": None if v is None else sample(v)}
            text = nm + " " + ("" if v is None or tn not in ("string", "token", "string[]", "token[]", "asset")
                               else str(v))
            if KW.search(text):
                prim_rels = [r.GetName() for r in p.GetAuthoredRelationships()]
                rec["pmi_hits"].append({
                    "prim": key[0], "prim_type": p.GetTypeName(), "attr": nm, "type": tn,
                    "value": None if v is None else sample(v),
                    "typed_numeric": tn in NUMERIC,
                    "on_geomsubset": is_subset,
                    "prim_relationships": prim_rels,
                    "namespace": nm.rsplit(":", 1)[0] if ":" in nm else ""})
    rec["n_attrs"] = len(rec["attrs"])
    return rec


def find_default(ddir, name):
    for c in (f"{name}.default.usdc", f"{name}.usdc"):
        p = os.path.join(ddir, c)
        if os.path.exists(p):
            return p
    return None


def main():
    mdir, ddir, out = sys.argv[1:4]
    rows = []
    for mp in sorted(glob.glob(os.path.join(mdir, "*.meta.usdc"))):
        name = os.path.basename(mp)[:-len(".meta.usdc")]
        m = scan(mp)
        dp = find_default(ddir, name)
        d = scan(dp) if dp else None
        row = {"model": name, "meta": {k: m[k] for k in ("bytes", "prims", "meshes", "subsets", "n_attrs",
                                                          "customLayerData")},
               "pmi_hits": m["pmi_hits"], "prim_meta": m["prim_meta"][:50], "rels": m["rels"][:50]}
        if d:
            new_keys = sorted(set(m["attrs"]) - set(d["attrs"]))
            gone_keys = sorted(set(d["attrs"]) - set(m["attrs"]))
            changed = sorted(k for k in set(m["attrs"]) & set(d["attrs"])
                             if m["attrs"][k]["value"] != d["attrs"][k]["value"])
            ns = {}
            for k in new_keys:
                nm = k.rsplit(".", 1)[1]
                ns[nm.rsplit(":", 1)[0] if ":" in nm else "(none)"] = ns.get(
                    nm.rsplit(":", 1)[0] if ":" in nm else "(none)", 0) + 1
            row["default"] = {"file": os.path.basename(dp), "bytes": d["bytes"], "prims": d["prims"],
                              "meshes": d["meshes"], "subsets": d["subsets"], "n_attrs": d["n_attrs"],
                              "customLayerData": d["customLayerData"]}
            row["diff"] = {"new_attrs": len(new_keys), "removed_attrs": len(gone_keys),
                           "changed_values": len(changed), "new_attr_namespaces": ns,
                           "new_attr_examples": [{"key": k, **m["attrs"][k]} for k in new_keys[:40]],
                           "changed_examples": [{"key": k, "meta": m["attrs"][k]["value"],
                                                 "default": d["attrs"][k]["value"]} for k in changed[:10]],
                           "prim_meta_new": len(m["prim_meta"]) - len(d["prim_meta"]),
                           "rels_new": len(m["rels"]) - len(d["rels"])}
        rows.append(row)
        h = row["pmi_hits"]
        print(f"[49] {name} prims={m['prims']} attrs={m['n_attrs']} pmi_hits={len(h)} "
              f"typed={sum(1 for x in h if x.get('typed_numeric'))} "
              f"on_subset={sum(1 for x in h if x.get('on_geomsubset'))} "
              + (f"new_attrs={row['diff']['new_attrs']}" if d else "no-default"))
    summ = {"models": len(rows),
            "models_with_pmi_hits": sum(1 for r in rows if r["pmi_hits"]),
            "pmi_hits": sum(len(r["pmi_hits"]) for r in rows),
            "typed_numeric_hits": sum(1 for r in rows for x in r["pmi_hits"] if x.get("typed_numeric")),
            "hits_on_geomsubset": sum(1 for r in rows for x in r["pmi_hits"] if x.get("on_geomsubset")),
            "hits_with_relationship": sum(1 for r in rows for x in r["pmi_hits"] if x.get("prim_relationships")),
            "new_attrs_total": sum(r.get("diff", {}).get("new_attrs", 0) for r in rows),
            "geomsubsets_total": sum(r["meta"]["subsets"] for r in rows)}
    json.dump({"summary": summ, "rows": rows}, open(out, "w"), indent=1, ensure_ascii=False)
    print("[49] SUMMARY", summ)


if __name__ == "__main__":
    main()
