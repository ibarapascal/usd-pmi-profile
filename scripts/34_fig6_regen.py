# fig6 重生成（2026-08-29）：此前是 v1 存档栅格件原样复用，像素量固定在 1358×763@300dpi，
# 达不到 combination art 600 dpi 的出版要求。本脚本用 v1 归档的同一批数据与同一逻辑重跑
# 逐点邻近查询，输出 png/tiff/eps 三件（散点 rasterized，保证 EPS 不爆体积）。
# 逻辑来源：v1 归档的 figures/fig_scripts.py 的 fig2()，数值口径不变（同数据、同随机种子 7、同 50k 子样、同 2 mm 阈值）。
# 用法: .venv/bin/python scripts/34_fig6_regen.py     （耗时以邻近查询为主，数分钟量级）
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

os.chdir(os.path.join(os.path.dirname(__file__), ".."))
# 单栏 85 mm 作图＋字号 ≥8 pt（本刊硬要求）；栅格 600 dpi 在该尺寸上即为最终尺寸下的 600 dpi
plt.rcParams.update({"font.size": 8.5, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 600, "savefig.bbox": None, "font.family": "Helvetica",
                     "ps.fonttype": 42, "pdf.fonttype": 42,
                     "axes.labelsize": 8.5, "xtick.labelsize": 8.0, "ytick.labelsize": 8.0})
WARM = "#c4552d"
PILOT = os.environ.get("V1_ARCHIVE", "archive/v1-pilot") + "/pilot"
BASE = "nist_ctc_02_asme1_ap242-e2"

import trimesh
from pxr import Usd, UsdGeom
from trimesh.proximity import ProximityQuery

cv = np.loadtxt(f"{PILOT}/out/batch_v3/chainA_{BASE}.convverts.xyz")
stage = Usd.Stage.Open(f"{PILOT}/out/batch_v3/{BASE}.chainA.usdc")
all_f, off = [], 0
for prim in stage.Traverse(Usd.TraverseInstanceProxies()):
    if prim.IsA(UsdGeom.Mesh):
        m = UsdGeom.Mesh(prim)
        counts = np.array(m.GetFaceVertexCountsAttr().Get())
        idx = np.array(m.GetFaceVertexIndicesAttr().Get())
        faces, cur = [], 0
        for c in counts:
            for j in range(1, c - 1):
                faces.append([idx[cur], idx[cur + j], idx[cur + j + 1]])
            cur += c
        all_f.append(np.array(faces) + off)
        off += int(idx.max()) + 1
conv = trimesh.Trimesh(cv, np.vstack(all_f), process=False)

gt = np.loadtxt(f"{PILOT}/out/batch_v2/{BASE}.gtv2.xyz")
sub = gt[np.random.default_rng(7).choice(len(gt), 50000, replace=False)]
CACHE = f".cache/fig6_{BASE}.npz"          # 邻近查询要数分钟；只调版式时不必重算
os.makedirs(".cache", exist_ok=True)
if os.path.exists(CACHE):
    z = np.load(CACHE); sub, d = z["sub"], z["d"]
    print("[34] using cached proximity result", CACHE)
else:
    print("[34] running proximity query on 50,000 points ...")
    d = ProximityQuery(conv).on_surface(sub)[1]
    np.savez_compressed(CACHE, sub=sub, d=d)

# 🔴 版式：这是空间图，85 mm 单栏下画幅只有 ~55×20 mm，点密度不可读 → 174 mm 双栏。
# 🔴 色标：全体偏差的 p90 = 0.11 mm、p99 = 0.23 mm，原来的 vmin/vmax = 0/2 让 98% 的点
#    落在色标最淡的一端（白底上几乎不可见，对比度远低于本刊 4.5:1）。改为 0–0.25 饱和
#    （colorbar extend="max"）＋截断 Blues 的浅色端，使最淡的点仍是可见的中蓝。
CMAP = LinearSegmentedColormap.from_list("Blues_t", plt.get_cmap("Blues")(np.linspace(0.32, 1.0, 256)))
VMAX = 0.25
fig, ax = plt.subplots(figsize=(6.85, 2.45), layout="constrained")
near = d <= 2.0
ax.scatter(sub[near, 1], sub[near, 2], c=d[near], cmap=CMAP, s=2, vmin=0, vmax=VMAX,
           rasterized=True)
ax.scatter(sub[~near, 1], sub[~near, 2], color=WARM, s=16, marker="^", rasterized=True,
           label=f"dev. > 2 mm (n={int((~near).sum())})")
sm = plt.cm.ScalarMappable(cmap=CMAP, norm=plt.Normalize(0, VMAX))
cb = fig.colorbar(sm, ax=ax, shrink=0.62, aspect=14, pad=0.02, extend="max",
                  label="distance to mesh (mm)")
cb.set_ticks([0, 0.05, 0.10, 0.15, 0.20, 0.25])
ax.set_xlabel("y (mm)")
ax.set_ylabel("z (mm)")
ax.set_aspect("equal")
ax.legend(loc="upper left", frameon=False, fontsize=8, handletextpad=0.3, borderpad=0.1)
fig.patch.set_alpha(1.0)
for ext in ("png", "tiff", "eps"):
    fig.savefig(f"figures/fig6_spatial.{ext}", dpi=600)
print("[34] fig6 regenerated; far points:", int((~near).sum()))
