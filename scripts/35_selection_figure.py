# Fig 8：选择往返（selection round-trip）——交互式评审环境在 profile 化场景上实际能做的动作，画成静态图。
# 双向都画，因为评审工具两边都用：
#   (a) 选中一条公差标注 → 高亮它管辖的面，并读出 typed 字段（值/带/单位/语义）＋**仅凭场景的公差对判**
#   (b) 选中一张面      → 列出所有管辖它的标注
# ⚠️ 口径：全部信息取自交付的 USD 场景（pmi:type / value / bounds / sourceUnit / dimName /
#    appliesTo / brepFace subset）与 E11 的 stage-only 判定输出，**不查 STEP 源**。这是 CF1–CF3
#    读取路径的可视化，不是我们实现了一个交互工具——本图是该路径的一次静态取样。
# 版式（2026-08-29 第三轮 review 重做）：viewport 在上、inspector 面板在下，读起来像评审环境的属性面板；
#    字号全部 ≥8 pt（本刊 8–12 pt 硬要求），画幅按双栏满宽 174 mm 作图，排版时不缩放。
# 用法: .venv/bin/python scripts/35_selection_figure.py [model_stem]
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from pxr import Usd, UsdGeom

os.chdir(os.path.join(os.path.dirname(__file__), ".."))
WIDE = 6.85                     # 174 mm
FS = 8.0                        # 本刊下限
plt.rcParams.update({"font.size": FS, "figure.dpi": 300, "savefig.bbox": None,
                     "font.family": "Helvetica", "ps.fonttype": 42, "pdf.fonttype": 42})
BLUE, WARM, GRAY, GREEN = "#2b5f9e", "#c4552d", "#c9ced6", "#3a7d44"
STEM = sys.argv[1] if len(sys.argv) > 1 else "nist_ctc_01_asme1_ap242-e1"

stage = Usd.Stage.Open(f"out/proto_v2/{STEM}.usdc")
mesh = next(p for p in stage.Traverse() if p.IsA(UsdGeom.Mesh))
m = UsdGeom.Mesh(mesh)
V = np.array(m.GetPointsAttr().Get())
idx = np.array(m.GetFaceVertexIndicesAttr().Get()).reshape(-1, 3)

subsets = {}                       # subset path -> 三角形索引
for p in stage.Traverse():
    if p.IsA(UsdGeom.Subset) and UsdGeom.Subset(p).GetFamilyNameAttr().Get() == "brepFace":
        subsets[p.GetPath().pathString] = np.array(UsdGeom.Subset(p).GetIndicesAttr().Get())

def A(p, n):
    a = p.GetAttribute(n)
    return a.Get() if a else None

annos = [p for p in stage.Traverse() if A(p, "pmi:type")]

# --- (a) 选一条带双侧带、且 E11 已对判过的直径标注 ---
E11 = json.load(open("out/e11/tolerance_judgement.json"))
judged = {(r["model"], r["stepId"]): [] for r in E11["rows"]}
for r in E11["rows"]:
    judged[(r["model"], r["stepId"])].append(r)

sel = None
for p in annos:
    rel = p.GetRelationship("pmi:appliesTo")
    if (A(p, "pmi:type") == "DIMENSIONAL_SIZE" and A(p, "pmi:dimName") == "diameter"
            and A(p, "pmi:value") is not None and A(p, "pmi:lowerBound") is not None
            and rel and rel.GetTargets() and (STEM, A(p, "pmi:stepId")) in judged):
        sel = (p, [str(t) for t in rel.GetTargets()])
        break
assert sel, "该模型没有既满足条件又进入 E11 对判的标注"
anno, targets = sel
rows = judged[(STEM, A(anno, "pmi:stepId"))]

# --- (b) 反向：取其中一张面，找出所有管辖它的标注 ---
probe = targets[0]
governing = [p for p in annos
             if p.GetRelationship("pmi:appliesTo")
             and probe in [str(t) for t in p.GetRelationship("pmi:appliesTo").GetTargets()]]

fig = plt.figure(figsize=(WIDE, 4.0))
gs = fig.add_gridspec(2, 2, height_ratios=[0.92, 1.3], hspace=0.02, wspace=0.03,
                      left=0.005, right=0.995, top=0.93, bottom=0.01)

lim = [(V[:, i].min(), V[:, i].max()) for i in range(3)]
ctr = [(l + h) / 2 for l, h in lim]
EXT = np.array([h - l for l, h in lim])

def draw(ax, hi_tris, title, zoom=None, hl=WARM):
    hi = set(hi_tris.tolist())
    base = np.array([t for i, t in enumerate(idx) if i not in hi])
    ax.add_collection3d(Poly3DCollection(V[base], facecolor=GRAY, edgecolor="none",
                                         alpha=0.22, rasterized=True))
    ax.add_collection3d(Poly3DCollection(V[idx[list(hi)]], facecolor=hl, edgecolor=hl,
                                         linewidth=0.25, rasterized=True))
    if zoom is None:
        for i, s in enumerate("xyz"):
            getattr(ax, f"set_{s}lim")(ctr[i] - EXT[i] / 2 * 1.02, ctr[i] + EXT[i] / 2 * 1.02)
        ax.set_box_aspect(tuple(EXT / EXT.max()))
    else:
        c, r = zoom
        for i, s in enumerate("xyz"):
            getattr(ax, f"set_{s}lim")(c[i] - r, c[i] + r)
        ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=24, azim=-58)
    try:
        ax.set_box_aspect(ax.get_box_aspect(), zoom=1.12)   # 压掉 3D 轴自带的大片留白
    except TypeError:
        pass
    ax.set_axis_off()


def inspector(ax, header, fields, note, ec, vx=0.33):
    """把读出画成属性面板：标题条 ＋ 字段/值两栏 ＋ 脚注。字段名与值都用等宽体，像工具的 UI。"""
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.012, 0.02), 0.976, 0.96, boxstyle="round,pad=0.004",
                                fc="white", ec=ec, lw=1.0, zorder=1))
    ax.add_patch(FancyBboxPatch((0.012, 0.80), 0.976, 0.18, boxstyle="round,pad=0.004",
                                fc=ec, ec=ec, lw=1.0, zorder=2))
    ax.text(0.032, 0.885, header, fontsize=FS, color="white", va="center",
            family="monospace", zorder=3)
    y, pitch = 0.735, 0.072                           # pitch≈11 pt @ 本图版式，8 pt 字不相撞
    for k, v in fields:
        if k == "":                                   # 分隔线＋小标题
            ax.plot([0.032, 0.968], [y + 0.030, y + 0.030], color="#d6dbe2", lw=0.7, zorder=3)
            ax.text(0.032, y - 0.012, v, fontsize=FS, style="italic", color="#555",
                    va="center", zorder=3)
            y -= pitch
            continue
        ax.text(0.032, y, k, fontsize=FS, family="monospace", color="#666", va="center", zorder=3)
        ax.text(vx, y, v, fontsize=FS, family="monospace", color="#111", va="center", zorder=3)
        y -= pitch
    if note:
        ax.text(0.032, 0.085, note, fontsize=FS, style="italic", color="#555", va="center", zorder=3)

# ---------- (a) ----------
ax1 = fig.add_subplot(gs[0, 0], projection="3d")
tri_a = np.concatenate([subsets[t] for t in targets if t in subsets])
_tv = [V[idx[subsets[t]]].reshape(-1, 3) for t in targets if t in subsets]
_all = np.concatenate(_tv)
_types = {A(stage.GetPrimAtPath(t), "pmi:surfaceType") for t in targets if t in subsets}
_one_body = (len(_tv) > 1 and _types == {"Cylinder"}
             and all(((v.max(0) - v.min(0)) >= 0.55 * (_all.max(0) - _all.min(0))).all() for v in _tv))
draw(ax1, tri_a, "")
fig.text(0.02, 0.975, "(a) selecting an annotation highlights its faces",
         fontsize=FS + 1.0, va="top")

val, lo, hi_b = A(anno, "pmi:value"), A(anno, "pmi:lowerBound"), A(anno, "pmi:upperBound")
meas = [r["measured"] for r in rows]
lo_b, up_b = rows[0]["band_lo"], rows[0]["band_hi"]
verdicts = {r["verdict"] for r in rows}
tie = any(r.get("cause") == "at_limit" for r in rows)
vtext = ("inside the band" if verdicts == {"in"} else "outside on some faces")
if tie:
    vtext += ", at a limit"
tgt = f"{len(targets)} brepFace subsets"
if _one_body and len(_tv) == 2:
    tgt += " (one bore)"
inspector(
    fig.add_subplot(gs[1, 0]),
    f"selected  {anno.GetPath().name}",
    [("pmi:type", A(anno, "pmi:type")),
     ("pmi:dimName", str(A(anno, "pmi:dimName"))),
     ("pmi:value", f"{val:g} {lo:+g}/{hi_b:+g}   [{A(anno,'pmi:sourceUnit')}]"),
     ("pmi:appliesTo", tgt),
     ("", "resolved from the delivered stage alone (Sect. 6.4)"),
     ("fitted size", f"{min(meas):.6f} mm  (both faces)"),
     ("tolerance band", f"{lo_b:g} … {up_b:g} mm"),
     ("verdict", vtext)],
    "No source CAD is consulted. Excursions below the declared\n"
    "1e-05 mm tie tolerance are counted as inside.",
    WARM)

# ---------- (b) ----------
ax2 = fig.add_subplot(gs[0, 1], projection="3d")
_pv = V[idx[subsets[probe]]].reshape(-1, 3)
_c = _pv.mean(axis=0); _r = max(np.abs(_pv - _c).max() * 3.2, EXT.max() * 0.10)
draw(ax2, subsets[probe], "", zoom=(_c, _r), hl=GREEN)
fig.text(0.515, 0.975, "(b) selecting a face lists what governs it (zoomed)",
         fontsize=FS + 1.0, va="top")

def _line(p):
    t = A(p, "pmi:type")
    if A(p, "pmi:value") is not None:
        v = f"{A(p,'pmi:value'):g}"
        return t, v + (f"  ({A(p,'pmi:dimName')})" if A(p, "pmi:dimName") else "")
    if A(p, "pmi:datumLetter"):
        return t, f"datum [{A(p,'pmi:datumLetter')}]"
    if A(p, "pmi:dimName"):
        return t, f"({A(p,'pmi:dimName')}), no source value"
    return t, str(A(p, "pmi:stepId"))
inspector(
    fig.add_subplot(gs[1, 1]),
    f"selected  {probe.split('/')[-1]}",
    [("family", "brepFace"),
     ("pmi:surfaceType", str(A(stage.GetPrimAtPath(probe), "pmi:surfaceType"))),
     ("", f"governed by {len(governing)} annotations, via the inverse relationship")]
    + [_line(p) for p in governing[:4]],
    "The third entry carries no value entity in the source,\n"
    "and is reported as such rather than silently omitted.",
    BLUE, vx=0.42)

fig.patch.set_alpha(1.0)
for ext in ("png", "tiff", "eps"):
    fig.savefig(f"figures/fig8_selection.{ext}", dpi=600)
print(f"[35] fig8 written | anno={A(anno,'pmi:stepId')} targets={len(targets)} "
      f"probe={probe.split('/')[-1]} governing={len(governing)} measured={meas}")
