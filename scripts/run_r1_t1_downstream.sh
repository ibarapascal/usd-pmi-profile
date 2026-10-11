#!/bin/zsh
# R1 修回 T1 下游（2026-10-05）：对 47 产出的每个网格化变体，用 r1b graph（out/e1，I-1＋I-7 修复后）走
#   15（写 stage）→16（CF1–CF7）→19 --subset（C3）→36（E11），回答「C3／E11 对网格化与网格器是否敏感」。
#   只读 <T1W>/out/t1/<variant>/*.faces.json（不写该目录）；输出 out/r1/t1/<variant>/，汇总 out/r1/t1/downstream_table.json。
#   变体之间互不依赖，按 PAR 并行（每变体内 16 件串行）。
# 用法: T1W=<t1t2t8 工作目录> PY=<python> PAR=4 zsh scripts/run_r1_t1_downstream.sh
set -eu
cd "$(dirname "$0")/.."
PY="${PY:-.venv/bin/python}"
T1W="${T1W:?need T1W}"
PAR="${PAR:-4}"
CYL="${V1_ARCHIVE:-archive/v1-pilot}/pilot/out/batch_v3"
OUT=out/r1/t1
mkdir -p "$OUT"

one_variant() {
  local v=$1 d=$OUT/$1
  mkdir -p "$d/hole"
  for gj in out/e1/*ap242*.graph.json; do
    local b=$(basename "$gj" .graph.json)
    [ "$b" = "nist_ftc_08_asme1_ap242-e1-tg" ] && continue
    local fj="$T1W/out/t1/$v/$b.faces.json"
    "$PY" scripts/15_usd_author_v2.py "$fj" "$gj" "out/e1/$b.match.json" "$d/$b.usdc" > /dev/null
    "$PY" scripts/16_audit_v2.py "$d/$b.usdc" "$gj" "$d/$b.audit_v2.json" "$fj" > /dev/null
    "$PY" scripts/19_hole_v2.py "$d/$b.usdc" "$CYL/$b.cylinders.json" "out/gt_area/$b.xyz" "$d/hole/$b.proto.json" --subset > /dev/null
  done
  "$PY" scripts/36_tolerance_judgement.py "$d" "$d/hole" "$d/tolerance_judgement.json" > "$d/36.log"
  echo "[t1-down] $v done"
}

variants=(${(f)"$(cd "$T1W/out/t1" && ls -d */ | tr -d / | grep -v -e '^summary$' -e '^match_rerun$')"})
for v in $variants; do
  ( one_variant $v > "$OUT/$v.down.log" 2>&1 || echo "[t1-down] $v FAILED" >> "$OUT/$v.down.log" ) &
  while [ $(jobs -r | wc -l) -ge $PAR ]; do sleep 2; done
done
wait

"$PY" - "$OUT" $variants <<'EOF'
import glob, json, os, sys
import numpy as np
out, variants = sys.argv[1], sys.argv[2:]
tab = {}
for v in variants:
    d = os.path.join(out, v)
    row = {}
    try:
        cf = {}
        for f in glob.glob(f"{d}/*.audit_v2.json"):
            for k, c in json.load(open(f))["cf"].items():
                cf.setdefault(k, []).append(bool(c.get("pass")))
        row["cf_pass_models"] = {k: f"{sum(x)}/{len(x)}" for k, x in sorted(cf.items())}
        e = []
        for f in glob.glob(f"{d}/hole/*.proto.json"):
            e += [r["abs_err"] for r in (json.load(open(f)).get("c3_rows") or []) if r.get("abs_err") is not None]
        e = np.array(e)
        row["c3"] = {"n": int(len(e)), "median": float(f"{np.median(e):.2g}"), "p99": round(float(np.percentile(e, 99)), 4),
                     "max": round(float(e.max()), 4), "n_gt_0.04": int((e > 0.04).sum())}
        tj = json.load(open(f"{d}/tolerance_judgement.json"))
        s = tj["summary"]
        row["e11"] = {k: s.get(k) for k in ("groups", "groups_clean", "groups_clean_pct", "faces", "faces_in_band", "at_limit_faces", "cause_by_group")}
        row["e11_incidents"] = [{k: g[k] for k in ("model", "stepId", "dimName", "faces", "cause")} for g in tj["groups"] if not g["clean"]]
    except Exception as ex:
        row["error"] = repr(ex)
    tab[v] = row
json.dump(tab, open(os.path.join(out, "downstream_table.json"), "w"), indent=1)
print(json.dumps({v: {"c3": r.get("c3"), "e11": (r.get("e11") or {}).get("groups_clean"), "cf": r.get("cf_pass_models"), "err": r.get("error")} for v, r in tab.items()}))
EOF
echo "R1_T1_DOWNSTREAM_DONE"
