# E1 步骤一：STEP 实体引用图解析器 → typed PMI 抽取 + STEP 层 associativity（anno → ADVANCED_FACE ids）
# 设计 → notes/20260828-e1-design.md §1。姿态：collect-what-parses + 全量覆盖率报告，不 silent drop。
# 用法: python 13_step_graph.py <input.stp> <out.json>
import json
import re
import sys
from collections import Counter

stp, out = sys.argv[1], sys.argv[2]
txt = open(stp, encoding="utf-8", errors="replace").read()
# DATA 段；去换行（STEP 记录可跨行）
data = txt.split("DATA;", 1)[1].split("ENDSEC;", 1)[0]
flat = re.sub(r"\s+", " ", data)

# ---- 实体图：id -> list[(TYPE, argstr)]（简单实例 1 项，复合实例多项）----
graph, raw = {}, {}
for m in re.finditer(r"#(\d+)\s*=\s*(.+?);", flat):
    sid, body = int(m.group(1)), m.group(2).strip()
    raw[sid] = m.group(0)
    comps = []
    if body.startswith("("):  # 复合实例
        inner, depth, start = body[1:-1] if body.endswith(")") else body[1:], 0, None
        i = 0
        while i < len(inner):
            c = inner[i]
            if start is None and c.isalpha():
                start = i
            elif start is not None and c == "(" and depth == 0:
                typ = inner[start:i].strip()
                j, depth2, instr = i, 0, False
                while j < len(inner):
                    ch = inner[j]
                    if ch == "'" and not instr:
                        instr = True
                    elif ch == "'" and instr:
                        instr = False
                    elif not instr and ch == "(":
                        depth2 += 1
                    elif not instr and ch == ")":
                        depth2 -= 1
                        if depth2 == 0:
                            break
                    j += 1
                comps.append((typ, inner[i + 1:j]))
                i, start = j, None
            i += 1
    else:
        mm = re.match(r"([A-Z0-9_]+)\s*\((.*)\)$", body, re.S)
        if mm:
            comps = [(mm.group(1), mm.group(2))]
    if comps:
        graph[sid] = comps

def split_args(argstr):
    """顶层逗号切分（尊重括号与字符串）"""
    args, depth, instr, cur = [], 0, False, []
    for c in argstr:
        if c == "'" and not instr:
            instr = True
        elif c == "'" and instr:
            instr = False
        if not instr:
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            elif c == "," and depth == 0:
                args.append("".join(cur).strip()); cur = []
                continue
        cur.append(c)
    if cur:
        args.append("".join(cur).strip())
    return args

def types_of(sid):
    return {t for t, _ in graph.get(sid, [])}

def comp_args(sid, typ):
    for t, a in graph.get(sid, []):
        if t == typ:
            return split_args(a)
    return None

def refs_in(s):
    return [int(x) for x in re.findall(r"#(\d+)", s)]

def sstr(a):
    m = re.match(r"^'(.*)'$", a.strip())
    return m.group(1) if m else None

# ---- 单位上下文解析（2026-08-29 新增）----
# 背景：此前完全不解析单位，PMI 数值按源文件原样输出。NIST 集里存在**几何毫米而 PMI 英寸**的混合单位件
# （如 ctc_03 同时声明 CONVERSION_BASED_UNIT('MILLIMETRE') 与 ('inch')），用几何尺度换算会错 25.4×。
# 现按 STEP 自身的单位链数值化解析：MEASURE_WITH_UNIT(...,#u) → #u 递归求出「1 该单位 = ? 毫米」。
_SI_PREFIX_TO_MM = {"": 1000.0, "MILLI": 1.0, "CENTI": 10.0, "DECI": 100.0,
                    "MICRO": 0.001, "KILO": 1e6, "NANO": 1e-6}
_unit_memo = {}

def unit_to_mm(uid, depth=0):
    """返回 (1 单位 = ? 毫米, 单位名)；无法判定时返回 (None, None)。"""
    if uid in _unit_memo:
        return _unit_memo[uid]
    if depth > 4 or uid not in graph:
        return (None, None)
    res = (None, None)
    for t, a in graph[uid]:
        if t == "SI_UNIT":
            m = re.match(r"\s*\.?([A-Z]*)\.?\s*,\s*\.METRE\.", a)
            if m or ".METRE." in a:
                pre = (m.group(1) if m else "").strip(".")
                res = (_SI_PREFIX_TO_MM.get(pre), pre.title() + "metre" if pre else "Metre")
                break
        if t == "CONVERSION_BASED_UNIT":
            args = split_args(a)
            name = sstr(args[0]) if args else None
            # 第二参数指向 LENGTH_MEASURE_WITH_UNIT(LENGTH_MEASURE(f), #base)：f 个 base 单位＝1 本单位
            for r in (refs_in(args[1]) if len(args) > 1 else []):
                f, base = _measure_of(r)
                if f is None or base is None:
                    continue
                bs, _ = unit_to_mm(base, depth + 1)
                if bs is not None:
                    res = (f * bs, name)
                    break
            if res[0] is not None:
                break
    _unit_memo[uid] = res
    return res

def _measure_of(sid):
    """取实体自身（不展开引用）的 *_MEASURE(数值) 与随后的单位引用。"""
    for t, a in graph.get(sid, []):
        m = re.search(r"[A-Z_]*MEASURE\s*\(\s*([-\d.Ee+]+)\s*\)", a)
        if m:
            rest = a[m.end():]
            u = refs_in(rest)
            return float(m.group(1)), (u[0] if u else None)
    return None, None

def find_measure(sid, depth=0):
    """在实体（含引用展开）里找 (数值, 单位实体号)。"""
    if depth > 3 or sid not in graph:
        return None, None
    v, u = _measure_of(sid)
    if v is not None:
        return v, u
    for t, a in graph[sid]:
        for r in refs_in(a):
            v, u = find_measure(r, depth + 1)
            if v is not None:
                return v, u
    return None, None

def find_measure_value(sid, depth=0):
    """向后兼容的取值接口（丢弃单位）。"""
    return find_measure(sid, depth)[0]

def set_unit(rec, uid):
    """把该标注数值所用的长度单位记进 rec：unitName ＋ unitToMm（1 单位 = ? 毫米）。"""
    if uid is None or rec.get("unitToMm") is not None:
        return
    mm, name = unit_to_mm(uid)
    if mm is not None:
        rec["unitToMm"], rec["unitName"] = mm, (name or "UNKNOWN")

# ---- 索引：反向引用 ----
back = {}
for sid, comps in graph.items():
    for t, a in comps:
        for r in refs_in(a):
            back.setdefault(r, []).append(sid)

SUPPORT = {"PLUS_MINUS_TOLERANCE", "TOLERANCE_VALUE", "TOLERANCE_ZONE", "TOLERANCE_ZONE_FORM",
           "TOLERANCE_ZONE_DEFINITION", "GEOMETRIC_TOLERANCE_RELATIONSHIP"}
SA_LIKE = {"SHAPE_ASPECT", "COMPOSITE_SHAPE_ASPECT", "ALL_AROUND_SHAPE_ASPECT", "DATUM_FEATURE",
           "COMPOSITE_GROUP_SHAPE_ASPECT", "CONTINUOS_SHAPE_ASPECT", "CENTRE_OF_SYMMETRY",
           "APEX", "GEOMETRIC_ALIGNMENT", "PERPENDICULAR_TO", "PARALLEL_OFFSET", "TANGENT",
           "SYMMETRIC_SHAPE_ASPECT", "DERIVED_SHAPE_ASPECT"}

def shape_aspect_faces(sa_id, seen=None):
    """shape_aspect → GISU/IIRU/关系展开 → (ADVANCED_FACE ids, EDGE/其他几何 ids)"""
    if sa_id and isinstance(sa_id, tuple):
        sa_id, seen = sa_id  # 不会发生，防御
    if seen is None:
        seen = set()
    if sa_id in seen:
        return set(), set()
    seen.add(sa_id)
    faces, edges = set(), set()
    for user in back.get(sa_id, []):
        utypes = types_of(user)
        for usage in ("GEOMETRIC_ITEM_SPECIFIC_USAGE", "ITEM_IDENTIFIED_REPRESENTATION_USAGE"):
            if usage in utypes:
                args = comp_args(user, usage)
                # GISU: (name, desc, definition, used_rep, identified_item)
                # IIRU: (name, desc, definition, used_rep, SET_REPRESENTATION_ITEM((...)))
                if args and sa_id in refs_in(args[2]):
                    for r in refs_in(args[-1]):
                        if "ADVANCED_FACE" in types_of(r):
                            faces.add(r)
                        elif types_of(r):  # 边/顶点/曲线等非面锚定
                            edges.add(r)

        # DATUM_TARGET / DERIVING 关系：derived aspect → 原 aspect
        if "SHAPE_ASPECT_DERIVING_RELATIONSHIP" in utypes:
            a = comp_args(user, "SHAPE_ASPECT_DERIVING_RELATIONSHIP")
            if a and len(a) >= 4 and sa_id in refs_in(a[2]):
                for other in refs_in(a[3]):
                    f2, e2 = shape_aspect_faces(other, seen)
                    faces |= f2; edges |= e2
        # SHAPE_ASPECT_RELATIONSHIP: related/relating 展开（composite → 成员）
        if "SHAPE_ASPECT_RELATIONSHIP" in utypes or "COMPONENT_PATH_SHAPE_ASPECT" in utypes:
            for t, a in graph[user]:
                if "SHAPE_ASPECT_RELATIONSHIP" in t:
                    args = split_args(a)
                    if len(args) >= 4:
                        rel = refs_in(args[2]) + refs_in(args[3])
                        if sa_id in rel:
                            for other in rel:
                                if other != sa_id and (types_of(other) & SA_LIKE):
                                    f2, e2 = shape_aspect_faces(other, seen)
                                    faces |= f2; edges |= e2
    return faces, edges

# ---- 顶层标注枚举（与 09 同口径）----
annos = []
for sid, comps in graph.items():
    tset = {t for t, _ in comps}
    is_tol = any(t.endswith("_TOLERANCE") and t not in SUPPORT and not t.startswith("GEOMETRIC_TOLERANCE")
                 for t in tset) or (len(comps) > 1 and any("TOLERANCE" in t for t in tset) and not (tset <= SUPPORT))
    if "DATUM" in tset and "DATUM_FEATURE" not in tset and "DATUM_REFERENCE" not in " ".join(tset):
        annos.append((sid, "DATUM"))
    elif "DATUM_FEATURE" in tset:
        annos.append((sid, "DATUM_FEATURE"))
    elif "DIMENSIONAL_SIZE" in tset:
        annos.append((sid, "DIMENSIONAL_SIZE"))
    elif "DIMENSIONAL_LOCATION" in tset:
        annos.append((sid, "DIMENSIONAL_LOCATION"))
    elif is_tol:
        leaf = sorted(t for t in tset if t.endswith("_TOLERANCE") and t not in SUPPORT)
        annos.append((sid, leaf[-1] if leaf else "GEOMETRIC_TOLERANCE"))

# ---- typed 抽取 + associativity ----
result, cov = [], Counter()
for sid, kind in sorted(annos):
    rec = {"stepId": sid, "type": kind, "raw": raw.get(sid, "")[:2000]}
    tset = types_of(sid)
    if kind == "DATUM":
        args = comp_args(sid, "DATUM")
        rec["datumLetter"] = sstr(args[-1]) if args else None
        cov["datum_letter_ok" if rec.get("datumLetter") else "datum_letter_miss"] += 1
        result.append(rec); continue
    # 关联 shape_aspect 集合
    sa_ids = []
    if kind == "DATUM_FEATURE":
        sa_ids = [sid]  # datum_feature 自身是 shape_aspect
    elif kind in ("DIMENSIONAL_SIZE", "DIMENSIONAL_LOCATION"):
        args = comp_args(sid, kind)
        if args:
            if kind == "DIMENSIONAL_SIZE":  # (applies_to, name)
                sa_ids = refs_in(args[0])
            else:  # DIMENSIONAL_LOCATION: (name, description, relating_sa, related_sa)
                sa_ids = [r for a_ in args[2:4] for r in refs_in(a_)] if len(args) >= 4 else refs_in(" ".join(args))
        # 值：反向找 DIMENSIONAL_CHARACTERISTIC_REPRESENTATION
        for user in back.get(sid, []):
            if "DIMENSIONAL_CHARACTERISTIC_REPRESENTATION" in types_of(user):
                a = comp_args(user, "DIMENSIONAL_CHARACTERISTIC_REPRESENTATION")
                for r in refs_in(a[1] if a and len(a) > 1 else ""):
                    v, u = find_measure(r)
                    if v is not None:
                        rec["value"] = v
                        set_unit(rec, u)
        # 公差带：PLUS_MINUS_TOLERANCE
        for user in back.get(sid, []):
            if "PLUS_MINUS_TOLERANCE" in types_of(user):
                a = comp_args(user, "PLUS_MINUS_TOLERANCE")
                for r in refs_in(a[0] if a else ""):
                    tv = comp_args(r, "TOLERANCE_VALUE")
                    if tv and len(tv) >= 2:
                        lo, ul = find_measure(refs_in(tv[0])[0]) if refs_in(tv[0]) else (None, None)
                        hi, _ = find_measure(refs_in(tv[1])[0]) if refs_in(tv[1]) else (None, None)
                        rec["lowerBound"], rec["upperBound"] = lo, hi
                        set_unit(rec, ul)
        nm = comp_args(sid, kind)
        if nm:
            rec["dimName"] = sstr(nm[1] if kind == "DIMENSIONAL_SIZE" else nm[0])
        cov[f"{kind.lower()}_value_ok" if "value" in rec else f"{kind.lower()}_value_miss"] += 1
    else:  # 公差框
        # magnitude + toleranced_shape_aspect：取第一个 *_TOLERANCE 组件的标准 4 参数
        for t, a in graph[sid]:
            # 复合实例中空参数组件（如 FLATNESS_TOLERANCE()）可能排在前——遍历全部组件取有 4 参数者
            if "TOLERANCE" in t and t not in SUPPORT:
                args = split_args(a)
                if len(args) >= 4:
                    for r in refs_in(args[2]):
                        v, u = find_measure(r)
                        if v is not None:
                            rec["value"] = v
                            set_unit(rec, u)
                    sa_ids = refs_in(args[3])
                    break
        # datum 引用：候选=①公差组件第 5 个及以后参数（简单实例 DATUM_SYSTEM 列表）②*DATUM_REFERENCE* 组件参数；BFS ≤3 层收 DATUM 字母
        cands = []
        for t, a in graph[sid]:
            if "TOLERANCE" in t and t not in SUPPORT:
                args_ = split_args(a)
                for a_ in args_[4:]:
                    cands += refs_in(a_)
            if "DATUM_REFERENCE" in t:
                cands += refs_in(a)
        drefs, frontier, seen_d = [], list(cands), set()
        for _ in range(3):
            nxt = []
            for r in frontier:
                if r in seen_d or r not in graph:
                    continue
                seen_d.add(r)
                for t2, a2 in graph[r]:
                    if t2 == "DATUM":
                        dl = sstr(split_args(a2)[-1])
                        if dl:
                            drefs.append(dl)
                    if "DATUM" in t2 or "REFERENCE" in t2 or "SYSTEM" in t2:
                        nxt += refs_in(a2)
            frontier = nxt
        if drefs:
            rec["datumRefs"] = sorted(set(drefs))
        cov["tol_value_ok" if "value" in rec else "tol_value_miss"] += 1
        cov["tol_datum_ok" if drefs else "tol_datum_none"] += 1
    faces, edges = set(), set()
    for sa in sa_ids:
        f2, e2 = shape_aspect_faces(sa)
        faces |= f2; edges |= e2
    rec["faceIds"] = sorted(faces)
    if edges:
        rec["nonFaceAnchorIds"] = sorted(edges)
    if faces:
        rec["anchorKind"] = "face"
    elif edges:
        rec["anchorKind"] = "edge"
    elif any("PRODUCT_DEFINITION_SHAPE" in types_of(sa) for sa in sa_ids):
        rec["anchorKind"] = "part"   # 整件级锚定（如全体形状基准）——合法非面锚定
    else:
        rec["anchorKind"] = "none"   # 源文件中该 shape_aspect 仅有图形展示关联（DRAUGHTING），无 GISU/IIRU
    cov[f"assoc_{rec['anchorKind']}"] += 1
    result.append(rec)

summary = {"file": stp, "n_entities": len(graph), "n_annos": len(annos),
           "by_type": dict(Counter(k for _, k in annos)), "coverage": dict(cov)}
# 🔴 单位解析失败必须可见，不得静默按 1.0 处理：凡有 typed 长度却解不出单位者，
# 标记 unitName="UNRESOLVED"（unitToMm 留空）。writer 会照此写 pmi:sourceUnit，
# 审计器的 CF4 据此判失败——把「解析失败」从静默默认变成一次红。
_unresolved = 0
for _r in result:
    if any(_r.get(k) is not None for k in ("value", "lowerBound", "upperBound")) and _r.get("unitToMm") is None:
        _r["unitName"] = "UNRESOLVED"
        _unresolved += 1
summary["unit_unresolved"] = _unresolved

json.dump({"summary": summary, "annotations": result}, open(out, "w"), indent=1)
print(json.dumps(summary, indent=1))
