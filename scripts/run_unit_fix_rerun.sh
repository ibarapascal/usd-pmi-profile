#!/bin/zsh
# 单位修复后的最小重跑（2026-08-29）：只重跑 writer(15) 与 audit(16)。
# 为什么只跑这两步：孔计量(19)与三组基线(29/30/31)经 grep 确认只读 pmi:surfaceType 与几何，
# 都不读 pmi:value —— 数值单位换算不影响任何几何/经验结果，故 E3/E4/E9 系全批无需重跑。
# 用法: ./scripts/run_unit_fix_rerun.sh
set -u
cd "$(dirname "$0")/.."
ARC="${V1_ARCHIVE:-archive/v1-pilot}/pilot/out"
n=0
for gj in out/e1/*ap242*.graph.json; do
  b=$(basename "$gj" .graph.json)
  [ "$b" = "nist_ftc_08_asme1_ap242-e1-tg" ] && continue
  .venv/bin/python scripts/15_usd_author_v2.py \
      "$ARC/proto/${b}.faces.json" "$gj" "out/e1/${b}.match.json" "out/proto_v2/${b}.usdc" \
      | sed "s/^/[$b] /"
  .venv/bin/python scripts/16_audit_v2.py \
      "out/proto_v2/${b}.usdc" "$gj" "out/e1/${b}.audit_v2.json" "$ARC/proto/${b}.faces.json" \
      | sed "s/^/[$b] /"
  n=$((n+1))
done
echo "UNIT_FIX_RERUN_DONE models=$n"
