# R1 修回新数字键：从 out/r1/ 各任务的冻结产物抽数 → out/r1/canonical_r1.json（键名一律 r1.* 前缀）
# 用途：draft-en-v5.md 里的新数字走 {{r1.*}} 占位，由 21_render_draft.py 在 EXTRA_KEYS 指定时合并渲染；
#       不改 out/e1/canonical_numbers.json（681 键 SSOT，修回只登记授权例外，不在那边追加）。
# 每个键都对 notes/20261005-revision-numbers.md §F 的冻结值做 assert——产物一漂移即报错，正文不会静默变数。
# 输入（只读）：out/r1/t1/t1t2_pca/{t1_table,t2_table}.json、out/r1/t1/downstream_table.json、out/r1/t3b/stage_overhead.json、
#   out/r1/t43/{t4_match_check,t9_float_precision,t7_unit_census}.json、out/r1/t6b/assoc_crosscheck.summary.json、
#   out/r1/t6e/sfa_rule_assoc.summary.json、out/r1/t8/t8_scan.json、out/r1/t11b/minimality_ablation.json、
#   out/r1/t12b/composition_check.json
# 用法: .venv/bin/python scripts/51_r1_keys.py      （本机 <1 秒，纯 JSON 读取）
#   公开 repo／去标识 archive 内：R1_DIR=results/r1 R1_OUT=<新文件> python scripts/51_r1_keys.py
#   （2026-10-05 加 R1_DIR／R1_OUT；不设时行为不变：读 out/r1/、写 out/r1/canonical_r1.json）
import json
import os
from pathlib import Path

os.chdir(Path(__file__).resolve().parent.parent)
R = Path(os.environ.get("R1_DIR", "out/r1"))
J = lambda p: json.load(open(R / p))
K = {}

def put(key, val, frozen=None):
    if frozen is not None:
        assert val == frozen, f"{key}: 产物 {val!r} ≠ §F 冻结值 {frozen!r}"
    K["r1." + key] = val

# ---- T1 网格化敏感性（§F F3-19/F3-20）
t1 = J("t1/t1t2_pca/t1_table.json")
dn = J("t1/downstream_table.json")
put("t1.n_variants", len(t1), 7)
put("t1.fp_unchanged_all", all(v["fp_unchanged"] == v["n_faces"] == 3843 for v in t1.values()), True)
put("t1.match_identical_all", all(v["match_identical"] == v["match_checked"] == 16 for v in t1.values()), True)
cf_same = len({json.dumps(dn[v]["cf_pass_models"], sort_keys=True) for v in dn}) == 1
put("t1.cf_same_all", cf_same, True)
clean = {v: dn[v]["e11"]["groups_clean"] for v in dn}
put("t1.e11_clean_min", min(clean.values()), 118)
put("t1.e11_clean_max", max(clean.values()), 124)
put("t1.e11_clean_coarse", clean["occ_d0.5_a1.0"], 124)
put("t1.e11_clean_mefisto", clean["mefisto"], 118)
put("t1.e11_clean_netgen", clean["netgen_f2"], 122)
occ = ["occ_d0.01", "occ_d0.05", "occ_d0.1", "occ_d0.5"]
put("t1.e11_occ_same", len({json.dumps(dn[v]["e11_incidents"], sort_keys=True) for v in occ}) == 1, True)
for v, tag in (("occ_d0.5_a1.0", "coarse"), ("mefisto", "mefisto"), ("netgen_f2", "netgen")):
    put(f"t1.gt004_{tag}", t1[v]["c3_gt_0.04mm"])
    put(f"t1.gt004_flagged_{tag}", t1[v]["c3_gt_0.04mm_flagged"])
    put(f"t1.c3_median_{tag}", t1[v]["c3_median_err"])
    put(f"t1.c3_p99_{tag}", t1[v]["c3_p99_err"])
assert (K["r1.t1.gt004_coarse"], K["r1.t1.gt004_flagged_coarse"]) == (48, 22)
assert (K["r1.t1.gt004_mefisto"], K["r1.t1.gt004_flagged_mefisto"]) == (325, 44)
assert (K["r1.t1.gt004_netgen"], K["r1.t1.gt004_flagged_netgen"]) == (47, 23)
assert all(t1[v]["c3_gt_0.04mm"] == t1[v]["c3_gt_0.04mm_flagged"] == 4 for v in occ)

# ---- T2 拓扑扰动（F3-21）
t2 = J("t1/t1t2_pca/t2_table.json")["variants"]
put("t2.split_new", t2["split_periodic"]["new_faces"], 5104)
put("t2.split_wrong", t2["split_periodic"]["new_wrong"], 220)
put("t2.split_correct", t2["split_periodic"]["new_correct"], 779)
put("t2.split_unmatched", t2["split_periodic"]["new_unmatched"], 4105)
put("t2.unify_new", t2["unify"]["new_faces"], 1050)
put("t2.unify_wrong", t2["unify"]["new_wrong"], 4)
put("t2.unify_reassigned", t2["unify"]["unchanged_diff"], 4)
noise = {k: v for k, v in t2.items() if k.startswith("noise_")}
put("t2.noise_wrong_max", max(v["unchanged_diff"] + v["new_wrong"] for v in noise.values()), 2)

# ---- T3 stage 开销（F3-16；2026-10-05 改取 r1b stage 同源重测 out/r1/t3b，冻结值见 numbers 文档 §F 末「订正（F3-16）」；
#      旧 out/r1/t3 测于 DATUM 修复前的 r1 stage，保留不删）
t3 = J("t3b/stage_overhead.json")
rat = t3["summary"]["ratio_full_over_geom"]
put("t3.bytes_ratio", round(rat["bytes"], 3), 1.024)
put("t3.open_ratio", round(rat["open_s_med"], 2), 1.37)
put("t3.rss_ratio", round(rat["rss_delta_med"], 2), 1.13)
rows = {(r["model"], r["variant"]): r for r in t3["rows"]}
models = sorted({m for m, _ in rows})
d_kb = max((rows[m, "full"]["bytes"] - rows[m, "geom"]["bytes"]) / 1024 for m in models)   # KiB
d_ms = max((rows[m, "full"]["open_s_med"] - rows[m, "geom"]["open_s_med"]) * 1e3 for m in models)
d_mb = max((rows[m, "full"]["rss_delta_med"] - rows[m, "geom"]["rss_delta_med"]) / 2**20 for m in models)   # MiB
put("t3.max_extra_kb", round(d_kb), 38)
put("t3.max_extra_open_ms", round(d_ms, 1), 3.0)
put("t3.max_extra_rss_mb", round(d_mb, 1), 2.5)
put("t3.mesh_identical", sum(c["full_eq_geom"] for c in t3["checks"]), 16)
put("t3.weld_partition_ok", sum(c["weld_full_partition_ok"] and c["weld_full_validate_family"] for c in t3["checks"]), 16)

# ---- T4 未对齐面与匹配对核查（F3-3/F3-4）
t4 = J("t43/t4_match_check.json")
s4 = t4["summary"]
types = [u["type"] for u in t4["unmatched"]]
put("t4.unaligned_cone", types.count("Cone"), 17)
put("t4.unaligned_sphere", types.count("Sphere"), 2)
put("t4.twin_unique", sum(len(u["geom_coincident_step_faces"]) == 1 and not u["geom_coincident_step_faces"][0]["matched_to_other"]
                          and u["geom_coincident_step_faces"][0]["n_step_verts"] == 1 for u in t4["unmatched"]), 19)
put("t4.resid_tested", s4["resid_tested"], 3744)
put("t4.resid_le_1e3", s4["resid_le_1e-3"], 3578)
put("t4.bspline_pairs", s4["pairs"] - s4["resid_tested"], 80)
# 2026-10-06（R4 外审 B-P1-3）：43 t4 补 B 样条类型判定与几何残差后的新键（numbers §F6）
put("t4.type_eq", s4["type_eq"], 3824)
put("t4.bspline_tested", s4["bspline_resid_tested"], 80)
put("t4.bspline_max", round(s4["bspline_resid_max"], 3), 0.021)

# ---- T6/T6b NIST 内嵌校验属性（F3-7）
s6 = J("t6b/assoc_crosscheck.summary.json")
put("t6.area_n", s6["with_nist_area"], 283)
put("t6.area_ok", s6["ok2_down"], 251)
put("t6.area_pct", round(100 * s6["ok2_down"] / s6["with_nist_area"], 1), 88.7)
put("t6.area_unexplained", 3)                     # ftc_06 #149–151（numbers §T6，人工归因，非产物字段）
put("t6.area_refside", s6["with_nist_area"] - s6["ok2_down"] - 3, 29)
put("t6.files_with_props", 12)                    # numbers §T6 已查④（STEP grep），非 42 产物字段
# 2026-10-06（R4 外审 B-P1-1）：覆盖口径——非零 affected area 实际连上标注的件数；128 组里既无非零面积、又不在图纸核对 4 件的组数
_rows6 = J("t6b/assoc_crosscheck.json")["rows"]
put("t6.files_with_area", len({r["model"] for r in _rows6 if r["nist_area"]}), 7)
_g6c = J("t43/t6c_e11_reattribution.json")["groups"]
put("t6.groups_reimpl_only", sum(g["nist_area_mm2"] is None or not g["nist_area_mm2"] for g in _g6c
                                 if g["model"].split("-")[0] not in ("ftc_08", "ftc_09", "ftc_10", "ftc_11")), 38)

# ---- T6e SFA 规则重实现（F3-8）
se = J("t6e/sfa_rule_assoc.summary.json")
put("t6e.n", se["n"], 724)
put("t6e.equal", se["rel"]["equal"] + se["rel"]["equal_empty"], 724)
put("t6e.e11_equal", se["e11"]["rel"]["equal"], 128)
put("t6e.ftc08_11", sum(v["n"] for v in se["ftc_08_11"].values()), 204)
put("t6e.ftc08_11_equal", sum(sum(v["rel"].values()) for v in se["ftc_08_11"].values()), 204)

# ---- T8 P2 convertMetadata（F3-22）
s8 = J("t8/t8_scan.json")["summary"]
put("t8.new_attrs", s8["new_attrs_total"], 2092)
put("t8.pmi_hits", s8["pmi_hits"], 59)
put("t8.pmi_models", s8["models_with_pmi_hits"], 12)
put("t8.inputs", s8["models"], 17)
put("t8.subsets", s8["geomsubsets_total"], 0)
put("t8.rel_hits", s8["hits_with_relationship"], 0)
put("t8.numeric_hits", s8["typed_numeric_hits"], 2)

# ---- T9 float64 复拟（F3-14）
s9 = J("t43/t9_float_precision.json")
put("t9.n", s9["float64_faces_json"]["n"], 1715)
put("t9.p99", round(s9["float64_faces_json"]["p99"], 4), 0.0073)

# ---- T11 minimality 消融（F3-17，r1b）
s11 = J("t11b/minimality_ablation.json")["summary"]
put("t11.targets", int(s11["full"]["K1_locate"].split("/")[1]), 2527)
put("t11.values", int(s11["full"]["K2_read"].split("/")[1]), 617)
put("t11.units_phys_left", int(s11["no_units"]["K3_phys"].split("/")[0]), 4)
put("t11.units_phys_wrong", 617 - int(s11["no_units"]["K3_phys"].split("/")[0]), 613)
put("t11.units_k5", s11["no_units"]["K5_judged"] + "|" + s11["no_units"]["K5_clean"], "128/128|122/122")

# ---- T12 组合（F3-18，r1b）
s12 = J("t12b/composition_check.json")
put("t12.instances", s12["instances"], 18)
put("t12.annos", s12["composed"]["annos"], 929)
put("t12.subsets", s12["composed"]["subsets"], 4147)
put("t12.targets", s12["composed"]["rel_targets"], 2763)
put("t12.foreign", s12["composed"]["foreign_targets"] + s12["flattened"]["foreign_targets"], 0)
put("t12.family_fail", s12["composed"]["validate_family_fail"] + s12["flattened"]["validate_family_fail"], 0)

out = Path(os.environ.get("R1_OUT", R / "canonical_r1.json"))
json.dump(dict(sorted(K.items())), open(out, "w"), indent=1)
print(f"[51] {len(K)} keys -> {out}（全部 assert 通过）")
