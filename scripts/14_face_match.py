# E1 步骤二：STEP ADVANCED_FACE id ↔ OCC 面 index 匹配（路线 B，设计 → notes/20260828-e1-design.md §2）
# 指纹 = 边界顶点坐标集合（STEP 侧 FACE_BOUND→…→CARTESIAN_POINT；OCC 侧 face.Vertexes，同源同值）
#        ＋ 面类型/半径 tie-break；Jaccard 重叠贪心 1:1（seam/拆分导致两侧集合非严格相等）。
# 单位自校准：英寸文件 OCC 读入即转 mm，而文件内 INCH 字符串可能只属 PMI 单位定义（stc_06 实测误判），
#            故对 scale∈{1, 25.4} 各匹配一遍取率高者，选择入报告。匹配率与 unmatched 如实报告。
# 用法: freecadcmd 14_face_match.py <input.stp> <out_match.json>
import json
import re
import sys

import os

import FreeCAD  # noqa: F401
import Part

# E8 消融开关：ABLATE=noscale（禁双 scale 自校准，只跑 scale=1）/ notype（禁面类型/半径加权）
ABLATE = os.environ.get("ABLATE", "")

args = [a for a in sys.argv if not a.endswith(("FreeCADCmd", "freecadcmd", ".py"))]
stp, out = args[-2], args[-1]
R = 4  # 坐标圆整位数（mm 级模型，1e-4 mm 精度）

# ---- STEP 实体表 ----
txt = open(stp, encoding="utf-8", errors="replace").read()
data = txt.split("DATA;", 1)[1].split("ENDSEC;", 1)[0]
flat = re.sub(r"\s+", " ", data)
ent = {}
for m in re.finditer(r"#(\d+)\s*=\s*([A-Z0-9_]+)\s*\((.*?)\)\s*;", flat):
    ent[int(m.group(1))] = (m.group(2), m.group(3))

def refs(s):
    return [int(x) for x in re.findall(r"#(\d+)", s)]

SURFACE_TYPES = {"PLANE": "Plane", "CYLINDRICAL_SURFACE": "Cylinder", "CONICAL_SURFACE": "Cone",
                 "SPHERICAL_SURFACE": "Sphere", "TOROIDAL_SURFACE": "Toroid"}

def build_step_faces(scale):
    cpt = {}
    for i, (t, a) in ent.items():
        if t == "CARTESIAN_POINT":
            nums = re.findall(r"[-\d.Ee+]+", a.split("(", 1)[1]) if "(" in a else []
            if len(nums) >= 3:
                cpt[i] = tuple(round(float(x) * scale, R) for x in nums[:3])
    step_faces = {}
    for i, (t, a) in ent.items():
        if t != "ADVANCED_FACE":
            continue
        verts, frontier, seen = set(), refs(a), set()
        for _ in range(6):
            nxt = []
            for r in frontier:
                if r in seen:
                    continue
                seen.add(r)
                if r in cpt:
                    verts.add(cpt[r])
                    continue
                if r in ent and ent[r][0] in ("FACE_BOUND", "FACE_OUTER_BOUND", "EDGE_LOOP",
                                              "ORIENTED_EDGE", "EDGE_CURVE", "VERTEX_POINT"):
                    nxt += refs(ent[r][1])
            frontier = nxt
        styp, srad = None, None
        for r in refs(a):
            if r in ent and ent[r][0] in SURFACE_TYPES:
                styp = SURFACE_TYPES[ent[r][0]]
                nums = re.findall(r"[-\d.Ee+]+", ent[r][1].rsplit(",", 1)[-1])
                if styp in ("Cylinder", "Sphere") and nums:
                    srad = round(float(nums[-1]) * scale, R)
        step_faces[i] = {"verts": frozenset(verts), "type": styp, "radius": srad}
    return step_faces

# ---- OCC 侧 ----
shape = Part.Shape()
shape.read(stp)
occ_faces = []
for idx, f in enumerate(shape.Faces):
    verts = frozenset(tuple(round(c, R) for c in (v.X, v.Y, v.Z)) for v in f.Vertexes)
    styp = type(f.Surface).__name__
    srad = round(f.Surface.Radius, R) if hasattr(f.Surface, "Radius") else None
    occ_faces.append({"index": idx, "verts": verts, "type": styp, "radius": srad})

def run_match(step_faces):
    vert_index = {}
    for sid, sf in step_faces.items():
        for v in sf["verts"]:
            vert_index.setdefault(v, set()).add(sid)
    pairs = []
    for of in occ_faces:
        cand_ids = set()
        for v in of["verts"]:
            cand_ids |= vert_index.get(v, set())
        for sid in cand_ids:
            sf = step_faces[sid]
            inter = len(of["verts"] & sf["verts"])
            union = len(of["verts"] | sf["verts"]) or 1
            score = inter / union
            if score < 0.34:
                continue
            if sf["type"] and sf["type"] == of["type"]:
                if ABLATE != "notype":
                    score += 0.5
                    if sf["radius"] is not None and sf["radius"] == of["radius"]:
                        score += 0.25
            pairs.append((score, of["index"], sid))
    match, used_o, used_s = {}, set(), set()
    for score, oi, sid in sorted(pairs, reverse=True):
        if oi in used_o or sid in used_s:
            continue
        match[oi] = sid
        used_o.add(oi)
        used_s.add(sid)
    return match

best_scale, best_match = None, {}
for scale in ((1.0,) if ABLATE == "noscale" else (1.0, 25.4)):
    m = run_match(build_step_faces(scale))
    if len(m) > len(best_match):
        best_scale, best_match = scale, m

n_step = sum(1 for t, _ in ent.values() if t == "ADVANCED_FACE")
unmatched = [of["index"] for of in occ_faces if of["index"] not in best_match]
rep = {"file": stp, "scale": best_scale, "n_occ": len(occ_faces), "n_step": n_step,
       "matched": len(best_match), "unmatched": len(unmatched),
       "match_rate": round(len(best_match) / max(1, len(occ_faces)), 4),
       "occ_to_step": best_match, "unmatched_idx": unmatched}
json.dump(rep, open(out, "w"), indent=1)
print(f"[14] scale={best_scale} occ={len(occ_faces)} step={n_step} matched={len(best_match)} "
      f"unm={len(unmatched)} rate={rep['match_rate']}")
