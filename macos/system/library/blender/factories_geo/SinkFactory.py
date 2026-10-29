# [FL_INDEX: keywords="blender_factory, procedural_3d, SinkFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: SinkFactory | Category: factories_geo
# Prompt: A 3D model of a rectangular kitchen sink basin with a faucet, rendered from a slightly elevated three-quarter perspective. The sink features a deep box-shaped basin with rounded interior edges, a flat rim around the top, and a curved gooseneck faucet mounted on one side with a small handle at its base.

"""SinkFactory — kitchen sink with metal shaders and wear_tear.

Seeding: np.random.seed(SEED) then single RNG stream (no FixedSeed resets).
Materials: sink body + tap each drawn independently from weighted metals pool.
Wear-tear: 50% scratch / 50% edge_wear gates from same stream.
"""


import os
import math
import random
import hashlib
import colorsys

import bpy
import numpy as np

# ── environment / seeding ─────────────────────────────────────────────────────

SEED = int(os.environ.get("SEED", "0"))
np.random.seed(SEED)
U = np.random.uniform


def log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))


def hsv2rgba(hsv):
    h, s, v = hsv
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)


# hex -> hex2rgba (srgb_to_linear) -> rgb2hsv
_NATURAL_BASE_HSV = [
    (0.0,    0.0,    0.5271),  # 0xC0C0C0 silver
    (0.0961, 0.6702, 0.2623),  # 0x8C7853 khaki
    (0.1319, 0.1682, 0.5089),  # 0xBDBAAE light gray
    (0.6296, 0.1518, 0.4678),  # 0xA9ACB6 gray-blue
    (0.0749, 0.1518, 0.4678),  # 0xB6AFA9 gray-beige
]


def metal_natural_hsv():
    idx = np.random.randint(0, len(_NATURAL_BASE_HSV))
    h, s, v = _NATURAL_BASE_HSV[idx]
    return (
        h + float(np.random.uniform(-0.1, 0.1)),
        s + float(np.random.uniform(-0.1, 0.1)),
        v * float(log_uniform(0.2, 0.5)),
    )


def metal_hsv():
    if np.random.uniform() < 0.2:
        return metal_natural_hsv()
    return (np.random.uniform(0, 1),
            np.random.uniform(0.3, 0.6),
            log_uniform(0.02, 0.5))

def weighted_sample(reg):
    classes, w = zip(*reg)
    w = np.array(w, dtype=float)
    return classes[int(np.random.choice(len(classes), p=w / w.sum()))]


# ── scene helpers ─────────────────────────────────────────────────────────────

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for c in list(bpy.data.curves):
        bpy.data.curves.remove(c)
    for ng in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(ng)
    bpy.context.scene.cursor.location = (0, 0, 0)


def select_only(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def apply_tf(obj, loc=False):
    select_only(obj)
    bpy.ops.object.transform_apply(location=loc, rotation=True, scale=True)


def set_fillet_mode(node, mode_str):
    try:
        node.mode = mode_str
        return
    except (AttributeError, TypeError):
        pass
    for inp in node.inputs:
        if inp.bl_idname == "NodeSocketMenu" or inp.name == "Mode":
            try:
                inp.default_value = mode_str
            except TypeError:
                inp.default_value = mode_str.title()
            return


def assign_float_curve(curve_mapping, control_points):
    curve_mapping.use_clip = False
    curve = curve_mapping.curves[0]
    while len(curve.points) > len(control_points):
        curve.points.remove(curve.points[-1])
    while len(curve.points) < len(control_points):
        curve.points.new(0, 0)
    for i, (x, y) in enumerate(control_points):
        curve.points[i].location = (x, y)
    curve_mapping.update()


# ============================================================================
# Material library — all 6 metals + wear_tear
# ============================================================================

def _new_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    return mat


def _set_principled(bsdf, **kw):
    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Coat Weight": ("Coat Weight", "Clearcoat"),
    }
    for k, v in kw.items():
        for name in aliases.get(k, (k,)):
            if name in bsdf.inputs:
                bsdf.inputs[name].default_value = v
                break


def _build_float_curve(nt, value_socket, anchors):
    fc = nt.nodes.new("ShaderNodeFloatCurve")
    fc.mapping.use_clip = False
    curve = fc.mapping.curves[0]
    for i, (x, y) in enumerate(anchors):
        if i < 2:
            curve.points[i].location = (x, y)
        else:
            curve.points.new(x, y)
        curve.points[i].handle_type = "VECTOR"
    fc.mapping.update()
    nt.links.new(value_socket, fc.inputs["Value"])
    return fc


def _noise_fac_output(noise_node):
    if "Fac" in noise_node.outputs:
        return noise_node.outputs["Fac"]
    if "Factor" in noise_node.outputs:
        return noise_node.outputs["Factor"]
    return noise_node.outputs[0]


def _connect_output(nt, bsdf, displacement=None):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    if displacement is not None:
        nt.links.new(displacement, out.inputs["Displacement"])
    return out


def _find_node(nt, bl_idname):
    return next((n for n in nt.nodes if n.bl_idname == bl_idname), None)


def _math(nt, op, in0=None, in1=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
    for idx, val in [(0, in0), (1, in1)]:
        if val is None:
            continue
        if hasattr(val, "links"):
            nt.links.new(val, n.inputs[idx])
        else:
            n.inputs[idx].default_value = val
    return n


def _vmath(nt, op, in0=None, in1=None, scale=None):
    n = nt.nodes.new("ShaderNodeVectorMath")
    n.operation = op
    for idx, val in [(0, in0), (1, in1)]:
        if val is None:
            continue
        if hasattr(val, "links"):
            nt.links.new(val, n.inputs[idx])
        else:
            n.inputs[idx].default_value = val
    if scale is not None:
        for inp in n.inputs:
            if inp.name == "Scale":
                inp.default_value = scale
                break
    return n


def _value_node(nt, value):
    n = nt.nodes.new("ShaderNodeValue")
    n.outputs[0].default_value = value
    return n


def _color_ramp(nt, fac_socket, stops):
    cr = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(fac_socket, cr.inputs.get("Fac") or cr.inputs[0])
    elements = cr.color_ramp.elements
    for i, (pos, color) in enumerate(stops):
        if i < len(elements):
            elements[i].position = pos
            elements[i].color = color
        else:
            e = elements.new(pos)
            e.color = color
    return cr


def _noise_tex(nt, vector_socket, scale, detail=2.0, distortion=0.0, roughness=0.5):
    n = nt.nodes.new("ShaderNodeTexNoise")
    if vector_socket is not None:
        nt.links.new(vector_socket, n.inputs["Vector"])
    if isinstance(scale, (int, float)):
        n.inputs["Scale"].default_value = float(scale)
    else:
        nt.links.new(scale, n.inputs["Scale"])
    if "Detail" in n.inputs:
        n.inputs["Detail"].default_value = detail
    if "Distortion" in n.inputs:
        n.inputs["Distortion"].default_value = distortion
    if "Roughness" in n.inputs:
        n.inputs["Roughness"].default_value = roughness
    return n


# --- Metal shaders -----------------------------------------------------------

def make_metal_basic(name="MetalBasic", color_hsv=None):
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = float(np.random.uniform(10, 25))
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    fc = _build_float_curve(
        nt, _noise_fac_output(noise),
        [(0, float(np.random.uniform(0, 0.2))),
         (1, float(np.random.uniform(0.4, 0.7)))],
    )

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf,
        Metallic=1.0,
        **{"Specular IOR Level": float(np.random.uniform(0.5, 1.0))},
        **{"Base Color": hsv2rgba(color_hsv or metal_hsv())},
    )
    nt.links.new(fc.outputs["Value"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat


def make_brushed_metal(name="BrushedMetal", base_color_hsv=None):
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    mapping_1.inputs["Scale"].default_value = (0.2, 0.2, 5.0)
    nt.links.new(tex_coord.outputs["Object"], mapping_1.inputs["Vector"])
    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise2, "noise_dimensions"):
        try:
            noise2.noise_dimensions = "4D"
        except TypeError:
            pass
    noise2.inputs["Scale"].default_value = 100.0
    if "Detail" in noise2.inputs:
        noise2.inputs["Detail"].default_value = 15.0
    if "Roughness" in noise2.inputs:
        noise2.inputs["Roughness"].default_value = 0.4
    if "Distortion" in noise2.inputs:
        noise2.inputs["Distortion"].default_value = 0.1
    if "W" in noise2.inputs:
        noise2.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(mapping_1.outputs["Vector"], noise2.inputs["Vector"])
    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[1].default_value = 0.4
    map_range.inputs[2].default_value = 0.6
    map_range.inputs[3].default_value = 0.8
    map_range.inputs[4].default_value = 1.2
    nt.links.new(_noise_fac_output(noise2), map_range.inputs[0])
    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_node.inputs["Color"].default_value = hsv2rgba(base_color_hsv)
    nt.links.new(map_range.outputs["Result"], hsv_node.inputs["Value"])
    map_range_r = nt.nodes.new("ShaderNodeMapRange")
    map_range_r.inputs[1].default_value = 0.4
    map_range_r.inputs[2].default_value = 0.6
    map_range_r.inputs[3].default_value = 0.2
    map_range_r.inputs[4].default_value = 0.3
    nt.links.new(_noise_fac_output(noise2), map_range_r.inputs[0])
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Metallic=1.0, **{"Specular IOR Level": 0.0})
    nt.links.new(hsv_node.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(map_range_r.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat


def make_galvanized_metal(name="GalvanizedMetal", base_color_hsv=None, scale=1.0):
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    seed = float(np.random.uniform(-1000, 1000))
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # Noise jitter for voronoi
    mul_scale = _math(nt, "MULTIPLY", scale, 5.0)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise, "noise_dimensions"):
        try:
            noise.noise_dimensions = "4D"
        except TypeError:
            pass
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(mul_scale.outputs[0], noise.inputs["Scale"])
    if "W" in noise.inputs:
        noise.inputs["W"].default_value = seed
    if "Detail" in noise.inputs:
        noise.inputs["Detail"].default_value = 15.0
    if "Roughness" in noise.inputs:
        noise.inputs["Roughness"].default_value = 0.4
    if "Distortion" in noise.inputs:
        noise.inputs["Distortion"].default_value = 0.2

    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
    mix.inputs[0].default_value = 0.05
    nt.links.new(tex_coord.outputs["Object"], mix.inputs[6])
    nt.links.new(noise.outputs["Color"], mix.inputs[7])

    mul_voronoi_scale = _math(nt, "MULTIPLY", scale, 500.0)
    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(voronoi, "voronoi_dimensions"):
        try:
            voronoi.voronoi_dimensions = "4D"
        except TypeError:
            pass
    if hasattr(voronoi, "distance"):
        try:
            voronoi.distance = "MINKOWSKI"
        except TypeError:
            pass
    nt.links.new(mix.outputs[2], voronoi.inputs["Vector"])
    nt.links.new(mul_voronoi_scale.outputs[0], voronoi.inputs["Scale"])
    if "W" in voronoi.inputs:
        voronoi.inputs["W"].default_value = seed

    mr = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(voronoi.outputs["Color"], mr.inputs[0])
    mr.inputs[3].default_value = 0.1
    mr.inputs[4].default_value = 0.5

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf,
        Metallic=1.0,
        **{"Specular IOR Level": 0.0},
        **{"Base Color": hsv2rgba(base_color_hsv)},
    )
    nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat


def make_grained_metal(name="GrainedMetal", base_color_hsv=None, scale=5.0):
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    roughness = float(np.random.uniform(0.0, 1.0))
    seed = float(np.random.uniform(-1000, 1000))
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs[0].default_value = roughness
    mr.inputs[3].default_value = 0.05
    mr.inputs[4].default_value = 0.25

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf,
        Metallic=1.0,
        **{"Specular IOR Level": 0.0},
        **{"Base Color": hsv2rgba(base_color_hsv)},
    )
    nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])

    mul_ns = _math(nt, "MULTIPLY", scale, 2000.0)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise, "noise_dimensions"):
        try:
            noise.noise_dimensions = "4D"
        except TypeError:
            pass
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(mul_ns.outputs[0], noise.inputs["Scale"])
    if "W" in noise.inputs:
        noise.inputs["W"].default_value = seed
    if "Detail" in noise.inputs:
        noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs:
        noise.inputs["Distortion"].default_value = 2.0

    mul_r = _math(nt, "MULTIPLY", mr.outputs["Result"], 0.4)
    mul_disp = _math(nt, "MULTIPLY", _noise_fac_output(noise), mul_r.outputs[0])
    mul_final = _math(nt, "MULTIPLY", mul_disp.outputs[0], 0.01)

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_final.outputs[0], disp.inputs["Height"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


def make_hammered_metal(name="HammeredMetal", base_color_hsv=None, scale=None):
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    if scale is None:
        scale = log_uniform(0.8, 1.2)
    seed = float(np.random.uniform(-1000, 1000))
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf,
        Metallic=1.0,
        Roughness=0.1,
        **{"Specular IOR Level": 0.0},
        **{"Base Color": hsv2rgba(base_color_hsv)},
    )

    mul_scale = _math(nt, "MULTIPLY", scale, 20.0)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise, "noise_dimensions"):
        try:
            noise.noise_dimensions = "4D"
        except TypeError:
            pass
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(mul_scale.outputs[0], noise.inputs["Scale"])
    if "W" in noise.inputs:
        noise.inputs["W"].default_value = seed
    if "Detail" in noise.inputs:
        noise.inputs["Detail"].default_value = 15.0
    if "Roughness" in noise.inputs:
        noise.inputs["Roughness"].default_value = 0.4
    if "Distortion" in noise.inputs:
        noise.inputs["Distortion"].default_value = 0.2

    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
    mix.inputs[0].default_value = 0.01
    nt.links.new(tex_coord.outputs["Object"], mix.inputs[6])
    nt.links.new(noise.outputs["Color"], mix.inputs[7])

    mul_voronoi_scale = _math(nt, "MULTIPLY", scale, 300.0)
    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(voronoi, "voronoi_dimensions"):
        try:
            voronoi.voronoi_dimensions = "4D"
        except TypeError:
            pass
    if hasattr(voronoi, "feature"):
        try:
            voronoi.feature = "SMOOTH_F1"
        except TypeError:
            pass
    nt.links.new(mix.outputs[2], voronoi.inputs["Vector"])
    nt.links.new(mul_voronoi_scale.outputs[0], voronoi.inputs["Scale"])
    if "W" in voronoi.inputs:
        voronoi.inputs["W"].default_value = seed
    if "Smoothness" in voronoi.inputs:
        voronoi.inputs["Smoothness"].default_value = 0.2

    mul_dist = _math(nt, "MULTIPLY",
                     voronoi.outputs.get("Distance") or voronoi.outputs[0],
                     scale)
    power = _math(nt, "POWER", mul_dist.outputs[0], 2.5)
    bump_scale = log_uniform(0.001, 0.003)
    mul_bump = _math(nt, "MULTIPLY", power.outputs[0], bump_scale)

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_bump.outputs[0], disp.inputs["Height"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


def make_brushed_black_metal(name="BrushedBlackMetal"):
    mat = _new_material(name)
    nt = mat.node_tree
    # Anisotropic BSDF may not be available in all Blender versions;
    # fallback to Principled with anisotropic settings.
    try:
        aniso = nt.nodes.new("ShaderNodeBsdfAnisotropic")
        aniso.inputs["Color"].default_value = (0.0167, 0.0167, 0.0167, 1.0)
        _connect_output(nt, aniso)
    except Exception:
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        _set_principled(
            bsdf,
            Metallic=1.0,
            Roughness=0.3,
            **{"Base Color": (0.0167, 0.0167, 0.0167, 1.0)},
        )
        if "Anisotropic" in bsdf.inputs:
            bsdf.inputs["Anisotropic"].default_value = 0.5
        _connect_output(nt, bsdf)
    return mat


# --- Metals registry (matches material_assignments.metals) --------------------

metals_registry = [
    (make_metal_basic, 3.0),
    (make_brushed_metal, 2.0),
    (make_galvanized_metal, 1.0),
    (make_grained_metal, 1.0),
    (make_hammered_metal, 0.7),
    (make_brushed_black_metal, 0.3),
]


def get_metal_material(name="Metal"):
    ctor = weighted_sample(metals_registry)
    return ctor(name=name)


# --- wear_tear ----------------------------------------------------------------

WEAR_TEAR_PROB = [0.5, 0.5]
SCRATCH_LABEL = "scratch"
EDGE_WEAR_LABEL = "wear_tear"


def get_scratch_params():
    return dict(
        angle1=float(np.random.uniform(10.0, 80.0)),
        angle2=float(np.random.uniform(-80.0, -10.0)),
        scratch_scale=log_uniform(5, 80),
        scratch_mask_ratio=log_uniform(0.01, 0.9),
        scratch_mask_noise=log_uniform(5, 40),
        scratch_depth=log_uniform(0.1, 1.0),
    )


def _build_scratch_graph(nt, params):
    n_angle1 = _value_node(nt, params["angle1"])
    n_angle2 = _value_node(nt, params["angle2"])
    n_scale = _value_node(nt, params["scratch_scale"])
    n_mask_ratio = _value_node(nt, params["scratch_mask_ratio"])
    n_mask_noise = _value_node(nt, params["scratch_mask_noise"])
    n_depth = _value_node(nt, params["scratch_depth"])
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    cxyz1 = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(n_angle1.outputs[0], cxyz1.inputs["Y"])
    map1 = nt.nodes.new("ShaderNodeMapping")
    if hasattr(map1, "vector_type"):
        try:
            map1.vector_type = "TEXTURE"
        except TypeError:
            pass
    map1.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map1.inputs["Vector"])
    nt.links.new(cxyz1.outputs[0], map1.inputs["Rotation"])
    noise1 = _noise_tex(nt, map1.outputs["Vector"], n_scale.outputs[0],
                        detail=15.0, distortion=22.8, roughness=0.0)

    cxyz2 = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(n_angle2.outputs[0], cxyz2.inputs["Y"])
    map2 = nt.nodes.new("ShaderNodeMapping")
    if hasattr(map2, "vector_type"):
        try:
            map2.vector_type = "TEXTURE"
        except TypeError:
            pass
    map2.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map2.inputs["Vector"])
    nt.links.new(cxyz2.outputs[0], map2.inputs["Rotation"])
    noise2 = _noise_tex(nt, map2.outputs["Vector"], n_scale.outputs[0],
                        detail=15.0, distortion=22.8, roughness=0.0)

    add = _math(nt, "ADD", _noise_fac_output(noise1), _noise_fac_output(noise2))

    map3 = nt.nodes.new("ShaderNodeMapping")
    if hasattr(map3, "vector_type"):
        try:
            map3.vector_type = "TEXTURE"
        except TypeError:
            pass
    map3.inputs["Rotation"].default_value = (0.1588, -0.5742, 0.1920)
    nt.links.new(tex_coord.outputs["Object"], map3.inputs["Vector"])
    noise3 = _noise_tex(nt, map3.outputs["Vector"], n_mask_noise.outputs[0], detail=1.0)
    cr_mask = _color_ramp(nt, _noise_fac_output(noise3),
                          [(0.4109, (0, 0, 0, 1)), (1.0, (1, 1, 1, 1))])
    mul_mask = _math(nt, "MULTIPLY", n_mask_ratio.outputs[0], cr_mask.outputs["Color"])
    add_combined = _math(nt, "ADD", add.outputs[0], mul_mask.outputs[0], clamp=True)

    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[1].default_value = 0.7
    map_range.inputs[2].default_value = 0.72
    map_range.inputs[4].default_value = 0.9
    nt.links.new(add_combined.outputs[0], map_range.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(map_range.outputs["Result"], disp.inputs["Height"])
    nt.links.new(n_depth.outputs[0], disp.inputs["Scale"])
    return disp.outputs[0]


def apply_scratches(obj, **params):
    if obj is None or obj.data is None or not hasattr(obj.data, "materials"):
        return
    if not params:
        params = get_scratch_params()
    for slot_idx in range(len(obj.data.materials)):
        mat = obj.data.materials[slot_idx]
        if mat is None or not mat.use_nodes:
            continue
        nt = mat.node_tree
        if any(n.label == SCRATCH_LABEL for n in nt.nodes):
            continue
        mat_out = _find_node(nt, "ShaderNodeOutputMaterial")
        if mat_out is None:
            continue
        try:
            disp_out = _build_scratch_graph(nt, params)
            nt.links.new(disp_out, mat_out.inputs["Displacement"])
            disp_out.node.label = SCRATCH_LABEL
        except Exception as e:
            print(f"  [scratches] failed on {mat.name}: {type(e).__name__}: {e}")


def get_edge_wear_params():
    return dict(
        worn_off_opacity=float(np.random.uniform(0, 0.01)),
        worn_off_radius=float(np.random.uniform(0.005, 0.01)),
        scratch_radius=float(np.random.uniform(0.01, 0.03)),
        worn_off_mask_randomness=float(np.random.uniform(2.5, 3.0)),
        edge_base_color_hue=float(np.random.uniform(0.0, 1.0)),
        edge_base_color_whiteness=float(np.random.uniform(0.1, 0.6)),
        scratch_mask_randomness=float(np.random.choice(
            [np.random.uniform(0.1, 5.0), np.random.uniform(1.0, 10.0)])),
        scratch_density=float(np.random.uniform(1.5, 10.0)),
        scratch_opacity=float(np.random.uniform(0.5, 1.0)),
    )


def _build_edge_wear_graph(nt, original_bsdf_node, original_displacement_node, p):
    n_scratch_opacity = _value_node(nt, p["scratch_opacity"])
    n_scratch_mask_randomness = _value_node(nt, p["scratch_mask_randomness"])
    n_scratch_radius = _value_node(nt, p["scratch_radius"])
    n_worn_opacity = _value_node(nt, p["worn_off_opacity"])
    n_worn_radius = _value_node(nt, p["worn_off_radius"])
    n_worn_mask_randomness = _value_node(nt, p["worn_off_mask_randomness"])
    n_edge_whiteness = _value_node(nt, p["edge_base_color_whiteness"])
    n_edge_hue = _value_node(nt, p["edge_base_color_hue"])
    n_scratch_density = _value_node(nt, p["scratch_density"])

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    noise_a = _noise_tex(nt, mapping.outputs["Vector"],
                         n_scratch_mask_randomness.outputs[0], detail=1.0)
    cr_a = _color_ramp(nt, _noise_fac_output(noise_a),
                       [(0.4436, (0, 0, 0, 1)), (0.5345, (1, 1, 1, 1))])

    bevel = nt.nodes.new("ShaderNodeBevel")
    bevel.samples = 20
    nt.links.new(n_scratch_radius.outputs[0], bevel.inputs["Radius"])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sub = _vmath(nt, "SUBTRACT", bevel.outputs[0], geo.outputs["Normal"])
    abs_a = _math(nt, "ABSOLUTE", sub.outputs["Vector"])
    cr_b = _color_ramp(nt, abs_a.outputs[0],
                       [(0.0691, (0, 0, 0, 1)), (0.1564, (1, 1, 1, 1))])

    mul_a = _math(nt, "MULTIPLY", cr_a.outputs["Color"], cr_b.outputs["Color"],
                  clamp=True)
    mul_a1 = _math(nt, "MULTIPLY", n_scratch_opacity.outputs[0], mul_a.outputs[0],
                   clamp=True)

    bevel2 = nt.nodes.new("ShaderNodeBevel")
    bevel2.samples = 20
    nt.links.new(n_worn_radius.outputs[0], bevel2.inputs["Radius"])
    sub2 = _vmath(nt, "SUBTRACT", bevel2.outputs[0], geo.outputs["Normal"])
    abs_b = _math(nt, "ABSOLUTE", sub2.outputs["Vector"])

    noise_b = _noise_tex(nt, mapping.outputs["Vector"],
                         n_worn_mask_randomness.outputs[0], detail=1.0)
    cr_c = _color_ramp(nt, _noise_fac_output(noise_b),
                       [(0.0764, (1, 1, 1, 1)), (0.5709, (0, 0, 0, 1))])
    mul_b = _math(nt, "MULTIPLY", abs_b.outputs[0], cr_c.outputs["Color"], clamp=True)
    mul_b1 = _math(nt, "MULTIPLY", n_worn_opacity.outputs[0], mul_b.outputs[0],
                   clamp=True)
    cr_d = _color_ramp(nt, mul_b1.outputs[0],
                       [(0.0, (0, 0, 0, 1)), (0.7782, (1, 1, 1, 1))])

    combine_color = nt.nodes.new("ShaderNodeCombineColor")
    if hasattr(combine_color, "mode"):
        try:
            combine_color.mode = "HSV"
        except TypeError:
            pass
    nt.links.new(n_edge_hue.outputs[0], combine_color.inputs["Red"])
    combine_color.inputs["Green"].default_value = 0.7733
    combine_color.inputs["Blue"].default_value = 0.0100

    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
    nt.links.new(n_edge_whiteness.outputs[0], mix.inputs[0])
    nt.links.new(combine_color.outputs[0], mix.inputs[6])
    mix.inputs[7].default_value = (0.02, 0.02, 0.02, 1.0)

    bsdf_worn1 = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix.outputs[2], bsdf_worn1.inputs["Base Color"])
    _set_principled(bsdf_worn1, Metallic=0.3745, Roughness=0.1436,
                    **{"Specular IOR Level": 0.0})

    mix_shader = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(cr_d.outputs["Color"], mix_shader.inputs["Fac"])
    nt.links.new(original_bsdf_node.outputs[0], mix_shader.inputs[1])
    nt.links.new(bsdf_worn1.outputs[0], mix_shader.inputs[2])

    # Scratch component
    map_h = nt.nodes.new("ShaderNodeMapping")
    map_h.inputs["Scale"].default_value = (10.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map_h.inputs["Vector"])
    vor_h = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(vor_h, "feature"):
        try:
            vor_h.feature = "DISTANCE_TO_EDGE"
        except TypeError:
            pass
    nt.links.new(map_h.outputs["Vector"], vor_h.inputs["Vector"])
    nt.links.new(n_scratch_density.outputs[0], vor_h.inputs["Scale"])

    map_v = nt.nodes.new("ShaderNodeMapping")
    map_v.inputs["Scale"].default_value = (1.0, 10.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map_v.inputs["Vector"])

    scale_v = _vmath(nt, "SCALE", in0=n_scratch_density.outputs[0], scale=2.0)
    vor_v = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(vor_v, "feature"):
        try:
            vor_v.feature = "DISTANCE_TO_EDGE"
        except TypeError:
            pass
    nt.links.new(map_v.outputs["Vector"], vor_v.inputs["Vector"])
    nt.links.new(scale_v.outputs[0], vor_v.inputs["Scale"])

    dist_h = vor_h.outputs.get("Distance") or vor_h.outputs[0]
    dist_v = vor_v.outputs.get("Distance") or vor_v.outputs[0]
    mul_dist = _math(nt, "MULTIPLY", dist_h, dist_v, clamp=True)
    cr_e = _color_ramp(nt, mul_dist.outputs[0],
                       [(0.0, (1, 1, 1, 1)), (0.0073, (0, 0, 0, 1))])
    mul_e = _math(nt, "MULTIPLY", cr_b.outputs["Color"], cr_e.outputs["Color"],
                  clamp=True)
    mul_f = _math(nt, "MULTIPLY", mul_a.outputs[0], mul_e.outputs[0], clamp=True)

    bsdf_worn2 = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix.outputs[2], bsdf_worn2.inputs["Base Color"])
    _set_principled(bsdf_worn2, Metallic=0.3855, Roughness=0.0,
                    **{"Specular IOR Level": 0.0})

    mix_shader_2 = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mul_a1.outputs[0], mix_shader_2.inputs["Fac"])
    nt.links.new(mix_shader.outputs[0], mix_shader_2.inputs[1])
    nt.links.new(bsdf_worn2.outputs[0], mix_shader_2.inputs[2])

    scale_disp = _vmath(nt, "SCALE", in0=mul_f.outputs[0], scale=2.0)
    if original_displacement_node is None:
        total_displacement = scale_disp.outputs[0]
    else:
        add_disp = _math(nt, "ADD", original_displacement_node.outputs[0],
                         scale_disp.outputs[0], clamp=True)
        total_displacement = add_disp.outputs[0]
    return mix_shader_2.outputs[0], total_displacement


def apply_edge_wear(obj, **params):
    if obj is None or obj.data is None or not hasattr(obj.data, "materials"):
        return
    if not params:
        params = get_edge_wear_params()
    for slot_idx in range(len(obj.data.materials)):
        mat = obj.data.materials[slot_idx]
        if mat is None or not mat.use_nodes:
            continue
        nt = mat.node_tree
        if any(n.label == EDGE_WEAR_LABEL for n in nt.nodes):
            continue
        mat_out = _find_node(nt, "ShaderNodeOutputMaterial")
        if mat_out is None:
            continue
        surface_links = mat_out.inputs["Surface"].links
        if not surface_links:
            continue
        original_bsdf = surface_links[0].from_node
        disp_links = mat_out.inputs["Displacement"].links
        original_disp = disp_links[0].from_node if disp_links else None
        try:
            final_bsdf_socket, final_disp_socket = _build_edge_wear_graph(
                nt, original_bsdf, original_disp, params)
            nt.links.new(final_bsdf_socket, mat_out.inputs["Surface"])
            nt.links.new(final_disp_socket, mat_out.inputs["Displacement"])
            final_bsdf_socket.node.label = EDGE_WEAR_LABEL
        except Exception as e:
            print(f"  [edge_wear] failed on {mat.name}: {type(e).__name__}: {e}")


# ============================================================================
# Geometry — identical to objects_blender/table_decorations/SinkFactory.py
# ============================================================================

def build_handle_nodegroup():
    ng = bpy.data.node_groups.new("nodegroup_handle", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    nodes = ng.nodes
    links = ng.links

    out = nodes.new("NodeGroupOutput")
    out.location = (1200, 0)

    bezier = nodes.new("GeometryNodeCurvePrimitiveBezierSegment")
    bezier.inputs["Start"].default_value = (0, 0, 0)
    bezier.inputs["Start Handle"].default_value = (0, 0, 0.7)
    bezier.inputs["End Handle"].default_value = (0.2, 0, 0.7)
    bezier.inputs["End"].default_value = (1, 0, 0.9)

    sparam = nodes.new("GeometryNodeSplineParameter")
    fcurve = nodes.new("ShaderNodeFloatCurve")
    assign_float_curve(fcurve.mapping, [(0.0, 0.975), (1.0, 0.1625)])
    links.new(sparam.outputs["Factor"], fcurve.inputs["Value"])

    mul = nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 1.3
    links.new(fcurve.outputs[0], mul.inputs[0])

    scr = nodes.new("GeometryNodeSetCurveRadius")
    links.new(bezier.outputs[0], scr.inputs["Curve"])
    links.new(mul.outputs[0], scr.inputs["Radius"])

    cc = nodes.new("GeometryNodeCurvePrimitiveCircle")
    cc.inputs["Radius"].default_value = 0.2
    cc.mode = "RADIUS"

    ctm = nodes.new("GeometryNodeCurveToMesh")
    links.new(scr.outputs[0], ctm.inputs["Curve"])
    links.new(cc.outputs["Curve"], ctm.inputs["Profile Curve"])
    ctm.inputs["Fill Caps"].default_value = True

    pos = nodes.new("GeometryNodeInputPosition")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(pos.outputs[0], sep.inputs[0])

    mr = nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.2
    mr.inputs["From Max"].default_value = 1.0
    mr.inputs["To Min"].default_value = 1.0
    mr.inputs["To Max"].default_value = 2.5
    links.new(sep.outputs["X"], mr.inputs["Value"])

    mul2 = nodes.new("ShaderNodeMath")
    mul2.operation = "MULTIPLY"
    links.new(sep.outputs["Y"], mul2.inputs[0])
    links.new(mr.outputs["Result"], mul2.inputs[1])

    comb = nodes.new("ShaderNodeCombineXYZ")
    links.new(sep.outputs["X"], comb.inputs["X"])
    links.new(mul2.outputs[0], comb.inputs["Y"])
    links.new(sep.outputs["Z"], comb.inputs["Z"])

    sp = nodes.new("GeometryNodeSetPosition")
    links.new(ctm.outputs[0], sp.inputs["Geometry"])
    links.new(comb.outputs[0], sp.inputs["Position"])

    subdiv = nodes.new("GeometryNodeSubdivisionSurface")
    subdiv.inputs["Level"].default_value = 2
    links.new(sp.outputs[0], subdiv.inputs["Mesh"])

    sss = nodes.new("GeometryNodeSetShadeSmooth")
    links.new(subdiv.outputs[0], sss.inputs["Geometry"])

    links.new(sss.outputs[0], out.inputs[0])
    return ng


def build_water_tap_nodegroup(params):
    ng = bpy.data.node_groups.new("nodegroup_water_tap_sink", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    nodes = ng.nodes
    links = ng.links

    gi = nodes.new("NodeGroupInput")
    go = nodes.new("NodeGroupOutput")

    # Vertical stem
    stem_line = nodes.new("GeometryNodeCurvePrimitiveLine")
    stem_line.inputs["End"].default_value = (0, 0, 0.6)
    stem_profile = nodes.new("GeometryNodeCurvePrimitiveCircle")
    stem_profile.inputs["Radius"].default_value = 0.03
    stem_profile.mode = "RADIUS"
    stem_mesh = nodes.new("GeometryNodeCurveToMesh")
    links.new(stem_line.outputs[0], stem_mesh.inputs["Curve"])
    links.new(stem_profile.outputs["Curve"], stem_mesh.inputs["Profile Curve"])

    # Spout A (ring)
    spout_circle = nodes.new("GeometryNodeCurvePrimitiveCircle")
    spout_circle.inputs["Radius"].default_value = 0.2
    spout_circle.mode = "RADIUS"
    spout_tf1 = nodes.new("GeometryNodeTransform")
    spout_tf1.inputs["Translation"].default_value = (0, 0.2, 0)
    links.new(spout_circle.outputs["Curve"], spout_tf1.inputs["Geometry"])
    spout_tf2 = nodes.new("GeometryNodeTransform")
    spout_tf2.inputs["Rotation"].default_value = (-1.5708, 1.5708, 0)
    spout_tf2.inputs["Scale"].default_value = (1, 0.7, 1)
    links.new(spout_tf1.outputs[0], spout_tf2.inputs["Geometry"])

    # Spout B (bezier)
    comb_eh = nodes.new("ShaderNodeCombineXYZ")
    comb_eh.inputs["X"].default_value = 0.2
    comb_eh.inputs["Y"].default_value = params["Y"]
    bezier_sp = nodes.new("GeometryNodeCurvePrimitiveBezierSegment")
    bezier_sp.inputs["Resolution"].default_value = 177
    bezier_sp.inputs["Start"].default_value = (0, 0, 0)
    bezier_sp.inputs["Start Handle"].default_value = (0, 1.2, 0)
    links.new(comb_eh.outputs[0], bezier_sp.inputs["End Handle"])
    bezier_sp.inputs["End"].default_value = (-0.05, 0.1, 0)
    trim = nodes.new("GeometryNodeTrimCurve")
    links.new(bezier_sp.outputs[0], trim.inputs["Curve"])
    trim.inputs[3].default_value = 0.6625
    trim.inputs[5].default_value = 3.0
    spout_tf3 = nodes.new("GeometryNodeTransform")
    spout_tf3.inputs["Rotation"].default_value = (1.5708, 0, 2.522)
    spout_tf3.inputs["Scale"].default_value = (5.2, 0.5, 7.8)
    links.new(trim.outputs[0], spout_tf3.inputs["Geometry"])
    spout_prof = nodes.new("GeometryNodeCurvePrimitiveCircle")
    spout_prof.inputs["Radius"].default_value = 0.03
    spout_prof.mode = "RADIUS"
    spout_b_mesh = nodes.new("GeometryNodeCurveToMesh")
    links.new(spout_tf3.outputs[0], spout_b_mesh.inputs["Curve"])
    links.new(spout_prof.outputs["Curve"], spout_b_mesh.inputs["Profile Curve"])

    # Switch spout
    sw_sp = nodes.new("GeometryNodeSwitch")
    sw_sp.input_type = "GEOMETRY"
    sw_sp.inputs[0].default_value = params["Switch"]
    links.new(spout_tf2.outputs[0], sw_sp.inputs[1])
    links.new(spout_b_mesh.outputs[0], sw_sp.inputs[2])

    spout_mesh = nodes.new("GeometryNodeCurveToMesh")
    links.new(sw_sp.outputs[0], spout_mesh.inputs["Curve"])
    links.new(stem_profile.outputs["Curve"], spout_mesh.inputs["Profile Curve"])

    # Filter Z > -0.01
    pos1 = nodes.new("GeometryNodeInputPosition")
    sep1 = nodes.new("ShaderNodeSeparateXYZ")
    links.new(pos1.outputs[0], sep1.inputs[0])
    gt = nodes.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    links.new(sep1.outputs["Z"], gt.inputs[0])
    gt.inputs[1].default_value = -0.01
    sw_sel = nodes.new("GeometryNodeSwitch")
    sw_sel.input_type = "FLOAT"
    sw_sel.inputs[0].default_value = params["Switch"]
    links.new(gt.outputs[0], sw_sel.inputs[1])
    sw_sel.inputs[2].default_value = 1.0
    sep_geo = nodes.new("GeometryNodeSeparateGeometry")
    links.new(spout_mesh.outputs[0], sep_geo.inputs["Geometry"])
    links.new(sw_sel.outputs[0], sep_geo.inputs["Selection"])

    # Scale by tap_head
    c_th = nodes.new("ShaderNodeCombineXYZ")
    c_th.inputs["X"].default_value = 1
    c_th.inputs["Y"].default_value = 1
    c_th.inputs["Z"].default_value = params["tap_head"]
    sw_th = nodes.new("GeometryNodeSwitch")
    sw_th.input_type = "VECTOR"
    sw_th.inputs[0].default_value = params["Switch"]
    links.new(c_th.outputs[0], sw_th.inputs[1])
    sw_th.inputs[2].default_value = (1, 1, 1)
    spout_pos = nodes.new("GeometryNodeTransform")
    spout_pos.inputs["Translation"].default_value = (0, 0, 0.6)
    links.new(sep_geo.outputs["Selection"], spout_pos.inputs["Geometry"])
    links.new(sw_th.outputs[0], spout_pos.inputs["Scale"])

    join_ss = nodes.new("GeometryNodeJoinGeometry")
    links.new(stem_mesh.outputs[0], join_ss.inputs["Geometry"])
    links.new(spout_pos.outputs[0], join_ss.inputs["Geometry"])

    c_rot = nodes.new("ShaderNodeCombineXYZ")
    c_rot.inputs["Z"].default_value = params["roation_z"]
    c_ht = nodes.new("ShaderNodeCombineXYZ")
    c_ht.inputs["X"].default_value = 1
    c_ht.inputs["Y"].default_value = 1
    c_ht.inputs["Z"].default_value = params["tap_height"]
    tf_body = nodes.new("GeometryNodeTransform")
    links.new(join_ss.outputs[0], tf_body.inputs["Geometry"])
    links.new(c_rot.outputs[0], tf_body.inputs["Rotation"])
    links.new(c_ht.outputs[0], tf_body.inputs["Scale"])

    # Handle A
    handle_ng = build_handle_nodegroup()
    h1 = nodes.new("GeometryNodeGroup")
    h1.node_tree = handle_ng
    htf1 = nodes.new("GeometryNodeTransform")
    htf1.inputs["Translation"].default_value = (0, -0.2, 0)
    htf1.inputs["Rotation"].default_value = (0, 0, 3.6652)
    htf1.inputs["Scale"].default_value = (0.3, 0.3, 0.3)
    links.new(h1.outputs[0], htf1.inputs["Geometry"])
    h2 = nodes.new("GeometryNodeGroup")
    h2.node_tree = handle_ng
    htf2 = nodes.new("GeometryNodeTransform")
    htf2.inputs["Translation"].default_value = (0, 0.2, 0)
    htf2.inputs["Rotation"].default_value = (0, 0, 2.618)
    htf2.inputs["Scale"].default_value = (0.3, 0.3, 0.3)
    links.new(h2.outputs[0], htf2.inputs["Geometry"])
    jh_a = nodes.new("GeometryNodeJoinGeometry")
    links.new(htf1.outputs[0], jh_a.inputs["Geometry"])
    links.new(htf2.outputs[0], jh_a.inputs["Geometry"])

    # Handle B (cylinders)
    cy1 = nodes.new("GeometryNodeMeshCylinder")
    cy1.inputs["Vertices"].default_value = 41
    cy1.inputs["Side Segments"].default_value = 39
    cy1.inputs["Radius"].default_value = 0.03
    cy1.inputs["Depth"].default_value = 0.1
    cy1r = nodes.new("GeometryNodeTransform")
    cy1r.inputs["Translation"].default_value = (0, 0.05, 0.1)
    cy1r.inputs["Rotation"].default_value = (1.5708, 0, 0)
    links.new(cy1.outputs["Mesh"], cy1r.inputs["Geometry"])
    sw_os1 = nodes.new("GeometryNodeSwitch")
    sw_os1.input_type = "GEOMETRY"
    sw_os1.inputs[0].default_value = params["one_side"]
    links.new(cy1r.outputs[0], sw_os1.inputs[1])
    cy1l = nodes.new("GeometryNodeTransform")
    cy1l.inputs["Translation"].default_value = (0, -0.05, 0.1)
    cy1l.inputs["Rotation"].default_value = (1.5708, 0, 0)
    links.new(cy1.outputs["Mesh"], cy1l.inputs["Geometry"])
    jbc = nodes.new("GeometryNodeJoinGeometry")
    links.new(sw_os1.outputs[0], jbc.inputs["Geometry"])
    links.new(cy1l.outputs[0], jbc.inputs["Geometry"])

    cy2 = nodes.new("GeometryNodeMeshCylinder")
    cy2.inputs["Vertices"].default_value = 41
    cy2.inputs["Side Segments"].default_value = 39
    cy2.inputs["Radius"].default_value = 0.005
    cy2.inputs["Depth"].default_value = 0.1
    cy2r = nodes.new("GeometryNodeTransform")
    cy2r.inputs["Translation"].default_value = (0, 0.08, 0.15)
    cy2r.inputs["Scale"].default_value = (1, 1, 1.1)
    links.new(cy2.outputs["Mesh"], cy2r.inputs["Geometry"])
    sw_os2 = nodes.new("GeometryNodeSwitch")
    sw_os2.input_type = "GEOMETRY"
    sw_os2.inputs[0].default_value = params["one_side"]
    links.new(cy2r.outputs[0], sw_os2.inputs[1])
    cy2l = nodes.new("GeometryNodeTransform")
    cy2l.inputs["Translation"].default_value = (0, -0.08, 0.15)
    cy2l.inputs["Rotation"].default_value = (0, 0, 0.0855)
    cy2l.inputs["Scale"].default_value = (1, 1, 1.1)
    links.new(cy2.outputs["Mesh"], cy2l.inputs["Geometry"])

    length_one_side = params.get("length_one_side", U() < 0.2)
    cy2l_long = nodes.new("GeometryNodeTransform")
    cy2l_long.inputs["Translation"].default_value = (0, -0.01, -0.005)
    cy2l_long.inputs["Scale"].default_value = (4.1, 1, 1)
    links.new(cy2l.outputs[0], cy2l_long.inputs["Geometry"])
    sw_len = nodes.new("GeometryNodeSwitch")
    sw_len.input_type = "GEOMETRY"
    sw_len.inputs[0].default_value = length_one_side
    links.new(cy2l.outputs[0], sw_len.inputs[1])
    links.new(cy2l_long.outputs[0], sw_len.inputs[2])
    sw_ol2 = nodes.new("GeometryNodeSwitch")
    sw_ol2.input_type = "GEOMETRY"
    sw_ol2.inputs[0].default_value = params["one_side"]
    links.new(cy2l.outputs[0], sw_ol2.inputs[1])
    links.new(sw_len.outputs[0], sw_ol2.inputs[2])
    jtc = nodes.new("GeometryNodeJoinGeometry")
    links.new(sw_os2.outputs[0], jtc.inputs["Geometry"])
    links.new(sw_ol2.outputs[0], jtc.inputs["Geometry"])
    jac = nodes.new("GeometryNodeJoinGeometry")
    links.new(jbc.outputs[0], jac.inputs["Geometry"])
    links.new(jtc.outputs[0], jac.inputs["Geometry"])

    c_hands = nodes.new("ShaderNodeCombineXYZ")
    c_hands.inputs["X"].default_value = params["hands_length_x"]
    c_hands.inputs["Y"].default_value = params["hands_length_Y"]
    c_hands.inputs["Z"].default_value = 1.0
    tf_hands = nodes.new("GeometryNodeTransform")
    links.new(jac.outputs[0], tf_hands.inputs["Geometry"])
    links.new(c_hands.outputs[0], tf_hands.inputs["Scale"])

    sw_hand = nodes.new("GeometryNodeSwitch")
    sw_hand.input_type = "GEOMETRY"
    sw_hand.inputs[0].default_value = params["hand_type"]
    links.new(jh_a.outputs[0], sw_hand.inputs[1])
    links.new(tf_hands.outputs[0], sw_hand.inputs[2])

    # Base (circle)
    bc = nodes.new("GeometryNodeCurvePrimitiveCircle")
    bc.inputs["Radius"].default_value = 0.05
    bc.mode = "RADIUS"
    bf = nodes.new("GeometryNodeFillCurve")
    links.new(bc.outputs["Curve"], bf.inputs["Curve"])
    be = nodes.new("GeometryNodeExtrudeMesh")
    be.inputs["Offset Scale"].default_value = 0.15
    links.new(bf.outputs[0], be.inputs["Mesh"])

    j_std = nodes.new("GeometryNodeJoinGeometry")
    links.new(tf_body.outputs[0], j_std.inputs["Geometry"])
    links.new(sw_hand.outputs[0], j_std.inputs["Geometry"])
    links.new(be.outputs["Mesh"], j_std.inputs["Geometry"])

    # Alt body (different_type=True): bezier body with Y-flatten, plus disc base + arm/knob cylinders.
    alt_bezier = nodes.new("GeometryNodeCurvePrimitiveBezierSegment")
    alt_bezier.inputs["Resolution"].default_value = 54
    alt_bezier.inputs["Start"].default_value = (0, 0, 0)
    alt_bezier.inputs["Start Handle"].default_value = (0, 0, 0.7)
    alt_bezier.inputs["End Handle"].default_value = (0.2, 0, 0.7)
    alt_bezier.inputs["End"].default_value = (1, 0, 0.9)

    alt_sparam = nodes.new("GeometryNodeSplineParameter")
    alt_fcurve = nodes.new("ShaderNodeFloatCurve")
    assign_float_curve(
        alt_fcurve.mapping,
        [(0.0, 0.975), (0.6295, 0.4125), (1.0, 0.1625)],
    )
    links.new(alt_sparam.outputs["Factor"], alt_fcurve.inputs["Value"])

    alt_mul = nodes.new("ShaderNodeMath")
    alt_mul.operation = "MULTIPLY"
    alt_mul.inputs[1].default_value = 1.3
    links.new(alt_fcurve.outputs[0], alt_mul.inputs[0])

    alt_scr = nodes.new("GeometryNodeSetCurveRadius")
    links.new(alt_bezier.outputs[0], alt_scr.inputs["Curve"])
    links.new(alt_mul.outputs[0], alt_scr.inputs["Radius"])

    alt_profile = nodes.new("GeometryNodeCurvePrimitiveCircle")
    alt_profile.inputs["Radius"].default_value = 0.1
    alt_profile.mode = "RADIUS"

    alt_ctm = nodes.new("GeometryNodeCurveToMesh")
    links.new(alt_scr.outputs[0], alt_ctm.inputs["Curve"])
    links.new(alt_profile.outputs["Curve"], alt_ctm.inputs["Profile Curve"])
    alt_ctm.inputs["Fill Caps"].default_value = True

    alt_pos = nodes.new("GeometryNodeInputPosition")
    alt_sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(alt_pos.outputs[0], alt_sep.inputs[0])

    alt_mr = nodes.new("ShaderNodeMapRange")
    alt_mr.inputs["From Min"].default_value = 0.2
    alt_mr.inputs["From Max"].default_value = 1.0
    alt_mr.inputs["To Min"].default_value = 1.0
    alt_mr.inputs["To Max"].default_value = 2.5
    links.new(alt_sep.outputs["X"], alt_mr.inputs["Value"])

    alt_mul2 = nodes.new("ShaderNodeMath")
    alt_mul2.operation = "MULTIPLY"
    links.new(alt_sep.outputs["Y"], alt_mul2.inputs[0])
    links.new(alt_mr.outputs["Result"], alt_mul2.inputs[1])

    alt_comb = nodes.new("ShaderNodeCombineXYZ")
    links.new(alt_sep.outputs["X"], alt_comb.inputs["X"])
    links.new(alt_mul2.outputs[0], alt_comb.inputs["Y"])
    links.new(alt_sep.outputs["Z"], alt_comb.inputs["Z"])

    alt_sp = nodes.new("GeometryNodeSetPosition")
    links.new(alt_ctm.outputs[0], alt_sp.inputs["Geometry"])
    links.new(alt_comb.outputs[0], alt_sp.inputs["Position"])

    alt_subdiv = nodes.new("GeometryNodeSubdivisionSurface")
    alt_subdiv.inputs["Level"].default_value = 1
    links.new(alt_sp.outputs[0], alt_subdiv.inputs["Mesh"])

    alt_sss = nodes.new("GeometryNodeSetShadeSmooth")
    links.new(alt_subdiv.outputs[0], alt_sss.inputs["Geometry"])

    alt_body_tf = nodes.new("GeometryNodeTransform")
    alt_body_tf.inputs["Translation"].default_value = (0, 0, 0.1)
    alt_body_tf.inputs["Rotation"].default_value = (0, 0, 0.6807)
    alt_body_tf.inputs["Scale"].default_value = (0.4, 0.4, 0.3)
    links.new(alt_sss.outputs[0], alt_body_tf.inputs["Geometry"])

    alt_base_circle = nodes.new("GeometryNodeCurvePrimitiveCircle")
    alt_base_circle.inputs["Resolution"].default_value = 307
    alt_base_circle.inputs["Radius"].default_value = 0.055
    alt_base_circle.mode = "RADIUS"

    alt_base_fill = nodes.new("GeometryNodeFillCurve")
    links.new(alt_base_circle.outputs["Curve"], alt_base_fill.inputs["Curve"])

    alt_base_extr = nodes.new("GeometryNodeExtrudeMesh")
    alt_base_extr.inputs["Offset Scale"].default_value = 0.15
    links.new(alt_base_fill.outputs[0], alt_base_extr.inputs["Mesh"])

    alt_arm_cyl = nodes.new("GeometryNodeMeshCylinder")
    alt_arm_cyl.inputs["Vertices"].default_value = 100
    alt_arm_cyl.inputs["Radius"].default_value = 0.01
    alt_arm_cyl.inputs["Depth"].default_value = 0.7

    alt_arm_sp = nodes.new("GeometryNodeSetPosition")
    links.new(alt_arm_cyl.outputs["Mesh"], alt_arm_sp.inputs["Geometry"])

    alt_arm_tf = nodes.new("GeometryNodeTransform")
    alt_arm_tf.inputs["Translation"].default_value = (0.3, 0, 0.25)
    alt_arm_tf.inputs["Rotation"].default_value = (0, -2.042, 0)
    alt_arm_tf.inputs["Scale"].default_value = (1.7, 3.1, 1)
    links.new(alt_arm_sp.outputs[0], alt_arm_tf.inputs["Geometry"])

    alt_knob_cyl = nodes.new("GeometryNodeMeshCylinder")
    alt_knob_cyl.inputs["Vertices"].default_value = 318
    alt_knob_cyl.inputs["Radius"].default_value = 0.02
    alt_knob_cyl.inputs["Depth"].default_value = 0.03

    alt_knob_tf = nodes.new("GeometryNodeTransform")
    alt_knob_tf.inputs["Translation"].default_value = (0.595, 0, 0.38)
    links.new(alt_knob_cyl.outputs["Mesh"], alt_knob_tf.inputs["Geometry"])

    alt_arm_join = nodes.new("GeometryNodeJoinGeometry")
    links.new(alt_arm_tf.outputs[0], alt_arm_join.inputs["Geometry"])
    links.new(alt_knob_tf.outputs[0], alt_arm_join.inputs["Geometry"])

    alt_arm_scale = nodes.new("GeometryNodeTransform")
    alt_arm_scale.inputs["Scale"].default_value = (0.9, 1, 1)
    links.new(alt_arm_join.outputs[0], alt_arm_scale.inputs["Geometry"])

    alt_join = nodes.new("GeometryNodeJoinGeometry")
    links.new(alt_body_tf.outputs[0], alt_join.inputs["Geometry"])
    links.new(alt_base_extr.outputs["Mesh"], alt_join.inputs["Geometry"])
    links.new(alt_arm_scale.outputs[0], alt_join.inputs["Geometry"])

    alt_rot = nodes.new("GeometryNodeTransform")
    alt_rot.inputs["Rotation"].default_value = (0, 0, 3.1416)
    links.new(alt_join.outputs[0], alt_rot.inputs["Geometry"])

    sw_dt = nodes.new("GeometryNodeSwitch")
    sw_dt.input_type = "GEOMETRY"
    sw_dt.inputs[0].default_value = params["different_type"]
    links.new(j_std.outputs[0], sw_dt.inputs[1])
    links.new(alt_rot.outputs[0], sw_dt.inputs[2])

    # Base plate
    qb = nodes.new("GeometryNodeCurvePrimitiveQuadrilateral")
    qb.inputs["Width"].default_value = params["base_width"]
    qb.inputs["Height"].default_value = 0.7
    fb = nodes.new("GeometryNodeFilletCurve")
    fb.inputs["Count"].default_value = 19
    fb.inputs["Radius"].default_value = params["base_radius"]
    links.new(qb.outputs[0], fb.inputs["Curve"])
    set_fillet_mode(fb, "POLY")
    ffb = nodes.new("GeometryNodeFillCurve")
    links.new(fb.outputs[0], ffb.inputs["Curve"])
    efb = nodes.new("GeometryNodeExtrudeMesh")
    efb.inputs["Offset Scale"].default_value = 0.05
    links.new(ffb.outputs[0], efb.inputs["Mesh"])

    fj = nodes.new("GeometryNodeJoinGeometry")
    links.new(sw_dt.outputs[0], fj.inputs["Geometry"])
    links.new(efb.outputs["Mesh"], fj.inputs["Geometry"])

    links.new(fj.outputs[0], go.inputs[0])
    return ng


def build_sink_nodegroup(params):
    ng = bpy.data.node_groups.new("nodegroup_sink_geometry", "GeometryNodeTree")

    geo_in = ng.interface.new_socket("Geometry", in_out="INPUT",
                                     socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT",
                            socket_type="NodeSocketGeometry")

    nodes = ng.nodes
    links = ng.links

    gi = nodes.new("NodeGroupInput")
    go = nodes.new("NodeGroupOutput")

    width = params["Width"]
    depth = params["Depth"]
    curvature = params["Curvature"]
    upper_height = params["Upper Height"]
    lower_height = params["Lower Height"]
    hole_radius = params["HoleRadius"]
    margin = params["Margin"]
    watertap_margin = params["WaterTapMargin"]

    min_dim = min(width, depth)
    fillet_radius = min_dim * 0.1

    # Inner basin quadrilateral
    quad = nodes.new("GeometryNodeCurvePrimitiveQuadrilateral")
    quad.inputs["Width"].default_value = depth
    quad.inputs["Height"].default_value = width

    fillet = nodes.new("GeometryNodeFilletCurve")
    fillet.inputs["Count"].default_value = 50
    fillet.inputs["Radius"].default_value = fillet_radius
    links.new(quad.outputs[0], fillet.inputs["Curve"])
    set_fillet_mode(fillet, "POLY")

    tf_curv = nodes.new("GeometryNodeTransform")
    tf_curv.inputs["Scale"].default_value = (curvature, curvature, 1)
    links.new(fillet.outputs[0], tf_curv.inputs["Geometry"])

    drain_circle = nodes.new("GeometryNodeCurvePrimitiveCircle")
    drain_circle.inputs["Radius"].default_value = hole_radius
    drain_circle.mode = "RADIUS"

    join_floor = nodes.new("GeometryNodeJoinGeometry")
    links.new(tf_curv.outputs[0], join_floor.inputs["Geometry"])
    links.new(drain_circle.outputs["Curve"], join_floor.inputs["Geometry"])

    fill_floor = nodes.new("GeometryNodeFillCurve")
    links.new(join_floor.outputs[0], fill_floor.inputs["Curve"])

    comb_lh = nodes.new("ShaderNodeCombineXYZ")
    comb_lh.inputs["Z"].default_value = lower_height

    tf_floor = nodes.new("GeometryNodeTransform")
    links.new(fill_floor.outputs[0], tf_floor.inputs["Geometry"])
    links.new(comb_lh.outputs[0], tf_floor.inputs["Translation"])

    extr_floor = nodes.new("GeometryNodeExtrudeMesh")
    extr_floor.inputs["Offset Scale"].default_value = -0.01
    extr_floor.inputs["Individual"].default_value = False
    links.new(tf_floor.outputs[0], extr_floor.inputs["Mesh"])

    # Drain pipe
    drain_inner = nodes.new("GeometryNodeTransform")
    drain_inner.inputs["Scale"].default_value = (0.7, 0.7, 1)
    links.new(drain_circle.outputs["Curve"], drain_inner.inputs["Geometry"])

    join_drain_rings = nodes.new("GeometryNodeJoinGeometry")
    links.new(drain_circle.outputs["Curve"], join_drain_rings.inputs["Geometry"])
    links.new(drain_inner.outputs[0], join_drain_rings.inputs["Geometry"])

    fill_drain = nodes.new("GeometryNodeFillCurve")
    links.new(join_drain_rings.outputs[0], fill_drain.inputs["Curve"])

    comb_drain_z = nodes.new("ShaderNodeCombineXYZ")
    comb_drain_z.inputs["Z"].default_value = lower_height - 0.01

    tf_drain_plate = nodes.new("GeometryNodeTransform")
    links.new(fill_drain.outputs[0], tf_drain_plate.inputs["Geometry"])
    links.new(comb_drain_z.outputs[0], tf_drain_plate.inputs["Translation"])

    extr_drain = nodes.new("GeometryNodeExtrudeMesh")
    extr_drain.inputs["Offset Scale"].default_value = lower_height
    extr_drain.inputs["Individual"].default_value = False
    links.new(tf_drain_plate.outputs[0], extr_drain.inputs["Mesh"])

    comb_pipe_end = nodes.new("ShaderNodeCombineXYZ")
    comb_pipe_end.inputs["Z"].default_value = lower_height - 0.01

    drain_line = nodes.new("GeometryNodeCurvePrimitiveLine")
    links.new(comb_pipe_end.outputs[0], drain_line.inputs["End"])

    drain_tube = nodes.new("GeometryNodeCurveToMesh")
    links.new(drain_line.outputs[0], drain_tube.inputs["Curve"])
    links.new(drain_circle.outputs["Curve"], drain_tube.inputs["Profile Curve"])

    tf_drain_tube = nodes.new("GeometryNodeTransform")
    links.new(drain_tube.outputs[0], tf_drain_tube.inputs["Geometry"])
    links.new(comb_lh.outputs[0], tf_drain_tube.inputs["Translation"])

    # Rim
    rim_inner = nodes.new("GeometryNodeTransform")
    rim_inner.inputs["Scale"].default_value = (0.99, 0.99, 1)
    links.new(fillet.outputs[0], rim_inner.inputs["Geometry"])

    join_rim = nodes.new("GeometryNodeJoinGeometry")
    links.new(rim_inner.outputs[0], join_rim.inputs["Geometry"])
    links.new(fillet.outputs[0], join_rim.inputs["Geometry"])

    fill_rim = nodes.new("GeometryNodeFillCurve")
    links.new(join_rim.outputs[0], fill_rim.inputs["Curve"])

    extr_rim = nodes.new("GeometryNodeExtrudeMesh")
    extr_rim.inputs["Offset Scale"].default_value = lower_height
    links.new(fill_rim.outputs[0], extr_rim.inputs["Mesh"])

    # Curvature deformation on rim
    pos_curv = nodes.new("GeometryNodeInputPosition")
    sep_curv = nodes.new("ShaderNodeSeparateXYZ")
    links.new(pos_curv.outputs[0], sep_curv.inputs[0])

    lt = nodes.new("ShaderNodeMath")
    lt.operation = "LESS_THAN"
    links.new(sep_curv.outputs["Z"], lt.inputs[0])
    lt.inputs[1].default_value = 0.0

    pos_curv2 = nodes.new("GeometryNodeInputPosition")
    sep_curv2 = nodes.new("ShaderNodeSeparateXYZ")
    links.new(pos_curv2.outputs[0], sep_curv2.inputs[0])

    mul_cx = nodes.new("ShaderNodeMath")
    mul_cx.operation = "MULTIPLY"
    links.new(sep_curv2.outputs["X"], mul_cx.inputs[0])
    mul_cx.inputs[1].default_value = curvature

    mul_cy = nodes.new("ShaderNodeMath")
    mul_cy.operation = "MULTIPLY"
    links.new(sep_curv2.outputs["Y"], mul_cy.inputs[0])
    mul_cy.inputs[1].default_value = curvature

    comb_curv = nodes.new("ShaderNodeCombineXYZ")
    links.new(mul_cx.outputs[0], comb_curv.inputs["X"])
    links.new(mul_cy.outputs[0], comb_curv.inputs["Y"])
    links.new(sep_curv2.outputs["Z"], comb_curv.inputs["Z"])

    sp_curv = nodes.new("GeometryNodeSetPosition")
    links.new(extr_rim.outputs["Mesh"], sp_curv.inputs["Geometry"])
    links.new(lt.outputs[0], sp_curv.inputs["Selection"])
    links.new(comb_curv.outputs[0], sp_curv.inputs["Position"])

    # Outer body
    depth_total = depth + margin + watertap_margin
    width_total = width + margin
    wtm_offset = -watertap_margin * 0.5

    quad_outer = nodes.new("GeometryNodeCurvePrimitiveQuadrilateral")
    quad_outer.inputs["Width"].default_value = depth_total
    quad_outer.inputs["Height"].default_value = width_total

    tf_outer_offset = nodes.new("GeometryNodeTransform")
    tf_outer_offset.inputs["Translation"].default_value = (wtm_offset, 0, 0)
    links.new(quad_outer.outputs[0], tf_outer_offset.inputs["Geometry"])

    fillet_outer = nodes.new("GeometryNodeFilletCurve")
    fillet_outer.inputs["Count"].default_value = 10
    fillet_outer.inputs["Radius"].default_value = fillet_radius
    links.new(tf_outer_offset.outputs[0], fillet_outer.inputs["Curve"])
    set_fillet_mode(fillet_outer, "POLY")

    join_body = nodes.new("GeometryNodeJoinGeometry")
    links.new(fillet.outputs[0], join_body.inputs["Geometry"])
    links.new(fillet_outer.outputs[0], join_body.inputs["Geometry"])

    fill_body = nodes.new("GeometryNodeFillCurve")
    links.new(join_body.outputs[0], fill_body.inputs["Curve"])

    body_height = upper_height - lower_height
    extr_body = nodes.new("GeometryNodeExtrudeMesh")
    extr_body.inputs["Offset Scale"].default_value = body_height
    links.new(fill_body.outputs[0], extr_body.inputs["Mesh"])

    comb_body_z = nodes.new("ShaderNodeCombineXYZ")
    comb_body_z.inputs["Z"].default_value = lower_height

    tf_body_geo = nodes.new("GeometryNodeTransform")
    links.new(extr_body.outputs["Mesh"], tf_body_geo.inputs["Geometry"])
    links.new(comb_body_z.outputs[0], tf_body_geo.inputs["Translation"])

    # Join all sink parts
    join_all = nodes.new("GeometryNodeJoinGeometry")
    links.new(extr_floor.outputs["Mesh"], join_all.inputs["Geometry"])
    links.new(tf_floor.outputs[0], join_all.inputs["Geometry"])
    links.new(extr_drain.outputs["Mesh"], join_all.inputs["Geometry"])
    links.new(tf_drain_tube.outputs[0], join_all.inputs["Geometry"])
    links.new(sp_curv.outputs[0], join_all.inputs["Geometry"])
    links.new(tf_body_geo.outputs[0], join_all.inputs["Geometry"])

    # Center offset
    center_offset = (watertap_margin + margin) / 2.56
    comb_offset = nodes.new("ShaderNodeCombineXYZ")
    comb_offset.inputs["X"].default_value = center_offset

    sp_final = nodes.new("GeometryNodeSetPosition")
    links.new(join_all.outputs[0], sp_final.inputs["Geometry"])
    links.new(comb_offset.outputs[0], sp_final.inputs["Offset"])

    links.new(sp_final.outputs[0], go.inputs[0])
    return ng


# ── main: build sink + tap, assign materials, apply wear_tear ────────────────

def make_tap():
    tap_params = {
        "base_width": U(0.2, 0.3),
        "tap_head": U(0.7, 1.1),
        "roation_z": U(5.5, 7.0),
        "tap_height": U(0.5, 1),
        "base_radius": U(0.0, 0.1),
        "Switch": True if U() > 0.5 else False,
        "Y": U(-0.5, -0.06),
        "hand_type": True if U() > 0.2 else False,
        "hands_length_x": U(0.75, 1.25),
        "hands_length_Y": U(0.95, 1.55),
        "one_side": True if U() > 0.5 else False,
        "different_type": True if U() > 0.8 else False,
        "length_one_side": True if U() > 0.8 else False,
    }

    tap_ng = build_water_tap_nodegroup(tap_params)
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    tap = bpy.context.active_object
    mod = tap.modifiers.new("TapNodes", "NODES")
    mod.node_group = tap_ng
    select_only(tap)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    tap.scale = (0.4, 0.4, 0.4)
    tap.rotation_euler.z += math.pi
    apply_tf(tap, loc=True)
    return tap


def make_sink():
    np.random.seed(SEED)

    width = U(0.4, 1.0)
    depth_val = U(0.4, 0.5)
    upper_height = U(0.2, 0.4)

    sink_ng = build_sink_nodegroup({
        "Width": width,
        "Depth": depth_val,
        "Curvature": U(1.0, 1.0),
        "Upper Height": upper_height,
        "Lower Height": U(0.0, 0.01),
        "HoleRadius": U(0.02, 0.05),
        "Margin": U(0.02, 0.05),
        "WaterTapMargin": U(0.1, 0.12),
    })

    bpy.ops.mesh.primitive_plane_add(location=(0, 0, 0))
    sink_obj = bpy.context.active_object
    mod = sink_obj.modifiers.new("SinkNodes", "NODES")
    mod.node_group = sink_ng
    select_only(sink_obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)

    # Snapshot polygon count before tap is appended
    n_sink_polys = len(sink_obj.data.polygons)

    tap = make_tap()
    tap.location = (-depth_val / 2, 0, upper_height)
    apply_tf(tap, loc=True)

    # Join tap into sink
    select_only(sink_obj)
    tap.select_set(True)
    bpy.ops.object.join()
    sink_obj = bpy.context.active_object

    # --- Material assignment --------------------------------------------------
    # Draw sink surface material from metals registry
    MAT_SINK = get_metal_material(name="SinkSurface")
    # Draw tap material from metals registry (independent RNG draw)
    MAT_TAP = get_metal_material(name="SinkTap")

    sink_obj.data.materials.clear()
    sink_obj.data.materials.append(MAT_SINK)
    sink_obj.data.materials.append(MAT_TAP)

    # Assign: sink body polygons = slot 0, tap polygons = slot 1
    for i, p in enumerate(sink_obj.data.polygons):
        p.material_index = 1 if i >= n_sink_polys else 0

    # --- Wear & tear ----------------------------------------------------------
    _scratch_p, _edge_wear_p = WEAR_TEAR_PROB
    do_scratch = (np.random.uniform() <= _scratch_p)
    do_edge_wear = (np.random.uniform() <= _edge_wear_p)

    if do_scratch:
        apply_scratches(sink_obj)
    if do_edge_wear:
        apply_edge_wear(sink_obj)

    sink_obj.name = "Sink"
    return sink_obj


clear_scene()
make_sink()
