# usd-pmi-profile

Specification, reference writer, and full-set audit for the paper *A minimal standards-only
carrier profile for semantic PMI in OpenUSD: design, open implementation, and validation on
the NIST MBE test models* (submitted, 2026).

- **SPEC.md** — the one-page profile convention (face subsets, typed PMI, associations, units).
- **scripts/** — the complete pipeline: STEP entity-graph parser (13), STEP-face-to-mesh
  fingerprint alignment (14), profile writer (15), audits (16, 26), geometric ground truth and
  measurement (17, 18), hole-metrology regimes A/B/C/C2/C3 (19), the geometry-only baselines —
  regime D sequential RANSAC (29) and regime D2 per-prim fitting (30) — the asset-side
  flaggability rule and its P3 counter-check (31, 32), aggregation to the numbers SSOT (20),
  and figures (27). Scripts 01/02/04/07/11 are the earlier batch that produced the
  archived P1 meshes and per-face inputs.
- **results/** — `canonical_numbers.json` (every number in the paper, keyed), the 64-row
  per-model registration table (`registration_table_v2.json`), the flaggability-rule outputs
  (`flag_rule.json`, `flag_rule_p3.json`), the E2 scan, the E8 ablation outputs, and the
  human-readable digest.
- **figures/** — the paper's figures as generated.

## Reproduce

1. Data: download the NIST MBE PMI test models (public domain) —
   https://www.nist.gov/ctl/smart-connected-systems-division/smart-connected-manufacturing-systems-group/mbe-pmi-0
   — and place the 17 AP242 `.stp` files under `data/nist/`.
2. Environment: Python 3.13; `pip install -r requirements.txt`; FreeCAD 1.1.1 (headless
   `freecadcmd`) for scripts 14/17; Blender 5.0.1 for the import check (24).
3. Run order and per-script usage are documented in each script header; batch entry points are
   the `run_*.sh` files (`run_e9_batch.sh` runs the D/D2 baselines; `PRIM_RMS_TOL` scans the
   D2 classifier threshold). `scripts/20_aggregate_v2.py` regenerates
   `results/canonical_numbers.json`.
4. P2 (Omniverse) meshes are archived artifacts; re-conversion requires an Omniverse
   environment and the vendor's written permission (see the paper, Section 4.7). P3 conversion
   uses official prebuilt binaries of Mayo 0.10.0 and guc 0.5 (`scripts/25_e2_pcb_batch.ps1`).

## Cite

Citation metadata will be added on publication (CITATION.cff placeholder).

## License

MIT (LICENSE). The NIST test models are public domain and are not redistributed here.
