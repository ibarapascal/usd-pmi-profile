#!/bin/zsh
# E3 批量：16 模型 × {chainA, omni, proto_v2} × {面积一致 GT, v1 UV 网格 GT}——串行防 OOM，全部产物入 out/dirB/
set -u
cd "$(dirname "$0")/.."
ARC="${V1_ARCHIVE:-archive/v1-pilot}/pilot/out"
for gt_kind in area uv; do
  for gj in out/e1/*ap242*.graph.json; do
    b=$(basename "$gj" .graph.json)
    [ "$b" = "nist_ftc_08_asme1_ap242-e1-tg" ] && continue
    if [ "$gt_kind" = area ]; then GT="out/gt_area/${b}.xyz"; else GT="$ARC/batch_v2/${b}.gtv2.xyz"; fi
    [ -f "$GT" ] || { echo "NOGT $gt_kind $b"; continue; }
    for pl in chainA omni proto; do
      case $pl in
        chainA) M="$ARC/batch_v4/${b}.chainA.usdc";;
        omni)   M="$ARC/batch_v2/omni/${b}.usdc";;
        proto)  M="out/proto_v2/${b}.usdc";;
      esac
      O="out/dirB/${b}.${pl}.${gt_kind}.json"
      [ -f "$M" ] || { echo "NOMESH $pl $b"; continue; }
      [ -f "$O" ] && continue
      .venv/bin/python scripts/18_measure_dirB.py "$GT" "$M" "$O" 2>/dev/null | sed "s/^/[$b|$pl|$gt_kind] /"
    done
  done
done
echo E3_BATCH_DONE
