#!/bin/bash
# E2 审计批：Mayo→glTF→guc 链（out/e2_mayo/*.usdc，Windows 侧转换，脚本 25）过全测量框架。
# ①26 语义/结构扫描 ②18 几何偏差（面积一致 GT）③19 孔径 A/B 口径。逐件串行防 OOM。
cd "$(dirname "$0")/.."
set -u
PY=.venv/bin/python
mkdir -p out/e2_audit
$PY scripts/26_e2_scan.py out/e2_audit/scan.json 2>&1 | tee out/e2_audit/scan.log
ARC=archive/2026-jcde-cycle/pilot/out
for gt in out/gt_area/*.xyz; do
  b=$(basename "$gt" .xyz)
  usd=out/e2_mayo/$b.usdc
  [ -f "$usd" ] || { echo "[skip] $b no usdc"; continue; }
  echo "=== $b geom ==="
  $PY scripts/18_measure_dirB.py "$gt" "$usd" out/e2_audit/$b.dirB.json
  cyl=$ARC/batch_v3/$b.cylinders.json
  if [ -f "$cyl" ]; then
    echo "=== $b hole ==="
    $PY scripts/19_hole_v2.py "$usd" "$cyl" "$gt" out/e2_audit/$b.hole.json
  fi
done
echo "E2 audit batch done"
