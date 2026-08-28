<!-- v2 复现指引。目的：任何人（含未来的我们）从 NIST 公共数据零起点复算全部论文数字。
     结构：环境 → 数据 → 流水线步骤（编号=scripts/ 序号）→ 数字渲染。更新规则：脚本增删时同步。 -->

# 08 v2 复现指引

## 环境（本机实测配置）

- macOS；FreeCAD 1.1.1（`/Applications/FreeCAD.app/.../freecadcmd`，headless）；Blender 5.0.1（E5 用）
- Python 3.13 venv：`python3.13 -m venv .venv && .venv/bin/pip install numpy scipy trimesh rtree usd-core point-cloud-utils`
- usdchecker（系统自带或随 usd 发行）

## 数据

- NIST MBE PMI 测试模型（公共领域）→ `../../.cache/usd-cad/nist/NIST-PMI-STEP-Files/`（17 个 AP242 输入 = 16 B-rep + 1 tessellated 变体）
- v1 时代产物（转换网格，复用不重转；路径可用 `V1_ARCHIVE` 覆盖）：`archive/v1-pilot/pilot/out/`——`batch_v4/*.chainA.usdc`（FreeCAD–OBJ–Blender 链）、`batch_v2/omni/*.usdc`（Omniverse hoops_core 511.3.2，NVIDIA 书面许可）、`proto/*.faces.json`（逐面 tessellation）、`batch_v2/*.gtv2.xyz`（v1 UV 网格 GT，敏感性对照用）、`batch_v3/*.cylinders.json`（名义圆柱清单）

## 流水线（scripts/，编号即执行序）

| # | 脚本 | 功能 | 运行器 | 产物 |
|---|---|---|---|---|
| 13 | `13_step_graph.py` | STEP 实体图解析：顶层标注枚举＋typed 抽取＋锚定四分层（face/edge/part/none） | python3 | `out/e1/*.graph.json` |
| 14 | `14_face_match.py` | STEP ADVANCED_FACE ↔ OCC 面 index（顶点集合指纹＋双 scale 自校准） | freecadcmd | `out/e1/*.match.json` |
| 15 | `15_usd_author_v2.py` | writer v2：subset＋typed PMI＋rel appliesTo | .venv | `out/proto_v2/*.usdc` |
| 16 | `16_audit_v2.py` | 审计：存活/typed 往返等值/rel 有效性，并**逐条判定 CF1–CF7** 输出 per-condition verdict（标注按 `pmi:type` 属性发现，不依赖命名） | .venv | `out/e1/*.audit_v2.json` |
| 17 | `17_gt_area_sample.py` | 面积一致 GT 采样（Jacobian 拒绝采样，seed=42） | freecadcmd | `out/gt_area/*.xyz` |
| 18 | `18_measure_dirB.py` | 方向 B 距离（pcu C++ BVH；恒等+24 旋转 bbox-中心注册；单位自校准） | .venv | `out/dirB/*.json` |
| 19 | `19_hole_v2.py` | 孔径四口径 A/B/C/C2 | .venv | `out/hole/*.json` |
| 20 | `20_aggregate_v2.py` | 聚合 → canonical numbers | .venv | `out/e1/canonical_numbers.json`＋`notes/calculation-results.md` |
| 21 | `21_render_draft.py` | draft {{key}} 渲染 | .venv | `draft-zh-v2.rendered.md` |
| 25 | `25_e2_pcb_batch.ps1` | E2 第二开源链批转换：STEP→Mayo 0.10.0(mayo-conv)→glb→guc 0.5(USD 25.11 预编译) | **Windows 工作站**（预编译栈：Mayo win64 zip＋guc_USD25.11_Windows＋pablode/USD v25.11-ci-release） | `out/e2_mayo/*.{glb,usdc}`＋`e2_batch.log` |
| 26 | `26_e2_scan.py` | E2 语义/结构扫描（PMI 痕迹/单位声明/mesh·subset 计数） | .venv | `out/e2_audit/scan.json` |
| 27 | `27_figures_v2.py` | 论文 7 图（3 示意＋4 数据；fig6 复用 v1 存档产物） | .venv | `figures/fig*.{png,tiff}` |
| 40 | `40_supplement_legacy.py` | ⚠️ 已废弃：SI 唯一源改为投稿包内 supplementary-material.md 手工维护 | — | — |
| 41 | `41_repo_staging.py` | 白名单单向同步 → `../usd-pmi-profile/`（同级 checkout；`--check` 漂移校验；repo 自有文件不碰） | .venv | 同级 repo |
| 28 | `28_convert_docx.py` | 投稿包 docx 转换＋后处理（列宽/行号/页码）＋自检；目标目录见脚本头 | .venv＋pandoc | `<投稿包>/*.docx` |
| 29 | `29_ransac_baseline.py` | E9 regime D：asset-only 序贯 RANSAC 圆柱抽取基线（无 face identity；名义窗口 post-hoc 评分） | .venv | `out/e9/*.{pl}.json` |
| 30 | `30_perprim_baseline.py` | E9b regime D2：逐 mesh prim C2 同款拟合基线（prim 粒度=隐式分割；P3 主对象；`PRIM_RMS_TOL` 环境变量做阈值扫描） | .venv | `out/e9b/*.{pl}.json` |
| 31 | `31_flag_rule.py` | E10：W 侧 asset-side 可标记性规则（60° 角覆盖；全部 >0.04mm 误差被标记） | .venv | `out/e1/flag_rule.json` |
| 32 | `32_flag_rule_p3.py` | E10b：同规则在 P3 prim 上的反向验证（93 个 >0.1mm 误差仅标出 6） | .venv | `out/e1/flag_rule_p3.json` |
| 33 | `33_graphical_abstract.py` | Graphical Abstract（部分期刊的强制项；刻意不含结果数字） | .venv | `figures/graphical_abstract.{png,tiff,eps}` |
| 34 | `34_fig6_regen.py` | fig6 重生成（原为 v1 存档栅格件，dpi 不达刊要求；同数据/同种子/同阈值重跑邻近查询） | .venv | `figures/fig6_spatial.{png,tiff,eps}` |
| 37 | `37_preflight.py` | **投稿包 preflight**：跨文件不变量（源/交付物新鲜度・正文声称的存档物是否真在 repo・实验→SI 归属登记・cover letter 陈旧・期刊硬指标・双盲・SI 节数・repo 漂移与白名单）；**红项必须清零才可提交** | .venv | 退出码 |
| 35 | `35_selection_figure.py` | **Fig 8：选择往返**——标注→其管辖面、面→管辖它的标注，双向均只读交付场景（CF1–CF3 读取路径的静态取样，非交互工具） | .venv | `figures/fig8_selection.{png,tiff,eps}` |
| 36 | `36_tolerance_judgement.py` | **E11：stage-only 判定链闭合演示**——按**标注组**（非按面）把 C3 拟合尺寸与经 `pmi:appliesTo` 关联的公差带对判；尺寸语义取自 `pmi:dimName`；输出漏斗计数、双口径与出带真因分类；含数值平局容差 | .venv | `out/e11/tolerance_judgement.json` |

批处理入口（**统一在 scripts/ 下，2026-08-28 归位**）：`scripts/run_e3_batch.sh`（E3 全量）、`run_e4_batch.sh`（E4 全量）、`run_redo_batch.sh`（2026-08-28 修复重跑链）、`run_e4b_fix_batch.sh`（C3＋win30 敏感性）、`run_e2_audit_batch.sh`（E2 审计：26 扫描＋18 几何＋19 孔径 A/B，输入=`out/e2_mayo/`）；E9/E9b＝`run_e9_batch.sh`（29/30 逐管线批；D2 阈值扫描＝`PRIM_RMS_TOL` 循环于 `out/e9b_rms*/`）；P3 win30＝`HOLE_WIN_R=0.30` 循环 19 于 `out/e2_win30/`。E5：`usdchecker out/proto_v2/*.usdc`＋`24_blender_import_check.py`（Blender -b --python）。E5b：`22_independent_reader.py`（独立消费端演示；英文注释版 `22_independent_reader_en.py` 入 SI S8 与公开 repo）。S3：`23_registration_table.py`。E8 消融（Table S5，双尺度自标定承重性）＝`run_e8_ablation.sh`。

**单位修复后的最小重跑（2026-08-29）**：`scripts/run_unit_fix_rerun.sh`——只重跑 13→15→16。⚠️ 只需这三步：孔计量(19)与基线(29/30/31/32)经核仅读 `pmi:surfaceType` 与几何，**不读 `pmi:value`**，故单位换算不影响任何几何/经验结果（实测 canonical 644 键零漂移）。E11 随后跑 36。

## P1/P2 存档网格的来源（scripts/01–12＝v1 时代脚本，保留供追溯）

`scripts/01–12` 为 v1 批次（2026-07）的生成与测量脚本，本轮**只复用其转换产物、不重转**：
- `batch_v4/*.chainA.usdc` ＝ `01_step_to_mesh.py`（freecadcmd，STEP→OBJ）→ `02_mesh_to_usd.py`（Blender headless，OBJ→USD）——链 A 的两跳
- `batch_v2/omni/*.usdc` ＝ Windows 工作站上 Omniverse usd-convert-cad workflow（hoops_core 511.3.2）产物传回；**本机无 Omniverse，重转需该环境＋厂商许可**（v1 记录 → `archive/v1-pilot/pilot/pilot-log.md` §4.5–4.9）
- `proto/*.faces.json` ＝ `11_face_tess.py`（freecadcmd 逐面 tessellation）
- `batch_v2/*.gtv2.xyz` ＝ `04_brep_sample.py`（UV 网格 GT，仅作 v2 敏感性对照）
- `batch_v3/*.cylinders.json` ＝ `07_cylinders.py`（名义圆柱清单）

## 已知实现教训（审计记录，勿重蹈）

1. 距离核心禁用 trimesh.proximity（纯 Python，50k 点不可用）；手搓 kNN 预筛两版均在大三角形上系统性漏检——**终版＝point-cloud-utils 精确 BVH**，STC-06 proto 复算 0.0007mm 与 v1 吻合为对账锚。
2. 注册平移必须用 **bbox 中心**，点云质心被顶点密度不均污染（chainA 全线 1.3–15mm 假偏差的教训）。
3. 复合实例中空参数组件（`FLATNESS_TOLERANCE()`）排序在前——公差组件遍历不可 first-match-break。
4. STEP 文本坐标与 OCC 读入坐标的单位差（英寸件）用双 scale 自校准，禁按 `INCH` 字符串判定（stc_06 的 PMI 单位定义会误中）。
