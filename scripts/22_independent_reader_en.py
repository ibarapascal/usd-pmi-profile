# Independent-consumer demonstration (Supplement S8). Reads profile semantics using only the public
# pxr API and the one-page convention (pmi:* attribute names, rel pmi:appliesTo, familyName=brepFace).
# Imports no module from this project and does not inspect the writer implementation.
# Code identical to scripts/22_independent_reader.py; comments translated for the supplement.
# Usage: python 22_independent_reader_en.py <stage.usdc>
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
