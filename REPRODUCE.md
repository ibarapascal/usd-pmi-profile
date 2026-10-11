<!-- v2 复现指引。目的：任何人（含未来的我们）从 NIST 公共数据零起点复算全部论文数字。
     结构：环境 → 数据 → 流水线步骤（编号=scripts/ 序号）→ 数字渲染。更新规则：脚本增删时同步。 -->

# 08 v2 复现指引

## 环境（本机实测配置）

- macOS；FreeCAD 1.1.1（`/Applications/FreeCAD.app/.../freecadcmd`，headless）；Blender 5.0.1（E5 用）
- Python 3.13 venv：`python3.13 -m venv .venv && .venv/bin/pip install numpy scipy trimesh rtree usd-core point-cloud-utils`
- usdchecker（系统自带或随 usd 发行）

## 数据

- NIST MBE PMI 测试模型（公共领域）→ 下载后放 `data/nist/`（公开 repo README 步骤 1 的约定；批入口默认读此处），已有副本用环境变量 `NIST_DIR` 指定（17 个 AP242 输入 = 16 B-rep + 1 tessellated 变体）
- v1 时代产物（转换网格，复用不重转；路径可用 `V1_ARCHIVE` 覆盖）：`archive/v1-pilot/pilot/out/`——`batch_v4/*.chainA.usdc`（FreeCAD–OBJ–Blender 链）、`batch_v2/omni/*.usdc`（Omniverse hoops_core 511.3.2，NVIDIA 书面许可）、`proto/*.faces.json`（逐面 tessellation）、`batch_v2/*.gtv2.xyz`（v1 UV 网格 GT，敏感性对照用）、`batch_v3/*.cylinders.json`（名义圆柱清单）

## 流水线（scripts/，编号即执行序）

| # | 脚本 | 功能 | 运行器 | 产物 |
|---|---|---|---|---|
| 13 | `13_step_graph.py` | STEP 实体图解析：顶层标注枚举＋typed 抽取＋锚定四分层（face/edge/part/none）。**R1（2026-10-05）起 SHAPE_ASPECT_RELATIONSHIP 只做 relating→related 下行展开**（I-1 修复）；`STEP_SAR_EXPAND=both` 复现 v4 双向行为 | python3 | `out/e1/*.graph.json` |
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
| 27 | `27_figures_v2.py` | 论文图 1–7（3 示意＋4 数据；fig6 改由 34 真重生成）。Fig 8 见 35 | .venv | `figures/fig*.{png,tiff,eps}` |
| 40 | `40_supplement_legacy.py` | ⚠️ 已废弃：SI 唯一源改为投稿包内 supplementary-material.md 手工维护 | — | — |
| 41 | `41_repo_staging.py` | 白名单单向同步 → `../usd-pmi-profile/`（同级 checkout；`--check` 漂移校验；repo 自有文件不碰） | .venv | 同级 repo |
| 42 | `42_assoc_crosscheck.py` | **R1 T6a**：标注→面关联三方核查（v4 双向 graph／下行-only／STEP 内嵌 CAx-IF `pmi validation property` 的 affected area 与 equivalent unicode string）；另断言 `STEP_SAR_EXPAND=both` 逐条复现 v4 graph | .venv | `out/r1/t6/assoc_crosscheck*.json` |
| 43 | `43_r1_tables.py` | **R1 T4/T5/T5b/T6c/T7b/T9/T10 表合集**（未对齐面诊断＋3824 对解析面几何核查／锚定清单＋DATUM what-if／E11 重新归因与 I-5 判别／单位普查／float64 vs float32 C3／0.06 mm 参照读出） | .venv | `out/r1/t43/*.json` |
| 44 | `44_stage_overhead.py` | **R1 T3**：full／geom／weld_geom／weld_full 四变体的载入时间、内存、文件大小（独立子进程×10）＋网格逐元素恒等核验 | .venv | `out/r1/t3/stage_overhead.json` |
| 45 | `45_minimality_ablation.py` | **R1 T11**：profile 四元素逐一剥除后独立消费者的 K1–K7 能力（含自足 C3＋E11 判定链） | .venv | `out/r1/t11/minimality_ablation.json` |
| 46 | `46_composition_check.py` | **R1 T12**：18 实例装配 stage（reference＋Xform）与 Flatten 后的 CF1–CF4 读取路径、实例间零串号、ValidateFamily | .venv | `out/r1/t12/composition_check.json` |
| 28 | `28_convert_docx.py` | 投稿包 docx 转换＋后处理（列宽/行号/页码）＋自检；目标目录见脚本头 | .venv＋pandoc | `<投稿包>/*.docx` |
| 29 | `29_ransac_baseline.py` | E9 regime D：asset-only 序贯 RANSAC 圆柱抽取基线（无 face identity；名义窗口 post-hoc 评分） | .venv | `out/e9/*.{pl}.json` |
| 30 | `30_perprim_baseline.py` | E9b regime D2：逐 mesh prim C2 同款拟合基线（prim 粒度=隐式分割；P3 主对象；`PRIM_RMS_TOL` 环境变量做阈值扫描） | .venv | `out/e9b/*.{pl}.json` |
| 31 | `31_flag_rule.py` | E10：W 侧 asset-side 可标记性规则（60° 角覆盖；全部 >0.04mm 误差被标记） | .venv | `out/e1/flag_rule.json` |
| 32 | `32_flag_rule_p3.py` | E10b：同规则在 P3 prim 上的反向验证（93 个 >0.1mm 误差仅标出 6） | .venv | `out/e1/flag_rule_p3.json` |
| 33 | `33_graphical_abstract.py` | Graphical Abstract（部分期刊的强制项；刻意不含结果数字） | .venv | `figures/graphical_abstract.{png,tiff,eps}` |
| 34 | `34_fig6_regen.py` | fig6 重生成（原为 v1 存档栅格件，dpi 不达刊要求；同数据/同种子/同阈值重跑邻近查询） | .venv | `figures/fig6_spatial.{png,tiff,eps}` |
| 37 | `37_preflight.py` | **投稿包 preflight**：跨文件不变量（源/交付物新鲜度・正文声称的存档物是否真在 repo・实验→SI 归属登记・cover letter 陈旧・期刊硬指标・双盲・SI 节数・repo 漂移与白名单）；**红项必须清零才可提交** | .venv | 退出码 |
| 38 | `38_figure_check.py` | **图合规检查**（2026-08-29 新建）：解 EPS 的 PostScript 源逐图判定 ①最小字号 ≥8 pt（数学上标 0.7×/0.5× 白名单放行）②画幅 ∈{85,174} mm——**按最终排版尺寸作图，排版才不会缩放使字号失效** ③内嵌栅格等效 dpi ≥600 ④正文 `Fig. N` 首现序 ⑤**源件 `figures/*.eps` ⇄ 包内 `Fig{N}.eps` 逐字节一致**（`--deploy` 先复制再检查；手工 cp 会漏，已实踩）。被 `37` 的 I 组调用 | .venv | 退出码 |
| 39 | `39_anon_archive.py` | **ESM_2＝双盲审稿用的去标识 archive**（2026-08-29 新建）：先断言 `41 --check` drift=0（保证与论文数字同源）→ 从公开 repo checkout 复制 → 移除引用元数据文件、匿名化版权行与 Cite 节、全树替换一切定位串 → **逐字节复扫全部文件，命中即中止不出包** → 定时间戳打包。与 37/40/41 同属论文侧工具，不入公开 repo | .venv | `<输出目录>/ESM_2.zip`（默认 `ijidem-submission/`；r1 起 `anon-deposit/`，不随投稿包上传） |
| 35 | `35_selection_figure.py` | **Fig 8：选择往返**——标注→其管辖面、面→管辖它的标注，双向均只读交付场景（CF1–CF3 读取路径的静态取样，非交互工具） | .venv | `figures/fig8_selection.{png,tiff,eps}` |
| 36 | `36_tolerance_judgement.py` | **E11：stage-only 判定链闭合演示**——按**标注组**（非按面）把 C3 拟合尺寸与经 `pmi:appliesTo` 关联的公差带对判；尺寸语义取自 `pmi:dimName`；输出漏斗计数、双口径与出带真因分类；含数值平局容差。**并逐模型普查 `pmi:sourceUnit`**（mm-only / inch-only / mixed 分类与单位缺陷模型的同伴计数 → canonical `e11.u_*`，供 SI S10 直接取值，不再手数） | .venv | `out/e11/tolerance_judgement.json` |
| 47 | `47_tess_sweep.py` | **R1 T1 网格化扫描**（2026-10-05）：逐面网格化 7 变体（OCC deflection 0.01/0.05/0.1=基线/0.5、粗档 0.5 mm＋1.0 rad、Mefisto 等三角数、Netgen Fineness=2），同进程核 B-rep 顶点指纹不变＋C3（同 19 算法、float32）＋60° 角覆盖标记；`--aggregate` 出 `t1_table.json`。参数走环境变量 `T1_STP/T1_OUT/T1_CYL` | freecadcmd（聚合用 .venv） | `<W>/out/t1/<variant>/*.faces.json`（大，留计算节点，不入 repo）、`out/r1/t1/` |
| 48 | `48_topo_perturb.py` | **R1 T2 拓扑/坐标扰动**：经 Part 垫片原样执行未改动的 14，变体 base／split_periodic（1:N）／unify（N:1）／STEP 坐标 ±ε×圆整位 R／仅改 R；逐面分「不变／正确／未匹配／错配」。环境变量 `T2_STP/T2_OUT/T2_BASE` | freecadcmd | `out/r1/t2/*.t2.json` |
| 49 | `49_p2_metadata.ps1`＋`49_p2_metadata.py` | **R1 T8c**：ps1 在 Windows 工作站以**桌面用户本人**跑 hoops_core `convertMetadata=true` 与同会话默认配置各 17 件（服务账户读不到用户 profile 内的 Python 与 Kit 扩展缓存）；py 扫描 PMI 相关属性/metadata/关系（名＋值、typed、是否在 GeomSubset）并逐件 diff | Windows 工作站桌面 PowerShell／.venv | `C:\omniverse\usd-cad\batch-metadata\`、`out/r1/t8/` |
| 50 | `50_sfa_rule_assoc.py` | **R1 T6e（方案 B）**：按 NIST SFA 5.51 开源实现 `sfa-geom.tcl`（getAssocGeom／relatedShapeAspect／getAssocGeomFace）与入口（`sfa-dimtol.tcl` L923–962、`sfa-geotol.tcl` L292/L998）的遍历规则重实现标注→面集合，与 graph.json（r1b，另可对 v4/r1）逐条四分类比对，附 NIST affected area 对照；STEP 分词复用 13 的解析层，遍历规则独立。**是规则重实现，不是 SFA 运行输出** | .venv | `out/r1/t6e/sfa_rule_assoc*.json` |
| 51 | `51_r1_keys.py` | **R1 数字键抽取**：从 `out/r1/` 冻结产物抽 75 个 `r1.*` 键，**逐键 assert 冻结值**；`R1_DIR`／`R1_OUT` 环境变量可改输入/输出（公开 repo 内 `R1_DIR=results/r1`） | .venv | `out/r1/canonical_r1.json` |
| 52 | `52_r1_token_diff.py` | R1 稿件数字 token diff（v4→v5 渲染稿，未授权变动检测）。论文侧工具，不入公开 repo | .venv | 标准输出 |
| 53 | `53_response_check.py` | response letter 校验（引用块／摘录／数字／双盲禁词）＋转 docx。论文侧工具，不入公开 repo | .venv＋pandoc | `<投稿包>/response-letter.docx` |
| 54 | `54_verify_results.py` | **只读 `results/` 的自足核验**（2026-10-05）：逐模型审计求和、E11 逐组重数、关联目标数与 42 交叉核对、以 `R1_DIR=results/r1` 重跑 51 并逐字节对 `canonical_r1.json`。**须在公开 repo／archive 根目录跑**（论文侧无 `results/`） | python3（仅标准库） | 退出码 |

批处理入口（**统一在 scripts/ 下，2026-08-28 归位**）：`scripts/run_e3_batch.sh`（E3 全量）、`run_e4_batch.sh`（E4 全量）、`run_redo_batch.sh`（2026-08-28 修复重跑链）、`run_e4b_fix_batch.sh`（C3＋win30 敏感性）、`run_e2_audit_batch.sh`（E2 审计：26 扫描＋18 几何＋19 孔径 A/B，输入=`out/e2_mayo/`）；E9/E9b＝`run_e9_batch.sh`（29/30 逐管线批；D2 阈值扫描＝`PRIM_RMS_TOL` 循环于 `out/e9b_rms*/`）；P3 win30＝`HOLE_WIN_R=0.30` 循环 19 于 `out/e2_win30/`。E5：`usdchecker out/proto_v2/*.usdc`＋`24_blender_import_check.py`（Blender -b --python）。E5b：`22_independent_reader.py`（独立消费端演示；英文注释版 `22_independent_reader_en.py` 入 SI S8 与公开 repo）。S3：`23_registration_table.py`。E8 消融（Table S5，双尺度自标定承重性）＝`run_e8_ablation.sh`。R1 T1/T2＝`run_r1_t1t2.sh <W> [t1|t2|both]`（在 Mac 计算节点经作业调度器跑；要求 FreeCAD 1.1.1，版本不符即中止）。

**单位修复后的最小重跑（2026-08-29）**：`scripts/run_unit_fix_rerun.sh`——只重跑 13→15→16。⚠️ 只需这三步：孔计量(19)与基线(29/30/31/32)经核仅读 `pmi:surfaceType` 与几何，**不读 `pmi:value`**，故单位换算不影响任何几何/经验结果（实测 canonical 全键零漂移；该轮键数 669）。E11 随后跑 36。

**R1 修回的关联修复重跑（2026-10-05）**：`scripts/run_r1_assoc_rerun.sh`——13（SAR 下行展开）→15→16→36→20；先把 v4 产物冻结到 `out/r1/t6/v4-frozen/`，canonical 的 v4 冻结件为 `out/e1/canonical_numbers.v4-submitted.json`。19/29–32 只读几何与 `pmi:surfaceType`、14 不读标注，不重跑。实测：同环境先跑 20 复现 v4 canonical 逐字节一致，再重跑后 681 键中 16 键变化（逐键登记 → `notes/20261005-revision-numbers.md`「canonical diff」节）。

**R1 I-7 修复重跑（r1→r1b，2026-10-05）**：13 的 `SA_LIKE` 加 `DATUM` 后再跑 `run_r1_assoc_rerun.sh`（r1 产物先冻结到 `out/r1/t6/r1-frozen/`、`out/e1/canonical_numbers.r1.json`）；r1→r1b 681 键变 8（只涉 `e1.anchor_*`／`e1.audit.rel_*`／`e1.audit.target_*`，E11 逐字节不变），与 `out/r1/t6/i7-whatif/` 完全一致。42 用 r1b 重跑输出 `out/r1/t6b/`（v4 graph＋match 合成目录 `out/r1/t6b/v4e1/`）；45/46 用 r1b stage 重跑输出 `out/r1/t11b/`、`t12b/`。**T1 下游**：`scripts/run_r1_t1_downstream.sh`（`T1W=<t1t2t8 工作目录> PAR=4`）对 47 的 7 个网格化变体各走 15→16→19 --subset→36（r1b graph），汇总 `out/r1/t1/downstream_table.json`。

**全面 review 后的增补（2026-08-29 晚）**：36 增加单位普查、20 增加 `e11.u_*` 七键，canonical 由 669 → **676 键，既有键零漂移**（逐键 diff 核实）。27 的 fig7 组间距与 35 的 Fig 8 读出同轮修正，需重跑 `27 7`＋`35`。

## 公开 repo／去标识 archive 中的 R1 内容（2026-10-05）

- **同步**：`41_repo_staging.py` 白名单＝上表中标「不入公开 repo」以外的复现链脚本（含 42–51、54 与 `run_r1_*.sh`）；`results/r1/` 保持 `out/r1/` 的相对路径（`canonical_r1.json`、T1 `downstream_table.json`／`t1_table.json`／`t2_table.json`、T3 `t3b/stage_overhead.json`、`t43/*.json` 全部 8 件、T6 `t6b/assoc_crosscheck{,.summary}.json`、T6e `t6e/sfa_rule_assoc{,.summary}.json`、T8 `t8/*.json`、T11 `t11b/minimality_ablation.json`、T12 `t12b/composition_check.json`，约 2 MB）。SI 取修回版 `ijidem-submission-r1/supplementary-material.md`；Fig 3／Fig 4／GA 取 `ijidem-submission-r1/figures/src/` 的修回件。
- **不入**（体积或可再生）：各网格化变体与 T3/T11/T12 的 stage（`.usdc`，各约 12 MB）、T1 逐面 `faces.json` 与逐模型 summary、T1 各变体逐模型审计／孔／E11 明细（汇总在 `downstream_table.json`）、T2 逐模型 `*.t2.json`（汇总在 `t2_table.json`）、P2 原始转换输出、被 r1b 取代的首轮件与冻结副本、运行日志与调度 spec。
- **自足核验（无需 FreeCAD／Omniverse／NIST 下载）**：在 repo 或 archive 根目录 `python scripts/54_verify_results.py`——复算 838 存活、695/697 关联、2527/2555＝98.9% 目标（并与 42 的独立计数交叉）、E11 122/128 组与 599 面，并以 51 重抽 75 个 r1 键（逐键 assert 冻结值）且输出与存档逐字节一致。
- **去标识 archive**：`39_anon_archive.py anon-deposit`（先要求 `41 --check` drift=0；禁用串含作者／机构／repo 名／DOI／机器名／本地用户路径，逐字节复扫 0 命中才出包）。

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
