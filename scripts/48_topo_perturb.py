# R1 T2（实验①b，回应 R2-4 "topology changes"）：B-rep 拓扑／坐标扰动下的面对齐表现。
# 设计 → notes/20261005-revision-numbers.md §T2；结果 → notes/20261005-revision-numbers-t1t2t8.md §T2。
# 做法：**原样执行未改动的 14_face_match.py 源码**（经 Part 模块垫片把扰动后的 shape 喂给它），
#   STEP 文本侧照旧解析，只改 OCC 侧拓扑（或只改 STEP 文本侧坐标），再与基线 match 逐面对账：
#   base            无扰动（健全性：须与 out/e1/<model>.match.json 逐键相同）
#   split_periodic  每个周期面（圆柱/圆锥/球/环；闭合面与半圆柱等均算）沿「含轴、过 u 中点」的平面剖开 → 1:N
#                   （闭合面恰在缝线与对侧剖成两半；NIST 件多为半圆柱，故不只剖闭合面——只剖闭合面在 ctc_01 上 0 处可剖）
#   unify           ShapeUpgrade.UnifySameDomain 合并同域相邻面 → N:1
#   noise_<ε>_R<n>  STEP 文本侧 CARTESIAN_POINT 坐标加 ±ε mm 均匀扰动（固定种子；英寸件按 scale 换算），
#                   ε ∈ {1e-5,1e-4,1e-3}，指纹圆整位 R ∈ {4(基线),3}（对 14 源码做单行替换 R = 4 → R = n，其余逐字不动）
#   round_R3/R5     无扰动、只改圆整位
# 对账口径：未变面按 hashCode 对回基线面号，比 STEP id 是否不变；新面（剖出的子面／合并面）按构造或
#   面上取点归属到基线父面，分「对到父面 STEP id（正确）／未匹配（fail closed）／对到别的 STEP id（错配）」。
# 用法: T2_STP=<input.stp> T2_OUT=<out_dir> T2_BASE=<baseline match.json> freecadcmd 48_topo_perturb.py
#      （参数走环境变量，理由同 47）；输出 <out_dir>/<model>.t2.json（各变体 match.json 另存 <out_dir>/<variant>/）。
import json
import math
import os
import random
import re
import sys
import tempfile
import time
import types

import FreeCAD  # noqa: F401
import Part

HERE = os.path.dirname(os.path.abspath(__file__))
P14 = os.path.join(HERE, "14_face_match.py")
stp, out_dir, base_json = os.environ["T2_STP"], os.environ["T2_OUT"], os.environ["T2_BASE"]
model = os.path.splitext(os.path.basename(stp))[0]
base = json.load(open(base_json))
base_map = {int(k): int(v) for k, v in base["occ_to_step"].items()}
scale = float(base["scale"])
os.makedirs(out_dir, exist_ok=True)


def run14(step_path, shape_obj, out_json, R=None):
    """执行 14 原文件源码；Part.Shape().read() 被垫片接管为返回给定 shape。"""
    src = open(P14, encoding="utf-8").read()
    if R is not None:
        new = re.sub(r"^R = 4 ", f"R = {R} ", src, count=1, flags=re.M)
        assert new != src, "14 中未找到 R = 4"
        src = new

    class _S:
        def read(self, p):
            pass

        def __getattr__(self, n):
            return getattr(shape_obj, n)

    shim = types.ModuleType("Part")
    shim.Shape = _S
    old_part, old_argv = sys.modules.get("Part"), sys.argv
    sys.modules["Part"] = shim
    sys.argv = ["14_face_match.py", step_path, out_json]
    try:
        exec(compile(src, P14, "exec"), {"__name__": "__r14__", "__file__": P14})
    finally:
        sys.modules["Part"] = old_part
        sys.argv = old_argv
    m = json.load(open(out_json))
    return {int(k): int(v) for k, v in m["occ_to_step"].items()}, m


def read_shape():
    s = Part.Shape()
    s.read(stp)
    return s


def interior_point(f):
    """面内一点：取粗三角化一个三角形的质心投影回曲面（避开边界）。"""
    vv, tt = f.tessellate(0.5)
    if not tt:
        return None
    a, b, c = (vv[i] for i in tt[len(tt) // 2])
    p = (a + b + c) * (1.0 / 3.0)
    try:
        q = f.Surface.projectPoint(p, "NearestPoint")
        return q
    except Exception:
        return p


def split_periodic(shape):
    from BOPTools import SplitAPI
    faces, parent_of, n_split, errs = [], [], 0, []
    for i, f in enumerate(shape.Faces):
        surf = f.Surface
        tn = type(surf).__name__
        u0, u1, v0, v1 = f.ParameterRange
        if tn in ("Cylinder", "Cone", "Sphere", "Toroid"):
            try:
                a = FreeCAD.Vector(surf.Axis).normalize()
                c = FreeCAD.Vector(surf.Center)
                p0 = f.valueAt(0.5 * (u0 + u1), 0.5 * (v0 + v1))
                d = p0 - c
                d = d - a * d.dot(a)
                n = a.cross(d).normalize()
                B = 10.0 * max(f.BoundBox.DiagonalLength, 1.0)
                pl = Part.Plane(c, n).toShape(-B, B, -B, B)
                pieces = SplitAPI.slice(f, [pl], "Split").Faces
                if len(pieces) >= 2:
                    faces += pieces
                    parent_of += [i] * len(pieces)
                    n_split += 1
                    continue
            except Exception as e:
                errs.append({"index": i, "err": f"{type(e).__name__}: {e}"[:160]})
        faces.append(f)
        parent_of.append(i)
    return Part.makeCompound(faces), parent_of, n_split, errs


def unify(shape):
    u = Part.ShapeUpgrade.UnifySameDomain(shape)
    u.build()
    res = u.shape()
    base_hash = {f.hashCode(): i for i, f in enumerate(shape.Faces)}
    res_hash = {f.hashCode() for f in res.Faces}
    gone = [i for i, f in enumerate(shape.Faces) if f.hashCode() not in res_hash]
    pts = {i: interior_point(shape.Faces[i]) for i in gone}
    parent_of = []
    for f in res.Faces:
        h = f.hashCode()
        if h in base_hash:
            parent_of.append(base_hash[h])
            continue
        ps = [i for i, p in pts.items() if p is not None and f.distToShape(Part.Vertex(p))[0] < 1e-5]
        parent_of.append(ps if ps else None)
    return res, parent_of, len(gone)


def perturb_step(eps_mm, seed=42):
    rng = random.Random(seed)
    eps = eps_mm / scale                     # 文件单位
    txt = open(stp, encoding="utf-8", errors="replace").read()
    num = re.compile(r"[-+]?\d+\.?\d*(?:[Ee][-+]?\d+)?")

    def rep(m):
        coords = num.sub(lambda x: repr(float(x.group()) + rng.uniform(-eps, eps)), m.group(2))
        return m.group(1) + coords + m.group(3)

    txt2 = re.sub(r"(CARTESIAN_POINT\s*\(\s*'[^']*'\s*,\s*\()([^)]*)(\))", rep, txt)
    fd, p = tempfile.mkstemp(suffix=".stp")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(txt2)
    return p


def judge(mapping, parent_of):
    """parent_of[k] = 基线面号 | [基线面号...] | None；返回逐类计数。"""
    r = {"n_occ": len(parent_of), "matched": len(mapping), "unchanged_same": 0, "unchanged_diff": 0,
         "unchanged_unmatched": 0, "new_faces": 0, "new_correct": 0, "new_unmatched": 0, "new_wrong": 0,
         "wrong_examples": []}
    for k, par in enumerate(parent_of):
        sid = mapping.get(k)
        if isinstance(par, int) and not isinstance(par, bool) and parent_of.count(par) == 1:
            exp = base_map.get(par)
            if sid is None:
                r["unchanged_unmatched"] += 1
            elif sid == exp:
                r["unchanged_same"] += 1
            else:
                r["unchanged_diff"] += 1
                r["wrong_examples"].append({"occ": k, "parent": par, "got": sid, "exp": exp})
            continue
        r["new_faces"] += 1
        pars = par if isinstance(par, list) else ([par] if par is not None else [])
        exp = {base_map.get(p) for p in pars} - {None}
        if sid is None:
            r["new_unmatched"] += 1
        elif sid in exp:
            r["new_correct"] += 1
        else:
            r["new_wrong"] += 1
            r["wrong_examples"].append({"occ": k, "parents": pars, "got": sid, "exp": sorted(exp)})
    r["wrong_examples"] = r["wrong_examples"][:20]
    return r


res = {"model": model, "scale": scale, "baseline_matched": len(base_map), "variants": {}}
shape0 = read_shape()
ident = list(range(len(shape0.Faces)))


def record(name, mapping, meta, parent_of, extra=None):
    j = judge(mapping, parent_of)
    j["match_rate"] = round(len(mapping) / max(1, len(parent_of)), 4)
    j["unmatched_baseline_step_ids"] = len(set(base_map.values()) - set(mapping.values()))
    if extra:
        j.update(extra)
    res["variants"][name] = j
    print(f"[48] {model} {name} occ={j['n_occ']} matched={j['matched']} same={j['unchanged_same']} "
          f"diff={j['unchanged_diff']} new={j['new_faces']} new_ok={j['new_correct']} "
          f"new_unm={j['new_unmatched']} new_wrong={j['new_wrong']}", flush=True)


def vpath(name):
    d = os.path.join(out_dir, name)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{model}.match.json")


t0 = time.time()
m, meta = run14(stp, shape0, vpath("base"))
record("base", m, meta, ident, {"identical_to_baseline": m == base_map})

shp, par, nsp, errs = split_periodic(read_shape())
m, meta = run14(stp, shp, vpath("split_periodic"))
record("split_periodic", m, meta, par, {"faces_split": nsp, "split_errors": errs})

sh = read_shape()
ushp, upar, ngone = unify(sh)
m, meta = run14(stp, ushp, vpath("unify"))
record("unify", m, meta, upar, {"faces_merged_away": ngone})

for eps in (1e-5, 1e-4, 1e-3):
    p = perturb_step(eps)
    try:
        for R in (None, 3):
            nm = f"noise_{eps:g}_R{R or 4}"
            m, meta = run14(p, read_shape(), vpath(nm), R=R)
            record(nm, m, meta, ident)
    finally:
        os.remove(p)

for R in (3, 5):
    m, meta = run14(stp, read_shape(), vpath(f"round_R{R}"), R=R)
    record(f"round_R{R}", m, meta, ident)

res["seconds"] = round(time.time() - t0, 1)
oj = os.path.join(out_dir, f"{model}.t2.json")
with open(oj + ".tmp", "w") as fh:
    json.dump(res, fh, indent=1)
os.replace(oj + ".tmp", oj)
print(f"[48] DONE {model} {res['seconds']}s", flush=True)
