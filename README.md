# usd-pmi-profile

Specification, reference writer, and full-set audit for the paper *Tolerance-resolvable
OpenUSD: a minimal standards-only carrier profile for semantic PMI, its open implementation,
and validation on the NIST MBE test models* (submitted, 2026).

- **SPEC.md** — the one-page profile convention (face subsets, typed PMI, associations, units).
- **scripts/** — the complete pipeline: STEP entity-graph parser (13), STEP-face-to-mesh
  fingerprint alignment (14), profile writer (15), audits (16, 26), geometric ground truth and
  measurement (17, 18), hole-metrology regimes A/B/C/C2/C3 (19), the geometry-only baselines —
  regime D sequential RANSAC (29) and regime D2 per-prim fitting (30) — the asset-side
  flaggability rule and its P3 counter-check (31, 32), the stage-only tolerance judgement (36),
  aggregation to the numbers SSOT (20), and figures (27, 33, 34). Scripts 01/02/04/07/11 are
  the earlier batch that produced the archived P1 meshes and per-face inputs.
  Added in the first revision: the association cross-check against the CAx-IF validation
  properties (42) and a re-implementation of the NIST SFA association rules (50), the revision
  tables (43: unaligned faces, anchoring inventory, E11 re-attribution, unit census, float
  precision), stage overhead (44), the minimality ablation (45), the composition check (46),
  tessellation and topology robustness (47, 48), the P2 metadata re-conversion scan (49), the
  revision-number extractor (51), and a results-only verifier (54).
- **results/** — `canonical_numbers.json` (every number in the paper, keyed), the 64-row
  per-model registration table (`registration_table_v2.json`), the flaggability-rule outputs
  (`flag_rule.json`, `flag_rule_p3.json`), the E2 scan, the E8 ablation outputs, the
  stage-only tolerance judgements (`e11_tolerance_judgement.json`), the per-model audit outputs
  with their per-condition CF1–CF7 verdicts (`audit_per_model/`), and the human-readable digest.
  `results/r1/` holds the revision outputs behind the new numbers and supplementary tables
  (`canonical_r1.json`, the summary tables of each revision experiment, and the `usdchecker`
  log of the revised stages, `t13/usdchecker_r1b.log`).
- **figures/** — the paper's figures as generated.

## Reproduce

1. Data: download the NIST MBE PMI test models (public domain) —
   https://www.nist.gov/ctl/smart-connected-systems-division/smart-connected-manufacturing-systems-group/mbe-pmi-0
   — and place the 17 AP242 `.stp` files under `data/nist/`.
2. Environment: Python 3.13; `pip install -r requirements.txt`; FreeCAD 1.1.1 (headless
   `freecadcmd`) for scripts 14/17; Blender 5.0.1 for the import check (24).
3. Run order and per-script usage are documented in each script header; batch entry points are
   the `scripts/run_*.sh` files (`run_e9_batch.sh` runs the D/D2 baselines; `PRIM_RMS_TOL` scans the
   D2 classifier threshold). `scripts/20_aggregate_v2.py` regenerates
   `results/canonical_numbers.json`. After a change to unit handling or the writer, the
   minimal re-run is `scripts/run_unit_fix_rerun.sh` (parser → writer → audit only): the hole
   metrology and the geometry-only baselines read `pmi:surfaceType` and geometry, never
   `pmi:value`, so they are unaffected by the typed-value units.
4. Verification without FreeCAD or the NIST download: `python scripts/54_verify_results.py`
   re-derives the audit, association-target and E11 counts from the archived per-model outputs
   and re-runs the revision-number extractor (51) on `results/r1/`, asserting every frozen value.
   The revision re-runs are `scripts/run_r1_assoc_rerun.sh` (parser fix → writer → audit → E11
   → aggregation), `scripts/run_r1_t1t2.sh` and `scripts/run_r1_t1_downstream.sh` (tessellation
   and topology robustness, FreeCAD 1.1.1).
5. P2 (Omniverse) meshes are archived artifacts; re-conversion requires an Omniverse
   environment and the vendor's written permission (see the paper, Section 4.6). P3 conversion
   uses official prebuilt binaries of Mayo 0.10.0 and guc 0.5 (`scripts/25_e2_pcb_batch.ps1`).

## Cite

See CITATION.cff (GitHub "Cite this repository" button). Concept DOI: [10.5281/zenodo.22142164](https://doi.org/10.5281/zenodo.22142164) (always resolves to the latest version).

## License

MIT (LICENSE). The NIST test models are public domain and are not redistributed here.
