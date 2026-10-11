# Online Resource 1 — Supplementary material

**Tolerance-resolvable OpenUSD: a minimal standards-only carrier profile for semantic PMI** — Supplements S1–S15.

## S1. Search protocol

Two rounds (July 2026; August 2026). Publication window 2016–2026; preprints included via arXiv. Sources: arXiv (cs.GR, cs.CE), Scopus-indexed journals, proceedings of the main graphics and engineering-informatics venues, and the AOUSD developer forum (site search).

Query families (each run with variants): "OpenUSD PMI", "USD GD&T", "CAD to USD semantic", "semantic PMI scene description", "PMI embedding visualization format", "GD&T derivative format", "MBD derivative format", "semantic annotation scene graph". AOUSD forum site queries: "PMI", "GD&T", "tolerance", "CAD metadata".

Round outcomes: no peer-reviewed quantitative treatment of semantic-PMI survival in CAD-to-USD ingestion was found in either round; the forum search returned no public PMI/GD&T support requests. The closest works found — the FreeCAD-Omniverse connector and the AP242/WebGL browser visualization — are cited and differentiated in Section 1 of the paper.

Round 3 (October 2026, during revision) had two aims. The first was an update of rounds 1–2 (OpenAlex, arXiv, Crossref, Google Scholar; Semantic Scholar, Springer, ScienceDirect, and Scopus search pages could not be accessed in this round); it found the stand-off annotation architectures cited in Section 2.2 and no published carrier for semantic PMI in USD. The second was a targeted search for an existing convention for B-rep face identity, topology, or PMI in USD:

| Source searched | Queries or scope | Outcome |
|---|---|---|
| AOUSD developer forum | "PMI", "STEP AP242", "B-rep", "product manufacturing information", "semantic CAD", "Geometry working group", "annotation", "engineering data", "digital twin CAD", "geomsubset CAD"; also "GeomSubset", "familyName", "face id" | No relevant thread; the GeomSubset threads concern material assignment and highlighting subsets in viewers |
| OpenUSD issue tracker | "CAD", "B-rep", "PMI", "boundary representation", "CAD kernel", "face partition", "GeomSubset CAD" | None |
| OpenUSD and AOUSD proposal repositories | Full list of proposals; issue search "CAD", "GeomSubset", "familyName", "B-rep" | No merged CAD, B-rep, or PMI proposal; under open review (pull requests #108 and #109, checked 9 October 2026): a B-rep schema, UsdSolid, from AOUSD's Geometry Working Group, which leaves B-rep–mesh correlation as an open question and defines no PMI; related: the semantic-labels schema and the profiles-and-capabilities mechanism (Sections 2.3 and 7.2) |
| AOUSD Core Specification 1.0.1 (public repository) | Full text: "B-rep", "PMI", "GeomSubset", "familyName", "tolerance" | No occurrence |
| NVIDIA converter documentation | hoops_core overview and usage, CAD-to-USD concept mapping, OBJ-to-USD concept mapping, Scene Optimizer operations | Subsets are documented for material and style grouping; source B-rep topology is not emitted; no face-identity convention |

Negative result: no convention for B-rep face identity or PMI in USD was found, and no B-rep topology schema has been merged. The nearest precedents are the material-binding use of `UsdGeomSubset` (the one family name OpenUSD reserves, `materialBind`) and NVIDIA's guidance to map OBJ groups to named subsets.

## S2. Archived P1/P2 artifacts: versions and generation commands

P1 (STEP-FreeCAD-OBJ-Blender-USD): FreeCAD 1.1.1 headless (`freecadcmd`), OpenCASCADE kernel, STEP import + OBJ export at linear deflection 0.1 mm; Blender 5.0.1 headless (`blender -b --python`), OBJ import + USD export, default settings. One command pair per model; scripts 01-02 of the archived pilot directory of the reproduction package.

P2 (Omniverse): omni.kit.converter.hoops_core 511.3.2, HOOPS Exchange 10.6.1, Kit SDK 110.1.1, default conversion settings, executed on a Windows RTX workstation; per-model logs archived. Quantitative results published with NVIDIA's written permission.

P3 (Mayo-glTF-guc): Mayo 0.10.0 (`mayo-conv --export <model>.glb <model>.stp`), guc 0.5 built against USD 25.11 (`guc <model>.glb <model>.usdc`), official prebuilt binaries; the batch driver script of the reproduction package and per-model log archived.

The documented options of these pipelines that bear on PMI, curves, or metadata, the values used, and the criteria of the output scan are listed in S11.


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

### S3b. Unaligned faces, the correctness of aligned pairs, and partial-target annotations

Models with unaligned faces (all other models align at 100%). The 28 unmapped association targets of Section 6.2 fall on 10 of these faces, all in `stc_06` and `stc_10`, and affect 17 annotations; the 7 unaligned faces of `ctc_05` are not the target of any annotation.

| Model | Unaligned faces | Total faces | Alignment rate |
|---|---|---|---|
| ctc_05-e1 | 7 | 156 | 95.5% |
| stc_06-e3 | 4 | 144 | 97.2% |
| stc_10-e2 | 8 | 256 | 96.9% |

**Distribution of the 19 unaligned faces.** For each unaligned OCC face we searched all STEP ADVANCED_FACE entities for one whose analytic surface (type, placement, radius) fits every tessellation vertex of the OCC face to within 10⁻³ mm.

| Model | OCC faces | Surface type | Mesh area (mm²) each | Twin STEP face | Vertices on twin's boundary | Twin radius (mm) |
|---|---|---|---|---|---|---|
| ctc_05-e1 | 29, 31, 33, 35 | Cone | 57.71 | #1340, #1342, #1344, #1346 | 1 | 3.969 |
| ctc_05-e1 | 78, 80, 82 | Cone | 105.18 | #1389, #1391, #1393 | 1 | 5.358 |
| stc_06-e3 | 32, 80 | Sphere | 2597.61 | #1945, #2840 | 1 | 15.875 |
| stc_06-e3 | 34, 39 | Cone | 36.93 | #1975, #2076 | 1 | 3.175 |
| stc_10-e2 | 55, 202, 204, 206, 208, 210 | Cone | 8.24 | #7039, #7186, #7188, #7190, #7192, #7194 | 1 | 1.5 |
| stc_10-e2 | 57, 59 | Cone | 27.71 | #7041, #7043 | 1 | 2.75 |

All 19 are cones (17) or spheres (2), and every one has exactly one geometric twin among the STEP faces; no twin has been assigned to another OCC face, so the failure is not a tie lost in the greedy assignment. Each twin's boundary carries a single STEP vertex (the single vertex of the closed circular edge of a cone, or the seam vertex of a sphere), so a vertex-set fingerprint has too little to score: since the twin was free, the pair can only have failed the candidate threshold (vertex-set Jaccard ≥ 0.34). All 19 could be recovered by matching analytic surfaces, a fallback this implementation does not include.

**Correctness of the 3,824 aligned pairs.** Surface types are compatible for all 3,824 pairs: 3,744 pairs have identical analytic types, and in the remaining 80 both faces are B-spline surfaces (on the STEP side, 75 written as simple and 5 as complex instances). For the 3,744 analytic pairs, the largest distance from the OCC face's tessellation vertices to the analytic surface of its assigned STEP face has a median of 3.4×10⁻¹³ mm; 3,578 pairs are within 10⁻³ mm, 3,735 within 0.01 mm, and all within 0.051 mm (the largest on a few cylinders and spheres of ftc_07, stc_07, ctc_04, and ftc_11). For the 80 B-spline pairs, the same distance, taken to the STEP B-spline surface itself, is at most 0.021 mm (33 pairs within 10⁻³ mm). An assignment to a different feature would leave a residual of millimeters, so no pair is a mismatch. Limit of this check: it confirms that both faces lie on the same analytic surface, so it cannot tell apart two faces that share one surface, such as the two half-cylinders of a hole; for those the vertex fingerprint is the only evidence.

Per-annotation target lists are machine-readable in the archived audit outputs.

## S4. Measured versus not-measured boundary of the semantic parser

| Layer | Measured | Not measured (and why) |
|---|---|---|
| Top-level annotation inventory | All instances of the tolerance/dimension/datum entity families, simple and complex instances | Supporting entities (shape aspects, representation items) are traversed but not counted as annotations |
| Typed values | Dimensional values, PLUS_MINUS bands, tolerance-frame values, datum letters, datum references (DATUM_SYSTEM and WITH_DATUM_REFERENCE) | Tolerance modifiers (MMC/LMC), composite frame hierarchies — recorded verbatim, not typed |
| Association | GISU and IIRU chains via shape aspects to ADVANCED_FACE, followed downward only: composite to members, and SHAPE_ASPECT_RELATIONSHIP / SHAPE_ASPECT_DERIVING_RELATIONSHIP from the relating to the related aspect, never back up to another composite that shares a member; for a DATUM_FEATURE, also the relationship to its DATUM, whose GISU carries the feature's geometry in 9 cases | Presentation-only DRAUGHTING links (recorded as the no-machine-readable-association class) |
| Anchoring | Face / edge (EDGE_CURVE and other curve entities) / whole part (PRODUCT_DEFINITION_SHAPE) / none | — |
| Round-trip equivalence | Numeric equality within 1e-9 for typed values | Empty-to-empty round-trips excluded from the equivalence rate |

### S4b. Anchoring inventory: every annotation that is not face-anchored or not typed

Of the 724 non-DATUM annotations, 697 are face-anchored. The other 27, and the 5 annotations without a typed value, are listed below with the source-side evidence for each class. STEP entity ids refer to the NIST files.

| Class | Count | Annotations (model: STEP id) | Source-side evidence |
|---|---|---|---|
| No machine-readable association in the source | 2 | ftc_06: #348; stc_08: #234 (both SURFACE_PROFILE_TOLERANCE) | The toleranced shape aspect and everything below it reach no GISU or IIRU entity; the only links are DRAUGHTING_MODEL_ITEM_ASSOCIATION presentation links. A genuine source-side gap. (The magnitude of stc_08 #234, 0.06, is the only millimeter-tagged value in an otherwise inch-denominated part; possibly a unit-tagging defect of the kind discussed in S10, not checked against a drawing, since only a 3D PDF is published for this part.) |
| Datum features whose association sits on the DATUM | 9 (face-anchored) | ctc_02: #79; ctc_03: #93, #95; ftc_06: #140, #141, #144, #145; stc_08: #446, #449 | Each DATUM_FEATURE relates to a DATUM through a SHAPE_ASPECT_RELATIONSHIP (relating = feature, related = datum), and the GISU naming the face is attached to that DATUM (e.g. ctc_02: `#469 = SHAPE_ASPECT_RELATIONSHIP('',$,#79,#128)`, `#661 = GEOMETRIC_ITEM_SPECIFIC_USAGE('','DATUM',#128,#1341,#2514)`, `#2514 = ADVANCED_FACE`). Followed by the parser (S4); the embedded affected area agrees with the face so obtained for all nine (within 0.15%) |
| Edge-anchored | 23 | ctc_04 3, ctc_05 6, ftc_06 4, ftc_09 3, ftc_10 6, stc_09 1 (DIMENSIONAL_LOCATION 10, DIMENSIONAL_SIZE 8, POSITION_TOLERANCE 4, STRAIGHTNESS_TOLERANCE 1) | The GISU names an EDGE_CURVE, TRIMMED_CURVE, or GEOMETRIC_CURVE_SET rather than a face; written as `pmi:anchorKind = edge` with the source ids (CF3(c)) |
| Whole part | 2 | ftc_07: #13917; ftc_10: #18511 (both SURFACE_PROFILE_TOLERANCE) | Associated with the PRODUCT_DEFINITION_SHAPE of the part |
| No typed value | 5 | ctc_01: #24, #25 (DIMENSIONAL_LOCATION), #126, #127 (DIMENSIONAL_SIZE); ctc_03: #269 (DIMENSIONAL_SIZE) | The annotation is referenced only by presentation links and a PROPERTY_DEFINITION; no DIMENSIONAL_CHARACTERISTIC_REPRESENTATION, i.e. no value entity, exists in the file |

Attribution: of the 11 annotations that a parser stopping at the DATUM_FEATURE would leave unlinked, 9 are a parser limitation (the association sits one relationship further, on the DATUM) and are resolved by the parser used here; 2 are genuine gaps in the source files.

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

Regime D (sequential RANSAC; `29_ransac_baseline.py` in the deposited archive): 40,000 area-weighted surface samples per model with triangle normals; per extraction round, 200 axis hypotheses from normal pairs (pairs with near-parallel normals, cross-product norm < 0.08, rejected); inlier criterion: radial deviation < 0.15 mm (tessellation linear deflection 0.1 mm plus margin) and |normal–axis cosine| < 0.25; clusters accepted at ≥ 15 inliers, refined with the same normal-covariance axis + Kåsa circle estimator as regime C2; extraction stops after 3 consecutive dry rounds or 400 rounds. Regime D2 (per-prim fitting; `30_perprim_baseline.py`): every mesh prim is fitted with the C2 estimator on its triangle vertices and classified as cylindrical when the radial residual RMS < 0.05 mm; window matching uses 2,000 area-weighted samples per accepted prim. Scoring for both is post hoc: a nominal cylinder counts as recovered when ≥ 8 of a detected cluster's points fall inside the nominal spatial window of Section 4.5 (10% axial trim, radial ±15%) — the extraction is asset-only, but this matching step uses source-side windows, so recovery rates are oracle-scored upper bounds (Section 6.4). Random seed 42 throughout.

D2 classifier-threshold sensitivity on P3 (RMS acceptance threshold scanned around the default 0.05 mm; the 0.02 mm setting sits below and 0.1/0.2 mm above the 0.1 mm tessellation deflection):

| RMS threshold (mm) | Recovered (%) | Median (mm) | p99 (mm) | Max (mm) |
|---|---|---|---|---|
| 0.02 | 99.0 | 3.6e-06 | 8.0 | 184.1 |
| 0.05 (default) | 99.7 | 3.5e-06 | 8.0 | 184.1 |
| 0.10 | 99.7 | 3.2e-06 | 8.0 | 184.1 |
| 0.20 | 99.7 | 3.6e-06 | 12.1 | 184.1 |

The recovery rate and the contaminated tail are insensitive to the classifier threshold across a 10× range; in particular the 184 mm worst cases persist at every setting.

Asset-side flaggability rule (Section 6.4; `31_flag_rule.py` / `32_flag_rule_p3.py`): angular coverage of the fitted arc, computed per face subset (W) or per accepted prim (P3) from asset-side information only; threshold 60°. On W it flags 93/1,866 cylinders (5.0%) and, on the delivered tessellation, captures every radius error above 0.04 mm (unflagged maximum 0.037 mm; unflagged p99 0.0044 mm); S12 shows that this completeness holds across OpenCASCADE deflections of 0.01–0.5 mm but not under a coarse setting or other meshers. On P3 it captures 6 of P3's 93 errors above 0.1 mm (a count that coincides numerically with the 93 flagged cylinders on W but is unrelated to it); the 184 mm cases present 180–350° of apparent coverage.

## S10. Unit resolution and the stage-only decision-closure demonstration

**Unit resolution.** Length values in AP242 are qualified by a unit context, and that context is not uniform across a file. Each measured value reaches the profile through `MEASURE_WITH_UNIT(LENGTH_MEASURE(v), #u)`; `#u` resolves either to `SI_UNIT(<prefix>, .METRE.)` or to `CONVERSION_BASED_UNIT('<name>', #k)`, where `#k` is itself a `LENGTH_MEASURE_WITH_UNIT` giving the factor to a base unit. The parser follows that chain numerically — it does not match on the unit's name — and records, per annotation, the factor to stage units together with the unit name. The writer multiplies value and both bounds by that factor and records the name as `pmi:sourceUnit`; the verbatim `pmi:step` record retains the unqualified source figure.

This is resolved **per annotation, not per file**. Over the 16 models the resolved units are millimeter only on 6 models (`ctc_01`, `ctc_02`, `ctc_04`, `ftc_10`, `ftc_11`, `stc_10`), inch only on 8 (`ctc_03`, `ctc_05`, `ftc_06`, `ftc_07`, `ftc_08`, `stc_06`, `stc_07`, `stc_09`), and **both units within a single part on 2** (`nist_ftc_09_asme1_ap242-e1`, 22 inch and 31 millimeter; `nist_stc_08_asme1_ap242-e3`, 36 inch and 1 millimeter). A per-file scale factor — for instance one inferred from the geometry — cannot be correct for those two. In `ftc_09` the millimeter tags are themselves a source defect (all 31 geometric-tolerance magnitudes, which NIST's drawing states in inches; see the evidence below); in `stc_08` the single millimeter value is the magnitude of #234 (S4b). It is also silently wrong by 25.4× on three further models (`ctc_03`, `ftc_06`, `stc_06`) whose coordinates are millimeter-scaled while every one of their annotations is inch-denominated. The two properties are independent: only 5 of the 16 models are inch-scaled geometrically (`ctc_05`, `ftc_07`, `ftc_08`, `stc_07`, `stc_09`), whereas 10 carry at least one inch-denominated annotation — the inch-scaled set is a strict subset of the inch-denominated one, and five models are inch-denominated without being inch-scaled.

The audit does not take the factor from the writer's output. It re-reads it from the parsed source context and additionally checks that the unit name the stage declares agrees with the source; a stage whose values were converted with the wrong factor, or whose declared unit name disagrees, fails CF6. The limit of that check must be stated: writer and audit read the **same** parsed graph, so CF6 detects a writer-side arithmetic or naming error, not a misreading of the STEP file by the shared parser. The verbatim `pmi:step` record is retained precisely so a reader can audit the parse itself.

A length whose unit the chain cannot resolve is **not** silently treated as millimeters. The parser marks it, the writer authors `pmi:sourceUnit = UNRESOLVED`, and CF4 fails on it — converting a failed parse into a visible verdict rather than a passing one. The resolver covers `SI_UNIT` with a metre base and the usual decimal prefixes, and `CONVERSION_BASED_UNIT` chains that reduce numerically to such a base (depth ≤ 4); anything outside that is marked rather than assumed. No annotation in the NIST set is so marked.

**Decision-closure demonstration (Section 6.4).** Objects: annotation groups — one `DIMENSIONAL_SIZE` with a two-sided band, together with the cylindrical faces it reaches through `pmi:appliesTo` that carry an asset-only fitted radius (regime C3). Size semantics are read from `pmi:dimName`: `diameter` compares against twice the fitted radius, `radius` against the fitted radius; any other name is excluded rather than coerced. Verdict: `value + lowerBound ≤ measured ≤ value + upperBound`, with a declared numerical tie tolerance of 1e-05 mm — an excursion below that magnitude is numerical, not physical, and is counted as at-limit. Every input to the verdict is read from the stage; the STEP file is not consulted.

**This is not an inspection of a manufactured part.** The fitted size returns the source nominal to a median of about 10⁻⁶ mm (the single-precision floor of the stored vertices, S12) against bands of 0.0508–10.16 mm, because the mesh is a tessellation of the geometry the tolerance was authored against. The reported figure is a **closure rate**, not a pass rate.

Funnel (why the denominator is what it is):

| Stage | Count |
|---|---|
| Annotations on the delivered stages | 838 |
| of which `DIMENSIONAL_SIZE` | 212 |
| of which carrying a two-sided band | 149 (dropped: 63 single-sided or basic) |
| of which naming a diameter or radius | 130 (excluded: 19 thickness / curve length / spherical diameter) |
| reaching ≥1 cylindrical face with a fitted radius | **128** (dropped: 2) |
| face-level rows produced by those groups | 599 |

Result: **122 of 128 groups (95.31%) close cleanly**; at face level 585/599 (97.66%) inside band, of which 12 at-limit. The 6 groups that do not close are attributable as: source unit inconsistency 1 (4 faces); one annotation spanning faces of different size 2 (2 faces); tessellation 3 (8 faces). All verdicts are computed on the tessellation W delivers (OpenCASCADE, linear deflection 0.1 mm); their sensitivity to tessellation and mesher is in S12.

| Model | Annotation | Nominal and band (mm) | Faces (out of band / in group) | Measured | Cause | Evidence |
|---|---|---|---|---|---|---|
| ftc_09 | #9251 diameter | 203.2, [198.12, 208.28] (8.000 ±0.200 tagged inch) | 4 / 4 | 8.001 | Source unit inconsistency | STEP entities and NIST drawing, below |
| stc_10 | #299 diameter | Ø10 | 1 / 5 (the face of a Ø6 hole, #249) | mixed | One annotation spanning faces of different size | The composite shape aspect the file assigns ('Radial Hole and Thread Callout') contains a member of another diameter; the re-implemented analyzer traversal (S14) yields the same face set |
| stc_10 | #307 diameter | Ø10 | 1 / 5 (the face of a Ø7 hole, #69) | mixed | One annotation spanning faces of different size | As above |
| ftc_07 | #15130, #15238, #15344 diameter | 6.35, [6.35, 6.4262] (0.250 +0.003/−0 in) | 2 / 2, 2 / 2, 4 / 4 | 6.349899 | Tessellation (1.01×10⁻⁴ mm below the lower limit) | Measured about the nominal axis without estimation, the vertices' mean radial distance is 3.174948 mm, matching the fitted 3.174949 mm; 72% of vertices lie radially inside the nominal surface (median offset −3.3×10⁻⁶ mm), the deepest by 1.96×10⁻⁴ mm. The deficit is in the delivered vertices, not the estimator |

**The source unit inconsistency, in full.** `nist_ftc_09` annotation `#9251` is `DIMENSIONAL_SIZE(#9230,'diameter')`; its value entity is `#9252 = (… MEASURE_WITH_UNIT(LENGTH_MEASURE(8.000000), #8506) …)` with bounds `±0.200` bound to the same unit, and `#8506 = (CONVERSION_BASED_UNIT('INCH', #8505) …)`, `#8505 = LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(25.4), #12)`. The unit chain resolves numerically and unambiguously to inch, so the profile carries 203.2 mm. The four faces the annotation reaches measure 8.001 mm and the part's coordinates span about 190 mm, so the stated feature cannot exist on it; read as millimeters the callout fits exactly. The model's other 21 inch-tagged annotations (22 carry an inch-resolved unit in total, `#9251` among them) convert correctly (for example `#8504`, 0.234 in → 5.9436 mm, matching its faces). We therefore report this as a defect in the source model, detected from the delivered scene alone.

The evidence that the defect originates in the reference file, and not in our conversion or interpretation, consists of three parts, each checkable without our code:

1. **The STEP file** (`nist_ftc_09_asme1_ap242-e1.stp`, header timestamp 2022-02-01). The following entities can be found with a text editor or `grep -n "LENGTH_MEASURE(8.000000)"` and `grep -n "^#8506="`:

   ```
   #8505=LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(25.4),#12);
   #8506= (CONVERSION_BASED_UNIT('INCH',#8505)LENGTH_UNIT()NAMED_UNIT(#10));
   #9251=DIMENSIONAL_SIZE(#9230,'diameter');
   #9252=(LENGTH_MEASURE_WITH_UNIT()MEASURE_REPRESENTATION_ITEM()MEASURE_WITH_UNIT(LENGTH_MEASURE(8.000000),#8506)REPRESENTATION_ITEM('nominal value'));
   #9255=LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(0.200000),#8506);
   #9256=LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(-0.200000),#8506);
   ```

   `#12` is the SI millimeter. No length value of 0.315 occurs anywhere in the file.

2. **NIST's drawing of FTC-09** (distributed with the test models [15]): the general notes state that units are inches and that values in square brackets are millimeters; the drawing dimensions the two holes as "2X Ø.315 ±.008 [8 ±0.2]", with the note "Dual units used for 2X Ø.315 holes". NIST's test-case definition describes the same callout as an 8 mm hole on an inch-based part. The STEP file therefore stores the bracketed millimeter value, 8 ±0.2, under the primary unit, inch.

3. **The geometry.** The four faces reached by #9251 measure Ø8.001 mm = 0.315 in. The 2023 STC-09 file, a simplified derivative of FTC-09 with the same geometry, encodes the same hole correctly as `LENGTH_MEASURE(0.315)` with an inch unit.

We found no record of this defect in NIST's project and download pages, the CAD-PMI-Testing repository, the release notes and issue tracker of NIST's STEP File Analyzer, or the CAx-IF resource pages (October 2026); NIST's README states that the files are not error-free reference files.

**A second unit defect in the same file, not detectable from the stage.** All 31 geometric-tolerance magnitudes of `ftc_09` are bound to `#12` (millimeter), while the drawing states them in inches. Example: `#10783=(GEOMETRIC_TOLERANCE('Position.36','',#10784, #9230) …)` with `#10784=LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(0.030000),#12)`, a position tolerance on the same feature `#9230` that the drawing gives as "⌀.030 [0.76]" — stored 25.4× too tight. A tolerance magnitude is not compared against measured geometry, and these magnitudes (0.008–0.260 mm) are plausible in millimeters, so neither the stage-only decision path nor a magnitude-plausibility rule flags them. Across the 16 files, a within-part disagreement between the units of dimensions and of tolerance magnitudes occurs only in `ftc_09` and `stc_08`; it is a hint, not a verdict, because a part may mix units legitimately.

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
| nist_stc_06_asme1_ap242-e3 | 8 | 8 | 0 |
| nist_stc_07_asme1_ap242-e3 | 7 | 7 | 0 |
| nist_stc_08_asme1_ap242-e3 | 7 | 7 | 0 |
| nist_stc_09_asme1_ap242-e3 | 13 | 13 | 0 |
| nist_stc_10_asme1_ap242-e2 | 11 | 9 | 2 |

## S11. Production-pipeline configurations and inspection criteria

**Configurations.** Versions and commands are in S2. Table S11a lists, per pipeline, the documented options that bear on PMI, curves, or metadata, the value used in the measured batch, and the non-default values that were also run.

| Pipeline | Components | Documented options bearing on PMI, curves, or metadata | Value in the measured batch | Also run with |
|---|---|---|---|---|
| P1 | FreeCAD 1.1.1 (OpenCASCADE) → OBJ → Blender 5.0.1 → USD | FreeCAD offers no STEP AP242 PMI import (stated in its issue tracker; no option exists). OBJ has no slot for PMI, units, or face identity. Blender's USD export creates a subset per material only | Linear deflection 0.1 mm; Blender import/export defaults | — |
| P2 | omni.kit.converter.hoops_core 511.3.2, HOOPS Exchange 10.6.1, Kit SDK 110.1.1 | `convertCurves` (B-rep wireframe curves; default false); `convertMetadata` (documented as importing metadata "including PMI" as USD attributes; default false) | Defaults | `convertCurves=true` on a seven-model batch (S7); `convertMetadata=true` on all 17 inputs (below) |
| P3 | Mayo 0.10.0 (`mayo-conv`) → glTF 2.0 → guc 0.5 (USD 25.11) | Mayo's STEP import parameters contain no PMI or annotation option (its annotation import exists only for DXF); glTF has no standardized PMI extension; guc documents no PMI handling | Defaults | — |

The vendor's own description of P2 agrees with the measurement: the converter's concept-mapping document states that it "does not author visible PMI geometry, dedicated PMI schemas, or editable CAD PMI semantics". Documentation consulted (accessed 5 October 2026): NVIDIA, usd-convert-cad `docs/concept_mapping.md` (v0.3.0), https://github.com/NVIDIA-Omniverse/usd-convert-cad/blob/main/docs/concept_mapping.md; NVIDIA, omni.kit.converter.hoops_core overview, https://docs.omniverse.nvidia.com/kit/docs/omni.kit.converter.hoops_core/latest/Overview.html; Blender manual, USD import/export, https://docs.blender.org/manual/en/latest/files/import_export/usd.html; FreeCAD issues #19795 and #29772, https://github.com/FreeCAD/FreeCAD/issues; Mayo wiki (supported formats; import parameters v0.10.0), https://github.com/fougue/mayo/wiki; guc README and documentation, https://github.com/pablode/guc.

**Inspection criteria, default configurations.** Every prim of every output is visited, instance proxies expanded. Attribute names and customData keys are matched case-insensitively against `toleran|datum|dimension|pmi|annotat|gdt` (for P3 also prim names), and every hit is inspected by hand; all hits are product names containing "PMI" (Section 6.1). A structural census of the 48 B-rep outputs (Table S11b) adds subsets, assetInfo, customData keys, and the authored string attributes.

| Pipeline | Files | Mesh prims | GeomSubsets | assetInfo entries | customData keys | Authored string attributes |
|---|---|---|---|---|---|---|
| P1 | 16 | 16 | 0 | 0 | `Blender` (16); `userDocBrief` (48, USD's built-in schema documentation) | Blender object and data names; `xformOpOrder`; `subdivisionScheme` |
| P2 | 16 | 21 | 0 | 0 | layer `creator` (16); `userDocBrief` (171) | `omni:hoops:material:name` (21); `info:id`; `orientation`; `xformOpOrder`; `subdivisionScheme` |
| P3 | 16 | 4,936 | 0 | 0 | `generator`, `version` (16 each); `userDocBrief` (5,240) | `subdivisionScheme`; `info:id`; `inputs:opacityMode` |

String values in these outputs are object, material, and shader names only.

**Inspection criteria, P2 with `convertMetadata=true`.** All 17 inputs were converted twice in the same session with the same converter build, once with `convertMetadata=true` and once at defaults, and the two outputs of each input were compared. The scan covers every authored attribute (name, type, and value), prim metadata (customData, assetInfo, and any other authored key), the layer's customLayerData, every relationship and its targets, and every GeomSubset. The keyword set is extended with GD&T terms (flatness, perpendicularity, parallelism, position, profile, runout, concentricity, symmetry, cylindricity, straightness, angularity) and symbols (±, Ø, ⌀, ⌖, ⏥, ⌓). An attribute is a *PMI hit* when its name or string value matches; a hit is *typed* when its value is numeric and attributable to a dimension, tolerance, or datum; it is *face-associated* when it sits on a GeomSubset or is linked to faces by a relationship. As a self-check, the scanner applied to the archived default outputs against themselves reports no difference.

| Measure | Value |
|---|---|
| Attributes added by `convertMetadata=true` (17 inputs) | 2,092 |
| PMI hits | 59, on 12 inputs, all on the part's root transform under `omni:hoops:metadata:` |
| Hits on a GeomSubset / hits with a relationship | 0 / 0 |
| GeomSubsets in the outputs | 0 |
| Numeric hits | 2, neither a tolerance value: an enumeration code (`GDT_STANDARD` = 5302, ctc_05) and a count (`numberofannotations` = 58, stc_09) |
| Content of the hits | Product-level metadata (STEP product name, identifier, description), the text of annotation notes (drawing notes), user-defined attribute strings |

No per-annotation dimension or tolerance value, tolerance type, datum reference, or annotation-to-face link appears in either configuration. The value-level scan was applied to P2 only; for P1 and P3 no documented option bears on PMI.

## S12. Sensitivity to tessellation, mesher, topology, and numerical precision

**Variants.** All 16 B-rep models were re-tessellated face by face under seven settings, reading the STEP file afresh for each: OpenCASCADE `tessellate` at linear deflections of 0.01, 0.05, 0.1 (the delivered setting), and 0.5 mm; a coarse setting of FreeCAD's standard mesher (linear deflection 0.5 mm, angular deflection 1.0 rad); Mefisto (maximum edge length calibrated to the triangle count of the delivered setting); and Netgen (fineness 2). For each variant the B-rep vertex fingerprints were recomputed after tessellation and the face alignment was re-run, and each variant then passed through the same authoring, audit (CF1–CF7), asset-only fitting (C3), and decision-closure steps as the delivered stages. The delivered variant reproduces the published C3 and decision-closure results exactly. Scripts `47_tess_sweep.py`, `48_topo_perturb.py`, and the downstream driver are in the deposited archive.

**Table S12a.** Face alignment and asset-only fitting (C3) under seven tessellations (3,843 faces; 1,866 nominal cylinders; errors in mm)

| Variant | Triangles | Fingerprints unchanged after tessellation | Alignment identical to delivered | C3 fitted | C3 median | C3 p99 | C3 max | Errors > 0.04 mm | of which flagged by the 60° rule |
|---|---|---|---|---|---|---|---|---|---|
| OCC, 0.01 mm | 3,921,948 | 3843/3843 | 16/16 | 1866 | 1.3e-6 | 0.0041 | 1.6915 | 4 | 4 |
| OCC, 0.05 mm | 1,314,638 | 3843/3843 | 16/16 | 1866 | 1.8e-6 | 0.0084 | 2.795 | 4 | 4 |
| **OCC, 0.1 mm (delivered)** | 1,256,800 | 3843/3843 | 16/16 | 1866 | 1.8e-6 | 0.0073 | 3.4709 | 4 | 4 |
| OCC, 0.5 mm | 1,163,450 | 3843/3843 | 16/16 | 1866 | 1.8e-6 | 0.0058 | 3.1808 | 4 | 4 |
| Coarse (0.5 mm, 1.0 rad) | 76,790 | 3843/3843 | 16/16 | 1866 | 4.8e-6 | 0.1761 | 4.7294 | 48 | 22 |
| Mefisto (equal triangle count) | 1,955,476 | 3843/3843 | 16/16 | 1854 | 4.0e-4 | 2.4215 | 94.93 | 325 | 44 |
| Netgen (fineness 2) | 625,622 | 3843/3843 | 16/16 | 1866 | 6.7e-5 | 0.1679 | 94952 (one degenerate fit) | 47 | 23 |

**Table S12b.** Conformance and decision closure under the same variants

| Variant | CF1, CF2, CF4, CF5, CF6 | CF3 | CF7 | Groups closed (of 128) | Faces in band (of 599) | Groups not closed |
|---|---|---|---|---|---|---|
| OCC, 0.01 / 0.05 / 0.1 / 0.5 mm | 16/16 | 15/16 | 14/16 | 122 | 585 | Tessellation 3 (ftc_07 #15130, #15238, #15344); unit 1 (ftc_09 #9251); mixed size 2 (stc_10 #299, #307) — identical group by group at all four deflections |
| Coarse | 16/16 | 15/16 | 14/16 | 124 | 591 | Tessellation 1 (stc_07 #14717); unit 1; mixed size 2 |
| Mefisto | 16/16 | 15/16 | 14/16 | 118 | 563 | Other 6 (four ftc_07 groups; stc_07 #14717, #14760); tessellation 1 (ctc_01 #121); unit 1; mixed size 2 |
| Netgen | 16/16 | 15/16 | 14/16 | 122 | 589 | Mixed size 4 (including ctc_01 #120, #121, misattributed: the fitted radii of equal-diameter faces scatter); tessellation 1 (stc_07 #14717); unit 1 |

Reading. Alignment and the CF1–CF7 verdicts do not depend on the tessellation: the fingerprints are computed on B-rep vertices. The asset-only fit does: on OpenCASCADE's strip-wise tessellation the C3 statistics and the decision-closure verdicts are stable from 0.01 to 0.5 mm, whereas under the coarse setting and the other two meshers the fit degrades (the axis is estimated from the triangle normals, and oblique triangles tilt it), the 60° rule captures only 14–49% of the errors above 0.04 mm, and the closure count moves between 118 and 124. The two source-side findings, the unit defect of ftc_09 and the mixed-size groups of stc_10, are found under all seven variants. The cause labels of the decision-closure step are rules calibrated on the delivered tessellation and become unreliable under other meshers (the Netgen misattribution above).

**Table S12c.** Topological and coordinate perturbation of the B-rep before alignment (alignment algorithm unchanged; 16 models)

| Variant | OCC faces | Matched | Unchanged faces keeping their STEP id | Unchanged faces re-assigned to another id | New faces: correct / unmatched / wrong id | Baseline STEP ids lost |
|---|---|---|---|---|---|---|
| None | 3843 | 3824 | 3824 (identical to delivered) | 0 | — | 0 |
| Periodic faces split in two | 6395 | 2290 | 1291 | 0 | 779 / 4105 / 220 | 1534 |
| Same-domain faces merged | 3307 | 3271 | 2234 | 4 | 1029 / 17 / 4 | 553 |
| Coordinates ±10⁻⁵ mm, rounding to 4 decimals | 3843 | 3644 | 3642 | 2 | — | 180 |
| Coordinates ±10⁻⁵ mm, rounding to 3 decimals | 3843 | 3724 | 3724 | 0 | — | 100 |
| Coordinates ±10⁻⁴ mm, rounding to 4 decimals | 3843 | 50 | 49 | 1 | — | 3774 |
| Coordinates ±10⁻⁴ mm, rounding to 3 decimals | 3843 | 3559 | 3559 | 0 | — | 265 |
| Coordinates ±10⁻³ mm, rounding to 4 decimals | 3843 | 0 | 0 | 0 | — | 3824 |
| Coordinates ±10⁻³ mm, rounding to 3 decimals | 3843 | 45 | 44 | 1 | — | 3779 |
| Rounding to 3 or 5 decimals, no perturbation | 3843 | 3824 | 3824 | 0 | — | 0 |

New faces count as correct when they receive the id of the face they came from. Coordinates were perturbed uniformly on the STEP side (fixed seed; scaled for inch-coordinate models). Reading: the fingerprint is guaranteed only when the tessellated B-rep and the STEP source are the same file. Splitting faces (one source face becomes several) is the main failure: 80.4% of the sub-faces stay unmatched, 15.3% recover their parent's id, and 4.3% (220, in 12 models) are assigned to a neighbouring face. Merging is mostly safe but not free of wrong assignments. Coordinate drift beyond the rounding precision turns most faces into non-matches, with at most 2 of 3,843 faces wrongly assigned.

**Table S12d.** Numerical floor of the asset-only fit (C3): the same algorithm applied to the same tessellation vertices at different storage precisions (1,715 nominal cylinders on the 14 models registered without recentering; ftc_09 and stc_09, which register under recentering, are excluded so that no registration transform enters)

| Vertex precision | Cylinders | Median abs. radius error (mm) | p99 (mm) | Max (mm) |
|---|---|---|---|---|
| Double precision (tessellation output) | 1715 | 2.0e-11 | 0.0073 | 3.450 |
| Single precision (cast) | 1715 | 2.36e-6 | 0.0073 | 3.471 |
| As delivered (single precision on the stage) | 1715 | 2.36e-6 | 0.0073 | 3.471 |

The single-precision cast reproduces the delivered result cylinder by cylinder, and double precision lowers the median by five orders of magnitude: the C3 median is set by single-precision vertex storage (spacing 3.8×10⁻⁶–3.05×10⁻⁵ mm at coordinates of 32–256 mm), not by measurement. The tail is unchanged and is a geometric and estimator property (the shallow-arc case of Section 6.4). The median here differs from the 1.8×10⁻⁶ mm of the full set of 1,866 because two models are excluded. Per model, the double-precision median is below 10⁻¹⁰ mm on 9 of the 14 and 1.4×10⁻⁶–1.1×10⁻⁴ mm on ctc_04, ftc_07, ftc_10, ftc_11, and stc_07.

## S13. Load and memory overhead of the semantic layer

Four variants of each of the 16 delivered stages, all written by the same export call: *full* (as delivered); *geom* (all annotation prims and `brepFace` subsets removed, mesh untouched); *weld_geom* (geom with vertices welded across face boundaries); *weld_full* (the welded mesh carrying the original subsets and annotation prims). Each (part, variant) was opened in 10 independent processes (usd-core 26.8, Python 3.13, single core, Apple M1 Max); times exclude `import pxr`, and memory is the peak resident set minus that of a process that only imports pxr. Medians over the 16 parts.

| Variant | File, MB (median / max) | Stage open, ms (median / max) | Read all arrays and attributes, ms (median / max) | World bounding box, ms | Resident memory increase, MiB (median / max) | Prims (median) |
|---|---|---|---|---|---|---|
| full | 0.68 / 1.68 | 4.99 / 6.54 | 9.04 / 18.3 | 0.23 | 11.4 / 15.0 | 286.5 |
| geom | 0.66 / 1.64 | 3.67 / 3.88 | 3.41 / 4.83 | 0.17 | 10.1 / 12.6 | 2 |
| weld_geom | 0.68 / 1.66 | 3.72 / 3.81 | 3.81 / 5.84 | 0.15 | 10.4 / 14.5 | 2 |
| weld_full | 0.70 / 1.68 | 5.16 / 6.65 | 9.58 / 19.4 | 0.23 | 11.6 / 15.5 | 286.5 |

Median per-part ratios full/geom: file 1.024 (at most 38 KiB more), stage open 1.37 (at most 3.0 ms more), resident memory 1.13 (at most 2.5 MiB more); reading every array and attribute takes 2.6× as long, the difference being the annotation strings themselves, which a consumer that does not read them does not pay for. The median interquartile range of the open time across the 10 repetitions is 0.48 ms for the full variant. Render frame time was not measured (usd-core contains no renderer).

Checks: the points, face-vertex indices, and face-vertex counts of *full* and *geom* are element-for-element identical on 16/16 parts. On *weld_full*, every triangle belongs to exactly one `brepFace` subset and `UsdGeom.Subset.ValidateFamily` passes on 16/16 parts: subsets partition triangles, not vertices, so the per-face vertex duplication of the delivered meshes (1.11–2.04×) is an implementation choice rather than a cost of the profile. Welding does not reduce the file size of a binary stage (weld_geom is 0.4% larger than geom).

## S14. Independent checks of association correctness

The audit of Section 5.5 scores the stage against the parsed source and therefore cannot detect a parser that resolves an association wrongly. Three references independent of the parser's traversal were used.

**(a) Validation properties embedded in the NIST files.** 12 of the 16 files (all except ftc_08–ftc_11) carry CAx-IF PMI validation properties written by the authoring CAD system (`PROPERTY_DEFINITION('pmi validation property', …)`), among them the *affected area* of each annotation and an *equivalent Unicode string* of the callout. A non-zero affected area linked to annotations is present in 7 of them (ctc_02, ctc_03, ctc_04, ftc_06, ftc_07, stc_07, stc_08): ctc_01, ctc_05, and stc_09 carry other properties only, the affected areas of stc_06 are all zero, and those of stc_10 could not be linked to annotations. Of the 128 groups of Section 6.4, 52 are therefore covered by (a), the 38 of ftc_08–ftc_11 by (c), and the other 38, in five files, by (b) alone. For each annotation, the affected area (converted to mm² through its unit) was compared with the summed mesh area of the faces our association reaches; a datum feature without a property of its own takes the property on the DATUM it relates to. The ±2% criterion is applied to the 283 annotations with a non-zero affected area (the 92 values of stc_06 are all zero).

| Annotations with a non-zero affected area | Within ±2% |
|---|---|
| All | 251 / 283 (88.7%) |
| Geometric tolerances | 137 / 137 |
| Datum features | 39 / 39 |
| Dimensional sizes | 62 / 90 |
| Dimensional locations | 13 / 17 |
| In the 128 groups of Section 6.4 | 52 / 52 |

The 32 that do not agree: 28 radius dimensions of stc_07, to which the file assigns one identical affected area (153.97 mm²) although each one's own GISU names a single face and the faces fall into five size classes; the four whose face is of that size agree to 0.01%, so the property is inconsistent on the reference side. One location dimension of ftc_07 (#15545), whose reference area equals twice the area of the face it names. Three location dimensions of ftc_06 (#149, #150, #151), whose reference areas are 4–200 times ours; unexplained, and not among the groups of Section 6.4. The equivalent Unicode strings state an instance count ("4X …") for only 13 annotations, all of which match the number of faces or connected face groups we associate; with so few, this serves as a side check only.

**(b) Re-implemented traversal of NIST's STEP File Analyzer.** We re-implemented, following the traversal rules of NIST's open-source STEP File Analyzer and Viewer (v5.51; `sfa-geom.tcl` and the entry points for dimensional sizes and locations, geometric tolerances, and datum features), the procedure that collects an annotation's associated geometry. Under those rules, a shape aspect's own GISU/IIRU is read only for non-composite aspects; SHAPE_ASPECT_RELATIONSHIP is followed only from relating to related; a composite related aspect is expanded one level to its members; the traversal never climbs to a parent; a datum feature reads the GISU on its DATUM. The implementation shares STEP tokenization with our parser but none of its traversal code. The parser's direction rule was itself aligned with these rules in this revision (Section 4.4), so (b) confirms the implementation of that rule rather than the rule.

| Comparison of face sets | Result |
|---|---|
| All 724 annotations other than DATUM entries | 724 / 724 identical (697 non-empty, 27 empty on both sides: 23 edge-anchored, 2 whole-part, 2 without a source link) |
| Edge entities, all 724 annotations | 724 / 724 identical |
| The 128 groups of Section 6.4 | 128 / 128 identical |
| The four files without validation properties (ftc_08–ftc_11) | 204 / 204 identical, including all 38 groups of Section 6.4 |

The two mixed-size groups of stc_10 (#299, #307) also contain a face of a different diameter under these rules; their attribution to the source rests on the composite each callout is assigned, which itself contains a member of the other diameter (S10).

**(c) NIST drawings for the four files without validation properties.** For ftc_08 (9 groups), ftc_09 (14), ftc_10 (13), and ftc_11 (2), the number of hole instances and the nominal value of each of the 38 groups of Section 6.4 were compared with the callouts on NIST's drawings: 38/38 agree. This checks instance counts and nominal values, not individual face identities, which a drawing cannot provide.

**Sensitivity to the traversal direction.** Following SHAPE_ASPECT_RELATIONSHIP in both directions instead of downward only lets an annotation climb, through a member shape aspect shared with another annotation's composite (for example a 'Feature Control Frame' aspect), into the sibling's faces. Applied to these files it enlarges the face sets of 79 annotations and moves two location dimensions of ftc_09 from their edges to faces, adding 2,318 targets in all; of the changed annotations that carry an affected area, none agrees with it under the bidirectional traversal (0 of 44) and 15 do under the corrected one, the other 29 being the cases of (a) that point to the reference side; the traversal rules of (b) never climb. The parser therefore follows relationships downward only (Section 4.4).

**Limit.** All three references read the association entities that the source file states. They establish that our parser reads those entities as NIST's tools and documents do; they cannot reveal an association that the source file itself states wrongly.

## S15. Composition check

An assembly stage references each of the 16 delivered parts once, each under its own translation and rotation about the z axis, and two parts (ctc_01, ftc_06) a second time: 18 instances. The composed stage and its flattened export were each read by attribute discovery, as in the independent reader of S8.

| Measure | Composed stage | Flattened stage | Sum over the instances read singly |
|---|---|---|---|
| Annotation prims | 929 | 929 | 929 |
| `brepFace` subsets | 4147 | 4147 | 4147 |
| `pmi:appliesTo` targets | 2763 | 2763 | 2763 |
| Targets outside their own instance | 0 | 0 | — |
| CF1, CF2, CF3(b) violationsᵃ | 0 | 0 | — |
| `ValidateFamily(brepFace)` failures | 0 / 18 | 0 / 18 | — |

ᵃ The check covers the reading path; the two CF3(a) failures of stc_06 (Section 5.5) are carried into the assembly unchanged.

Every instance agrees item by item with its part read singly; relationship targets are remapped by reference composition, so the two instances of one part each point to their own subsets. The assembly layer declares `metersPerUnit` = 0.001, as every part does. Under USD semantics a referenced layer's own `metersPerUnit` does not enter the composed stage, so an assembly of parts with different stage units must reconcile them in the assembly layer; this is a general constraint of USD, not one specific to the profile. The OpenUSD compliance checker is not available in the pip build of usd-core 26.8 used here; usdchecker (Apple USD Tools 0.24.3), run on the revised stages, passes on the 16 parts and on both the composed and the flattened stage.
