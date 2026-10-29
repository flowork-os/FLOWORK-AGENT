# [FL_INDEX: keywords="blender_factory, procedural_3d, SpinyLobsterFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: SpinyLobsterFactory | Category: factories_tex
# Prompt: A spiny lobster rendered as a textured 3D model. Unlike a true lobster, this crustacean lacks large front chelae (claws) and instead features two extremely long, stout, upward-curving antennae as its most prominent feature. The segmented abdomen is wide and composed of multiple smooth, rounded orange-red carapace segments. The cephalothorax is short and compact, with several pairs of small walking legs with pointed tips beneath. A small fan-shaped tail is visible at the rear. The smooth exoskeleton is a warm orange-red with slight specular highlights on the convex segment surfaces.

import os

import bpy
import numpy as np
from mathutils import Euler as MEuler, Quaternion, Vector
from mathutils.bvhtree import BVHTree

try:
    from scipy.interpolate import interp1d
except ImportError:
    def interp1d(x, y, kind='linear', fill_value=None, bounds_error=True):
        x, y = np.asarray(x), np.asarray(y)
        def f(xi):
            return np.interp(np.asarray(xi), x, y)
        return f

SEED = int(os.environ.get("SEED", 0))
np.random.seed(SEED)

# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
import random as _random, colorsys as _colorsys


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
    """Crustacean shell: metallic with clearcoat, musgrave-driven color.
    """

    np.random.seed(seed); _random.seed(seed)
    value_shift = _log_uniform(2, 10)
    # base_hue: 60% chance red/orange [0,0.05], 40% chance blue/teal [0.4,0.45]
    if float(np.random.uniform(0, 1)) < 0.6:
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
    spec_tint_v = float(np.random.uniform(0, 1))
    specular_tint = (spec_tint_v, spec_tint_v, spec_tint_v, 1.0)
    clearcoat = float(np.random.uniform(0.2, 0.8))
    roughness = float(np.random.uniform(0.1, 0.3))
    metallic = float(np.random.uniform(0.6, 0.8))
    musg_scale = _log_uniform(5, 8)

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new

    geom = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ln(geom.outputs["Position"], sep.inputs["Vector"])
    abs_y = nt.nodes.new("ShaderNodeMath"); abs_y.operation = "ABSOLUTE"
    ln(sep.outputs["Y"], abs_y.inputs[0])
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    ln(sep.outputs["X"], comb.inputs["X"])
    ln(abs_y.outputs[0], comb.inputs["Y"])
    ln(sep.outputs["Z"], comb.inputs["Z"])

    # Noise as musgrave replacement → map_range [0,1]
    noise = nt.nodes.new("ShaderNodeTexNoise")
    ln(comb.outputs["Vector"], noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = musg_scale
    noise.inputs["Detail"].default_value = 2.0

    # 4-stop color ramp HSV
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.color_mode = "HSV"; cr.color_ramp.hue_interpolation = "NEAR"
    ln(_fac(noise), cr.inputs["Fac"])
    cr.color_ramp.elements.new(0); cr.color_ramp.elements.new(0)
    cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[0].color = bright_color
    cr.color_ramp.elements[1].position = 0.3; cr.color_ramp.elements[1].color = bright_color
    cr.color_ramp.elements[2].position = 0.7; cr.color_ramp.elements[2].color = dark_color
    cr.color_ramp.elements[3].position = 1.0; cr.color_ramp.elements[3].color = dark_color

    # Mix with light_color using a ratio attribute (fallback: 0.3 constant)
    light_rgb = nt.nodes.new("ShaderNodeRGB"); light_rgb.outputs[0].default_value = light_color
    mix_c = nt.nodes.new("ShaderNodeMix"); mix_c.data_type = "RGBA"
    mix_c.inputs[0].default_value = 0.3
    ln(light_rgb.outputs[0], mix_c.inputs[6]); ln(cr.outputs["Color"], mix_c.inputs[7])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(mix_c.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    spec_key = "Specular IOR Level" if "Specular IOR Level" in bsdf.inputs else "Specular"
    bsdf.inputs[spec_key].default_value = specular
    if "Specular Tint" in bsdf.inputs:
        try:
            bsdf.inputs["Specular Tint"].default_value = specular_tint
        except TypeError:
            bsdf.inputs["Specular Tint"].default_value = specular_tint[0]
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
CREATURE_MAT = make_creature_material(SEED, "SpinyLobsterFactory_Material")
EYE_MAT = make_eye_material("SpinyLobsterFactory_EyeMaterial")
np.random.seed(SEED)


def log_uniform(low, high):
    return np.exp(np.random.uniform(np.log(low), np.log(high)))

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITIES  (identical to CrustaceanFactory)
# ═══════════════════════════════════════════════════════════════════════════════

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

def deep_clone(obj):
    new_mesh = obj.data.copy()
    new_obj = obj.copy()
    new_obj.data = new_mesh
    bpy.context.scene.collection.objects.link(new_obj)
    return new_obj

# ═══════════════════════════════════════════════════════════════════════════════
# BEZIER / SPIN / LEAF  (identical to CrustaceanFactory)
# ═══════════════════════════════════════════════════════════════════════════════

def bezier_curve(anchors, vector_locations=(), resolution=None):
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

def spin_mesh(anchors, vector_locations=(), axis=(0, 0, 1)):
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

# ═══════════════════════════════════════════════════════════════════════════════
# NOISE HELPER
# ═══════════════════════════════════════════════════════════════════════════════

def pseudo_noise(positions, scale=1.0):
    p = positions * scale
    return (
        np.sin(p[:, 0] * 1.0 + p[:, 1] * 2.3 + p[:, 2] * 1.7) * 0.30
        + np.sin(p[:, 0] * 3.1 + p[:, 1] * 0.7 + p[:, 2] * 2.9) * 0.30
        + np.sin(p[:, 0] * 5.3 + p[:, 1] * 4.1 + p[:, 2] * 3.3) * 0.20
        + np.sin(p[:, 0] * 7.7 + p[:, 1] * 6.5 + p[:, 2] * 5.1) * 0.10
        + np.sin(p[:, 0] * 11.3 + p[:, 1] * 9.7 + p[:, 2] * 8.3) * 0.10
    )

# ═══════════════════════════════════════════════════════════════════════════════
# BODY  (same as CrustaceanFactory)
# ═══════════════════════════════════════════════════════════════════════════════

def sample_body_params():
    x_length = np.random.uniform(0.6, 0.8)
    y_length = np.random.uniform(0.15, 0.2)
    z_length = y_length * np.random.uniform(1.0, 1.2)
    midpoint_first = np.random.uniform(0.65, 0.75)
    midpoint_second = np.random.uniform(0.95, 1.05)
    z_shift = np.random.uniform(0.4, 0.6)
    z_shift_midpoint = np.random.uniform(0.2, 0.3)
    bottom_cutoff = np.random.uniform(0.2, 0.3)
    bottom_shift = np.random.uniform(0.3, 0.5)
    noise_scale = np.random.uniform(5, 8)
    noise_strength = np.random.uniform(0.02, 0.04)
    return dict(
        x_length=x_length, y_length=y_length, z_length=z_length,
        midpoint_first=midpoint_first, midpoint_second=midpoint_second,
        z_shift=z_shift, z_shift_midpoint=z_shift_midpoint,
        bottom_cutoff=bottom_cutoff, bottom_shift=bottom_shift,
        noise_scale=noise_scale, noise_strength=noise_strength,
    )

def build_body(params):
    xl = params['x_length']
    yl = params['y_length']
    mp1 = params['midpoint_first']
    mp2 = params['midpoint_second']

    x_anch = np.array([0, 0, 1/3, 2/3, 1, 1]) * xl
    y_anch = np.array([0, 1, mp2, mp1, 0.01, 0]) * yl
    obj = spin_mesh([x_anch, y_anch, 0.0], [1, 4], axis=(1, 0, 0))

    z_s = params['z_shift']
    z_sm = params['z_shift_midpoint']
    h_fn = interp1d([0, 0.5, 1], [0, z_sm / 2, z_s], kind='quadratic')
    co = read_co(obj)
    x_norm = np.clip(co[:, 0] / xl, 0, 1)
    co[:, 2] += h_fn(x_norm) * yl
    write_co(obj, co)

    bc = params['bottom_cutoff']
    bs = params['bottom_shift']
    displace_vertices(obj, lambda x, y, z: (
        0, 0, -np.clip(z + yl * bc, None, 0) * (1 - bs)
    ))

    obj.scale[2] = params['z_length'] / yl
    apply_tf(obj)

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

    co = read_co(obj)
    head_z = co[co[:, 0].argmax(), 2]
    skeleton = np.zeros((4, 3))
    skeleton[:, 0] = np.linspace(0, xl, 4)
    skeleton[:, 2] = np.linspace(0, head_z, 4)

    return obj, skeleton

# ═══════════════════════════════════════════════════════════════════════════════
# TAIL  (same as CrustaceanFactory)
# ═══════════════════════════════════════════════════════════════════════════════

def sample_tail_params(body_params):
    x_length = body_params['x_length'] * log_uniform(1.2, 1.8)
    y_length = body_params['y_length']
    z_length = y_length * np.random.uniform(1.0, 1.2)
    n_segments = np.random.randint(6, 10)
    x_decay = np.random.uniform(0.2, 0.3)
    shell_ratio = np.random.uniform(1.10, 1.15)
    y_midpoint_first = np.random.uniform(0.5, 0.65)
    y_midpoint_second = np.random.uniform(0.35, 0.50)
    bottom_cutoff = np.random.uniform(0.2, 0.3)
    bottom_shift = np.random.uniform(0.3, 0.5)
    top_shift = np.random.uniform(0.2, 0.4)
    top_cutoff = np.random.uniform(0.6, 0.8)
    noise_scale = log_uniform(5, 10)
    noise_strength = np.random.uniform(0.005, 0.01)
    return dict(
        x_length=x_length, y_length=y_length, z_length=z_length,
        n_segments=n_segments, x_decay=x_decay, shell_ratio=shell_ratio,
        y_midpoint_first=y_midpoint_first, y_midpoint_second=y_midpoint_second,
        bottom_cutoff=bottom_cutoff, bottom_shift=bottom_shift,
        top_shift=top_shift, top_cutoff=top_cutoff,
        noise_scale=noise_scale, noise_strength=noise_strength,
    )

def build_tail_segment(x0, x1, y0, y1, params):
    xl = params['x_length']
    yl = params['y_length']
    sr = params['shell_ratio']

    x_anch = np.array([x0, (x0 + x1) / 2, x1]) * xl
    y_anch = np.array([y0, np.sqrt(max(y0 * y1, 0.001)), y1 * sr]) * yl
    xa = np.array([x_anch[0], *x_anch, x_anch[-1]])
    ya = np.array([0, *y_anch, 0])
    seg = spin_mesh([xa, ya, 0.0], [1, 3], axis=(1, 0, 0))

    y_base = max(y0, y1) * yl
    bc = params['bottom_cutoff']
    bs = params['bottom_shift']
    displace_vertices(seg, lambda x, y, z: (
        0, 0, -np.clip(z + y_base * bc, None, 0) * (1 - bs)
    ))

    tc = params['top_cutoff']
    ts = params['top_shift']
    displace_vertices(seg, lambda x, y, z: (
        0, 0, np.where(z > 0,
                       np.clip(tc * y_base - np.abs(y), 0, None) * ts, 0)
    ))

    co = read_co(seg)
    if len(co) > 0:
        sym = np.column_stack([co[:, 0], np.abs(co[:, 1]), co[:, 2]])
        noise = pseudo_noise(sym, params['noise_scale'])
        normals = co.copy()
        normals[:, 0] = 0
        nl = np.linalg.norm(normals, axis=-1, keepdims=True)
        nl[nl == 0] = 1
        normals /= nl
        co += normals * (noise * params['noise_strength'])[:, np.newaxis]
        write_co(seg, co)

    seg.scale[2] = params['z_length'] / yl
    apply_tf(seg)
    return seg

def build_tail(params):
    xl = params['x_length']
    n_seg = params['n_segments']
    x_decay = params['x_decay']

    decay_per = np.exp(np.log(x_decay) / n_seg)
    widths = np.array([decay_per ** i for i in range(n_seg)])
    x_cuts = np.concatenate([[0], np.cumsum(widths)])
    x_cuts /= x_cuts[-1]

    y_interp = interp1d(
        [0, 0.33, 0.67, 1],
        [1.0 / params['shell_ratio'], params['y_midpoint_first'],
         params['y_midpoint_second'], 0.1],
        kind='linear'
    )
    y_cuts = y_interp(x_cuts)

    segments = []
    for i in range(n_seg):
        seg = build_tail_segment(
            x_cuts[i], x_cuts[i + 1],
            y_cuts[i], y_cuts[i + 1], params)
        segments.append(seg)

    obj = join_objs(segments)
    add_modifier(obj, "WELD", merge_threshold=0.001)

    skeleton = np.array([[0, 0, 0], [xl, 0, 0]], dtype=float)
    return obj, skeleton

# ═══════════════════════════════════════════════════════════════════════════════
# LEG SEGMENT BUILDER  (same as CrustaceanFactory)
# ═══════════════════════════════════════════════════════════════════════════════

def sample_leg_params():
    x_length = np.random.uniform(0.8, 1.2)
    y_length = np.random.uniform(0.01, 0.015)
    z_length = y_length * np.random.uniform(1.0, 1.2)
    x_mid_first = np.random.uniform(0.3, 0.4)
    x_mid_second = np.random.uniform(0.6, 0.7)
    y_mid_first = np.random.uniform(0.7, 1.0)
    y_mid_second = y_mid_first / 2 * np.random.uniform(1.1, 1.3)
    y_expand = np.random.uniform(1.1, 1.3)
    noise_strength = np.random.uniform(0.003, 0.006)
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
    xl = params['x_length']
    yl = params['y_length']
    ye = params['y_expand']

    xs = np.array([x_start, x_start + 0.01,
                   (x_start + x_end) / 2,
                   x_end - 0.01, x_end])
    ys = np.array([y_start * 0.9, y_start,
                   (y_start + y_end) / 2 * ye,
                   y_end, y_end * 0.9])

    obj = spin_mesh(
        [np.array([xs[0], *xs, xs[-1]]) * xl,
         np.array([0, *ys, 0]) * yl, 0.0],
        [1, len(xs)], axis=(1, 0, 0),
    )

    y_base = yl * y_start
    bc, bs = params['bottom_cutoff'], params['bottom_shift']
    displace_vertices(obj, lambda x, y, z: (
        0, 0, -np.clip(z + y_base * bc, None, 0) * (1 - bs)
    ))

    tc, ts = params['top_cutoff'], params['top_shift']
    displace_vertices(obj, lambda x, y, z: (
        0, 0, np.where(z > 0,
                       np.clip(tc * y_base - np.abs(y), 0, None) * ts, 0)
    ))

    co = read_co(obj)
    if len(co) > 0:
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

def leg_bend(obj, bend_angle):
    co = read_co(obj)
    if len(co) == 0:
        return
    x_max = co[:, 0].max()
    if x_max < 1e-6:
        return

    t = np.clip(co[:, 0] / x_max, 0, 1)
    y_cs = co[:, 1].copy()
    z_cs = co[:, 2].copy()
    L = x_max

    n_grid = 200
    t_grid = np.linspace(0, 1, n_grid)
    a_grid = bend_angle * t_grid
    ds = L / (n_grid - 1)

    x_grid = np.cumsum(np.concatenate(
        [[0], 0.5 * (np.cos(a_grid[:-1]) + np.cos(a_grid[1:])) * ds]))
    z_grid = np.cumsum(np.concatenate(
        [[0], 0.5 * (np.sin(a_grid[:-1]) + np.sin(a_grid[1:])) * ds]))

    x_center = np.interp(t, t_grid, x_grid)
    z_center = np.interp(t, t_grid, z_grid)

    angle_at_t = bend_angle * t
    co[:, 0] = x_center - z_cs * np.sin(angle_at_t)
    co[:, 1] = y_cs
    co[:, 2] = z_center + z_cs * np.cos(angle_at_t)
    write_co(obj, co)

def build_leg(params, bend_angle=-np.pi * 0.35):
    x_cuts = [0, params['x_mid_first'], params['x_mid_second'], 1]
    y_cuts = [1, params['y_mid_first'], params['y_mid_second'], 0.01]
    segs = []
    for i in range(len(x_cuts) - 1):
        segs.append(build_segment(
            x_cuts[i], x_cuts[i + 1],
            y_cuts[i], y_cuts[i + 1], params))
    obj = join_objs(segs)
    add_modifier(obj, "WELD", merge_threshold=0.001)
    leg_bend(obj, bend_angle)
    return obj

# ═══════════════════════════════════════════════════════════════════════════════
# SPINY LOBSTER ANTENNA  (SpinyLobsterAntennaFactory)
# KEY DIFFERENCE: y_length = 0.05-0.08 (3-5x thicker than regular lobster)
# ═══════════════════════════════════════════════════════════════════════════════

def sample_antenna_params(body_params):
    x_length = body_params['x_length'] * log_uniform(1.6, 3.0)
    # SpinyLobsterAntennaFactory: y_length=0.05-0.08 (much thicker)
    y_length = np.random.uniform(0.05, 0.08)
    z_length = y_length * log_uniform(1.0, 1.2)
    x_mid_first = np.random.uniform(0.1, 0.15)
    x_mid_second = np.random.uniform(0.25, 0.3)
    y_mid_first = np.random.uniform(0.7, 1.0)
    y_mid_second = y_mid_first / 2 * np.random.uniform(1.1, 1.3)
    y_expand = np.random.uniform(1.1, 1.3)
    noise_strength = np.random.uniform(0.002, 0.004)
    noise_scale = log_uniform(5, 10)
    bottom_shift = np.random.uniform(0.3, 0.5)
    bottom_cutoff = np.random.uniform(0.2, 0.5)
    top_shift = np.random.uniform(0.2, 0.4)
    top_cutoff = np.random.uniform(0.6, 0.8)
    antenna_bend = np.random.uniform(2, 5)
    return dict(
        x_length=x_length, y_length=y_length, z_length=z_length,
        x_mid_first=x_mid_first, x_mid_second=x_mid_second,
        y_mid_first=y_mid_first, y_mid_second=y_mid_second,
        y_expand=y_expand, noise_strength=noise_strength,
        noise_scale=noise_scale, bottom_shift=bottom_shift,
        bottom_cutoff=bottom_cutoff, top_shift=top_shift,
        top_cutoff=top_cutoff, antenna_bend=antenna_bend,
    )

def build_antenna(params):
    """Build spiny lobster antenna: thick 3-segment tapered tube with bend."""

    x_cuts = [0, params['x_mid_first'], params['x_mid_second'], 1]
    y_cuts = [1, params['y_mid_first'], params['y_mid_second'], 0.01]

    segs = []
    for i in range(len(x_cuts) - 1):
        seg = build_segment(x_cuts[i], x_cuts[i + 1],
                            y_cuts[i], y_cuts[i + 1], params)
        segs.append(seg)

    obj = join_objs(segs)
    add_modifier(obj, "WELD", merge_threshold=0.001)

    # Quadratic upward bend on the distal portion
    xl = params['x_length']
    bend = params['antenna_bend']
    x_bend_start = params['x_mid_second']
    co = read_co(obj)
    if len(co) > 0:
        x_norm = co[:, 0] / xl
        mask = x_norm > x_bend_start
        dz = np.where(mask,
                      bend * (x_norm - x_bend_start) ** 2 * params['z_length'],
                      0)
        co[:, 2] += dz
        write_co(obj, co)

    return obj

# ═══════════════════════════════════════════════════════════════════════════════
# EYE  (same as CrustaceanFactory)
# ═══════════════════════════════════════════════════════════════════════════════

def sample_eye_params():
    radius = np.random.uniform(0.015, 0.02)
    length = radius * np.random.uniform(1.0, 1.5)
    return dict(radius=radius, length=length)

def build_eye(params):
    radius = params['radius']
    length = params['length']

    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=radius)
    sphere = bpy.context.active_object

    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.008, depth=length, location=(-length / 2, 0, 0))
    cylinder = bpy.context.active_object
    cylinder.rotation_euler[1] = np.pi / 2
    apply_tf(cylinder)

    obj = join_objs([sphere, cylinder])
    add_modifier(obj, "REMESH", mode='VOXEL', voxel_size=0.005)

    co = read_co(obj)
    co[:, 0] -= co[:, 0].min()
    write_co(obj, co)
    return obj

# ═══════════════════════════════════════════════════════════════════════════════
# ATTACHMENT SYSTEM  (same as CrustaceanFactory)
# ═══════════════════════════════════════════════════════════════════════════════

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

# ═══════════════════════════════════════════════════════════════════════════════
# ASSEMBLY
# ═══════════════════════════════════════════════════════════════════════════════

def build_spiny_lobster():

    n_legs = 4
    n_limbs = 5

    # ── Assembly parameters (same as lobster base) ──
    x_start = np.random.uniform(0.05, 0.08)
    x_end = np.random.uniform(0.2, 0.25)
    x_legs = (np.linspace(x_start, x_end, n_limbs)
              + np.arange(n_limbs) * 0.02)[::-1]

    leg_angle = np.random.uniform(0.3, 0.35)
    ljx = np.sort(np.random.uniform(-5, 5, n_legs))
    ljy = np.sort(np.random.uniform(0, 10, n_legs))
    ljz = (np.sort(np.random.uniform(95, 110, n_legs)
                   + np.random.uniform(-8, 8))
           + np.arange(n_legs) * 2)

    # Front limbs: spiny lobster uses LobsterLegFactory (not claw)
    # claw_joint = (uniform(10,40), uniform(0,10), min(leg_joint_z) + uniform(-10,-5))
    x_claw_off = np.random.uniform(0.08, 0.1)
    claw_angle = leg_angle   # spiny lobster: claw_angle = leg_angle
    leg_joint_z_min = float(np.min(ljz)) + np.random.uniform(-10, -5)
    claw_joint = (
        np.random.uniform(10, 40),
        np.random.uniform(0, 10),
        leg_joint_z_min,
    )

    # Eyes
    x_eye = np.random.uniform(0.8, 0.88)
    eye_angle = np.random.uniform(0.8, 0.85)
    eye_joint = (0, np.random.uniform(-60, 0), np.random.uniform(10, 70))

    # Antenna placement (spiny lobster overrides from lobster base):
    # x_antenna = 0.7-0.75 (slightly forward vs lobster's 0.76-0.8)
    # antenna_angle kept at side-of-body placement
    # Joint Y steepened from original -30 to -40 → -55 to -70 to produce
    # more vertical antennae matching reference images
    x_antenna = np.random.uniform(0.7, 0.75)
    antenna_angle = np.random.uniform(0.4, 0.5)    # side-of-head placement
    # Y = -75 to -85 gives 75-85° elevation (nearly vertical antennae)
    antenna_joint = (
        np.random.uniform(70, 100),
        np.random.uniform(-85, -75),   # 75-85° elevation, nearly vertical
        np.random.uniform(15, 25),     # outward spread
    )

    # ── Part parameters ──
    body_params = sample_body_params()

    leg_x_length = body_params['x_length'] * log_uniform(0.6, 0.8)
    leg_x_lengths = np.sort(
        np.random.uniform(0.6, 1, n_legs))[::-1] * leg_x_length

    shared_lp = sample_leg_params()
    leg_params_list = []
    for i in range(n_legs):
        lp = sample_leg_params()
        lp['bottom_cutoff'] = shared_lp['bottom_cutoff']
        lp['x_length'] = leg_x_lengths[i]
        leg_params_list.append(lp)

    # Front limbs: same as leg (LobsterLegFactory), length = leg_x_length
    front_limb_params = sample_leg_params()
    front_limb_params['x_length'] = leg_x_length  # claw_x_length = leg_x_length

    tail_params = sample_tail_params(body_params)
    antenna_params = sample_antenna_params(body_params)
    eye_params = sample_eye_params()

    # ══════════════════════════════════════════════════════════════════════
    # BUILD ALL GEOMETRY
    # ══════════════════════════════════════════════════════════════════════

    # Body
    body_obj, body_skeleton = build_body(body_params)
    all_parts = [body_obj]

    # Tail (rotate 180° to extend backward)
    tail_obj, _ = build_tail(tail_params)
    tail_rot = euler_quat(0, 0, 180)
    tail_rot_mat = np.array(tail_rot.to_matrix())
    co = read_co(tail_obj)
    co = co @ tail_rot_mat.T
    write_co(tail_obj, co)
    all_parts.append(tail_obj)

    # Legs (4 pairs)
    for i in range(n_legs):
        for side in [1, -1]:
            leg = build_leg(leg_params_list[i])
            place_part(leg, body_obj, body_skeleton,
                       x_legs[i + 1], leg_angle, 0.99,
                       (ljx[i], ljy[i], ljz[i]), side)
            all_parts.append(leg)

    # Front limbs (LobsterLegFactory, not claw — spiny lobster has no chelipeds)
    front_r = build_leg(front_limb_params)
    front_l = deep_clone(front_r)
    place_part(front_r, body_obj, body_skeleton,
               x_legs[0] + x_claw_off, claw_angle, 0.99,
               claw_joint, 1)
    place_part(front_l, body_obj, body_skeleton,
               x_legs[0] + x_claw_off, claw_angle, 0.99,
               claw_joint, -1)
    all_parts.extend([front_r, front_l])

    # Antennae (thick: y_length=0.05-0.08)
    ant_r = build_antenna(antenna_params)
    ant_l = deep_clone(ant_r)
    place_part(ant_r, body_obj, body_skeleton,
               x_antenna, antenna_angle, 0.99,
               antenna_joint, 1)
    place_part(ant_l, body_obj, body_skeleton,
               x_antenna, antenna_angle, 0.99,
               antenna_joint, -1)
    all_parts.extend([ant_r, ant_l])

    # Eyes
    for side in [1, -1]:
        eye = build_eye(eye_params)
        assign_material(eye, EYE_MAT)
        place_part(eye, body_obj, body_skeleton,
                   x_eye, eye_angle, 0.99, eye_joint, side)
        all_parts.append(eye)

    # ── Join body parts and apply SUBSURF ──
    for part in all_parts:
        if len(part.data.materials) == 0:
            assign_material(part, CREATURE_MAT)
    result = join_objs(all_parts)
    add_modifier(result, "WELD", merge_threshold=0.002)
    add_modifier(result, "SUBSURF", levels=1, render_levels=1)

    # Smooth shading
    select_only(result)
    bpy.ops.object.shade_smooth()

    # Ground (z-min = 0)
    co = read_co(result)
    co[:, 2] -= co[:, 2].min()
    write_co(result, co)

    return result

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

clear_scene()
bpy.context.scene.cursor.location = (0, 0, 0)
lobster = build_spiny_lobster()
if lobster is not None and len(lobster.data.materials) == 0:
    lobster.data.materials.append(CREATURE_MAT)
lobster.name = "SpinyLobsterFactory"

script_dir = os.path.dirname(os.path.abspath(bpy.data.filepath or __file__))
blend_path = os.path.join(script_dir, "SpinyLobsterFactory.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
