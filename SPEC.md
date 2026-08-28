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
  - `pmi:sourceUnit` (token): the length unit the source expressed this annotation in
    (e.g. `MILLIMETRE`, `INCH`) — provenance, see §4

## 3. Association

- Relationship `pmi:appliesTo` on the annotation prim, targeting one or more `brepFace`
  subsets (multi-target allowed).
- Edge-anchored annotations (e.g., linear distances between edges) do not fake a face
  association: they record `pmi:anchorKind = "edge"` and `pmi:edgeAnchorStepIds` (int[]) —
  an explicit extension point.
- Annotations with no machine-readable geometric association in the source (presentation-only
  links) carry `pmi:anchorKind = "none"`.

## 4. Units and up-axis

- `metersPerUnit` and `upAxis` are authored on the stage.
- **Every typed length (`pmi:value`, `pmi:lowerBound`, `pmi:upperBound`) is expressed in the
  stage's declared linear unit**, so a consumer may compare a tolerance against geometry
  without any conversion. This is the single most consequential rule on this page: a value
  left in its source unit on a stage declaring another is silently wrong by the ratio between
  them (25.4× for inch-on-millimetre).
- The conversion is resolved **per annotation** from the source unit context, not per file.
  In AP242 the chain is `MEASURE_WITH_UNIT(LENGTH_MEASURE(v), #u)` where `#u` is either
  `SI_UNIT(<prefix>, .METRE.)` or `CONVERSION_BASED_UNIT('<name>', #k)` with `#k` a
  `LENGTH_MEASURE_WITH_UNIT` giving the factor to a base unit; the factor is read numerically,
  not matched by name. A single part may mix units across its annotations — 2 of the 16 NIST
  models do — so a per-file scale factor is not a valid implementation of this rule.
- `pmi:sourceUnit` records the unit the source used, so the original figure remains
  recoverable; `pmi:step` retains the unqualified source record verbatim.

## 5. Conformance

A stage conforms if and only if the following hold. The first four are decidable from the
delivered stage alone; the last three additionally require the source part inventory.

**Stage-local well-formedness**

- **CF1** Every `UsdGeomSubset` in the `brepFace` family carries a `pmi:surfaceType` token.
- **CF2** Every annotation prim under the part's `PMI` scope carries `pmi:type` and `pmi:stepId`.
  The scope is named relative to the part, not by absolute path, so a conformant part stays
  conformant when referenced into an assembly.
- **CF3** Every prim declaring `pmi:anchorKind = "face"` carries a non-empty `pmi:appliesTo`;
  every `pmi:appliesTo` is non-empty and all its targets are `brepFace` subsets; every prim
  declaring `pmi:anchorKind = "edge"` also carries `pmi:edgeAnchorStepIds`.
- **CF4** The stage declares `metersPerUnit` and `upAxis`, and every annotation carrying a typed
  length also carries `pmi:sourceUnit` — and not the sentinel `UNRESOLVED`, which a writer must
  author when it cannot resolve the source unit rather than silently assuming stage units.

**Source-relative completeness**

- **CF5** Every B-rep face of the source appears as exactly one `brepFace` subset, and no subset
  lacks a source face.
- **CF6** Every semantic annotation of the source appears as exactly one prim under the part's
  `PMI` scope, and its typed fields equal the source values converted by that annotation's own
  source unit.
- **CF7** Every face-anchored annotation of the source carries a `pmi:appliesTo` whose targets are
  valid **and cover every one of its source target faces** — a relationship resolving to one face
  of a forty-face requirement satisfies CF3 but not CF7; every edge-anchored annotation is declared
  as such rather than being reshaped into a face association.

⚠️ **CF1–CF4 are universally quantified over what a stage contains, so a stage that authors no
subsets and no annotation prims satisfies all four vacuously.** Conformance states
well-formedness; it is never a substitute for content. A consumer using it as an acceptance
test must add its own non-emptiness requirement.

`scripts/16_audit_v2.py` evaluates CF1–CF7 and emits a per-condition verdict per model. It
discovers annotations **by attribute** (any prim carrying `pmi:type`), not by prim name or path,
so it scores a stage produced by any converter under any naming. It imports no code from the
writer and reads the delivered stage rather than writer-side state.

It is **not** independent of the STEP parser: writer and audit consume the same parsed entity
graph, so a parsing error is invisible to both. CF6's unit clause in particular compares against
the same conversion factor the writer used — it catches a writer-side arithmetic or naming error,
not a misreading of the source file. The verbatim `pmi:step` record exists so that a reader can
audit the parse itself.

## 6. Reading the profile (consumer contract)

A generic consumer needs only this page: enumerate subsets with `familyName == "brepFace"`;
enumerate prims carrying `pmi:type`; resolve `pmi:appliesTo` targets against the subset set.
A 24-line reference reader using only the public pxr API is `scripts/22_independent_reader_en.py`.

## 7. What the profile is not

Not a schema (no C1 addition), not a complete GD&T standard: tolerance modifiers (MMC/LMC),
composite frames, and assembly constraints are out of scope and belong to the
standardization agenda. The audit protocol (scripts/16, 19, 26) reserves positions for them.
