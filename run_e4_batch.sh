#!/bin/zsh
# E4 批量：16 模型 × {chainA, omni, proto(--subset)}，圆柱清单=batch_v3，GT=面积一致采样
set -u
cd "$(dirname "$0")/.."
ARC=archive/2026-jcde-cycle/pilot/out
for gj in out/e1/*ap242*.graph.json; do
  b=$(basename "$gj" .graph.json)
  [ "$b" = "nist_ftc_08_asme1_ap242-e1-tg" ] && continue
  CY="$ARC/batch_v3/${b}.cylinders.json"; GT="out/gt_area/${b}.xyz"
  [ -f "$CY" ] && [ -f "$GT" ] || { echo "SKIP $b"; continue; }
  for pl in chainA omni proto; do
    case $pl in
      chainA) M="$ARC/batch_v4/${b}.chainA.usdc"; X="";;
      omni)   M="$ARC/batch_v2/omni/${b}.usdc"; X="";;
      proto)  M="out/proto_v2/${b}.usdc"; X="--subset";;
    esac
    O="out/hole/${b}.${pl}.json"
    [ -f "$M" ] || { echo "NOMESH $pl $b"; continue; }
    [ -f "$O" ] && continue
    .venv/bin/python scripts/19_hole_v2.py "$M" "$CY" "$GT" "$O" $X 2>/dev/null | sed "s/^/[$pl] /"
  done
done
echo E4_BATCH_DONE
