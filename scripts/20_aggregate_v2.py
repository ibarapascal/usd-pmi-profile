# 数字 SSOT 聚合器：扫全部实验产物 → canonical_numbers.json（key→值）＋ calculation-results.md（人读表）
# draft 用 {{key}} 占位，21_render_draft.py 替换——重跑实验后重渲即同步（用户 2026-08-28 指示的机制）。
# key 命名：{实验}.{对象}.{指标}，模型级 key 带模型短名。只聚合不计算新量；缺产物如实标 MISSING。
# 用法: .venv/bin/python 20_aggregate_v2.py
import glob
import json
import os
from collections import Counter

os.chdir(os.path.join(os.path.dirname(__file__), ".."))
K = {}

def short(b):
    return b.replace("nist_", "").replace("_asme1_ap242", "").replace("-", "_")

models = sorted(short(os.path.basename(f).replace(".graph.json", ""))
                for f in glob.glob("out/e1/*ap242*.graph.json")
                if "e1-tg" not in f)

# ---- E1: graph 解析（typed / anchor）----
tot = Counter(); n_annos = 0; per_type = Counter()
for f in glob.glob("out/e1/*ap242*.graph.json"):
    if "e1-tg" in f:
        continue
    d = json.load(open(f))["summary"]
    n_annos += d["n_annos"]
    for k, v in d["coverage"].items():
        tot[k] += v
    for k, v in d["by_type"].items():
        per_type[k] += v
K["e1.total_annos"] = n_annos
val_ok = sum(v for k, v in tot.items() if k.endswith("_value_ok")) + tot["datum_letter_ok"]
val_all = val_ok + sum(v for k, v in tot.items() if k.endswith("_value_miss")) + tot["datum_letter_miss"]
K["e1.typed_ok"] = val_ok
K["e1.typed_total"] = val_all
K["e1.typed_pct"] = round(100 * val_ok / val_all, 1)
af, ae, ap_, an = tot["assoc_face"], tot["assoc_edge"], tot["assoc_part"], tot["assoc_none"]
den = af + ae + ap_ + an
K["e1.anchor_face"] = af
K["e1.anchor_edge"] = ae
K["e1.anchor_part"] = ap_
K["e1.anchor_none"] = an
K["e1.anchor_face_pct"] = round(100 * af / den, 1)
K["e1.anchor_linked_pct"] = round(100 * (af + ae + ap_) / den, 1)
K["e1.tol_datum_ok"] = tot["tol_datum_ok"]
K["e1.tol_datum_none"] = tot["tol_datum_none"]
for t, v in per_type.items():
    K[f"e1.bytype.{t}"] = v

# ---- E1: 面匹配 ----
mt = ms = 0; rates = []; inch = []
for f in glob.glob("out/e1/*ap242*.match.json"):
    d = json.load(open(f))
    b = short(os.path.basename(f).replace(".match.json", ""))
    mt += d["matched"]; ms += d["n_occ"]
    rates.append((b, d["match_rate"]))
    K[f"e1.match.{b}.rate"] = d["match_rate"]
    if d.get("scale") == 25.4:
        inch.append(b)
K["e1.match.total_matched"] = mt
K["e1.match.total_faces"] = ms
K["e1.match.total_pct"] = round(100 * mt / ms, 1)
K["e1.match.min_rate_pct"] = round(100 * min(r for _, r in rates), 1)
K["e1.match.perfect_models"] = sum(1 for _, r in rates if r == 1.0)
K["e1.match.inch_models"] = len(inch)

# ---- E1: writer/audit v2 ----
sv = te = ro = fa = 0
for f in glob.glob("out/e1/*ap242*.audit_v2.json"):
    d = json.load(open(f))
    sv += d["survive"]; te += d["typed_eq"]; ro += d["rel_ok"]; fa += d["anchor_face_expected"]
K["e1.audit.survive"] = sv
K["e1.audit.typed_eq"] = te
K["e1.audit.rel_ok"] = ro
K["e1.audit.rel_expected"] = fa
K["e1.audit.rel_pct"] = round(100 * ro / fa, 1) if fa else None

# 关联目标级完整性（rel 存在 ≠ 目标齐全——stc_10 实测 15 条部分目标缺失的教训）
tt = tk = 0
for f in glob.glob("out/e1/*ap242*.match.json"):
    m = json.load(open(f))
    b2 = os.path.basename(f).replace(".match.json", "")
    matched_step = set(int(v) for v in m["occ_to_step"].values())
    g2 = json.load(open(f"out/e1/{b2}.graph.json"))
    for a2 in g2["annotations"]:
        for fid in a2.get("faceIds", []):
            tt += 1
            if fid in matched_step:
                tk += 1
K["e1.audit.target_ok"] = tk
K["e1.audit.target_total"] = tt
K["e1.audit.target_pct"] = round(100 * tk / tt, 1) if tt else None

# ---- E3: 方向 B（area / uv × 三管线）----
for kind in ("area", "uv"):
    for pl in ("chainA", "omni", "proto"):
        means, p95s, p99s, maxs, regs = [], [], [], [], []
        for f in glob.glob(f"out/dirB/*.{pl}.{kind}.json"):
            d = json.load(open(f))
            b = short(os.path.basename(f).split(".")[0])
            s = d["stats"]
            means.append(s["mean"]); p95s.append(s["p95"]); p99s.append(s["p99"]); maxs.append(s["max"])
            regs.append(d["registration"])
            K[f"e3.{kind}.{pl}.{b}.mean"] = round(s["mean"], 4)
            K[f"e3.{kind}.{pl}.{b}.p95"] = round(s["p95"], 4)
            K[f"e3.{kind}.{pl}.{b}.max"] = round(s["max"], 4)
            K[f"e3.{kind}.{pl}.{b}.reg"] = d["registration"]
        if means:
            import statistics as st
            K[f"e3.{kind}.{pl}.n_models"] = len(means)
            K[f"e3.{kind}.{pl}.mean_of_means"] = round(st.mean(means), 4)
            K[f"e3.{kind}.{pl}.sd_of_means"] = round(st.pstdev(means), 4)
            K[f"e3.{kind}.{pl}.median_p95"] = round(st.median(p95s), 4)
            K[f"e3.{kind}.{pl}.max_of_max"] = round(max(maxs), 4)
            K[f"e3.{kind}.{pl}.nonidentity_reg"] = sum(1 for r in regs if r != "identity")

# ---- E4: 孔径（可测率＝汇总计数；误差＝逐孔合并分布 median/mean/p99/max）----
agg = {}
for f in glob.glob("out/hole/*.json"):
    base = os.path.basename(f)[:-5]
    if base.count(".") < 1:
        continue
    b, pl = base.rsplit(".", 1)
    d = json.load(open(f))
    for key in ("A_vertex_all", "B_surface", "C_subset", "C2_selfcontained"):
        if key in d["summary"]:
            a = agg.setdefault((pl, key), {"meas": 0, "tot": 0, "errs": []})
            a["meas"] += d["summary"][key]["measurable"]; a["tot"] += d["summary"][key]["total"]
            for r in d["per_hole"]:
                e = r.get(key, {}).get("abs_err")
                if e is not None:
                    a["errs"].append(e)
import numpy as _np
for (pl, key), a in agg.items():
    K[f"e4.{pl}.{key}.measurable"] = a["meas"]
    K[f"e4.{pl}.{key}.total"] = a["tot"]
    K[f"e4.{pl}.{key}.pct"] = round(100 * a["meas"] / a["tot"], 1) if a["tot"] else None
    if a["errs"]:
        e = _np.array(a["errs"])
        K[f"e4.{pl}.{key}.mean_err"] = round(float(e.mean()), 4)
        K[f"e4.{pl}.{key}.median_err"] = float(f"{_np.median(e):.2g}")
        K[f"e4.{pl}.{key}.p99_err"] = round(float(_np.percentile(e, 99)), 4)
        K[f"e4.{pl}.{key}.max_err"] = round(float(e.max()), 4)

# ---- E4-C3（asset-only）：逐 subset 行合并 ----
c3_errs, c3_enum, c3_nom, c3_matched = [], 0, 0, 0
for f in glob.glob("out/hole/*.proto.json"):
    d = json.load(open(f))
    su = d["summary"].get("C3_asset_only")
    if not su:
        continue
    c3_enum += su["enumerated_from_usd"]; c3_nom += su["nominal_total"]
    c3_matched += su["matched_to_nominal"]
    for r in (d.get("c3_rows") or []):
        if r.get("abs_err") is not None:
            c3_errs.append(r["abs_err"])
if c3_errs:
    e = _np.array(c3_errs)
    K["e4.proto.C3_asset_only.enumerated"] = c3_enum
    K["e4.proto.C3_asset_only.nominal"] = c3_nom
    K["e4.proto.C3_asset_only.match_pct"] = round(100 * c3_matched / c3_enum, 1)
    K["e4.proto.C3_asset_only.median_err"] = float(f"{_np.median(e):.2g}")
    K["e4.proto.C3_asset_only.p99_err"] = round(float(_np.percentile(e, 99)), 4)
    K["e4.proto.C3_asset_only.max_err"] = round(float(e.max()), 4)

# ---- E4 窗口敏感性（WIN_R=0.30）----
for f in glob.glob("out/hole_win30/*.json"):
    pass
agg30 = {}
for f in glob.glob("out/hole_win30/*.json"):
    b, pl = os.path.basename(f)[:-5].rsplit(".", 1)
    d = json.load(open(f))["summary"]
    for key in ("A_vertex_all", "B_surface"):
        if key in d:
            a = agg30.setdefault((pl, key), {"meas": 0, "tot": 0})
            a["meas"] += d[key]["measurable"]; a["tot"] += d[key]["total"]
for (pl, key), a in agg30.items():
    K[f"e4win30.{pl}.{key}.pct"] = round(100 * a["meas"] / a["tot"], 1) if a["tot"] else None

# ---- 可测判据阈值扫描（由逐孔支持点数事后推得，无需重跑）----
for pl in ("chainA", "omni", "proto"):
    counts = {"A_vertex_all": [], "B_surface": []}
    for f in glob.glob(f"out/hole/*.{pl}.json"):
        for r in json.load(open(f))["per_hole"]:
            for key in counts:
                if key in r:
                    counts[key].append(r[key]["n"])
    for key, ns in counts.items():
        if not ns:
            continue
        arr = _np.array(ns)
        for t in (4, 8, 16, 32, 64):
            K[f"e4scan.{pl}.{key}.t{t}.pct"] = round(100 * float((arr >= t).mean()), 1)

# ---- E2：第二开源链 Mayo→glTF→guc（Windows 侧转换脚本 25，审计 26/18/19 → out/e2_audit）----
if glob.glob("out/e2_audit/*.dirB.json"):
    scan = json.load(open("out/e2_audit/scan.json"))
    # 语义扫描：pmi_hit 逐条核过均为产品名字符串假阳性（NIST_PMI_*），载体计零
    K["e2.scan.n"] = len(scan)
    K["e2.scan.pmi_zero"] = all(
        all("nist_pmi" in h.split(":")[-1] or "NIST_PMI".lower() in h.lower() for h in r["pmi_hits"])
        for r in scan)
    K["e2.scan.units_authored"] = sum(1 for r in scan if r["authored_units"])
    K["e2.scan.mpu_all_1"] = all(r["metersPerUnit"] == 1.0 for r in scan)
    K["e2.scan.subsets_total"] = sum(r["subsets"] for r in scan)
    K["e2.scan.mesh_min"] = min(r["meshes"] for r in scan)
    K["e2.scan.mesh_max"] = max(r["meshes"] for r in scan)
    means, nonid = [], 0
    for f in sorted(glob.glob("out/e2_audit/*.dirB.json")):
        d = json.load(open(f))
        means.append(d["stats"]["mean"])
        if d["registration"] != "identity":
            nonid += 1
    K["e2.geom.mean_of_means"] = round(float(_np.mean(means)), 4)
    K["e2.geom.n_models"] = len(means)
    K["e2.geom.nonidentity"] = nonid
    mA = tA = mB = tB = 0
    eA, eB = [], []
    for f in sorted(glob.glob("out/e2_audit/*.hole.json")):
        d = json.load(open(f))
        s = d["summary"]
        mA += s["A_vertex_all"]["measurable"]; tA += s["A_vertex_all"]["total"]
        mB += s["B_surface"]["measurable"]; tB += s["B_surface"]["total"]
        for h in d["per_hole"]:
            for key, acc in (("A_vertex_all", eA), ("B_surface", eB)):
                r = h.get(key)
                if r and r["n"] >= 8 and r["abs_err"] is not None:
                    acc.append(r["abs_err"])
    K["e2.hole.A.pct"] = round(100 * mA / tA, 1)
    K["e2.hole.B.pct"] = round(100 * mB / tB, 1)
    K["e2.hole.A.median"] = round(float(_np.median(eA)), 4)
    K["e2.hole.B.median"] = round(float(_np.median(eB)), 4)
    K["e2.hole.B.p99"] = round(float(_np.percentile(eB, 99)), 4)
    K["e2.hole.A.p99"] = round(float(_np.percentile(eA, 99)), 4)
    K["e2.hole.A.max"] = round(float(_np.max(eA)), 4)
    K["e2.hole.B.max"] = round(float(_np.max(eB)), 4)
    # P3 阈值扫描（同 e4scan 口径，事后由逐孔支持点数推得）
    cnts = {"A_vertex_all": [], "B_surface": []}
    for f in glob.glob("out/e2_audit/*.hole.json"):
        for r in json.load(open(f))["per_hole"]:
            for key in cnts:
                if key in r:
                    cnts[key].append(r[key]["n"])
    for key, ns in cnts.items():
        arr = _np.array(ns)
        for t in (4, 8, 16, 32, 64):
            K[f"e4scan.mayo.{key}.t{t}.pct"] = round(100 * float((arr >= t).mean()), 1)
    # P3 窗口敏感性（WIN_R=0.30，out/e2_win30）
    a30 = {"A_vertex_all": [0, 0], "B_surface": [0, 0]}
    for f in glob.glob("out/e2_win30/*.hole.json"):
        s = json.load(open(f))["summary"]
        for key in a30:
            a30[key][0] += s[key]["measurable"]; a30[key][1] += s[key]["total"]
    for key, (m_, t_) in a30.items():
        if t_:
            K[f"e4win30.mayo.{key}.pct"] = round(100 * m_ / t_, 1)

# ---- typed 往返两口径并记（账本自洽：typed_eq 含 empty-to-empty；nonempty=有 typed 值者）----
K["e1.audit.typed_eq_nonempty"] = K["e1.typed_ok"]

# ---- E9：asset-only 几何分割基线（regime D，RANSAC；scripts/29）----
for pl in ("chainA", "omni", "mayo"):
    meas = tot = 0
    errs = []
    for f in glob.glob(f"out/e9/*.{pl}.json"):
        d = json.load(open(f))
        s = d["summary"]["D_ransac"]
        meas += s["measurable"]; tot += s["total"]
        for r in d["per_hole"]:
            e = r["D_ransac"].get("abs_err")
            if e is not None:
                errs.append(e)
    if tot:
        e = _np.array(errs)
        K[f"e9.{pl}.pct"] = round(100 * meas / tot, 1)
        K[f"e9.{pl}.measurable"] = meas
        K[f"e9.{pl}.total"] = tot
        if len(errs):
            K[f"e9.{pl}.median_err"] = float(f"{_np.median(e):.3g}")
            K[f"e9.{pl}.p99_err"] = round(float(_np.percentile(e, 99)), 1)
            K[f"e9.{pl}.max_err"] = round(float(e.max()), 1)

# ---- E9b：per-prim 拟合基线（regime D2；scripts/30）----
for pl in ("chainA", "omni", "mayo"):
    meas = tot = 0
    errs = []
    for f in glob.glob(f"out/e9b/*.{pl}.json"):
        d = json.load(open(f))
        s = d["summary"]["D2_perprim"]
        meas += s["measurable"]; tot += s["total"]
        for r in d["per_hole"]:
            e = r["D2_perprim"].get("abs_err")
            if e is not None:
                errs.append(e)
    if tot:
        e = _np.array(errs)
        K[f"e9b.{pl}.pct"] = round(100 * meas / tot, 1)
        K[f"e9b.{pl}.measurable"] = meas
        K[f"e9b.{pl}.total"] = tot
        if len(errs):
            def _fmt(x):
                return float(f"{x:.2g}") if x < 0.01 else round(float(x), 1)
            K[f"e9b.{pl}.median_err"] = _fmt(float(_np.median(e)))
            K[f"e9b.{pl}.p99_err"] = _fmt(float(_np.percentile(e, 99)))
            K[f"e9b.{pl}.max_err"] = _fmt(float(e.max()))


# ---- E11：stage-only 公差判定（2026-08-29）----
_e11p = "out/e11/tolerance_judgement.json"
if os.path.exists(_e11p):
    _e = json.load(open(_e11p))
    _s = _e["summary"]
    # ⚠️ canonical 是**平铺点分键**（渲染器 21 做平铺查表，不解析点路径）——嵌套会静默漏渲染
    _f, _cg, _cf = _s["funnel"], _s["cause_by_group"], _s["cause_by_face"]
    K["e11.groups"] = _s["groups"]; K["e11.groups_clean"] = _s["groups_clean"]
    K["e11.groups_pct"] = _s["groups_clean_pct"]
    K["e11.faces"] = _s["faces"]; K["e11.faces_in"] = _s["faces_in_band"]
    K["e11.faces_pct"] = _s["faces_in_band_pct"]; K["e11.at_limit"] = _s["at_limit_faces"]
    K["e11.out_groups"] = _s["groups"] - _s["groups_clean"]
    K["e11.out_faces"] = _s["faces"] - _s["faces_in_band"]
    for tag, key in (("tessellation", "tess"), ("unit_inconsistent_source", "unit"),
                     ("multi_size_group", "multi")):
        K[f"e11.{key}_g"] = _cg.get(tag, 0); K[f"e11.{key}_f"] = _cf.get(tag, 0)
    K["e11.f_annos"] = _f["annotations_total"]; K["e11.f_size"] = _f["dimensional_size"]
    K["e11.f_twosided"] = _f["two_sided_band"]; K["e11.f_dimok"] = _f["diameter_or_radius"]
    K["e11.f_noband"] = _f["dropped_no_two_sided_band"]; K["e11.f_nocyl"] = _f.get("group_without_fitted_cylinder", 0)
    K["e11.skipped"] = sum(_s["skipped_by_dimName"].values())
    K["e11.band_min"] = _s["band_width_min"]; K["e11.band_max"] = _s["band_width_max"]
    K["e11.tie"] = _s["tie_tolerance_mm"]
    # 单位分布（S10）与单位缺陷模型的同伴计数——此前是手数，2026-08-29 全面 review 查出 mm/inch
    # 分类与 ftc_09 的「其余 inch 标注」两处都错，故提成 canonical 键，禁止再在正文里手写
    K["e11.u_mm"] = _s["unit_models_mm"]; K["e11.u_inch"] = _s["unit_models_inch"]
    K["e11.u_mixed"] = _s["unit_models_mixed"]
    K["e11.u_defect_inch"] = _s["defect_model_inch_total"]
    K["e11.u_defect_other"] = _s["defect_model_inch_other"]
    K["e11.u_inch_any"] = _s["unit_models_inch_any"]   # 含 inch 标注的模型数（inch-only ＋ mixed）
    K["e11.u_total"] = _s["unit_models_total"]

# ---- 实现层的规模与代价（§5.4）：逐面 tessellation 保住了面身份，代价是共享边上的顶点被复制。
#      2026-08-29 第四轮 review：§5.4 原本只有三句、无任何可核对的量，与标题声称的「open
#      implementation」不相称。这两组数由交付 stage 现算，不手写。
try:
    from pxr import Usd as _Usd, UsdGeom as _UG
    _dups, _sizes = [], []
    for _f in sorted(glob.glob("out/proto_v2/*.usdc")):
        _sizes.append(os.path.getsize(_f) / 1048576.0)
        _st = _Usd.Stage.Open(_f)
        for _pr in _st.Traverse():
            if _pr.IsA(_UG.Mesh):
                _pt = _np.array(_UG.Mesh(_pr).GetPointsAttr().Get())
                _dups.append(len(_pt) / len(_np.unique(_np.round(_pt, 6), axis=0)))
                break
    if _dups:
        K["impl.vdup_min"] = round(min(_dups), 2)
        K["impl.vdup_max"] = round(max(_dups), 2)
        K["impl.vdup_med"] = round(float(_np.median(_dups)), 2)
        K["impl.stage_mb_min"] = f"{min(_sizes):.2f}"      # 字符串：两端小数位一致，正文才不会出现 0.14–1.6
        K["impl.stage_mb_max"] = f"{max(_sizes):.2f}"
except Exception as _e:                      # usd-core 缺席时不阻断聚合
    print("[20] impl.* skipped:", _e)

json.dump(K, open("out/e1/canonical_numbers.json", "w"), indent=1, ensure_ascii=False)

# ---- 人读版 ----
with open("notes/calculation-results.md", "w") as fh:
    fh.write("<!-- 自动生成：scripts/20_aggregate_v2.py。数字 SSOT = out/e1/canonical_numbers.json；"
             "draft 用 {{key}} 占位由 21_render_draft.py 替换。手改无效，重跑聚合器覆盖。-->\n\n")
    fh.write("# v2 计算结果（canonical numbers 人读版）\n\n")
    for k in sorted(K):
        fh.write(f"- `{k}` = {K[k]}\n")
print(f"[20] keys={len(K)} -> out/e1/canonical_numbers.json + notes/calculation-results.md")
