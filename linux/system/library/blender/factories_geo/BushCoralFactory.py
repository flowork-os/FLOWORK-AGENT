# [FL_INDEX: keywords="blender_factory, procedural_3d, BushCoralFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: BushCoralFactory | Category: factories_geo
# Prompt: A bush-type branching coral rendered as a textured 3D model. The coral spreads outward and upward in an irregular bush-like form with multiple thick, finger-like branches diverging from a central base. Each branch has a rough, granular surface texture covered in small polyp bumps. The coloring is warm pink-salmon to sandy beige, with subtle depth variation across the branches. The organic, sprawling silhouette casts a complex shadow on the white background below.

import os
import random
import colorsys
import sys
import bpy
import numpy as np
import math


SEED = int(os.environ.get("SEED", "0"))
np.random.seed(SEED)

# ═══════════════════════════════════════════════════════════════════════════
#  Coral material — translated from generate.py:shader_coral (raw bpy)
# ═══════════════════════════════════════════════════════════════════════════

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
    """Musgrave replacement: NoiseTexture (Musgrave removed in Blender 5.0).
    Original: MusgraveTexture -> MapRange[-1,1]->[0,1]. Noise already [0,1]."""

    n = nt.nodes.new("ShaderNodeTexNoise")
    ln(tc_obj_out, n.inputs["Vector"])
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = 2.0
    n.inputs["Roughness"].default_value = 0.5
    return _fac_out(n)

def _color_ramp_hsv(nt, ln, fac_out, positions, colors):
    """build_color_ramp with HSV interpolation mode."""

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
    """build_float_curve with VECTOR handles."""

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
    """CoralFactory.build_base_hue()"""

    if np.random.uniform(0, 1) < 0.25:
        return float(np.random.uniform(0, 1))
    else:
        return float(np.random.uniform(-0.2, 0.3)) % 1.0

def make_coral_material(base_hue, name="CoralMaterial"):
    """Faithful translation of generate.py:shader_coral(nw, base_hue).
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


# Phase 1: material sampling (mirrors CoralFactory.__init__ with FixedSeed)
# from FixedSeed(factory_seed). To get equivalent diversity, we hash the seed for material
# sampling (otherwise consecutive seeds all produce similar warm-red hues).
_mat_seed = ((SEED + 1) * 2654435761) & 0xFFFFFFFF  # Knuth multiplicative hash
_seed_all(_mat_seed)
_coral_base_hue = _build_base_hue()
CORAL_MAT = make_coral_material(_coral_base_hue, "BushCoralFactory_Material")

# Re-seed for geometry (standalone uses seed for geometry params)
np.random.seed(SEED)


# ── Config (TreeBaseCoralFactory overrides) ──────────────────────────────────
n_branch = np.random.randint(6, 8)
n_major  = np.random.randint(4, 5)
n_minor  = np.random.randint(4, 5)
n_detail = np.random.randint(3, 4)
span     = np.random.uniform(0.4, 0.5)

base_radius    = 0.08
default_scale  = np.array([1.0, 1.0, 1.0])  # TreeBaseCoralFactory override
noise_strength = 0.01                         # TreeBaseCoralFactory override
bump_prob      = 0.3
tentacle_prob  = 0.8                          # TreeBaseCoralFactory override
tentacle_density = 500


# ── Helpers ──────────────────────────────────────────────────────────────────

def rodrigues_rot(vec, axis, angle):
    axis = axis / (np.linalg.norm(axis) + 1e-12)
    cs, sn = np.cos(angle), np.sin(angle)
    return vec * cs + np.cross(axis, vec) * sn + axis * np.dot(axis, vec) * (1 - cs)


def compute_radii(base_r, n_pts):
    decay_root = 0.85
    decay_leaf = np.random.uniform(0.4, 0.6)
    r = base_r * decay_root ** np.arange(n_pts, dtype=float)
    r[-1] *= decay_leaf
    return r


def rand_path(n_pts, init_vec, init_pt=None, std=0.3, momentum=0.5,
              sz=1.0, sz_decay=1.0):
    init_vec = np.array(init_vec, dtype=float)
    init_vec = init_vec / (np.linalg.norm(init_vec) + 1e-12)
    path = np.zeros((n_pts, 3))
    if init_pt is not None:
        path[0] = np.array(init_pt, dtype=float)
    for i in range(1, n_pts):
        if i == 1:
            prev_delta = init_vec * sz
        else:
            prev_delta = path[i - 1] - path[i - 2]
        prev_sz = np.linalg.norm(prev_delta) + 1e-12
        new_delta = prev_delta + np.random.randn(3) * std
        new_delta = (new_delta / (np.linalg.norm(new_delta) + 1e-12)) * prev_sz
        tmp_mom = 1.0 - (1.0 - momentum) * (i + 1) / n_pts
        delta = prev_delta * tmp_mom + new_delta * (1.0 - tmp_mom)
        delta = (delta / (np.linalg.norm(delta) + 1e-12)) * sz * (sz_decay ** i)
        path[i] = path[i - 1] + delta
    return path


def get_spawn_pt(parent_path, rnd_idx=None, ang_min=np.pi / 6,
                 ang_max=0.9 * np.pi / 2, axis2=None, init_vec=None):
    n = len(parent_path)
    if n == 1:
        return 0, parent_path[0].copy(), np.array(init_vec, dtype=float)
    if rnd_idx is None:
        rnd_idx = np.random.randint(max(1, n // 2), n)
    rnd_idx = min(rnd_idx, n - 1)
    pt = parent_path[rnd_idx].copy()
    if init_vec is not None:
        return rnd_idx, pt, np.array(init_vec, dtype=float)
    curr_vec = parent_path[rnd_idx] - parent_path[max(0, rnd_idx - 1)]
    if np.linalg.norm(curr_vec) < 1e-12:
        curr_vec = np.array([0.0, 0.0, 1.0])
    if axis2 is None:
        axis2 = np.array([0.0, 0.0, 1.0])
    else:
        axis2 = np.array(axis2, dtype=float)
    rnd_ang = np.random.uniform(ang_min, ang_max)
    rnd_ang *= np.sign(np.random.randn())
    child_vec = rodrigues_rot(curr_vec, axis2, rnd_ang)
    return rnd_idx, pt, child_vec


def sample_direction(min_z):
    for _ in range(100):
        x = np.random.randn(3)
        y = x / (np.linalg.norm(x) + 1e-12)
        if y[2] > min_z:
            return y
    return np.array([0.0, 0.0, 1.0])


def interpolate_path(path, radii, subdiv=16):
    n = len(path)
    if n < 2:
        return path, radii
    dists = np.zeros(n)
    for i in range(1, n):
        dists[i] = dists[i - 1] + np.linalg.norm(path[i] - path[i - 1])
    total = dists[-1]
    if total < 1e-12:
        return path, radii
    n_out = subdiv * (n - 1) + 1
    t_out = np.linspace(0.0, total, n_out)
    new_path = np.zeros((n_out, 3))
    for ax in range(3):
        new_path[:, ax] = np.interp(t_out, dists, path[:, ax])
    new_r = np.interp(t_out, dists, radii)
    return new_path, new_r


# ── Skeleton construction ────────────────────────────────────────────────────
# Build connected skeleton: vertices + edges + radii.
# Geometry Nodes (MeshToCurve → CurveToMesh) converts to proper tube mesh.

skel_verts = []  # list of (x, y, z)
skel_edges = []  # list of (i, j) vertex index pairs
skel_radii = []  # radius per vertex


# ── Build coral tree ─────────────────────────────────────────────────────────
# We store raw paths + radii, then scale and build skeleton
raw_branches = []  # (path, radii, parent_branch_idx, spawn_idx_in_parent)
root = np.zeros(3)

# Add root vertex
skel_verts.append((0.0, 0.0, 0.0))
skel_radii.append(base_radius)
root_idx = 0

for b_idx in range(n_branch):
    angle = 2 * np.pi * b_idx / n_branch + np.random.uniform(-np.pi / 9, np.pi / 9)
    init_vec = [
        span * math.cos(angle),
        span * math.sin(angle),
        math.sqrt(max(0, 1 - span * span)),
    ]
    sz_major = np.random.uniform(0.08, 0.10)
    n_pts_major = n_major + 1
    major_path = rand_path(n_pts=n_pts_major, init_vec=init_vec, init_pt=root,
                           std=0.4, momentum=0.4, sz=sz_major)
    major_radii = compute_radii(base_radius, n_pts_major)
    raw_branches.append((major_path, major_radii, None, None))

    for m_idx in range(n_major):
        spawn_idx, attach_pt, child_vec = get_spawn_pt(
            major_path, rnd_idx=m_idx + 1,
            ang_min=np.pi / 12, ang_max=np.pi / 8, axis2=[0, 0, 1])
        minor_base_r = major_radii[spawn_idx]
        n_pts_minor = n_minor + 1
        sz_minor = max(0.03 * (1.2 * n_minor - m_idx), 0.005)
        minor_path = rand_path(n_pts=n_pts_minor, init_vec=child_vec, init_pt=attach_pt,
                               std=0.4, momentum=0.4, sz=sz_minor)
        minor_radii = compute_radii(minor_base_r, n_pts_minor)
        major_br_idx = len(raw_branches) - 1
        raw_branches.append((minor_path, minor_radii, major_br_idx, spawn_idx))

        for d_idx in range(n_minor):
            spawn_idx2, attach_d, det_vec = get_spawn_pt(
                minor_path, rnd_idx=d_idx + 1,
                ang_min=np.pi / 12, ang_max=np.pi / 8, axis2=[0, 0, 1])
            detail_base_r = minor_radii[spawn_idx2]
            n_pts_detail = n_detail + 1
            sz_detail = max(0.01 * (1.5 * n_detail - d_idx), 0.003)
            det_path = rand_path(n_pts=n_pts_detail, init_vec=det_vec, init_pt=attach_d,
                                 std=0.4, momentum=0.6, sz=sz_detail)
            det_radii = compute_radii(detail_base_r, n_pts_detail)
            minor_br_idx = len(raw_branches) - 1
            raw_branches.append((det_path, det_radii, minor_br_idx, spawn_idx2))

# Scale positions only (skeleton scaled, radii stay as vertex weights)
all_pts = np.concatenate([b[0] for b in raw_branches])
skel_max_dim = max(np.ptp(all_pts[:, 0]), np.ptp(all_pts[:, 1]), 1e-6)
pos_scale = 2.0 * default_scale / skel_max_dim

# Build skeleton with scaled positions
# Track which skeleton vertex corresponds to each (branch_idx, point_idx)
branch_skel_indices = []  # branch_skel_indices[br_idx] = list of skeleton vertex indices

for br_idx, (path, radii, parent_br, parent_spawn) in enumerate(raw_branches):
    scaled_path = path * pos_scale
    interp_path, interp_radii = interpolate_path(scaled_path, radii, subdiv=4)

    base_skel_idx = len(skel_verts)
    vert_indices = []
    for i, (pt, r) in enumerate(zip(interp_path, interp_radii)):
        skel_verts.append(tuple(pt))
        skel_radii.append(r)
        vi = base_skel_idx + i
        vert_indices.append(vi)
        if i > 0:
            skel_edges.append((vi - 1, vi))

    # Connect to parent branch at spawn point
    if parent_br is not None and parent_br < len(branch_skel_indices):
        parent_verts = branch_skel_indices[parent_br]
        # Find closest parent vertex to this branch's start
        p0 = np.array(skel_verts[vert_indices[0]])
        min_dist = float('inf')
        connect_to = parent_verts[0]
        for pvi in parent_verts:
            d = np.linalg.norm(p0 - np.array(skel_verts[pvi]))
            if d < min_dist:
                min_dist = d
                connect_to = pvi
        skel_edges.append((connect_to, vert_indices[0]))
    else:
        # Major branch: connect to root
        skel_edges.append((root_idx, vert_indices[0]))

    branch_skel_indices.append(vert_indices)

print(f"Skeleton: {len(skel_verts)} verts, {len(skel_edges)} edges")

# Create skeleton mesh
mesh = bpy.data.meshes.new("BushCoralFactory")
mesh.from_pydata(skel_verts, skel_edges, [])
mesh.update()

obj = bpy.data.objects.new("BushCoralFactory", mesh)
bpy.context.scene.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)

vg = obj.vertex_groups.new(name="radius")
for i, r in enumerate(skel_radii):
    vg.add([i], r, 'REPLACE')

# ── Geometry Nodes: MeshToCurve → SetCurveRadius → CurveToMesh → MergeByDistance ──

gn_mod = obj.modifiers.new("GeoRadius", 'NODES')

# Create node tree
tree = bpy.data.node_groups.new("geo_radius", 'GeometryNodeTree')
gn_mod.node_group = tree

# Clear default nodes
for n in tree.nodes:
    tree.nodes.remove(n)

# Create nodes
input_node = tree.nodes.new('NodeGroupInput')
input_node.location = (-600, 0)

output_node = tree.nodes.new('NodeGroupOutput')
output_node.location = (600, 0)

# Add Geometry input/output sockets
tree.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

# MeshToCurve
mesh_to_curve = tree.nodes.new('GeometryNodeMeshToCurve')
mesh_to_curve.location = (-400, 0)
tree.links.new(input_node.outputs[0], mesh_to_curve.inputs[0])

# Read radius from Named Attribute
named_attr = tree.nodes.new('GeometryNodeInputNamedAttribute')
named_attr.location = (-400, -200)
named_attr.data_type = 'FLOAT'
named_attr.inputs['Name'].default_value = "radius"

# SetCurveRadius
set_radius = tree.nodes.new('GeometryNodeSetCurveRadius')
set_radius.location = (-200, 0)
tree.links.new(mesh_to_curve.outputs[0], set_radius.inputs['Curve'])
tree.links.new(named_attr.outputs['Attribute'], set_radius.inputs['Radius'])

# CurveCircle (profile with 32 segments)
circle = tree.nodes.new('GeometryNodeCurvePrimitiveCircle')
circle.location = (-200, -200)
circle.mode = 'RADIUS'
circle.inputs['Resolution'].default_value = 32
circle.inputs['Radius'].default_value = 1.0

# CurveToMesh
curve_to_mesh = tree.nodes.new('GeometryNodeCurveToMesh')
curve_to_mesh.location = (0, 0)
tree.links.new(set_radius.outputs[0], curve_to_mesh.inputs['Curve'])
tree.links.new(circle.outputs[0], curve_to_mesh.inputs['Profile Curve'])
curve_to_mesh.inputs['Fill Caps'].default_value = True
# Blender 5.0+: connect radius to Scale input (SetCurveRadius ignored by CurveToMesh)
try:
    tree.links.new(named_attr.outputs['Attribute'], curve_to_mesh.inputs['Scale'])
except Exception:
    pass  # older Blender: SetCurveRadius handles it

# MergeByDistance
merge = tree.nodes.new('GeometryNodeMergeByDistance')
merge.location = (200, 0)
tree.links.new(curve_to_mesh.outputs[0], merge.inputs[0])
merge.inputs['Distance'].default_value = 0.004

# Connect to output
tree.links.new(merge.outputs[0], output_node.inputs[0])

# Store radius as named attribute before GeoNodes modifier runs
# (vertex group is automatically accessible via named attribute)

# Apply the GeoNodes modifier
bpy.ops.object.modifier_apply(modifier="GeoRadius")
print(f"After GeoRadius: verts={len(obj.data.vertices)}  faces={len(obj.data.polygons)}")

bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

# ── Postprocess (CoralFactory.create_asset) ──────────────────────────────────
# Scale to fit ~2 units
dims = np.array([obj.dimensions.x, obj.dimensions.y, obj.dimensions.z])
max_xy = max(dims[0], dims[1], 1e-6)
s2 = 2.0 * default_scale / max_xy * np.random.uniform(0.8, 1.2, 3)
obj.scale = tuple(s2)
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.transform_apply(scale=True)

print(f"After scale: verts={len(obj.data.vertices)}  faces={len(obj.data.polygons)}  "
      f"dims={obj.dimensions.x:.3f}x{obj.dimensions.y:.3f}x{obj.dimensions.z:.3f}")

# Voxel remesh to merge overlapping tube surfaces into clean shell
m_rem = obj.modifiers.new("Remesh", "REMESH")
m_rem.mode = "VOXEL"
m_rem.voxel_size = 0.01
bpy.ops.object.modifier_apply(modifier="Remesh")
print(f"After remesh: verts={len(obj.data.vertices)}  faces={len(obj.data.polygons)}  "
      f"dims={obj.dimensions.x:.3f}x{obj.dimensions.y:.3f}x{obj.dimensions.z:.3f}")

# Noise/bump displacement (noise_strength=0.01)
has_bump = False
if noise_strength > 0:
    has_bump = np.random.uniform() < bump_prob
    if has_bump:
        tex_type = np.random.choice(['STUCCI', 'MARBLE'])
        tex = bpy.data.textures.new("coral_noise", type=tex_type)
        tex.noise_scale = math.exp(np.random.uniform(math.log(0.01), math.log(0.02)))
        m_d = obj.modifiers.new("Noise", "DISPLACE")
        m_d.texture = tex
        m_d.strength = noise_strength * np.random.uniform(0.9, 1.2)
        m_d.mid_level = 0
    else:
        tex = bpy.data.textures.new("coral_bump", type='VORONOI')
        tex.noise_scale = math.exp(np.random.uniform(math.log(0.02), math.log(0.03)))
        tex.noise_intensity = math.exp(np.random.uniform(math.log(1.5), math.log(2.0)))
        tex.distance_metric = 'MINKOVSKY'
        tex.minkovsky_exponent = np.random.uniform(1, 1.5)
        m_d = obj.modifiers.new("Bump", "DISPLACE")
        m_d.texture = tex
        m_d.strength = -noise_strength * np.random.uniform(1, 2)
        m_d.mid_level = 1
    bpy.ops.object.modifier_apply(modifier=m_d.name)

print(f"Coral base: verts={len(obj.data.vertices)}  faces={len(obj.data.polygons)}")


# ══════════════════════════════════════════════════════════════════════════════
# TENTACLES (matching tentacles.py)
# ══════════════════════════════════════════════════════════════════════════════

def simple_tube(path, radii, n_ring=6):
    """Simple tube mesh for tentacles (small, don't need Skin modifier)."""

    N = len(path)
    all_v = []
    for i, (pt, r) in enumerate(zip(path, radii)):
        if i == 0:
            tang = path[1] - path[0]
        elif i == N - 1:
            tang = path[-1] - path[-2]
        else:
            tang = path[i + 1] - path[i - 1]
        tang = tang / (np.linalg.norm(tang) + 1e-12)
        ref = np.array([0, 0, 1.0]) if abs(tang[2]) < 0.9 else np.array([1, 0, 0.0])
        nx = np.cross(ref, tang); nx /= (np.linalg.norm(nx) + 1e-12)
        ny = np.cross(tang, nx)
        angles = np.linspace(0, 2 * np.pi, n_ring, endpoint=False)
        ring = pt + r * (np.cos(angles)[:, None] * nx + np.sin(angles)[:, None] * ny)
        all_v.append(ring)
    verts = np.concatenate(all_v)
    faces = []
    for i in range(N - 1):
        for j in range(n_ring):
            a = i * n_ring + j
            b = i * n_ring + (j + 1) % n_ring
            c = (i + 1) * n_ring + (j + 1) % n_ring
            d = (i + 1) * n_ring + j
            faces.append([a, b, c, d])
    tip_c = len(verts)
    verts = np.vstack([verts, path[-1]])
    for j in range(n_ring):
        a = (N - 1) * n_ring + j
        b = (N - 1) * n_ring + (j + 1) % n_ring
        faces.append([a, b, tip_c])
    return verts, faces


def build_one_tentacle():
    """Build a single tentacle mesh (5 branches × 8 pts, radius 0.002-0.004)."""

    t_verts, t_faces = [], []
    t_offset = 0
    tent_base_r = np.random.uniform(0.002, 0.004)
    n_tent_branch = 5
    n_tent_pts = 8

    for _ in range(n_tent_branch):
        ivec = sample_direction(0.6)
        path = rand_path(n_pts=n_tent_pts, init_vec=ivec, std=0.5,
                         momentum=0.5, sz=0.008)
        radii = compute_radii(tent_base_r, n_tent_pts)
        path, radii = interpolate_path(path, radii, subdiv=4)
        v, f = simple_tube(path, radii, n_ring=6)
        t_verts.append(v)
        t_faces.extend([[fi + t_offset for fi in face] for face in f])
        t_offset += len(v)

    if not t_verts:
        return None
    all_v = np.concatenate(t_verts, axis=0)
    me = bpy.data.meshes.new("tentacle")
    me.from_pydata(all_v.tolist(), [], t_faces)
    me.update()
    t_obj = bpy.data.objects.new("tentacle", me)
    bpy.context.scene.collection.objects.link(t_obj)
    return t_obj


def distribute_points_on_mesh(obj, density=500, min_distance=0.05,
                              radius_threshold=0.4):
    """Sample random points on mesh surface, then filter like make_radius_points_fn.

    1. Sample proportional to face area (density per unit area)
    2. Merge within 2*min_distance near center (radius < 1.5*threshold)
    3. Merge within min_distance everywhere
    4. Keep only points with radius > threshold
    """

    mesh = obj.data
    mesh.calc_loop_triangles()

    # World-space transform
    mw = np.array(obj.matrix_world)

    # Collect triangles
    tri_verts = []
    tri_normals = []
    for tri in mesh.loop_triangles:
        vs = [np.array(mesh.vertices[i].co) for i in tri.vertices]
        tri_verts.append(vs)
        tri_normals.append(np.array(tri.normal))

    # Compute areas
    areas = []
    for vs in tri_verts:
        edge1 = vs[1] - vs[0]
        edge2 = vs[2] - vs[0]
        areas.append(0.5 * np.linalg.norm(np.cross(edge1, edge2)))

    total_area = sum(areas)
    if total_area < 1e-12:
        return np.zeros((0, 3)), np.zeros((0, 3))

    n_points = int(total_area * density)
    print(f"  Tentacle points: sampling {n_points} from area={total_area:.4f}")

    probs = np.array(areas) / total_area
    face_indices = np.random.choice(len(areas), size=n_points, p=probs)

    points = []
    normals = []
    for fi in face_indices:
        vs = tri_verts[fi]
        r1, r2 = np.random.random(2)
        if r1 + r2 > 1:
            r1, r2 = 1 - r1, 1 - r2
        pt = vs[0] * (1 - r1 - r2) + vs[1] * r1 + vs[2] * r2
        points.append(pt)
        normals.append(tri_normals[fi])

    points = np.array(points)
    normals = np.array(normals)

    # Distance from origin (median point after origin_set)
    origin = np.zeros(3)
    radii = np.linalg.norm(points - origin, axis=1)

    # Phase 1: aggressive merge near center (radius < 1.5 * threshold)
    keep = np.ones(len(points), dtype=bool)
    near_center = radii < radius_threshold * 1.5
    if near_center.any():
        nc_idx = np.where(near_center)[0]
        for i, idx in enumerate(nc_idx):
            if not keep[idx]:
                continue
            dists = np.linalg.norm(points[nc_idx[i + 1:]] - points[idx], axis=1)
            too_close = nc_idx[i + 1:][dists < min_distance * 2]
            keep[too_close] = False

    # Phase 2: merge everywhere at min_distance
    remaining = np.where(keep)[0]
    for i, idx in enumerate(remaining):
        if not keep[idx]:
            continue
        dists = np.linalg.norm(points[remaining[i + 1:]] - points[idx], axis=1)
        too_close = remaining[i + 1:][dists < min_distance]
        keep[too_close] = False

    # Phase 3: radius filter (keep only outer region)
    keep &= (radii > radius_threshold)

    points = points[keep]
    normals = normals[keep]
    print(f"  After filtering: {len(points)} tentacle placement points")
    return points, normals


def rotation_from_normal(normal):
    """Compute rotation matrix to align Z-axis with surface normal."""

    nrm = normal / (np.linalg.norm(normal) + 1e-12)
    up = np.array([0.0, 0.0, 1.0])
    if abs(np.dot(nrm, up)) > 0.999:
        ref = np.array([1.0, 0.0, 0.0])
    else:
        ref = up
    right = np.cross(ref, nrm)
    right = right / (np.linalg.norm(right) + 1e-12)
    fwd = np.cross(nrm, right)
    # Rotation matrix: columns = right, fwd, nrm
    return np.column_stack([right, fwd, nrm])


add_tentacles = (np.random.uniform() < tentacle_prob) and (not has_bump)

if add_tentacles:
    print("Adding tentacles...")
    # Build 5 tentacle variants
    tent_variants = []
    for vi in range(5):
        t = build_one_tentacle()
        if t is not None:
            tent_variants.append(t)

    if tent_variants:
        # Distribute points on coral surface
        pts, nrms = distribute_points_on_mesh(
            obj, density=tentacle_density,
            min_distance=0.05, radius_threshold=0.4)

        if len(pts) > 0:
            tent_objs = []
            for i in range(len(pts)):
                # Pick random variant
                src = tent_variants[np.random.randint(0, len(tent_variants))]
                # Duplicate
                new_obj = src.copy()
                new_obj.data = src.data.copy()
                bpy.context.scene.collection.objects.link(new_obj)

                # Random scale (0.6 - 1.0)
                sc = np.random.uniform(0.6, 1.0)
                new_obj.scale = (sc, sc, sc)

                # Align to surface normal + random twist
                rot_mat = rotation_from_normal(nrms[i])
                twist = np.random.uniform(0, 2 * np.pi)
                twist_mat = np.array([
                    [np.cos(twist), -np.sin(twist), 0],
                    [np.sin(twist),  np.cos(twist), 0],
                    [0, 0, 1],
                ])
                final_rot = rot_mat @ twist_mat
                new_obj.matrix_world = (
                    np.eye(4)
                )
                # Set rotation via 3x3
                for r in range(3):
                    for c in range(3):
                        new_obj.matrix_world[r][c] = final_rot[r, c] * sc
                # Set position
                new_obj.matrix_world[0][3] = pts[i][0]
                new_obj.matrix_world[1][3] = pts[i][1]
                new_obj.matrix_world[2][3] = pts[i][2]

                tent_objs.append(new_obj)

            # Join all tentacles + coral
            bpy.ops.object.select_all(action='DESELECT')
            for t in tent_objs:
                t.select_set(True)
            for t in tent_variants:
                t.select_set(True)
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.join()
            obj = bpy.context.active_object  # re-get after join
            # Recalculate normals after join
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.object.editmode_toggle()
            print(f"  Joined {len(tent_objs)} tentacles onto coral")
        else:
            # Clean up unused variants
            for t in tent_variants:
                bpy.data.objects.remove(t, do_unlink=True)
    else:
        print("  No tentacle variants generated")
else:
    print("Skipping tentacles (has_bump or probability)")


# ── assign coral material ──
obj.data.materials.clear()
obj.data.materials.append(CORAL_MAT)

obj.name = "BushCoralFactory"
print(f"Final dims: {obj.dimensions.x:.3f} x {obj.dimensions.y:.3f} x {obj.dimensions.z:.3f}")
print(f"Done: BushCoralFactory  verts={len(obj.data.vertices)}  faces={len(obj.data.polygons)}")


# ══════════════════════════════════════════════════════════════════════════════
# RENDER (optional: pass -- --render to enable)
# ══════════════════════════════════════════════════════════════════════════════

argv = sys.argv
if "--" in argv:
    custom_args = argv[argv.index("--") + 1:]
else:
    custom_args = []

if "--render" in custom_args:
    import os
    from mathutils import Vector

    # Parse distance multiplier (1.0 = auto-fit, 0.5 = close-up)
    cam_distance = 1.0
    if "--distance" in custom_args:
        di = custom_args.index("--distance")
        if di + 1 < len(custom_args):
            cam_distance = float(custom_args[di + 1])

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "BushCoralFactory_render.png")

    # Compute world-space bounding box center and size
    bbox_corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    center = sum(bbox_corners, Vector()) / 8
    bbox_size = max(
        max(c[i] for c in bbox_corners) - min(c[i] for c in bbox_corners)
        for i in range(3)
    )
    print(f"Rendering: bbox_size={bbox_size:.3f}, dist_mult={cam_distance}")

    # (coral material already assigned via CORAL_MAT)

    # Camera — looking at coral from front-above
    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = 50  # Standard lens, minimal distortion
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj

    # Place camera at a distance that shows the whole coral with some margin
    # Use 50mm lens and compute distance to fit the coral
    sensor_w = cam_data.sensor_width  # default 36mm
    # Angular FOV: 2*atan(sensor_w / (2*lens))
    hfov = 2 * math.atan(sensor_w / (2 * cam_data.lens))
    # Distance to fit bbox_size in frame (with 30% margin)
    fit_dist = (bbox_size * 0.65) / math.tan(hfov / 2)
    dist = fit_dist * cam_distance

    # Camera position: front-above, showing coral from slight elevation
    cam_loc = Vector((
        center.x + dist * 0.4,
        center.y - dist * 0.7,
        center.z + dist * 0.55,
    ))
    cam_obj.location = cam_loc

    # Direct look-at rotation
    direction = center - cam_loc
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()

    actual_dist = (cam_loc - center).length
    print(f"  cam at {tuple(f'{x:.2f}' for x in cam_loc)}, dist={actual_dist:.2f}, lens={cam_data.lens:.1f}mm")

    # Lights — balanced key + fill for clear shape
    light_data = bpy.data.lights.new("Key", type='SUN')
    light_data.energy = 2.5
    light_data.angle = math.radians(5)
    light_obj = bpy.data.objects.new("Key", light_data)
    light_obj.rotation_euler = (math.radians(50), math.radians(10), math.radians(30))
    bpy.context.scene.collection.objects.link(light_obj)

    fill_data = bpy.data.lights.new("Fill", type='SUN')
    fill_data.energy = 1.5
    fill_obj = bpy.data.objects.new("Fill", fill_data)
    fill_obj.rotation_euler = (math.radians(70), math.radians(-30), math.radians(-50))
    bpy.context.scene.collection.objects.link(fill_obj)

    # Bottom fill to illuminate underside
    bottom_data = bpy.data.lights.new("Bottom", type='SUN')
    bottom_data.energy = 0.8
    bottom_obj = bpy.data.objects.new("Bottom", bottom_data)
    bottom_obj.rotation_euler = (math.radians(150), 0, 0)
    bpy.context.scene.collection.objects.link(bottom_obj)

    # Neutral background with subtle ambient
    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.15, 0.15, 0.17, 1)
    bg.inputs["Strength"].default_value = 0.5

    # Save .blend for debugging
    blend_path = output_path.replace('.png', '.blend')
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"Saved blend: {blend_path}")

    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 64
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    scene.render.filepath = output_path
    scene.render.image_settings.file_format = 'PNG'
    # Ground plane at coral base
    min_z = min(c.z for c in bbox_corners)
    bpy.ops.mesh.primitive_plane_add(size=8, location=(center.x, center.y, min_z + 0.05))
    plane = bpy.context.active_object
    plane_mat = bpy.data.materials.new("Ground")
    plane_mat.use_nodes = True
    plane_bsdf = plane_mat.node_tree.nodes["Principled BSDF"]
    plane_bsdf.inputs["Base Color"].default_value = (0.08, 0.07, 0.06, 1.0)
    plane_bsdf.inputs["Roughness"].default_value = 0.9
    plane.data.materials.append(plane_mat)
    # Re-select coral as active
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Make sure coral is selected and active for render
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.context.view_layer.update()

    bpy.ops.render.render(write_still=True)
    print(f"Rendered to: {output_path}")
