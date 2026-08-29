# Graphical Abstract 生成（用于 TOC/摘要展示；故意不含任何结果数字——期刊要求不剧透结果）
# 构图：CAD(AP242 语义 PMI) → [今日的交付：几何到达、语义与关联断链] vs [本文的载体 profile：语义与关联随几何到达]
#      → 下游 design/manufacturing 消费者（检验计量・机器人・设计评审）
# 风格沿用 scripts/27_figures_v2.py（Helvetica 9pt / 同色板 / 300dpi）
# 用法: .venv/bin/python scripts/33_graphical_abstract.py
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

os.chdir(os.path.join(os.path.dirname(__file__), ".."))
os.makedirs("figures", exist_ok=True)
# 字号：本刊 8–12 pt；GA 还会被缩成 TOC 缩略图，故按双栏满宽 174 mm 作图并把最小字号抬到 8.5 pt
plt.rcParams.update({"font.size": 9, "figure.dpi": 300, "savefig.bbox": None,
                     "font.family": "Helvetica", "ps.fonttype": 42, "pdf.fonttype": 42})
# 无障碍：GA 的两条路径此前是红/绿——色觉差异下最不安全的一对。绿改为偏青的深绿
# （与正文 W 的绿同族但离橙更远），并让两条箭头一虚一实，不只靠颜色区分。
BLUE, GRAY, WARM, GREEN = "#2b5f9e", "#8a8f98", "#c4552d", "#1b6b5a"


def box(ax, x, y, w, h, title, sub=None, fc="#eef2f7", ec=BLUE, fs=9.8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.015", fc=fc, ec=ec, lw=1.2))
    ax.text(x + w / 2, y + h - 0.20 if sub else y + h / 2, title, ha="center",
            va="center", fontsize=fs, fontweight="bold", color="#1a1a1a")
    if sub:
        ax.text(x + w / 2, y + h / 2 - 0.075, sub, ha="center", va="center",
                fontsize=max(fs - 1.2, 8.0), color="#3a3a3a", linespacing=1.45)


def arrow(ax, x1, y1, x2, y2, color=BLUE, style="-", lw=1.6):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=13,
                                 color=color, lw=lw, linestyle=style,
                                 shrinkA=2, shrinkB=2))


fig, ax = plt.subplots(figsize=(6.85, 3.25), layout="constrained")
ax.set_xlim(0, 10.2); ax.set_ylim(0, 4.1); ax.axis("off")

# 左：源
box(ax, 0.05, 1.30, 1.85, 1.45, "CAD source", "STEP AP242\ngeometry +\nsemantic PMI",
    fc="#f2f5f9", ec=GRAY)

# 上路：今日的交付
box(ax, 2.55, 2.42, 3.15, 1.42, "Today's delivery to USD",
    "geometry arrives\ntolerances, datums and the\nlink to the face do not", fc="#fbf0ec", ec=WARM)
arrow(ax, 1.90, 2.28, 2.55, 3.02, color=WARM)
ax.text(2.02, 3.12, "convert", fontsize=8.5, color=WARM, ha="center")

# 下路：本文
box(ax, 2.55, 0.22, 3.15, 1.42, "This paper: carrier profile",
    "per-face subsets, typed PMI,\nnative association —\nUSD mechanisms only", fc="#e9f2ef", ec=GREEN)
arrow(ax, 1.90, 1.78, 2.55, 1.02, color=GREEN)
ax.text(2.02, 0.78, "convert", fontsize=8.5, color=GREEN, ha="center")

# 右：下游消费者
box(ax, 6.02, 1.24, 4.14, 1.57, "Downstream design and manufacturing",
    "inspection and metrology planning\nrobotic handling and assembly\ninteractive design review",
    fc="#eef2f7", ec=BLUE, fs=8.8)

arrow(ax, 5.70, 3.02, 6.80, 2.86, color=WARM, style=(0, (3, 2)), lw=1.3)
ax.text(5.88, 3.16, "no tolerance link", fontsize=8.5, color=WARM)
arrow(ax, 5.70, 1.02, 6.80, 1.22, color=GREEN, lw=1.9)
ax.text(5.80, 0.70, "feature-to-tolerance link preserved", fontsize=8.5, color=GREEN)

# 底部一句话（不含任何结果数字）
ax.text(5.1, -0.13, "A standards-only convention, stated as conformance conditions any converter can be checked against",
        ha="center", va="center", fontsize=9.0, color="#1a1a1a", style="italic")

fig.patch.set_alpha(1.0)
for ext, dpi in (("png", 300), ("tiff", 600), ("eps", 600)):
    fig.savefig(f"figures/graphical_abstract.{ext}", dpi=dpi)
plt.close(fig)
print("[33] figures/graphical_abstract.{png,tiff} written")
