# [FL_INDEX: keywords="blender_factory, procedural_3d, ChopsticksFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: ChopsticksFactory | Category: factories_tex
# Prompt: A 3D model of a pair of chopsticks rendered from a top-down slightly angled perspective. The chopsticks feature two long, slender tapered cylindrical rods laid crossed over each other, with a uniform dark blue-black coloring and squared-off tops tapering to thin rounded tips.

"""ChopsticksFactory -- standalone Blender script with wood/bamboo material + wear_tear.

Geometry: copied verbatim from objects_blender/tableware/ChopsticksFactory.py
          — chopsticks are wood/bamboo; the TablewareFactory base class uses
            material_assignments.cup for surface, but we use 'woods' registry (wood.Wood)
            since chopsticks are characteristically wooden.
Wear_tear: scratches (50% prob) + edge_wear (50% prob)

Run:  blender --background --python ChopsticksFactory.py
"""


import os
import math
import random
import colorsys

import bpy
import numpy as np
from numpy.random import uniform

# --- Seed ---
SEED = int(os.environ.get("SEED", 0))
np.random.seed(SEED)
random.seed(SEED)

def seed_all(seed: int):
    np.random.seed(seed)
    random.seed(seed)

# --- Utility helpers ---

def log_uniform(low, high, size=None):
    return np.exp(np.random.uniform(np.log(low), np.log(high), size))

def hsv2rgba(hsv):
    h, s, v = hsv
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

def _mat_log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

WOOD_COLORS = [
    0x4C2F27, 0x69432D, 0x371803, 0x7F4040, 0xCC9576, 0x9E8170, 0x3D2B1F,
    0x8D6A58, 0x8B3325, 0x79443C, 0x88540B, 0x9B5F43, 0x4E3828, 0x4E3828,
    0xC09A6B, 0x944536, 0x3F0110, 0x773C12, 0x6E4E37, 0x5C4033, 0x5C4033,
    0x3C3034, 0x96704C, 0x371B1A, 0x483B32, 0x43141A, 0x471713, 0xC3B090,
    0x6B4423,
]

def hex2rgba(h):
    r = ((h >> 16) & 0xFF) / 255.0
    g = ((h >> 8) & 0xFF) / 255.0
    b = (h & 0xFF) / 255.0
    return (r, g, b, 1.0)

def bark_hsv():
    hexval = int(np.random.choice(WOOD_COLORS))
    r, g, b, _ = hex2rgba(hexval)
    return colorsys.rgb_to_hsv(r, g, b)

def get_wood_color():
    h, s, v = bark_hsv()
    return hsv2rgba((
        h + np.random.uniform(-0.0, 0.05),
        s + np.random.uniform(-0.3, 0.2),
        v * _mat_log_uniform(0.2, 20),
    ))

# --- Low-level node-tree helpers ---

def _new_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat

def _set_principled(bsdf, **kw):
    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Specular": ("Specular IOR Level", "Specular"),
        "Coat Weight": ("Coat Weight", "Clearcoat"),
        "Coat Roughness": ("Coat Roughness", "Clearcoat Roughness"),
        "Sheen Weight": ("Sheen Weight", "Sheen"),
        "Transmission Weight": ("Transmission Weight", "Transmission"),
        "Subsurface Weight": ("Subsurface Weight", "Subsurface"),
    }
    for k, v in kw.items():
        names = aliases.get(k, (k,))
        for name in names:
            if name in bsdf.inputs:
                bsdf.inputs[name].default_value = v
                break

def _noise_fac_output(noise_node):
    if "Fac" in noise_node.outputs:
        return noise_node.outputs["Fac"]
    if "Factor" in noise_node.outputs:
        return noise_node.outputs["Factor"]
    return noise_node.outputs[0]

def _connect_output(nt, bsdf, displacement=None, volume=None):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    if displacement is not None:
        nt.links.new(displacement, out.inputs["Displacement"])
    if volume is not None:
        nt.links.new(volume, out.inputs["Volume"])
    return out

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

def _value_node(nt, value):
    n = nt.nodes.new("ShaderNodeValue")
    n.outputs[0].default_value = value
    return n

def _math(nt, op, in0=None, in1=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
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
    return n

def _vmath(nt, op, in0=None, in1=None, scale=None):
    n = nt.nodes.new("ShaderNodeVectorMath")
    n.operation = op
    if in0 is not None:
        if hasattr(in0, "links"):
            nt.links.new(in0, n.inputs[0])
        else:
            n.inputs[0].default_value = in0
    if in1 is not None:
        if hasattr(in1, "links"):
            nt.links.new(in1, n.inputs[1])
        else:
            n.inputs[1].default_value = in1
    if scale is not None:
        for inp in n.inputs:
            if inp.name == "Scale":
                inp.default_value = scale
                break
    return n

def _color_ramp(nt, fac_socket, stops):
    cr = nt.nodes.new("ShaderNodeValToRGB")
    fac_in = cr.inputs.get("Fac") or cr.inputs[0]
    nt.links.new(fac_socket, fac_in)
    elements = cr.color_ramp.elements
    for i, (pos, color) in enumerate(stops):
        if i < len(elements):
            elements[i].position = pos
            elements[i].color = color
        else:
            e = elements.new(pos)
            e.color = color
    return cr

def _noise_tex(nt, vector_socket, scale, detail=2.0, distortion=0.0, roughness=0.5,
               dimensions="3D", w_socket=None, w_value=None):
    n = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(n, "noise_dimensions"):
        try:
            n.noise_dimensions = dimensions
        except TypeError:
            pass
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
    if w_socket is not None and "W" in n.inputs:
        nt.links.new(w_socket, n.inputs["W"])
    elif w_value is not None and "W" in n.inputs:
        n.inputs["W"].default_value = w_value
    return n

def _find_node(nt, bl_idname):
    return next((n for n in nt.nodes if n.bl_idname == bl_idname), None)

# --- Wood shader (faithfully ported from materials/wood/wood.py) ---

def make_wood(name="WoodMaterial"):
    """Faithful raw-bpy port of shader_wood.

    Uses MusgraveTexture substituted with 4D NoiseTexture (Musgrave removed
    in Blender 4.0+). The overall node graph structure is preserved.
    """

    color = get_wood_color()
    w = float(np.random.uniform(0, 1))

    mat = _new_material(name)
    nt = mat.node_tree

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    vec = tex_coord.outputs["Object"]

    # mapping_2:  Scale (5, 100, 100) -- stretches along X for wood grain
    mapping_2 = nt.nodes.new("ShaderNodeMapping")
    mapping_2.inputs["Scale"].default_value = (5.0, 100.0, 100.0)
    nt.links.new(vec, mapping_2.inputs["Vector"])

    # musgrave_texture_2 -> noise substitute (4D, Scale=10, Detail=15)
    musgrave_2 = _noise_tex(nt, mapping_2.outputs["Vector"], 10.0,
                            detail=15.0, dimensions="4D", w_value=w)

    map_range_2 = nt.nodes.new("ShaderNodeMapRange")
    map_range_2.inputs[3].default_value = 1.0   # From Min
    map_range_2.inputs[4].default_value = -1.0   # From Max
    nt.links.new(_noise_fac_output(musgrave_2), map_range_2.inputs[0])

    # mapping_1: identity mapping
    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(vec, mapping_1.inputs["Vector"])

    # noise_texture_1: 4D, Scale=0.5, Detail=1, Distortion=1.1
    noise_1 = _noise_tex(nt, mapping_1.outputs["Vector"], 0.5,
                         detail=1.0, distortion=1.1, dimensions="4D", w_value=w)

    # musgrave_texture_1 -> noise substitute (4D, Scale driven by noise_1 Fac)
    musgrave_1 = _noise_tex(nt, None, _noise_fac_output(noise_1),
                            detail=15.0, dimensions="4D", w_value=w)

    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[3].default_value = -1.4
    map_range.inputs[4].default_value = 1.5
    nt.links.new(_noise_fac_output(musgrave_1), map_range.inputs[0])

    map_range_1 = nt.nodes.new("ShaderNodeMapRange")
    map_range_1.inputs[3].default_value = 1.0
    map_range_1.inputs[4].default_value = 0.5
    nt.links.new(map_range.outputs["Result"], map_range_1.inputs[0])

    # mapping: Scale (0.15, 1, 0.15)
    mapping_0 = nt.nodes.new("ShaderNodeMapping")
    mapping_0.inputs["Scale"].default_value = (0.15, 1.0, 0.15)
    nt.links.new(vec, mapping_0.inputs["Vector"])

    # noise_texture: 4D, Detail=5, Distortion=1
    noise_0 = _noise_tex(nt, mapping_0.outputs["Vector"], 2.0,
                         detail=5.0, distortion=1.0, dimensions="4D", w_value=w)

    # musgrave_texture -> noise substitute (4D, Scale=4, Detail=10)
    musgrave_0 = _noise_tex(nt, _noise_fac_output(noise_0), 4.0,
                            detail=10.0, dimensions="4D", w_value=w)

    # mix: RGBA blend of noise_0 Fac and musgrave_0
    mix_0 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_0, "data_type"):
        mix_0.data_type = "RGBA"
    nt.links.new(_noise_fac_output(noise_0), mix_0.inputs[6])
    nt.links.new(_noise_fac_output(musgrave_0), mix_0.inputs[7])

    # mix_1: MULTIPLY, factor=0.9
    mix_1 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_1, "data_type"):
        mix_1.data_type = "RGBA"
    if hasattr(mix_1, "blend_type"):
        try:
            mix_1.blend_type = "MULTIPLY"
        except TypeError:
            pass
    mix_1.inputs[0].default_value = 0.9
    nt.links.new(map_range_1.outputs["Result"], mix_1.inputs[6])
    nt.links.new(mix_0.outputs[2], mix_1.inputs[7])

    # mix_2: MULTIPLY, factor=0.95
    mix_2 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_2, "data_type"):
        mix_2.data_type = "RGBA"
    if hasattr(mix_2, "blend_type"):
        try:
            mix_2.blend_type = "MULTIPLY"
        except TypeError:
            pass
    mix_2.inputs[0].default_value = 0.95
    nt.links.new(map_range_2.outputs["Result"], mix_2.inputs[6])
    nt.links.new(mix_1.outputs[2], mix_2.inputs[7])

    # hue_saturation_value
    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_node.inputs["Saturation"].default_value = 0.8
    hsv_node.inputs["Value"].default_value = 0.2
    hsv_node.inputs["Color"].default_value = color

    # mix_3: blend hue_sat and color using mix_2 as factor
    mix_3 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_3, "data_type"):
        mix_3.data_type = "RGBA"
    nt.links.new(mix_2.outputs[2], mix_3.inputs[0])
    nt.links.new(hsv_node.outputs["Color"], mix_3.inputs[6])
    mix_3.inputs[7].default_value = color

    # displacement
    disp_scale = _mat_log_uniform(0.0002, 0.01)
    multiply_disp = _math(nt, "MULTIPLY", mix_2.outputs[2])
    multiply_disp.inputs[1].default_value = disp_scale
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(multiply_disp.outputs[0], disp.inputs["Height"])

    # roughness: float curve over noise
    roughness_base = float(np.random.uniform(0.0, 0.4))
    roughness_high = roughness_base + float(np.random.uniform(0.0, 0.8))
    noise_rough = _noise_tex(nt, None, _mat_log_uniform(40, 50))
    fc = _build_float_curve(nt, _noise_fac_output(noise_rough),
                            [(0, roughness_base), (1, roughness_high)])

    # principled BSDF
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix_3.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(fc.outputs[0], bsdf.inputs["Roughness"])
    coat_weight = float(np.clip(np.random.uniform(0, 1.4), 0, 1))
    _set_principled(bsdf, **{"Coat Weight": coat_weight})

    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# --- wear_tear post-processing (scratches + edge_wear) ---
WEAR_TEAR_PROB = [0.5, 0.5]
SCRATCH_LABEL = "scratch"
EDGE_WEAR_LABEL = "wear_tear"

def get_scratch_params():
    return dict(
        angle1=float(np.random.uniform(10.0, 80.0)),
        angle2=float(np.random.uniform(-80.0, -10.0)),
        scratch_scale=_mat_log_uniform(5, 80),
        scratch_mask_ratio=_mat_log_uniform(0.01, 0.9),
        scratch_mask_noise=_mat_log_uniform(5, 40),
        scratch_depth=_mat_log_uniform(0.1, 1.0),
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
        except Exception as exc:
            print(f"  [scratches] failed on {mat.name}: {type(exc).__name__}: {exc}")

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
    if hasattr(mix, "clamp_result"):
        try:
            mix.clamp_result = True
        except TypeError:
            pass
    if hasattr(mix, "clamp_factor"):
        try:
            mix.clamp_factor = False
        except TypeError:
            pass
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
        except Exception as exc:
            print(f"  [edge_wear] failed on {mat.name}: {type(exc).__name__}: {exc}")

# --- Material assignment ---

def assign_material(obj, mat):
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)

# --- Seed materials (before geometry, so RNG state is correct) ---
seed_all(SEED)
WOOD_MAT = make_wood("Chopsticks_Wood")
_scratch_p, _edge_wear_p = WEAR_TEAR_PROB
WEAR_DO_SCRATCH = (np.random.uniform() <= _scratch_p)
WEAR_DO_EDGEWEAR = (np.random.uniform() <= _edge_wear_p)

# Reset geometry seed
np.random.seed(SEED)
random.seed(SEED)

# --- Geometry (copied from objects_blender/tableware/ChopsticksFactory.py) ---

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for c in list(bpy.data.curves):
        bpy.data.curves.remove(c)
    bpy.context.scene.cursor.location = (0, 0, 0)

def select_only(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

def apply_transform(obj, loc=False):
    select_only(obj)
    bpy.ops.object.transform_apply(location=loc, rotation=True, scale=True)

def modify_mesh(obj, mod_type, apply=True, **kwargs):
    select_only(obj)
    mod = obj.modifiers.new(name=mod_type, type=mod_type)
    for k, v in kwargs.items():
        setattr(mod, k, v)
    if apply:
        bpy.ops.object.modifier_apply(modifier=mod.name)

def write_co(obj, arr):
    obj.data.vertices.foreach_set('co', arr.reshape(-1))

def subsurf(obj, levels, simple=False):
    if levels > 0:
        modify_mesh(obj, 'SUBSURF',
                     levels=levels, render_levels=levels,
                     subdivision_type='SIMPLE' if simple else 'CATMULL_CLARK')

def new_grid(x_subdivisions=10, y_subdivisions=10):
    bpy.ops.mesh.primitive_grid_add(
        location=(0, 0, 0),
        x_subdivisions=x_subdivisions,
        y_subdivisions=y_subdivisions
    )
    obj = bpy.context.active_object
    apply_transform(obj, loc=True)
    return obj

def deep_clone(obj):
    select_only(obj)
    bpy.ops.object.duplicate()
    return bpy.context.active_object

def join_objects(objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.location = 0, 0, 0
    obj.rotation_euler = 0, 0, 0
    obj.scale = 1, 1, 1
    bpy.ops.object.select_all(action='DESELECT')
    return obj

def make_single(y_length, y_shrink, is_square, scale):
    n = int(1 / y_length)
    obj = new_grid(x_subdivisions=n - 1, y_subdivisions=1)
    modify_mesh(obj, 'SOLIDIFY', thickness=y_length * 2)
    l = np.linspace(y_shrink, 1, n) * y_length
    x = np.concatenate([np.linspace(0, 1, n)] * 4)
    y = np.concatenate([-l, l, -l, l])
    z = np.concatenate([l, l, -l, -l])
    write_co(obj, np.stack([x, y, z], -1))
    subsurf(obj, 2, is_square)
    obj.scale = [scale] * 3
    apply_transform(obj)
    return obj

def make_parallel(obj, y_length):
    distance = float(log_uniform(y_length, 0.04))
    if uniform(0, 1) < 0.5:
        other = deep_clone(obj)
        obj.location[1] = distance
        obj.rotation_euler[2] = uniform(0, np.pi / 8)
        other.location[1] = -distance
        other.rotation_euler[2] = -uniform(0, np.pi / 8)
    else:
        obj.location[0] = -1
        apply_transform(obj, loc=True)
        other = deep_clone(obj)
        obj.location[1] = distance
        obj.rotation_euler[2] = -uniform(0, np.pi / 8)
        other.location[1] = -distance
        other.rotation_euler[2] = uniform(0, np.pi / 8)
    return join_objects([obj, other])

def make_crossed(obj, y_length):
    other = deep_clone(obj)
    other.location = uniform(-0.1, 0.2), uniform(-0.2, 0.2), y_length
    sign = np.sign(other.location[1])
    other.rotation_euler[2] = -sign * float(log_uniform(np.pi / 8, np.pi / 4))
    return join_objects([obj, other])

def create_chopsticks():
    y_length = uniform(0.01, 0.02)
    y_shrink = float(log_uniform(0.2, 0.8))
    is_square = uniform(0, 1) < 0.5
    scale = float(log_uniform(0.2, 0.4))

    obj = make_single(y_length, y_shrink, is_square, scale)
    if uniform(0, 1) < 0.6:
        obj = make_parallel(obj, y_length)
    else:
        obj = make_crossed(obj, y_length)

    return obj

# --- Build ---

def build(seed):
    clear_scene()
    np.random.seed(seed)
    random.seed(seed)

    obj = create_chopsticks()
    obj.name = "ChopsticksFactory"

    # Assign wood material
    assign_material(obj, WOOD_MAT)

    # Apply wear_tear
    if WEAR_DO_SCRATCH:
        apply_scratches(obj)
    if WEAR_DO_EDGEWEAR:
        apply_edge_wear(obj)

    return obj

build(SEED)

