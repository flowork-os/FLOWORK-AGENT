# [FL_INDEX: keywords="blender_factory, procedural_3d, SpatulaOnHookBaseFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: SpatulaOnHookBaseFactory | Category: factories_geo
# Prompt: A 3D model of spatulas hanging on a wall-mounted hook rack, rendered from a three-quarter perspective, featuring a rectangular backplate panel with a dark frame border and multiple curved hooks along the bottom from which kitchen spatulas are suspended.

# SpatulaOnHookBaseFactory — standalone Blender script (hook metal + board + spatula plastic).
# Dual-seed: SEED for material, int_hash((SEED,0)) for geometry. No wear_tear.
import os
import math
import random
import colorsys
import hashlib
from types import SimpleNamespace

import bpy
import numpy as np
from numpy.random import uniform, randint

C = bpy.context
D = bpy.data

# ============================================================================
# ============================================================================
def seed_all(seed: int):
    np.random.seed(seed)
    random.seed(seed)


def hsv2rgba(hsv):
    h, s, v = hsv
    h = h - math.floor(h)
    s = max(0.0, min(1.0, float(s)))
    v = max(0.0, min(1.0, float(v)))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)


def log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))


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


def _new_material(name: str) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat


def _set_principled(bsdf, **kw):
    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Specular":           ("Specular IOR Level", "Specular"),
        "Coat Weight":        ("Coat Weight", "Clearcoat"),
    }
    for k, v in kw.items():
        names = aliases.get(k, (k,))
        for name in names:
            if name in bsdf.inputs:
                bsdf.inputs[name].default_value = v
                break


def _noise_fac_output(noise_node):
    return noise_node.outputs.get("Fac") or noise_node.outputs.get("Factor") or noise_node.outputs[0]


def _connect_output(nt, bsdf, displacement=None):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    if displacement is not None:
        nt.links.new(displacement, out.inputs["Displacement"])


def make_brushed_metal(name="BrushedMetal", base_color_hsv=None) -> bpy.types.Material:
    """

    The original is a nodegroup: TexCoord -> Mapping(0.2,0.2,5) -> NoiseTex_2
    (scale=scale*100, detail=15, rough=0.4, dist=0.1, 4D); another TexCoord mapping
    feeds NoiseTex_1 (scale=0.1, detail=15, rough=0, 4D); those are mixed with
    Mix(RGBA, fac=0.2); the result feeds NoiseTex (scale*100, detail=15, rough=0.6,
    dist=0.1, 4D); NoiseTex_2 and NoiseTex are DARKEN-mixed; result goes into
    MapRange(0.4-0.6 -> 0.8-1.2) -> HueSat on base color -> Principled
    (metallic=1, specular=0, roughness from a second MapRange 0.4-0.6 -> 0.2-0.3).
    This function reproduces the full chain node-for-node.
    """

    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree

    # Seed (shared W input for all 4D noises, matches shader_brushed_metal's seed arg)
    w_seed = float(np.random.uniform(-1000.0, 1000.0))
    # Scale multiplier replicates Math MULTIPLY(scale, 100)
    scale_mul = 100.0

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # --- mapping_1 : (0.2, 0.2, 5) for noise_texture_2 ---
    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    mapping_1.inputs["Scale"].default_value = (0.2, 0.2, 5.0)
    nt.links.new(tex_coord.outputs["Object"], mapping_1.inputs["Vector"])

    noise_texture_2 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise_texture_2, "noise_dimensions"):
        try: noise_texture_2.noise_dimensions = "4D"
        except TypeError: pass
    noise_texture_2.inputs["Scale"].default_value = scale_mul
    if "Detail" in noise_texture_2.inputs:     noise_texture_2.inputs["Detail"].default_value = 15.0
    if "Roughness" in noise_texture_2.inputs:  noise_texture_2.inputs["Roughness"].default_value = 0.4
    if "Distortion" in noise_texture_2.inputs: noise_texture_2.inputs["Distortion"].default_value = 0.1
    if "W" in noise_texture_2.inputs:          noise_texture_2.inputs["W"].default_value = w_seed
    nt.links.new(mapping_1.outputs["Vector"], noise_texture_2.inputs["Vector"])

    # --- mapping : (1, 1, 20) (unused mapping in source but kept for fidelity) ---
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1.0, 1.0, 20.0)
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    # --- noise_texture_1: low-scale 4D noise fed by raw TexCoord ---
    noise_texture_1 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise_texture_1, "noise_dimensions"):
        try: noise_texture_1.noise_dimensions = "4D"
        except TypeError: pass
    noise_texture_1.inputs["Scale"].default_value = 0.1
    if "Detail" in noise_texture_1.inputs:     noise_texture_1.inputs["Detail"].default_value = 15.0
    if "Roughness" in noise_texture_1.inputs:  noise_texture_1.inputs["Roughness"].default_value = 0.0
    if "W" in noise_texture_1.inputs:          noise_texture_1.inputs["W"].default_value = w_seed
    nt.links.new(tex_coord.outputs["Object"], noise_texture_1.inputs["Vector"])

    # --- mix : RGBA, fac=0.2, A=mapping(color), B=noise_texture_1.Color ---
    mix_rgba = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_rgba, "data_type"):
        try: mix_rgba.data_type = "RGBA"
        except TypeError: pass
    mix_rgba.inputs[0].default_value = 0.2
    # Feed mapping vector into A (cast via its Vector output — matches source)
    nt.links.new(mapping.outputs["Vector"], mix_rgba.inputs[6])
    nt.links.new(noise_texture_1.outputs["Color"], mix_rgba.inputs[7])

    # --- noise_texture: vector=mix.Result, scale=100, detail=15, rough=0.6, dist=0.1 ---
    noise_texture = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise_texture, "noise_dimensions"):
        try: noise_texture.noise_dimensions = "4D"
        except TypeError: pass
    noise_texture.inputs["Scale"].default_value = scale_mul
    if "Detail" in noise_texture.inputs:     noise_texture.inputs["Detail"].default_value = 15.0
    if "Roughness" in noise_texture.inputs:  noise_texture.inputs["Roughness"].default_value = 0.6
    if "Distortion" in noise_texture.inputs: noise_texture.inputs["Distortion"].default_value = 0.1
    if "W" in noise_texture.inputs:          noise_texture.inputs["W"].default_value = w_seed
    # mix.outputs[2] is the RGBA "Result" — feed it to noise Vector
    nt.links.new(mix_rgba.outputs[2], noise_texture.inputs["Vector"])

    # --- mix_1 : DARKEN, fac=1.0, A=noise_2.Fac, B=noise.Fac ---
    mix_darken = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_darken, "data_type"):
        try: mix_darken.data_type = "RGBA"
        except TypeError: pass
    if hasattr(mix_darken, "blend_type"):
        try: mix_darken.blend_type = "DARKEN"
        except TypeError: pass
    mix_darken.inputs[0].default_value = 1.0
    nt.links.new(_noise_fac_output(noise_texture_2), mix_darken.inputs[6])
    nt.links.new(_noise_fac_output(noise_texture), mix_darken.inputs[7])

    # --- map_range : value -> (0.4,0.6) -> (0.8,1.2) : brightness modulator ---
    map_range_bright = nt.nodes.new("ShaderNodeMapRange")
    map_range_bright.inputs[1].default_value = 0.4
    map_range_bright.inputs[2].default_value = 0.6
    map_range_bright.inputs[3].default_value = 0.8
    map_range_bright.inputs[4].default_value = 1.2
    nt.links.new(mix_darken.outputs[2], map_range_bright.inputs[0])

    # --- hue_saturation_value : color=base, value=map_range_bright ---
    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_node.inputs["Color"].default_value = hsv2rgba(base_color_hsv)
    nt.links.new(map_range_bright.outputs["Result"], hsv_node.inputs["Value"])

    # --- map_range_1 : value -> (0.4,0.6) -> (0.2,0.3) : roughness modulator ---
    map_range_rough = nt.nodes.new("ShaderNodeMapRange")
    map_range_rough.inputs[1].default_value = 0.4
    map_range_rough.inputs[2].default_value = 0.6
    map_range_rough.inputs[3].default_value = 0.2
    map_range_rough.inputs[4].default_value = 0.3
    nt.links.new(mix_darken.outputs[2], map_range_rough.inputs[0])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Metallic=1.0, **{"Specular IOR Level": 0.0})
    nt.links.new(hsv_node.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(map_range_rough.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat


def make_plastic_rough(name="PlasticRough", base_color_rgba=None) -> bpy.types.Material:
    """

    Original: TexCoord -> 4D NoiseTexture(scale*2000, detail=15, dist=2); a
    roughness uniform drives MapRange(0-1 -> 0.05-0.25); MULTIPLY chain
    (rough*0.4)*noise.Fac*0.003 feeds Displacement. Principled BSDF uses
    (Base Color, Roughness=mapped).
    """

    if base_color_rgba is None:
        base_color_rgba = hsv2rgba((np.random.uniform(0, 1),
                                    np.random.uniform(0.5, 0.8),
                                    log_uniform(0.01, 0.5)))
    roughness_in = float(np.random.uniform(0.0, 1.0))
    w_seed = float(np.random.uniform(-1000.0, 1000.0))

    mat = _new_material(name)
    nt = mat.node_tree

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    noise = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise, "noise_dimensions"):
        try: noise.noise_dimensions = "4D"
        except TypeError: pass
    noise.inputs["Scale"].default_value = 2000.0
    if "Detail" in noise.inputs:     noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs: noise.inputs["Distortion"].default_value = 2.0
    if "W" in noise.inputs:          noise.inputs["W"].default_value = w_seed
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[0].default_value = roughness_in
    map_range.inputs[3].default_value = 0.05
    map_range.inputs[4].default_value = 0.25

    # Displacement chain: (mapped_rough * 0.4) * noise.fac * 0.003
    mul1 = nt.nodes.new("ShaderNodeMath")
    mul1.operation = "MULTIPLY"
    mul1.inputs[1].default_value = 0.4
    nt.links.new(map_range.outputs["Result"], mul1.inputs[0])

    mul2 = nt.nodes.new("ShaderNodeMath")
    mul2.operation = "MULTIPLY"
    nt.links.new(_noise_fac_output(noise), mul2.inputs[0])
    nt.links.new(mul1.outputs[0], mul2.inputs[1])

    mul3 = nt.nodes.new("ShaderNodeMath")
    mul3.operation = "MULTIPLY"
    mul3.inputs[1].default_value = 0.003
    nt.links.new(mul2.outputs[0], mul3.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul3.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, **{"Base Color": base_color_rgba})
    nt.links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


# ============================================================================
# === wear_tear post-processing (faithful raw-bpy port) =======================
# ============================================================================
WEAR_TEAR_PROB = [0.5, 0.5]
SCRATCH_LABEL = "scratch"
EDGE_WEAR_LABEL = "wear_tear"


def _find_node(nt, bl_idname):
    return next((n for n in nt.nodes if n.bl_idname == bl_idname), None)


def _value_node(nt, value):
    n = nt.nodes.new("ShaderNodeValue")
    n.outputs[0].default_value = float(value)
    return n


def _math(nt, op, in0=None, in1=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
    for idx, arg in enumerate((in0, in1)):
        if arg is None:
            continue
        if hasattr(arg, "default_value") or hasattr(arg, "links"):
            nt.links.new(arg, n.inputs[idx])
        else:
            n.inputs[idx].default_value = arg
    return n


def _vmath(nt, op, in0=None, in1=None, scale=None):
    n = nt.nodes.new("ShaderNodeVectorMath")
    n.operation = op
    if in0 is not None:
        if hasattr(in0, "default_value") or hasattr(in0, "links"):
            nt.links.new(in0, n.inputs[0])
        else:
            n.inputs[0].default_value = in0
    if in1 is not None:
        if hasattr(in1, "default_value") or hasattr(in1, "links"):
            nt.links.new(in1, n.inputs[1])
        else:
            n.inputs[1].default_value = in1
    if scale is not None:
        for inp in n.inputs:
            if inp.name == "Scale":
                inp.default_value = float(scale)
                break
    return n


def _color_ramp(nt, fac_socket, stops):
    cr = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(fac_socket, cr.inputs["Fac"] if "Fac" in cr.inputs else cr.inputs[0])
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
    if "Detail" in n.inputs:     n.inputs["Detail"].default_value = detail
    if "Distortion" in n.inputs: n.inputs["Distortion"].default_value = distortion
    if "Roughness" in n.inputs:  n.inputs["Roughness"].default_value = roughness
    return n


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
    """Faithful translation of wear_tear/scratches.py:scratch_shader."""

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
        try: map1.vector_type = "TEXTURE"
        except TypeError: pass
    map1.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map1.inputs["Vector"])
    nt.links.new(cxyz1.outputs[0], map1.inputs["Rotation"])
    noise1 = _noise_tex(nt, map1.outputs["Vector"], n_scale.outputs[0],
                        detail=15.0, distortion=22.8, roughness=0.0)

    cxyz2 = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(n_angle2.outputs[0], cxyz2.inputs["Y"])
    map2 = nt.nodes.new("ShaderNodeMapping")
    if hasattr(map2, "vector_type"):
        try: map2.vector_type = "TEXTURE"
        except TypeError: pass
    map2.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map2.inputs["Vector"])
    nt.links.new(cxyz2.outputs[0], map2.inputs["Rotation"])
    noise2 = _noise_tex(nt, map2.outputs["Vector"], n_scale.outputs[0],
                        detail=15.0, distortion=22.8, roughness=0.0)

    add = _math(nt, "ADD", _noise_fac_output(noise1), _noise_fac_output(noise2))

    map3 = nt.nodes.new("ShaderNodeMapping")
    if hasattr(map3, "vector_type"):
        try: map3.vector_type = "TEXTURE"
        except TypeError: pass
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


def _build_edge_wear_graph(nt, original_bsdf_node, original_displacement_node, params):
    """Faithful port of edge_wear.py:shader_edge_tear_free_node_group."""

    p = params
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

    noise_a = _noise_tex(nt, mapping.outputs["Vector"], n_scratch_mask_randomness.outputs[0], detail=1.0)
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

    noise_b = _noise_tex(nt, mapping.outputs["Vector"], n_worn_mask_randomness.outputs[0], detail=1.0)
    cr_c = _color_ramp(nt, _noise_fac_output(noise_b),
                       [(0.0764, (1, 1, 1, 1)), (0.5709, (0, 0, 0, 1))])
    mul_b = _math(nt, "MULTIPLY", abs_b.outputs[0], cr_c.outputs["Color"], clamp=True)
    mul_b1 = _math(nt, "MULTIPLY", n_worn_opacity.outputs[0], mul_b.outputs[0], clamp=True)
    cr_d = _color_ramp(nt, mul_b1.outputs[0],
                       [(0.0, (0, 0, 0, 1)), (0.7782, (1, 1, 1, 1))])

    combine_color = nt.nodes.new("ShaderNodeCombineColor")
    if hasattr(combine_color, "mode"):
        try: combine_color.mode = "HSV"
        except TypeError: pass
    nt.links.new(n_edge_hue.outputs[0], combine_color.inputs["Red"])
    combine_color.inputs["Green"].default_value = 0.7733
    combine_color.inputs["Blue"].default_value = 0.0100

    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        try: mix.data_type = "RGBA"
        except TypeError: pass
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
        try: vor_h.feature = "DISTANCE_TO_EDGE"
        except TypeError: pass
    nt.links.new(map_h.outputs["Vector"], vor_h.inputs["Vector"])
    nt.links.new(n_scratch_density.outputs[0], vor_h.inputs["Scale"])

    map_v = nt.nodes.new("ShaderNodeMapping")
    map_v.inputs["Scale"].default_value = (1.0, 10.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map_v.inputs["Vector"])
    scale_v = _vmath(nt, "SCALE", in0=n_scratch_density.outputs[0], scale=2.0)
    vor_v = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(vor_v, "feature"):
        try: vor_v.feature = "DISTANCE_TO_EDGE"
        except TypeError: pass
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
# === Geometry framework (verbatim from objects_blender/) ====================
# ============================================================================
class FixedSeed:
    def __init__(self, seed):
        self.seed = int(seed)
        self.py_state = None
        self.np_state = None
    def __enter__(self):
        self.py_state = random.getstate(); self.np_state = np.random.get_state()
        random.seed(self.seed); np.random.seed(self.seed)
    def __exit__(self, *_):
        random.setstate(self.py_state); np.random.set_state(self.np_state)

def md5_hash(x):
    if isinstance(x, (tuple, list)):
        m = hashlib.md5(); [m.update(str(s).encode('utf-8')) for s in x]; return m
    return hashlib.md5(str(x).encode('utf-8'))

def int_hash(x, max=(2**32 - 1)):
    return abs(int(md5_hash(x).hexdigest(), 16)) % max

def _select_none():
    for o in list(bpy.context.selected_objects): o.select_set(False)
    if bpy.context.active_object: bpy.context.active_object.select_set(False)

def _set_active(o):
    bpy.context.view_layer.objects.active = o
    if o is not None: o.select_set(True)

def apply_transform(obj, loc=False, rot=True, scale=True):
    _select_none()
    _set_active(obj)
    bpy.ops.object.transform_apply(location=loc, rotation=rot, scale=scale)

def geometry_node_group_empty_new():
    group = bpy.data.node_groups.new('Geometry Nodes', 'GeometryNodeTree')
    group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    inp = group.nodes.new('NodeGroupInput')
    out = group.nodes.new('NodeGroupOutput')
    out.is_active_output = True
    try:
        group.links.new(inp.outputs['Geometry'], out.inputs['Geometry'])
    except Exception:
        pass
    return group

def ng_inputs(node_group):
    return {s.name: s for s in node_group.interface.items_tree if s.in_out == 'INPUT'}

def ng_outputs(node_group):
    return {s.name: s for s in node_group.interface.items_tree if s.in_out == 'OUTPUT'}

def assign_curve(c, points, handles=None):
    for i, p in enumerate(points):
        if i < 2: c.points[i].location = p
        else: c.points.new(*p)
        if handles is not None: c.points[i].handle_type = handles[i]

def to_nodegroup(name=None, singleton=False, type='GeometryNodeTree'):
    def reg(fn):
        ng_name = name or fn.__name__
        if singleton: ng_name += ' (no gc)'
        def init_fn(*args, **kwargs):
            if singleton and ng_name in bpy.data.node_groups:
                return bpy.data.node_groups[ng_name]
            ng = bpy.data.node_groups.new(ng_name, type)
            nw = NodeWrangler(ng)
            fn(nw, *args, **kwargs)
            return ng
        return init_fn
    return reg

node_utils = SimpleNamespace(to_nodegroup=to_nodegroup, assign_curve=assign_curve)

def _infer_output_socket(item):
    if isinstance(item, bpy.types.NodeSocket): return item
    if isinstance(item, tuple) and len(item) == 2 and hasattr(item[0], 'outputs'):
        n, s = item
        try: return n.outputs[s]
        except Exception: return n.outputs[int(s)]
    if hasattr(item, 'outputs'):
        for s in item.outputs:
            if getattr(s, 'enabled', True): return s
        if len(item.outputs): return item.outputs[0]
    return None

def _socket_type_for_val(v):
    if isinstance(v, bool): return 'NodeSocketBool'
    if isinstance(v, int): return 'NodeSocketInt'
    if isinstance(v, float): return 'NodeSocketFloat'
    if isinstance(v, (tuple, list, np.ndarray)):
        if len(v) == 3: return 'NodeSocketVector'
        if len(v) == 4: return 'NodeSocketColor'
    return 'NodeSocketFloat'

def _socket_type_for_out(sock):
    if sock is None: return 'NodeSocketFloat'
    sid = getattr(sock, 'bl_idname', None)
    return sid if isinstance(sid, str) and sid.startswith('NodeSocket') else 'NodeSocketFloat'

class NodeWrangler:
    def __init__(self, node_group_or_mod):
        if isinstance(node_group_or_mod, bpy.types.NodesModifier):
            self.modifier = node_group_or_mod
            self.node_group = self.modifier.node_group
        else:
            self.modifier = None
            self.node_group = node_group_or_mod
        self.nodes = self.node_group.nodes
        self.links = self.node_group.links

    def _group_io(self, bl_idname):
        for n in self.nodes:
            if n.bl_idname == bl_idname: return n
        n = self.nodes.new(bl_idname)
        if bl_idname == 'NodeGroupOutput': n.is_active_output = True
        return n

    def expose_input(self, name, val=None, attribute=None, dtype=None, use_namednode=False):
        gi = self._group_io('NodeGroupInput')
        if name not in ng_inputs(self.node_group):
            socket_type = dtype if isinstance(dtype, str) and dtype.startswith('NodeSocket') else _socket_type_for_val(val)
            if val is None and name == 'Geometry': socket_type = 'NodeSocketGeometry'
            iface = self.node_group.interface.new_socket(name=name, in_out='INPUT', socket_type=socket_type)
            if val is not None and hasattr(iface, 'default_value'):
                try: iface.default_value = val
                except Exception:
                    try: iface.default_value = tuple(val)
                    except Exception: pass
            if self.modifier is not None and val is not None:
                try: self.modifier[iface.identifier] = val
                except Exception: pass
        return gi.outputs[name]

    def connect_input(self, sock, item):
        if isinstance(item, list):
            for it in item: self.connect_input(sock, it)
            return
        out = _infer_output_socket(item)
        if out is not None:
            self.links.new(out, sock)
            return
        if hasattr(sock, 'default_value'):
            try: sock.default_value = item
            except Exception:
                try: sock.default_value = tuple(item)
                except Exception: pass

    def _make_node(self, node_type):
        if isinstance(node_type, str) and node_type in bpy.data.node_groups and not node_type.startswith(('ShaderNode','GeometryNode','FunctionNode','CompositorNode','NodeGroup')):
            n = self.nodes.new('GeometryNodeGroup' if self.node_group.bl_idname == 'GeometryNodeTree' else 'ShaderNodeGroup')
            n.node_tree = bpy.data.node_groups[node_type]
            return n
        if isinstance(node_type, str) and node_type in bpy.data.node_groups:
            try: return self.nodes.new(node_type)
            except Exception:
                n = self.nodes.new('GeometryNodeGroup' if self.node_group.bl_idname == 'GeometryNodeTree' else 'ShaderNodeGroup')
                n.node_tree = bpy.data.node_groups[node_type]
                return n
        return self.nodes.new(node_type)

    def new_node(self, node_type, input_args=None, attrs=None, input_kwargs=None, label=None, expose_input=None, compat_mode=True, strict=True):
        input_args = [] if input_args is None else list(input_args)
        attrs = {} if attrs is None else dict(attrs)
        input_kwargs = {} if input_kwargs is None else dict(input_kwargs)
        if node_type == getattr(Nodes, 'GroupInput', 'NodeGroupInput'):
            node = self._group_io('NodeGroupInput')
        elif node_type == getattr(Nodes, 'GroupOutput', 'NodeGroupOutput'):
            node = self._group_io('NodeGroupOutput')
        else:
            node = self._make_node(node_type)
        if label is not None:
            node.label = label; node.name = label
        if expose_input is not None:
            for dtype, name, val in expose_input:
                self.expose_input(name, val=val, dtype=dtype)
        for k, v in attrs.items():
            t = node
            if '.' in k:
                parts = k.split('.')
                for p in parts[:-1]: t = getattr(t, p)
                setattr(t, parts[-1], v)
            else:
                setattr(node, k, v)
        for k, v in list(enumerate(input_args)) + list(input_kwargs.items()):
            if v is None: continue
            if node.bl_idname == 'NodeGroupOutput' and not isinstance(k, int) and k not in node.inputs:
                out_sock = _infer_output_socket(v)
                self.node_group.interface.new_socket(name=k, in_out='OUTPUT', socket_type=_socket_type_for_out(out_sock))
            try: sock = node.inputs[k]
            except Exception: sock = node.inputs[int(k)]
            self.connect_input(sock, v)
        return node

def add_geomod(objs, geo_func, name=None, apply=False, input_args=None, input_kwargs=None, attributes=None, **_ignored):
    if input_args is None: input_args = []
    if input_kwargs is None: input_kwargs = {}
    if attributes is None: attributes = []
    if not isinstance(objs, list): objs = [objs]
    if not objs: return None
    ng = None
    mod_last = None
    for obj in objs:
        mod = obj.modifiers.new(name=name or geo_func.__name__, type='NODES')
        if ng is None:
            if mod.node_group is None: mod.node_group = geometry_node_group_empty_new()
            nw = NodeWrangler(mod)
            geo_func(nw, *input_args, **input_kwargs)
            ng = mod.node_group
            ng.name = name or geo_func.__name__
        else:
            mod.node_group = ng
        if attributes:
            try:
                outs = [o for o in ng_outputs(mod.node_group).values() if getattr(o, 'socket_type', None) != 'NodeSocketGeometry']
                for o, att in zip(outs, attributes):
                    if att: mod[o.identifier + '_attribute_name'] = att
            except Exception:
                pass
        if apply:
            _select_none()
            _set_active(obj)
            bpy.ops.object.modifier_apply(modifier=mod.name)
        mod_last = mod
    return mod_last

class AssetFactory:
    def __init__(self, factory_seed=None, coarse=False):
        self.factory_seed = int(factory_seed if factory_seed is not None else np.random.randint(1e9))
        self.coarse = coarse
    def __call__(self, i=0, **kwargs):
        with FixedSeed(int_hash((self.factory_seed, i))):
            return self.create_asset(i=i, **kwargs)

class Nodes:
    CombineXYZ = 'ShaderNodeCombineXYZ'
    CurveBezierSegment = 'GeometryNodeCurvePrimitiveBezierSegment'
    CurveCircle = 'GeometryNodeCurvePrimitiveCircle'
    CurveLine = 'GeometryNodeCurvePrimitiveLine'
    CurveToMesh = 'GeometryNodeCurveToMesh'
    FloatCurve = 'ShaderNodeFloatCurve'
    GroupOutput = 'NodeGroupOutput'
    InstanceOnPoints = 'GeometryNodeInstanceOnPoints'
    Integer = 'FunctionNodeInputInt'
    JoinGeometry = 'GeometryNodeJoinGeometry'
    Math = 'ShaderNodeMath'
    MergeByDistance = 'GeometryNodeMergeByDistance'
    MeshBoolean = 'GeometryNodeMeshBoolean'
    MeshCube = 'GeometryNodeMeshCube'
    MeshLine = 'GeometryNodeMeshLine'
    MeshToCurve = 'GeometryNodeMeshToCurve'
    RealizeInstances = 'GeometryNodeRealizeInstances'
    ScaleInstances = 'GeometryNodeScaleInstances'
    SetCurveRadius = 'GeometryNodeSetCurveRadius'
    SetMaterial = 'GeometryNodeSetMaterial'
    SplineParameter = 'GeometryNodeSplineParameter'
    Transform = 'GeometryNodeTransform'
    Value = 'ShaderNodeValue'
    Vector = 'FunctionNodeInputVector'


# Phase 1: materials on raw SEED (hook metal → board plastic → spatula plastic)
SEED = int(os.environ.get("SEED", 0))
seed_all(SEED)
MAT_HOOK_METAL         = make_brushed_metal(name="HookMetal")
MAT_HOOK_BOARD_PLASTIC = make_plastic_rough(name="HookBoardPlastic")
MAT_SPATULA_PLASTIC    = make_plastic_rough(name="SpatulaPlastic")

_scratch_p, _edge_p = WEAR_TEAR_PROB
WEAR_DO_SCRATCH  = (np.random.uniform() <= _scratch_p)
WEAR_DO_EDGEWEAR = (np.random.uniform() <= _edge_p)


# ---------------------------------------------------------------------------
# Geometry (SetMaterial sites use pre-built MAT_* materials)
# ---------------------------------------------------------------------------

def hook_geometry_nodes(nw: NodeWrangler, **kwargs):
    # Code generated using version 2.6.5 of the node_transpiler

    hook_num = nw.new_node(Nodes.Integer, label="hook_num")
    hook_num.integer = kwargs["num_hook"]

    add = nw.new_node(Nodes.Math, input_kwargs={0: hook_num, 1: -1.0000})

    hook_gap = nw.new_node(Nodes.Value, label="hook_gap")
    hook_gap.outputs[0].default_value = kwargs["hook_gap"]

    multiply = nw.new_node(
        Nodes.Math, input_kwargs={0: hook_gap, 1: add}, attrs={"operation": "MULTIPLY"}
    )

    multiply_1 = nw.new_node(
        Nodes.Math, input_kwargs={0: multiply}, attrs={"operation": "MULTIPLY"}
    )

    multiply_2 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: multiply_1, 1: -1.0000},
        attrs={"operation": "MULTIPLY"},
    )

    combine_xyz_2 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": multiply_2})

    combine_xyz_1 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": multiply_1})

    mesh_line = nw.new_node(
        Nodes.MeshLine,
        input_kwargs={
            "Count": add,
            "Start Location": combine_xyz_2,
            "Offset": combine_xyz_1,
        },
        attrs={"mode": "END_POINTS"},
    )

    bezier_segment = nw.new_node(
        Nodes.CurveBezierSegment,
        input_kwargs={
            "Start": (0.0000, 0.0000, 0.0000),
            "Start Handle": (0.0000, 0.0000, kwargs["init_handle"]),
            "End Handle": kwargs["curve_handle"],
            "End": kwargs["curve_end_point"],
        },
    )

    curve_line = nw.new_node(Nodes.CurveLine)

    join_geometry_3 = nw.new_node(
        Nodes.JoinGeometry, input_kwargs={"Geometry": [bezier_segment, curve_line]}
    )

    spline_parameter = nw.new_node(Nodes.SplineParameter)

    float_curve = nw.new_node(
        Nodes.FloatCurve, input_kwargs={"Factor": spline_parameter.outputs["Factor"]}
    )
    node_utils.assign_curve(
        float_curve.mapping.curves[0], [(0.0000, 0.8), (0.5, 0.8), (1.0000, 0.8)]
    )

    raduis = nw.new_node(Nodes.Value, label="raduis")
    raduis.outputs[0].default_value = kwargs["hook_radius"]

    multiply_3 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: float_curve, 1: raduis},
        attrs={"operation": "MULTIPLY"},
    )

    set_curve_radius = nw.new_node(
        Nodes.SetCurveRadius,
        input_kwargs={"Curve": join_geometry_3, "Radius": multiply_3},
    )

    curve_circle = nw.new_node(
        Nodes.CurveCircle,
        input_kwargs={
            "Resolution": kwargs["hook_resolution"],
            "Point 1": (1.0000, 0.0000, 0.0000),
            "Point 3": (-1.0000, 0.0000, 0.0000),
        },
        attrs={"mode": "POINTS"},
    )

    hook_reshape = nw.new_node(Nodes.Vector, label="hook_reshape")
    hook_reshape.vector = (1.0000, 1.0000, 1.0000)

    transform_geometry_2 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": curve_circle.outputs["Curve"], "Scale": hook_reshape},
    )

    # Blender 5.0: SetCurveRadius ignored by CurveToMesh — pass via Scale input
    curve_to_mesh = nw.new_node(
        Nodes.CurveToMesh,
        input_kwargs={
            "Curve": set_curve_radius,
            "Profile Curve": transform_geometry_2,
            "Fill Caps": True,
            "Scale": multiply_3,
        },
    )

    hook_size = nw.new_node(Nodes.Value, label="hook_size")
    hook_size.outputs[0].default_value = kwargs["hook_size"]

    transform_geometry = nw.new_node(
        Nodes.Transform, input_kwargs={"Geometry": curve_to_mesh, "Scale": hook_size}
    )

    realize_instances_1 = nw.new_node(
        Nodes.RealizeInstances, input_kwargs={"Geometry": transform_geometry}
    )

    merge_by_distance_1 = nw.new_node(
        Nodes.MergeByDistance, input_kwargs={"Geometry": realize_instances_1}
    )

    instance_on_points = nw.new_node(
        Nodes.InstanceOnPoints,
        input_kwargs={"Points": mesh_line, "Instance": merge_by_distance_1},
    )

    scale_instances = nw.new_node(
        Nodes.ScaleInstances, input_kwargs={"Instances": instance_on_points}
    )

    # hook curves -> brushed metal
    set_material = nw.new_node(
        Nodes.SetMaterial,
        input_kwargs={
            "Geometry": scale_instances,
            "Material": MAT_HOOK_METAL,
        },
    )

    board_side_gap = nw.new_node(Nodes.Value, label="board_side_gap")
    board_side_gap.outputs[0].default_value = kwargs["board_side_gap"]

    add_1 = nw.new_node(Nodes.Math, input_kwargs={0: multiply, 1: board_side_gap})

    board_thickness = nw.new_node(Nodes.Value, label="board_thickness")
    board_thickness.outputs[0].default_value = kwargs["board_thickness"]

    board_height = nw.new_node(Nodes.Value, label="board_height")
    board_height.outputs[0].default_value = kwargs["board_height"]

    combine_xyz = nw.new_node(
        Nodes.CombineXYZ,
        input_kwargs={"X": add_1, "Y": board_thickness, "Z": board_height},
    )

    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": combine_xyz})

    multiply_4 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: board_thickness, 1: -0.5000},
        attrs={"operation": "MULTIPLY"},
    )

    multiply_5 = nw.new_node(
        Nodes.Math, input_kwargs={0: board_height}, attrs={"operation": "MULTIPLY"}
    )

    subtract = nw.new_node(
        Nodes.Math,
        input_kwargs={0: hook_size, 1: multiply_5},
        attrs={"operation": "SUBTRACT"},
    )

    combine_xyz_3 = nw.new_node(
        Nodes.CombineXYZ, input_kwargs={"Y": multiply_4, "Z": subtract}
    )

    transform_geometry_1 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": cube.outputs["Mesh"], "Translation": combine_xyz_3},
    )

    # backing board -> rough plastic
    set_material_1 = nw.new_node(
        Nodes.SetMaterial,
        input_kwargs={
            "Geometry": transform_geometry_1,
            "Material": MAT_HOOK_BOARD_PLASTIC,
        },
    )

    join_geometry_2 = nw.new_node(
        Nodes.JoinGeometry, input_kwargs={"Geometry": [set_material, set_material_1]}
    )

    realize_instances = nw.new_node(
        Nodes.RealizeInstances, input_kwargs={"Geometry": join_geometry_2}
    )

    triangulate = nw.new_node(
        "GeometryNodeTriangulate", input_kwargs={"Mesh": realize_instances}
    )

    transform_geometry_3 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": triangulate, "Rotation": (0.0000, 0.0000, -1.5708)},
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": transform_geometry_3},
        attrs={"is_active_output": True},
    )

def spatula_geometry_nodes(nw: NodeWrangler, **kwargs):
    # Code generated using version 2.6.5 of the node_transpiler

    handle_length = nw.new_node(Nodes.Value, label="handle_length")
    handle_length.outputs[0].default_value = kwargs["handle_length"]

    combine_xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": handle_length})

    mesh_line = nw.new_node(
        Nodes.MeshLine,
        input_kwargs={"Count": 64, "Offset": combine_xyz},
        attrs={"mode": "END_POINTS"},
    )

    mesh_to_curve = nw.new_node(Nodes.MeshToCurve, input_kwargs={"Mesh": mesh_line})

    handle_radius = nw.new_node(Nodes.Value, label="handle_radius")
    handle_radius.outputs[0].default_value = kwargs["handle_radius"]

    spline_parameter = nw.new_node(Nodes.SplineParameter)

    float_curve = nw.new_node(
        Nodes.FloatCurve, input_kwargs={"Value": spline_parameter.outputs["Factor"]}
    )
    node_utils.assign_curve(
        float_curve.mapping.curves[0], kwargs["handle_control_points"]
    )

    multiply = nw.new_node(
        Nodes.Math,
        input_kwargs={0: handle_radius, 1: float_curve},
        attrs={"operation": "MULTIPLY"},
    )

    set_curve_radius = nw.new_node(
        Nodes.SetCurveRadius, input_kwargs={"Curve": mesh_to_curve, "Radius": multiply}
    )

    curve_circle = nw.new_node(Nodes.CurveCircle)

    # Blender 5.0: SetCurveRadius ignored by CurveToMesh — pass via Scale input
    curve_to_mesh = nw.new_node(
        Nodes.CurveToMesh,
        input_kwargs={
            "Curve": set_curve_radius,
            "Profile Curve": curve_circle.outputs["Curve"],
            "Fill Caps": True,
            "Scale": multiply,
        },
    )

    transform_geometry = nw.new_node(
        Nodes.Transform,
        input_kwargs={
            "Geometry": curve_to_mesh,
            "Scale": (kwargs["handle_ratio"], 1.0, 1.0),
        },
    )

    hole_radius = nw.new_node(Nodes.Value, label="hole_radius")
    hole_radius.outputs[0].default_value = kwargs["hole_radius"]

    cylinder = nw.new_node(
        "GeometryNodeMeshCylinder",
        input_kwargs={"Radius": hole_radius, "Depth": 0.1000},
    )

    hole_place_ratio = nw.new_node(Nodes.Value, label="hole_placement")
    hole_place_ratio.outputs[0].default_value = kwargs["hole_placement"]

    multiply_1 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: handle_length, 1: hole_place_ratio},
        attrs={"operation": "MULTIPLY"},
    )

    combine_xyz_1 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": multiply_1})

    transform_geometry_1 = nw.new_node(
        Nodes.Transform,
        input_kwargs={
            "Geometry": cylinder.outputs["Mesh"],
            "Translation": combine_xyz_1,
            "Rotation": (0.0000, 1.5708, 0.0000),
            "Scale": (kwargs["hole_ratio"], 1.0000, 1.0000),
        },
    )

    difference = nw.new_node(
        Nodes.MeshBoolean,
        input_kwargs={"Mesh 1": transform_geometry, "Mesh 2": transform_geometry_1},
    )

    cube = nw.new_node(
        Nodes.MeshCube,
        input_kwargs={
            "Size": (
                kwargs["plate_thickness"],
                kwargs["plate_width"],
                kwargs["plate_length"],
            ),
            "Vertices X": 2,
            "Vertices Y": 6,
            "Vertices Z": 6,
        },
    )

    transform_geometry_3 = nw.new_node(
        Nodes.Transform,
        input_kwargs={
            "Geometry": cube.outputs["Mesh"],
            "Translation": (0.0000, 0.0000, -kwargs["plate_length"] / 2.0),
        },
    )

    # Handle-plate transition collar
    collar = nw.new_node(
        Nodes.MeshCube,
        input_kwargs={
            "Size": (
                kwargs["plate_thickness"],
                kwargs["plate_width"] * 0.5,
                0.005,
            ),
            "Vertices X": 2,
            "Vertices Y": 6,
            "Vertices Z": 2,
        },
    )

    transform_collar = nw.new_node(
        Nodes.Transform,
        input_kwargs={
            "Geometry": collar.outputs["Mesh"],
            "Translation": (0.0000, 0.0000, -0.0025),
        },
    )

    join_geometry = nw.new_node(
        Nodes.JoinGeometry,
        input_kwargs={
            "Geometry": [
                difference.outputs["Mesh"],
                transform_collar,
                transform_geometry_3,
            ]
        },
    )

    realize_instances = nw.new_node(
        Nodes.RealizeInstances, input_kwargs={"Geometry": join_geometry}
    )

    triangulate = nw.new_node(
        "GeometryNodeTriangulate", input_kwargs={"Mesh": realize_instances}
    )

    multiply_2 = nw.new_node(
        Nodes.Math,
        input_kwargs={0: multiply_1, 1: -1.0000},
        attrs={"operation": "MULTIPLY"},
    )

    combine_xyz_2 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": multiply_2})

    transform_geometry_2 = nw.new_node(
        Nodes.Transform,
        input_kwargs={"Geometry": triangulate, "Translation": combine_xyz_2},
    )

    # whole spatula -> rough plastic
    set_material = nw.new_node(
        Nodes.SetMaterial,
        input_kwargs={
            "Geometry": transform_geometry_2,
            "Material": MAT_SPATULA_PLASTIC,
        },
    )

    group_output = nw.new_node(
        Nodes.GroupOutput,
        input_kwargs={"Geometry": set_material},
        attrs={"is_active_output": True},
    )

class HookBaseFactory(AssetFactory):
    def __init__(self, factory_seed, params={}, coarse=False):
        super(HookBaseFactory, self).__init__(factory_seed, coarse=coarse)
        self.params = params

    def sample_params(self):
        return self.params.copy()

    def get_hang_points(self, params):
        # compute the lowest point in the bezier curve
        x = params["init_handle"]
        y = params["curve_handle"][2] - params["init_handle"]
        z = params["curve_end_point"][2] - params["curve_handle"][2]

        t1 = (x - y + np.sqrt(y**2 - x * z)) / (x + z - 2 * y)
        t2 = (x - y - np.sqrt(y**2 - x * z)) / (x + z - 2 * y)

        t = 0
        if t1 >= 0 and t1 <= 1:
            t = max(t1, t)
        if t2 >= 0 and t2 <= 1:
            t = max(t2, t)
        if t == 0:
            t = 0.5

        alpha1 = 3 * ((1 - t) ** 2) * t
        alpha2 = 3 * (1 - t) * (t**2)
        alpha3 = t**3

        z = (
            alpha1 * params["init_handle"]
            + alpha2 * params["curve_handle"][-1]
            + alpha3 * params["curve_end_point"][-1]
        )
        x = alpha2 * params["curve_handle"][-2] + alpha3 * params["curve_end_point"][-2]

        ys = []
        total_length = (
            params["board_side_gap"] + (params["num_hook"] - 1) * params["hook_gap"]
        )
        for i in range(params["num_hook"]):
            y = (
                -total_length / 2.0
                + params["board_side_gap"] / 2.0
                + i * params["hook_gap"]
            )
            ys.append(y)

        hang_points = []
        for y in ys:
            hang_points.append((x * params["hook_size"], y, z * params["hook_size"]))

        return hang_points

    def get_asset_params(self, i=0):
        params = self.sample_params()
        if params.get("num_hook", None) is None:
            params["num_hook"] = randint(3, 6)
        if params.get("hook_size", None) is None:
            params["hook_size"] = uniform(0.05, 0.1)
        if params.get("hook_radius", None) is None:
            params["hook_radius"] = uniform(0.002, 0.004) / params["hook_size"]
        else:
            params["hook_radius"] = params["hook_radius"] / params["hook_size"]

        if params.get("hook_resolution", None) is None:
            params["hook_resolution"] = np.random.choice([4, 32], p=[0.5, 0.5])

        if params.get("hook_gap", None) is None:
            params["hook_gap"] = uniform(0.04, 0.08)
        if params.get("board_height", None) is None:
            params["board_height"] = params["hook_size"] + uniform(-0.02, 0.01)
        if params.get("board_thickness", None) is None:
            params["board_thickness"] = uniform(0.005, 0.015)
        if params.get("board_side_gap", None) is None:
            params["board_side_gap"] = uniform(0.03, 0.05)

        params["init_handle"] = uniform(-0.15, -0.25)
        params["curve_handle"] = (0, uniform(0.15, 0.35), uniform(-0.15, -0.35))
        params["curve_end_point"] = (0, uniform(0.35, 0.55), uniform(-0.05, 0.15))

        return params

    def create_asset(self, i=0, **params):
        bpy.ops.mesh.primitive_plane_add(
            size=1,
            enter_editmode=False,
            align="WORLD",
            location=(0, 0, 0),
            scale=(1, 1, 1),
        )
        obj = bpy.context.active_object

        obj_params = self.get_asset_params(i)
        add_geomod(
            obj, hook_geometry_nodes, attributes=[], apply=True, input_kwargs=obj_params
        )

        hang_points = self.get_hang_points(obj_params)

        return obj, hang_points

class SpatulaBaseFactory(AssetFactory):
    def __init__(self, factory_seed, params={}, coarse=False):
        super(SpatulaBaseFactory, self).__init__(factory_seed, coarse=coarse)
        self.params = params

    def sample_params(self):
        return self.params.copy()

    def get_asset_params(self, i=0):
        params = self.sample_params()

        if params.get("hole_radius", None) is None:
            params["hole_radius"] = uniform(0.005, 0.010)
        if params.get("hole_placement", None) is None:
            params["hole_placement"] = uniform(0.75, 0.9)
        if params.get("hole_ratio", None) is None:
            params["hole_ratio"] = uniform(0.8, 2.0)

        if params.get("handle_length", None) is None:
            params["handle_length"] = uniform(0.15, 0.25)

        if params.get("handle_ratio", None) is None:
            params["handle_ratio"] = uniform(0.1, 0.4)
        if params.get("handle_control_points", None) is None:
            params["handle_control_points"] = [
                (0, uniform(0.55, 0.70)),
                (0.3, uniform(0.58, 0.72)),
                (0.65, uniform(0.50, 0.62)),
                (1.0, uniform(0.42, 0.55)),
            ]
        if params.get("handle_radius", None) is None:
            params["handle_radius"] = (
                params["hole_radius"] / params["handle_control_points"][0][1]
            ) / uniform(0.6, 0.8)

        if params.get("plate_thickness", None) is None:
            params["plate_thickness"] = uniform(0.005, 0.01)
        if params.get("plate_width", None) is None:
            params["plate_width"] = uniform(0.04, 0.06)
        if params.get("plate_length", None) is None:
            params["plate_length"] = uniform(0.05, 0.08)

        return params

    def create_asset(self, i=0, **params):
        bpy.ops.mesh.primitive_plane_add(
            size=1,
            enter_editmode=False,
            align="WORLD",
            location=(0, 0, 0),
            scale=(1, 1, 1),
        )
        obj = bpy.context.active_object

        obj_params = self.get_asset_params(i)
        add_geomod(
            obj,
            spatula_geometry_nodes,
            attributes=[],
            apply=True,
            input_kwargs=obj_params,
        )

        return obj

class SpatulaOnHookBaseFactory(AssetFactory):
    def __init__(self, factory_seed, params={}, coarse=False):
        super(SpatulaOnHookBaseFactory, self).__init__(factory_seed, coarse=coarse)
        self.params = params

        self.hook_fac = HookBaseFactory(factory_seed, params=params)
        self.spatula_fac = SpatulaBaseFactory(factory_seed, params=params)

    def get_asset_params(self, i):
        if self.params.get("hook_radius", None) is None:
            r = uniform(0.002, 0.0035)
            self.hook_fac.params["hook_radius"] = r
            self.spatula_fac.params["hole_radius"] = r / uniform(0.3, 0.6)

    def create_asset(self, i, **params):
        self.get_asset_params(i)
        hook, hang_points = self.hook_fac.create_asset(i)
        spatula = self.spatula_fac.create_asset(i)

        spatula.location = hang_points[0]
        apply_transform(spatula, loc=True)

        # Join hook + spatula into a single object so that both parts live
        # on the same mesh and the renderer (which picks active_object) can
        # see all 3 material slots. The geometry script kept them separate
        # and only returned ``hook``, dropping the spatula from the active
        # hierarchy — we fix that here.
        _select_none()
        _set_active(spatula)
        hook.select_set(True)
        _set_active(hook)  # active = join target
        bpy.ops.object.join()
        joined = bpy.context.active_object
        _select_none()
        return joined


def build(seed=SEED):
    fac = SpatulaOnHookBaseFactory(seed)
    with FixedSeed(int_hash((fac.factory_seed, 0))):
        result = fac.create_asset(i=0)
    obj = result if not isinstance(result, tuple) else result[0]
    obj.name = "SpatulaOnHookBaseFactory"
    # apply wear_tear (gates sampled in Phase 1)
    if WEAR_DO_SCRATCH:
        apply_scratches(obj)
    if WEAR_DO_EDGEWEAR:
        apply_edge_wear(obj)
    fallback = next((mat for mat in obj.data.materials if mat is not None), None)
    if fallback is not None:
        for i in range(len(obj.data.materials)):
            if obj.data.materials[i] is None:
                obj.data.materials[i] = fallback
    return obj


obj = build(SEED)
