# v2 论文图生成（英文投稿版，7 张 → figures/）
# fig1 PMI concept (semantic vs graphical, schematic)     fig2 protocol overview (schematic)
# fig3 profile structure (schematic)                       fig4 semantic inventory (per-model, lose-all vs keep-all)
# fig5 deviation vs triangle budget (STC-06, archived scan data)
# fig6 spatial localization case (v1 archived artifact copied verbatim — regeneration needs heavy proximity query)
# fig7 downstream hole task: five regimes (measurable% + error distributions)
# 数据源：out/e1/canonical_numbers.json、out/hole/*.json、out/e2_audit/*.hole.json、archive pilot 扫描件
# 用法: .venv/bin/python scripts/27_figures_v2.py [1-7|all]
import glob
import json
import os
import shutil
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

os.chdir(os.path.join(os.path.dirname(__file__), ".."))
os.makedirs("figures", exist_ok=True)
# 🔴 字号硬约束（IJIDeM 明文）：图内无衬线 8–12 pt。达成方式＝**按最终排版尺寸作图**，
#    使排版时不发生缩放：WIDE=174 mm（双栏满宽）/ NARROW=85 mm（单栏）。
#    任何 <8 pt 的显式 fontsize 都是缺陷；`scripts/38_figure_check.py` 会解 EPS 逐图判定。
WIDE, NARROW = 6.85, 3.35          # inches：174 mm / 85 mm
FS_MIN, FS_BODY, FS_TITLE = 8.0, 8.0, 9.5
plt.rcParams.update({"font.size": FS_BODY, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 300, "savefig.bbox": None, "font.family": "Helvetica",
                     "ps.fonttype": 42, "pdf.fonttype": 42,
                     "axes.labelsize": 8.5, "xtick.labelsize": 8.0, "ytick.labelsize": 8.0,
                     "legend.fontsize": 8.0})
BLUE, GRAY, WARM, GREEN, PURPLE = "#2b5f9e", "#8a8f98", "#c4552d", "#3a7d44", "#6a4c93"
# 无障碍（本刊明文「用图案而非纯色区分」）：每条 pipeline 一色一图案，灰度打印与色觉差异下仍可分。
HATCH = {"P1": "///", "P2": "\\\\\\", "P3": "xxx", "W": ""}
K = json.load(open("out/e1/canonical_numbers.json"))


def save_all(fig, stem):
    """png（阅读用）＋ tiff（栅格备份）＋ eps（投稿交付：矢量优先，含嵌入字体）。
    EPS 不支持 alpha，故显式给白底，避免透明区域在 EPS 里变黑。"""
    fig.patch.set_alpha(1.0)
    fig.savefig(f"figures/{stem}.png")
    fig.savefig(f"figures/{stem}.tiff")
    fig.savefig(f"figures/{stem}.eps", format="eps")

def box(ax, x, y, w, h, text, fc="#eef2f7", ec=BLUE, fs=FS_BODY, weight="normal"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fc=fc, ec=ec, lw=1.1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, weight=weight)

def arrow(ax, x1, y1, x2, y2, color=GRAY, style="-|>", lw=1.2, ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, color=color,
                                 lw=lw, linestyle=ls, mutation_scale=12))

def fig1():
    fig, (a, b) = plt.subplots(1, 2, figsize=(WIDE, 3.5), layout="constrained")
    for ax in (a, b):
        ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
    a.set_title("(a) Semantic PMI: typed entity graph", fontsize=FS_TITLE, loc="left")
    box(a, 2.6, 8.2, 5.2, 1.3, "DIMENSIONAL_SIZE\n'diameter'", fs=FS_BODY)
    box(a, 0.3, 5.4, 4.2, 1.3, "value = 3.5 mm\nPLUS_MINUS ±0.1", fc="#eaf3ea", ec=GREEN, fs=FS_BODY)
    box(a, 5.5, 5.4, 4.2, 1.3, "GISU / IIRU\nassociation", fs=FS_BODY)
    box(a, 5.5, 2.4, 4.2, 1.3, "ADVANCED_FACE\n(cylindrical)", fc="#f4ede2", ec=WARM, fs=FS_BODY)
    box(a, 0.3, 2.4, 4.2, 1.3, "DATUM_SYSTEM\n[A / B / C]", fs=FS_BODY)
    arrow(a, 4.0, 8.2, 2.4, 6.7); arrow(a, 6.4, 8.2, 7.6, 6.7)
    arrow(a, 7.6, 5.4, 7.6, 3.7); arrow(a, 1.4, 5.4, 1.8, 3.7)
    a.text(0.3, 0.6, "machine-readable: values, tolerances, datums,\nand face references are typed entities",
           fontsize=FS_BODY, style="italic")
    b.set_title("(b) Graphical PMI: presentation polylines", fontsize=FS_TITLE, loc="left")
    b.add_patch(plt.Rectangle((1.2, 3.2), 6.0, 4.2, fc="none", ec=GRAY, lw=1.0))
    b.add_patch(plt.Circle((4.2, 5.3), 1.15, fc="none", ec=GRAY, lw=1.0))
    b.plot([4.9, 6.6], [6.2, 8.2], color=GRAY, lw=0.9)
    b.text(6.5, 8.4, "⌀ 3.5 ± 0.1", fontsize=9, family="monospace")
    b.text(6.5, 7.5, "(stroked curves)", fontsize=FS_BODY, color=GRAY)
    b.text(1.2, 1.2, "human-readable only: the same callout rendered as\nunstructured curve geometry — no queryable value",
           fontsize=FS_BODY, style="italic")
    save_all(fig, "fig1_pmi_concept")
    print("fig1 done")

def fig2():
    fig, ax = plt.subplots(figsize=(WIDE, 4.3), layout="constrained")
    ax.set_xlim(0, 14); ax.set_ylim(0, 10); ax.axis("off")
    box(ax, 0.2, 3.6, 2.6, 2.6, "NIST MBE PMI\ntest set\n17 AP242 inputs\n(16 B-rep + 1 tess.)",
        fc="#f4ede2", ec=WARM, fs=FS_BODY)
    labels = [("P1  STEP-FreeCAD-OBJ-Blender-USD", 8.3),
              ("P2  Omniverse hoops_core converter", 6.5),
              ("P3  Mayo-glTF-guc", 4.7),
              ("W   profile writer (this paper)", 2.9)]
    for t, y in labels:
        fc = "#eaf0e6" if t.startswith("W") else "#eef2f7"
        ec = GREEN if t.startswith("W") else BLUE
        box(ax, 3.3, y - 0.65, 5.85, 1.3, t, fc=fc, ec=ec, fs=FS_BODY)
        arrow(ax, 2.8, 4.9, 3.3, y)
    box(ax, 9.35, 6.9, 4.6, 2.4, "Semantic audit\ninventory diff · typed round-trip\nassociation validity", fs=FS_BODY)
    box(ax, 9.35, 3.9, 4.6, 2.4, "Geometric audit\narea-uniform sampling\nregistration · BVH distance", fs=FS_BODY)
    box(ax, 9.35, 0.9, 4.6, 2.4, "Downstream task\nhole-diameter recovery\nseven information regimes", fs=FS_BODY)
    for y in (8.3, 6.5, 4.7, 2.9):
        for ty in (8.1, 5.1, 2.1):
            arrow(ax, 9.15, y, 9.35, ty, lw=0.7)
    ax.text(0.2, 0.4, "Audit tooling predates the writer and has no privileged interface to any pipeline.",
            fontsize=FS_BODY, style="italic")
    save_all(fig, "fig2_protocol")
    print("fig2 done")

def fig3():
    fig, ax = plt.subplots(figsize=(WIDE, 4.5), layout="constrained")
    ax.set_xlim(0, 14); ax.set_ylim(0, 10); ax.axis("off")
    ax.set_title("STEP entities (left) mapped to USD prims under the profile (right)", fontsize=FS_TITLE, loc="left")
    box(ax, 0.2, 7.2, 4.6, 1.4, "#412 DIMENSIONAL_SIZE\nvalue 3.5, ±0.1 (PLUS_MINUS)", fc="#f4ede2", ec=WARM, fs=FS_BODY)
    box(ax, 0.2, 4.6, 4.6, 1.4, "#231 ADVANCED_FACE\n(via GISU / shape aspect chain)", fc="#f4ede2", ec=WARM, fs=FS_BODY)
    box(ax, 0.2, 2.0, 4.6, 1.4, "#88 DATUM 'A'", fc="#f4ede2", ec=WARM, fs=FS_BODY)
    box(ax, 7.2, 8.3, 6.4, 1.2, "/Part  (UsdGeomMesh, per-face tessellation;\nmetersPerUnit per source declaration)", fs=FS_BODY)
    box(ax, 8.0, 6.3, 5.6, 1.4, "GeomSubset 'brepFace_231'\nfamilyName = brepFace\npmi:surfaceType = \"Cylinder\"", fc="#eaf0e6", ec=GREEN, fs=FS_BODY)
    box(ax, 8.0, 3.7, 5.6, 1.9, "/Part/PMI/anno_412\npmi:type/value/lowerBound/upperBound\npmi:stepId · verbatim record\nrel pmi:appliesTo: brepFace_231", fc="#eaf0e6", ec=GREEN, fs=FS_BODY)
    box(ax, 8.0, 1.4, 5.6, 1.4, "/Part/PMI/anno_88\npmi:type=\"datum\", pmi:datumLetter=\"A\"", fc="#eaf0e6", ec=GREEN, fs=FS_BODY)
    arrow(ax, 4.8, 7.9, 8.0, 4.9, color=PURPLE)
    arrow(ax, 4.8, 5.3, 8.0, 7.0, color=PURPLE)
    arrow(ax, 4.8, 2.7, 8.0, 2.1, color=PURPLE)
    arrow(ax, 10.8, 5.6, 10.8, 6.3, color=GREEN, ls="--")
    ax.text(11.0, 5.75, "relationship", fontsize=FS_BODY, color=GREEN)
    ax.text(5.2, 0.5, "fingerprint alignment maps STEP face ids to mesh face indices (Sec. 5.3)",
            fontsize=FS_BODY, style="italic", color=PURPLE)
    save_all(fig, "fig3_profile")
    print("fig3 done")

def fig4():
    # 锚定四分层堆叠（实证账②）：face/edge/part/none per model；DATUM（无锚定语义）单独浅色段
    rows = []
    for gj in sorted(glob.glob("out/e1/*ap242*.graph.json")):
        b = os.path.basename(gj).replace(".graph.json", "")
        if "e1-tg" in b:
            continue
        g = json.load(open(gj))
        cnt = {"face": 0, "edge": 0, "part": 0, "none": 0, "datum": 0}
        for a in g["annotations"]:
            k = a.get("anchorKind")
            cnt[k if k in cnt else "datum"] += 1
        rows.append((b.replace("nist_", "").replace("_asme1_ap242", ""), cnt))
    fig, ax = plt.subplots(figsize=(WIDE, 5.0), layout="constrained")
    names = [r[0] for r in rows]
    y = np.arange(len(rows))
    # 无障碍：灰度下 green/warm 与 blue/purple 会并到一起，故段也用图案区分（本刊明文要求）
    segs = [("face", GREEN, "", "face-anchored (690)"), ("edge", BLUE, "//", "edge-anchored (21)"),
            ("part", PURPLE, "xx", "whole-part (2)"),
            ("none", WARM, "\\\\", "no machine-readable link in source (11)"),
            ("datum", "#d9dde3", "", "DATUM (identity only, 114)")]
    left = np.zeros(len(rows))
    for key, color, hat, label in segs:
        vals = np.array([r[1][key] for r in rows])
        ax.barh(y, vals, left=left, height=0.62, color=color, label=label,
                hatch=hat, edgecolor="white", linewidth=0.4)
        left += vals
    for yy, tot in zip(y, left):
        ax.annotate(str(int(tot)), (tot, yy), xytext=(3, 0), textcoords="offset points",
                    va="center", fontsize=FS_BODY)
    ax.set_yticks(y, names, fontsize=FS_BODY)
    ax.invert_yaxis()
    ax.set_xlabel("Top-level semantic PMI annotations (anchoring stratification)")
    # 🔴 本刊明文：图注写在正文文件里，不得嵌进图片。原来这里嵌了两句完整说明文字，
    #    与正文图注重复且形同「图内 caption」——删除，说明全部由正文图注承担。
    ax.legend(fontsize=FS_BODY, loc="upper center", bbox_to_anchor=(0.5, -0.11), ncol=2, framealpha=0.95)
    save_all(fig, "fig4_inventory")
    print("fig4 done", int(left.sum()))

def fig5():
    ARC = os.environ.get("V1_ARCHIVE", "archive/v1-pilot") + "/pilot"
    rows = []
    for d in ["0.05", "0.1", "0.5"]:
        r = json.load(open(f"{ARC}/out/batch_v2/stc06_d{d}.v2report.json"))["B_gt_to_conv"]
        tris = {"0.05": 18546, "0.1": 12376, "0.5": 7110}[d]
        rows.append((tris, r))
    omni = json.load(open(f"{ARC}/out/batch_v2/omni_nist_stc_06_asme1_ap242-e3.v2report.json"))["B_gt_to_conv"]
    fig, ax = plt.subplots(figsize=(NARROW, 2.95), layout="constrained")
    x = [r[0] for r in rows]
    for key, marker, al in [("mean", "o", 1.0), ("p99", "s", 0.7), ("max", "^", 0.45)]:
        ax.plot(x, [r[1][key] for r in rows], marker=marker, color=BLUE, lw=1.5, ms=5, alpha=al)
        ax.annotate(key, (x[-1], rows[-1][1][key]), xytext=(6, 0), textcoords="offset points",
                    va="center", color=BLUE, fontsize=FS_BODY)
        ax.scatter([5951], [omni[key]], marker="D", s=26, color=WARM, zorder=5)
        # 图必须自足：三个菱形分别是哪一个统计量，此前只有图注外的正文才说得清
        ax.annotate(key, (5951, omni[key]), xytext=(-5, 0), textcoords="offset points",
                    ha="right", va="center", color=WARM, fontsize=FS_BODY)
    ax.annotate("Omniverse\n(default)", (5951, omni["mean"]), xytext=(0, -26),
                textcoords="offset points", ha="center", color=WARM, fontsize=FS_BODY)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Triangle count (STC-06)"); ax.set_ylabel("Direction-B deviation (mm)")
    ax.grid(True, which="both", lw=0.3, alpha=0.3)
    save_all(fig, "fig5_budget")
    print("fig5 done")

def fig6():
    # fig6 已改为真重生成（分辨率需达刊要求）→ 见 34_fig6_regen.py；此处不再复用存档栅格件。
    print("fig6: run 34_fig6_regen.py (regenerates at 600 dpi from the archived v1 data)")

def fig7():
    """(a) 可测率：**按消费者可用信息分块**——参考臂（用源侧信息）与 asset-only 消费者分开，
    因为把 D/D2 排除在图外会让读者以为 W 的 100% 没有对手（2026-08-29 第三轮 review 查出）。
    (b) 误差分布：加入 D2/P3，让「几何可恢复但尾巴不可标记」直接可见。
    无障碍：pipeline 用颜色＋图案双重编码；柱上不再逐个贴 P1/P2/P3/W（会相撞），改用图例。"""
    colors = {"P1": GRAY, "P2": WARM, "P3": PURPLE, "W": GREEN}
    # 刻度只放 regime 代号，描述放 xlabel——两行长标签在单柱组间必然相撞（第三轮 review 实测）
    REF = [("A", "A_vertex_all", ["P1", "P2", "P3", "W"]),
           ("B", "B_surface", ["P1", "P2", "P3", "W"]),
           ("C", "C_subset", ["W"]),
           ("C2", "C2_selfcontained", ["W"])]
    ASSET = [("C3", "C3_asset_only", ["W"]),
             ("D", "e9", ["P1", "P2", "P3"]),
             ("D2", "e9b", ["P1", "P2", "P3"])]
    SRC = {"P1": "chainA", "P2": "omni", "P3": "mayo"}

    def pct_of(key, name):
        if key == "e9":
            return K[f"e9.{SRC[name]}.pct"]
        if key == "e9b":
            return K[f"e9b.{SRC[name]}.pct"]
        if key == "C3_asset_only":
            return K["e4.proto.C3_asset_only.match_pct"]
        if name == "P3":
            return K[f"e2.hole.{'A' if key == 'A_vertex_all' else 'B'}.pct"]
        pl = {"P1": "chainA", "P2": "omni", "W": "proto"}[name]
        return K[f"e4.{pl}.{key}.pct"]

    fig, (a, b) = plt.subplots(1, 2, figsize=(WIDE, 4.1), gridspec_kw={"width_ratios": [1.35, 1]}, layout="constrained")
    xpos, xt, xl = 0.0, [], []
    seen = set()
    for block, oracle in ((REF, False), (ASSET, True)):
        if oracle:
            div = xpos - 1.5
            a.axvline(div, color=GRAY, lw=0.8, ls=(0, (4, 3)), ymax=0.93)
        for label, key, names in block:
            first = xpos
            for name in names:
                v = pct_of(key, name)
                a.bar(xpos, v, width=0.8, color=colors[name],
                      hatch=HATCH[name], edgecolor="white", linewidth=0.6,
                      label=name if name not in seen else None)
                if v < 3.0:                     # 近零柱看不见，会被读成「没画」——写出数值＋引导线
                    nz = sum(1 for n2 in names[:names.index(name)] if pct_of(key, n2) < 3.0)
                    a.annotate(f"{name} {v:g}%", (xpos, v), xytext=(-3, 3 + 12 * nz),
                               textcoords="offset points", ha="right", va="bottom",
                               fontsize=FS_BODY, color="#222",
                               arrowprops=dict(arrowstyle="-", lw=0.6, color=colors[name],
                                               shrinkA=0.5, shrinkB=0.5))
                seen.add(name)
                xpos += 1
            xt.append((first + xpos - 1) / 2); xl.append(label)
            xpos += 1.9
        xpos += 0.9
    a.set_xticks(xt, xl)
    a.set_xlabel("A per-vertex · B surface sampling · C nominal axis · C2 self-fit\n"
                 "C3 asset-only · D RANSAC · D2 per-prim  (D and D2 oracle-scored)")
    a.set_xlim(-1.1, xpos - 3.0)
    a.set_ylim(0, 124)
    a.set_yticks([0, 20, 40, 60, 80, 100])
    a.axhline(100, color=GRAY, lw=0.5, ls=":")
    a.set_ylabel("Measurable cylinders (%)")
    a.set_title("(a) Measurability by regime (n = 1,866)", fontsize=FS_TITLE, loc="left")
    a.text((xt[0] + xt[3]) / 2, 104, "reference arms\n(use source-side information)", ha="center",
           va="bottom", fontsize=FS_BODY, style="italic", color="#444", linespacing=1.25)
    a.text((xt[4] + xt[6]) / 2, 104, "asset-only\nconsumer", ha="center",
           va="bottom", fontsize=FS_BODY, style="italic", color="#444", linespacing=1.25)
    a.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.22), frameon=False,
             handlelength=1.6, columnspacing=1.4, fontsize=FS_BODY)

    # (b) 误差分布
    def perhole(files, key, sub=None):
        out = []
        for f in files:
            d = json.load(open(f))
            for h in d.get("per_hole", []):
                r = h.get(key)
                if not r or r.get("abs_err") is None:
                    continue
                if sub is None and r.get("n", 0) < 8:
                    continue
                out.append(max(r["abs_err"], 1e-9))
        return out
    dists, dl, dc, dh = [], [], [], []

    def add(vals, lab, name):
        dists.append(vals); dl.append(lab); dc.append(colors[name]); dh.append(HATCH[name])

    for pl, name in [("chainA", "P1"), ("omni", "P2")]:
        add(perhole(glob.glob(f"out/hole/*.{pl}.json"), "B_surface"), f"B\n{name}", name)
    add(perhole(glob.glob("out/e2_audit/*.hole.json"), "B_surface"), "B\nP3", "P3")
    add(perhole(glob.glob("out/hole/*.proto.json"), "B_surface"), "B\nW", "W")
    # 🔴 D（几何独立 RANSAC）必须进 (b)：它是「无 face identity 能恢复到什么程度」的主基线，
    #    只画 D2 会让 §6.4 的差异化论证在图上没有证据。
    for pl, name in [("chainA", "P1"), ("omni", "P2"), ("mayo", "P3")]:
        add(perhole(glob.glob(f"out/e9/*.{pl}.json"), "D_ransac", sub=True), f"D\n{name}", name)
    add(perhole(glob.glob("out/e9b/*.mayo.json"), "D2_perprim", sub=True), "D2\nP3", "P3")
    c3 = []
    for f in glob.glob("out/hole/*.proto.json"):
        d = json.load(open(f))
        for h in d.get("per_hole", []):
            r = h.get("C3_asset_only") or h.get("C2_selfcontained")
            if r and r.get("abs_err") is not None:
                c3.append(max(r["abs_err"], 1e-9))
    add(c3, "C3\nW", "W")
    # 🔴 whis=(0,100)：须画到最小/最大值。默认 1.5 IQR + showfliers=False 会把 Table 7 报告的
    #    尾部（D2/P3 max 184.1 mm、C3/W max 3.4709 mm）整段隐去，图与表互相矛盾。
    bp = b.boxplot(dists, tick_labels=dl, whis=(0, 100), showfliers=False,
                   patch_artist=True, widths=0.6)
    for patch, c, hh in zip(bp["boxes"], dc, dh):
        patch.set_facecolor(c); patch.set_alpha(0.55); patch.set_hatch(hh)
    for i, d in enumerate(dists, 1):        # p99 与 Table 7 的列一一对应
        b.plot([i], [np.percentile(d, 99)], marker="D", ms=2.4, mfc="#222", mec="#222",
               ls="none", zorder=6)
    b.plot([], [], marker="D", ms=2.4, mfc="#222", mec="#222", ls="none", label="p99")
    b.legend(loc="upper right", frameon=False, fontsize=FS_BODY, handletextpad=0.4,
             borderpad=0.1, handlelength=1.0)
    b.set_yscale("log"); b.set_ylabel("Absolute radius error (mm)")
    b.set_title("(b) Error distributions", fontsize=FS_TITLE, loc="left")
    print("   [fig7] n per box:", [len(d) for d in dists])
    save_all(fig, "fig7_downstream")
    print("fig7 done")

which = sys.argv[1] if len(sys.argv) > 1 else "all"
fns = {"1": fig1, "2": fig2, "3": fig3, "4": fig4, "5": fig5, "6": fig6, "7": fig7}
for k, fn in fns.items():
    if which in (k, "all"):
        fn()
