# R1 T1（实验①a，回应 R1-3/R2-4）：面对齐指纹与下游 C3 对网格化的敏感性扫描。
# 设计 → notes/20261005-revision-numbers.md §T1；结果 → notes/20261005-revision-numbers-t1t2t8.md。
# 两种模式：
#   ① T1_STP=<input.stp> T1_OUT=<out_root> T1_CYL=<cylinders.json> freecadcmd 47_tess_sweep.py
#      （参数走环境变量：freecadcmd 会把命令行里多余的文件参数当文档再打开一遍，白耗时间内存）
#      对一件模型逐变体逐面网格化：OCC deflection ∈ {0.01,0.05,0.1(基线=11_face_tess.py,逐字节复现),0.5} mm
#      （角度用默认，与 11 同），另加粗档 occ_d0.5_a1.0（MeshPart 标准网格器，线 0.5 mm＋角 1.0 rad），
#      另两种网格器 Mefisto（MeshPart MaxLength，L 按「总面积/基线三角数」等三角数标定）与 Netgen（Fineness=2）。
#      T1_VARIANTS=逗号列表 可只跑部分变体。
#      每变体输出 <out_root>/<variant>/<model>.faces.json（格式同 11，供 15/16/36 之后复用），
#      并在同一进程内算：网格化前后 B-rep 顶点指纹是否逐面不变；C3 asset-only 拟合（与 19 --subset 同算法，
#      点先转 float32 以复现 USD Vec3f 存储）与 31 的 60° 角覆盖标记；汇总到 <out_root>/summary/<model>.json。
#      每变体都**重新读 STEP**（避免 OCC 复用已有三角化）。输出先写 .tmp 再改名，可从头重跑。
#   ② python 47_tess_sweep.py --aggregate <out_root> [<baseline_match_dir>]
#      汇总全部 summary/*.json → <out_root>/t1_table.json；若给基线 match 目录，另比对
#      <out_root>/match_rerun/<model>.match.json（run_r1_t1t2.sh 在同一节点重跑 14 产出）与基线 occ_to_step 逐键相同。
#      注：14 只读 STEP 文本与 B-rep 顶点、不读网格，故重跑一次即可；逐变体的证据是同进程网格化后的指纹不变计数。
import json
import math
import os
import sys
import time

AGG = "--aggregate" in sys.argv
EIG_RATIO_FLAG = 1e-3   # 探索性阈值（ctc_01 冒烟后设定，未经全集验证——结果须标「探索」）


def c3_fit(verts, tris):
    """与 19_hole_v2.py C3 同算法：法线协方差最小特征向量为轴，⊥轴平面 Kasa 圆；另算 31 的角覆盖。"""
    import numpy as np
    V = np.asarray(verts, dtype=np.float32).astype(np.float64)   # 复现 USD points(Vec3f) 精度
    T = np.asarray(tris, dtype=np.int64)
    tri = V[T]
    pts = tri.reshape(-1, 3)
    if len(pts) < 8:
        return None
    nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ln = np.linalg.norm(nrm, axis=1)
    nrm = nrm[ln > 1e-12] / ln[ln > 1e-12][:, None]
    if len(nrm) < 1:
        return None
    w, vec = np.linalg.eigh(nrm.T @ nrm)
    e1v, e2v = vec[:, 1], vec[:, 2]
    uv = np.column_stack([pts @ e1v, pts @ e2v])
    A = np.column_stack([2 * uv, np.ones(len(uv))])
    sol, *_ = np.linalg.lstsq(A, (uv ** 2).sum(1), rcond=None)
    cx, cy, c0 = sol
    r = float(np.sqrt(max(c0 + cx * cx + cy * cy, 0.0)))
    ang = np.sort(np.arctan2(uv[:, 1] - cy, uv[:, 0] - cx))
    gaps = np.diff(np.concatenate([ang, [ang[0] + 2 * np.pi]]))
    cov = float(np.degrees(2 * np.pi - gaps.max()))
    # 探索性诊断（非 31 的既有规则）：法线协方差最小/次小特征值比——OCC 条带网格为 0，非条带网格轴不定时变大
    return {"n": int(len(pts)), "fitted_r": r, "coverage_deg": cov,
            "axis_eig_ratio": float(w[0] / w[1]) if w[1] > 0 else None}


def run_model(stp, out_root, cyl_json):
    import FreeCAD  # noqa: F401
    import Part
    import MeshPart

    model = os.path.splitext(os.path.basename(stp))[0]
    R = 4
    cyls = {c["face_index"]: c["radius"] for c in json.load(open(cyl_json))}

    def read():
        s = Part.Shape()
        s.read(stp)
        return s

    def fingerprints(shape):
        return [sorted(tuple(round(c, R) for c in (v.X, v.Y, v.Z)) for v in f.Vertexes) for f in shape.Faces]

    def free_flags(shape):
        h = {f.hashCode() for s in shape.Solids for f in s.Faces}
        return [f.hashCode() not in h for f in shape.Faces]

    base_shape = read()
    fp0 = fingerprints(base_shape)
    area_tot = sum(f.Area for f in base_shape.Faces)
    # 基线三角数（与 11 同设置）用于 Mefisto 的等三角数标定
    n_base = sum(len(f.tessellate(0.1)[1]) for f in base_shape.Faces)
    L = math.sqrt(4.0 * area_tot / (math.sqrt(3.0) * max(n_base, 1)))

    variants = [("occ_d0.01", "occ", 0.01), ("occ_d0.05", "occ", 0.05), ("occ_d0.1", "occ", 0.1),
                ("occ_d0.5", "occ", 0.5), ("occ_d0.5_a1.0", "std", (0.5, 1.0)),
                ("mefisto", "mefisto", L), ("netgen_f2", "netgen", 2)]
    only = os.environ.get("T1_VARIANTS")
    if only:
        variants = [v for v in variants if v[0] in only.split(",")]
    summ = {"model": model, "n_faces": len(fp0), "area_mm2": area_tot, "n_tris_baseline": n_base,
            "mefisto_maxlength": L, "variants": {}}
    for name, kind, par in variants:
        t0 = time.time()
        shape = read()
        free = free_flags(shape)
        faces, fails = [], []
        for i, f in enumerate(shape.Faces):
            try:
                if kind == "occ":
                    vv, tt = f.tessellate(par)
                    verts = [[v.x, v.y, v.z] for v in vv]
                    tris = [list(t) for t in tt]
                else:
                    if kind == "std":
                        m = MeshPart.meshFromShape(Shape=f, LinearDeflection=par[0], AngularDeflection=par[1],
                                                   Relative=False)
                    elif kind == "mefisto":
                        m = MeshPart.meshFromShape(Shape=f, MaxLength=par)
                    else:
                        m = MeshPart.meshFromShape(Shape=f, Fineness=int(par), SecondOrder=0, Optimize=1, AllowQuad=0)
                    pp, ff = m.Topology
                    verts = [[p.x, p.y, p.z] for p in pp]
                    tris = [list(t) for t in ff]
            except Exception as e:  # 单面失败如实记录，不中断
                verts, tris = [], []
                fails.append({"index": i, "err": f"{type(e).__name__}: {e}"[:200]})
            faces.append({"index": i, "surface": type(f.Surface).__name__, "free": free[i],
                          "verts": verts, "tris": tris})
        t_mesh = time.time() - t0
        # 网格化之后，同一 shape 对象上的 B-rep 顶点指纹是否逐面不变（构造性结论的实测）
        fp1 = fingerprints(shape)
        fp_same = sum(1 for a, b in zip(fp0, fp1) if a == b)
        # C3（枚举只看 surface=="Cylinder" 的面，同 19 的 USD 侧枚举口径）
        c3 = []
        for fc in faces:
            if fc["surface"] != "Cylinder" or not fc["tris"]:
                continue
            res = c3_fit(fc["verts"], fc["tris"])
            nom = cyls.get(fc["index"])
            row = {"face_index": fc["index"], "in_nominal_list": nom is not None}
            if res:
                row.update(res)
                row["abs_err"] = abs(res["fitted_r"] - nom) if nom is not None else None
            else:
                row["abs_err"] = None
            c3.append(row)
        d = os.path.join(out_root, name)
        os.makedirs(d, exist_ok=True)
        fj = os.path.join(d, f"{model}.faces.json")
        with open(fj + ".tmp", "w") as fh:
            json.dump({"file": stp, "accuracy": par if kind == "occ" else None, "mesher": kind,
                       "param": par, "n_faces": len(faces), "faces": faces}, fh)
        os.replace(fj + ".tmp", fj)
        ntri = sum(len(x["tris"]) for x in faces)
        summ["variants"][name] = {"mesher": kind, "param": par, "n_tris": ntri,
                                  "n_verts": sum(len(x["verts"]) for x in faces),
                                  "empty_faces": sum(1 for x in faces if not x["tris"]),
                                  "mesh_failures": fails, "fingerprint_unchanged": fp_same,
                                  "seconds": round(t_mesh, 2), "c3_rows": c3}
        print(f"[47] {model} {name} tris={ntri} empty={summ['variants'][name]['empty_faces']} "
              f"fp_same={fp_same}/{len(fp0)} c3={len(c3)} {t_mesh:.1f}s", flush=True)
        del faces, shape
    sd = os.path.join(out_root, "summary")
    os.makedirs(sd, exist_ok=True)
    sj = os.path.join(sd, f"{model}.json")
    with open(sj + ".tmp", "w") as fh:
        json.dump(summ, fh, indent=1)
    os.replace(sj + ".tmp", sj)
    print(f"[47] DONE {model}", flush=True)


def aggregate(out_root, base_match_dir=None):
    import glob
    import numpy as np
    rows = {}
    for sj in sorted(glob.glob(os.path.join(out_root, "summary", "*.json"))):
        s = json.load(open(sj))
        for name, v in s["variants"].items():
            r = rows.setdefault(name, {"models": 0, "n_faces": 0, "n_tris": 0, "fp_unchanged": 0,
                                       "empty_faces": 0, "mesh_failures": 0, "errs": [],
                                       "enumerated": 0, "matched_nominal": 0, "unmeasurable": 0,
                                       "flagged": 0, "big": 0, "big_flagged": 0, "big_flagged_eig": 0,
                                       "flagged_eig": 0, "match_identical": 0,
                                       "match_checked": 0})
            r["models"] += 1
            r["n_faces"] += s["n_faces"]
            r["n_tris"] += v["n_tris"]
            r["fp_unchanged"] += v["fingerprint_unchanged"]
            r["empty_faces"] += v["empty_faces"]
            r["mesh_failures"] += len(v["mesh_failures"])
            for c in v["c3_rows"]:
                r["enumerated"] += 1
                r["matched_nominal"] += int(c["in_nominal_list"])
                if c.get("abs_err") is None:
                    r["unmeasurable"] += int(c["in_nominal_list"])
                    continue
                r["errs"].append(c["abs_err"])
                fl = c["coverage_deg"] < 60.0
                fe = (c.get("axis_eig_ratio") or 0.0) > EIG_RATIO_FLAG
                r["flagged"] += int(fl)
                r["flagged_eig"] += int(fe)
                if c["abs_err"] > 0.04:
                    r["big"] += 1
                    r["big_flagged"] += int(fl)
                    r["big_flagged_eig"] += int(fe)
            if base_match_dir:
                mj = os.path.join(out_root, "match_rerun", f"{s['model']}.match.json")
                bj = os.path.join(base_match_dir, f"{s['model']}.match.json")
                if os.path.exists(mj) and os.path.exists(bj):
                    r["match_checked"] += 1
                    a = json.load(open(mj))["occ_to_step"]
                    b = json.load(open(bj))["occ_to_step"]
                    r["match_identical"] += int(a == b)
    table = {}
    for name, r in rows.items():
        e = np.array(r.pop("errs")) if r["errs"] else np.array([np.nan])
        r["c3_measured"] = int(np.isfinite(e).sum())
        r["c3_median_err"] = float(f"{np.nanmedian(e):.2g}")
        r["c3_p99_err"] = round(float(np.nanpercentile(e, 99)), 4)
        r["c3_max_err"] = round(float(np.nanmax(e)), 4)
        r["c3_gt_0.04mm"] = r.pop("big")
        r["c3_gt_0.04mm_flagged"] = r.pop("big_flagged")
        r["c3_gt_0.04mm_flagged_eig"] = r.pop("big_flagged_eig")
        r["flag_rate"] = round(r["flagged"] / max(1, r["c3_measured"]), 4)
        r["flag_rate_eig"] = round(r["flagged_eig"] / max(1, r["c3_measured"]), 4)
        table[name] = r
    out = os.path.join(out_root, "t1_table.json")
    json.dump(table, open(out, "w"), indent=1)
    for k, r in table.items():
        print(k, {x: r[x] for x in ("models", "n_tris", "fp_unchanged", "n_faces", "match_identical",
                                    "match_checked", "c3_measured", "c3_median_err", "c3_p99_err",
                                    "c3_max_err", "flag_rate", "c3_gt_0.04mm", "c3_gt_0.04mm_flagged",
                                    "flag_rate_eig", "c3_gt_0.04mm_flagged_eig")})


if AGG:
    i = sys.argv.index("--aggregate")
    aggregate(sys.argv[i + 1], sys.argv[i + 2] if len(sys.argv) > i + 2 else None)
else:
    run_model(os.environ["T1_STP"], os.environ["T1_OUT"], os.environ["T1_CYL"])
