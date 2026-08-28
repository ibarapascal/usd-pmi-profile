# The minimal carrier profile for semantic PMI in OpenUSD — specification

Version 1.0 (2026-08-28). Companion to the paper *A minimal standards-only carrier profile
for semantic PMI in OpenUSD*. Every construct below is an already-standardized USD mechanism;
this document defines only their usage convention.

## 1. Face identity

- One `UsdGeomSubset` per B-rep face of the source model, child of the mesh prim.
- `familyName = "brepFace"`; `elementType = "face"`; indices cover the triangles tessellated
  from that face (per-face tessellation preserves the partition).
- Naming: `brepFace_<STEP ADVANCED_FACE id>` where the STEP-to-mesh alignment resolves
  (scripts/14), else `brepFace_u<occ index>`.
- Supplemental (free) faces are kept and named in the same family.
- Surface type token: attribute `pmi:surfaceType` (token) on the subset —
  one of `Plane | Cylinder | Cone | Sphere | Toroid | Other`. This is the enumeration basis
  for asset-only downstream measurement (regime C3 in the paper).

## 2. Typed PMI

- Scope prim `/​<Part>/PMI`; one prim per top-level semantic annotation.
- Attributes (authored only when the source provides a machine-readable value):
  - `pmi:type` (token): `dimensional_size | dimensional_location | position | flatness |
    perpendicularity | surface_profile | ... | datum | datum_feature` (categories as present
    in the source; the set used for the NIST models is in the paper, Section 6.2)
  - `pmi:value` (double), `pmi:lowerBound` (double), `pmi:upperBound` (double)
  - `pmi:datumLetter` (string), `pmi:datumRefs` (string[]), `pmi:dimName` (string)
  - `pmi:stepId` (int): source entity id — the audit anchor
  - `pmi:step` (string): verbatim source record — lossless fallback
- Units of `pmi:value` follow the stage's declared linear unit.

## 3. Association

- Relationship `pmi:appliesTo` on the annotation prim, targeting one or more `brepFace`
  subsets (multi-target allowed).
- Edge-anchored annotations (e.g., linear distances between edges) do not fake a face
  association: they record `pmi:anchorKind = "edge"` and `pmi:sourceEdgeIds` (int[]) —
  an explicit extension point.
- Annotations with no machine-readable geometric association in the source (presentation-only
  links) carry `pmi:anchorKind = "none"`.

## 4. Units and up-axis

- `metersPerUnit` and `upAxis` authored per the source declaration.

## 5. Reading the profile (consumer contract)

A generic consumer needs only this page: enumerate subsets with `familyName == "brepFace"`;
enumerate prims carrying `pmi:type`; resolve `pmi:appliesTo` targets against the subset set.
A 24-line reference reader using only the public pxr API is `scripts/22_independent_reader_en.py`.

## 6. What the profile is not

Not a schema (no C1 addition), not a complete GD&T standard: tolerance modifiers (MMC/LMC),
composite frames, and assembly constraints are out of scope and belong to the
standardization agenda. The audit protocol (scripts/16, 19, 26) reserves positions for them.
