# [FL_INDEX: keywords="blender_factory, procedural_3d, FanCoralFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: FanCoralFactory | Category: factories_tex
# Prompt: A sea fan coral (gorgonian) rendered as a textured 3D model. The coral features numerous thin, rod-like branches that grow upward in a roughly planar fan arrangement, branching and bifurcating repeatedly to form a dense lattice-like net structure. The base is a wide, solid root from which the branching network fans outward and upward. The coloring is warm sandy beige to tan with a subtle brown gradient toward the base. A strong shadow beneath the dense branch network creates a dramatic silhouette on the white background.

"""
Standalone Blender script (geometry + coral material) – FanCoralFactory, seed 0.
Run:  blender --background --python FanCoralFactory.py

FanBaseCoralFactory base shape + coral_postprocess (scale + remesh).
noise_strength = 0.0 (no displacement), tentacle_prob = 0.0 (no tentacles).
"""




import os
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

SEED = int(os.environ.get("SEED", 0))
np.random.seed(SEED)

# ═══════════════════════════════════════════════════════════════════════════
#  Coral material — translated from generate.py:shader_coral (raw bpy)
# ═══════════════════════════════════════════════════════════════════════════
import os, random, colorsys

def _seed_all(seed):
    np.random.seed(seed); random.seed(seed)

def _hsv2rgba(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(float(h) % 1.0,
                                   max(0.0, min(1.0, float(s))),
                                   max(0.0, min(1.0, float(v))))
    return (r, g, b, 1.0)

def _new_coral_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat

def _fac_out(node):
    return node.outputs.get("Fac") or node.outputs.get("Factor") or node.outputs[0]

def _noise_as_musgrave(nt, ln, scale, tc_obj_out):
    """




Musgrave replacement: NoiseTexture (Musgrave removed in Blender 5.0).
    Original: MusgraveTexture -> MapRange[-1,1]->[0,1]. Noise already [0,1]."""


    n = nt.nodes.new("ShaderNodeTexNoise")
    ln(tc_obj_out, n.inputs["Vector"])
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = 2.0
    n.inputs["Roughness"].default_value = 0.5
    return _fac_out(n)

def _color_ramp_hsv(nt, ln, fac_out, positions, colors):
    """




build_color_ramp with HSV interpolation mode."""


    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.color_mode = "HSV"
    cr.color_ramp.hue_interpolation = "NEAR"
    ln(fac_out, cr.inputs["Fac"])
    for _ in range(len(positions) - 2):
        cr.color_ramp.elements.new(0.0)
    for i, (p, c) in enumerate(zip(positions, colors)):
        cr.color_ramp.elements[i].position = p
        cr.color_ramp.elements[i].color = c
    return cr

def _float_curve(nt, ln, fac_out, anchors):
    """




build_float_curve with VECTOR handles."""


    fc = nt.nodes.new("ShaderNodeFloatCurve")
    ln(fac_out, fc.inputs["Value"])
    c = fc.mapping.curves[0]
    for i, (x, y) in enumerate(anchors):
        if i < 2:
            c.points[i].location = (x, y)
        else:
            c.points.new(x, y)
        c.points[i].handle_type = "VECTOR"
    fc.mapping.use_clip = False
    fc.mapping.update()
    return fc

def _build_base_hue():
    """




CoralFactory.build_base_hue()"""


    if np.random.uniform(0, 1) < 0.25:
        return float(np.random.uniform(0, 1))
    else:
        return float(np.random.uniform(-0.2, 0.3)) % 1.0

def make_coral_material(base_hue, name="CoralMaterial"):
    """




Faithful translation of generate.py:shader_coral(nw, base_hue).
    Musgrave-driven 4-stop ColorRamp + light_color mix + noise roughness + SSS."""


    shift = float(np.random.uniform(0.05, 0.1)) * ((-1) ** int(np.random.randint(2)))
    subsurface_color = _hsv2rgba(np.random.uniform(0, 1), np.random.uniform(0, 1), 1.0)
    bright_color = _hsv2rgba((base_hue + shift) % 1, np.random.uniform(0.7, 0.9), 0.2)
    dark_color   = _hsv2rgba(base_hue, np.random.uniform(0.5, 0.7), 0.1)
    light_color  = _hsv2rgba((base_hue + float(np.random.uniform(-0.2, 0.2))) % 1,
                              np.random.uniform(0.2, 0.4), 0.4)
    specular = float(np.random.uniform(0.25, 0.5))
    musg1_scale = float(np.random.uniform(10, 20))
    musg2_scale = float(np.random.uniform(10, 20))
    fc_mid = float(np.random.uniform(0.3, 0.4))
    ss_ratio = float(np.random.uniform(0, 0.05)) if np.random.uniform(0, 1) > 0.5 else 0.0
    ss_r = float(np.random.uniform(0.05, 0.2))

    mat = _new_coral_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")

    # Color ramp: musgrave1 -> 4-stop HSV (dark -> bright)
    m1 = _noise_as_musgrave(nt, ln, musg1_scale, tc.outputs["Object"])
    cr = _color_ramp_hsv(nt, ln, m1,
        [0.0, 0.3, 0.7, 1.0],
        [dark_color, dark_color, bright_color, bright_color])

    # Mix with light_color via float curve of musgrave2
    m2 = _noise_as_musgrave(nt, ln, musg2_scale, tc.outputs["Object"])
    fc = _float_curve(nt, ln, m2, [(0, 1), (fc_mid, 0), (1, 0)])
    light_rgb = nt.nodes.new("ShaderNodeRGB")
    light_rgb.outputs[0].default_value = light_color
    mix_c = nt.nodes.new("ShaderNodeMix"); mix_c.data_type = "RGBA"
    ln(fc.outputs["Value"], mix_c.inputs[0])
    ln(cr.outputs["Color"], mix_c.inputs[6])
    ln(light_rgb.outputs[0], mix_c.inputs[7])

    # Roughness: noise(50) -> float curve (0.5 -> 1.0)
    n_r = nt.nodes.new("ShaderNodeTexNoise"); n_r.inputs["Scale"].default_value = 50.0
    fc_r = _float_curve(nt, ln, _fac_out(n_r), [(0, 0.5), (1, 1.0)])

    # Principled BSDF
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(mix_c.outputs[2], bsdf.inputs["Base Color"])
    ln(fc_r.outputs["Value"], bsdf.inputs["Roughness"])
    spec_key = "Specular IOR Level" if "Specular IOR Level" in bsdf.inputs else "Specular"
    bsdf.inputs[spec_key].default_value = specular
    bsdf.inputs["Subsurface Weight"].default_value = ss_ratio
    bsdf.inputs["Subsurface Radius"].default_value = (ss_r, ss_r, ss_r)
    if "Subsurface Color" in bsdf.inputs:
        bsdf.inputs["Subsurface Color"].default_value = subsurface_color

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

# from FixedSeed(factory_seed). To get equivalent diversity, we hash the seed for material
# sampling (otherwise consecutive seeds all produce similar warm-red hues).
_mat_seed = ((SEED + 1) * 2654435761) & 0xFFFFFFFF  # Knuth multiplicative hash
_seed_all(_mat_seed)
_coral_base_hue = _build_base_hue()
CORAL_MAT = make_coral_material(_coral_base_hue, "FanCoralFactory_Material")

# Re-seed for geometry (standalone uses seed for geometry params)
np.random.seed(SEED)

# ── Step 1: Create semicircular disc mesh ──────────────────────────────────

n_rings = 40
n_angles = 80

bm = bmesh.new()
center = bm.verts.new((0, 0, 0))

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

for a in range(n_angles):
    try:
        bm.faces.new([center, ring_verts[0][a], ring_verts[0][a + 1]])
    except ValueError:
        pass

for r in range(n_rings - 1):
    for a in range(n_angles):
        try:
            bm.faces.new([ring_verts[r][a], ring_verts[r][a + 1],
                          ring_verts[r + 1][a + 1], ring_verts[r + 1][a]])
        except ValueError:
            pass

bmesh.ops.triangulate(bm, faces=bm.faces[:])

me = bpy.data.meshes.new("fan_disc")
bm.to_mesh(me)
bm.free()

obj = bpy.data.objects.new("FanDisc", me)
bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

print(f"  Disc mesh: {len(me.vertices)} verts, {len(me.edges)} edges")

# ── Step 2: Shape by angles ───────────────────────────────────────────────

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
    v.co.x *= scale
    v.co.z *= scale

# ── Step 3: STUCCI displacement ───────────────────────────────────────────

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

sx = np.random.uniform(0.6, 1.2)
obj.scale.x *= sx
bpy.ops.object.transform_apply(scale=True)

me = obj.data

# ── Step 4: Extract graph ─────────────────────────────────────────────────

n_v = len(me.vertices)
coords = np.zeros((n_v, 3))
for i, v in enumerate(me.vertices):
    coords[i] = v.co[:]

edge_list = np.array([(e.vertices[0], e.vertices[1]) for e in me.edges])
n_e = len(edge_list)
lengths = np.linalg.norm(coords[edge_list[:, 0]] - coords[edge_list[:, 1]], axis=1)
rand_w = np.random.uniform(0.4, 1.0, n_e) * np.maximum(lengths, 1e-8)

row = np.concatenate([edge_list[:, 0], edge_list[:, 1]])
col = np.concatenate([edge_list[:, 1], edge_list[:, 0]])
data = np.concatenate([rand_w, rand_w])
graph = csr_matrix((data, (row, col)), shape=(n_v, n_v))

print(f"  Graph: {n_v} verts, {n_e} edges")

# ── Step 5: Bottom endpoints ──────────────────────────────────────────────

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

# ── Step 6: Dijkstra ──────────────────────────────────────────────────────

n_total = n_v + 1
vid = n_v
ext_row = np.concatenate([row, np.full(n_ep, vid, dtype=np.intp),
                          endpoints.astype(np.intp)])
ext_col = np.concatenate([col, endpoints.astype(np.intp),
                          np.full(n_ep, vid, dtype=np.intp)])
ext_data = np.concatenate([data, np.full(n_ep, 1e-10), np.full(n_ep, 1e-10)])
ext_graph = csr_matrix((ext_data, (ext_row, ext_col)), shape=(n_total, n_total))

_, pred_arr = dijkstra(ext_graph, directed=False, indices=vid,
                       return_predecessors=True)
pred = pred_arr[:n_v].copy()
for ep in endpoints:
    pred[ep] = -9999
pred[pred == vid] = -9999

reachable = np.sum((pred >= 0) | (pred == -9999))
print(f"  Reachable: {reachable}/{n_v}")

# ── Step 7: Tree + descendants ────────────────────────────────────────────

children = [[] for _ in range(n_v)]
for v in range(n_v):
    p = pred[v]
    if 0 <= p < n_v and p != v:
        children[p].append(v)

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

# ── Step 8: Radius ────────────────────────────────────────────────────────

thresh = np.random.uniform(40, 80)
ratio = np.random.uniform(0.8, 2.0)
base_r = 0.015

radii = np.empty(n_v)
for v in range(n_v):
    c = desc_count[v]
    r = 1.0 if c < thresh else 1.0 + ratio * math.log(c / thresh)
    radii[v] = base_r * r

# ── Step 9: Smooth tree positions ─────────────────────────────────────────

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

# ── Step 10: Extract chains ───────────────────────────────────────────────

chains = []

def extract_chains(root):
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
                break
            else:
                for k in kids:
                    stack.append((cur, k))
                break
        if len(chain) >= 2:
            path = smooth_coords[chain]
            chains.append((path, radii[chain[0]], radii[chain[-1]]))

for ep in endpoints:
    extract_chains(ep)

print(f"  Chains: {len(chains)}")

# ── Step 11: Smooth + resample chains ─────────────────────────────────────

def smooth_path(path, iterations=3):
    p = path.copy()
    for _ in range(iterations):
        s = p.copy()
        for i in range(1, len(p) - 1):
            s[i] = 0.25 * p[i - 1] + 0.5 * p[i] + 0.25 * p[i + 1]
        p = s
    return p

def resample_path(path, min_pts=4):
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

# ── Step 12: Delete disc, build tubes ─────────────────────────────────────

bpy.data.objects.remove(obj, do_unlink=True)
bpy.data.meshes.remove(me)

curve_data = bpy.data.curves.new("fan_curves", 'CURVE')
curve_data.dimensions = '3D'
curve_data.bevel_depth = 0.001
curve_data.bevel_resolution = 3
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

obj = bpy.data.objects.new("FanCoralFactory", curve_data)
bpy.context.collection.objects.link(obj)

bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.convert(target='MESH')

bpy.ops.object.editmode_toggle()
bpy.ops.mesh.remove_doubles(threshold=0.0005)
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.editmode_toggle()

bpy.ops.object.shade_smooth()

# Weld overlapping tubes
m_weld = obj.modifiers.new("Weld", "WELD")
m_weld.merge_threshold = 0.001
bpy.ops.object.modifier_apply(modifier="Weld")

# Origin to lowest
min_z = min(v.co.z for v in obj.data.vertices)
obj.location[2] -= min_z
bpy.ops.object.transform_apply(location=True)

# ── coral_postprocess: scale + remesh (noise_strength=0.0) ────────────────

default_scale = [0.8, 0.8, 0.8]
dims = [obj.dimensions.x, obj.dimensions.y, obj.dimensions.z]
max_xy = max(dims[0], dims[1], 1e-6)
scale = 2.0 * np.array(default_scale) / max_xy * np.random.uniform(0.8, 1.2, 3)
obj.scale = tuple(scale)
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.transform_apply(scale=True)

# Voxel remesh — fuses overlapping tubes at fork points
m_rem = obj.modifiers.new("Remesh", "REMESH")
m_rem.mode = "VOXEL"
m_rem.voxel_size = 0.007
bpy.ops.object.modifier_apply(modifier="Remesh")

bpy.ops.object.shade_smooth()
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

# ── assign coral material ──
obj.data.materials.clear()
obj.data.materials.append(CORAL_MAT)

obj.name = "FanCoralFactory"
print(f"Done: FanCoralFactory  verts={len(obj.data.vertices)}  faces={len(obj.data.polygons)}")

