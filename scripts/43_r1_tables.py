# R1 修回（2026-10-05）轻量表与考证合集：T4 / T5 / T6c / T7b / T9 / T10。全部只读，不改任何既有产物。
#   t4   未对齐面诊断（19 个）＋已对齐 3824 对的类型/解析面几何一致性核查（OCC 镶嵌顶点到 STEP 解析面的距离）
#        2026-10-06（R4 外审 B-P1-3）：B 样条对（80）改为直接解析 STEP 的 B_SPLINE_SURFACE_WITH_KNOTS（简单／RATIONAL 复合）
#        并求顶点到该面的距离；summary 增 bspline_* 字段，解析面 resid_* 口径与值不变
#   t5   锚定清单：none / edge / part / typed 失败逐条列出，并给 none 条的源侧引用实体类型（机读证据）
#   t5b  what-if：DF→DATUM 上的 GISU 若也跟随，11 个 none 缺口里哪些可被解析出面（只算不改 13）
#   t6c  E11 重新归因：v4 ⇄ r1 逐组对照＋NIST 校验属性联表＋I-5（镶嵌 vs 估计器）判别
#   t7   16 件单位标注普查与量级合理性规则（哪些单位错配 stage 内可检出、哪些不能）
#   t9   C3 半径拟合在 float64（faces.json）与 float32（stage）下的中位误差对照
#   t10  0.06 mm 的参照对象（canonical 读出，零计算）
# 用法: python 43_r1_tables.py <step_dir> <faces_dir> <cyl_dir> <out_dir> [t4 t5 t6c t7 t9 t10]
# 依赖：13（runpy，取实体图与单位解析）、out/e1、out/e11、out/hole、out/r1/t6（42 产物）、v4 冻结件 out/r1/t6/v4-frozen
import glob
import json
import math
import os
import re
import runpy
import sys
import tempfile
from collections import Counter, defaultdict

import numpy as np

step_dir, faces_dir, cyl_dir, out_dir = sys.argv[1:5]
todo = set(sys.argv[5:]) or {"t4", "t5", "t5b", "t6c", "t7", "t9", "t10"}
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.makedirs(out_dir, exist_ok=True)
MODELS = sorted(os.path.basename(f)[:-len(".graph.json")] for f in glob.glob(os.path.join(ROOT, "out/e1/*ap242*.graph.json"))
                if not f.endswith("-tg.graph.json"))


def short(b):
    return b.replace("nist_", "").replace("_asme1_ap242", "")


def dump(name, obj):
    json.dump(obj, open(os.path.join(out_dir, name), "w"), indent=1, ensure_ascii=False, default=str)


def run13(stp):
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
    argv0, sys.argv = sys.argv, ["13_step_graph.py", stp, tmp]
    os.environ["STEP_SAR_EXPAND"] = "down"
    try:
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):
            ns = runpy.run_path(os.path.join(HERE, "13_step_graph.py"), run_name="step13")
    finally:
        sys.argv = argv0
        os.unlink(tmp)
    return ns


# =====================================================================================
# T4
# =====================================================================================
SURF = {"PLANE": "Plane", "CYLINDRICAL_SURFACE": "Cylinder", "CONICAL_SURFACE": "Cone",
        "SPHERICAL_SURFACE": "Sphere", "TOROIDAL_SURFACE": "Toroid"}


def step_entities(stp):
    txt = open(stp, encoding="utf-8", errors="replace").read()
    flat = re.sub(r"\s+", " ", txt.split("DATA;", 1)[1].split("ENDSEC;", 1)[0])
    ent = {}
    for m in re.finditer(r"#(\d+)\s*=\s*([A-Z0-9_]+)\s*\((.*?)\)\s*;", flat):
        ent[int(m.group(1))] = (m.group(2), m.group(3))
    angle_deg = bool(re.search(r"CONVERSION_BASED_UNIT\s*\(\s*'DEGREE", flat, re.I))
    return ent, angle_deg


def refs(s):
    return [int(x) for x in re.findall(r"#(\d+)", s)]


def nums(s):
    return [float(x) for x in re.findall(r"(?<![#\w])[-+]?\d+\.?\d*(?:[Ee][-+]?\d+)?", s)]


def bspline_surface(flat, sid, sc):
    """2026-10-06 加（R4 外审 B-P1-3）：解析 STEP B 样条面（简单 B_SPLINE_SURFACE_WITH_KNOTS 与含 RATIONAL 的复合实例），
    返回 (kind, (求值器, 参数域))；求值器 ev(UV) → 点与两个偏导（已除权）。解析不了返回 (None, None)。"""
    from scipy.interpolate import NdBSpline
    m = re.search(r"#%d\s*=\s*(.*?);" % sid, flat)
    if not m:
        return None, None
    s = re.sub(r"\s+", "", m.group(1))
    if "B_SPLINE_SURFACE_WITH_KNOTS" not in s:
        return None, None
    if s.startswith("("):                                   # 复合实例
        kind = "complex"
        mb = re.search(r"B_SPLINE_SURFACE\((\d+),(\d+),\(((?:\([#\d,]+\),?)+)\)", s)
        mkn = re.search(r"B_SPLINE_SURFACE_WITH_KNOTS\(\(([\d,]+)\),\(([\d,]+)\),\(([-\d.,Ee+]+)\),\(([-\d.,Ee+]+)\)", s)
        mw = re.search(r"RATIONAL_B_SPLINE_SURFACE\(\(((?:\([-\d.,Ee+]+\),?)+)\)\)", s)
        if not (mb and mkn):
            return None, None
        du, dv, net = int(mb.group(1)), int(mb.group(2)), mb.group(3)
        mu, mv, ku, kv = mkn.groups()
    else:
        kind = "simple"
        ms = re.match(r"B_SPLINE_SURFACE_WITH_KNOTS\('[^']*',(\d+),(\d+),\(((?:\([#\d,]+\),?)+)\),\.\w+\.,\.\w\.,\.\w\.,\.\w\.,"
                      r"\(([\d,]+)\),\(([\d,]+)\),\(([-\d.,Ee+]+)\),\(([-\d.,Ee+]+)\)", s)
        mw = None
        if not ms:
            return None, None
        du, dv, net = int(ms.group(1)), int(ms.group(2)), ms.group(3)
        mu, mv, ku, kv = ms.groups()[3:]
    rows = [refs(r) for r in re.findall(r"\(([#\d,]+)\)", net)]
    P = np.array([[nums(re.search(r"#%d\s*=\s*CARTESIAN_POINT\s*\((.*?)\)\s*;" % i, flat).group(1).split("(", 1)[1])[:3]
                   for i in row] for row in rows]) * sc
    expand = lambda mult, kn: np.repeat(np.array(nums(kn)), [int(x) for x in mult.split(",")])
    tu, tv = expand(mu, ku), expand(mv, kv)
    W = np.ones(P.shape[:2])
    if mw:
        W = np.array([nums(r) for r in re.findall(r"\(([-\d.,Ee+]+)\)", mw.group(1))])
    if len(tu) != P.shape[0] + du + 1 or len(tv) != P.shape[1] + dv + 1 or W.shape != P.shape[:2]:
        return None, None
    H = NdBSpline((tu, tv), np.concatenate([P * W[..., None], W[..., None]], axis=2), (du, dv))
    dom = np.array([[tu[du], tu[-du - 1]], [tv[dv], tv[-dv - 1]]])

    def ev(UV):
        A, Au, Av = H(UV), H(UV, nu=(1, 0)), H(UV, nu=(0, 1))
        w, wu, wv = A[:, 3:], Au[:, 3:], Av[:, 3:]
        S = A[:, :3] / w
        return S, (Au[:, :3] - S * wu) / w, (Av[:, :3] - S * wv) / w
    return kind, (ev, dom)


def bspline_resid(evd, V):
    """顶点到 B 样条面的最近距离：40×40 参数网格最近点作初值，Gauss-Newton 20 步（参数域内截断）。"""
    from scipy.spatial import cKDTree
    ev, dom = evd
    g = np.stack(np.meshgrid(np.linspace(*dom[0], 40), np.linspace(*dom[1], 40), indexing="ij"), -1).reshape(-1, 2)
    UV = g[cKDTree(ev(g)[0]).query(V)[1]].copy()
    for _ in range(20):
        S, Su, Sv = ev(UV)
        J = np.stack([Su, Sv], axis=2)                     # (N,3,2)
        JTJ = np.einsum("nki,nkj->nij", J, J) + 1e-18 * np.eye(2)
        UV -= np.linalg.solve(JTJ, np.einsum("nki,nk->ni", J, S - V)[..., None])[..., 0]
        UV[:, 0] = UV[:, 0].clip(*dom[0]); UV[:, 1] = UV[:, 1].clip(*dom[1])
    return np.linalg.norm(ev(UV)[0] - V, axis=1)


def t4():
    out_rows, unm_rows, summ = [], [], Counter()
    for b in MODELS:
        ent, angle_deg = step_entities(os.path.join(step_dir, b + ".stp"))
        flat = re.sub(r"\s+", " ", open(os.path.join(step_dir, b + ".stp"), encoding="utf-8", errors="replace")
                      .read().split("DATA;", 1)[1].split("ENDSEC;", 1)[0])
        match = json.load(open(os.path.join(ROOT, "out/e1", b + ".match.json")))
        sc = float(match["scale"])
        faces = {f["index"]: f for f in json.load(open(os.path.join(faces_dir, b + ".faces.json")))["faces"]}

        def pt(i):
            return np.array(nums(ent[i][1].split("(", 1)[1])[:3]) * sc

        def dirv(i):
            v = np.array(nums(ent[i][1].split("(", 1)[1])[:3])
            return v / np.linalg.norm(v)

        def placement(i):
            r = refs(ent[i][1])
            return pt(r[0]), dirv(r[1])

        def surf_of(fid):
            for r in refs(ent[fid][1]):
                if r in ent and ent[r][0] in SURF:
                    t, a = ent[r]
                    m = re.match(r"\s*'[^']*'\s*,\s*#(\d+)\s*(.*)$", a)
                    p, n = placement(int(m.group(1)))
                    vals = nums(m.group(2)) if t != "PLANE" else []
                    return SURF[t], p, n, vals
            return None, None, None, None

        cpt = {}
        for i, (t, a) in ent.items():
            if t == "CARTESIAN_POINT":
                cpt[i] = tuple(round(x * sc, 4) for x in nums(a.split("(", 1)[1])[:3])

        def step_verts(fid):
            vs, fr, seen = set(), refs(ent[fid][1]), set()
            for _ in range(6):
                nx = []
                for r in fr:
                    if r in seen:
                        continue
                    seen.add(r)
                    if r in cpt:
                        vs.add(cpt[r]); continue
                    if r in ent and ent[r][0] in ("FACE_BOUND", "FACE_OUTER_BOUND", "EDGE_LOOP", "ORIENTED_EDGE",
                                                  "EDGE_CURVE", "VERTEX_POINT"):
                        nx += refs(ent[r][1])
                fr = nx
            return vs

        def resid(styp, p, n, vals, V):
            d = V - p
            h = d @ n
            rho = np.linalg.norm(d - np.outer(h, n), axis=1)
            if styp == "Plane":
                return np.abs(h)
            if styp == "Cylinder":
                return np.abs(rho - vals[0] * sc)
            if styp == "Sphere":
                return np.abs(np.linalg.norm(d, axis=1) - vals[0] * sc)
            if styp == "Toroid":
                return np.abs(np.hypot(rho - vals[0] * sc, h) - vals[1] * sc)
            if styp == "Cone":
                best = None
                for ang in (vals[1], math.radians(vals[1])):          # 平面角单位按残差自校准（rad / deg）
                    rr = np.abs(rho - (vals[0] * sc + h * math.tan(ang))) * math.cos(ang)
                    if best is None or np.median(rr) < np.median(best):
                        best = rr
                return best
            return None

        for oi, sid in match["occ_to_step"].items():
            oi = int(oi)
            f = faces[oi]
            styp, p, n, vals = surf_of(sid)
            V = np.asarray(f["verts"], float)
            rec = {"model": short(b), "occ": oi, "step": sid, "occ_type": f["surface"], "step_type": styp}
            if styp is None:                       # STEP 侧非解析面：按 B 样条面解析（简单实例与 RATIONAL 复合实例）
                # 2026-10-06 改（R4 外审 B-P1-3）：旧启发式只认「引用不在简单实体表里」的复合实例，
                # 简单 B_SPLINE_SURFACE_WITH_KNOTS 被判 type_eq=False（75 对）；现直接解析该实体并求几何残差。
                sref = refs(ent[sid][1])[-1]
                kind, evd = bspline_surface(flat, sref, sc)
                rec["step_type"] = f"BSplineSurface({kind})" if kind else None
                rec["type_eq"] = f["surface"] == "BSplineSurface" and kind is not None
                if evd is not None and len(V):
                    rec["max_resid_mm"] = float(bspline_resid(evd, V).max())
            else:
                rec["type_eq"] = (styp == f["surface"])
            if styp is not None and len(V):
                r = resid(styp, p, n, vals, V)
                rec["max_resid_mm"] = float(r.max())
            out_rows.append(rec)
            summ["pairs"] += 1
            summ["type_eq"] += rec["type_eq"]
            if styp is None:                       # B 样条对单列计数；解析面的 resid_* 口径不变
                summ["bspline_pairs"] += 1
                if "max_resid_mm" in rec:
                    summ["bspline_resid_tested"] += 1
                    summ["bspline_resid_le_1e-3"] += rec["max_resid_mm"] <= 1e-3
                    summ["bspline_resid_max"] = max(summ.get("bspline_resid_max", 0.0), rec["max_resid_mm"])
            elif "max_resid_mm" in rec:
                summ["resid_tested"] += 1
                summ["resid_le_1e-3"] += rec["max_resid_mm"] <= 1e-3
                summ["resid_le_1e-5"] += rec["max_resid_mm"] <= 1e-5
            else:
                summ[f"resid_untested_{styp or f['surface']}"] += 1

        matched_step = set(match["occ_to_step"].values())
        all_faces = [i for i, (t, _) in ent.items() if t == "ADVANCED_FACE"]
        un_step = [s for s in all_faces if s not in matched_step]
        for oi in match["unmatched_idx"]:
            f = faces[oi]
            V = np.asarray(f["verts"], float)
            T = {tuple(x) for x in np.round(V, 4).tolist()}
            t_ = np.asarray(f["tris"], int)
            a_ = V[t_[:, 1]] - V[t_[:, 0]]; c_ = V[t_[:, 2]] - V[t_[:, 0]]
            area = float(0.5 * np.linalg.norm(np.cross(a_, c_), axis=1).sum())
            cands = []
            for s in all_faces:
                styp, p, n, vals = surf_of(s)
                if styp != f["surface"]:
                    continue
                r = resid(styp, p, n, vals, V)
                if r is None or r.max() > 1e-3:
                    continue
                sv = step_verts(s)
                cands.append({"step": s, "matched_to_other": s in matched_step,
                              "n_step_verts": len(sv), "step_verts_on_occ_tess": len(sv & T),
                              "radius_mm": (vals[0] * sc if vals else None)})
            unm_rows.append({"model": short(b), "occ": oi, "type": f["surface"], "area_mm2": round(area, 2),
                             "bbox_mm": [round(x, 2) for x in (V.max(0) - V.min(0)).tolist()],
                             "geom_coincident_step_faces": cands})
        summ["unmatched"] += len(match["unmatched_idx"])
        summ["unmatched_step_faces"] += len(un_step)
    bad = [r for r in out_rows if not r["type_eq"] or r.get("max_resid_mm", 0) > 1e-3]
    dump("t4_match_check.json", {"summary": dict(summ), "nonconforming": bad, "unmatched": unm_rows})
    dump("t4_match_pairs.json", out_rows)
    print("[t4]", dict(summ), "nonconforming", len(bad))


# =====================================================================================
# T5
# =====================================================================================
def t5():
    rows, cnt = [], Counter()
    for b in MODELS:
        g = json.load(open(os.path.join(ROOT, "out/e1", b + ".graph.json")))["annotations"]
        need = [a for a in g if a.get("anchorKind") in ("none", "edge", "part")
                or (a["type"] not in ("DATUM", "DATUM_FEATURE") and "value" not in a)
                or (a["type"] == "DATUM" and not a.get("datumLetter"))]
        if not need:
            continue
        ns = run13(os.path.join(step_dir, b + ".stp"))
        back, types_of = ns["back"], ns["types_of"]
        for a in need:
            sid = a["stepId"]
            cat = (f"anchor_{a['anchorKind']}" if a.get("anchorKind") in ("none", "edge", "part")
                   else "typed_fail")
            if cat == "typed_fail" and a.get("anchorKind") in ("none", "edge", "part"):
                cat += "+" + a["anchorKind"]
            users = Counter(t for u in back.get(sid, []) for t in types_of(u))
            rec = {"model": short(b), "stepId": sid, "type": a["type"], "category": cat,
                   "anchorKind": a.get("anchorKind"), "referencing_entity_types": dict(users)}
            if a.get("nonFaceAnchorIds"):
                rec["nonFaceAnchorTypes"] = dict(Counter(t for e in a["nonFaceAnchorIds"] for t in types_of(e)))
            if a.get("anchorKind") == "none":
                # 标注入口 SA 及其 SAR 下行成员上是否存在 GISU/IIRU
                sa_ids = [sid] if a["type"] == "DATUM_FEATURE" else []
                if not sa_ids:
                    for t, aa in ns["graph"][sid]:
                        if "TOLERANCE" in t and t not in ns["SUPPORT"]:
                            ar = ns["split_args"](aa)
                            if len(ar) >= 4:
                                sa_ids = ns["refs_in"](ar[3]); break
                gisu = 0
                stack, seen = list(sa_ids), set()
                while stack:
                    s = stack.pop()
                    if s in seen:
                        continue
                    seen.add(s)
                    for u in back.get(s, []):
                        ut = types_of(u)
                        if ut & {"GEOMETRIC_ITEM_SPECIFIC_USAGE", "ITEM_IDENTIFIED_REPRESENTATION_USAGE"}:
                            gisu += 1
                        if "SHAPE_ASPECT_RELATIONSHIP" in ut:
                            ar = ns["comp_args"](u, "SHAPE_ASPECT_RELATIONSHIP")
                            if ar and s in ns["refs_in"](ar[2]):
                                stack += ns["refs_in"](ar[3])
                rec["sa_closure_size"] = len(seen)
                rec["gisu_or_iiru_in_closure"] = gisu
                rec["sa_closure_users"] = dict(Counter(t for s in seen for u in back.get(s, []) for t in types_of(u)))
            rows.append(rec)
            cnt[cat] += 1
    dump("t5_anchor_inventory.json", {"counts": dict(cnt), "rows": rows})
    print("[t5]", dict(cnt))


def t5b():
    """what-if：若 13 的下行展开把 DATUM 也当作 shape_aspect 继续下行（DF→DATUM→其 GISU），哪些标注的面集会变；
    并与 DATUM 实体上的 NIST 校验属性 affected area 对照。只算不改 13。"""
    xc = os.path.join(ROOT, "out/r1/t6/assoc_crosscheck.json")
    rows = []
    for b in MODELS:
        ns = run13(os.path.join(step_dir, b + ".stp"))
        base = {a["stepId"]: set(a.get("faceIds", [])) for a in ns["result"]}
        ns["SA_LIKE"].add("DATUM")                     # 函数闭包引用同一 set 对象
        f = ns["shape_aspect_faces"].__globals__
        g = json.load(open(os.path.join(ROOT, "out/e1", b + ".graph.json")))["annotations"]
        match = json.load(open(os.path.join(ROOT, "out/e1", b + ".match.json")))
        s2o = {int(v): int(k) for k, v in match["occ_to_step"].items()}
        fj = {x["index"]: x for x in json.load(open(os.path.join(faces_dir, b + ".faces.json")))["faces"]}

        def area(fids):
            tot = 0.0
            for fid in fids:
                o = s2o.get(fid)
                if o is None:
                    continue
                V = np.asarray(fj[o]["verts"], float); T = np.asarray(fj[o]["tris"], int)
                tot += float(0.5 * np.linalg.norm(np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]), axis=1).sum())
            return tot
        # NIST 属性（DATUM 上）
        vp = {}
        for sid, comps in ns["graph"].items():
            for t, a in comps:
                if t == "PROPERTY_DEFINITION" and "'pmi validation property'" in a:
                    tg = ns["refs_in"](ns["split_args"](a)[2])
                    for u in ns["back"].get(sid, []):
                        for t2, a2 in ns["graph"].get(u, []):
                            if t2 == "PROPERTY_DEFINITION_REPRESENTATION":
                                for rep in ns["refs_in"](ns["split_args"](a2)[1]):
                                    for t3, a3 in ns["graph"].get(rep, []):
                                        for it in ns["refs_in"](ns["split_args"](a3)[1]) if "REPRESENTATION" in t3 else []:
                                            for t4_, a4 in ns["graph"].get(it, []):
                                                if "'affected area'" in a4:
                                                    v = float(re.search(r"AREA_MEASURE\(\s*([-\d.Ee+]+)", a4).group(1))
                                                    ur = ns["refs_in"](ns["split_args"](a4)[-1])[0]
                                                    k = None
                                                    for t5_, a5 in ns["graph"].get(ur, []):
                                                        if t5_ == "DERIVED_UNIT":
                                                            de = ns["comp_args"](ns["refs_in"](a5)[0], "DERIVED_UNIT_ELEMENT")
                                                            mm, _ = ns["unit_to_mm"](ns["refs_in"](de[0])[0])
                                                            k = mm ** float(de[1]) if mm else None
                                                    for tt in tg:
                                                        vp[tt] = v * k if k else None
        for a in g:
            if a["type"] == "DATUM":
                continue
            sid = a["stepId"]
            # 复用 13 的入口规则：直接对该标注重算一次
            new = set()
            ents = []
            if a["type"] == "DATUM_FEATURE":
                ents = [sid]
            elif a["type"] in ("DIMENSIONAL_SIZE", "DIMENSIONAL_LOCATION"):
                ar = ns["comp_args"](sid, a["type"])
                if ar:
                    ents = (ns["refs_in"](ar[0]) if a["type"] == "DIMENSIONAL_SIZE"
                            else [r for x in ar[2:4] for r in ns["refs_in"](x)])
            else:
                for t, aa in ns["graph"][sid]:
                    if "TOLERANCE" in t and t not in ns["SUPPORT"]:
                        ar = ns["split_args"](aa)
                        if len(ar) >= 4:
                            ents = ns["refs_in"](ar[3]); break
            for e in ents:
                new |= f["shape_aspect_faces"](e)[0]
            old = base.get(sid, set())
            if new != old:
                datums = [r for u in ns["back"].get(sid, []) for t, aa in ns["graph"].get(u, [])
                          if t == "SHAPE_ASPECT_RELATIONSHIP" and sid in ns["refs_in"](ns["split_args"](aa)[2])
                          for r in ns["refs_in"](ns["split_args"](aa)[3]) if "DATUM" in ns["types_of"](r)]
                na = next((vp[d] for d in datums if vp.get(d)), None) if a["type"] == "DATUM_FEATURE" else vp.get(sid)
                rows.append({"model": short(b), "stepId": sid, "type": a["type"], "anchor_r1": a.get("anchorKind"),
                             "n_r1": len(old), "n_whatif": len(new), "old_subset_new": old <= new,
                             "area_whatif": round(area(new), 3), "nist_area": na,
                             "ratio": (round(area(new) / na, 4) if na else None)})
    S = {"changed": len(rows), "none_to_face": sum(1 for r in rows if r["anchor_r1"] == "none" and r["n_whatif"]),
         "with_area": sum(1 for r in rows if r["nist_area"]),
         "area_ok_2pct": sum(1 for r in rows if r["ratio"] and abs(r["ratio"] - 1) <= 0.02),
         "not_superset": sum(1 for r in rows if not r["old_subset_new"])}
    dump("t5b_datum_whatif.json", {"summary": S, "rows": rows})
    print("[t5b]", S)


# =====================================================================================
# T6c
# =====================================================================================
def t6c():
    new = json.load(open(os.path.join(ROOT, "out/e11/tolerance_judgement.json")))
    old = json.load(open(os.path.join(ROOT, "out/r1/t6/v4-frozen/e11/tolerance_judgement.json")))
    xc = json.load(open(os.path.join(ROOT, "out/r1/t6/assoc_crosscheck.json")))["rows"]
    X = {(r["model"], "#%d" % r["stepId"]): r for r in xc}
    O = {(g["model"], g["stepId"]): g for g in old["groups"]}
    N = {(g["model"], g["stepId"]): g for g in new["groups"]}
    changed, joined, ev = [], [], Counter()
    for k in sorted(set(O) | set(N)):
        a, b = O.get(k), N.get(k)
        x = X.get(k, {})
        row = {"model": short(k[0]), "stepId": k[1],
               "v4": a and {kk: a[kk] for kk in ("faces", "clean", "cause", "uniform")},
               "r1": b and {kk: b[kk] for kk in ("faces", "clean", "cause", "uniform", "nominal", "band_width")},
               "nist_area_mm2": x.get("nist_area"), "ratio_v4": x.get("ratio_v4"), "ratio_down": x.get("ratio_down"),
               "nist_ues": x.get("nist_ues"), "n_faces_down": x.get("n_down"), "inst_down": x.get("inst_down")}
        ues = x.get("nist_ues") or ""
        has_nx = bool(re.search(r"(?<![\d.])\d+\s*[Xx×](?=\s|⌀|↧|$)", ues))
        if x.get("nist_area"):
            tag = "area_ok" if x.get("ok_down") else "area_mismatch"
        elif x.get("nist_area") == 0:
            tag = "area_zero"
        else:
            tag = "no_area"
        if has_nx:
            tag += "+nx_ok" if x.get("nist_nx") in (x.get("n_down"), x.get("inst_down")) else "+nx_mismatch"
        row["nist_evidence"] = tag
        ev[tag] += 1
        joined.append(row)
        if (a and b) and (a["faces"], a["clean"], a["cause"]) != (b["faces"], b["clean"], b["cause"]):
            changed.append(row)
    # I-5：ftc_07 三组——镶嵌顶点到名义圆柱的径向距离 vs C3 拟合半径
    i5 = []
    b = "nist_ftc_07_asme1_ap242-e2"
    faces = {f["index"]: f for f in json.load(open(os.path.join(faces_dir, b + ".faces.json")))["faces"]}
    cyls = {c["face_index"]: c for c in json.load(open(os.path.join(cyl_dir, b + ".cylinders.json")))}
    c3 = {r["face_index"]: r for r in json.load(open(os.path.join(ROOT, "out/hole", b + ".proto.json")))["c3_rows"]}
    for r in new["rows"]:
        if r["model"] != b or r["cause"] != "tessellation":
            continue
        fi = r["face_index"]
        c, V = cyls.get(fi), np.asarray(faces[fi]["verts"], float)
        ax = np.asarray(c["axis"], float); ax /= np.linalg.norm(ax)
        d = V - np.asarray(c["center"], float)
        rho = np.linalg.norm(d - np.outer(d @ ax, ax), axis=1)
        V32 = V.astype(np.float32).astype(float)
        d32 = V32 - np.asarray(c["center"], float)
        rho32 = np.linalg.norm(d32 - np.outer(d32 @ ax, ax), axis=1)
        u = np.cross(ax, [1.0, 0, 0] if abs(ax[0]) < .9 else [0, 1.0, 0]); u /= np.linalg.norm(u)
        v = np.cross(ax, u)
        th = np.sort(np.degrees(np.arctan2(d @ v, d @ u)) % 360)
        gaps = np.diff(np.r_[th, th[0] + 360])
        ang = 360 - gaps.max()                                 # 顶点覆盖的圆弧角
        dev, dev32 = rho - c["radius"], rho32 - c["radius"]
        i5.append({"stepId": r["stepId"], "face_index": fi, "nominal_r": c["radius"],
                   "vertex_radial_dev_median_mm": float(np.median(dev)), "vertex_radial_dev_mean_mm": float(dev.mean()),
                   "vertex_radial_dev_min_mm": float(dev.min()),
                   "fixed_true_axis_r_f64": float(rho.mean()), "fixed_true_axis_r_f32": float(rho32.mean()),
                   "share_vertices_inside": float((dev < -1e-6).mean()),
                   "vertex_radial_dev_max_mm": float(np.abs(rho - c["radius"]).max()),
                   "vertex_radial_dev_max_f32_mm": float(np.abs(rho32 - c["radius"]).max()),
                   "c3_fitted_r": c3[fi]["fitted_r"], "c3_r_err_mm": c3[fi]["fitted_r"] - c["radius"],
                   "arc_span_deg": float(ang), "n_vertices": int(len(V)),
                   "diameter_excess_below_band_mm": r["excess"]})
    dump("t6c_e11_reattribution.json", {"changed_groups": changed, "evidence_counts": dict(ev),
                                         "groups": joined, "i5_ftc07": i5,
                                         "r1_summary": new["summary"]})
    print("[t6c] changed", len(changed), dict(ev))
    for x in i5:
        print("   I-5", x)


# =====================================================================================
# T7b
# =====================================================================================
def t7():
    rows, per = [], {}
    for b in MODELS:
        g = json.load(open(os.path.join(ROOT, "out/e1", b + ".graph.json")))["annotations"]
        dims = Counter(); gts = Counter(); flags = []
        for a in g:
            if a.get("value") is None or a.get("unitName") is None:
                continue
            kind = "dim" if a["type"].startswith("DIMENSIONAL") else "gt"
            (dims if kind == "dim" else gts)[a["unitName"].upper()] += 1
            vmm = a["value"] * (a.get("unitToMm") or 1.0)
            rec = {"model": short(b), "stepId": a["stepId"], "type": a["type"], "kind": kind,
                   "value": a["value"], "unit": a["unitName"], "value_mm": vmm}
            if kind == "gt" and (vmm < 0.005 or vmm > 5):
                rec["flag"] = "gt_magnitude_implausible"
            rows.append(rec)
        du, gu = set(dims), set(gts)
        red = bool(du and gu and du != gu)
        per[short(b)] = {"dim_units": dict(dims), "gt_units": dict(gts), "dim_gt_unit_mismatch": red}
    dump("t7_unit_census.json", {"per_model": per, "flagged": [r for r in rows if r.get("flag")],
                                 "n_values": len(rows)})
    print("[t7] mismatch models:", [m for m, v in per.items() if v["dim_gt_unit_mismatch"]],
          "| flagged GT:", Counter(r["model"] for r in rows if r.get("flag")))


# =====================================================================================
# T9
# =====================================================================================
def c3_fit(P):
    """与 19 的 C3 同算法：三角形法线协方差最小特征向量为轴 → ⊥ 平面 Kasa 圆"""
    tri = P
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ln = np.linalg.norm(nrm, axis=1)
    nrm = nrm[ln > 1e-12] / ln[ln > 1e-12][:, None]
    w, vec = np.linalg.eigh(nrm.T @ nrm)
    pts = tri.reshape(-1, 3)
    uv = np.column_stack([pts @ vec[:, 1], pts @ vec[:, 2]])
    A = np.column_stack([2 * uv, np.ones(len(uv))])
    (cx, cy, c0), *_ = np.linalg.lstsq(A, (uv ** 2).sum(1), rcond=None)
    return float(np.sqrt(max(c0 + cx * cx + cy * cy, 0.0)))


def t9():
    e64, e32, e_stage, per = [], [], [], {}
    for b in MODELS:
        hp = os.path.join(ROOT, "out/hole", b + ".proto.json")
        if not os.path.exists(hp):
            continue
        h = json.load(open(hp))
        if h["summary"].get("reg") != "identity" or h["summary"].get("scale") != 1.0:
            per[short(b)] = "skipped_nonidentity_registration"
            continue
        faces = {f["index"]: f for f in json.load(open(os.path.join(faces_dir, b + ".faces.json")))["faces"]}
        nom = {c["face_index"]: c["radius"] for c in json.load(open(os.path.join(cyl_dir, b + ".cylinders.json")))}
        m64 = []
        for r in h["c3_rows"]:
            fi = r["face_index"]
            if r.get("abs_err") is None or fi not in nom:
                continue
            V = np.asarray(faces[fi]["verts"], float); T = np.asarray(faces[fi]["tris"], int)
            r64 = c3_fit(V[T])
            V32 = V.astype(np.float32).astype(float)
            r32 = c3_fit(V32[T])
            e64.append(abs(r64 - nom[fi])); e32.append(abs(r32 - nom[fi])); e_stage.append(r["abs_err"])
            m64.append(abs(r64 - nom[fi]))
        per[short(b)] = {"n": len(m64), "median_err_f64": float(np.median(m64)) if m64 else None}
    q = lambda e: {"n": len(e), "median": float(np.median(e)), "p99": float(np.percentile(e, 99)), "max": float(np.max(e))}
    S = {"float64_faces_json": q(e64), "float32_cast": q(e32), "stage_c3_as_published": q(e_stage), "per_model": per}
    dump("t9_float_precision.json", S)
    print("[t9]", {k: v for k, v in S.items() if k != "per_model"})


# =====================================================================================
# T10
# =====================================================================================
def t10():
    K = json.load(open(os.path.join(ROOT, "out/e1/canonical_numbers.json")))
    keys = {k: v for k, v in K.items() if re.match(r"e[23]\.(area|geom)\..*mean_of_means", k) or k.startswith("e2.geom.")}
    dump("t10_reference_object.json", keys)
    print("[t10]", keys)


for name in ("t4", "t5", "t5b", "t6c", "t7", "t9", "t10"):
    if name in todo:
        globals()[name]()
