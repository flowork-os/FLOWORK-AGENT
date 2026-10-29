# [FL_INDEX: keywords="blender_factory, procedural_3d, TwigCoralFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: TwigCoralFactory | Category: factories_tex
# Prompt: A twig coral rendered as a textured 3D model. The coral is a sprawling, low-growing colony with many slender, twig-like branches radiating outward in all directions from a dense central base. The branches are thin and irregular, covered in fine polyp bumps and nodules giving a rough, encrusted texture. The coloring is warm dusty pink-beige with darker reddish-brown tones at the branch bases, creating a natural, organic color gradient. The wide, spreading silhouette casts a complex dense shadow on the white background below.

"""
Standalone Blender script (geometry + coral material) – TwigCoralFactory, seed 0.
Run:  blender --background --python TwigCoralFactory.py

TwigBaseCoralFactory base shape + CoralFactory.create_asset() postprocessing:
  scale with random jitter, voxel remesh at 0.01, noise/bump displacement.
"""
import os
import bpy
import numpy as np
import math
from scipy.interpolate import interp1d

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

# from FixedSeed(factory_seed). To get equivalent diversity, we hash the seed for material
# sampling (otherwise consecutive seeds all produce similar warm-red hues).
_mat_seed = ((SEED + 1) * 2654435761) & 0xFFFFFFFF  # Knuth multiplicative hash
_seed_all(_mat_seed)
_coral_base_hue = _build_base_hue()
CORAL_MAT = make_coral_material(_coral_base_hue, "TwigCoralFactory_Material")

# Re-seed for geometry (standalone uses seed for geometry params)
np.random.seed(SEED)

# ═══════════════════════════════════════════════════════════════════════════════
# Helper functions (ported from with no imports)
# ═══════════════════════════════════════════════════════════════════════════════

def rodrigues_rot(vec, axis, angle):
    """Rodrigues' rotation formula (from trees/utils/helper.py)."""

    axis = axis / (np.linalg.norm(axis) + 1e-12)
    cs = np.cos(angle)
    sn = np.sin(angle)
    return vec * cs + sn * np.cross(axis, vec) + axis * np.dot(axis, vec) * (1 - cs)

def rand_path(
    n_pts, sz=1, std=0.3, momentum=0.5,
    init_vec=(0, 0, 1), init_pt=(0, 0, 0),
    pull_dir=None, pull_init=1, pull_factor=0,
    sz_decay=1, decay_mom=True,
):
    """Random path generator (exact port from trees/tree.py:196-237)."""

    init_vec = np.array(init_vec, dtype=float)
    if pull_dir is not None:
        pull_dir = np.array(pull_dir, dtype=float)
        init_vec += pull_init * pull_dir
    init_vec = init_vec / (np.linalg.norm(init_vec) + 1e-12)

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
            new_delta += pull_factor * pull_dir
        new_delta = (new_delta / (np.linalg.norm(new_delta) + 1e-12)) * prev_sz

        if decay_mom:
            tmp_momentum = 1 - (1 - momentum) * (i + 1) / n_pts
        else:
            tmp_momentum = momentum
        delta = prev_delta * tmp_momentum + new_delta * (1 - tmp_momentum)
        delta = (delta / (np.linalg.norm(delta) + 1e-12)) * sz * (sz_decay ** i)
        path[i] = path[i - 1] + delta

    return path

def get_spawn_pt(
    path, rng=(0.5, 1),
    ang_min=np.pi / 6, ang_max=0.9 * np.pi / 2,
    rnd_idx=None, ang_sign=None, axis2=None,
    init_vec=None, z_bias=0,
):
    """Compute spawn point on parent path (exact port from trees/tree.py:240-271)."""

    n = len(path)
    if n == 1:
        return 0, path[0], init_vec

    if rnd_idx is None:
        rnd_idx = np.random.randint(int(n * rng[0]), int(n * rng[1]))
    rnd_idx = min(rnd_idx, n - 1)

    if init_vec is None:
        curr_vec = path[rnd_idx] - path[max(0, rnd_idx - 1)]
        axis1 = np.array([curr_vec[1], -curr_vec[0], 0])
        if axis2 is None:
            axis2 = rodrigues_rot(curr_vec, axis1, np.pi / 2)
        if callable(axis2):
            axis2 = axis2()
        rnd_ang = np.random.rand() * (ang_max - ang_min) + ang_min
        if ang_sign is None:
            ang_sign = np.sign(np.random.randn())
        rnd_ang *= ang_sign
        init_vec = rodrigues_rot(curr_vec, axis2, rnd_ang)

    return rnd_idx, path[rnd_idx], init_vec

# ═══════════════════════════════════════════════════════════════════════════════
# FineTreeVertices (ported from trees/tree.py:495-538)
# ═══════════════════════════════════════════════════════════════════════════════

class TreeVertices:
    def __init__(self, vtxs=None, parent=None, level=None):
        if vtxs is None:
            vtxs = np.array([[0, 0, 0]])
        elif isinstance(vtxs, list):
            vtxs = np.array(vtxs)
        parent = [-1] * len(vtxs) if parent is None else parent
        level = [0] * len(vtxs) if level is None else level
        self.vtxs = vtxs
        self.parent = parent
        self.level = level

    def get_idxs(self):
        return list(np.arange(len(self.vtxs)))

    def get_edges(self):
        edges = np.stack([np.arange(len(self.vtxs)), np.array(self.parent)], 1)
        return edges[edges[:, 1] != -1]

    def append(self, v, p, l=None):
        self.vtxs = np.append(self.vtxs, v, axis=0)
        self.parent += p
        if l is None:
            l = [0] * len(v)
        elif isinstance(l, int):
            l = [l] * len(v)
        self.level += l

    def __len__(self):
        return len(self.vtxs)

class FineTreeVertices(TreeVertices):
    def __init__(self, vtxs=None, parent=None, level=None, radius_fn=None, resolution=1):
        super().__init__(vtxs, parent, level)
        self.resolution = resolution
        if radius_fn is None:
            def radius_fn(base_radius, size, resolution):
                return [1] * size
        self.radius_fn = radius_fn
        self.detailed_locations = [[0, 0, 0]]
        self.radius = [1]
        self.detailed_parents = [-1]

    def append(self, v, p, l=None):
        super().append(v, p, l)
        f = interp1d(
            np.arange(len(v) + 1),
            np.concatenate([self.vtxs[p[0]:p[0] + 1], v]),
            axis=0, kind="quadratic",
        )
        self.detailed_locations.extend(
            f(np.linspace(0, len(v), len(v) * self.resolution + 1))[1:]
        )
        base_radius = self.radius[p[0] * self.resolution]
        self.radius.extend(self.radius_fn(base_radius, len(v), self.resolution))
        self.detailed_parents.append(p[0] * self.resolution)
        self.detailed_parents.extend(
            np.arange(0, len(v) * self.resolution - 1)
            + len(self.detailed_parents) - 1
        )

    @property
    def edges(self):
        edges = np.stack(
            [np.arange(len(self.detailed_locations)),
             np.array(self.detailed_parents)], 1,
        )
        return edges[edges[:, 1] != -1]

    def fix_first(self):
        self.radius[0] = self.radius[1]

# ═══════════════════════════════════════════════════════════════════════════════
# recursive_path (ported from trees/tree.py:274-310)
# ═══════════════════════════════════════════════════════════════════════════════

def recursive_path(
    tree, parent_idxs, level,
    path_kargs=None, spawn_kargs=None,
    n=1, symmetry=False, children=None,
):
    if path_kargs is None:
        return
    if symmetry:
        n = 2 * n

    for branch_idx in range(n):
        curr_idx = branch_idx // 2 if symmetry else branch_idx
        curr_path = path_kargs(curr_idx)
        curr_spawn = spawn_kargs(curr_idx)
        if symmetry:
            curr_spawn["ang_sign"] = 2 * (branch_idx % 2) - 1

        parent_idx, init_pt, init_vec = get_spawn_pt(
            tree.vtxs[parent_idxs], **curr_spawn
        )
        parent_idx = parent_idxs[parent_idx]

        path = rand_path(**curr_path, init_pt=init_pt, init_vec=init_vec)
        new_vtxs = path[1:]
        new_idxs = list(np.arange(len(new_vtxs)) + len(tree))
        node_idxs = [parent_idx] + new_idxs
        tree.append(new_vtxs, node_idxs[:-1], level)

        if children is not None:
            for c in children:
                recursive_path(tree, node_idxs, level + 1, **c)

# ═══════════════════════════════════════════════════════════════════════════════
# build_radius_tree (ported from trees/tree.py:541-552)
# ═══════════════════════════════════════════════════════════════════════════════

def build_radius_tree(radius_fn, branch_config, base_radius=0.002, resolution=1):
    vtx = FineTreeVertices(
        np.zeros((1, 3)), radius_fn=radius_fn, resolution=resolution
    )
    recursive_path(vtx, vtx.get_idxs(), level=0, **branch_config)

    locations = np.array(vtx.detailed_locations)
    edges = vtx.edges

    mesh = bpy.data.meshes.new("tree_skeleton")
    mesh.from_pydata(locations.tolist(), edges.tolist(), [])
    mesh.update()

    obj = bpy.data.objects.new("tree_skeleton", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    vg = obj.vertex_groups.new(name="radius")
    for i, r in enumerate(vtx.radius):
        vg.add([i], base_radius * r, "REPLACE")

    return obj

# ═══════════════════════════════════════════════════════════════════════════════
# radius_fn (from corals/tree.py:172-182)
# ═══════════════════════════════════════════════════════════════════════════════

def radius_fn(base_radius, size, resolution):
    radius_decay_root = 0.85
    radius_decay_leaf = np.random.uniform(0.4, 0.6)
    radius = base_radius * radius_decay_root ** (
        np.arange(size * resolution) / resolution
    )
    radius[-resolution:] *= radius_decay_leaf ** (
        np.arange(resolution) / resolution
    )
    return radius

# ═══════════════════════════════════════════════════════════════════════════════
# twig_config (from corals/tree.py:109-170)
# ═══════════════════════════════════════════════════════════════════════════════

n_branch = np.random.randint(6, 8)
n_major = np.random.randint(4, 5)
n_minor = np.random.randint(4, 5)
n_detail = np.random.randint(3, 4)
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

major_config = {
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
            math.sqrt(1 - span * span),
        ]
    },
    "children": [minor_config],
}

twig_config = major_config

# ═══════════════════════════════════════════════════════════════════════════════
# Build skeleton mesh (same as TwigBaseCoralFactory)
# ═══════════════════════════════════════════════════════════════════════════════

print("Building twig coral skeleton...")
obj = build_radius_tree(radius_fn, twig_config, base_radius=0.08, resolution=16)

max_xy = max(obj.dimensions[0], obj.dimensions[1], 1e-6)
scale_factor = 2.0 / max_xy
obj.scale = (scale_factor, scale_factor, scale_factor)
bpy.ops.object.transform_apply(scale=True)

print(f"Skeleton: {len(obj.data.vertices)} verts, {len(obj.data.edges)} edges")

# ═══════════════════════════════════════════════════════════════════════════════
# Apply geo_radius via Geometry Nodes
# ═══════════════════════════════════════════════════════════════════════════════

ng = bpy.data.node_groups.new("geo_radius", 'GeometryNodeTree')
ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

n_input = ng.nodes.new("NodeGroupInput")
n_output = ng.nodes.new("NodeGroupOutput")

n_mesh2curve = ng.nodes.new("GeometryNodeMeshToCurve")
ng.links.new(n_input.outputs["Geometry"], n_mesh2curve.inputs["Mesh"])

# align_tilt
n_tangent = ng.nodes.new("GeometryNodeInputTangent")
n_normal = ng.nodes.new("GeometryNodeInputNormal")

n_norm_tangent = ng.nodes.new("ShaderNodeVectorMath")
n_norm_tangent.operation = "NORMALIZE"
ng.links.new(n_tangent.outputs[0], n_norm_tangent.inputs[0])

n_axis = ng.nodes.new("ShaderNodeVectorMath")
n_axis.operation = "NORMALIZE"
n_axis.inputs[0].default_value = (0, 0, 1)

n_dot_at = ng.nodes.new("ShaderNodeVectorMath")
n_dot_at.operation = "DOT_PRODUCT"
ng.links.new(n_axis.outputs[0], n_dot_at.inputs[0])
ng.links.new(n_norm_tangent.outputs[0], n_dot_at.inputs[1])

n_scale_t = ng.nodes.new("ShaderNodeVectorMath")
n_scale_t.operation = "SCALE"
ng.links.new(n_norm_tangent.outputs[0], n_scale_t.inputs[0])
ng.links.new(n_dot_at.outputs["Value"], n_scale_t.inputs["Scale"])

n_sub_axis = ng.nodes.new("ShaderNodeVectorMath")
n_sub_axis.operation = "SUBTRACT"
ng.links.new(n_axis.outputs[0], n_sub_axis.inputs[0])
ng.links.new(n_scale_t.outputs[0], n_sub_axis.inputs[1])

n_norm_axis = ng.nodes.new("ShaderNodeVectorMath")
n_norm_axis.operation = "NORMALIZE"
ng.links.new(n_sub_axis.outputs[0], n_norm_axis.inputs[0])

n_cos = ng.nodes.new("ShaderNodeVectorMath")
n_cos.operation = "DOT_PRODUCT"
ng.links.new(n_norm_axis.outputs[0], n_cos.inputs[0])
ng.links.new(n_normal.outputs[0], n_cos.inputs[1])

n_cross = ng.nodes.new("ShaderNodeVectorMath")
n_cross.operation = "CROSS_PRODUCT"
ng.links.new(n_normal.outputs[0], n_cross.inputs[0])
ng.links.new(n_norm_axis.outputs[0], n_cross.inputs[1])

n_sin = ng.nodes.new("ShaderNodeVectorMath")
n_sin.operation = "DOT_PRODUCT"
ng.links.new(n_cross.outputs[0], n_sin.inputs[0])
ng.links.new(n_norm_tangent.outputs[0], n_sin.inputs[1])

n_atan2 = ng.nodes.new("ShaderNodeMath")
n_atan2.operation = "ARCTAN2"
ng.links.new(n_sin.outputs["Value"], n_atan2.inputs[0])
ng.links.new(n_cos.outputs["Value"], n_atan2.inputs[1])

n_set_tilt = ng.nodes.new("GeometryNodeSetCurveTilt")
ng.links.new(n_mesh2curve.outputs[0], n_set_tilt.inputs["Curve"])
ng.links.new(n_atan2.outputs[0], n_set_tilt.inputs["Tilt"])

# SetCurveRadius from named attribute
n_named_attr = ng.nodes.new("GeometryNodeInputNamedAttribute")
n_named_attr.data_type = "FLOAT"
n_named_attr.inputs["Name"].default_value = "radius"

n_set_radius = ng.nodes.new("GeometryNodeSetCurveRadius")
ng.links.new(n_set_tilt.outputs[0], n_set_radius.inputs["Curve"])
for out in n_named_attr.outputs:
    if out.type == 'VALUE':
        ng.links.new(out, n_set_radius.inputs["Radius"])
        break

# CurveCircle(32)
n_circle = ng.nodes.new("GeometryNodeCurvePrimitiveCircle")
n_circle.inputs["Resolution"].default_value = 32

# CurveToMesh with Scale input for Blender 5.0
n_curve2mesh = ng.nodes.new("GeometryNodeCurveToMesh")
ng.links.new(n_set_radius.outputs[0], n_curve2mesh.inputs["Curve"])
ng.links.new(n_circle.outputs[0], n_curve2mesh.inputs["Profile Curve"])
n_named_attr2 = ng.nodes.new("GeometryNodeInputNamedAttribute")
n_named_attr2.data_type = "FLOAT"
n_named_attr2.inputs["Name"].default_value = "radius"
for out in n_named_attr2.outputs:
    if out.type == 'VALUE':
        try:
            ng.links.new(out, n_curve2mesh.inputs["Scale"])
        except Exception:
            pass
        break

# MergeByDistance(0.004)
n_merge = ng.nodes.new("GeometryNodeMergeByDistance")
ng.links.new(n_curve2mesh.outputs[0], n_merge.inputs["Geometry"])
n_merge.inputs["Distance"].default_value = 0.004

ng.links.new(n_merge.outputs[0], n_output.inputs["Geometry"])

mod = obj.modifiers.new("geo_radius", 'NODES')
mod.node_group = ng

print("Applying geo_radius modifier...")
bpy.ops.object.modifier_apply(modifier="geo_radius")
bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

print(f"Base mesh: {len(obj.data.vertices)} verts, {len(obj.data.polygons)} faces")

# ═══════════════════════════════════════════════════════════════════════════════
# coral_postprocess (from corals/generate.py CoralFactory.create_asset)
# ═══════════════════════════════════════════════════════════════════════════════

# 1. Scale with random jitter: 2 * default_scale / max(dims[:2]) * uniform(0.8, 1.2, 3)
default_scale = np.array([1, 1, 1], dtype=float)
noise_strength = 0.01
bump_prob = 0.3

dims = [obj.dimensions.x, obj.dimensions.y, obj.dimensions.z]
max_xy = max(dims[0], dims[1], 1e-6)
scale = 2.0 * default_scale / max_xy * np.random.uniform(0.8, 1.2, 3)
obj.scale = tuple(scale)
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.transform_apply(scale=True)

# 2. Voxel remesh at face_size=0.01
m_rem = obj.modifiers.new("Remesh", "REMESH")
m_rem.mode = "VOXEL"
m_rem.voxel_size = 0.01
bpy.ops.object.modifier_apply(modifier="Remesh")

# 3. Noise/bump displacement
has_bump = np.random.uniform() < bump_prob
if noise_strength > 0:
    if has_bump:
        # apply_noise_texture: STUCCI or MARBLE
        tex_type = np.random.choice(['STUCCI', 'MARBLE'])
        tex = bpy.data.textures.new("coral_noise", type=tex_type)
        tex.noise_scale = math.exp(np.random.uniform(math.log(0.01), math.log(0.02)))
        m_d = obj.modifiers.new("Noise", "DISPLACE")
        m_d.texture = tex
        m_d.strength = noise_strength * np.random.uniform(0.9, 1.2)
        m_d.mid_level = 0
        bpy.ops.object.modifier_apply(modifier=m_d.name)
    else:
        # apply_bump: VORONOI
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

# ── assign coral material ──
obj.data.materials.clear()
obj.data.materials.append(CORAL_MAT)

obj.name = "TwigCoralFactory"
print(f"Done: TwigCoralFactory  verts={len(obj.data.vertices)}  faces={len(obj.data.polygons)}")

