# [FL_INDEX: keywords="blender_factory, procedural_3d, CrabFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: CrabFactory | Category: factories_geo
# Prompt: A crab rendered as a textured 3D model. The creature features a wide, rounded carapace (shell) in rich dark reddish-brown with subtle mottled patterns and a slightly glossy surface. Two large unequal chelipeds (claws) extend forward — the dominant claw is particularly elongated and prominent with a red and white coloring and an open pincer tip. Multiple slender walking legs protrude from each side of the body in orange-brown. Two small white eye stalks are visible at the front of the carapace. The overall shape is wide and low-profile, typical of a shore crab.

import os
import bmesh
import bpy
import numpy as np
from mathutils import Euler as MEuler
from mathutils import Quaternion, Vector
from mathutils.bvhtree import BVHTree

try:
    from scipy.interpolate import interp1d
except ImportError:
    def interp1d(x, y, kind='linear', fill_value=None, bounds_error=True):
        x, y = np.asarray(x), np.asarray(y)
        def f(xi):
            return np.interp(np.asarray(xi), x, y)
        return f

SEED = int(os.environ.get("SEED", "0"))
np.random.seed(SEED)

# ═══════════════════════════════════════════════════════════════════════════
import random as _random, colorsys as _colorsys

def _seed_mat(seed):
    _mat_seed = ((seed + 1) * 2654435761) & 0xFFFFFFFF
    np.random.seed(_mat_seed); _random.seed(_mat_seed)

def _hsv2rgba(h, s, v):
    r, g, b = _colorsys.hsv_to_rgb(float(h) % 1.0, max(0, min(1, float(s))), max(0, min(1, float(v))))
    return (r, g, b, 1.0)

def _log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def _new_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat

def _fac(n):
    return n.outputs.get("Fac") or n.outputs.get("Factor") or n.outputs[0]

def make_creature_material(seed, name="CrustaceanMaterial"):
    np.random.seed(seed); _random.seed(seed)
    value_shift = _log_uniform(2, 10)
    # base_hue: crab 60% chance [0,0.05], 40% chance [0.4,0.45]
    if np.random.uniform(0, 1) < 0.6:
        base_hue = float(np.random.uniform(0, 0.05))
    else:
        base_hue = float(np.random.uniform(0.4, 0.45))
    bright_color = _hsv2rgba(base_hue, np.random.uniform(0.8, 1.0),
                              _log_uniform(0.02, 0.05) * value_shift)
    dark_color = _hsv2rgba((base_hue + float(np.random.uniform(-0.05, 0.05))) % 1,
                            np.random.uniform(0.8, 1.0),
                            _log_uniform(0.01, 0.02) * value_shift)
    light_color = _hsv2rgba(base_hue, np.random.uniform(0.0, 0.4), _log_uniform(0.2, 1.0))
    specular = float(np.random.uniform(0.6, 0.8))
    specular_tint = tuple([float(np.random.uniform(0, 1))] * 3 + [1.0])
    clearcoat = float(np.random.uniform(0.2, 0.8))
    roughness = float(np.random.uniform(0.1, 0.3))
    metallic = float(np.random.uniform(0.6, 0.8))
    musg_scale = _log_uniform(5, 8)

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new

    # -- Coordinate pipeline: NewGeometry Position -> Separate -> abs(Y) -> Combine --
    geom = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ln(geom.outputs["Position"], sep.inputs["Vector"])
    abs_y = nt.nodes.new("ShaderNodeMath")
    abs_y.operation = "ABSOLUTE"
    ln(sep.outputs["Y"], abs_y.inputs[0])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    ln(sep.outputs["X"], comb.inputs["X"])
    ln(abs_y.outputs[0], comb.inputs["Y"])
    ln(sep.outputs["Z"], comb.inputs["Z"])

    # Noise (Musgrave replacement in 5.0) -> MapRange [0,1]
    noise = nt.nodes.new("ShaderNodeTexNoise")
    ln(comb.outputs["Vector"], noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = musg_scale
    noise.inputs["Detail"].default_value = 2.0
    mr = nt.nodes.new("ShaderNodeMapRange")
    ln(_fac(noise), mr.inputs["Value"])
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = 1.0
    mr.inputs["To Min"].default_value = 0.0
    mr.inputs["To Max"].default_value = 1.0

    # 4-stop color ramp HSV
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.color_mode = "HSV"; cr.color_ramp.hue_interpolation = "NEAR"
    ln(mr.outputs["Result"], cr.inputs["Fac"])
    cr.color_ramp.elements.new(0); cr.color_ramp.elements.new(0)
    cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[0].color = bright_color
    cr.color_ramp.elements[1].position = 0.3; cr.color_ramp.elements[1].color = bright_color
    cr.color_ramp.elements[2].position = 0.7; cr.color_ramp.elements[2].color = dark_color
    cr.color_ramp.elements[3].position = 1.0; cr.color_ramp.elements[3].color = dark_color

    # Mix: original is MixRGB(ratio, light_color, color)
    # = lerp(light_color, color, ratio_attribute)
    # "ratio" attr marks top(1) vs underside(0); standalone mesh lacks it,
    # so approximate with clamp(Normal.Z * 2 + 0.5, 0, 1): top=1, bottom=0
    light_rgb = nt.nodes.new("ShaderNodeRGB"); light_rgb.outputs[0].default_value = light_color
    norm_sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ln(geom.outputs["Normal"], norm_sep.inputs["Vector"])
    ratio_scale = nt.nodes.new("ShaderNodeMath"); ratio_scale.operation = "MULTIPLY"
    ln(norm_sep.outputs["Z"], ratio_scale.inputs[0]); ratio_scale.inputs[1].default_value = 2.0
    ratio_bias = nt.nodes.new("ShaderNodeMath"); ratio_bias.operation = "ADD"
    ln(ratio_scale.outputs[0], ratio_bias.inputs[0]); ratio_bias.inputs[1].default_value = 0.5
    ratio_clamp = nt.nodes.new("ShaderNodeClamp")
    ln(ratio_bias.outputs[0], ratio_clamp.inputs["Value"])
    ratio_clamp.inputs["Min"].default_value = 0.0
    ratio_clamp.inputs["Max"].default_value = 1.0
    mix_c = nt.nodes.new("ShaderNodeMix"); mix_c.data_type = "RGBA"
    ln(ratio_clamp.outputs["Result"], mix_c.inputs[0])
    # Color1 (A, index 6) = light_color, Color2 (B, index 7) = ramp color
    ln(light_rgb.outputs[0], mix_c.inputs[6])
    ln(cr.outputs["Color"], mix_c.inputs[7])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(mix_c.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    spec_key = "Specular IOR Level" if "Specular IOR Level" in bsdf.inputs else "Specular"
    bsdf.inputs[spec_key].default_value = specular
    if "Specular Tint" in bsdf.inputs:
        bsdf.inputs["Specular Tint"].default_value = specular_tint
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = clearcoat

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def make_eye_material(name="CrustaceanEyeMaterial"):
    mat = _new_mat(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (0.1, 0.1, 0.1, 1)
    spec_key = "Specular IOR Level" if "Specular IOR Level" in bsdf.inputs else "Specular"
    bsdf.inputs[spec_key].default_value = 0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def assign_material(obj, mat):
    if obj is not None and hasattr(obj, "data") and hasattr(obj.data, "materials"):
        obj.data.materials.clear()
        obj.data.materials.append(mat)


# Phase 1: creature material
CREATURE_MAT = make_creature_material(SEED, "CrabFactory_Material")
EYE_MAT = make_eye_material("CrabFactory_EyeMaterial")
np.random.seed(SEED)



def log_uniform(low, high):
    return np.exp(np.random.uniform(np.log(low), np.log(high)))


# ═══════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for block in list(bpy.data.meshes):
        bpy.data.meshes.remove(block)
    for block in list(bpy.data.curves):
        bpy.data.curves.remove(block)


def select_only(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def apply_tf(obj, loc=True, rot=True, scale=True):
    select_only(obj)
    bpy.ops.object.transform_apply(location=loc, rotation=rot, scale=scale)


def join_objs(objs):
    objs = [o for o in objs if o is not None]
    if not objs:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.active_object


def add_modifier(obj, mod_type, apply=True, **kwargs):
    select_only(obj)
    mod = obj.modifiers.new("mod", mod_type)
    for k, v in kwargs.items():
        setattr(mod, k, v)
    if apply:
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return mod


def read_co(obj):
    n = len(obj.data.vertices)
    if n == 0:
        return np.zeros((0, 3))
    arr = np.zeros(n * 3)
    obj.data.vertices.foreach_get("co", arr)
    return arr.reshape(-1, 3)


def write_co(obj, co):
    obj.data.vertices.foreach_set("co", co.ravel())
    obj.data.update()


def displace_vertices(obj, fn):
    co = read_co(obj)
    if len(co) == 0:
        return
    x, y, z = co.T
    dx, dy, dz = fn(x, y, z)
    co[:, 0] += np.asarray(dx, dtype=float).ravel()
    co[:, 1] += np.asarray(dy, dtype=float).ravel()
    co[:, 2] += np.asarray(dz, dtype=float).ravel()
    write_co(obj, co)


def remove_verts_by_mask(obj, mask):
    indices = np.nonzero(mask)[0]
    if len(indices) == 0:
        return
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    geom = [bm.verts[i] for i in indices]
    bmesh.ops.delete(bm, geom=geom, context='VERTS')
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def keep_largest_island(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    visited = set()
    islands = []
    for v in bm.verts:
        if v.index in visited:
            continue
        island = []
        stack = [v]
        while stack:
            cur = stack.pop()
            if cur.index in visited:
                continue
            visited.add(cur.index)
            island.append(cur)
            for e in cur.link_edges:
                other = e.other_vert(cur)
                if other.index not in visited:
                    stack.append(other)
        islands.append(island)
    if len(islands) > 1:
        largest = max(islands, key=len)
        largest_set = {v.index for v in largest}
        to_remove = [v for v in bm.verts if v.index not in largest_set]
        if to_remove:
            bmesh.ops.delete(bm, geom=to_remove, context='VERTS')
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def write_attr(obj, name, data, data_type='FLOAT', domain='POINT'):
    attr = obj.data.attributes.get(name)
    if attr is not None:
        obj.data.attributes.remove(attr)
    attr = obj.data.attributes.new(name, data_type, domain)
    attr.data.foreach_set("value", data.ravel())


def read_attr(obj, name):
    attr = obj.data.attributes[name]
    data = np.zeros(len(attr.data))
    attr.data.foreach_get("value", data)
    return data


def deep_clone(obj):
    new_mesh = obj.data.copy()
    new_obj = obj.copy()
    new_obj.data = new_mesh
    bpy.context.scene.collection.objects.link(new_obj)
    return new_obj


# ═══════════════════════════════════════════════════════════════════
# BEZIER / SPIN / LEAF
# ═══════════════════════════════════════════════════════════════════

def bezier_curve(anchors, vector_locations=(), resolution=None):
    """Create mesh polyline from bezier control points."""

    n = next(len(r) for r in anchors if hasattr(r, '__len__'))
    anchors_arr = np.array([
        np.array(r, dtype=float) if hasattr(r, '__len__') else np.full(n, float(r))
        for r in anchors
    ])

    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0))
    obj = bpy.context.active_object

    if n > 2:
        select_only(obj)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.subdivide(number_cuts=n - 2)
        bpy.ops.object.mode_set(mode='OBJECT')

    points = obj.data.splines[0].bezier_points
    for i in range(n):
        points[i].co = anchors_arr[:, i]
    for i in range(n):
        if i in vector_locations:
            points[i].handle_left_type = "VECTOR"
            points[i].handle_right_type = "VECTOR"
        else:
            points[i].handle_left_type = "AUTO"
            points[i].handle_right_type = "AUTO"

    obj.data.splines[0].resolution_u = resolution if resolution is not None else 12

    # Arc-length subdivision (curve2mesh)
    cos = np.array([p.co for p in points])
    seg_lengths = np.linalg.norm(cos[:-1] - cos[1:], axis=-1)

    select_only(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    for i in range(len(points)):
        pts = obj.data.splines[0].bezier_points
        if pts[i].handle_left_type == "FREE":
            pts[i].handle_left_type = "ALIGNED"
        if pts[i].handle_right_type == "FREE":
            pts[i].handle_right_type = "ALIGNED"
    for i in reversed(range(len(seg_lengths))):
        pts = list(obj.data.splines[0].bezier_points)
        number_cuts = min(int(seg_lengths[i] / 5e-3) - 1, 64)
        if number_cuts < 0:
            continue
        bpy.ops.curve.select_all(action="DESELECT")
        pts[i].select_control_point = True
        pts[i + 1].select_control_point = True
        bpy.ops.curve.subdivide(number_cuts=number_cuts)
    obj.data.splines[0].resolution_u = 1
    bpy.ops.object.mode_set(mode='OBJECT')

    select_only(obj)
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.active_object
    add_modifier(obj, "WELD", merge_threshold=1e-3)
    return obj


def remesh_fill(obj, resolution=0.015):
    """Convert filled flat polygon to open surface with uniform vertices."""

    add_modifier(obj, "SOLIDIFY", thickness=0.1, offset=-1)
    add_modifier(obj, "REMESH", mode='VOXEL', voxel_size=resolution)
    co = read_co(obj)
    if len(co) == 0:
        return obj
    z_mid = (co[:, 2].min() + co[:, 2].max()) / 2
    if abs(co[:, 2].min()) > abs(co[:, 2].max()):
        remove_verts_by_mask(obj, co[:, 2] < z_mid)
    else:
        remove_verts_by_mask(obj, co[:, 2] > z_mid)
    co = read_co(obj)
    if len(co) > 0:
        co[:, 2] = 0
        write_co(obj, co)
    return obj


def spin_mesh(anchors, vector_locations=(), axis=(0, 0, 1)):
    """Create surface of revolution from bezier profile."""

    obj = bezier_curve(anchors, vector_locations)
    co = read_co(obj)
    axis_arr = np.array(axis, dtype=float)
    axis_arr = axis_arr / (np.linalg.norm(axis_arr) + 1e-10)
    proj = (co @ axis_arr)[:, np.newaxis] * axis_arr[np.newaxis, :]
    mean_radius = np.mean(np.linalg.norm(co - proj, axis=-1))
    rot_res = max(min(int(2 * np.pi * mean_radius / 5e-3), 128), 8)

    add_modifier(obj, "WELD", merge_threshold=1e-3)

    select_only(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.spin(
        steps=rot_res, angle=np.pi * 2,
        center=(0.0, 0.0, 0.0), axis=axis
    )
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=1e-3)
    bpy.ops.object.mode_set(mode='OBJECT')
    return obj


def leaf_mesh(x_anchors, y_anchors, vector_locations=(), subdivision=64):
    """Create leaf-shaped flat mesh from two mirrored bezier curves."""

    curves = []
    for sign in [-1, 1]:
        anchors = [x_anchors, sign * np.array(y_anchors), 0]
        curves.append(bezier_curve(anchors, vector_locations, subdivision))
    obj = join_objs(curves)
    add_modifier(obj, "WELD", merge_threshold=0.001)

    select_only(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.fill()
    bpy.ops.object.mode_set(mode='OBJECT')

    remesh_fill(obj)
    keep_largest_island(obj)
    return obj


def distance2boundary(obj):
    """BFS distance from boundary vertices, normalized to [0, 1]."""

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    n_verts = len(bm.verts)

    boundary = set()
    for e in bm.edges:
        if e.is_boundary:
            boundary.add(e.verts[0].index)
            boundary.add(e.verts[1].index)

    distance = np.full(n_verts, -1.0)
    queue = set(boundary)
    d = 0
    while queue:
        for idx in queue:
            distance[idx] = d
        nxt = set()
        for idx in queue:
            for e in bm.verts[idx].link_edges:
                oi = e.other_vert(bm.verts[idx]).index
                if distance[oi] < 0:
                    nxt.add(oi)
        queue = nxt
        d += 1
    bm.free()

    distance[distance < 0] = 0
    max_d = max(d - 1, 1)
    distance /= max_d
    write_attr(obj, "distance", distance)
    return distance


# ═══════════════════════════════════════════════════════════════════
# NOISE HELPER
# ═══════════════════════════════════════════════════════════════════

def pseudo_noise(positions, scale=1.0):
    """Multi-octave sinusoidal noise approximation (symmetric in y)."""

    p = positions * scale
    return (
        np.sin(p[:, 0] * 1.0 + p[:, 1] * 2.3 + p[:, 2] * 1.7) * 0.30
        + np.sin(p[:, 0] * 3.1 + p[:, 1] * 0.7 + p[:, 2] * 2.9) * 0.30
        + np.sin(p[:, 0] * 5.3 + p[:, 1] * 4.1 + p[:, 2] * 3.3) * 0.20
        + np.sin(p[:, 0] * 7.7 + p[:, 1] * 6.5 + p[:, 2] * 5.1) * 0.10
        + np.sin(p[:, 0] * 11.3 + p[:, 1] * 9.7 + p[:, 2] * 8.3) * 0.10
    )


# ═══════════════════════════════════════════════════════════════════
# BODY CONSTRUCTION
# ═══════════════════════════════════════════════════════════════════

def sample_body_params():
    x_length = np.random.uniform(0.8, 1.2)
    y_length = x_length * np.random.uniform(0.5, 0.7)
    x_tip = np.random.uniform(0.3, 0.6)
    y_tail = np.random.uniform(0.1, 0.3)
    has_sharp_tip = np.random.uniform(0, 1) < 0.4
    front_midpoint = np.random.uniform(0.7, 0.9)
    back_midpoint = np.random.uniform(0.7, 0.9)
    front_angle = np.random.uniform(np.pi / 12, np.pi / 8)
    back_angle = np.random.uniform(np.pi / 6, np.pi / 4)
    tip_size = np.random.uniform(0.05, 0.15)
    upper_z = x_length * np.random.uniform(0.15, 0.3)
    upper_alpha = np.random.uniform(0.8, 0.9)
    upper_shift = np.random.uniform(-0.6, -0.4)
    noise_strength = np.random.uniform(0.02, 0.03)
    noise_scale = np.random.uniform(8, 15)
    lower_alpha = np.random.uniform(0.96, 0.98)
    lower_z = x_length * np.random.uniform(0.3, 0.4)
    lower_shift = np.random.uniform(0.1, 0.2)
    spike_height = np.random.uniform(0.05, 0.2) if np.random.uniform(0, 1) < 0.5 else 0
    spike_depth = log_uniform(0.4, 2)
    spike_center = np.random.uniform(0.3, 0.7)
    spike_density = log_uniform(100, 500)
    # Consume same random calls as original (mouth + color_cutoff) to keep state in sync
    _mouth_z = np.random.uniform(0.5, 0.8)
    _mouth_x = np.random.uniform(0.1, 0.15)
    _mouth_noise_scale = np.random.uniform(10, 15)
    _mouth_noise_strength = np.random.uniform(0.1, 0.2)
    bend_angle = np.random.uniform(0, np.pi / 3)
    bend_height = np.random.uniform(0.08, 0.12)
    _color_cutoff = np.random.uniform(0, 0.5)
    return dict(
        x_length=x_length, y_length=y_length, x_tip=x_tip, y_tail=y_tail,
        has_sharp_tip=has_sharp_tip,
        front_midpoint=front_midpoint, back_midpoint=back_midpoint,
        front_angle=front_angle, back_angle=back_angle, tip_size=tip_size,
        upper_z=upper_z, upper_alpha=upper_alpha, upper_shift=upper_shift,
        noise_strength=noise_strength, noise_scale=noise_scale,
        lower_z=lower_z, lower_alpha=lower_alpha, lower_shift=lower_shift,
        spike_height=spike_height, spike_depth=spike_depth,
        spike_density=spike_density, spike_center=spike_center,
        bend_angle=bend_angle, bend_height=bend_height,
    )


def make_body_surface(params):
    x_length = params['x_length']
    y_length = params['y_length']
    x_tip = params['x_tip']
    y_tail = params['y_tail']

    x_anchors = np.array(
        [0, 0, -x_tip / 2, -x_tip, -x_tip, -x_tip, -(x_tip + 1) / 2, -1, -1]
    ) * x_length
    y_anchors = np.array([
        0, 0.1, params['front_midpoint'], 1, 1, 1,
        params['back_midpoint'], y_tail, 0
    ]) * y_length

    tip_size = params['tip_size']
    if params['has_sharp_tip']:
        fa, ba = params['front_angle'], params['back_angle']
        x_anchors[3] += tip_size * np.sin(fa) * x_length
        x_anchors[5] -= tip_size * np.sin(ba) * x_length
        y_anchors[3] += tip_size * (1 - np.cos(fa)) * x_length
        y_anchors[4] += tip_size * x_length
        y_anchors[5] += tip_size * (1 - np.cos(ba)) * x_length
        vlocs = [4]
    else:
        x_anchors[3] += 0.05 * x_tip * x_length
        x_anchors[5] -= 0.05 * (1 - x_tip) * x_length
        vlocs = []

    obj = leaf_mesh(x_anchors, y_anchors, vlocs)
    add_modifier(obj, "SUBSURF", levels=1, render_levels=1)
    distance2boundary(obj)
    return obj


def make_surface_side(obj, params, prefix='upper'):
    dist = read_attr(obj, 'distance')
    height_fn = interp1d([0, 0.5, 1], [0, params[f'{prefix}_alpha'], 1], 'quadratic')
    direction = 1 if prefix == 'upper' else -1
    z_height = params[f'{prefix}_z']

    co = read_co(obj)
    co[:, 2] += direction * height_fn(dist) * z_height
    write_co(obj, co)

    shift = params[f'{prefix}_shift']
    co = read_co(obj)
    co[:, 0] += shift * co[:, 2]
    write_co(obj, co)

    # Symmetric noise approximation (replaces Musgrave texture)
    co = read_co(obj)
    x, y, z = co.T
    sym_pos = np.column_stack([x, np.abs(y), z])
    noise = pseudo_noise(sym_pos, params['noise_scale'])
    co[:, 2] += dist * noise * params['noise_strength']
    write_co(obj, co)
    return obj


def add_spikes(obj, params):
    spike_height = params['spike_height']
    if spike_height <= 0:
        return
    co = read_co(obj)
    x, y, z = co.T
    candidates = np.where((y > 0) & (z > 0.02))[0]
    if len(candidates) == 0:
        return
    n_spikes = min(int(params['spike_density'] * 0.1), len(candidates))
    if n_spikes <= 0:
        return
    spike_idx = np.random.choice(candidates, size=n_spikes, replace=False)
    locs = co[spike_idx].copy()
    locs_m = locs.copy()
    locs_m[:, 1] = -locs_m[:, 1]
    all_locs = np.concatenate([locs, locs_m], axis=0)

    dists = np.linalg.norm(
        co[np.newaxis, :, :] - all_locs[:, np.newaxis, :], axis=-1
    )
    min_dist = np.min(dists, axis=0)
    extrude = spike_height * np.clip(1 - min_dist / 0.02, 0, None)

    sc = params['spike_center']
    xl = params['x_length']
    sd = params['spike_depth']
    d = np.column_stack([x + sc * xl, y, z + sd])
    d_norm = np.linalg.norm(d, axis=-1, keepdims=True)
    d_norm[d_norm == 0] = 1
    d /= d_norm
    co += d * extrude[:, np.newaxis]
    write_co(obj, co)


def build_body(params):
    upper = make_body_surface(params)
    lower = deep_clone(upper)
    make_surface_side(upper, params, 'upper')
    make_surface_side(lower, params, 'lower')
    add_spikes(upper, params)

    obj = join_objs([upper, lower])
    add_modifier(obj, "WELD", merge_threshold=0.001)

    # Height bend along x-axis
    x_length = params['x_length']
    x_tip = params['x_tip']
    bend_height = params['bend_height']
    hs = interp1d(
        [0, -x_tip + 0.01, -x_tip - 0.01, -1],
        [0, bend_height, bend_height, 0],
        'quadratic', fill_value='extrapolate',
    )
    displace_vertices(obj, lambda x, y, z: (0, 0, hs(x / x_length)))

    # Build skeleton (2-point bent line)
    bend_angle = params['bend_angle']
    mesh = bpy.data.meshes.new('skel')
    mesh.from_pydata([(-x_length, 0, 0), (0, 0, 0)], [(0, 1)], [])
    mesh.update()
    line = bpy.data.objects.new('skel', mesh)
    bpy.context.scene.collection.objects.link(line)

    select_only(line)
    line.rotation_euler[1] = np.pi / 2
    apply_tf(line)
    add_modifier(line, "SIMPLE_DEFORM", deform_method='BEND',
                 angle=-bend_angle, deform_axis='Y')
    line.rotation_euler[1] = -np.pi / 2
    apply_tf(line)
    skeleton = read_co(line)
    bpy.data.objects.remove(line, do_unlink=True)

    # Apply BEND deform to body
    select_only(obj)
    obj.rotation_euler[1] = np.pi / 2
    apply_tf(obj)
    add_modifier(obj, "SIMPLE_DEFORM", deform_method='BEND',
                 angle=-bend_angle, deform_axis='Y')
    obj.rotation_euler[1] = -np.pi / 2
    apply_tf(obj)

    print(f"  Body: {len(obj.data.vertices)} verts")
    return obj, skeleton


# ═══════════════════════════════════════════════════════════════════
# LEG CONSTRUCTION
# ═══════════════════════════════════════════════════════════════════

def sample_leg_params():
    x_length = np.random.uniform(0.8, 1.2)
    y_length = np.random.uniform(0.025, 0.035)
    z_length = y_length * np.random.uniform(1.0, 1.5)
    x_mid_first = np.random.uniform(0.3, 0.4)
    x_mid_second = np.random.uniform(0.6, 0.7)
    y_mid_first = np.random.uniform(0.7, 1.0)
    y_mid_second = y_mid_first / 2 * np.random.uniform(1.1, 1.3)
    y_expand = np.random.uniform(1.1, 1.3)
    noise_strength = np.random.uniform(0.005, 0.01)
    noise_scale = log_uniform(5, 10)
    bottom_shift = np.random.uniform(0.3, 0.5)
    bottom_cutoff = np.random.uniform(0.2, 0.5)
    top_shift = np.random.uniform(0.2, 0.4)
    top_cutoff = np.random.uniform(0.6, 0.8)
    return dict(
        x_length=x_length, y_length=y_length, z_length=z_length,
        x_mid_first=x_mid_first, x_mid_second=x_mid_second,
        y_mid_first=y_mid_first, y_mid_second=y_mid_second,
        y_expand=y_expand, noise_strength=noise_strength,
        noise_scale=noise_scale, bottom_shift=bottom_shift,
        bottom_cutoff=bottom_cutoff, top_shift=top_shift,
        top_cutoff=top_cutoff,
    )


def build_segment(x_start, x_end, y_start, y_end, params):
    """Build one tapered tube segment via surface-of-revolution."""

    xl = params['x_length']
    yl = params['y_length']
    ye = params['y_expand']

    xs = np.array([x_start, x_start + 0.01, (x_start + x_end) / 2, x_end - 0.01, x_end])
    ys = np.array([y_start * 0.9, y_start, (y_start + y_end) / 2 * ye, y_end, y_end * 0.9])

    obj = spin_mesh(
        [np.array([xs[0], *xs, xs[-1]]) * xl,
         np.array([0, *ys, 0]) * yl, 0.0],
        [1, len(xs)], axis=(1, 0, 0),
    )

    # Bottom cutoff
    y_base = yl * y_start
    bc, bs = params['bottom_cutoff'], params['bottom_shift']
    displace_vertices(obj, lambda x, y, z: (
        0, 0, -np.clip(z + y_base * bc, None, 0) * (1 - bs)
    ))

    # Top shift
    tc, ts = params['top_cutoff'], params['top_shift']
    displace_vertices(obj, lambda x, y, z: (
        0, 0, np.where(z > 0,
                       np.clip(tc * y_base - np.abs(y), 0, None) * ts, 0)
    ))

    # Noise decoration
    co = read_co(obj)
    sym = np.column_stack([co[:, 0], np.abs(co[:, 1]), co[:, 2]])
    noise = pseudo_noise(sym, params['noise_scale'])
    normals = co.copy()
    normals[:, 0] = 0
    nl = np.linalg.norm(normals, axis=-1, keepdims=True)
    nl[nl == 0] = 1
    normals /= nl
    co += normals * (noise * params['noise_strength'])[:, np.newaxis]
    write_co(obj, co)

    obj.scale[2] = params['z_length'] / yl
    apply_tf(obj)
    return obj


def smooth_curl(obj, total_curl, base_angle=0.0):
    """Smoothly curve a part along a single circular arc in the XZ plane.

    Used for claws and other parts with gentle monotonic curvature.
    """

    co = read_co(obj)
    if len(co) == 0:
        return
    x_max = co[:, 0].max()
    if x_max < 1e-6:
        return

    t = np.clip(co[:, 0] / x_max, 0.0, 1.0)
    y_cs = co[:, 1].copy()
    z_cs = co[:, 2].copy()

    L = x_max
    abs_curl = abs(total_curl)

    if abs_curl < 0.01:
        cb, sb = np.cos(base_angle), np.sin(base_angle)
        co[:, 0] = t * L * cb - z_cs * sb
        co[:, 1] = y_cs
        co[:, 2] = t * L * sb + z_cs * cb
    else:
        R = L / abs_curl
        cx = R * np.sin(base_angle)
        cz = -R * np.cos(base_angle)
        phi = abs_curl * t
        co[:, 0] = cx + (R + z_cs) * np.sin(phi - base_angle)
        co[:, 1] = y_cs
        co[:, 2] = cz + (R + z_cs) * np.cos(phi - base_angle)

    write_co(obj, co)


def leg_arch(obj, leg_rot_x, leg_curl_x_mid=-np.pi * 1.1):
    """Bend leg mesh to match the original 3-bone armature pose.

    Original system (bend_bones_lerp in driver_repeated.py):
      - 3 bones with random ratios r0,r1,r2 (~1/3 each), summing to 1
      - Bone 0: X rotation = (leg_curl_x_mid + leg_rot_x) * r0
      - Bone 1: X rotation = leg_curl_x_mid * r1  (strong downward)
      - Bone 2: X rotation = leg_curl_x_mid * r2  (strong downward)

    We model this as piecewise-linear cumulative angle at bone boundaries,
    then numerically integrate to get the smooth centerline.

    leg_rot_x: first bone upward tilt (from crab_params, ~pi*0.8 to pi*1.1)
    leg_curl_x_mid: effective leg_curl X at the rendered frame. Default -pi*1.1
        because the animation driver evaluates to the maximum curl at frame 1
        (confirmed by inspecting original bone rotations).
    """

    co = read_co(obj)
    if len(co) == 0:
        return
    x_max = co[:, 0].max()
    if x_max < 1e-6:
        return

    t = np.clip(co[:, 0] / x_max, 0.0, 1.0)
    y_cs = co[:, 1].copy()
    z_cs = co[:, 2].copy()
    L = x_max

    # 3-bone rotations (equal ratios ≈ 1/3 each)
    r = 1.0 / 3.0
    bone_rots = [
        (leg_curl_x_mid + leg_rot_x) * r,  # bone 0: curl + rot (slight up)
        leg_curl_x_mid * r,                  # bone 1: curl only (strong down)
        leg_curl_x_mid * r,                  # bone 2: curl only (strong down)
    ]

    # Cumulative angle at bone boundaries [0, 1/3, 2/3, 1]
    cum = [0.0]
    for br in bone_rots:
        cum.append(cum[-1] + br)
    t_bounds = [0.0, 1.0 / 3, 2.0 / 3, 1.0]

    # Interpolate cumulative angle for each vertex
    angle_at_t = np.interp(t, t_bounds, cum)

    # Compute centerline by numerical integration on a fine grid
    n_grid = 500
    t_grid = np.linspace(0, 1, n_grid)
    angle_grid = np.interp(t_grid, t_bounds, cum)
    ds = L / (n_grid - 1)

    cos_a = np.cos(angle_grid)
    sin_a = np.sin(angle_grid)
    x_grid = np.cumsum(np.concatenate([[0], 0.5 * (cos_a[:-1] + cos_a[1:]) * ds]))
    z_grid = np.cumsum(np.concatenate([[0], 0.5 * (sin_a[:-1] + sin_a[1:]) * ds]))

    x_center = np.interp(t, t_grid, x_grid)
    z_center = np.interp(t, t_grid, z_grid)

    # Apply cross-section offset perpendicular to local tangent
    co[:, 0] = x_center - z_cs * np.sin(angle_at_t)
    co[:, 1] = y_cs
    co[:, 2] = z_center + z_cs * np.cos(angle_at_t)

    write_co(obj, co)


def build_leg(params, leg_rot_x):
    x_cuts = [0, params['x_mid_first'], params['x_mid_second'], 1]
    y_cuts = [1, params['y_mid_first'], params['y_mid_second'], 0.01]
    segs = []
    for i in range(len(x_cuts) - 1):
        segs.append(build_segment(x_cuts[i], x_cuts[i + 1],
                                  y_cuts[i], y_cuts[i + 1], params))
    obj = join_objs(segs)
    add_modifier(obj, "WELD", merge_threshold=0.001)
    # Replicate original armature bone bending (leg_rot + leg_curl)
    leg_arch(obj, leg_rot_x)
    return obj


# ═══════════════════════════════════════════════════════════════════
# CLAW CONSTRUCTION
# ═══════════════════════════════════════════════════════════════════

def sample_claw_params():
    base = sample_leg_params()
    z_length = base['y_length'] * np.random.uniform(1, 1.2)
    x_mid_first = np.random.uniform(0.2, 0.25)
    x_mid_second = np.random.uniform(0.4, 0.6)
    y_mid_first = np.random.uniform(1.5, 2.0)
    y_mid_second = y_mid_first * log_uniform(1.0, 1.5)
    y_expand = np.random.uniform(1.4, 1.5)
    noise_strength = np.random.uniform(0.01, 0.02)
    top_shift = np.random.uniform(0.6, 0.8)
    claw_y_first = np.random.uniform(0.6, 1.5)
    claw_y_second = claw_y_first * np.random.uniform(0.4, 0.6)
    claw_x_depth = (1 - x_mid_second) * np.random.uniform(0.3, 0.5)
    claw_x_turn = np.random.uniform(0.2, 0.4)
    claw_z_width = np.random.uniform(0.2, 0.3)
    claw_spike_strength = np.random.uniform(0.02, 0.03)
    _claw_spike_distance = np.random.uniform(0.03, 0.06)  # sync with original
    lower_z_scale = np.random.uniform(0.4, 0.6)
    lower_scale = np.random.uniform(0.75, 0.9)
    lower_z_offset = np.random.uniform(-0.5, 0.5)
    base.update(dict(
        z_length=z_length, x_mid_first=x_mid_first, x_mid_second=x_mid_second,
        y_mid_first=y_mid_first, y_mid_second=y_mid_second,
        y_expand=y_expand, noise_strength=noise_strength, top_shift=top_shift,
        claw_y_first=claw_y_first, claw_y_second=claw_y_second,
        claw_x_depth=claw_x_depth, claw_x_turn=claw_x_turn,
        claw_z_width=claw_z_width, claw_spike_strength=claw_spike_strength,
        lower_z_scale=lower_z_scale, lower_scale=lower_scale,
        lower_z_offset=lower_z_offset,
    ))
    return base


def build_claw(params):
    xl = params['x_length']
    yl = params['y_length']
    zl = params['z_length']
    x_mid = params['x_mid_second']
    y_mid = params['y_mid_second']

    # 2 base segments
    x_cuts = [0, params['x_mid_first'], x_mid, 1]
    y_cuts = [1, params['y_mid_first'], y_mid, 0.01]
    base_segs = []
    for i in range(2):
        base_segs.append(build_segment(
            x_cuts[i], x_cuts[i + 1], y_cuts[i], y_cuts[i + 1], params))

    # Claw (3rd segment = pincer)
    xs = np.array([x_mid, (x_mid + 1) / 2, (x_mid + 3) / 4, 1])
    ys = np.array([y_mid, y_mid * params['claw_y_first'],
                   y_mid * params['claw_y_second'], 0.01])
    claw = spin_mesh(
        [np.array([xs[0], *xs, xs[-1]]) * xl,
         np.array([0, *ys, 0]) * yl, 0.0],
        [1, len(xs)], axis=(1, 0, 0),
    )

    # Bottom depth cut
    bc = params['bottom_cutoff']
    cxd = params['claw_x_depth']
    displace_vertices(claw, lambda x, y, z: (
        0, 0,
        -np.clip(
            z + yl * bc + yl * (y_mid - bc) * (x / xl - x_mid) / cxd,
            None, 0
        ) * (1 - params['bottom_shift'])
    ))

    # Width expansion
    cxt = params['claw_x_turn']
    czw = params['claw_z_width']
    wfn = interp1d(
        [x_mid, x_mid + cxd, x_mid + cxd + cxt * (1 - x_mid - cxd), 1],
        [0, 0, czw, 0], 'cubic', fill_value='extrapolate',
    )
    displace_vertices(claw, lambda x, y, z: (
        0, 0,
        np.where(x > (x_mid + cxd) * xl, wfn(x / xl) * y_mid * yl, 0)
    ))

    # Top shift
    tc, ts = params['top_cutoff'], params['top_shift']
    displace_vertices(claw, lambda x, y, z: (
        0, 0,
        np.where(z > 0, np.clip(tc * yl - np.abs(y), 0, None) * ts, 0)
    ))

    # Inner spikes approximation
    co = read_co(claw)
    x, y, z = co.T
    inner = ((z < 0) & (x > (x_mid + cxd * 1.5) * xl) &
             (x < xl * 0.98) & (np.abs(y) < yl * 0.5))
    if np.any(inner):
        n_sp = min(20, int(np.sum(inner)))
        if n_sp > 0:
            sp_idx = np.random.choice(np.where(inner)[0], size=n_sp, replace=False)
            sp_locs = co[sp_idx]
            d2 = np.linalg.norm(
                co[np.newaxis] - sp_locs[:, np.newaxis], axis=-1)
            min_d = np.min(d2, axis=0)
            extr = params['claw_spike_strength'] * np.clip(1 - min_d / 0.01, 0, None)
            co[:, 2] -= extr
            write_co(claw, co)

    # Noise
    co = read_co(claw)
    sym = np.column_stack([co[:, 0], np.abs(co[:, 1]), co[:, 2]])
    noise = pseudo_noise(sym, params['noise_scale'])
    normals = co.copy()
    normals[:, 0] = 0
    nl = np.linalg.norm(normals, axis=-1, keepdims=True)
    nl[nl == 0] = 1
    normals /= nl
    co += normals * (noise * params['noise_strength'])[:, np.newaxis]
    write_co(claw, co)

    claw.scale[2] = zl / yl
    apply_tf(claw)

    # Lower jaw
    lower = deep_clone(claw)
    co_l = read_co(lower)
    remove_verts_by_mask(lower, co_l[:, 0] < (x_mid + cxd) * xl)

    lower.location[0] = -(x_mid + cxd) * xl
    apply_tf(lower, loc=True, rot=False, scale=False)

    ls = params['lower_scale']
    lzs = params['lower_z_scale']
    lower.scale = (ls, ls, -ls * lzs)
    lower.rotation_euler[1] = np.random.uniform(np.pi / 12, np.pi / 4)
    apply_tf(lower)

    lower.location[0] = (x_mid + cxd) * xl
    lower.location[2] = params['lower_z_offset'] * zl
    apply_tf(lower, loc=True, rot=False, scale=False)
    add_modifier(lower, "WELD", merge_threshold=0.001)

    obj = join_objs(base_segs + [claw, lower])
    add_modifier(obj, "WELD", merge_threshold=0.001)
    # Slight smooth curl for claws (claw_curl much smaller than legs)
    smooth_curl(obj, total_curl=-0.3, base_angle=0.1)
    return obj


# ═══════════════════════════════════════════════════════════════════
# EYE CONSTRUCTION
# ═══════════════════════════════════════════════════════════════════

def sample_eye_params():
    radius = np.random.uniform(0.015, 0.02)
    length = radius * np.random.uniform(1, 1.5)
    return dict(radius=radius, length=length)


def build_eye(params):
    radius = params['radius']
    length = params['length']

    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=radius)
    sphere = bpy.context.active_object

    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.01, depth=length, location=(-length / 2, 0, 0))
    cylinder = bpy.context.active_object
    cylinder.rotation_euler[1] = np.pi / 2
    apply_tf(cylinder)

    obj = join_objs([sphere, cylinder])
    add_modifier(obj, "REMESH", mode='VOXEL', voxel_size=0.005)

    # Origin to leftmost
    co = read_co(obj)
    co[:, 0] -= co[:, 0].min()
    write_co(obj, co)
    return obj


# ═══════════════════════════════════════════════════════════════════
# ATTACHMENT SYSTEM
# ═══════════════════════════════════════════════════════════════════

def euler_quat(x_deg, y_deg, z_deg):
    return MEuler(np.deg2rad([x_deg, y_deg, z_deg]).tolist()).to_quaternion()


def quat_align_vecs(a, b):
    a = Vector(a).normalized()
    b = Vector(b).normalized()
    dot = a.dot(b)
    if dot > 0.9999:
        return Quaternion()
    if dot < -0.9999:
        perp = Vector((1, 0, 0)).cross(a)
        if perp.length < 0.01:
            perp = Vector((0, 1, 0)).cross(a)
        return Quaternion(perp.normalized(), np.pi)
    return Quaternion(a.cross(b).normalized(), a.angle(b))


def raycast_attach(skeleton, body_obj, u, v, rad):
    n = len(skeleton)
    idx = u * (n - 1)
    i = min(int(idx), max(n - 2, 0))
    t = idx - i
    j = min(i + 1, n - 1)
    origin = (1 - t) * skeleton[i] + t * skeleton[j]

    tangent = skeleton[j] - skeleton[i] if n > 1 else np.array([1, 0, 0])
    tn = np.linalg.norm(tangent)
    tangent = tangent / tn if tn > 1e-10 else np.array([1, 0, 0])

    basis = quat_align_vecs(Vector((1, 0, 0)), Vector(tangent))
    dir_rot = euler_quat(180 * v, 0, 0) @ euler_quat(0, 90, 0)
    direction = basis @ dir_rot @ Vector((1, 0, 0))

    depsgraph = bpy.context.evaluated_depsgraph_get()
    bvh = BVHTree.FromObject(body_obj, depsgraph)
    loc, normal, index, dist = bvh.ray_cast(Vector(origin), direction)

    if loc is None:
        loc = Vector(origin)
    else:
        loc = Vector(origin).lerp(loc, rad)

    loc = body_obj.matrix_world @ loc
    return np.array(loc), normal, tangent


def place_part(part_obj, body_obj, skeleton, u, v, rad, joint_deg, side):
    loc, normal, tangent = raycast_attach(skeleton, body_obj, u, v, rad)
    rot = euler_quat(*joint_deg)
    rot_mat = np.array(rot.to_matrix())

    co = read_co(part_obj)
    co = co @ rot_mat.T + loc
    if side == -1:
        co[:, 1] = -co[:, 1]
    write_co(part_obj, co)

    if side == -1:
        select_only(part_obj)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.flip_normals()
        bpy.ops.object.mode_set(mode='OBJECT')


# ═══════════════════════════════════════════════════════════════════
# ASSEMBLY
# ═══════════════════════════════════════════════════════════════════

def build_crab():

    # ══════════════════════════════════════════════════════════════
    # PHASE 1: SAMPLE ALL PARAMETERS (no geometry construction)
    # Matches original flow: crab_params() → crustacean_genome()
    # where ALL factory params are sampled before any make_part()
    # ══════════════════════════════════════════════════════════════

    n_legs = 4
    n_limbs = 5

    # -- crab_params() random calls --
    _base_leg_curl = np.random.uniform(-np.pi * 0.15, np.pi * 0.15)
    x_start = np.random.uniform(0.08, 0.1)
    x_end = np.random.uniform(0.55, 0.6)
    x_legs = (np.linspace(x_start, x_end, n_limbs)
              + np.arange(n_limbs) * 0.02)[::-1]

    leg_angle = np.random.uniform(0.42, 0.44)
    ljx = np.sort(np.random.uniform(-5, 5, n_legs))
    if np.random.uniform(0, 1) > 0.5:
        pass
    else:
        ljx = ljx[::-1]
    ljy = np.sort(np.random.uniform(0, 10, n_legs))
    ljz = (np.sort(np.random.uniform(65, 105, n_legs)
                   + np.random.uniform(-8, 8))
           + np.arange(n_legs) * 2)

    x_claw_off = np.random.uniform(0.08, 0.1)
    claw_angle = np.random.uniform(0.44, 0.46)
    claw_joint = (np.random.uniform(-50, -40),
                  np.random.uniform(-20, 20),
                  np.random.uniform(10, 20))

    x_eye = np.random.uniform(0.92, 0.96)
    eye_angle = np.random.uniform(0.8, 0.85)
    eye_joint = (0, np.random.uniform(-60, 0), np.random.uniform(10, 70))

    leg_rot_x = np.random.uniform(np.pi * 0.8, np.pi * 1.1)
    if np.random.uniform(0, 1) < 0.6:
        _ = np.random.uniform(0, 0.05)
    else:
        _ = np.random.uniform(0.4, 0.45)
    _ = log_uniform(100, 200)

    # -- body_fac = CrabBodyFactory() → sample_params() --
    body_params = sample_body_params()

    # -- crustacean_genome: leg_x_length lambda evaluated --
    leg_x_length = body_params['y_length'] * log_uniform(2.0, 3.0)
    leg_x_lengths = np.sort(np.random.uniform(0.6, 1, 4))[::-1] * leg_x_length
    print(f"  leg_x_length={leg_x_length:.3f}, legs={[f'{v:.3f}' for v in leg_x_lengths]}")

    # -- shared leg factory + 4 individual leg factories (params only) --
    shared_lp = sample_leg_params()
    leg_params_list = []
    for i in range(n_legs):
        lp = sample_leg_params()
        lp['bottom_cutoff'] = shared_lp['bottom_cutoff']
        lp['x_length'] = leg_x_lengths[i]
        leg_params_list.append(lp)

    # -- claw_x_length lambda evaluated (AFTER leg factories) --
    claw_x_length = body_params['y_length'] * log_uniform(1.5, 1.8)
    print(f"  claw_x_length={claw_x_length:.3f}")

    # -- claw factory (params only) --
    cp = sample_claw_params()
    cp['x_length'] = claw_x_length

    # -- eye factory (params only) --
    ep = sample_eye_params()

    print(f"  Ratio claw/leg: {claw_x_length/leg_x_length:.3f}")

    # ══════════════════════════════════════════════════════════════
    # PHASE 2: BUILD ALL GEOMETRY
    # ══════════════════════════════════════════════════════════════

    # Build body
    body_obj, skeleton = build_body(body_params)
    all_parts = [body_obj]

    # Build + place legs
    for i in range(n_legs):
        for side in [1, -1]:
            leg = build_leg(leg_params_list[i], leg_rot_x)
            place_part(leg, body_obj, skeleton,
                       x_legs[i + 1], leg_angle, 0.99,
                       (ljx[i], ljy[i], ljz[i]), side)
            all_parts.append(leg)
        print(f"    Leg pair {i + 1}/4 done")

    # Build + place claws
    claw_r = build_claw(cp)
    claw_l = deep_clone(claw_r)
    place_part(claw_r, body_obj, skeleton,
               x_legs[0] + x_claw_off, claw_angle, 0.99,
               claw_joint, 1)
    place_part(claw_l, body_obj, skeleton,
               x_legs[0] + x_claw_off, claw_angle, 0.99,
               claw_joint, -1)
    all_parts.extend([claw_r, claw_l])

    # Build + place eyes
    for side in [1, -1]:
        eye = build_eye(ep)
        assign_material(eye, EYE_MAT)
        place_part(eye, body_obj, skeleton,
                   x_eye, eye_angle, 0.99, eye_joint, side)
        all_parts.append(eye)

    # Join all
    for part in all_parts:
        if len(part.data.materials) == 0:
            assign_material(part, CREATURE_MAT)
    result = join_objs(all_parts)
    add_modifier(result, "WELD", merge_threshold=0.002)
    select_only(result)
    bpy.ops.object.shade_smooth()
    return result


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

clear_scene()
bpy.context.scene.cursor.location = (0, 0, 0)
crab = build_crab()
if crab is not None and len(crab.data.materials) == 0:
    crab.data.materials.append(CREATURE_MAT)
crab.name = "CrabFactory"
