# Verify the archived results without FreeCAD, Omniverse or the NIST download (2026-10-05, R1).
# Runs inside the public repository / anonymized archive (reads results/ only, pure standard library):
#   A  E1 audit: re-sums the per-model audit outputs (results/audit_per_model/) and compares with
#      results/canonical_numbers.json (survival, typed round-trip, association rel_ok/rel_expected).
#   B  Association targets: target_pct recomputed from target_ok/target_total; target_total cross-checked
#      against the independent association cross-check (script 42 -> results/r1/t6b/).
#   C  E11: recounts groups / clean groups / faces from the per-group rows of
#      results/e11_tolerance_judgement.json and compares with the canonical keys.
#   D  Revision numbers: re-runs scripts/51_r1_keys.py on results/r1/ (every key asserted against its
#      frozen value inside 51) and checks the output is byte-identical to results/r1/canonical_r1.json.
# Usage (repository root): python scripts/54_verify_results.py      exit code 0 = all checks pass
import glob
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

os.chdir(Path(__file__).resolve().parent.parent)
assert Path("results/canonical_numbers.json").exists(), "run from the repository / archive root (needs results/)"
C = json.load(open("results/canonical_numbers.json"))
fails = []


def check(label, got, want):
    ok = got == want
    print(f"  {'ok ' if ok else 'FAIL'} {label}: {got}" + ("" if ok else f" (canonical {want})"))
    if not ok:
        fails.append(label)


print("[A] E1 audit (per-model outputs -> sums)")
sv = te = ro = fa = 0
audits = sorted(glob.glob("results/audit_per_model/*.audit_v2.json"))
for f in audits:
    d = json.load(open(f))
    sv += d["survive"]; te += d["typed_eq"]; ro += d["rel_ok"]; fa += d["anchor_face_expected"]
check("models", len(audits), 16)
check("e1.audit.survive", sv, C["e1.audit.survive"])
check("e1.audit.typed_eq", te, C["e1.audit.typed_eq"])
check("e1.audit.rel_ok", ro, C["e1.audit.rel_ok"])
check("e1.audit.rel_expected", fa, C["e1.audit.rel_expected"])
check("e1.audit.rel_pct", round(100 * ro / fa, 1), C["e1.audit.rel_pct"])

print("[B] association targets")
tk, tt = C["e1.audit.target_ok"], C["e1.audit.target_total"]
check(f"e1.audit.target_pct ({tk}/{tt})", round(100 * tk / tt, 1), C["e1.audit.target_pct"])
xc = json.load(open("results/r1/t6b/assoc_crosscheck.summary.json"))
check("target_total vs script 42 (downward-only targets)", xc["targets_down"], tt)
check("face-anchored annotations vs script 42", xc["face_anchored_down"], C["e1.anchor_face"])

print("[C] E11 stage-only tolerance judgement (per-group rows -> counts)")
e = json.load(open("results/e11_tolerance_judgement.json"))
g = e["groups"]
check("e11.groups", len(g), C["e11.groups"])
check("e11.groups_clean", sum(1 for x in g if x["clean"]), C["e11.groups_clean"])
check("e11.groups_pct", round(100 * sum(1 for x in g if x["clean"]) / len(g), 2), C["e11.groups_pct"])
check("e11.faces", sum(x["faces"] for x in g), C["e11.faces"])
check("e11.faces_in (summary)", e["summary"]["faces_in_band"], C["e11.faces_in"])

print("[D] revision numbers (script 51 on results/r1)")
with tempfile.TemporaryDirectory() as td:
    out = Path(td) / "canonical_r1.json"
    r = subprocess.run([sys.executable, "scripts/51_r1_keys.py"], capture_output=True, text=True,
                       env={**os.environ, "R1_DIR": "results/r1", "R1_OUT": str(out)})
    print("  " + (r.stdout.strip() or r.stderr.strip().splitlines()[-1]))
    if r.returncode != 0:
        fails.append("51")
    else:
        check("51 output byte-identical to results/r1/canonical_r1.json",
              out.read_bytes() == Path("results/r1/canonical_r1.json").read_bytes(), True)

print(f"[54] {'ALL PASS' if not fails else 'FAILED: ' + ', '.join(fails)}")
sys.exit(1 if fails else 0)
