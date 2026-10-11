# T6e 方案 B（R1 修回，2026-10-05）：按 NIST STEP File Analyzer（SFA）开源实现的「Associated Geometry」遍历规则
#   重实现标注→面集合，与我方 13 产出的 graph.json 逐条比对（一致／我方超集／我方子集／交叉／不相交）。
# ⚠️ 这是规则的重实现，不是 SFA 的运行输出；不得表述为「已用 SFA 验证」。
# 移植来源：github.com/usnistgov/SFA，Release 5.51（仓库 HEAD 72375d17c09c，2026-09-14）；
#   source/sfa-geom.tcl（sha256 df5c02b356d402b6…，最后修改 commit cef7878f49）L2–89 getAssocGeom、L92–122 relatedShapeAspect、
#   L125–166 getAssocGeomFace；入口：sfa-dimtol.tcl L923–962（dimensional_size／_location）、sfa-geotol.tcl L292（toleranced_shape_aspect）、
#   L998（datum_feature）。函数内注释的「L」号均指上述文件。
# STEP 分词复用 13 的解析层（runpy，只取 graph/back/split_args/refs_in），遍历规则在本文件独立实现，不调用 13 的 shape_aspect_faces。
# 复合实例的 SFA 类型名按「去掉超类型后叶类型小写、按字母序以 _and_ 连接」模拟 IFCsvr〔推测；另输出全组件连接口径的敏感性计数〕。
# 用法: python 50_sfa_rule_assoc.py <step_dir> <e1_dir(r1b graph+match)> <faces_dir> <out_dir> [<crosscheck.json> <e11.json> <v4_e1_dir> <r1_e1_dir>]
import glob
import json
import os
import runpy
import sys
import tempfile
import contextlib
import io
from collections import Counter, defaultdict

import numpy as np

step_dir, e1_dir, faces_dir, out_dir = sys.argv[1:5]
xcheck_p = sys.argv[5] if len(sys.argv) > 5 else None
e11_p = sys.argv[6] if len(sys.argv) > 6 else None
extra_dirs = {"v4": sys.argv[7] if len(sys.argv) > 7 else None, "r1": sys.argv[8] if len(sys.argv) > 8 else None}
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(out_dir, exist_ok=True)

# 超类型（仅本规则判型用到的那几族）
SUPERS = {"SHAPE_ASPECT", "COMPOSITE_SHAPE_ASPECT", "GEOMETRIC_TOLERANCE", "REPRESENTATION_ITEM",
          "GEOMETRIC_REPRESENTATION_ITEM", "SHAPE_ASPECT_RELATIONSHIP"}
LEAF_OVER = {"SHAPE_ASPECT": lambda ts: any(t != "SHAPE_ASPECT" and ("SHAPE_ASPECT" in t or "DATUM" in t or t in (
    "CENTRE_OF_SYMMETRY", "GEOMETRIC_ALIGNMENT", "APEX", "TANGENT", "PERPENDICULAR_TO", "PARALLEL_OFFSET")) for t in ts),
             "COMPOSITE_SHAPE_ASPECT": lambda ts: "COMPOSITE_GROUP_SHAPE_ASPECT" in ts or "CONTINUOS_SHAPE_ASPECT" in ts,
             "SHAPE_ASPECT_RELATIONSHIP": lambda ts: any(t != "SHAPE_ASPECT_RELATIONSHIP" and "RELATIONSHIP" in t for t in ts)}
SAR_FAMILY = {"SHAPE_ASPECT_RELATIONSHIP", "SHAPE_ASPECT_DERIVING_RELATIONSHIP", "DIMENSIONAL_LOCATION",
              "ANGULAR_LOCATION", "DIMENSIONAL_LOCATION_WITH_PATH", "DIRECTED_DIMENSIONAL_LOCATION",
              "FEATURE_COMPONENT_RELATIONSHIP", "SHAPE_ASPECT_TRANSITION"}


def load13(stp):
    os.environ["STEP_SAR_EXPAND"] = "down"
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
    argv0, sys.argv = sys.argv, ["13_step_graph.py", stp, tmp]
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            ns = runpy.run_path(os.path.join(HERE, "13_step_graph.py"), run_name="step13")
    finally:
        sys.argv = argv0
        os.unlink(tmp)
    return ns


class Rule:
    def __init__(self, ns):
        self.g, self.back = ns["graph"], ns["back"]
        self.split, self.refs = ns["split_args"], ns["refs_in"]
        self.stats = Counter()

    def T(self, sid, mode="leaf"):
        comps = [t for t, _ in self.g.get(sid, [])]
        if not comps:
            return ""
        if len(comps) == 1:
            return comps[0].lower()
        ts = set(comps)
        if mode == "leaf":
            ts = {t for t in ts if not (t in LEAF_OVER and LEAF_OVER[t](ts)) and t not in ("REPRESENTATION_ITEM",)}
        return "_and_".join(sorted(t.lower() for t in ts))

    def args_of(self, sid, pred):
        for t, a in self.g.get(sid, []):
            if pred(t):
                return t, self.split(a)
        return None, None

    def sar_users(self, sa):
        """GetUsedIn shape_aspect_relationship relating_shape_aspect（含子类型实例）→ [(e0, related_ref)]"""
        out = []
        for u in self.back.get(sa, []):
            t, a = self.args_of(u, lambda t: t in SAR_FAMILY)
            if a and len(a) >= 4 and sa in self.refs(a[2]):
                rel = self.refs(a[3])
                out.append((u, rel[0] if rel else None))
        return out

    def first_block(self, t):
        # L15–17
        return (t in ("shape_aspect", "all_around_shape_aspect", "centre_of_symmetry", "geometric_alignment")
                or "_occurrence" in t or ("datum" in t and "_and_" not in t))

    def cpsa_target(self, sid):
        _, a = self.args_of(sid, lambda t: t == "COMPONENT_PATH_SHAPE_ASPECT")
        r = self.refs(a[5]) if a and len(a) >= 6 else []   # Attributes Item 6（1 起）＝component_shape_aspect
        return r[0] if r else None

    def get_assoc_geom(self, ent, acc):
        # L2–89 getAssocGeom
        t = self.T(ent)
        if self.first_block(t):
            if t == "datum":   # L30–41：datum → 经 SAR(related=datum) 找 relating 的 datum_feature
                for u in self.back.get(ent, []):
                    _, a = self.args_of(u, lambda x: x in SAR_FAMILY)
                    if a and len(a) >= 4 and ent in self.refs(a[3]) and "relationship" in self.T(u):
                        for r in self.refs(a[2]):
                            if self.T(r) == "datum_feature":
                                ent = r
            self.assoc_face(ent, acc)           # L44
        acc["ents"].add(ent)                    # L49 appendAssocGeom D
        for e0, rel in self.sar_users(ent):     # L50–80
            if "relationship" not in self.T(e0):
                self.stats["sar_user_skipped_not_relationship_type"] += 1
                continue
            if rel is None:
                continue
            relT, a00 = self.T(rel), rel
            if relT == "component_path_shape_aspect":   # L60–65
                acc["ents"].add(rel)
                a00 = self.cpsa_target(rel)
                self.stats["cpsa_related"] += 1
                if a00 is None:
                    continue
                relT = self.T(a00)
            self.related_sa(relT, a00, acc)
        if t == "component_path_shape_aspect":  # L83–87
            a0 = self.cpsa_target(ent)
            if a0 is not None:
                self.related_sa(self.T(a0), a0, acc)

    def related_sa(self, relT, val, acc):
        # L92–122 relatedShapeAspect：只下行一层；若 related 是复合体／COS，再下行一层取其成员，不再递归
        acc["ents"].add(val)
        vals = []
        if "composite_shape_aspect" in relT or "composite_group_shape_aspect" in relT or "centre_of_symmetry" in relT:
            for e1, r in self.sar_users(val):
                if "relationship" not in self.T(e1) or r is None:
                    continue
                if self.T(r) == "component_path_shape_aspect":
                    r = self.cpsa_target(r)
                    if r is None:
                        continue
                vals.append(r)
                acc["ents"].add(r)
            if "centre_of_symmetry" in relT:
                vals.append(val)
        else:
            vals.append(val)
        for v in vals:
            self.assoc_face(v, acc)

    def assoc_face(self, sa, acc):
        # L125–166 getAssocGeomFace：definition＝sa 的 GISU/IIRU → identified_item
        for u in self.back.get(sa, []):
            _, a = self.args_of(u, lambda t: t in ("GEOMETRIC_ITEM_SPECIFIC_USAGE", "ITEM_IDENTIFIED_REPRESENTATION_USAGE"))
            if a and len(a) >= 5 and sa in self.refs(a[2]):
                for it in self.refs(a[4]):
                    if self.T(it) == "advanced_face":
                        acc["faces"].add(it)
                    else:
                        acc["nonface"].add(it)

    def start(self, sid, kind):
        """入口：dimtol L923–962、geotol L292/L998"""
        acc = {"faces": set(), "nonface": set(), "ents": set()}
        if kind == "DATUM_FEATURE":
            self.get_assoc_geom(sid, acc)
        elif kind == "DIMENSIONAL_SIZE":
            _, a = self.args_of(sid, lambda t: t in ("DIMENSIONAL_SIZE", "ANGULAR_SIZE"))
            for val in (self.refs(a[0]) if a else []):
                self.get_assoc_geom(val, acc)
                if not acc["ents"] and not acc["faces"] and not acc["nonface"]:   # L938–950 回退（实际几乎不触发）
                    self.stats["dimsize_fallback"] += 1
                    for _, rel in self.sar_users(val):
                        if rel is not None:
                            self.get_assoc_geom(rel, acc)
        elif kind == "DIMENSIONAL_LOCATION":
            _, a = self.args_of(sid, lambda t: t in ("DIMENSIONAL_LOCATION", "ANGULAR_LOCATION",
                                                     "DIMENSIONAL_LOCATION_WITH_PATH", "DIRECTED_DIMENSIONAL_LOCATION",
                                                     "SHAPE_ASPECT_RELATIONSHIP"))
            for val in ([r for x in a[2:4] for r in self.refs(x)] if a and len(a) >= 4 else []):
                self.get_assoc_geom(val, acc)
        else:   # 几何公差：toleranced_shape_aspect（第 4 参数）
            for t, aa in self.g.get(sid, []):
                if "TOLERANCE" in t:
                    a = self.split(aa)
                    if len(a) >= 4:
                        for val in self.refs(a[3]):
                            self.get_assoc_geom(val, acc)
                        break
        return acc


def relation(ours, sfa):
    ours, sfa = set(ours), set(sfa)
    if ours == sfa:
        return "equal_empty" if not ours else "equal"
    if not sfa:
        return "sfa_empty"
    if not ours:
        return "ours_empty"
    if ours > sfa:
        return "ours_superset"
    if ours < sfa:
        return "ours_subset"
    return "overlap" if ours & sfa else "disjoint"


def face_area(faces_json):
    d = json.load(open(faces_json))
    area = {}
    for f in d["faces"]:
        v = np.asarray(f["verts"], float)
        t = np.asarray(f["tris"], int)
        area[f["index"]] = float(0.5 * np.linalg.norm(np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]]), axis=1).sum()) if len(t) else 0.0
    return area


xrows = {}
if xcheck_p and os.path.exists(xcheck_p):
    for r in json.load(open(xcheck_p))["rows"]:
        xrows[(r["model"], r["stepId"])] = r
e11 = json.load(open(e11_p)) if e11_p and os.path.exists(e11_p) else None
e11_keys = {(g["model"], int(g["stepId"].lstrip("#"))) for g in e11["groups"]} if e11 else set()

rows, naming_diff = [], Counter()
for gj in sorted(glob.glob(os.path.join(e1_dir, "*ap242*.graph.json"))):
    base = os.path.basename(gj)[:-len(".graph.json")]
    stp = os.path.join(step_dir, base + ".stp")
    if not os.path.exists(stp) or not os.path.exists(os.path.join(e1_dir, base + ".match.json")):
        continue   # ftc_08-e1-tg（无 B-rep、无 match）不参与语义层
    ns = load13(stp)
    rule = Rule(ns)
    for sid in rule.g:
        if len(rule.g[sid]) > 1 and any("SHAPE_ASPECT" in t or "DATUM" in t for t, _ in rule.g[sid]):
            a, b = rule.T(sid, "leaf"), rule.T(sid, "all")
            naming_diff["complex_sa"] += 1
            if rule.first_block(a) != rule.first_block(b):
                naming_diff["first_block_differs"] += 1
    ours = {a["stepId"]: a for a in json.load(open(gj))["annotations"]}
    extra = {k: ({a["stepId"]: a for a in json.load(open(os.path.join(d, base + ".graph.json")))["annotations"]}
                 if d and os.path.exists(os.path.join(d, base + ".graph.json")) else None) for k, d in extra_dirs.items()}
    match = json.load(open(os.path.join(e1_dir, base + ".match.json")))
    s2o = {v: int(k) for k, v in match["occ_to_step"].items()}
    fj = os.path.join(faces_dir, base + ".faces.json")
    area = face_area(fj) if os.path.exists(fj) else {}
    scale_area = 1.0
    for sid, a in sorted(ours.items()):
        if a["type"] == "DATUM":
            continue
        acc = rule.start(sid, a["type"])
        sf, of = sorted(acc["faces"]), a.get("faceIds", [])

        def ar(ids):
            if not area:
                return None
            occ = [s2o[i] for i in ids if i in s2o]
            return round(sum(area.get(o, 0.0) for o in occ) * scale_area, 4)
        row = {"model": base, "stepId": sid, "type": a["type"], "dimName": a.get("dimName"),
               "anchor_ours": a.get("anchorKind"), "n_ours": len(of), "n_sfa": len(sf),
               "rel": relation(of, sf), "only_ours": sorted(set(of) - set(sf)), "only_sfa": sorted(set(sf) - set(of)),
               "sfa_nonface": sorted(acc["nonface"]), "ours_nonface": a.get("nonFaceAnchorIds", []),
               "nonface_rel": relation(a.get("nonFaceAnchorIds", []), acc["nonface"]),
               "in_e11": (base, sid) in e11_keys}
        for k, ex in extra.items():
            if ex is not None and sid in ex:
                row[f"rel_{k}"] = relation(ex[sid].get("faceIds", []), sf)
        x = xrows.get((base, sid))
        if x and x.get("nist_area"):
            na = x["nist_area"]
            row["nist_area"] = na
            row["area_ours"], row["area_sfa"] = ar(of), ar(sf)
            row["ok2_ours"] = row["area_ours"] is not None and abs(row["area_ours"] / na - 1) <= 0.02
            row["ok2_sfa"] = row["area_sfa"] is not None and abs(row["area_sfa"] / na - 1) <= 0.02
        rows.append(row)
    for k, v in rule.stats.items():
        naming_diff["stat_" + k] += v
    print(f"[50] {base} annos={sum(1 for r in rows if r['model'] == base)}", flush=True)


def tally(rs, key="rel"):
    return dict(Counter(r[key] for r in rs))


summ = {"n": len(rows), "rel": tally(rows), "nonface_rel": tally(rows, "nonface_rel"),
        "by_type": {t: tally([r for r in rows if r["type"] == t]) for t in sorted({r["type"] for r in rows})},
        "e11": {"n": sum(r["in_e11"] for r in rows), "rel": tally([r for r in rows if r["in_e11"]])},
        "ftc_08_11": {m: {"n": len(rs), "rel": tally(rs), "e11_rel": tally([r for r in rs if r["in_e11"]])}
                      for m in sorted({r["model"] for r in rows if any(f"ftc_{i:02d}" in r["model"] for i in (8, 9, 10, 11))})
                      for rs in [[r for r in rows if r["model"] == m]]},
        "naming_sensitivity": dict(naming_diff)}
for k in extra_dirs:
    rr = [r for r in rows if f"rel_{k}" in r]
    if rr:
        summ[f"rel_{k}_vs_sfa"] = tally(rr, f"rel_{k}")
        summ[f"rel_{k}_vs_sfa_e11"] = tally([r for r in rr if r["in_e11"]], f"rel_{k}")
wa = [r for r in rows if "nist_area" in r]
summ["nist_area"] = {"n": len(wa), "ok2_ours": sum(r["ok2_ours"] for r in wa), "ok2_sfa": sum(r["ok2_sfa"] for r in wa),
                     "differ_sets_with_area": [{k: r[k] for k in ("model", "stepId", "type", "rel", "n_ours", "n_sfa",
                                                                  "area_ours", "area_sfa", "nist_area", "ok2_ours", "ok2_sfa")}
                                               for r in wa if r["rel"] not in ("equal", "equal_empty")]}
summ["non_equal"] = [{k: r[k] for k in ("model", "stepId", "type", "dimName", "rel", "n_ours", "n_sfa", "only_ours",
                                        "only_sfa", "in_e11")} for r in rows if r["rel"] not in ("equal", "equal_empty")]
json.dump(rows, open(os.path.join(out_dir, "sfa_rule_assoc.json"), "w"), indent=1)
json.dump(summ, open(os.path.join(out_dir, "sfa_rule_assoc.summary.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: summ[k] for k in ("n", "rel", "nonface_rel", "e11", "naming_sensitivity")}, ensure_ascii=False))
print("[50] DONE", "nist_area", {k: summ["nist_area"][k] for k in ("n", "ok2_ours", "ok2_sfa")})
