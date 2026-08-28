#!/bin/zsh
# 修复后统一重跑：13 全集（公差组件 bug 修复）→ 15/16 重同步 → chainA E3 重测 → E4 全批
set -u
cd "$(dirname "$0")/.."
ARC="${V1_ARCHIVE:-archive/v1-pilot}/pilot/out"
NIST="${NIST_DIR:-data/nist}"   # NIST MBE PMI STEP files（README 指引下载后放 data/nist/）
for f in "$NIST"/nist_*_ap242-*.stp; do b=$(basename "$f" .stp); python3 scripts/13_step_graph.py "$f" "out/e1/${b}.graph.json" >/dev/null 2>&1; done
echo STEP13_DONE
for gj in out/e1/*ap242*.graph.json; do
  b=$(basename "$gj" .graph.json); [ "$b" = "nist_ftc_08_asme1_ap242-e1-tg" ] && continue
  .venv/bin/python scripts/15_usd_author_v2.py "$ARC/proto/${b}.faces.json" "$gj" "out/e1/${b}.match.json" "out/proto_v2/${b}.usdc" >/dev/null 2>&1
  .venv/bin/python scripts/16_audit_v2.py "out/proto_v2/${b}.usdc" "$gj" "out/e1/${b}.audit_v2.json" >/dev/null 2>&1
done
echo RESYNC_DONE
for gj in out/e1/*ap242*.graph.json; do
  b=$(basename "$gj" .graph.json); [ "$b" = "nist_ftc_08_asme1_ap242-e1-tg" ] && continue
  for kind in area uv; do
    if [ "$kind" = area ]; then GT="out/gt_area/${b}.xyz"; else GT="$ARC/batch_v2/${b}.gtv2.xyz"; fi
    O="out/dirB/${b}.chainA.${kind}.json"
    [ -f "$O" ] && continue
    .venv/bin/python scripts/18_measure_dirB.py "$GT" "$ARC/batch_v4/${b}.chainA.usdc" "$O" 2>/dev/null | sed "s/^/[chainA|$kind|$b] /"
  done
done
echo CHAINA_E3_DONE
./scripts/run_e4_batch.sh
