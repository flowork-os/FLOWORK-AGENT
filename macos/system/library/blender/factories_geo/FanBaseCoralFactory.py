# [FL_INDEX: keywords="blender_factory, procedural_3d, FanBaseCoralFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: FanBaseCoralFactory | Category: factories_geo
# Prompt: A white base mesh 3D model of a sea fan coral (gorgonian). The object reveals the raw geometric skeleton of a fan coral — numerous thin cylindrical branches extend upward from a shared base, bifurcating in a planar fan arrangement to form an open lattice network. Rendered without any texture or material color, the pure white mesh clearly exposes the branching hierarchy and overall fan silhouette, with complex shadows highlighting the open spaces within the branch network.

"""
Standalone Blender script – FanBaseCoralFactory, seed 0.
Run:  blender --background --python FanBaseCoralFactory.py

Fan coral: semicircular disc mesh → shortest-path tree → branching tubes.
  circle(512) → fill_grid → shape_by_angles → STUCCI displace
  → ShortestEdgePath → treeify → radius by descendants → geo_radius tubes.
"""




import bpy
import bmesh
import numpy as np
import math
from mathutils import Vector
from mathutils.noise import multi_fractal
from scipy.interpolate import interp1d
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from collections import deque

np.random.seed(0)


# ── Step 1: Create semicircular disc mesh ──────────────────────────────────

n_rings = 40       # radial divisions (center → edge)
n_angles = 80      # angular divisions over 180 degrees

bm = bmesh.new()

# Center vertex at bottom of fan
center = bm.verts.new((0, 0, 0))

# Ring vertices in polar grid, upright in XZ plane
# angle 0 = right (+x), angle pi/2 = top (+z), angle pi = left (-x)
ring_verts = []
for r in range(n_rings):
    ring = []
    radius = (r + 1) / n_rings
    for a in range(n_angles + 1):
        angle = a * math.pi / n_angles
        x = radius * math.cos(angle) + np.random.uniform(-0.005, 0.005)
        z = radius * math.sin(angle) + np.random.uniform(-0.005, 0.005)
        y = np.random.uniform(-0.005, 0.005)
        v = bm.verts.new((x, y, z))
        ring.append(v)
    ring_verts.append(ring)

bm.verts.index_update()

# Faces: center to first ring (triangles)
for a in range(n_angles):
    try:
        bm.faces.new([center, ring_verts[0][a], ring_verts[0][a + 1]])
    except ValueError:
        pass

# Quad faces between consecutive rings
for r in range(n_rings - 1):
    for a in range(n_angles):
        try:
            bm.faces.new([ring_verts[r][a], ring_verts[r][a + 1],
                          ring_verts[r + 1][a + 1], ring_verts[r + 1][a]])
        except ValueError:
            pass

# Triangulate for denser edge connectivity
bmesh.ops.triangulate(bm, faces=bm.faces[:])

# Transfer to Blender mesh
me = bpy.data.meshes.new("fan_disc")
bm.to_mesh(me)
bm.free()

obj = bpy.data.objects.new("FanDisc", me)
bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

print(f"  Disc mesh: {len(me.vertices)} verts, {len(me.edges)} edges")


# ── Step 2: Shape by angles (fan outline) ──────────────────────────────────
# Narrow the fan at the horizontal edges for a natural fan shape

edge_scale_L = np.random.uniform(0.3, 0.7)
edge_scale_R = np.random.uniform(0.3, 0.7)
angles_ref = np.array([0, math.pi / 2, math.pi])
scales_ref = np.array([edge_scale_R, 1.0, edge_scale_L])
shape_fn = interp1d(angles_ref, scales_ref, kind='quadratic',
                     bounds_error=False, fill_value=0.0)

for v in me.vertices:
    vx, vy, vz = v.co
    dist = math.sqrt(vx ** 2 + vz ** 2)
    if dist < 1e-6:
        continue
    angle = math.atan2(vz, vx)
    if angle < 0:
        angle += math.pi
    scale = max(0.05, float(shape_fn(angle)))
    ratio = scale
    v.co.x *= ratio
    v.co.z *= ratio


# ── Step 3: STUCCI displacement ────────────────────────────────────────────
# Strong Y displacement for organic depth waviness (matches original fan.py)

tex = bpy.data.textures.new("fan_stucci", type='STUCCI')
tex.noise_scale = np.random.uniform(0.5, 1.0)
m_disp = obj.modifiers.new("Displace", "DISPLACE")
m_disp.texture = tex
m_disp.strength = np.random.uniform(0.5, 1.0)
m_disp.direction = 'Y'
bpy.ops.object.modifier_apply(modifier="Displace")


# ── Step 3b: geo_extension – radial Musgrave noise for outline irregularity ──

noise_str = np.random.uniform(0.1, 0.2)
noise_scl = np.random.uniform(1.4, 2.8)
dir_jitter = Vector(np.random.uniform(-1, 1, 3).tolist())

for v in me.vertices:
    pos = Vector(v.co)
    if pos.length < 1e-6:
        continue
    direction = pos.normalized() + dir_jitter
    sample = direction * noise_scl
    n = (multi_fractal(sample, 1.0, 2.0, 2) + 0.25) * noise_str
    v.co += pos * n


# X-scale variation
sx = np.random.uniform(0.6, 1.2)
obj.scale.x *= sx
bpy.ops.object.transform_apply(scale=True)

me = obj.data


# ── Step 4: Extract mesh graph ─────────────────────────────────────────────

n_v = len(me.vertices)
coords = np.zeros((n_v, 3))
for i, v in enumerate(me.vertices):
    coords[i] = v.co[:]

edge_list = np.array([(e.vertices[0], e.vertices[1]) for e in me.edges])
n_e = len(edge_list)

lengths = np.linalg.norm(coords[edge_list[:, 0]] - coords[edge_list[:, 1]], axis=1)

# Randomize weights: 40-100% of edge length (key for organic branching)
rand_w = np.random.uniform(0.4, 1.0, n_e) * np.maximum(lengths, 1e-8)

# Build symmetric sparse adjacency
row = np.concatenate([edge_list[:, 0], edge_list[:, 1]])
col = np.concatenate([edge_list[:, 1], edge_list[:, 0]])
data = np.concatenate([rand_w, rand_w])
graph = csr_matrix((data, (row, col)), shape=(n_v, n_v))

print(f"  Graph: {n_v} verts, {n_e} edges")


# ── Step 5: Choose bottom endpoints ────────────────────────────────────────

z_coords = coords[:, 2]
z_min, z_max = z_coords.min(), z_coords.max()
z_range = z_max - z_min
x_abs = np.abs(coords[:, 0])

mask = (z_coords < z_min + 0.03 * z_range) & (x_abs < 0.15)
candidates = np.where(mask)[0]

if len(candidates) < 3:
    mask = (z_coords < z_min + 0.08 * z_range) & (x_abs < 0.3)
    candidates = np.where(mask)[0]

n_ep = min(5, max(1, len(candidates)))
endpoints = np.random.choice(candidates, n_ep, replace=False)

print(f"  Endpoints: {n_ep}")


# ── Step 6: Multi-source Dijkstra ──────────────────────────────────────────

n_total = n_v + 1
vid = n_v

ext_row = np.concatenate([row,
                          np.full(n_ep, vid, dtype=np.intp),
                          endpoints.astype(np.intp)])
ext_col = np.concatenate([col,
                          endpoints.astype(np.intp),
                          np.full(n_ep, vid, dtype=np.intp)])
ext_data = np.concatenate([data,
                           np.full(n_ep, 1e-10),
                           np.full(n_ep, 1e-10)])
ext_graph = csr_matrix((ext_data, (ext_row, ext_col)), shape=(n_total, n_total))

_, pred_arr = dijkstra(ext_graph, directed=False, indices=vid,
                       return_predecessors=True)

pred = pred_arr[:n_v].copy()
for ep in endpoints:
    pred[ep] = -9999
pred[pred == vid] = -9999

reachable = np.sum((pred >= 0) | (pred == -9999))
print(f"  Reachable: {reachable}/{n_v}")


# ── Step 7: Build tree, count descendants ──────────────────────────────────

children = [[] for _ in range(n_v)]
for v in range(n_v):
    p = pred[v]
    if 0 <= p < n_v and p != v:
        children[p].append(v)

# Bottom-up BFS to count descendants
desc_count = np.ones(n_v, dtype=int)
n_kids = np.array([len(children[v]) for v in range(n_v)])

queue = deque()
for v in range(n_v):
    if n_kids[v] == 0 and (0 <= pred[v] < n_v or pred[v] == -9999):
        queue.append(v)

done = np.zeros(n_v, dtype=bool)
while queue:
    v = queue.popleft()
    done[v] = True
    p = pred[v]
    if 0 <= p < n_v:
        desc_count[p] += desc_count[v]
        n_kids[p] -= 1
        if n_kids[p] == 0:
            queue.append(p)

print(f"  Tree: {done.sum()} verts, max_desc={desc_count.max()}")


# ── Step 8: Assign radius per vertex ───────────────────────────────────────

thresh = np.random.uniform(40, 80)
ratio = np.random.uniform(0.8, 2.0)
base_r = 0.015

radii = np.empty(n_v)
for v in range(n_v):
    c = desc_count[v]
    r = 1.0 if c < thresh else 1.0 + ratio * math.log(c / thresh)
    radii[v] = base_r * r


# ── Step 9: Smooth tree vertex positions ───────────────────────────────────
# Laplacian smoothing moves vertices toward tree neighbor averages
# This smooths out the zigzag paths from grid traversal

smooth_coords = coords.copy()
for _ in range(5):
    new_c = smooth_coords.copy()
    for v in range(n_v):
        nbrs = list(children[v])
        p = pred[v]
        if 0 <= p < n_v:
            nbrs.append(p)
        if len(nbrs) > 0:
            avg = np.mean(smooth_coords[nbrs], axis=0)
            new_c[v] = 0.6 * smooth_coords[v] + 0.4 * avg
    smooth_coords = new_c


# ── Step 10: Extract path chains (FIXED: include fork-to-child edges) ─────

chains = []


def extract_chains(root):
    """




Extract chains from tree rooted at root.

    Each chain goes from a fork/root vertex through consecutive
    degree-2 vertices to the next fork or leaf. Fork vertices are
    shared between parent and child chains (overlap for welding).
    """

    # Stack items: (start_vertex, forced_first_child_or_None)
    stack = [(root, None)]
    while stack:
        start, forced_child = stack.pop()
        chain = [start]
        if forced_child is not None:
            chain.append(forced_child)
            cur = forced_child
        else:
            cur = start

        while True:
            kids = children[cur]
            if len(kids) == 1:
                chain.append(kids[0])
                cur = kids[0]
            elif len(kids) == 0:
                break  # leaf
            else:
                # Fork: chain ends here, start new chains from each child
                for k in kids:
                    stack.append((cur, k))
                break

        if len(chain) >= 2:
            path = smooth_coords[chain]
            r0 = radii[chain[0]]
            r1 = radii[chain[-1]]
            chains.append((path, r0, r1))


for ep in endpoints:
    extract_chains(ep)

print(f"  Chains: {len(chains)}")


# ── Step 11: Additional smoothing + resampling on chains ──────────────────

def smooth_path(path, iterations=3):
    """




Moving average smoothing."""


    p = path.copy()
    for _ in range(iterations):
        s = p.copy()
        for i in range(1, len(p) - 1):
            s[i] = 0.25 * p[i - 1] + 0.5 * p[i] + 0.25 * p[i + 1]
        p = s
    return p


def resample_path(path, min_pts=4):
    """




Ensure path has at least min_pts points with uniform spacing."""


    if len(path) < 2:
        return path
    diffs = np.diff(path, axis=0)
    seg_len = np.linalg.norm(diffs, axis=1)
    total = seg_len.sum()
    if total < 1e-8:
        return path[:2]
    n_pts = max(min_pts, len(path))
    cum = np.zeros(len(path))
    cum[1:] = np.cumsum(seg_len)
    targets = np.linspace(0, total, n_pts)
    resampled = np.zeros((n_pts, 3))
    for d in range(3):
        resampled[:, d] = np.interp(targets, cum, path[:, d])
    return resampled


final_chains = []
for path, r0, r1 in chains:
    p = smooth_path(path, iterations=3)
    p = resample_path(p, min_pts=4)
    final_chains.append((p, r0, r1))
chains = final_chains


# ── Step 12: Delete disc mesh, build tubes ─────────────────────────────────

bpy.data.objects.remove(obj, do_unlink=True)
bpy.data.meshes.remove(me)

curve_data = bpy.data.curves.new("fan_curves", 'CURVE')
curve_data.dimensions = '3D'
curve_data.bevel_depth = 0.001
curve_data.bevel_resolution = 3   # 16-sided circle cross-section
curve_data.use_fill_caps = True

for path, r_start, r_end in chains:
    n = len(path)
    if n < 2:
        continue
    sp = curve_data.splines.new('POLY')
    sp.points.add(n - 1)
    for i in range(n):
        sp.points[i].co = (*path[i], 1.0)
        t = i / max(1, n - 1)
        r = r_start * (1 - t) + r_end * t
        sp.points[i].radius = r / curve_data.bevel_depth

obj = bpy.data.objects.new("FanBaseCoralFactory", curve_data)
bpy.context.collection.objects.link(obj)

# Convert curve to mesh
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.convert(target='MESH')

# Clean up mesh
bpy.ops.object.editmode_toggle()
bpy.ops.mesh.remove_doubles(threshold=0.0005)
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.editmode_toggle()

bpy.ops.object.shade_smooth()

# Weld overlapping tubes at fork points
m_weld = obj.modifiers.new("Weld", "WELD")
m_weld.merge_threshold = 0.001
bpy.ops.object.modifier_apply(modifier="Weld")

# Origin to lowest vertex
min_z = min(v.co.z for v in obj.data.vertices)
obj.location[2] -= min_z
bpy.ops.object.transform_apply(location=True)
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

obj.name = "FanBaseCoralFactory"
print(f"Done: FanBaseCoralFactory  verts={len(obj.data.vertices)}  faces={len(obj.data.polygons)}")
