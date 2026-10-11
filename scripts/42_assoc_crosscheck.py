# T6a（R1 修回，2026-10-05）：标注→面关联的三方独立核查
#   ① v4 graph（13 旧版 SAR 双向展开，out/e1/*.graph.json 冻结件）
#   ② 下行-only（13 现版 STEP_SAR_EXPAND=down，本脚本内 runpy 现算）
#   ③ NIST 参照＝STEP 文件内嵌 CAx-IF「pmi validation property」（导出 CAD 系统自写，与本解析器无关）：
#      'affected area'（关联面面积和）＋'equivalent unicode string'（含 nX 实例数）
# 我方面积＝关联 STEP 面经 match.json 映射到 OCC 面后，逐面镶嵌网格（faces.json，float64）的三角形面积和。
# 实例数＝关联面按共享顶点（1e-4 mm 圆整）连通分量计数。
# 另核：13 在 STEP_SAR_EXPAND=both 下须逐条复现 v4 graph.json 的 faceIds（开关正确性断言）。
# 用法: python 42_assoc_crosscheck.py <step_dir> <faces_dir> <e1_dir> <out_dir>
import glob
import json
import os
import re
import runpy
import sys
import tempfile
from collections import Counter, defaultdict

import numpy as np

step_dir, faces_dir, e1_dir, out_dir = sys.argv[1:5]
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(out_dir, exist_ok=True)
TOLS = (0.02, 0.05)          # 面积比判定带：|ratio−1| ≤ 2%（主）／5%（宽）


def run13(stp, mode):
    os.environ["STEP_SAR_EXPAND"] = mode
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
    argv0 = sys.argv
    sys.argv = ["13_step_graph.py", stp, tmp]
    try:
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):
            ns = runpy.run_path(os.path.join(HERE, "13_step_graph.py"), run_name="step13")
    finally:
        sys.argv = argv0
        os.unlink(tmp)
    return ns


def decode_step_str(s):
    """STEP \\X2\\hhhh…\\X0\\ 编码 → unicode"""
    def rep(m):
        h = m.group(1)
        return "".join(chr(int(h[i:i + 4], 16)) for i in range(0, len(h), 4))
    return re.sub(r"\\X2\\([0-9A-Fa-f]+)\\X0\\", rep, s or "")


def validation_props(ns):
    """target_id → {item_name: value}；面积换算成 mm²"""
    graph, back = ns["graph"], ns["back"]
    split_args, refs_in, sstr, unit_to_mm = ns["split_args"], ns["refs_in"], ns["sstr"], ns["unit_to_mm"]
    out = defaultdict(dict)
    for sid, comps in graph.items():
        for t, a in comps:
            if t != "PROPERTY_DEFINITION":
                continue
            args = split_args(a)
            if not args or sstr(args[0]) != "pmi validation property":
                continue
            tgt = refs_in(args[2])[0] if len(args) > 2 and refs_in(args[2]) else None
            for u in back.get(sid, []):
                for t2, a2 in graph.get(u, []):
                    if t2 != "PROPERTY_DEFINITION_REPRESENTATION":
                        continue
                    for rep in refs_in(split_args(a2)[1]):
                        for t3, a3 in graph.get(rep, []):
                            if "REPRESENTATION" not in t3:
                                continue
                            ra = split_args(a3)
                            if len(ra) < 2:
                                continue
                            for it in refs_in(ra[1]):
                                for t4, a4 in graph.get(it, []):
                                    ia = split_args(a4)
                                    nm = sstr(ia[0]) if ia else None
                                    if not nm:
                                        continue
                                    if t4 == "MEASURE_REPRESENTATION_ITEM" and "AREA_MEASURE" in a4:
                                        v = float(re.search(r"AREA_MEASURE\(\s*([-\d.Ee+]+)", a4).group(1))
                                        k = None
                                        uref = refs_in(ia[-1])
                                        if uref:
                                            for t5, a5 in graph.get(uref[0], []):
                                                if t5 == "DERIVED_UNIT":
                                                    for de in refs_in(a5):
                                                        dea = ns["comp_args"](de, "DERIVED_UNIT_ELEMENT")
                                                        if dea:
                                                            lu = refs_in(dea[0])[0]
                                                            ex = float(dea[1])
                                                            mm, _ = unit_to_mm(lu)
                                                            if mm is not None:
                                                                k = mm ** ex
                                        out[tgt][nm] = v * k if k is not None else None
                                        out[tgt][nm + "_raw"] = v
                                    elif t4 == "DESCRIPTIVE_REPRESENTATION_ITEM":
                                        out[tgt][nm] = decode_step_str(sstr(ia[1]) if len(ia) > 1 else "")
                                    else:
                                        m = re.search(r"MEASURE\(\s*([-\d.Ee+]+)", a4)
                                        if m:
                                            out[tgt][nm] = float(m.group(1))
    return out


def face_geom(faces_json):
    d = json.load(open(faces_json))
    area, vkeys = {}, {}
    for f in d["faces"]:
        v = np.asarray(f["verts"], float)
        t = np.asarray(f["tris"], int)
        if len(t):
            a = v[t[:, 1]] - v[t[:, 0]]
            b = v[t[:, 2]] - v[t[:, 0]]
            area[f["index"]] = float(0.5 * np.linalg.norm(np.cross(a, b), axis=1).sum())
        else:
            area[f["index"]] = 0.0
        vkeys[f["index"]] = {tuple(x) for x in np.round(v, 4).tolist()}
    return area, vkeys


def n_components(occ_ids, vkeys):
    occ_ids = list(occ_ids)
    parent = {i: i for i in occ_ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    owner = {}
    for i in occ_ids:
        for k in vkeys.get(i, ()):
            if k in owner:
                parent[find(i)] = find(owner[k])
            else:
                owner[k] = i
    return len({find(i) for i in occ_ids})


def nx_of(s):
    """'DIM\\w4X ⌀0.415 ±0.008' → 4；无 nX 前缀记 1"""
    m = re.search(r"(?<![\d.])(\d+)\s*[Xx×](?=\s|⌀|↧|$)", s or "")
    return int(m.group(1)) if m else (1 if s else None)


def datum_of_df(ns, df):
    """DATUM_FEATURE 自身无校验属性时，取 SAR(relating=DF, related=DATUM) 的 DATUM（CAx-IF 把属性挂在 DATUM 上）"""
    out = []
    for u in ns["back"].get(df, []):
        for t, a in ns["graph"].get(u, []):
            if t == "SHAPE_ASPECT_RELATIONSHIP":
                args = ns["split_args"](a)
                if len(args) >= 4 and df in ns["refs_in"](args[2]):
                    out += [r for r in ns["refs_in"](args[3]) if "DATUM" in ns["types_of"](r)]
    return out


def upward_hops(ns, sa_ids):
    """以 v4 双向规则遍历，记录「成员→复合体」上爬所经 SAR 的名字（诊断多关联来源）"""
    graph, back, split_args, refs_in, sstr, types_of = (ns[k] for k in
        ("graph", "back", "split_args", "refs_in", "sstr", "types_of"))
    SA_LIKE = ns["SA_LIKE"]
    hops, seen, stack = [], set(), list(sa_ids)
    while stack:
        s = stack.pop()
        if s in seen:
            continue
        seen.add(s)
        for u in back.get(s, []):
            ut = types_of(u)
            if "SHAPE_ASPECT_DERIVING_RELATIONSHIP" in ut:
                a = ns["comp_args"](u, "SHAPE_ASPECT_DERIVING_RELATIONSHIP")
                if a and len(a) >= 4 and s in refs_in(a[2]):
                    stack += refs_in(a[3])
            if "SHAPE_ASPECT_RELATIONSHIP" in ut or "COMPONENT_PATH_SHAPE_ASPECT" in ut:
                for t, a in graph[u]:
                    if "SHAPE_ASPECT_RELATIONSHIP" in t:
                        args = split_args(a)
                        if len(args) < 4:
                            continue
                        rel_g, rel_d = refs_in(args[2]), refs_in(args[3])
                        if s in rel_g:
                            stack += [o for o in rel_d if types_of(o) & SA_LIKE]
                        if s in rel_d:
                            up = [o for o in rel_g if types_of(o) & SA_LIKE]
                            if up:
                                hops.append({"sar": u, "name": sstr(args[0]), "from": s, "to": up})
                            stack += up
    return hops


def sa_ids_of(ns, sid, kind):
    """与 13 同口径取标注的 shape_aspect 入口"""
    ca, refs_in, split_args = ns["comp_args"], ns["refs_in"], ns["split_args"]
    if kind == "DATUM_FEATURE":
        return [sid]
    if kind in ("DIMENSIONAL_SIZE", "DIMENSIONAL_LOCATION"):
        a = ca(sid, kind)
        if not a:
            return []
        if kind == "DIMENSIONAL_SIZE":
            return refs_in(a[0])
        return [r for x in a[2:4] for r in refs_in(x)] if len(a) >= 4 else refs_in(" ".join(a))
    for t, a in ns["graph"].get(sid, []):
        if "TOLERANCE" in t and t not in ns["SUPPORT"]:
            args = split_args(a)
            if len(args) >= 4:
                return refs_in(args[3])
    return []


rows, sanity = [], Counter()
for gj in sorted(glob.glob(os.path.join(e1_dir, "*ap242*.graph.json"))):
    base = os.path.basename(gj)[:-len(".graph.json")]
    if base.endswith("-tg"):
        continue
    stp = os.path.join(step_dir, base + ".stp")
    v4 = {a["stepId"]: a for a in json.load(open(gj))["annotations"]}
    match = json.load(open(os.path.join(e1_dir, base + ".match.json")))
    s2o = {int(v): int(k) for k, v in match["occ_to_step"].items()}
    area, vkeys = face_geom(os.path.join(faces_dir, base + ".faces.json"))

    ns_b = run13(stp, "both")
    both = {a["stepId"]: a for a in ns_b["result"]}
    for sid, a in v4.items():
        sanity["both_eq_v4" if both.get(sid, {}).get("faceIds") == a.get("faceIds") else "both_ne_v4"] += 1
    ns_d = run13(stp, "down")
    down = {a["stepId"]: a for a in ns_d["result"]}
    vp = validation_props(ns_d)

    for sid, a in sorted(v4.items()):
        if a["type"] == "DATUM":
            continue
        d = down.get(sid, {})
        prop = vp.get(sid, {})
        prop_src = "self" if prop else None
        if not prop and a["type"] == "DATUM_FEATURE":
            for dt in datum_of_df(ns_d, sid):
                if vp.get(dt):
                    prop, prop_src = vp[dt], f"DATUM#{dt}"
                    break
        rec = {"model": base, "stepId": sid, "type": a["type"], "dimName": a.get("dimName"),
               "anchor_v4": a.get("anchorKind"), "anchor_down": d.get("anchorKind")}
        for tag, fids in (("v4", a.get("faceIds", [])), ("down", d.get("faceIds", []))):
            occ = [s2o[f] for f in fids if f in s2o]
            rec[f"n_{tag}"] = len(fids)
            rec[f"unmapped_{tag}"] = len(fids) - len(occ)
            rec[f"area_{tag}"] = round(sum(area.get(o, 0.0) for o in occ), 4)
            rec[f"inst_{tag}"] = n_components(occ, vkeys) if occ else 0
        rec["down_subset_v4"] = set(d.get("faceIds", [])) <= set(a.get("faceIds", []))
        rec["nist_area"] = prop.get("affected area")
        rec["nist_ues"] = prop.get("equivalent unicode string")
        rec["nist_nx"] = nx_of(rec["nist_ues"]) if rec["nist_ues"] else None
        rec["has_prop"] = bool(prop)
        rec["prop_src"] = prop_src
        if rec["nist_area"]:
            for tag in ("v4", "down"):
                r = rec[f"area_{tag}"] / rec["nist_area"]
                rec[f"ratio_{tag}"] = round(r, 4)
                rec[f"ok_{tag}"] = abs(r - 1) <= TOLS[0]
                rec[f"ok5_{tag}"] = abs(r - 1) <= TOLS[1]
        if rec["n_v4"] != rec["n_down"]:
            rec["upward_hops"] = upward_hops(ns_d, sa_ids_of(ns_d, sid, a["type"]))
        rows.append(rec)
    print(f"[42] {base}: annos={len(v4)} props={len(vp)}", flush=True)

json.dump({"sanity": dict(sanity), "rows": rows}, open(os.path.join(out_dir, "assoc_crosscheck.json"), "w"),
          indent=1, default=list)

# ---- 汇总 ----
S = {"sanity": dict(sanity), "annos_nondatum": len(rows)}
fa = [r for r in rows if r["anchor_v4"] == "face"]
S["face_anchored_v4"] = len(fa)
S["face_anchored_down"] = sum(1 for r in rows if r["anchor_down"] == "face")
S["targets_v4"] = sum(r["n_v4"] for r in rows)
S["targets_down"] = sum(r["n_down"] for r in rows)
S["changed"] = sum(1 for r in rows if r["n_v4"] != r["n_down"])
S["down_not_subset"] = sum(1 for r in rows if not r["down_subset_v4"])
S["down_empty_v4_face"] = sum(1 for r in fa if r["n_down"] == 0)
cmp_ = [r for r in rows if r.get("nist_area")]
S["with_nist_area"] = len(cmp_)
S["with_nist_area_zero"] = sum(1 for r in rows if r.get("nist_area") == 0)
for tag in ("v4", "down"):
    S[f"ok2_{tag}"] = sum(1 for r in cmp_ if r.get(f"ok_{tag}"))
    S[f"ok5_{tag}"] = sum(1 for r in cmp_ if r.get(f"ok5_{tag}"))
S["ok2_changed_v4"] = sum(1 for r in cmp_ if r.get("ok_v4") and r["n_v4"] != r["n_down"])
S["ok2_changed_down"] = sum(1 for r in cmp_ if r.get("ok_down") and r["n_v4"] != r["n_down"])
S["changed_with_area"] = sum(1 for r in cmp_ if r["n_v4"] != r["n_down"])
nxr = [r for r in rows if r.get("nist_nx") and r["n_down"]]
S["with_nx"] = len(nxr)
for tag in ("v4", "down"):
    S[f"nx_eq_{tag}"] = sum(1 for r in nxr if r[f"inst_{tag}"] == r["nist_nx"])
S["hop_sar_names"] = dict(Counter(re.sub(r"\d+", "N", h["name"] or "") for r in rows
                                   for h in r.get("upward_hops", [])))
S["by_model_changed"] = dict(Counter(r["model"] for r in rows if r["n_v4"] != r["n_down"]))
json.dump(S, open(os.path.join(out_dir, "assoc_crosscheck.summary.json"), "w"), indent=1)
print(json.dumps(S, indent=1))
