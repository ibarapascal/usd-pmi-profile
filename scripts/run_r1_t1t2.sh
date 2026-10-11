#!/bin/zsh
# R1 T1/T2 批跑入口（在 Mac 计算节点上经作业调度器提交；需 FreeCAD 1.1.1 —— 与基线 11/14 同版本，否则中止）。
# 目录约定（rsync 自 Mac）：$W/scripts/{14,47,48}*.py  $W/nist/*.stp  $W/cyl/*.cylinders.json  $W/e1match/*.match.json
# 输出：$W/out/t1/<variant>/<model>.faces.json（大，留节点复用）、$W/out/t1/summary/、$W/out/t1/match_rerun/、
#       $W/out/t2/<model>.t2.json；聚合表 $W/out/t1/t1_table.json 由 Mac 侧 .venv 跑 47 --aggregate。
# 用法: zsh run_r1_t1t2.sh <W> [t1|t2|both]
set -u
W=${1:?workdir}; WHAT=${2:-both}
FC=${FC:-/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd}   # 可用环境变量覆盖（计算节点上可指向工作目录内的 FreeCAD.app 副本）
V=$($FC --version 2>&1 | grep -o 'FreeCAD [0-9.]*' | head -1)
[ "$V" = "FreeCAD 1.1.1" ] || { echo "ABORT: need FreeCAD 1.1.1, got '$V'"; exit 3; }
cd $W
for stp in nist/*.stp; do
  b=$(basename $stp .stp); [ "$b" = "nist_ftc_08_asme1_ap242-e1-tg" ] && continue   # 无 B-rep，基线即排除
  if [ "$WHAT" != t2 ]; then
    if [ ! -f out/t1/summary/$b.json ]; then
      T1_STP=$PWD/$stp T1_OUT=$PWD/out/t1 T1_CYL=$PWD/cyl/$b.cylinders.json $FC scripts/47_tess_sweep.py 2>&1 | grep -E '^\[47\]|Error|Traceback'
    fi
    mkdir -p out/t1/match_rerun
    [ -f out/t1/match_rerun/$b.match.json ] || $FC scripts/14_face_match.py $PWD/$stp $PWD/out/t1/match_rerun/$b.match.json 2>&1 | grep -E '^\[14\]|Error'
  fi
  if [ "$WHAT" != t1 ] && [ ! -f out/t2/$b.t2.json ]; then
    T2_STP=$PWD/$stp T2_OUT=$PWD/out/t2 T2_BASE=$PWD/e1match/$b.match.json $FC scripts/48_topo_perturb.py 2>&1 | grep -E '^\[48\]|Error|Traceback'
  fi
done
echo RUN_R1_T1T2_DONE
