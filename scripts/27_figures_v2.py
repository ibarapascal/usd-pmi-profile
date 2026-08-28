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
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 300, "savefig.bbox": "tight", "font.family": "Helvetica"})
BLUE, GRAY, WARM, GREEN, PURPLE = "#2b5f9e", "#8a8f98", "#c4552d", "#3a7d44", "#6a4c93"
K = json.load(open("out/e1/canonical_numbers.json"))


def save_all(fig, stem):
    """png（阅读用）＋ tiff（栅格备份）＋ eps（投稿交付：矢量优先，含嵌入字体）。
    EPS 不支持 alpha，故显式给白底，避免透明区域在 EPS 里变黑。"""
    fig.patch.set_alpha(1.0)
    fig.savefig(f"figures/{stem}.png")
    fig.savefig(f"figures/{stem}.tiff")
    fig.savefig(f"figures/{stem}.eps", format="eps")

def box(ax, x, y, w, h, text, fc="#eef2f7", ec=BLUE, fs=8, weight="normal"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fc=fc, ec=ec, lw=1.1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, weight=weight)

def arrow(ax, x1, y1, x2, y2, color=GRAY, style="-|>", lw=1.2, ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, color=color,
                                 lw=lw, linestyle=ls, mutation_scale=12))

def fig1():
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 3.1))
    for ax in (a, b):
        ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
    a.set_title("(a) Semantic PMI: typed entity graph", fontsize=9, loc="left")
    box(a, 2.6, 8.2, 5.2, 1.3, "DIMENSIONAL_SIZE\n'diameter'", fs=7.5)
    box(a, 0.3, 5.4, 4.2, 1.3, "value = 3.5 mm\nPLUS_MINUS ±0.1", fc="#eaf3ea", ec=GREEN, fs=7.5)
    box(a, 5.5, 5.4, 4.2, 1.3, "GISU / IIRU\nassociation", fs=7.5)
    box(a, 5.5, 2.4, 4.2, 1.3, "ADVANCED_FACE\n(cylindrical)", fc="#f4ede2", ec=WARM, fs=7.5)
    box(a, 0.3, 2.4, 4.2, 1.3, "DATUM_SYSTEM\n[A|B|C]", fs=7.5)
    arrow(a, 4.0, 8.2, 2.4, 6.7); arrow(a, 6.4, 8.2, 7.6, 6.7)
    arrow(a, 7.6, 5.4, 7.6, 3.7); arrow(a, 1.4, 5.4, 1.8, 3.7)
    a.text(0.3, 0.6, "machine-readable: values, tolerances, datums,\nand face references are typed entities",
           fontsize=7.5, style="italic")
    b.set_title("(b) Graphical PMI: presentation polylines", fontsize=9, loc="left")
    b.add_patch(plt.Rectangle((1.2, 3.2), 6.0, 4.2, fc="none", ec=GRAY, lw=1.0))
    b.add_patch(plt.Circle((4.2, 5.3), 1.15, fc="none", ec=GRAY, lw=1.0))
    b.plot([4.9, 6.6], [6.2, 8.2], color=GRAY, lw=0.9)
    b.text(6.7, 8.3, "⌀ 3.5 ± 0.1", fontsize=9, family="monospace")
    b.text(6.7, 7.6, "(stroked curves)", fontsize=7, color=GRAY)
    b.text(1.2, 1.2, "human-readable only: the same callout rendered as\nunstructured curve geometry — no queryable value",
           fontsize=7.5, style="italic")
    save_all(fig, "fig1_pmi_concept")
    print("fig1 done")

def fig2():
    fig, ax = plt.subplots(figsize=(7.0, 3.9))
    ax.set_xlim(0, 14); ax.set_ylim(0, 10); ax.axis("off")
    box(ax, 0.2, 3.6, 2.6, 2.6, "NIST MBE PMI\ntest set\n17 AP242 inputs\n(16 B-rep + 1 tess.)",
        fc="#f4ede2", ec=WARM, fs=7.5)
    labels = [("P1  STEP-FreeCAD-OBJ-Blender-USD", 8.3),
              ("P2  Omniverse hoops_core converter", 6.5),
              ("P3  Mayo-glTF-guc", 4.7),
              ("W   profile writer (this paper)", 2.9)]
    for t, y in labels:
        fc = "#eaf0e6" if t.startswith("W") else "#eef2f7"
        ec = GREEN if t.startswith("W") else BLUE
        box(ax, 3.6, y - 0.65, 5.3, 1.3, t, fc=fc, ec=ec, fs=7.5)
        arrow(ax, 2.8, 4.9, 3.6, y)
    box(ax, 9.8, 6.9, 4.0, 2.4, "Semantic audit\ninventory diff · typed round-trip\nassociation validity", fs=7.2)
    box(ax, 9.8, 3.9, 4.0, 2.4, "Geometric audit\narea-uniform sampling\nregistration · BVH distance", fs=7.2)
    box(ax, 9.8, 0.9, 4.0, 2.4, "Downstream task\nhole-diameter recovery\nfive information regimes", fs=7.2)
    for y in (8.3, 6.5, 4.7, 2.9):
        for ty in (8.1, 5.1, 2.1):
            arrow(ax, 8.9, y, 9.8, ty, lw=0.7)
    ax.text(0.2, 0.4, "Audit tooling predates the writer and has no privileged interface to any pipeline.",
            fontsize=7.5, style="italic")
    save_all(fig, "fig2_protocol")
    print("fig2 done")

def fig3():
    fig, ax = plt.subplots(figsize=(7.0, 3.9))
    ax.set_xlim(0, 14); ax.set_ylim(0, 10); ax.axis("off")
    ax.set_title("STEP entities (left) mapped to USD prims under the profile (right)", fontsize=9, loc="left")
    box(ax, 0.2, 7.2, 4.6, 1.4, "#412 DIMENSIONAL_SIZE\nvalue 3.5, ±0.1 (PLUS_MINUS)", fc="#f4ede2", ec=WARM, fs=7)
    box(ax, 0.2, 4.6, 4.6, 1.4, "#231 ADVANCED_FACE\n(via GISU / shape aspect chain)", fc="#f4ede2", ec=WARM, fs=7)
    box(ax, 0.2, 2.0, 4.6, 1.4, "#88 DATUM 'A'", fc="#f4ede2", ec=WARM, fs=7)
    box(ax, 7.2, 8.3, 6.4, 1.2, "/Part  (UsdGeomMesh, per-face tessellation;\nmetersPerUnit per source declaration)", fs=7)
    box(ax, 8.0, 6.3, 5.6, 1.4, "GeomSubset 'brepFace_231'\nfamilyName = brepFace\npmi:surfaceType = \"Cylinder\"", fc="#eaf0e6", ec=GREEN, fs=7)
    box(ax, 8.0, 3.7, 5.6, 1.9, "/Part/PMI/anno_412\npmi:type/value/lowerBound/upperBound\npmi:stepId · verbatim record\nrel pmi:appliesTo: brepFace_231", fc="#eaf0e6", ec=GREEN, fs=7)
    box(ax, 8.0, 1.4, 5.6, 1.4, "/Part/PMI/anno_88\npmi:type=\"datum\", pmi:datumLetter=\"A\"", fc="#eaf0e6", ec=GREEN, fs=7)
    arrow(ax, 4.8, 7.9, 8.0, 4.9, color=PURPLE)
    arrow(ax, 4.8, 5.3, 8.0, 7.0, color=PURPLE)
    arrow(ax, 4.8, 2.7, 8.0, 2.1, color=PURPLE)
    arrow(ax, 10.8, 5.6, 10.8, 6.3, color=GREEN, ls="--")
    ax.text(11.0, 5.8, "relationship", fontsize=6.5, color=GREEN)
    ax.text(5.2, 0.5, "fingerprint alignment maps STEP face ids to mesh face indices (Sec. 4.5)",
            fontsize=7.5, style="italic", color=PURPLE)
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
    fig, ax = plt.subplots(figsize=(6.6, 4.4))
    names = [r[0] for r in rows]
    y = np.arange(len(rows))
    segs = [("face", GREEN, "face-anchored (690)"), ("edge", BLUE, "edge-anchored (21)"),
            ("part", PURPLE, "whole-part (2)"),
            ("none", WARM, "no machine-readable link in source (11)"),
            ("datum", "#d9dde3", "DATUM (identity only, 114)")]
    left = np.zeros(len(rows))
    for key, color, label in segs:
        vals = np.array([r[1][key] for r in rows])
        ax.barh(y, vals, left=left, height=0.62, color=color, label=label)
        left += vals
    for yy, tot in zip(y, left):
        ax.annotate(str(int(tot)), (tot, yy), xytext=(3, 0), textcoords="offset points",
                    va="center", fontsize=7)
    ax.set_yticks(y, names, fontsize=7.5)
    ax.invert_yaxis()
    ax.set_xlabel("Top-level semantic PMI annotations (anchoring stratification)")
    ax.set_title("All 838 annotations carried by W (by construction); production pipelines carry 0.\n"
                 "Colors: the empirical anchoring stratification of the sources.", fontsize=8, loc="left")
    ax.legend(fontsize=6.8, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, framealpha=0.95)
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
    fig, ax = plt.subplots(figsize=(4.6, 3.2))
    x = [r[0] for r in rows]
    for key, marker, al in [("mean", "o", 1.0), ("p99", "s", 0.7), ("max", "^", 0.45)]:
        ax.plot(x, [r[1][key] for r in rows], marker=marker, color=BLUE, lw=1.5, ms=5, alpha=al)
        ax.annotate(key, (x[-1], rows[-1][1][key]), xytext=(6, 0), textcoords="offset points",
                    va="center", color=BLUE, fontsize=8)
        ax.scatter([5951], [omni[key]], marker="D", s=26, color=WARM, zorder=5)
    ax.annotate("Omniverse\n(default)", (5951, omni["mean"]), xytext=(0, -26),
                textcoords="offset points", ha="center", color=WARM, fontsize=7.5)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Triangle count (STC-06)"); ax.set_ylabel("Direction-B deviation (mm)")
    ax.grid(True, which="both", lw=0.3, alpha=0.3)
    save_all(fig, "fig5_budget")
    print("fig5 done")

def fig6():
    # fig6 已改为真重生成（分辨率需达刊要求）→ 见 34_fig6_regen.py；此处不再复用存档栅格件。
    print("fig6: run 34_fig6_regen.py (regenerates at 600 dpi from the archived v1 data)")

def fig7():
    regimes = [("A\nvertex", "A_vertex_all", {"chainA": "P1", "omni": "P2", "e2": "P3", "proto": "W"}),
               ("B\nsurface", "B_surface", {"chainA": "P1", "omni": "P2", "e2": "P3", "proto": "W"}),
               ("C\nnominal axis", "C_subset", {"proto": "W"}),
               ("C2\nself-fit", "C2_selfcontained", {"proto": "W"}),
               ("C3\nasset-only", "C3_asset_only", {"proto": "W"})]
    # (a) measurable %
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 3.4), gridspec_kw={"width_ratios": [1.15, 1]})
    colors = {"P1": GRAY, "P2": WARM, "P3": PURPLE, "W": GREEN}
    xt, xl = [], []
    xpos = 0
    for label, key, pls in regimes:
        for pl, name in pls.items():
            if pl == "e2":
                pct = K.get(f"e2.hole.{'A' if key == 'A_vertex_all' else 'B'}.pct")
            elif key == "C3_asset_only":
                # C3 可测率＝枚举一致下全量（match_pct 是枚举一致率）
                pct = K.get("e4.proto.C3_asset_only.match_pct")
            else:
                pct = K.get(f"e4.{pl}.{key}.pct")
            a.bar(xpos, pct, color=colors[name], width=0.8)
            a.annotate(name, (xpos, pct), xytext=(0, 2), textcoords="offset points",
                       ha="center", fontsize=6.5)
            xpos += 1
        xt.append(xpos - (len(pls) + 1) / 2 + 0.5); xl.append(label)
        xpos += 2.8          # 组间距：单柱组的两行标签在 1.6 下会相撞（2026-08-29 全面 review 查出）
    a.set_xticks(xt, xl, fontsize=6.5); a.set_ylabel("Measurable cylinders (%)")
    a.set_title("(a) Measurability by regime (n = 1,866)", fontsize=8.5, loc="left")
    a.axhline(100, color=GRAY, lw=0.5, ls=":")
    # (b) error distributions (abs err, log scale)
    def perhole(files, key):
        out = []
        for f in files:
            d = json.load(open(f))
            for h in d["per_hole"]:
                r = h.get(key)
                if r and r.get("n", 0) >= 8 and r.get("abs_err") is not None:
                    out.append(max(r["abs_err"], 1e-9))
        return out
    dists, dl, dc = [], [], []
    for pl, name in [("chainA", "P1"), ("omni", "P2")]:
        dists.append(perhole(glob.glob(f"out/hole/*.{pl}.json"), "B_surface")); dl.append(f"B\n{name}"); dc.append(colors[name])
    dists.append(perhole(glob.glob("out/e2_audit/*.hole.json"), "B_surface")); dl.append("B\nP3"); dc.append(colors["P3"])
    dists.append(perhole(glob.glob("out/hole/*.proto.json"), "B_surface")); dl.append("B\nW"); dc.append(colors["W"])
    c3 = []
    for f in glob.glob("out/hole/*.proto.json"):
        d = json.load(open(f))
        for h in d.get("per_hole", []):
            r = h.get("C3_asset_only") or h.get("C2_selfcontained")
            if r and r.get("abs_err") is not None:
                c3.append(max(r["abs_err"], 1e-9))
    dists.append(c3); dl.append("C3\nW"); dc.append(colors["W"])
    bp = b.boxplot(dists, tick_labels=dl, showfliers=False, patch_artist=True, widths=0.55)
    for patch, c in zip(bp["boxes"], dc):
        patch.set_facecolor(c); patch.set_alpha(0.55)
    b.set_yscale("log"); b.set_ylabel("Absolute radius error (mm)")
    b.set_title("(b) Error distributions (measured holes)", fontsize=8.5, loc="left")
    b.tick_params(axis="x", labelsize=7)
    save_all(fig, "fig7_downstream")
    print("fig7 done")

which = sys.argv[1] if len(sys.argv) > 1 else "all"
fns = {"1": fig1, "2": fig2, "3": fig3, "4": fig4, "5": fig5, "6": fig6, "7": fig7}
for k, fn in fns.items():
    if which in (k, "all"):
        fn()
