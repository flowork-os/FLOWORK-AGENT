# [FL_INDEX: keywords="blender_factory, procedural_3d, TreeBaseCoralFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: TreeBaseCoralFactory | Category: factories_geo
# Prompt: A white base mesh 3D model of a tree coral structure. The object shows a multi-branching coral skeleton with numerous arms extending outward in all directions from a shared central root — thicker branches near the base split into progressively thinner, shorter sub-branches toward the tips, creating a sprawling tree-like topology. Without any texture or material, the white smooth geometry exposes the full branching hierarchy and the wide, irregular footprint with a complex cast shadow on the white background.

"""
Standalone Blender script (geometry + coral material) – TreeBaseCoralFactory, seed 0.
Run:  blender --background --python TreeBaseCoralFactory.py

  rand_path (momentum-damped random walk) → get_spawn_pt (Rodrigues rotation)
  → FineTreeVertices (quadratic interpolation, resolution=16)
  → hierarchical radius decay → curve-based tube conversion.

Randomly selects bush or twig variant (50/50).
"""
import os
import random
import colorsys
import bpy
import numpy as np
import math
from scipy.interpolate import interp1d


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
CORAL_MAT = make_coral_material(_coral_base_hue, "TreeBaseCoralFactory_Material")

# Re-seed for geometry (standalone uses seed for geometry params)
np.random.seed(SEED)



# ── Helper: Rodrigues rotation ───────────────────────────────────────────────

def rodrigues_rot(v, k, theta):
    """Rotate vector v around axis k by angle theta."""

    k = np.array(k, dtype=float)
    nk = np.linalg.norm(k)
    if nk < 1e-12:
        return np.array(v, dtype=float)
    k = k / nk
    v = np.array(v, dtype=float)
    ct, st = math.cos(theta), math.sin(theta)
    return v * ct + np.cross(k, v) * st + k * np.dot(k, v) * (1 - ct)


# ── Random walk path generator (matches tree.py rand_path) ──────────────────

def rand_path(n_pts, sz=1.0, std=0.3, momentum=0.5, init_vec=None, init_pt=None,
              pull_dir=None, pull_init=1, pull_factor=0, sz_decay=1, decay_mom=True):
    """Generate a smooth random walk path with momentum-damped direction."""

    if init_vec is None:
        init_vec = [0, 0, 1]
    if init_pt is None:
        init_pt = [0, 0, 0]
    init_vec = np.array(init_vec, dtype=float)
    init_pt = np.array(init_pt, dtype=float)

    if pull_dir is not None:
        pull_dir = np.array(pull_dir, dtype=float)
        init_vec = init_vec + pull_init * pull_dir
    norm = np.linalg.norm(init_vec)
    if norm > 1e-12:
        init_vec = init_vec / norm

    path = np.zeros((n_pts, 3))
    path[0] = init_pt

    for i in range(1, n_pts):
        if i == 1:
            prev_delta = init_vec * sz
        else:
            prev_delta = path[i - 1] - path[i - 2]

        prev_sz = np.linalg.norm(prev_delta)
        new_delta = prev_delta + np.random.randn(3) * std

        if pull_dir is not None:
            new_delta = new_delta + pull_factor * pull_dir

        nd_norm = np.linalg.norm(new_delta)
        if nd_norm > 1e-12:
            new_delta = (new_delta / nd_norm) * prev_sz

        if decay_mom:
            tmp_momentum = 1 - (1 - momentum) * (i + 1) / n_pts
        else:
            tmp_momentum = momentum

        delta = prev_delta * tmp_momentum + new_delta * (1 - tmp_momentum)
        d_norm = np.linalg.norm(delta)
        if d_norm > 1e-12:
            delta = (delta / d_norm) * sz * (sz_decay ** i)

        path[i] = path[i - 1] + delta

    return path


# ── Spawn point selection (matches tree.py get_spawn_pt) ─────────────────────

def get_spawn_pt(path, rnd_idx=None, ang_min=np.pi / 6, ang_max=0.9 * np.pi / 2,
                 ang_sign=None, axis2=None, init_vec=None, rng=None, z_bias=0):
    """Find spawn point and initial direction on parent path."""

    if rng is None:
        rng = [0.5, 1.0]
    n = len(path)
    if n == 1:
        iv = np.array(init_vec if init_vec is not None else [0, 0, 1], dtype=float)
        return 0, path[0].copy(), iv

    if rnd_idx is None:
        lo = max(1, int(n * rng[0]))
        hi = max(lo + 1, int(n * rng[1]))
        rnd_idx = np.random.randint(lo, hi)
    rnd_idx = min(rnd_idx, n - 1)

    if init_vec is not None:
        return rnd_idx, path[rnd_idx].copy(), np.array(init_vec, dtype=float)

    # Direction at spawn point
    prev = max(0, rnd_idx - 1)
    curr_vec = path[rnd_idx] - path[prev]
    if np.linalg.norm(curr_vec) < 1e-10:
        curr_vec = np.array([0.0, 0.0, 1.0])

    # Perpendicular axis
    axis1 = np.array([curr_vec[1], -curr_vec[0], 0.0])
    if np.linalg.norm(axis1) < 1e-10:
        axis1 = np.array([1.0, 0.0, 0.0])

    if axis2 is None:
        axis2 = rodrigues_rot(curr_vec, axis1, np.pi / 2)
    if callable(axis2):
        axis2 = axis2()
    axis2 = np.array(axis2, dtype=float)

    rnd_ang = np.random.rand() * (ang_max - ang_min) + ang_min
    if ang_sign is None:
        ang_sign = np.sign(np.random.randn())
    rnd_ang *= ang_sign

    result_vec = rodrigues_rot(curr_vec, axis2, rnd_ang)
    return rnd_idx, path[rnd_idx].copy(), result_vec


# ── Radius function (matches coral tree.py) ──────────────────────────────────

def radius_fn(base_radius, size, resolution):
    """Exponential decay with faster leaf decay at tips."""

    decay_root = 0.85
    decay_leaf = np.random.uniform(0.4, 0.6)
    total = size * resolution
    r = base_radius * decay_root ** (np.arange(total) / resolution)
    r[-resolution:] *= decay_leaf ** (np.arange(resolution) / resolution)
    return r


# ── Branch config (bush / twig, 50/50 random choice) ────────────────────────

method = np.random.choice(["twig", "bush"], p=[0.5, 0.5])
print(f"  Method: {method}")

n_branch = np.random.randint(6, 8)
n_major = np.random.randint(4, 5)
n_minor = np.random.randint(4, 5)
n_detail = np.random.randint(3, 4)

if method == "bush":
    span = np.random.uniform(0.4, 0.5)
    detail_config = {
        "n": n_minor,
        "path_kargs": lambda idx: {
            "n_pts": n_detail + 1,
            "std": 0.4,
            "momentum": 0.6,
            "sz": 0.01 * (1.5 * n_detail - idx),
        },
        "spawn_kargs": lambda idx: {
            "rnd_idx": idx + 1,
            "ang_min": np.pi / 12,
            "ang_max": np.pi / 8,
            "axis2": [0, 0, 1],
        },
        "children": [],
    }
    minor_config = {
        "n": n_major,
        "path_kargs": lambda idx: {
            "n_pts": n_minor + 1,
            "std": 0.4,
            "momentum": 0.4,
            "sz": 0.03 * (1.2 * n_minor - idx),
        },
        "spawn_kargs": lambda idx: {
            "rnd_idx": idx + 1,
            "ang_min": np.pi / 12,
            "ang_max": np.pi / 8,
            "axis2": [0, 0, 1],
        },
        "children": [detail_config],
    }
    branch_config = {
        "n": n_branch,
        "path_kargs": lambda idx: {
            "n_pts": n_major + 1,
            "std": 0.4,
            "momentum": 0.4,
            "sz": np.random.uniform(0.08, 0.1),
        },
        "spawn_kargs": lambda idx: {
            "init_vec": [
                span * np.cos(2 * np.pi * idx / n_branch + np.random.uniform(-np.pi / 9, np.pi / 9)),
                span * np.sin(2 * np.pi * idx / n_branch + np.random.uniform(-np.pi / 9, np.pi / 9)),
                math.sqrt(max(0, 1 - span * span)),
            ]
        },
        "children": [minor_config],
    }
else:  # twig
    span = np.random.uniform(0.7, 0.8)
    detail_config = {
        "n": n_minor,
        "path_kargs": lambda idx: {
            "n_pts": n_detail * 2 + 1,
            "std": 0.4,
            "momentum": 0.6,
            "sz": 0.01 * (2.5 * n_detail - idx),
        },
        "spawn_kargs": lambda idx: {
            "rnd_idx": 2 * idx + 1,
            "ang_min": np.pi / 8,
            "ang_max": np.pi / 6,
            "axis2": [0, 0, 1],
        },
        "children": [],
    }
    minor_config = {
        "n": n_major,
        "path_kargs": lambda idx: {
            "n_pts": n_minor * 2 + 1,
            "std": 0.4,
            "momentum": 0.4,
            "sz": 0.03 * (2.2 * n_minor - idx),
        },
        "spawn_kargs": lambda idx: {
            "rnd_idx": 2 * idx + 1,
            "ang_min": np.pi / 8,
            "ang_max": np.pi / 6,
            "axis2": [0, 0, 1],
        },
        "children": [detail_config],
    }
    branch_config = {
        "n": n_branch,
        "path_kargs": lambda idx: {
            "n_pts": n_major * 2 + 1,
            "std": 0.4,
            "momentum": 0.4,
            "sz": np.random.uniform(0.08, 0.1),
        },
        "spawn_kargs": lambda idx: {
            "init_vec": [
                span * np.cos(2 * np.pi * idx / n_branch + np.random.uniform(-np.pi / 9, np.pi / 9)),
                span * np.sin(2 * np.pi * idx / n_branch + np.random.uniform(-np.pi / 9, np.pi / 9)),
                math.sqrt(max(0, 1 - span * span)),
            ]
        },
        "children": [minor_config],
    }


# ── Recursive tree generation ────────────────────────────────────────────────

resolution = 16
base_radius = 0.08
all_branches = []  # List of (detailed_path, detailed_radii) per branch


def generate_tree(parent_coarse_path, parent_coarse_radii, level,
                  path_kargs=None, spawn_kargs=None, n=1,
                  children=None, symmetry=False):
    """Recursively generate branches with interpolation and radius decay."""

    if path_kargs is None:
        return
    if symmetry:
        n = 2 * n

    for branch_idx in range(n):
        curr_idx = branch_idx // 2 if symmetry else branch_idx
        p_args = path_kargs(curr_idx)
        s_args = spawn_kargs(curr_idx)
        if symmetry:
            s_args["ang_sign"] = 2 * (branch_idx % 2) - 1

        # Find spawn point on parent
        local_idx, init_pt, init_vec = get_spawn_pt(parent_coarse_path, **s_args)

        # Generate coarse path (includes spawn point as first point)
        coarse_path = rand_path(init_pt=init_pt, init_vec=init_vec, **p_args)
        n_new = len(coarse_path) - 1  # new points (excluding spawn)

        if n_new < 1:
            continue

        # Quadratic interpolation for smooth detailed path
        kind = 'quadratic' if n_new >= 2 else 'linear'
        f = interp1d(np.arange(n_new + 1), coarse_path, axis=0, kind=kind)
        n_detailed = n_new * resolution
        detailed_path = f(np.linspace(0, n_new, n_detailed + 1))

        # Radius: inherit from parent at spawn point, then decay
        parent_r = parent_coarse_radii[min(local_idx, len(parent_coarse_radii) - 1)]
        new_radii = radius_fn(parent_r, n_new, resolution)
        detailed_radii = np.concatenate([[parent_r], new_radii])

        all_branches.append((detailed_path, detailed_radii))

        # Recurse for children
        if children:
            # Sample coarse radii from detailed
            coarse_radii = detailed_radii[::resolution]
            # Ensure length matches coarse_path
            if len(coarse_radii) < len(coarse_path):
                coarse_radii = np.concatenate([coarse_radii, [detailed_radii[-1]]])
            for c in children:
                generate_tree(coarse_path, coarse_radii[:len(coarse_path)], level + 1, **c)


# Build the tree from root [0,0,0]
root_path = np.array([[0.0, 0.0, 0.0]])
root_radii = np.array([1.0])
generate_tree(root_path, root_radii, level=0, **branch_config)

print(f"  Branches: {len(all_branches)}")
total_pts = sum(len(p) for p, _ in all_branches)
print(f"  Total detailed points: {total_pts}")


# ── Create Blender curves from branches ──────────────────────────────────────

# Compute scale factor from raw positions FIRST (before creating curves).
# The original scales skeleton positions, THEN creates tubes with absolute radii.
# Blender's transform_apply scales point.radius too, so we must pre-scale positions
# and set radii at their absolute values to match the original.
all_raw_pts = np.vstack([p for p, _ in all_branches])
raw_max_dim = max(all_raw_pts[:, 0].max() - all_raw_pts[:, 0].min(), all_raw_pts[:, 1].max() - all_raw_pts[:, 1].min(), 1e-6)
scale_factor = 2.0 / raw_max_dim
print(f"  raw_max_dim={raw_max_dim:.4f}  scale_factor={scale_factor:.4f}")

curve_data = bpy.data.curves.new("tree_curves", 'CURVE')
curve_data.dimensions = '3D'
curve_data.bevel_depth = 0.001
curve_data.bevel_resolution = 5   # ~24-sided cross-section
curve_data.use_fill_caps = True

for detailed_path, detailed_radii in all_branches:
    n = len(detailed_path)
    if n < 2:
        continue
    sp = curve_data.splines.new('POLY')
    sp.points.add(n - 1)
    for i in range(n):
        # Scale positions to fit 2 units, but keep radii at absolute values
        scaled_pos = detailed_path[i] * scale_factor
        sp.points[i].co = (*scaled_pos, 1.0)
        actual_r = detailed_radii[i] * base_radius  # absolute radius, NOT scaled
        sp.points[i].radius = actual_r / curve_data.bevel_depth

obj = bpy.data.objects.new("TreeBaseCoralFactory", curve_data)
bpy.context.scene.collection.objects.link(obj)
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active = obj

# Convert curve to mesh (no scaling needed — positions already pre-scaled)
bpy.ops.object.convert(target='MESH')

# Clean up mesh
bpy.ops.object.editmode_toggle()
bpy.ops.mesh.remove_doubles(threshold=0.002)
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.editmode_toggle()

bpy.ops.object.shade_smooth()

# Weld overlapping tubes at junctions
m_weld = obj.modifiers.new("Weld", "WELD")
m_weld.merge_threshold = 0.004
bpy.ops.object.modifier_apply(modifier="Weld")

# Origin to geometry center
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

# ── assign coral material ──
obj.data.materials.clear()
obj.data.materials.append(CORAL_MAT)

obj.name = "TreeBaseCoralFactory"
print(f"Done: TreeBaseCoralFactory  verts={len(obj.data.vertices)}  faces={len(obj.data.polygons)}")
