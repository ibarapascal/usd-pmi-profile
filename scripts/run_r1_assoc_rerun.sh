#!/bin/zsh
# R1 修回 I-1（2026-10-05）：13 改为 SAR 下行展开后的语义链重跑 13→15→16→36→20。
# 为什么只跑这几步：19（孔计量）与 29–32（基线/可标记性）只读几何与 pmi:surfaceType，不读 pmi:appliesTo，
#   关联口径变化不影响它们（同 run_unit_fix_rerun.sh 的论证）；14（面匹配）不读标注。
# 先冻结 v4 产物到 out/r1/t6/v4-frozen/ 供逐键 diff；canonical 的 v4 冻结件另存 out/e1/canonical_numbers.v4-submitted.json。
# 用法: NIST_DIR=<STEP 目录> PY=<python> ./scripts/run_r1_assoc_rerun.sh
set -eu
cd "$(dirname "$0")/.."
PY="${PY:-.venv/bin/python}"
NIST="${NIST_DIR:-data/nist}"   # 默认同 run_redo_batch.sh（公开 repo README 约定）；本地缓存副本用 NIST_DIR 指定（2026-10-05 去本地路径）
ARC="${V1_ARCHIVE:-archive/v1-pilot}/pilot/out"
FZ=out/r1/t6/v4-frozen
if [ ! -d "$FZ" ]; then
  mkdir -p "$FZ/e1" "$FZ/proto_v2" "$FZ/e11"
  cp out/e1/*.graph.json out/e1/*.audit_v2.json "$FZ/e1/"
  cp out/proto_v2/*.usdc "$FZ/proto_v2/"
  cp out/e11/tolerance_judgement.json "$FZ/e11/"
fi
for stp in "$NIST"/*ap242*.stp; do
  b=$(basename "$stp" .stp)
  STEP_SAR_EXPAND=down "$PY" scripts/13_step_graph.py "$stp" "out/e1/${b}.graph.json" > /dev/null
  echo "[13] $b"
done
n=0
for gj in out/e1/*ap242*.graph.json; do
  b=$(basename "$gj" .graph.json)
  [ "$b" = "nist_ftc_08_asme1_ap242-e1-tg" ] && continue
  "$PY" scripts/15_usd_author_v2.py \
      "$ARC/proto/${b}.faces.json" "$gj" "out/e1/${b}.match.json" "out/proto_v2/${b}.usdc" | sed "s/^/[$b] /"
  "$PY" scripts/16_audit_v2.py \
      "out/proto_v2/${b}.usdc" "$gj" "out/e1/${b}.audit_v2.json" "$ARC/proto/${b}.faces.json" | sed "s/^/[$b] /"
  n=$((n+1))
done
"$PY" scripts/36_tolerance_judgement.py out/proto_v2 out/hole out/e11/tolerance_judgement.json
"$PY" scripts/20_aggregate_v2.py
echo "R1_ASSOC_RERUN_DONE models=$n"
