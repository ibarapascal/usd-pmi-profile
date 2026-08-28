#!/bin/zsh
# 内部审 P0-1/P0-3 修复批：proto 重跑（含 C3 asset-only）＋全 48 组 WIN_R=0.30 窗口敏感性
set -u
cd "$(dirname "$0")/.."
ARC=archive/2026-jcde-cycle/pilot/out
for gj in out/e1/*ap242*.graph.json; do
  b=$(basename "$gj" .graph.json); [ "$b" = "nist_ftc_08_asme1_ap242-e1-tg" ] && continue
  CY="$ARC/batch_v3/${b}.cylinders.json"; GT="out/gt_area/${b}.xyz"
  .venv/bin/python scripts/19_hole_v2.py "out/proto_v2/${b}.usdc" "$CY" "$GT" "out/hole/${b}.proto.json" --subset 2>/dev/null | sed "s/^/[proto] /"
done
echo PROTO_C3_DONE
mkdir -p out/hole_win30
for gj in out/e1/*ap242*.graph.json; do
  b=$(basename "$gj" .graph.json); [ "$b" = "nist_ftc_08_asme1_ap242-e1-tg" ] && continue
  CY="$ARC/batch_v3/${b}.cylinders.json"; GT="out/gt_area/${b}.xyz"
  for pl in chainA omni proto; do
    case $pl in
      chainA) M="$ARC/batch_v4/${b}.chainA.usdc"; X="";;
      omni)   M="$ARC/batch_v2/omni/${b}.usdc"; X="";;
      proto)  M="out/proto_v2/${b}.usdc"; X="--subset";;
    esac
    O="out/hole_win30/${b}.${pl}.json"
    [ -f "$O" ] && continue
    HOLE_WIN_R=0.30 .venv/bin/python scripts/19_hole_v2.py "$M" "$CY" "$GT" "$O" $X 2>/dev/null | sed "s/^/[win30|$pl] /"
  done
done
echo WIN30_DONE
