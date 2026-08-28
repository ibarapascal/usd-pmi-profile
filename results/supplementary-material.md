# Online Resource 1 — Supplementary material

**Tolerance-resolvable OpenUSD: a minimal standards-only carrier profile for semantic PMI** — Supplements S1–S10.

## S1. Search protocol

Two rounds (July 2026; August 2026). Publication window 2016–2026; preprints included via arXiv. Sources: arXiv (cs.GR, cs.CE), Scopus-indexed journals, proceedings of the main graphics and engineering-informatics venues, and the AOUSD developer forum (site search).

Query families (each run with variants): "OpenUSD PMI", "USD GD&T", "CAD to USD semantic", "semantic PMI scene description", "PMI embedding visualization format", "GD&T derivative format", "MBD derivative format", "semantic annotation scene graph". AOUSD forum site queries: "PMI", "GD&T", "tolerance", "CAD metadata".

Round outcomes: no peer-reviewed quantitative treatment of semantic-PMI survival in CAD-to-USD ingestion was found in either round; the forum search returned no public PMI/GD&T support requests. The closest works found — the FreeCAD-Omniverse connector and the AP242/WebGL browser visualization — are cited and differentiated in Section 1 of the paper.

## S2. Archived P1/P2 artifacts: versions and generation commands

P1 (STEP-FreeCAD-OBJ-Blender-USD): FreeCAD 1.1.1 headless (`freecadcmd`), OpenCASCADE kernel, STEP import + OBJ export at linear deflection 0.1 mm; Blender 5.0.1 headless (`blender -b --python`), OBJ import + USD export, default settings. One command pair per model; scripts 01-02 of the archived pilot directory of the reproduction package.

P2 (Omniverse): omni.kit.converter.hoops_core 511.3.2, HOOPS Exchange 10.6.1, Kit SDK 110.1.1, default conversion settings, executed on a Windows RTX workstation; per-model logs archived. Quantitative results published with NVIDIA's written permission.

P3 (Mayo-glTF-guc): Mayo 0.10.0 (`mayo-conv --export <model>.glb <model>.stp`), guc 0.5 built against USD 25.11 (`guc <model>.glb <model>.usdc`), official prebuilt binaries; the batch driver script of the reproduction package and per-model log archived.


## S3. Per-model registration table

Protocol of Section 4.3 (identity + 24 proper rotations, bounding-box-center translation, median criterion on a 2,000-point subsample). Winner, runner-up, and gap ratio per model and pipeline (P1 = FreeCAD-OBJ-Blender, P2 = Omniverse hoops_core, P3 = Mayo-glTF-guc, W = the profile writer). Candidate labels: `identity` is the untransformed pose (no rotation, no translation); `rot0` is the identity rotation combined with the bounding-box-centering translation; `rot1`-`rot23` are the remaining proper rotations, each with the centering translation. On models already centered, `identity` and `rot0` coincide and ties at 0.0 are resolved arbitrarily. Gap ratios above 10^4 arise from division by a near-zero winner median and are capped in this table.

| Model | Pipeline | Winner | Median (mm) | Runner-up | Runner median (mm) | Gap ratio |
|---|---|---|---|---|---|---|
| ctc_01-e1 | P1 | rot3 | 1e-05 | rot7 | 2e-05 | 1.3 |
| ctc_01-e1 | P2 | identity | 0.0 | rot0 | 0.0 | 1.0 |
| ctc_01-e1 | P3 | rot0 | 0.0 | rot5 | 0.0 | 1.0 |
| ctc_01-e1 | W | identity | 0.0 | rot0 | 0.0 | 1.0 |
| ctc_02-e2 | P1 | rot3 | 0.01263 | rot6 | 9.62259 | 761.9 |
| ctc_02-e2 | P2 | identity | 0.0 | rot0 | 0.01263 | 5657.9 |
| ctc_02-e2 | P3 | identity | 1e-05 | rot0 | 0.01189 | 1424.4 |
| ctc_02-e2 | W | identity | 0.0 | rot0 | 0.00683 | 4349.8 |
| ctc_03-e2 | P1 | rot3 | 0.01297 | rot7 | 0.97026 | 74.8 |
| ctc_03-e2 | P2 | identity | 0.0 | rot0 | 0.013 | 3528.8 |
| ctc_03-e2 | P3 | identity | 0.0 | rot0 | 2.02965 | >10^4 |
| ctc_03-e2 | W | identity | 0.0 | rot0 | 0.013 | 4259.0 |
| ctc_04-e1 | P1 | rot3 | 0.00886 | rot7 | 4.23515 | 478.0 |
| ctc_04-e1 | P2 | identity | 0.0 | rot0 | 0.00891 | >10^4 |
| ctc_04-e1 | P3 | identity | 0.0 | rot0 | 5.68871 | >10^4 |
| ctc_04-e1 | W | identity | 0.0 | rot0 | 0.00891 | >10^4 |
| ctc_05-e1 | P1 | rot3 | 4e-05 | rot7 | 5e-05 | 1.2 |
| ctc_05-e1 | P2 | identity | 0.0 | rot0 | 0.0 | 1.4 |
| ctc_05-e1 | P3 | identity | 0.0 | rot0 | 0.0 | 1.5 |
| ctc_05-e1 | W | identity | 0.0 | rot0 | 0.0 | 3.0 |
| ftc_06-e2 | P1 | rot3 | 1e-05 | rot6 | 0.89436 | >10^4 |
| ftc_06-e2 | P2 | identity | 0.0 | rot0 | 0.0 | >10^4 |
| ftc_06-e2 | P3 | identity | 0.0 | rot0 | 0.0 | 1.9 |
| ftc_06-e2 | W | identity | 0.0 | rot0 | 0.0 | >10^4 |
| ftc_07-e2 | P1 | rot3 | 0.00841 | rot7 | 1.7838 | 212.0 |
| ftc_07-e2 | P2 | identity | 0.0 | rot0 | 0.8953 | >10^4 |
| ftc_07-e2 | P3 | identity | 0.0 | rot0 | 3.17258 | >10^4 |
| ftc_07-e2 | W | identity | 0.0 | rot0 | 0.00841 | 5514.0 |
| ftc_08-e2 | P1 | rot3 | 1e-05 | rot7 | 1e-05 | 1.1 |
| ftc_08-e2 | P2 | identity | 0.0 | rot0 | 0.0 | 1.3 |
| ftc_08-e2 | P3 | identity | 0.0 | rot0 | 0.0 | 1.2 |
| ftc_08-e2 | W | identity | 0.0 | rot0 | 0.0 | 1.0 |
| ftc_09-e1 | P1 | rot3 | 1e-05 | rot7 | 1e-05 | 1.2 |
| ftc_09-e1 | P2 | rot0 | 0.0 | rot1 | 0.0 | 1.0 |
| ftc_09-e1 | P3 | identity | 0.0 | rot0 | 1.10725 | >10^4 |
| ftc_09-e1 | W | rot0 | 0.0 | rot5 | 0.0 | 1.0 |
| ftc_10-e2 | P1 | rot3 | 0.00032 | rot6 | 0.86717 | 2743.3 |
| ftc_10-e2 | P2 | identity | 0.00032 | rot0 | 0.00035 | 1.1 |
| ftc_10-e2 | P3 | identity | 0.0 | rot0 | 0.00032 | 189.6 |
| ftc_10-e2 | W | identity | 0.0 | rot0 | 0.00022 | 425.1 |
| ftc_11-e2 | P1 | rot7 | 0.00158 | rot11 | 0.00158 | 1.0 |
| ftc_11-e2 | P2 | identity | 0.0 | rot0 | 0.01066 | >10^4 |
| ftc_11-e2 | P3 | identity | 0.0 | rot0 | 0.0001 | 6803.1 |
| ftc_11-e2 | W | identity | 0.0 | rot0 | 4e-05 | 4992.7 |
| stc_06-e3 | P1 | rot3 | 1e-05 | rot7 | 0.73638 | >10^4 |
| stc_06-e3 | P2 | identity | 0.0 | rot0 | 0.0 | >10^4 |
| stc_06-e3 | P3 | identity | 0.0 | rot0 | 5.83581 | >10^4 |
| stc_06-e3 | W | identity | 0.0 | rot0 | 0.0 | >10^4 |
| stc_07-e3 | P1 | rot3 | 0.00841 | rot7 | 1.97446 | 234.7 |
| stc_07-e3 | P2 | identity | 0.0 | rot0 | 0.63 | >10^4 |
| stc_07-e3 | P3 | identity | 0.0 | rot0 | 3.85049 | >10^4 |
| stc_07-e3 | W | identity | 0.0 | rot0 | 0.00841 | 4643.3 |
| stc_08-e3 | P1 | rot3 | 1e-05 | rot7 | 1e-05 | 1.2 |
| stc_08-e3 | P2 | identity | 0.0 | rot0 | 0.0 | 1.3 |
| stc_08-e3 | P3 | identity | 0.0 | rot0 | 0.0 | 1.0 |
| stc_08-e3 | W | identity | 0.0 | rot0 | 0.0 | 1.3 |
| stc_09-e3 | P1 | rot3 | 1e-05 | rot7 | 1e-05 | 1.2 |
| stc_09-e3 | P2 | rot0 | 0.0 | rot1 | 0.0 | 1.0 |
| stc_09-e3 | P3 | rot0 | 0.0 | rot1 | 0.0 | 1.0 |
| stc_09-e3 | W | rot0 | 0.0 | rot4 | 0.0 | 1.0 |
| stc_10-e2 | P1 | rot3 | 0.00015 | rot6 | 0.69204 | 4694.1 |
| stc_10-e2 | P2 | identity | 0.0 | rot0 | 0.00014 | 193.9 |
| stc_10-e2 | P3 | identity | 0.0 | rot0 | 0.00015 | 48.7 |
| stc_10-e2 | W | identity | 0.0 | rot0 | 0.00015 | >10^4 |

Rows with gap ratio < 2 have winner and runner-up medians at or below the 1e-3 mm level (many exactly 0.0) — equivalent solutions on near-symmetric parts; distribution statistics agree under either candidate.

### S3b. Unaligned faces and partial-target annotations

Models with unaligned faces (all other models align at 100%); the 28 unmapped association targets and 17 partially-covered annotations of Section 6.2 concentrate on these faces.

| Model | Unaligned faces | Total faces | Alignment rate |
|---|---|---|---|
| ctc_05-e1 | 7 | 156 | 95.5% |
| stc_06-e3 | 4 | 144 | 97.2% |
| stc_10-e2 | 8 | 256 | 96.9% |

Per-annotation target lists are machine-readable in the archived audit outputs.

## S4. Measured versus not-measured boundary of the semantic parser

| Layer | Measured | Not measured (and why) |
|---|---|---|
| Top-level annotation inventory | All instances of the tolerance/dimension/datum entity families, simple and complex instances | Supporting entities (shape aspects, representation items) are traversed but not counted as annotations |
| Typed values | Dimensional values, PLUS_MINUS bands, tolerance-frame values, datum letters, datum references (DATUM_SYSTEM and WITH_DATUM_REFERENCE) | Tolerance modifiers (MMC/LMC), composite frame hierarchies — recorded verbatim, not typed |
| Association | GISU and IIRU chains via shape aspects (composite expansion, deriving relationships) to ADVANCED_FACE | Presentation-only DRAUGHTING links (recorded as the no-machine-readable-association class) |
| Anchoring | Face / edge (EDGE_CURVE) / whole part (PRODUCT_DEFINITION_SHAPE) / none | — |
| Round-trip equivalence | Numeric equality within 1e-9 for typed values | Empty-to-empty round-trips excluded from the equivalence rate |

## S5. Face-alignment ablation

| Variant | Aligned faces | Total faces | Rate |
|---|---|---|---|
| Full algorithm | 3824 | 3843 | 99.5% |
| noscale (no dual-scale self-calibration) | 2691 | 3843 | 70.0% |
| notype (no type/radius weighting) | 3824 | 3843 | 99.5% |

## S6. Measurability-threshold scan and window-width sensitivity

Threshold scan (share of the 1,866 nominal cylinders with at least t supporting points), derived post hoc from per-hole support counts:

| Pipeline | Regime | t=4 | t=8 | t=16 | t=32 | t=64 |
|---|---|---|---|---|---|---|
| P1 | A | 6.1 | 5.5 | 4.4 | 2.7 | 1.7 |
| P1 | B | 96.8 | 94.7 | 91.3 | 82.2 | 63.0 |
| P2 | A | 5.3 | 5.1 | 3.8 | 2.7 | 2.0 |
| P2 | B | 98.3 | 96.7 | 93.5 | 85.6 | 65.3 |
| P3 | A | 6.1 | 5.6 | 5.4 | 4.5 | 3.3 |
| P3 | B | 98.3 | 97.1 | 93.4 | 85.4 | 64.7 |
| W | A | 5.8 | 5.6 | 5.4 | 5.0 | 4.7 |
| W | B | 98.1 | 97.2 | 93.4 | 86.0 | 65.3 |

Window-width sensitivity (radial window ±15% → ±30%), measurable share (%):

| Pipeline | Regime | ±15% | ±30% |
|---|---|---|---|
| P1 | A | 5.5 | 6.6 |
| P1 | B | 94.7 | 96.1 |
| P2 | A | 5.1 | 6.2 |
| P2 | B | 96.7 | 97.2 |
| P3 | A | 5.6 | 7.0 |
| P3 | B | 97.1 | 97.3 |
| W | A | 5.6 | 8.4 |
| W | B | 97.2 | 97.3 |

## S7. Falsification experiment on P2's curve output (commands and log evidence)

Configuration: `omni.kit.converter.hoops_core` with `convertCurves: true` (default `false`), seven-model control batch including two AP242 models carrying both semantic and graphical PMI.

Exact invocation (from the archived batch driver `batch_curves.bat`, executed in `C:\omniverse\usd-convert-cad`):

```
py -3.12 convert.py "<model>.stp" "<out>\<model>.curves.usdc" --report "<out>\<model>.curves.report.json" --option convertCurves=true
```

Log evidence of activation and outcome (verbatim excerpts from `nist_ctc_02_asme1_ap242-e2.curves.run.log`):

```
[omni.converter.hoops_log]*status*HOOPS Converter version: 10.6.1
[omni.converter.hoops_log]*status*Parameters:
[omni.converter.hoops_log]*status*  convertCurves: true
...
[omni.converter.hoops_log]*status*Result:
[omni.converter.hoops_log]*status*  Total Meshes in USD = 1
[omni.converter.hoops_log]*status*  Total Triangles in USD = 11894
[omni.converter.hoops_log]*status*  Total Curves in USD = 0
```

Outcome: zero curve prims in every output; the byte-level difference of each `.usdc` against its default-setting counterpart is +12 to +48 bytes, attributable to file-name strings only. Interpretation: `convertCurves` governs B-rep wireframe curves; annotation geometry has no ingestion path in this converter — graphical PMI produces zero output under both settings. Batch artifacts (per-model `run.log`, `report.json`, and `.usdc`) are archived with the reproduction package (Data availability).

## S8. Independent-reader demonstration (full script)

```python
# Independent-consumer demonstration (Supplement S8). Reads profile semantics using only the public
# pxr API and the one-page convention (pmi:* attribute names, rel pmi:appliesTo, familyName=brepFace).
# Imports no module from this project and does not inspect the writer implementation.
# Code identical to the independent-reader script of the reproduction package; comments translated for the supplement.
# Usage: python independent_reader.py <stage.usdc>
import sys

from pxr import Usd, UsdGeom

stage = Usd.Stage.Open(sys.argv[1])
subsets = {p.GetPath(): p for p in stage.Traverse()
           if p.IsA(UsdGeom.Subset) and UsdGeom.Subset(p).GetFamilyNameAttr().Get() == "brepFace"}
print(f"units: metersPerUnit={UsdGeom.GetStageMetersPerUnit(stage)}, upAxis={UsdGeom.GetStageUpAxis(stage)}")
n = 0
for p in stage.Traverse():
    t = p.GetAttribute("pmi:type")
    if not t or not t.Get():
        continue
    n += 1
    rel = p.GetRelationship("pmi:appliesTo")
    subset_paths = {str(k) for k in subsets}
    faces = [str(x) for x in (rel.GetTargets() if rel else []) if str(x) in subset_paths]
    fields = {a: p.GetAttribute(f"pmi:{a}").Get() for a in
              ("value", "lowerBound", "upperBound", "datumLetter", "datumRefs", "dimName")
              if p.GetAttribute(f"pmi:{a}") and p.GetAttribute(f"pmi:{a}").Get() is not None}
    if n <= 5:
        print(f"[{t.Get()}] {p.GetName()}: {fields} -> faces={[f.split('/')[-1] for f in faces]}")
print(f"total annotations readable: {n}; face subsets present: {len(subsets)}")
```

## S9. Parameters of the geometry-only baselines (regimes D and D2)

Regime D (sequential RANSAC; `29_ransac_baseline.py` in the deposited archive): 40,000 area-weighted surface samples per model with triangle normals; per extraction round, 200 axis hypotheses from normal pairs (pairs with near-parallel normals, cross-product norm < 0.08, rejected); inlier criterion: radial deviation < 0.15 mm (tessellation linear deflection 0.1 mm plus margin) and |normal–axis cosine| < 0.25; clusters accepted at ≥ 15 inliers, refined with the same normal-covariance axis + Kåsa circle estimator as regime C2; extraction stops after 3 consecutive dry rounds or 400 rounds. Regime D2 (per-prim fitting; `30_perprim_baseline.py`): every mesh prim is fitted with the C2 estimator on its triangle vertices and classified as cylindrical when the radial residual RMS < 0.05 mm; window matching uses 2,000 area-weighted samples per accepted prim. Scoring for both is post hoc: a nominal cylinder counts as recovered when ≥ 8 of a detected cluster's points fall inside the nominal spatial window of Section 4.6 (10% axial trim, radial ±15%) — the extraction is asset-only, but this matching step uses source-side windows, so recovery rates are oracle-scored upper bounds (Section 6.4). Random seed 42 throughout.

D2 classifier-threshold sensitivity on P3 (RMS acceptance threshold scanned around the default 0.05 mm; the 0.02 mm setting sits below and 0.1/0.2 mm above the 0.1 mm tessellation deflection):

| RMS threshold (mm) | Recovered (%) | Median (mm) | p99 (mm) | Max (mm) |
|---|---|---|---|---|
| 0.02 | 99.0 | 3.6e-06 | 8.0 | 184.1 |
| 0.05 (default) | 99.7 | 3.5e-06 | 8.0 | 184.1 |
| 0.10 | 99.7 | 3.2e-06 | 8.0 | 184.1 |
| 0.20 | 99.7 | 3.6e-06 | 12.1 | 184.1 |

The recovery rate and the contaminated tail are insensitive to the classifier threshold across a 10× range; in particular the 184 mm worst cases persist at every setting.

Asset-side flaggability rule (Section 6.4; `31_flag_rule.py` / `32_flag_rule_p3.py`): angular coverage of the fitted arc, computed per face subset (W) or per accepted prim (P3) from asset-side information only; threshold 60°. On W it flags 93/1,866 cylinders (5.0%) and captures every radius error above 0.04 mm (unflagged maximum 0.037 mm; unflagged p99 0.0044 mm). On P3 it captures 6 of P3's 93 errors above 0.1 mm (a count that coincides numerically with the 93 flagged cylinders on W but is unrelated to it); the 184 mm cases present 180–350° of apparent coverage.

## S10. Unit resolution and the stage-only decision-closure demonstration

**Unit resolution.** Length values in AP242 are qualified by a unit context, and that context is not uniform across a file. Each measured value reaches the profile through `MEASURE_WITH_UNIT(LENGTH_MEASURE(v), #u)`; `#u` resolves either to `SI_UNIT(<prefix>, .METRE.)` or to `CONVERSION_BASED_UNIT('<name>', #k)`, where `#k` is itself a `LENGTH_MEASURE_WITH_UNIT` giving the factor to a base unit. The parser follows that chain numerically — it does not match on the unit's name — and records, per annotation, the factor to stage units together with the unit name. The writer multiplies value and both bounds by that factor and records the name as `pmi:sourceUnit`; the verbatim `pmi:step` record retains the unqualified source figure.

This is resolved **per annotation, not per file**. Over the 16 models the resolved units are millimetre only on 6 models (`ctc_01`, `ctc_02`, `ctc_04`, `ftc_10`, `ftc_11`, `stc_10`), inch only on 8 (`ctc_03`, `ctc_05`, `ftc_06`, `ftc_07`, `ftc_08`, `stc_06`, `stc_07`, `stc_09`), and **both units within a single part on 2** (`nist_ftc_09_asme1_ap242-e1`, 22 inch and 31 millimetre; `nist_stc_08_asme1_ap242-e3`, 36 inch and 1 millimetre). A per-file scale factor — for instance one inferred from the geometry — cannot be correct for those two. It is also silently wrong by 25.4× on three further models (`ctc_03`, `ftc_06`, `stc_06`) whose coordinates are millimetre-scaled while every one of their annotations is inch-denominated. The two properties are independent: only 5 of the 16 models are inch-scaled geometrically (`ctc_05`, `ftc_07`, `ftc_08`, `stc_07`, `stc_09`), whereas 10 carry at least one inch-denominated annotation — the inch-scaled set is a strict subset of the inch-denominated one, and five models are inch-denominated without being inch-scaled.

The audit does not take the factor from the writer's output. It re-reads it from the parsed source context and additionally checks that the unit name the stage declares agrees with the source; a stage whose values were converted with the wrong factor, or whose declared unit name disagrees, fails CF6. ⚠️ The limit of that check must be stated: writer and audit read the **same** parsed graph, so CF6 detects a writer-side arithmetic or naming error, not a misreading of the STEP file by the shared parser. The verbatim `pmi:step` record is retained precisely so a reader can audit the parse itself.

A length whose unit the chain cannot resolve is **not** silently treated as millimetres. The parser marks it, the writer authors `pmi:sourceUnit = UNRESOLVED`, and CF4 fails on it — converting a failed parse into a visible verdict rather than a passing one. The resolver covers `SI_UNIT` with a metre base and the usual decimal prefixes, and `CONVERSION_BASED_UNIT` chains that reduce numerically to such a base (depth ≤ 4); anything outside that is marked rather than assumed. No annotation in the NIST set is so marked.

**Decision-closure demonstration (Section 6.4).** Objects: annotation groups — one `DIMENSIONAL_SIZE` with a two-sided band, together with the cylindrical faces it reaches through `pmi:appliesTo` that carry an asset-only fitted radius (regime C3). Size semantics are read from `pmi:dimName`: `diameter` compares against twice the fitted radius, `radius` against the fitted radius; any other name is excluded rather than coerced. Verdict: `value + lowerBound ≤ measured ≤ value + upperBound`, with a declared numerical tie tolerance of 1e-05 mm — an excursion below that magnitude is numerical, not physical, and is counted as at-limit. Every input to the verdict is read from the stage; the STEP file is not consulted.

⚠️ **This is not an inspection of a manufactured part.** The fitted size returns the source nominal to a median of about 10⁻⁶ mm against bands of 0.0508–10.16 mm, because the mesh is a tessellation of the geometry the tolerance was authored against. The reported figure is a **closure rate**, not a pass rate.

Funnel (why the denominator is what it is):

| Stage | Count |
|---|---|
| Annotations on the delivered stages | 838 |
| of which `DIMENSIONAL_SIZE` | 212 |
| of which carrying a two-sided band | 149 (dropped: 63 single-sided or basic) |
| of which naming a diameter or radius | 130 (excluded: 19 thickness / curve length / spherical diameter) |
| reaching ≥1 cylindrical face with a fitted radius | **128** (dropped: 2) |
| face-level rows produced by those groups | 615 |

Result: **119 of 128 groups (92.97%) close cleanly**; at face level 585/615 (95.12%) inside band, of which 12 at-limit. The 9 groups that do not close are attributable as: source unit inconsistency 1 (4 faces); one annotation spanning faces of different size 5 (18 faces); tessellation 3 (8 faces).

⭐ **The source unit inconsistency, in full.** `nist_ftc_09` annotation `#9251` is `DIMENSIONAL_SIZE(#9230,'diameter')`; its value entity is `#9252 = (… MEASURE_WITH_UNIT(LENGTH_MEASURE(8.000000), #8506) …)` with bounds `±0.200` bound to the same unit, and `#8506 = (CONVERSION_BASED_UNIT('INCH', #8505) …)`, `#8505 = LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(25.4), #12)`. The unit chain resolves numerically and unambiguously to inch, so the profile carries 203.2 mm. The four faces the annotation reaches measure 8.001 mm and the part's coordinates span about 190 mm, so the stated feature cannot exist on it; read as millimetres the callout fits exactly. The model's other 21 inch-tagged annotations (22 carry an inch-resolved unit in total, `#9251` among them) convert correctly (for example `#8504`, 0.234 in → 5.9436 mm, matching its faces). We therefore report this as a defect in the source model, detected from the delivered scene alone.

Per-model closure (annotation groups):

| Model | Groups | Closed | Not closed |
|---|---|---|---|
| nist_ctc_01_asme1_ap242-e1 | 5 | 5 | 0 |
| nist_ctc_02_asme1_ap242-e2 | 7 | 7 | 0 |
| nist_ctc_03_asme1_ap242-e2 | 7 | 7 | 0 |
| nist_ctc_04_asme1_ap242-e1 | 3 | 3 | 0 |
| nist_ctc_05_asme1_ap242-e1 | 1 | 1 | 0 |
| nist_ftc_06_asme1_ap242-e2 | 10 | 10 | 0 |
| nist_ftc_07_asme1_ap242-e2 | 11 | 8 | 3 |
| nist_ftc_08_asme1_ap242-e2 | 9 | 9 | 0 |
| nist_ftc_09_asme1_ap242-e1 | 14 | 13 | 1 |
| nist_ftc_10_asme1_ap242-e2 | 13 | 13 | 0 |
| nist_ftc_11_asme1_ap242-e2 | 2 | 2 | 0 |
| nist_stc_06_asme1_ap242-e3 | 8 | 7 | 1 |
| nist_stc_07_asme1_ap242-e3 | 7 | 7 | 0 |
| nist_stc_08_asme1_ap242-e3 | 7 | 7 | 0 |
| nist_stc_09_asme1_ap242-e3 | 13 | 13 | 0 |
| nist_stc_10_asme1_ap242-e2 | 11 | 7 | 4 |
