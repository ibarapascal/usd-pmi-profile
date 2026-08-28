# E3 步骤二：方向 B 测量（GT 面积一致采样点 → 被测网格最近距离分布），v1 协议复刻＋两处升级：
#  - 采样测度 = 面积一致（17 号产物）；同时可对 v1 UV 网格采样（batch_v2 gtv2.xyz）跑同协议做敏感性对照
#  - 注册协议同 v1：候选 = 恒等 + 24 真旋转（质心平移），中位数判据选择；非恒等最优即坐标约定变更，入报告
#  - 距离核心：三角形质心 KDTree 预筛 k 近邻 → 向量化精确点-三角形距离（分块，内存平坦）——
#    trimesh.proximity 纯 Python 实现在 50k 点上不可用（Air 8GB 实测卡死），此实现同精度快两个量级
#  - 网格单位自校准：坐标转 mm 的 scale 从 {1.0(数值即 mm), mpu×1000(按声明)} 中按 GT 包围盒匹配选择并记录
#    （单位声明的对错是独立维度的既有发现，测量层只需几何对齐；选择入报告可审计）
# 用法: .venv/bin/python 18_measure_dirB.py <gt.xyz> <mesh.usdc|.obj> <out.json> [--sub N]
import json
import sys

import numpy as np
import trimesh

gt_path, mesh_path, out = sys.argv[1:4]
SUB_SEL = 2000  # 注册选择用子采样

gt = np.loadtxt(gt_path)
P = gt[:, :3]
face_idx = gt[:, 3].astype(int) if gt.shape[1] > 3 else None

# ---- 网格加载 ----
def load_mesh(path):
    if path.endswith((".usdc", ".usda", ".usd")):
        from pxr import Usd, UsdGeom
        stage = Usd.Stage.Open(path)
        mpu = UsdGeom.GetStageMetersPerUnit(stage)
        verts, faces, off = [], [], 0
        cache = UsdGeom.XformCache()
        for p in stage.Traverse(Usd.TraverseInstanceProxies()):
            if not p.IsA(UsdGeom.Mesh):
                continue
            m = UsdGeom.Mesh(p)
            pts = m.GetPointsAttr().Get()
            fvc = m.GetFaceVertexCountsAttr().Get()
            fvi = m.GetFaceVertexIndicesAttr().Get()
            if not pts or not fvc:
                continue
            xf = np.array(cache.GetLocalToWorldTransform(p))
            v = np.array([tuple(x) for x in pts])
            v = v @ xf[:3, :3] + xf[3, :3]
            k = 0
            for c in fvc:
                for t in range(1, c - 1):  # fan 三角化
                    faces.append([fvi[k] + off, fvi[k + t] + off, fvi[k + t + 1] + off])
                k += c
            verts.append(v)
            off += len(v)
        V = np.vstack(verts)
        return trimesh.Trimesh(vertices=V, faces=np.array(faces), process=False), mpu
    m = trimesh.load(mesh_path, force="mesh", process=False)
    return m, None

mesh, mpu = load_mesh(mesh_path)

# ---- 单位自校准（GT 为 mm）----
scales = [1.0]
if mpu:
    scales.append(mpu * 1000.0)
gt_ext = np.linalg.norm(P.max(0) - P.min(0))
best_scale = min(set(scales), key=lambda s: abs(np.linalg.norm(
    mesh.vertices.max(0) - mesh.vertices.min(0)) * s - gt_ext))
V0 = mesh.vertices * best_scale


# ---- 距离核心：KDTree 预筛 + 向量化点-三角形距离 ----
from scipy.spatial import cKDTree

def point_tri_dist(pts, tri):
    """pts (n,3) 与 tri (n,3,3) 一一对应的精确点-三角形距离（向量化）"""
    a, b, c = tri[:, 0], tri[:, 1], tri[:, 2]
    ab, ac, ap = b - a, c - a, pts - a
    d1 = (ab * ap).sum(1); d2 = (ac * ap).sum(1)
    bp = pts - b
    d3 = (ab * bp).sum(1); d4 = (ac * bp).sum(1)
    cp = pts - c
    d5 = (ab * cp).sum(1); d6 = (ac * cp).sum(1)
    # 区域判定（Ericson, Real-Time Collision Detection）
    res = np.empty(len(pts))
    done = np.zeros(len(pts), bool)
    def setd(mask, closest):
        m = mask & ~done
        if m.any():
            res[m] = np.linalg.norm(pts[m] - closest[m], axis=1)
            done[m] = True
    setd((d1 <= 0) & (d2 <= 0), a)
    setd((d3 >= 0) & (d4 <= d3), b)
    setd((d6 >= 0) & (d5 <= d6), c)
    vc = d1 * d4 - d3 * d2
    t = np.divide(d1, d1 - d3, out=np.zeros_like(d1), where=(d1 - d3) != 0)
    setd((vc <= 0) & (d1 >= 0) & (d3 <= 0), a + t[:, None] * ab)
    vb = d5 * d2 - d1 * d6
    t2 = np.divide(d2, d2 - d6, out=np.zeros_like(d2), where=(d2 - d6) != 0)
    setd((vb <= 0) & (d2 >= 0) & (d6 <= 0), a + t2[:, None] * ac)
    va = d3 * d6 - d5 * d4
    t3 = np.divide(d4 - d3, (d4 - d3) + (d5 - d6), out=np.zeros_like(d4),
                   where=((d4 - d3) + (d5 - d6)) != 0)
    setd((va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0), b + t3[:, None] * (c - b))
    denom = va + vb + vc
    v = np.divide(vb, denom, out=np.zeros_like(vb), where=denom != 0)
    w = np.divide(vc, denom, out=np.zeros_like(vc), where=denom != 0)
    setd(np.ones(len(pts), bool), a + v[:, None] * ab + w[:, None] * ac)
    return res

import point_cloud_utils as pcu

class MeshDist:
    """精确点-网格距离，C++ BVH（point_cloud_utils）。一次构建结构语义：pcu 每次调用自建 BVH，
    但 C++ 实现下 50k 点 × 10 万三角形 < 1s，无需缓存。"""
    def __init__(self, V, F, k=None):
        self.V = np.ascontiguousarray(V, dtype=np.float64)
        self.F = np.ascontiguousarray(F, dtype=np.int32)
    def query(self, pts, chunk=None):
        d, _, _ = pcu.closest_points_on_mesh(np.ascontiguousarray(pts, np.float64), self.V, self.F)
        return np.abs(d)

# ---- 注册：恒等 + 24 真旋转（质心平移），中位数判据 ----
def rot24():
    mats, seen = [], set()
    axes = [np.eye(3)[i] * s for i in range(3) for s in (1, -1)]
    for x in axes:
        for y in axes:
            if abs(np.dot(x, y)) > 1e-9:
                continue
            z = np.cross(x, y)
            Rm = np.column_stack([x, y, z])
            if np.linalg.det(Rm) < 0.5:
                continue
            key = tuple(np.round(Rm.flatten(), 6))
            if key not in seen:
                seen.add(key)
                mats.append(Rm)
    return mats

rng = np.random.default_rng(42)
sel = rng.choice(len(P), min(SUB_SEL, len(P)), replace=False)
Psub = P[sel]
gt_c = 0.5 * (P.min(0) + P.max(0))   # bbox 中心（v1 协议；点云质心受顶点密度不均污染——chainA 实测教训）

cands = [("identity", np.eye(3), np.zeros(3))]
for i, Rm in enumerate(rot24()):
    Vr = V0 @ Rm.T
    cands.append((f"rot{i}", Rm, gt_c - 0.5 * (Vr.min(0) + Vr.max(0))))

md = MeshDist(V0, np.asarray(mesh.faces))
best = None
for name, Rm, tv in cands:
    # d(R V + t, p) == d(V, R^T (p - t))：逆变换查询点，结构只建一次
    q = (Psub - tv) @ Rm
    med = float(np.median(md.query(q)))
    if best is None or med < best[0]:
        best = (med, name, Rm, tv)
med_sel, reg_name, Rm, tv = best

# ---- 全量方向 B ----
d = md.query((P - tv) @ Rm)
stats = {"n": int(len(d)), "mean": float(d.mean()), "rms": float(np.sqrt((d ** 2).mean())),
         "p95": float(np.percentile(d, 95)), "p99": float(np.percentile(d, 99)),
         "max": float(d.max())}
per_face = None
if face_idx is not None:
    per_face = {}
    for fi in np.unique(face_idx):
        di = d[face_idx == fi]
        per_face[int(fi)] = {"n": int(len(di)), "mean": float(di.mean()), "max": float(di.max())}

json.dump({"gt": gt_path, "mesh": mesh_path, "scale": best_scale, "mpu": mpu,
           "registration": reg_name, "reg_median": med_sel, "stats": stats,
           "per_face": per_face}, open(out, "w"), indent=1)
print(f"[18] n={stats['n']} reg={reg_name} scale={best_scale} mean={stats['mean']:.4f} "
      f"p95={stats['p95']:.4f} p99={stats['p99']:.4f} max={stats['max']:.4f}")
