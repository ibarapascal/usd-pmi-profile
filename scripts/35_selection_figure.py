# Fig 8：选择往返（selection round-trip）——交互式评审环境在 profile 化场景上实际能做的动作，画成静态图。
# 双向都画，因为评审工具两边都用：
#   (a) 选中一条公差标注 → 高亮它管辖的面，并读出 typed 字段（值/带/单位/语义）
#   (b) 选中一张面     → 列出所有管辖它的标注
# ⚠️ 口径：全部信息取自交付的 USD 场景（pmi:type / value / bounds / sourceUnit / dimName /
#    appliesTo / brepFace subset），**不查 STEP 源**。这是 CF1–CF3 读取路径的可视化，
#    不是我们实现了一个交互工具——本图是该路径的一次静态取样。
# 用法: .venv/bin/python scripts/35_selection_figure.py [model_stem]
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from pxr import Usd, UsdGeom

os.chdir(os.path.join(os.path.dirname(__file__), ".."))
plt.rcParams.update({"font.size": 8.5, "figure.dpi": 300, "savefig.bbox": "tight",
                     "font.family": "Helvetica"})
BLUE, WARM, GRAY, GREEN = "#2b5f9e", "#c4552d", "#c9ced6", "#3a7d44"
STEM = sys.argv[1] if len(sys.argv) > 1 else "nist_ctc_01_asme1_ap242-e1"

stage = Usd.Stage.Open(f"out/proto_v2/{STEM}.usdc")
mesh = next(p for p in stage.Traverse() if p.IsA(UsdGeom.Mesh))
m = UsdGeom.Mesh(mesh)
V = np.array(m.GetPointsAttr().Get())
idx = np.array(m.GetFaceVertexIndicesAttr().Get()).reshape(-1, 3)

subsets = {}                       # face_index -> 三角形索引
for p in stage.Traverse():
    if p.IsA(UsdGeom.Subset) and UsdGeom.Subset(p).GetFamilyNameAttr().Get() == "brepFace":
        subsets[p.GetPath().pathString] = np.array(UsdGeom.Subset(p).GetIndicesAttr().Get())

def A(p, n):
    a = p.GetAttribute(n)
    return a.Get() if a else None

annos = [p for p in stage.Traverse() if A(p, "pmi:type")]

# --- (a) 选一条带双侧带的直径标注 ---
sel = None
for p in annos:
    rel = p.GetRelationship("pmi:appliesTo")
    if (A(p, "pmi:type") == "DIMENSIONAL_SIZE" and A(p, "pmi:dimName") == "diameter"
            and A(p, "pmi:value") is not None and A(p, "pmi:lowerBound") is not None
            and rel and rel.GetTargets()):
        sel = (p, [str(t) for t in rel.GetTargets()])
        break
assert sel, "该模型没有满足条件的标注"
anno, targets = sel

# --- (b) 反向：取其中一张面，找出所有管辖它的标注 ---
probe = targets[0]
governing = []
for p in annos:
    rel = p.GetRelationship("pmi:appliesTo")
    if rel and probe in [str(t) for t in rel.GetTargets()]:
        governing.append(p)

fig = plt.figure(figsize=(7.6, 2.75))
lim = [(V[:, i].min(), V[:, i].max()) for i in range(3)]
span = max(h - l for l, h in lim) / 2
ctr = [(l + h) / 2 for l, h in lim]

EXT = np.array([h - l for l, h in lim])

def draw(ax, hi_tris, title, zoom=None, hl=WARM):
    hi = set(hi_tris.tolist())
    base = np.array([t for i, t in enumerate(idx) if i not in hi])
    ax.add_collection3d(Poly3DCollection(V[base], facecolor=GRAY, edgecolor="none",
                                         alpha=0.22, rasterized=True))
    ax.add_collection3d(Poly3DCollection(V[idx[list(hi)]], facecolor=hl, edgecolor=hl,
                                         linewidth=0.25, rasterized=True))
    if zoom is None:                      # 全局：按真实比例填满，不用立方体（零件是扁长的）
        for i, s in enumerate("xyz"):
            getattr(ax, f"set_{s}lim")(ctr[i] - EXT[i] / 2 * 1.02, ctr[i] + EXT[i] / 2 * 1.02)
        ax.set_box_aspect(tuple(EXT / EXT.max()))
    else:                                 # 局部：以选中面为中心等比放大
        c, r = zoom
        for i, s in enumerate("xyz"):
            getattr(ax, f"set_{s}lim")(c[i] - r, c[i] + r)
        ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=24, azim=-58); ax.set_axis_off()
    ax.set_title(title, fontsize=8.5, pad=-6)

ax1 = fig.add_subplot(121, projection="3d")
tri_a = np.concatenate([subsets[t] for t in targets if t in subsets])
draw(ax1, tri_a, "(a) selecting the annotation lights up the faces it governs")
val, lo, hi_b = A(anno, "pmi:value"), A(anno, "pmi:lowerBound"), A(anno, "pmi:upperBound")
ax1.text2D(0.02, 0.05,
           f"{A(anno,'pmi:type')}  ({A(anno,'pmi:dimName')})\n"
           f"{val:g} {lo:+g}/{hi_b:+g}  (stage units; source {A(anno,'pmi:sourceUnit')})\n"
           f"applies to {len(targets)} face subset(s)",
           transform=ax1.transAxes, fontsize=7.2, va="bottom",
           bbox=dict(boxstyle="round,pad=0.32", fc="#fbf0ec", ec=WARM, lw=0.9))

ax2 = fig.add_subplot(122, projection="3d")
_pv = V[idx[subsets[probe]]].reshape(-1, 3)
_c = _pv.mean(axis=0); _r = max(np.abs(_pv - _c).max() * 3.2, EXT.max() * 0.10)
draw(ax2, subsets[probe], "(b) selecting one face reveals what governs it", zoom=(_c, _r), hl=GREEN)
def _line(p):
    t = A(p, "pmi:type")
    if A(p, "pmi:value") is not None:
        t += f"  {A(p,'pmi:value'):g}"
        if A(p, "pmi:dimName"):
            t += f" ({A(p,'pmi:dimName')})"
    elif A(p, "pmi:datumLetter"):
        t += f"  datum [{A(p,'pmi:datumLetter')}]"
    else:                                  # 无数值者显示源实体号，避免出现空行
        t += f"  {A(p,'pmi:stepId')}"
    return t
lines = [_line(p) for p in governing[:4]]
ax2.text2D(0.02, 0.05, f"{probe.split('/')[-1]} is governed by {len(governing)} annotation(s):\n"
           + "\n".join("  · " + l for l in lines),
           transform=ax2.transAxes, fontsize=7.2, va="bottom",
           bbox=dict(boxstyle="round,pad=0.32", fc="#eef2f7", ec=BLUE, lw=0.9))

fig.subplots_adjust(wspace=0.0, left=0.01, right=0.99, top=1.02, bottom=0.02)
fig.patch.set_alpha(1.0)
for ext in ("png", "tiff", "eps"):
    fig.savefig(f"figures/fig8_selection.{ext}", dpi=600)
print(f"[35] fig8 written | anno={A(anno,'pmi:stepId')} targets={len(targets)} "
      f"probe={probe.split('/')[-1]} governing={len(governing)}")
