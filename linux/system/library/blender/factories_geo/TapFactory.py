# [FL_INDEX: keywords="blender_factory, procedural_3d, TapFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: TapFactory | Category: factories_geo
# Prompt: A 3D model of a kitchen faucet mounted on a flat rectangular base plate, rendered from a slightly elevated three-quarter perspective. The tap features a tall curved gooseneck spout made of a cylindrical tube that arcs downward at the top, a small lever handle near the base, and a flat elongated mounting plate beneath it.

"""
TapFactory — standalone Blender script with procedural metal shaders + wear_tear.

Geometry: copied from objects_blender/table_decorations/TapFactory.py
Shaders:  MetalBasic (3.0), BrushedMetal (2.0), GalvanizedMetal (1.0),
          GrainedMetal (1.0), HammeredMetal (0.7), BrushedBlackMetal (0.3)
"""
# SEED-deterministic: all random calls seeded from SEED

import os
import math
import hashlib
import random
import colorsys

import bpy
import numpy as np

# ── environment / seed ────────────────────────────────────────────────────��──

def int_hash(x):
    m = hashlib.md5()
    for s in x:
        m.update(str(s).encode("utf-8"))
    return abs(int(m.hexdigest(), 16)) % (2**32 - 1)

factory_seed = int(os.environ.get("SEED", "0"))
SEED = factory_seed
np.random.seed(SEED)
random.seed(SEED)
U = np.random.uniform

# ── basic helpers ───────────────────────────────────���────────────────────────

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

def weighted_sample(registry):
    classes, w = zip(*registry)
    w = np.array(w, dtype=float)
    return classes[int(np.random.choice(len(classes), p=w / w.sum()))]


# ── Blender scene helpers ──────────────────────────��─────────────────────────

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for c in list(bpy.data.curves):
        bpy.data.curves.remove(c)
    for ng in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(ng)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    bpy.context.scene.cursor.location = (0, 0, 0)


def select_only(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def apply_tf(obj, loc=False):
    select_only(obj)
    bpy.ops.object.transform_apply(location=loc, rotation=True, scale=True)


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


# ============================================================================
# Material library
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


def _noise_fac_output(noise_node):
    if "Fac" in noise_node.outputs:
        return noise_node.outputs["Fac"]
    if "Factor" in noise_node.outputs:
        return noise_node.outputs["Factor"]
    return noise_node.outputs[0]


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


def _connect_output(nt, bsdf, displacement=None):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    if displacement is not None:
        nt.links.new(displacement, out.inputs["Displacement"])
    return out


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


# ── 1. MetalBasic ──────────────────────���───────────────────────────────────���─

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


# ── 2. BrushedMetal ───────────────────────────���──────────────────────────────

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


# ── 3. GalvanizedMetal ──────────────────────────────��────────────────────────

def make_galvanized_metal(name="GalvanizedMetal", base_color_hsv=None, scale=1.0, seed=None):
    if seed is None:
        seed = float(np.random.uniform(-1000, 1000))
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # Noise for displacement of voronoi lookup
    mul_scale = _math(nt, "MULTIPLY", scale, 5.0)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise, "noise_dimensions"):
        try:
            noise.noise_dimensions = "4D"
        except TypeError:
            pass
    if "Detail" in noise.inputs:
        noise.inputs["Detail"].default_value = 15.0
    if "Roughness" in noise.inputs:
        noise.inputs["Roughness"].default_value = 0.4
    if "Distortion" in noise.inputs:
        noise.inputs["Distortion"].default_value = 0.2
    if "W" in noise.inputs:
        noise.inputs["W"].default_value = seed
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(mul_scale.outputs[0], noise.inputs["Scale"])

    # Mix object coords with noise color
    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
    mix.inputs[0].default_value = 0.05
    mix.clamp_factor = False
    nt.links.new(tex_coord.outputs["Object"], mix.inputs[6])
    nt.links.new(noise.outputs["Color"], mix.inputs[7])

    # Voronoi for galvanized crystallite pattern
    mul_scale2 = _math(nt, "MULTIPLY", scale, 500.0)
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
    if "W" in voronoi.inputs:
        voronoi.inputs["W"].default_value = seed
    nt.links.new(mix.outputs[2], voronoi.inputs["Vector"])
    nt.links.new(mul_scale2.outputs[0], voronoi.inputs["Scale"])

    # Map voronoi color to roughness
    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[3].default_value = 0.1
    map_range.inputs[4].default_value = 0.5
    vor_color = voronoi.outputs.get("Color") or voronoi.outputs[0]
    nt.links.new(vor_color, map_range.inputs[0])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf,
        Metallic=1.0,
        **{"Specular IOR Level": 0.0},
        **{"Base Color": hsv2rgba(base_color_hsv)},
    )
    nt.links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat


# ── 4. GrainedMetal ──────────────────────────────────────────────────────────

def make_grained_metal(name="GrainedMetal", base_color_hsv=None, scale=1.0,
                       roughness=None, seed=None):
    if roughness is None:
        roughness = float(np.random.uniform(0, 1))
    if seed is None:
        seed = float(np.random.uniform(-1000, 1000))
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree

    # MapRange: roughness → 0.05..0.25
    mr_rough = nt.nodes.new("ShaderNodeMapRange")
    mr_rough.inputs[0].default_value = roughness
    mr_rough.inputs[3].default_value = 0.05
    mr_rough.inputs[4].default_value = 0.25

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf,
        Metallic=1.0,
        **{"Specular IOR Level": 0.0},
        **{"Base Color": hsv2rgba(base_color_hsv)},
    )
    nt.links.new(mr_rough.outputs["Result"], bsdf.inputs["Roughness"])

    # Displacement from high-frequency noise
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mul_scale = _math(nt, "MULTIPLY", scale, 2000.0)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise, "noise_dimensions"):
        try:
            noise.noise_dimensions = "4D"
        except TypeError:
            pass
    if "Detail" in noise.inputs:
        noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs:
        noise.inputs["Distortion"].default_value = 2.0
    if "W" in noise.inputs:
        noise.inputs["W"].default_value = seed
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(mul_scale.outputs[0], noise.inputs["Scale"])

    mul_r = _math(nt, "MULTIPLY", mr_rough.outputs["Result"], 0.4)
    mul_disp = _math(nt, "MULTIPLY", _noise_fac_output(noise), mul_r.outputs[0])
    mul_final = _math(nt, "MULTIPLY", mul_disp.outputs[0], 0.01)

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_final.outputs[0], disp.inputs["Height"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


# ── 5. HammeredMetal ────────────────────────────────────────────────────────��

def make_hammered_metal(name="HammeredMetal", base_color_hsv=None, scale=None, seed=None):
    if seed is None:
        seed = float(np.random.uniform(-1000, 1000))
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    if scale is None:
        scale = log_uniform(0.8, 1.2)
    mat = _new_material(name)
    nt = mat.node_tree

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf,
        Metallic=1.0,
        **{"Specular IOR Level": 0.0},
        Roughness=0.1,
        **{"Base Color": hsv2rgba(base_color_hsv)},
    )

    # Noise for displacement seed
    mul_scale = _math(nt, "MULTIPLY", scale, 20.0)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise, "noise_dimensions"):
        try:
            noise.noise_dimensions = "4D"
        except TypeError:
            pass
    if "Detail" in noise.inputs:
        noise.inputs["Detail"].default_value = 15.0
    if "Roughness" in noise.inputs:
        noise.inputs["Roughness"].default_value = 0.4
    if "Distortion" in noise.inputs:
        noise.inputs["Distortion"].default_value = 0.2
    if "W" in noise.inputs:
        noise.inputs["W"].default_value = seed
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])
    nt.links.new(mul_scale.outputs[0], noise.inputs["Scale"])

    # Mix coords + noise
    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
    mix.inputs[0].default_value = 0.01
    mix.clamp_factor = False
    nt.links.new(tex_coord.outputs["Object"], mix.inputs[6])
    nt.links.new(noise.outputs["Color"], mix.inputs[7])

    # Voronoi smooth F1
    mul_scale2 = _math(nt, "MULTIPLY", scale, 300.0)
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
    if "Smoothness" in voronoi.inputs:
        voronoi.inputs["Smoothness"].default_value = 0.2
    if "W" in voronoi.inputs:
        voronoi.inputs["W"].default_value = seed
    nt.links.new(mix.outputs[2], voronoi.inputs["Vector"])
    nt.links.new(mul_scale2.outputs[0], voronoi.inputs["Scale"])

    # Displacement: distance * scale ^ 2.5 * coeff
    vor_dist = voronoi.outputs.get("Distance") or voronoi.outputs[0]
    mul_dist = _math(nt, "MULTIPLY", vor_dist, scale)
    power = _math(nt, "POWER", mul_dist.outputs[0], 2.5)
    disp_coeff = log_uniform(0.001, 0.003)
    mul_disp = _math(nt, "MULTIPLY", power.outputs[0], disp_coeff)

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_disp.outputs[0], disp.inputs["Height"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


# ── 6. BrushedBlackMetal ─────────────────────────────────────────────────────

def make_brushed_black_metal(name="BrushedBlackMetal"):
    """Uses AnisotropicBSDF if available, else PrincipledBSDF fallback."""

    mat = _new_material(name)
    nt = mat.node_tree
    # Try AnisotropicBSDF first
    try:
        bsdf = nt.nodes.new("ShaderNodeBsdfAnisotropic")
        bsdf.inputs["Color"].default_value = (0.0167, 0.0167, 0.0167, 1.0)
    except Exception:
        # Fallback: PrincipledBSDF in dark mode
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        _set_principled(
            bsdf,
            **{"Base Color": (0.0167, 0.0167, 0.0167, 1.0)},
            Metallic=1.0,
            Roughness=0.3,
            **{"Specular IOR Level": 0.5},
        )
    _connect_output(nt, bsdf)
    return mat


# ── Metal registry (mirrors material_assignments.metals) ─────────────────────

METALS_REGISTRY = [
    (make_metal_basic,        3.0),
    (make_brushed_metal,      2.0),
    (make_galvanized_metal,   1.0),
    (make_grained_metal,      1.0),
    (make_hammered_metal,     0.7),
    (make_brushed_black_metal, 0.3),
]


# ============================================================================
# Wear-and-tear: scratches + edge_wear
# ============================================================================

SCRATCH_LABEL = "scratch"
EDGE_WEAR_LABEL = "wear_tear"
WEAR_TEAR_PROB = [0.5, 0.5]

_find_node = lambda nt, bl: next((n for n in nt.nodes if n.bl_idname == bl), None)


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

    mul_a = _math(nt, "MULTIPLY", cr_a.outputs["Color"], cr_b.outputs["Color"], clamp=True)
    mul_a1 = _math(nt, "MULTIPLY", n_scratch_opacity.outputs[0], mul_a.outputs[0], clamp=True)

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
    mul_b1 = _math(nt, "MULTIPLY", n_worn_opacity.outputs[0], mul_b.outputs[0], clamp=True)
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
    mul_e = _math(nt, "MULTIPLY", cr_b.outputs["Color"], cr_e.outputs["Color"], clamp=True)
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
# Geometry — from objects_blender/table_decorations/TapFactory.py
# ============================================================================

def build_handle_nodegroup():
    """Create the 'nodegroup_handle' geometry node group."""

    ng = bpy.data.node_groups.new("nodegroup_handle", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    nodes = ng.nodes
    links = ng.links

    out = nodes.new("NodeGroupOutput")
    out.location = (1200, 0)

    bezier = nodes.new("GeometryNodeCurvePrimitiveBezierSegment")
    bezier.location = (0, 0)
    bezier.inputs["Start"].default_value = (0, 0, 0)
    bezier.inputs["Start Handle"].default_value = (0, 0, 0.7)
    bezier.inputs["End Handle"].default_value = (0.2, 0, 0.7)
    bezier.inputs["End"].default_value = (1, 0, 0.9)

    sparam = nodes.new("GeometryNodeSplineParameter")
    sparam.location = (0, -200)

    fcurve = nodes.new("ShaderNodeFloatCurve")
    fcurve.location = (200, -200)
    assign_float_curve(fcurve.mapping, [(0.0, 0.975), (1.0, 0.1625)])
    links.new(sparam.outputs["Factor"], fcurve.inputs["Value"])

    mul = nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.location = (400, -200)
    mul.inputs[1].default_value = 1.3
    links.new(fcurve.outputs[0], mul.inputs[0])

    scr = nodes.new("GeometryNodeSetCurveRadius")
    scr.location = (400, 0)
    links.new(bezier.outputs[0], scr.inputs["Curve"])
    links.new(mul.outputs[0], scr.inputs["Radius"])

    cc = nodes.new("GeometryNodeCurvePrimitiveCircle")
    cc.location = (400, -400)
    cc.inputs["Radius"].default_value = 0.2
    cc.mode = "RADIUS"

    ctm = nodes.new("GeometryNodeCurveToMesh")
    ctm.location = (600, 0)
    links.new(scr.outputs[0], ctm.inputs["Curve"])
    links.new(cc.outputs["Curve"], ctm.inputs["Profile Curve"])
    ctm.inputs["Fill Caps"].default_value = True

    pos = nodes.new("GeometryNodeInputPosition")
    pos.location = (400, -600)
    sep = nodes.new("ShaderNodeSeparateXYZ")
    sep.location = (600, -600)
    links.new(pos.outputs[0], sep.inputs[0])

    mr = nodes.new("ShaderNodeMapRange")
    mr.location = (800, -600)
    mr.inputs["From Min"].default_value = 0.2
    mr.inputs["From Max"].default_value = 1.0
    mr.inputs["To Min"].default_value = 1.0
    mr.inputs["To Max"].default_value = 2.5
    links.new(sep.outputs["X"], mr.inputs["Value"])

    mul2 = nodes.new("ShaderNodeMath")
    mul2.operation = "MULTIPLY"
    mul2.location = (1000, -600)
    links.new(sep.outputs["Y"], mul2.inputs[0])
    links.new(mr.outputs["Result"], mul2.inputs[1])

    comb = nodes.new("ShaderNodeCombineXYZ")
    comb.location = (1000, -400)
    links.new(sep.outputs["X"], comb.inputs["X"])
    links.new(mul2.outputs[0], comb.inputs["Y"])
    links.new(sep.outputs["Z"], comb.inputs["Z"])

    sp = nodes.new("GeometryNodeSetPosition")
    sp.location = (800, 0)
    links.new(ctm.outputs[0], sp.inputs["Geometry"])
    links.new(comb.outputs[0], sp.inputs["Position"])

    subdiv = nodes.new("GeometryNodeSubdivisionSurface")
    subdiv.location = (1000, 0)
    subdiv.inputs["Level"].default_value = 2
    links.new(sp.outputs[0], subdiv.inputs["Mesh"])

    sss = nodes.new("GeometryNodeSetShadeSmooth")
    sss.location = (1100, 0)
    links.new(subdiv.outputs[0], sss.inputs["Geometry"])

    links.new(sss.outputs[0], out.inputs[0])

    return ng


def build_water_tap_nodegroup(params):
    """Create the water tap geometry node group."""

    ng = bpy.data.node_groups.new("nodegroup_water_tap", "GeometryNodeTree")

    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    nodes = ng.nodes
    links = ng.links

    gi = nodes.new("NodeGroupInput")
    gi.location = (-600, 0)
    go = nodes.new("NodeGroupOutput")
    go.location = (3000, 0)

    # ── Vertical stem: CurveLine → CurveToMesh ──
    stem_line = nodes.new("GeometryNodeCurvePrimitiveLine")
    stem_line.location = (0, 400)
    stem_line.inputs["End"].default_value = (0, 0, 0.6)

    stem_profile = nodes.new("GeometryNodeCurvePrimitiveCircle")
    stem_profile.location = (0, 200)
    stem_profile.inputs["Radius"].default_value = 0.03
    stem_profile.mode = "RADIUS"

    stem_mesh = nodes.new("GeometryNodeCurveToMesh")
    stem_mesh.location = (200, 400)
    links.new(stem_line.outputs[0], stem_mesh.inputs["Curve"])
    links.new(stem_profile.outputs["Curve"], stem_mesh.inputs["Profile Curve"])

    # ── Spout option A (ring): CurveCircle(R=0.2) ──
    spout_circle = nodes.new("GeometryNodeCurvePrimitiveCircle")
    spout_circle.location = (0, -200)
    spout_circle.inputs["Radius"].default_value = 0.2
    spout_circle.mode = "RADIUS"

    spout_tf1 = nodes.new("GeometryNodeTransform")
    spout_tf1.location = (200, -200)
    spout_tf1.inputs["Translation"].default_value = (0, 0.2, 0)
    links.new(spout_circle.outputs["Curve"], spout_tf1.inputs["Geometry"])

    spout_tf2 = nodes.new("GeometryNodeTransform")
    spout_tf2.location = (400, -200)
    spout_tf2.inputs["Rotation"].default_value = (-1.5708, 1.5708, 0)
    spout_tf2.inputs["Scale"].default_value = (1, 0.7, 1)
    links.new(spout_tf1.outputs[0], spout_tf2.inputs["Geometry"])

    # ── Spout option B (bezier): BezierSegment → TrimCurve ──
    Y_val = params["Y"]
    comb_endhandle = nodes.new("ShaderNodeCombineXYZ")
    comb_endhandle.location = (0, -600)
    comb_endhandle.inputs["X"].default_value = 0.2
    comb_endhandle.inputs["Y"].default_value = Y_val

    bezier_spout = nodes.new("GeometryNodeCurvePrimitiveBezierSegment")
    bezier_spout.location = (200, -500)
    bezier_spout.inputs["Resolution"].default_value = 177
    bezier_spout.inputs["Start"].default_value = (0, 0, 0)
    bezier_spout.inputs["Start Handle"].default_value = (0, 1.2, 0)
    links.new(comb_endhandle.outputs[0], bezier_spout.inputs["End Handle"])
    bezier_spout.inputs["End"].default_value = (-0.05, 0.1, 0)

    trim = nodes.new("GeometryNodeTrimCurve")
    trim.location = (400, -500)
    links.new(bezier_spout.outputs[0], trim.inputs["Curve"])
    trim.inputs[3].default_value = 0.6625
    trim.inputs[5].default_value = 3.0

    spout_tf3 = nodes.new("GeometryNodeTransform")
    spout_tf3.location = (600, -500)
    spout_tf3.inputs["Rotation"].default_value = (1.5708, 0, 2.522)
    spout_tf3.inputs["Scale"].default_value = (5.2, 0.5, 7.8)
    links.new(trim.outputs[0], spout_tf3.inputs["Geometry"])

    spout_profile = nodes.new("GeometryNodeCurvePrimitiveCircle")
    spout_profile.location = (600, -700)
    spout_profile.inputs["Radius"].default_value = 0.03
    spout_profile.mode = "RADIUS"

    spout_b_mesh = nodes.new("GeometryNodeCurveToMesh")
    spout_b_mesh.location = (800, -500)
    links.new(spout_tf3.outputs[0], spout_b_mesh.inputs["Curve"])
    links.new(spout_profile.outputs["Curve"], spout_b_mesh.inputs["Profile Curve"])

    # ── Switch between spout A and B ──
    switch_spout_curve = nodes.new("GeometryNodeSwitch")
    switch_spout_curve.location = (800, -200)
    switch_spout_curve.input_type = "GEOMETRY"
    switch_spout_curve.inputs[0].default_value = params["Switch"]
    links.new(spout_tf2.outputs[0], switch_spout_curve.inputs[1])
    links.new(spout_b_mesh.outputs[0], switch_spout_curve.inputs[2])

    # CurveToMesh for the switched spout
    spout_final_mesh = nodes.new("GeometryNodeCurveToMesh")
    spout_final_mesh.location = (1000, -200)
    links.new(switch_spout_curve.outputs[0], spout_final_mesh.inputs["Curve"])
    links.new(stem_profile.outputs["Curve"], spout_final_mesh.inputs["Profile Curve"])

    # ── Filter spout: Position.Z > -0.01 when Switch is ring ──
    pos1 = nodes.new("GeometryNodeInputPosition")
    pos1.location = (800, -400)
    sep1 = nodes.new("ShaderNodeSeparateXYZ")
    sep1.location = (1000, -400)
    links.new(pos1.outputs[0], sep1.inputs[0])

    gt = nodes.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    gt.location = (1200, -400)
    links.new(sep1.outputs["Z"], gt.inputs[0])
    gt.inputs[1].default_value = -0.01

    switch_sel = nodes.new("GeometryNodeSwitch")
    switch_sel.location = (1200, -200)
    switch_sel.input_type = "FLOAT"
    switch_sel.inputs[0].default_value = params["Switch"]
    links.new(gt.outputs[0], switch_sel.inputs[1])
    switch_sel.inputs[2].default_value = 1.0

    sep_geo = nodes.new("GeometryNodeSeparateGeometry")
    sep_geo.location = (1400, -200)
    links.new(spout_final_mesh.outputs[0], sep_geo.inputs["Geometry"])
    links.new(switch_sel.outputs[0], sep_geo.inputs["Selection"])

    # ── Scale spout by tap_head (Z) ──
    comb_taphead = nodes.new("ShaderNodeCombineXYZ")
    comb_taphead.location = (1200, -600)
    comb_taphead.inputs["X"].default_value = 1.0
    comb_taphead.inputs["Y"].default_value = 1.0
    comb_taphead.inputs["Z"].default_value = params["tap_head"]

    switch_taphead = nodes.new("GeometryNodeSwitch")
    switch_taphead.location = (1400, -600)
    switch_taphead.input_type = "VECTOR"
    switch_taphead.inputs[0].default_value = params["Switch"]
    links.new(comb_taphead.outputs[0], switch_taphead.inputs[1])
    switch_taphead.inputs[2].default_value = (1, 1, 1)

    spout_positioned = nodes.new("GeometryNodeTransform")
    spout_positioned.location = (1600, -200)
    spout_positioned.inputs["Translation"].default_value = (0, 0, 0.6)
    links.new(sep_geo.outputs["Selection"], spout_positioned.inputs["Geometry"])
    links.new(switch_taphead.outputs[0], spout_positioned.inputs["Scale"])

    # Join stem + spout
    join_stem_spout = nodes.new("GeometryNodeJoinGeometry")
    join_stem_spout.location = (1800, 200)
    links.new(stem_mesh.outputs[0], join_stem_spout.inputs["Geometry"])
    links.new(spout_positioned.outputs[0], join_stem_spout.inputs["Geometry"])

    # ── Rotation + height scaling ──
    comb_rot = nodes.new("ShaderNodeCombineXYZ")
    comb_rot.location = (1800, -100)
    comb_rot.inputs["Z"].default_value = params["roation_z"]

    comb_height = nodes.new("ShaderNodeCombineXYZ")
    comb_height.location = (1800, -300)
    comb_height.inputs["X"].default_value = 1.0
    comb_height.inputs["Y"].default_value = 1.0
    comb_height.inputs["Z"].default_value = params["tap_height"]

    tf_body = nodes.new("GeometryNodeTransform")
    tf_body.location = (2000, 200)
    links.new(join_stem_spout.outputs[0], tf_body.inputs["Geometry"])
    links.new(comb_rot.outputs[0], tf_body.inputs["Rotation"])
    links.new(comb_height.outputs[0], tf_body.inputs["Scale"])

    # ── Handle type A: nodegroup_handle (bezier handles) ──
    handle_ng = build_handle_nodegroup()
    handle_inst_1 = nodes.new("GeometryNodeGroup")
    handle_inst_1.node_tree = handle_ng
    handle_inst_1.location = (1400, 600)

    handle_tf1 = nodes.new("GeometryNodeTransform")
    handle_tf1.location = (1600, 700)
    handle_tf1.inputs["Translation"].default_value = (0, -0.2, 0)
    handle_tf1.inputs["Rotation"].default_value = (0, 0, 3.6652)
    handle_tf1.inputs["Scale"].default_value = (0.3, 0.3, 0.3)
    links.new(handle_inst_1.outputs[0], handle_tf1.inputs["Geometry"])

    handle_inst_2 = nodes.new("GeometryNodeGroup")
    handle_inst_2.node_tree = handle_ng
    handle_inst_2.location = (1400, 400)

    handle_tf2 = nodes.new("GeometryNodeTransform")
    handle_tf2.location = (1600, 500)
    handle_tf2.inputs["Translation"].default_value = (0, 0.2, 0)
    handle_tf2.inputs["Rotation"].default_value = (0, 0, 2.618)
    handle_tf2.inputs["Scale"].default_value = (0.3, 0.3, 0.3)
    links.new(handle_inst_2.outputs[0], handle_tf2.inputs["Geometry"])

    join_handles_a = nodes.new("GeometryNodeJoinGeometry")
    join_handles_a.location = (1800, 600)
    links.new(handle_tf1.outputs[0], join_handles_a.inputs["Geometry"])
    links.new(handle_tf2.outputs[0], join_handles_a.inputs["Geometry"])

    # ── Handle type B: Cylinders as knobs ──
    cyl1 = nodes.new("GeometryNodeMeshCylinder")
    cyl1.location = (1000, 800)
    cyl1.inputs["Vertices"].default_value = 41
    cyl1.inputs["Side Segments"].default_value = 39
    cyl1.inputs["Radius"].default_value = 0.03
    cyl1.inputs["Depth"].default_value = 0.1

    cyl1_tf_r = nodes.new("GeometryNodeTransform")
    cyl1_tf_r.location = (1200, 900)
    cyl1_tf_r.inputs["Translation"].default_value = (0, 0.05, 0.1)
    cyl1_tf_r.inputs["Rotation"].default_value = (1.5708, 0, 0)
    links.new(cyl1.outputs["Mesh"], cyl1_tf_r.inputs["Geometry"])

    switch_one_side_r = nodes.new("GeometryNodeSwitch")
    switch_one_side_r.location = (1400, 900)
    switch_one_side_r.input_type = "GEOMETRY"
    switch_one_side_r.inputs[0].default_value = params["one_side"]
    links.new(cyl1_tf_r.outputs[0], switch_one_side_r.inputs[1])

    cyl1_tf_l = nodes.new("GeometryNodeTransform")
    cyl1_tf_l.location = (1200, 700)
    cyl1_tf_l.inputs["Translation"].default_value = (0, -0.05, 0.1)
    cyl1_tf_l.inputs["Rotation"].default_value = (1.5708, 0, 0)
    links.new(cyl1.outputs["Mesh"], cyl1_tf_l.inputs["Geometry"])

    join_big_cyl = nodes.new("GeometryNodeJoinGeometry")
    join_big_cyl.location = (1600, 850)
    links.new(switch_one_side_r.outputs[0], join_big_cyl.inputs["Geometry"])
    links.new(cyl1_tf_l.outputs[0], join_big_cyl.inputs["Geometry"])

    # Thin cylinders (valve stems)
    cyl2 = nodes.new("GeometryNodeMeshCylinder")
    cyl2.location = (1000, 1200)
    cyl2.inputs["Vertices"].default_value = 41
    cyl2.inputs["Side Segments"].default_value = 39
    cyl2.inputs["Radius"].default_value = 0.005
    cyl2.inputs["Depth"].default_value = 0.1

    cyl2_tf_r = nodes.new("GeometryNodeTransform")
    cyl2_tf_r.location = (1200, 1300)
    cyl2_tf_r.inputs["Translation"].default_value = (0, 0.08, 0.15)
    cyl2_tf_r.inputs["Scale"].default_value = (1, 1, 1.1)
    links.new(cyl2.outputs["Mesh"], cyl2_tf_r.inputs["Geometry"])

    switch_one_side_r2 = nodes.new("GeometryNodeSwitch")
    switch_one_side_r2.location = (1400, 1300)
    switch_one_side_r2.input_type = "GEOMETRY"
    switch_one_side_r2.inputs[0].default_value = params["one_side"]
    links.new(cyl2_tf_r.outputs[0], switch_one_side_r2.inputs[1])

    cyl2_tf_l = nodes.new("GeometryNodeTransform")
    cyl2_tf_l.location = (1200, 1100)
    cyl2_tf_l.inputs["Translation"].default_value = (0, -0.08, 0.15)
    cyl2_tf_l.inputs["Rotation"].default_value = (0, 0, 0.0855)
    cyl2_tf_l.inputs["Scale"].default_value = (1, 1, 1.1)
    links.new(cyl2.outputs["Mesh"], cyl2_tf_l.inputs["Geometry"])

    cyl2_tf_l_long = nodes.new("GeometryNodeTransform")
    cyl2_tf_l_long.location = (1400, 1100)
    cyl2_tf_l_long.inputs["Translation"].default_value = (0, -0.01, -0.005)
    cyl2_tf_l_long.inputs["Scale"].default_value = (4.1, 1, 1)
    links.new(cyl2_tf_l.outputs[0], cyl2_tf_l_long.inputs["Geometry"])

    length_one_side = params.get("length_one_side", np.random.uniform() < 0.2)
    switch_len = nodes.new("GeometryNodeSwitch")
    switch_len.location = (1600, 1100)
    switch_len.input_type = "GEOMETRY"
    switch_len.inputs[0].default_value = length_one_side
    links.new(cyl2_tf_l.outputs[0], switch_len.inputs[1])
    links.new(cyl2_tf_l_long.outputs[0], switch_len.inputs[2])

    switch_one_l2 = nodes.new("GeometryNodeSwitch")
    switch_one_l2.location = (1800, 1100)
    switch_one_l2.input_type = "GEOMETRY"
    switch_one_l2.inputs[0].default_value = params["one_side"]
    links.new(cyl2_tf_l.outputs[0], switch_one_l2.inputs[1])
    links.new(switch_len.outputs[0], switch_one_l2.inputs[2])

    join_thin_cyl = nodes.new("GeometryNodeJoinGeometry")
    join_thin_cyl.location = (2000, 1200)
    links.new(switch_one_side_r2.outputs[0], join_thin_cyl.inputs["Geometry"])
    links.new(switch_one_l2.outputs[0], join_thin_cyl.inputs["Geometry"])

    join_all_b_cyls = nodes.new("GeometryNodeJoinGeometry")
    join_all_b_cyls.location = (2200, 1000)
    links.new(join_big_cyl.outputs[0], join_all_b_cyls.inputs["Geometry"])
    links.new(join_thin_cyl.outputs[0], join_all_b_cyls.inputs["Geometry"])

    comb_hands = nodes.new("ShaderNodeCombineXYZ")
    comb_hands.location = (2200, 800)
    comb_hands.inputs["X"].default_value = params["hands_length_x"]
    comb_hands.inputs["Y"].default_value = params["hands_length_Y"]
    comb_hands.inputs["Z"].default_value = 1.0

    tf_hands = nodes.new("GeometryNodeTransform")
    tf_hands.location = (2400, 1000)
    links.new(join_all_b_cyls.outputs[0], tf_hands.inputs["Geometry"])
    links.new(comb_hands.outputs[0], tf_hands.inputs["Scale"])

    # ── Switch between handle types ──
    switch_hand = nodes.new("GeometryNodeSwitch")
    switch_hand.location = (2200, 600)
    switch_hand.input_type = "GEOMETRY"
    switch_hand.inputs[0].default_value = params["hand_type"]
    links.new(join_handles_a.outputs[0], switch_hand.inputs[1])
    links.new(tf_hands.outputs[0], switch_hand.inputs[2])

    # ── Base plate (circle extrude) ──
    base_circle = nodes.new("GeometryNodeCurvePrimitiveCircle")
    base_circle.location = (2000, -400)
    base_circle.inputs["Radius"].default_value = 0.05
    base_circle.mode = "RADIUS"

    base_fill = nodes.new("GeometryNodeFillCurve")
    base_fill.location = (2200, -400)
    links.new(base_circle.outputs["Curve"], base_fill.inputs["Curve"])

    base_extrude = nodes.new("GeometryNodeExtrudeMesh")
    base_extrude.location = (2400, -400)
    base_extrude.inputs["Offset Scale"].default_value = 0.15
    links.new(base_fill.outputs[0], base_extrude.inputs["Mesh"])

    # ── Join body + handles + base (standard type) ──
    join_standard = nodes.new("GeometryNodeJoinGeometry")
    join_standard.location = (2600, 200)
    links.new(tf_body.outputs[0], join_standard.inputs["Geometry"])
    links.new(switch_hand.outputs[0], join_standard.inputs["Geometry"])
    links.new(base_extrude.outputs["Mesh"], join_standard.inputs["Geometry"])

    # ── Alternative body style (different_type) ──
    alt_bezier = nodes.new("GeometryNodeCurvePrimitiveBezierSegment")
    alt_bezier.location = (1000, -1000)
    alt_bezier.inputs["Resolution"].default_value = 54
    alt_bezier.inputs["Start"].default_value = (0, 0, 0)
    alt_bezier.inputs["Start Handle"].default_value = (0, 0, 0.7)
    alt_bezier.inputs["End Handle"].default_value = (0.2, 0, 0.7)
    alt_bezier.inputs["End"].default_value = (1, 0, 0.9)

    alt_sparam = nodes.new("GeometryNodeSplineParameter")
    alt_sparam.location = (1000, -1200)

    alt_fcurve = nodes.new("ShaderNodeFloatCurve")
    alt_fcurve.location = (1200, -1200)
    assign_float_curve(alt_fcurve.mapping, [(0.0, 0.975), (0.6295, 0.4125), (1.0, 0.1625)])
    links.new(alt_sparam.outputs["Factor"], alt_fcurve.inputs["Value"])

    alt_mul = nodes.new("ShaderNodeMath")
    alt_mul.operation = "MULTIPLY"
    alt_mul.location = (1400, -1200)
    alt_mul.inputs[1].default_value = 1.3
    links.new(alt_fcurve.outputs[0], alt_mul.inputs[0])

    alt_scr = nodes.new("GeometryNodeSetCurveRadius")
    alt_scr.location = (1400, -1000)
    links.new(alt_bezier.outputs[0], alt_scr.inputs["Curve"])
    links.new(alt_mul.outputs[0], alt_scr.inputs["Radius"])

    alt_profile = nodes.new("GeometryNodeCurvePrimitiveCircle")
    alt_profile.location = (1400, -1400)
    alt_profile.inputs["Radius"].default_value = 0.1
    alt_profile.mode = "RADIUS"

    alt_ctm = nodes.new("GeometryNodeCurveToMesh")
    alt_ctm.location = (1600, -1000)
    links.new(alt_scr.outputs[0], alt_ctm.inputs["Curve"])
    links.new(alt_profile.outputs["Curve"], alt_ctm.inputs["Profile Curve"])
    alt_ctm.inputs["Fill Caps"].default_value = True

    alt_pos = nodes.new("GeometryNodeInputPosition")
    alt_pos.location = (1400, -1600)
    alt_sep = nodes.new("ShaderNodeSeparateXYZ")
    alt_sep.location = (1600, -1600)
    links.new(alt_pos.outputs[0], alt_sep.inputs[0])

    alt_mr = nodes.new("ShaderNodeMapRange")
    alt_mr.location = (1800, -1600)
    alt_mr.inputs["From Min"].default_value = 0.2
    alt_mr.inputs["From Max"].default_value = 1.0
    alt_mr.inputs["To Min"].default_value = 1.0
    alt_mr.inputs["To Max"].default_value = 2.5
    links.new(alt_sep.outputs["X"], alt_mr.inputs["Value"])

    alt_mul2 = nodes.new("ShaderNodeMath")
    alt_mul2.operation = "MULTIPLY"
    alt_mul2.location = (2000, -1600)
    links.new(alt_sep.outputs["Y"], alt_mul2.inputs[0])
    links.new(alt_mr.outputs["Result"], alt_mul2.inputs[1])

    alt_comb = nodes.new("ShaderNodeCombineXYZ")
    alt_comb.location = (2000, -1400)
    links.new(alt_sep.outputs["X"], alt_comb.inputs["X"])
    links.new(alt_mul2.outputs[0], alt_comb.inputs["Y"])
    links.new(alt_sep.outputs["Z"], alt_comb.inputs["Z"])

    alt_sp = nodes.new("GeometryNodeSetPosition")
    alt_sp.location = (1800, -1000)
    links.new(alt_ctm.outputs[0], alt_sp.inputs["Geometry"])
    links.new(alt_comb.outputs[0], alt_sp.inputs["Position"])

    alt_subdiv = nodes.new("GeometryNodeSubdivisionSurface")
    alt_subdiv.location = (2000, -1000)
    alt_subdiv.inputs["Level"].default_value = 1
    links.new(alt_sp.outputs[0], alt_subdiv.inputs["Mesh"])

    alt_sss = nodes.new("GeometryNodeSetShadeSmooth")
    alt_sss.location = (2200, -1000)
    links.new(alt_subdiv.outputs[0], alt_sss.inputs["Geometry"])

    alt_body_tf = nodes.new("GeometryNodeTransform")
    alt_body_tf.location = (2400, -1000)
    alt_body_tf.inputs["Translation"].default_value = (0, 0, 0.1)
    alt_body_tf.inputs["Rotation"].default_value = (0, 0, 0.6807)
    alt_body_tf.inputs["Scale"].default_value = (0.4, 0.4, 0.3)
    links.new(alt_sss.outputs[0], alt_body_tf.inputs["Geometry"])

    alt_base_circle = nodes.new("GeometryNodeCurvePrimitiveCircle")
    alt_base_circle.location = (2200, -1200)
    alt_base_circle.inputs["Resolution"].default_value = 307
    alt_base_circle.inputs["Radius"].default_value = 0.055
    alt_base_circle.mode = "RADIUS"

    alt_base_fill = nodes.new("GeometryNodeFillCurve")
    alt_base_fill.location = (2400, -1200)
    links.new(alt_base_circle.outputs["Curve"], alt_base_fill.inputs["Curve"])

    alt_base_extr = nodes.new("GeometryNodeExtrudeMesh")
    alt_base_extr.location = (2600, -1200)
    alt_base_extr.inputs["Offset Scale"].default_value = 0.15
    links.new(alt_base_fill.outputs[0], alt_base_extr.inputs["Mesh"])

    alt_arm_cyl = nodes.new("GeometryNodeMeshCylinder")
    alt_arm_cyl.location = (2000, -1400)
    alt_arm_cyl.inputs["Vertices"].default_value = 100
    alt_arm_cyl.inputs["Radius"].default_value = 0.01
    alt_arm_cyl.inputs["Depth"].default_value = 0.7

    alt_arm_sp = nodes.new("GeometryNodeSetPosition")
    alt_arm_sp.location = (2200, -1400)
    links.new(alt_arm_cyl.outputs["Mesh"], alt_arm_sp.inputs["Geometry"])

    alt_arm_tf = nodes.new("GeometryNodeTransform")
    alt_arm_tf.location = (2400, -1400)
    alt_arm_tf.inputs["Translation"].default_value = (0.3, 0, 0.25)
    alt_arm_tf.inputs["Rotation"].default_value = (0, -2.042, 0)
    alt_arm_tf.inputs["Scale"].default_value = (1.7, 3.1, 1)
    links.new(alt_arm_sp.outputs[0], alt_arm_tf.inputs["Geometry"])

    alt_knob_cyl = nodes.new("GeometryNodeMeshCylinder")
    alt_knob_cyl.location = (2000, -1600)
    alt_knob_cyl.inputs["Vertices"].default_value = 318
    alt_knob_cyl.inputs["Radius"].default_value = 0.02
    alt_knob_cyl.inputs["Depth"].default_value = 0.03

    alt_knob_tf = nodes.new("GeometryNodeTransform")
    alt_knob_tf.location = (2400, -1600)
    alt_knob_tf.inputs["Translation"].default_value = (0.595, 0, 0.38)
    links.new(alt_knob_cyl.outputs["Mesh"], alt_knob_tf.inputs["Geometry"])

    alt_arm_join = nodes.new("GeometryNodeJoinGeometry")
    alt_arm_join.location = (2600, -1400)
    links.new(alt_arm_tf.outputs[0], alt_arm_join.inputs["Geometry"])
    links.new(alt_knob_tf.outputs[0], alt_arm_join.inputs["Geometry"])

    alt_arm_scale = nodes.new("GeometryNodeTransform")
    alt_arm_scale.location = (2800, -1400)
    alt_arm_scale.inputs["Scale"].default_value = (0.9, 1, 1)
    links.new(alt_arm_join.outputs[0], alt_arm_scale.inputs["Geometry"])

    alt_join = nodes.new("GeometryNodeJoinGeometry")
    alt_join.location = (2800, -1000)
    links.new(alt_body_tf.outputs[0], alt_join.inputs["Geometry"])
    links.new(alt_base_extr.outputs["Mesh"], alt_join.inputs["Geometry"])
    links.new(alt_arm_scale.outputs[0], alt_join.inputs["Geometry"])

    alt_rot = nodes.new("GeometryNodeTransform")
    alt_rot.location = (3000, -1000)
    alt_rot.inputs["Rotation"].default_value = (0, 0, 3.1416)
    links.new(alt_join.outputs[0], alt_rot.inputs["Geometry"])

    # ── Switch between standard and alt ──
    switch_type = nodes.new("GeometryNodeSwitch")
    switch_type.location = (2800, 200)
    switch_type.input_type = "GEOMETRY"
    switch_type.inputs[0].default_value = params["different_type"]
    links.new(join_standard.outputs[0], switch_type.inputs[1])
    links.new(alt_rot.outputs[0], switch_type.inputs[2])

    # ── Base plate (Quadrilateral + FilletCurve) ──
    quad_base = nodes.new("GeometryNodeCurvePrimitiveQuadrilateral")
    quad_base.location = (2400, -100)
    quad_base.inputs["Width"].default_value = params["base_width"]
    quad_base.inputs["Height"].default_value = 0.7

    fillet_base = nodes.new("GeometryNodeFilletCurve")
    fillet_base.location = (2600, -100)
    fillet_base.inputs["Count"].default_value = 19
    fillet_base.inputs["Radius"].default_value = params["base_radius"]
    links.new(quad_base.outputs[0], fillet_base.inputs["Curve"])
    set_fillet_mode(fillet_base, "POLY")

    fill_base = nodes.new("GeometryNodeFillCurve")
    fill_base.location = (2800, -100)
    links.new(fillet_base.outputs[0], fill_base.inputs["Curve"])

    extrude_base = nodes.new("GeometryNodeExtrudeMesh")
    extrude_base.location = (3000, -100)
    extrude_base.inputs["Offset Scale"].default_value = 0.05
    links.new(fill_base.outputs[0], extrude_base.inputs["Mesh"])

    # ── Final join ──
    final_join = nodes.new("GeometryNodeJoinGeometry")
    final_join.location = (3200, 0)
    links.new(switch_type.outputs[0], final_join.inputs["Geometry"])
    links.new(extrude_base.outputs["Mesh"], final_join.inputs["Geometry"])

    links.new(final_join.outputs[0], go.inputs[0])

    return ng


# ============================================================================
# Main — create tap with material
# ============================================================================

def make_tap(seed=None):
    """Create a tap object with material assigned."""

    if seed is not None:
        np.random.seed(seed)

    params = {
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

    ng = build_water_tap_nodegroup(params)

    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    obj = bpy.context.active_object

    mod = obj.modifiers.new("TapNodes", "NODES")
    mod.node_group = ng
    select_only(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)

    obj.scale = (0.4, 0.4, 0.4)
    obj.rotation_euler.z += math.pi
    apply_tf(obj, loc=True)

    # ── Assign metal material ──
    make_fn = weighted_sample(METALS_REGISTRY)
    mat = make_fn(name="TapMetal")
    obj.data.materials.clear()
    obj.data.materials.append(mat)

    scratch_prob, edge_wear_prob = WEAR_TEAR_PROB
    do_scratch = (np.random.uniform() <= scratch_prob)
    do_edge_wear = (np.random.uniform() <= edge_wear_prob)
    if do_scratch:
        apply_scratches(obj)
    if do_edge_wear:
        apply_edge_wear(obj)

    obj.name = "Tap"
    return obj


clear_scene()
make_tap()
