#!/bin/bash
# E8：面匹配消融批（S5）——noscale / notype 两变体全集重跑 14 号，产物 out/e8_ablation/
cd "$(dirname "$0")"
set -u
FC=/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd
STEP_DIR=../../.cache/usd-cad/nist/NIST-PMI-STEP-Files/NIST-PMI-STEP-Files
mkdir -p out/e8_ablation
for v in noscale notype; do
  for stp in "$STEP_DIR"/*.stp; do
    b=$(basename "$stp" .stp)
    [ "$b" = "nist_ftc_08_asme1_ap242-e1-tg" ] && continue
    ABLATE=$v "$FC" scripts/14_face_match.py "$stp" out/e8_ablation/$b.$v.json 2>/dev/null | grep "\[14\]"
  done
done
echo E8 done
