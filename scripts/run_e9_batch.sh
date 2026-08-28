#!/bin/bash
# E9/E9b 基线批：29（RANSAC regime D）+ 30（per-prim regime D2）逐管线；输入=P1/P2 存档网格＋P3 e2_mayo。
# 敏感性：PRIM_RMS_TOL 环境变量（D2 圆柱性阈值扫描，产物 out/e9b_rms{t}/，仅 P3 有意义）。
cd "$(dirname "$0")/.."
set -u
PY=.venv/bin/python
ARC="${V1_ARCHIVE:-archive/v1-pilot}/pilot/out"
mkdir -p out/e9 out/e9b
for gt in out/gt_area/*.xyz; do
  b=$(basename "$gt" .xyz)
  cyl=$ARC/batch_v3/$b.cylinders.json
  [ -f "$cyl" ] || continue
  for pl in chainA omni mayo; do
    case $pl in
      chainA) usd=$ARC/batch_v4/$b.chainA.usdc;;
      omni)   usd=$ARC/batch_v2/omni/$b.usdc;;
      mayo)   usd=out/e2_mayo/$b.usdc;;
    esac
    [ -f "$usd" ] || continue
    [ -f out/e9/$b.$pl.json ]  || $PY scripts/29_ransac_baseline.py "$usd" "$cyl" "$gt" out/e9/$b.$pl.json
    [ -f out/e9b/$b.$pl.json ] || $PY scripts/30_perprim_baseline.py "$usd" "$cyl" "$gt" out/e9b/$b.$pl.json
  done
done
echo E9-batch-done
