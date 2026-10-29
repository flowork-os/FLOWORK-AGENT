# [FL_INDEX: keywords="blender_factory, procedural_3d, StandingSinkFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: StandingSinkFactory | Category: factories_geo
# Prompt: A 3D model of a pedestal bathroom sink rendered from a three-quarter angle. The sink features a wide, slightly flared square basin with rounded corners in a dark forest-green glossy material with marble-like veining. A chrome gooseneck faucet with two handles is mounted at the back edge. The basin sits atop a central tapered pedestal column that widens at the square base, forming a classic freestanding sink silhouette.

import os

import bpy, bmesh
import numpy as np
import math, random, colorsys
import hashlib
import mathutils
import unicodedata

def int_hash(x):
    m = hashlib.md5()
    for s in x:
        m.update(str(s).encode("utf-8"))
    return abs(int(m.hexdigest(), 16)) % (2**32 - 1)

# ============================================================================
# Inlined material library — StandingSinkFactory uses:
#   make_ceramic + make_brushed_metal + make_metal_basic (bathroom_touchsurface)
#   wear_tear (scratches + edge_wear)
# ============================================================================

def hsv2rgba(hsv):
    h, s, v = hsv
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)


def log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))


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



def make_ceramic(name="Ceramic"):
    mat = _new_material(name)
    nt = mat.node_tree
    # 80% tinted color, 20% grayscale
    if np.random.uniform() < 0.8:
        color = hsv2rgba((np.random.uniform(0, 1),
                          np.random.uniform(0.2, 0.4),
                          log_uniform(0.3, 0.6)))
    else:
        color = hsv2rgba((0.0, 0.0, log_uniform(0.3, 0.6)))

    # Roughness from noise → float curve
    noise_r = nt.nodes.new("ShaderNodeTexNoise")
    noise_r.inputs["Scale"].default_value = log_uniform(20, 40)
    fc_r = _build_float_curve(nt, _noise_fac_output(noise_r), [(0, 0.0), (1, 0.8)])

    # Coat roughness from second noise → float curve
    noise_c = nt.nodes.new("ShaderNodeTexNoise")
    noise_c.inputs["Scale"].default_value = log_uniform(20, 40)
    fc_c = _build_float_curve(nt, _noise_fac_output(noise_c), [(0, 0.0), (1, 0.8)])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf,
        **{"Base Color": color, "Coat Weight": 1.0, "Specular IOR Level": 1.0,
           "Subsurface Weight": float(np.random.uniform(0.02, 0.05))},
    )
    nt.links.new(fc_r.outputs["Value"], bsdf.inputs["Roughness"])
    if "Coat Roughness" in bsdf.inputs:
        nt.links.new(fc_c.outputs["Value"], bsdf.inputs["Coat Roughness"])

    # Subtle displacement from a third noise
    noise_d = nt.nodes.new("ShaderNodeTexNoise")
    noise_d.inputs["Scale"].default_value = log_uniform(20, 40)
    mul_d = _math(nt, "MULTIPLY", _noise_fac_output(noise_d), log_uniform(0.001, 0.005))
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_d.outputs[0], disp.inputs["Height"])

    _connect_output(nt, bsdf, displacement=disp.outputs[0])
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
        try: noise2.noise_dimensions = "4D"
        except TypeError: pass
    noise2.inputs["Scale"].default_value = 100.0
    if "Detail" in noise2.inputs:     noise2.inputs["Detail"].default_value = 15.0
    if "Roughness" in noise2.inputs:  noise2.inputs["Roughness"].default_value = 0.4
    if "Distortion" in noise2.inputs: noise2.inputs["Distortion"].default_value = 0.1
    if "W" in noise2.inputs:          noise2.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
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


# Registry — StandingSinkFactory: bathroom_touchsurface + metal_neutral (tap)
metal_neutral = [(make_metal_basic, 1.0)]
bathroom_touchsurface = [
    (make_ceramic, 1.0),
    (make_brushed_metal, 0.1),
    (make_metal_basic, 0.1),
]
REGISTRY = {
    "metal_neutral": metal_neutral,
    "bathroom_touchsurface": bathroom_touchsurface,
}


# ---- wear_tear ------------------------------------------------------------
WEAR_TEAR_PROB = [0.5, 0.5]
SCRATCH_LABEL = "scratch"
EDGE_WEAR_LABEL = "wear_tear"


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
            e = elements.new(pos); e.color = color
    return cr


def _noise_tex(nt, vector_socket, scale, detail=2.0, distortion=0.0, roughness=0.5):
    n = nt.nodes.new("ShaderNodeTexNoise")
    if vector_socket is not None:
        nt.links.new(vector_socket, n.inputs["Vector"])
    if isinstance(scale, (int, float)):
        n.inputs["Scale"].default_value = float(scale)
    else:
        nt.links.new(scale, n.inputs["Scale"])
    if "Detail" in n.inputs:    n.inputs["Detail"].default_value = detail
    if "Distortion" in n.inputs:n.inputs["Distortion"].default_value = distortion
    if "Roughness" in n.inputs: n.inputs["Roughness"].default_value = roughness
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
# End of inlined material library
# ============================================================================

# bathroom_touchsurface registry weights: Ceramic=1.0, BrushedMetal=0.1, MetalBasic=0.1
_touchsurface_weights = np.array([1.0, 0.1, 0.1])
_touchsurface_weights = _touchsurface_weights / _touchsurface_weights.sum()

factory_seed = int(os.environ.get("SEED", 0))
instance_id = int(os.environ.get("SEED", str(factory_seed)))

# Approximate RNG consumed by BathroomSinkFactory.create_asset material setup
# before stand subdivision and faucet sampling.
material_rng_skip = 305

def consume_material_rng():
    for _ in range(material_rng_skip):
        np.random.uniform()

# ==============================================================================
# Extract inherited params: has_curve, disp_x, disp_y, hole_radius
# ==============================================================================
np.random.seed(factory_seed)
_bt_width     = np.random.uniform(1.5, 2.0)
_bt_size      = np.random.uniform(0.8, 1.0)
_bt_depth     = np.random.uniform(0.55, 0.7)
_bt_type      = np.random.choice(["alcove", "freestanding"], p=[0.5, 0.5])
_bt_has_base  = (_bt_type != "freestanding")
has_curve     = np.random.uniform() < 0.5       # needed for make_bowl
_             = np.random.uniform()               # has_legs
if _bt_has_base:
    _         = np.random.uniform(0.04, 0.08)     # thickness (alcove)
else:
    _         = np.random.uniform(0.02, 0.04)     # thickness (freestanding)
bt_disp_x     = np.random.uniform(0, 0.2, 2)
bt_disp_y     = np.random.uniform(0, 0.1)
_             = np.random.uniform(0.2, 0.3)       # leg_height
_             = np.random.uniform(0.05, 0.1)      # leg_side
_             = np.random.uniform(0.02, 0.03)     # leg_radius
_             = np.random.uniform()                # leg_y_scale
_             = np.random.randint(3)               # leg_subsurf_level
_             = np.random.uniform(-0.1, 0.1)      # taper_factor
_             = np.random.uniform(-0.2, 0.2)      # stretch_factor
if _bt_has_base:
    _         = np.random.randint(1, 3)            # alcove_levels (bathtub)
# levels=5, side_levels=2, is_hole_centered=False — no draws
hole_radius   = np.random.uniform(0.015, 0.02)    # from bathtub block

# ==============================================================================
# ==============================================================================
np.random.seed(factory_seed)
width         = np.random.uniform(0.6, 0.9)
size          = width * log_uniform(0.55, 0.8)
depth         = width * log_uniform(0.2, 0.4)
# contour_fn = make_box_contour (defined below)
sink_type     = np.random.choice(["undermount", "drop-in", "vessel"])

# Match block — conditional draws MUST be consumed to keep RNG aligned
if sink_type == "undermount":
    _sink_bt_type = "freestanding"
    _ = np.random.uniform()                        # has_extrude check
elif sink_type == "drop-in":
    _sink_bt_type = "alcove"
    # has_extrude = True, no draw
else:  # vessel
    _sink_bt_type = np.random.choice(["alcove", "freestanding"])
    _ = np.random.uniform()                        # has_extrude check

disp_x        = np.array([bt_disp_x[0], bt_disp_x[0]])
disp_y        = bt_disp_y
_al_r         = np.random.uniform()
alcove_levels = 0 if _al_r < 0.5 else np.random.randint(2, 4)
_sink_has_base = (_sink_bt_type != "freestanding")
if _sink_has_base:
    thickness = 0.01                               # no draw when has_base
else:
    thickness = np.random.uniform(0.01, 0.03)      # draw when freestanding
size_extrude  = np.random.uniform(0.2, 0.35)
tap_offset    = np.random.uniform(0.0, 0.05)
stand_radius  = width / 2 * log_uniform(0.15, 0.2)
_sb_r         = np.random.uniform()
stand_bottom  = width * log_uniform(0.2, 0.3) if _sb_r < 0.6 else stand_radius
stand_height  = np.random.uniform(0.7, 0.9) - depth
is_stand_circ = np.random.uniform() < 0.5
# is_hole_centered = True — no draw
# hole_radius is from BathtubFactory block (already set above)

material_idx  = int(np.random.choice(3, p=_touchsurface_weights))
# wear_tear gates
_scratch_p, _edge_wear_p = WEAR_TEAR_PROB
WEAR_DO_SCRATCH  = (np.random.uniform() <= _scratch_p)
WEAR_DO_EDGEWEAR = (np.random.uniform() <= _edge_wear_p)

# ==============================================================================
# ==============================================================================
bathtub_type  = "freestanding"
has_extrude   = True
has_stand     = True
has_base      = False
levels        = 5
side_levels   = 2

# ── helpers ──────────────────────────────────────────────────────────────────
def read_co(o):
    a = np.zeros(len(o.data.vertices)*3)
    o.data.vertices.foreach_get("co", a); return a.reshape(-1, 3)

def read_edges(o):
    a = np.zeros(len(o.data.edges)*2, int)
    o.data.edges.foreach_get("vertices", a); return a.reshape(-1, 2)

def read_fc(o):
    a = np.zeros(len(o.data.polygons)*3)
    o.data.polygons.foreach_get("center", a); return a.reshape(-1, 3)

def read_fn(o):
    a = np.zeros(len(o.data.polygons)*3)
    o.data.polygons.foreach_get("normal", a); return a.reshape(-1, 3)


def sel_none():
    for o in list(bpy.context.selected_objects): o.select_set(False)
    if bpy.context.active_object: bpy.context.active_object.select_set(False)

def set_active(o): bpy.context.view_layer.objects.active = o; o.select_set(True)

def apply_tf(o, loc=False):
    sel_none(); set_active(o)
    bpy.ops.object.transform_apply(location=loc, rotation=True, scale=True)
    sel_none()

def mod(o, t, **kw):
    m = o.modifiers.new(t, t)
    for k, v in kw.items(): setattr(m, k, v)
    sel_none(); set_active(o)
    bpy.ops.object.modifier_apply(modifier=m.name); sel_none()

def join(objs):
    if len(objs) == 1: return objs[0]
    sel_none()
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    o.location = (0,0,0); o.rotation_euler = (0,0,0); o.scale = (1,1,1)
    sel_none(); return o

def subsurf(o, lvl, simple=False):
    if lvl > 0:
        mod(o, "SUBSURF", levels=lvl, render_levels=lvl,
            subdivision_type="SIMPLE" if simple else "CATMULL_CLARK")

def new_cube():
    bpy.ops.mesh.primitive_cube_add(location=(0,0,0))
    return bpy.context.active_object

def new_cyl():
    bpy.ops.mesh.primitive_cylinder_add(location=(0,0,0.5), depth=1)
    o = bpy.context.active_object; apply_tf(o, True); return o

def new_base_cyl(**kw):
    bpy.ops.mesh.primitive_cylinder_add(**kw)
    o = bpy.context.active_object; apply_tf(o, True); return o

# ── box contour (BathtubFactory.make_box_contour) ────────────────────────────
def contour_fn(t, i):
    return [
        (t + disp_x[0]*i,          t + disp_y*i),
        (width - t - disp_x[1]*i,  t + disp_y*i),
        (width - t - disp_x[1]*i,  size - t - disp_y*i),
        (t + disp_x[0]*i,          size - t - disp_y*i),
    ]

def biring_obj(lower, upper, z0=0.0, z1=1.0):
    N = len(lower)
    verts = [(x,y,z0) for x,y in lower] + [(x,y,z1) for x,y in upper]
    faces = [(i,(i+1)%N, N+(i+1)%N, N+i) for i in range(N)]
    faces.append(list(range(N-1,-1,-1)))
    faces.append(list(range(N, 2*N)))
    mesh = bpy.data.meshes.new('sink')
    mesh.from_pydata(verts,[],faces); mesh.update()
    o = bpy.data.objects.new('sink', mesh)
    bpy.context.scene.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o
    sel_none(); o.select_set(True); return o

# ── geometry ─────────────────────────────────────────────────────────────────
def make_bowl():
    if has_curve:
        lower = contour_fn(0, 1)
        upper = contour_fn(0, -1)
    else:
        lower = contour_fn(0, 0)
        upper = contour_fn(0, 0)
    obj = biring_obj(lower[::-1], upper[::-1], 0.0, depth*2)
    subsurf(obj, alcove_levels, True)
    subsurf(obj, levels - alcove_levels - side_levels)
    return obj

def remove_top(obj):
    sel_none()
    sel_none(); set_active(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    geom = [f for f in bm.faces if f.calc_center_median()[-1] > depth]
    bmesh.ops.delete(bm, geom=geom, context="FACES_KEEP_BOUNDARY")
    bmesh.update_edit_mesh(obj.data)

    bpy.ops.object.mode_set(mode='OBJECT')
def find_hole(obj, x=None, y=None):
    if x is None: x = width / 2
    if y is None: y = size  / 2
    up = read_fn(obj)[:, -1] > 0
    fc = read_fc(obj)
    i = np.argmin(np.abs(fc[:,:2] - np.array([[x,y]])).sum(1) - up)
    return fc[i]

def add_hole(obj):
    # Original BathtubFactory.add_hole for freestanding draws uniform(0.35, 0.4)*width
    # for the x position, but is_hole_centered=True overrides it to centered.
    # We must consume the draw to maintain RNG alignment.
    _ = np.random.uniform(0.35, 0.4)
    loc = find_hole(obj)
    h = new_cyl()
    h.scale = (hole_radius, hole_radius, 0.005)
    h.location = tuple(loc); apply_tf(h, True)
    return h

def extrude_back(obj):
    sel_none(); set_active(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type="FACE")
    bpy.ops.mesh.select_all(action="DESELECT")
    bm = bmesh.from_edit_mesh(obj.data)
    for f in bm.faces:
        f.select_set(bool(f.calc_center_median()[1] > size / 2 and f.normal[1] > 0.1))
    bm.select_flush(False); bmesh.update_edit_mesh(obj.data)
    bpy.ops.mesh.extrude_region_move(
        TRANSFORM_OT_translate={"value": (0, size_extrude * size, 0)})

    bpy.ops.object.mode_set(mode='OBJECT')
def subdiv_edge_ring(o, cuts, axis=(0,0,1)):
    co = read_co(o); ev = read_edges(o)
    dirs = co[ev[:,1]] - co[ev[:,0]]
    n = np.linalg.norm(dirs, axis=-1, keepdims=True)
    dirs = np.where(n > 1e-8, dirs/n, dirs)
    ax = np.array(axis)
    sel = np.abs((dirs * ax).sum(1)) > 1 - 1e-3
    sel_none(); set_active(o)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(o.data); bm.edges.ensure_lookup_table()
    es = [bm.edges[i] for i in np.nonzero(sel)[0]]
    bmesh.ops.subdivide_edgering(bm, edges=es, cuts=int(cuts))
    bmesh.update_edit_mesh(o.data)

    bpy.ops.object.mode_set(mode='OBJECT')
def add_stand(obj):
    """Pedestal stand — always present for StandingSinkFactory."""

    if is_stand_circ:
        stand = new_base_cyl(vertices=16)
    else:
        stand = new_cube()
    stand.scale = (stand_radius, stand_radius, stand_height / 2)
    stand.location = (width/2, size/2, -stand_height/2)
    apply_tf(stand, True)
    subdiv_edge_ring(stand, np.random.randint(3, 6))
    sel_none(); set_active(stand)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type="FACE")
    bm = bmesh.from_edit_mesh(stand.data)
    for f in bm.faces: f.select_set(f.normal[-1] < -0.1)
    bm.select_flush(False); bmesh.update_edit_mesh(stand.data)
    bpy.ops.transform.resize(value=(
        stand_bottom / stand_radius,
        stand_bottom / stand_radius, 1))
    bpy.ops.object.mode_set(mode='OBJECT')
    subsurf(stand, 2, True); subsurf(stand, 1)
    return join([obj, stand])

# ==============================================================================
# Tap — geometry node tree recreation (nodegroup_handle + nodegroup_water_tap)
# ==============================================================================

def _set_rotation(node, euler_xyz):
    """Set rotation on a GeometryNodeTransform, handling Blender 4.x Rotation socket."""

    rot_input = node.inputs["Rotation"]
    try:
        rot_input.default_value = mathutils.Euler(euler_xyz)
    except TypeError:
        try:
            rot_input.default_value = euler_xyz
        except Exception:
            pass

def _normalize_enum_token(value):
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.replace("_", "").replace("-", "").replace(" ", "").lower()

def _resolve_enum_value(owner, attr_name, value):
    try:
        enum_items = owner.bl_rna.properties[attr_name].enum_items
    except Exception:
        return value
    wanted = _normalize_enum_token(value)
    for item in enum_items:
        choices = [item.identifier, item.name]
        for choice in choices:
            if _normalize_enum_token(choice) == wanted:
                return choice
    return value

def _set_enum_with_fallback(target, attr_name, value):
    """Set an enum value, trying common casing variants if the original fails.
    Blender 5.0 changed many enum identifiers from UPPER_CASE to TitleCase."""

    candidates_to_try = [value, value.title(), value.capitalize()]
    seen = set()
    for v in candidates_to_try:
        if v in seen:
            continue
        seen.add(v)
        try:
            setattr(target, attr_name, v)
            return
        except TypeError:
            continue
    # Last resort: raise with the original value
    setattr(target, attr_name, value)

def _set_node_enum(node, value, *candidates):
    """Set enum-like node properties across Blender API variants."""

    props = {p.identifier for p in node.bl_rna.properties}
    for name in candidates:
        if name in props:
            resolved = _resolve_enum_value(node, name, value)
            try:
                setattr(node, name, resolved)
            except TypeError:
                _set_enum_with_fallback(node, name, value)
            return
    for socket_name in candidates:
        socket = node.inputs.get(socket_name)
        if socket is not None:
            resolved = _resolve_enum_value(socket, "default_value", value)
            try:
                socket.default_value = resolved
            except TypeError:
                _set_enum_with_fallback(socket, "default_value", value)
            return
    raise AttributeError(
        f"Could not set enum {value!r} on {node.bl_idname}; tried {candidates}"
    )

def create_handle_nodegroup():
    """Create curved L-shaped handle geometry node tree (sink.py:192-283)."""

    tree = bpy.data.node_groups.new("nodegroup_handle", "GeometryNodeTree")
    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    L = tree.links

    out = tree.nodes.new("NodeGroupOutput")
    out.is_active_output = True

    bezier = tree.nodes.new("GeometryNodeCurvePrimitiveBezierSegment")
    bezier.inputs["Start"].default_value = (0, 0, 0)
    bezier.inputs["Start Handle"].default_value = (0, 0, 0.7)
    bezier.inputs["End Handle"].default_value = (0.2, 0, 0.7)
    bezier.inputs["End"].default_value = (1, 0, 0.9)
    bezier.inputs["Resolution"].default_value = 24

    sparam = tree.nodes.new("GeometryNodeSplineParameter")
    fcurve = tree.nodes.new("ShaderNodeFloatCurve")
    c = fcurve.mapping.curves[0]
    c.points[0].location = (0.0, 0.70)
    c.points[1].location = (1.0, 0.1625)
    fcurve.mapping.update()

    mul = tree.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 1.0

    set_rad = tree.nodes.new("GeometryNodeSetCurveRadius")

    profile = tree.nodes.new("GeometryNodeCurvePrimitiveCircle")
    profile.inputs["Radius"].default_value = 0.15
    c2m = tree.nodes.new("GeometryNodeCurveToMesh")
    c2m.inputs["Fill Caps"].default_value = True

    pos = tree.nodes.new("GeometryNodeInputPosition")
    sep = tree.nodes.new("ShaderNodeSeparateXYZ")
    mrange = tree.nodes.new("ShaderNodeMapRange")
    mrange.inputs[1].default_value = 0.2
    # inputs[2] (From Max) stays at default 1.0
    mrange.inputs[3].default_value = 1.0
    mrange.inputs[4].default_value = 1.8

    mul_y = tree.nodes.new("ShaderNodeMath")
    mul_y.operation = "MULTIPLY"
    comb = tree.nodes.new("ShaderNodeCombineXYZ")
    setpos = tree.nodes.new("GeometryNodeSetPosition")

    subdiv = tree.nodes.new("GeometryNodeSubdivisionSurface")
    subdiv.inputs["Level"].default_value = 2
    smooth = tree.nodes.new("GeometryNodeSetShadeSmooth")

    L.new(sparam.outputs["Factor"], fcurve.inputs["Value"])
    L.new(fcurve.outputs["Value"], mul.inputs[0])
    L.new(bezier.outputs["Curve"], set_rad.inputs["Curve"])
    L.new(mul.outputs["Value"], set_rad.inputs["Radius"])
    L.new(set_rad.outputs["Curve"], c2m.inputs["Curve"])
    L.new(profile.outputs["Curve"], c2m.inputs["Profile Curve"])
    L.new(mul.outputs["Value"], c2m.inputs["Scale"])  # Blender 5.0: SetCurveRadius no longer affects CurveToMesh
    L.new(pos.outputs["Position"], sep.inputs["Vector"])
    L.new(sep.outputs["X"], mrange.inputs[0])
    L.new(sep.outputs["Y"], mul_y.inputs[0])
    L.new(mrange.outputs[0], mul_y.inputs[1])
    L.new(sep.outputs["X"], comb.inputs["X"])
    L.new(mul_y.outputs["Value"], comb.inputs["Y"])
    L.new(sep.outputs["Z"], comb.inputs["Z"])
    L.new(c2m.outputs["Mesh"], setpos.inputs["Geometry"])
    L.new(comb.outputs["Vector"], setpos.inputs["Position"])
    L.new(setpos.outputs["Geometry"], subdiv.inputs["Mesh"])
    L.new(subdiv.outputs["Mesh"], smooth.inputs["Geometry"])
    L.new(smooth.outputs["Geometry"], out.inputs["Geometry"])

    return tree

def create_water_tap_nodegroup(params, handle_ng):
    """Create the full water tap geometry node tree (sink.py:285-897)."""

    tree = bpy.data.node_groups.new("nodegroup_water_tap", "GeometryNodeTree")
    L = tree.links

    float_params = ["base_width", "tap_head", "roation_z", "tap_height",
                    "base_radius", "Y", "hands_length_x", "hands_length_Y"]
    bool_params  = ["Switch", "hand_type", "one_side", "different_type", "length_one_side"]

    for name in float_params:
        s = tree.interface.new_socket(name, in_out="INPUT", socket_type="NodeSocketFloat")
        s.default_value = params[name]
    for name in bool_params:
        s = tree.interface.new_socket(name, in_out="INPUT", socket_type="NodeSocketBool")
        s.default_value = params[name]
    tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")

    gi = tree.nodes.new("NodeGroupInput")
    out = tree.nodes.new("NodeGroupOutput")
    out.is_active_output = True

    # Section C: Neck pipe
    curve_line = tree.nodes.new("GeometryNodeCurvePrimitiveLine")
    curve_line.inputs["End"].default_value = (0, 0, 0.6)
    neck_profile = tree.nodes.new("GeometryNodeCurvePrimitiveCircle")
    neck_profile.inputs["Radius"].default_value = 0.03
    neck_mesh = tree.nodes.new("GeometryNodeCurveToMesh")
    L.new(curve_line.outputs["Curve"], neck_mesh.inputs["Curve"])
    L.new(neck_profile.outputs["Curve"], neck_mesh.inputs["Profile Curve"])

    # Section D: Spout circle variant
    spout_circle = tree.nodes.new("GeometryNodeCurvePrimitiveCircle")
    spout_circle.inputs["Radius"].default_value = 0.2
    spout_tf1 = tree.nodes.new("GeometryNodeTransform")
    spout_tf1.inputs["Translation"].default_value = (0, 0.2, 0)
    spout_tf2 = tree.nodes.new("GeometryNodeTransform")
    _set_rotation(spout_tf2, (-1.5708, 1.5708, 0))
    spout_tf2.inputs["Scale"].default_value = (1, 0.7, 1)
    L.new(spout_circle.outputs["Curve"], spout_tf1.inputs["Geometry"])
    L.new(spout_tf1.outputs["Geometry"], spout_tf2.inputs["Geometry"])

    # Section E: Spout bezier variant
    comb_end_handle = tree.nodes.new("ShaderNodeCombineXYZ")
    comb_end_handle.inputs["X"].default_value = 0.2
    L.new(gi.outputs["Y"], comb_end_handle.inputs["Y"])
    spout_bezier = tree.nodes.new("GeometryNodeCurvePrimitiveBezierSegment")
    spout_bezier.inputs["Resolution"].default_value = 177
    spout_bezier.inputs["Start"].default_value = (0, 0, 0)
    spout_bezier.inputs["Start Handle"].default_value = (0, 1.2, 0)
    spout_bezier.inputs["End"].default_value = (-0.05, 0.1, 0)
    L.new(comb_end_handle.outputs["Vector"], spout_bezier.inputs["End Handle"])
    trim = tree.nodes.new("GeometryNodeTrimCurve")
    trim.inputs[3].default_value = 0.6625
    L.new(spout_bezier.outputs["Curve"], trim.inputs["Curve"])
    spout_bezier_tf = tree.nodes.new("GeometryNodeTransform")
    _set_rotation(spout_bezier_tf, (1.5708, 0, 2.522))
    spout_bezier_tf.inputs["Scale"].default_value = (5.2, 0.5, 7.8)
    L.new(trim.outputs["Curve"], spout_bezier_tf.inputs["Geometry"])
    spout_bezier_profile = tree.nodes.new("GeometryNodeCurvePrimitiveCircle")
    spout_bezier_profile.inputs["Radius"].default_value = 0.03
    spout_bezier_mesh = tree.nodes.new("GeometryNodeCurveToMesh")
    L.new(spout_bezier_tf.outputs["Geometry"], spout_bezier_mesh.inputs["Curve"])
    L.new(spout_bezier_profile.outputs["Curve"], spout_bezier_mesh.inputs["Profile Curve"])

    # Section F: Spout switch
    spout_switch = tree.nodes.new("GeometryNodeSwitch")
    L.new(gi.outputs["Switch"], spout_switch.inputs[0])
    L.new(spout_tf2.outputs["Geometry"], spout_switch.inputs[1])
    L.new(spout_bezier_mesh.outputs["Mesh"], spout_switch.inputs[2])
    spout_mesh = tree.nodes.new("GeometryNodeCurveToMesh")
    L.new(spout_switch.outputs[0], spout_mesh.inputs["Curve"])
    L.new(neck_profile.outputs["Curve"], spout_mesh.inputs["Profile Curve"])
    pos_f = tree.nodes.new("GeometryNodeInputPosition")
    sep_f = tree.nodes.new("ShaderNodeSeparateXYZ")
    L.new(pos_f.outputs["Position"], sep_f.inputs["Vector"])
    gt = tree.nodes.new("ShaderNodeMath")
    gt.operation = "GREATER_THAN"
    gt.inputs[1].default_value = -0.01
    L.new(sep_f.outputs["Z"], gt.inputs[0])
    filter_switch = tree.nodes.new("GeometryNodeSwitch")
    filter_switch.input_type = "FLOAT"
    L.new(gi.outputs["Switch"], filter_switch.inputs[0])
    L.new(gt.outputs["Value"], filter_switch.inputs[1])
    filter_switch.inputs[2].default_value = 1.0
    sep_geom = tree.nodes.new("GeometryNodeSeparateGeometry")
    L.new(spout_mesh.outputs["Mesh"], sep_geom.inputs["Geometry"])
    L.new(filter_switch.outputs[0], sep_geom.inputs["Selection"])
    comb_head_scale = tree.nodes.new("ShaderNodeCombineXYZ")
    comb_head_scale.inputs["X"].default_value = 1.0
    comb_head_scale.inputs["Y"].default_value = 1.0
    L.new(gi.outputs["tap_head"], comb_head_scale.inputs["Z"])
    head_scale_switch = tree.nodes.new("GeometryNodeSwitch")
    head_scale_switch.input_type = "VECTOR"
    L.new(gi.outputs["Switch"], head_scale_switch.inputs[0])
    L.new(comb_head_scale.outputs["Vector"], head_scale_switch.inputs[1])
    head_scale_switch.inputs[2].default_value = (1, 1, 1)
    spout_head_tf = tree.nodes.new("GeometryNodeTransform")
    spout_head_tf.inputs["Translation"].default_value = (0, 0, 0.6)
    L.new(sep_geom.outputs["Selection"], spout_head_tf.inputs["Geometry"])
    L.new(head_scale_switch.outputs[0], spout_head_tf.inputs["Scale"])

    # Section G: Neck + spout assembly
    neck_spout_join = tree.nodes.new("GeometryNodeJoinGeometry")
    L.new(neck_mesh.outputs["Mesh"], neck_spout_join.inputs["Geometry"])
    L.new(spout_head_tf.outputs["Geometry"], neck_spout_join.inputs["Geometry"])
    comb_rot_z = tree.nodes.new("ShaderNodeCombineXYZ")
    L.new(gi.outputs["roation_z"], comb_rot_z.inputs["Z"])
    comb_scale_h = tree.nodes.new("ShaderNodeCombineXYZ")
    comb_scale_h.inputs["X"].default_value = 1.0
    comb_scale_h.inputs["Y"].default_value = 1.0
    L.new(gi.outputs["tap_height"], comb_scale_h.inputs["Z"])
    euler_to_rot = tree.nodes.new("FunctionNodeEulerToRotation")
    L.new(comb_rot_z.outputs["Vector"], euler_to_rot.inputs[0])
    assembly_tf = tree.nodes.new("GeometryNodeTransform")
    L.new(neck_spout_join.outputs["Geometry"], assembly_tf.inputs["Geometry"])
    L.new(euler_to_rot.outputs[0], assembly_tf.inputs["Rotation"])
    L.new(comb_scale_h.outputs["Vector"], assembly_tf.inputs["Scale"])

    # Section H: Handles — curved type
    handle_node = tree.nodes.new("GeometryNodeGroup")
    handle_node.node_tree = handle_ng
    handle_left = tree.nodes.new("GeometryNodeTransform")
    handle_left.inputs["Translation"].default_value = (0, -0.2, 0)
    _set_rotation(handle_left, (0, 0, 3.6652))
    handle_left.inputs["Scale"].default_value = (0.3, 0.3, 0.3)
    L.new(handle_node.outputs[0], handle_left.inputs["Geometry"])
    handle_right = tree.nodes.new("GeometryNodeTransform")
    handle_right.inputs["Translation"].default_value = (0, 0.2, 0)
    _set_rotation(handle_right, (0, 0, 2.618))
    handle_right.inputs["Scale"].default_value = (0.3, 0.3, 0.3)
    L.new(handle_node.outputs[0], handle_right.inputs["Geometry"])
    curved_handles_join = tree.nodes.new("GeometryNodeJoinGeometry")
    L.new(handle_left.outputs["Geometry"], curved_handles_join.inputs["Geometry"])
    L.new(handle_right.outputs["Geometry"], curved_handles_join.inputs["Geometry"])

    # Section I: Handles — cylinder type
    crossbar = tree.nodes.new("GeometryNodeMeshCylinder")
    crossbar.inputs["Vertices"].default_value = 41
    crossbar.inputs["Side Segments"].default_value = 39
    crossbar.inputs["Radius"].default_value = 0.03
    crossbar.inputs["Depth"].default_value = 0.1
    crossbar_right = tree.nodes.new("GeometryNodeTransform")
    crossbar_right.inputs["Translation"].default_value = (0, 0.05, 0.1)
    _set_rotation(crossbar_right, (1.5708, 0, 0))
    L.new(crossbar.outputs["Mesh"], crossbar_right.inputs["Geometry"])
    crossbar_right_sw = tree.nodes.new("GeometryNodeSwitch")
    L.new(gi.outputs["one_side"], crossbar_right_sw.inputs[0])
    L.new(crossbar_right.outputs["Geometry"], crossbar_right_sw.inputs[1])
    crossbar_left = tree.nodes.new("GeometryNodeTransform")
    crossbar_left.inputs["Translation"].default_value = (0, -0.05, 0.1)
    _set_rotation(crossbar_left, (1.5708, 0, 0))
    L.new(crossbar.outputs["Mesh"], crossbar_left.inputs["Geometry"])
    crossbars_join = tree.nodes.new("GeometryNodeJoinGeometry")
    L.new(crossbar_right_sw.outputs[0], crossbars_join.inputs["Geometry"])
    L.new(crossbar_left.outputs["Geometry"], crossbars_join.inputs["Geometry"])
    rod = tree.nodes.new("GeometryNodeMeshCylinder")
    rod.inputs["Vertices"].default_value = 41
    rod.inputs["Side Segments"].default_value = 39
    rod.inputs["Radius"].default_value = 0.005
    rod.inputs["Depth"].default_value = 0.1
    rod_right = tree.nodes.new("GeometryNodeTransform")
    rod_right.inputs["Translation"].default_value = (0, 0.08, 0.15)
    rod_right.inputs["Scale"].default_value = (1, 1, 1.1)
    L.new(rod.outputs["Mesh"], rod_right.inputs["Geometry"])
    rod_right_sw = tree.nodes.new("GeometryNodeSwitch")
    L.new(gi.outputs["one_side"], rod_right_sw.inputs[0])
    L.new(rod_right.outputs["Geometry"], rod_right_sw.inputs[1])
    rod_left = tree.nodes.new("GeometryNodeTransform")
    rod_left.inputs["Translation"].default_value = (0, -0.08, 0.15)
    _set_rotation(rod_left, (0, 0, 0.0855))
    rod_left.inputs["Scale"].default_value = (1, 1, 1.1)
    L.new(rod.outputs["Mesh"], rod_left.inputs["Geometry"])
    rod_left_long = tree.nodes.new("GeometryNodeTransform")
    rod_left_long.inputs["Translation"].default_value = (0, -0.01, -0.005)
    rod_left_long.inputs["Scale"].default_value = (4.1, 1, 1)
    L.new(rod_left.outputs["Geometry"], rod_left_long.inputs["Geometry"])
    rod_left_len_sw = tree.nodes.new("GeometryNodeSwitch")
    L.new(gi.outputs["length_one_side"], rod_left_len_sw.inputs[0])
    L.new(rod_left.outputs["Geometry"], rod_left_len_sw.inputs[1])
    L.new(rod_left_long.outputs["Geometry"], rod_left_len_sw.inputs[2])
    rod_left_side_sw = tree.nodes.new("GeometryNodeSwitch")
    L.new(gi.outputs["one_side"], rod_left_side_sw.inputs[0])
    L.new(rod_left.outputs["Geometry"], rod_left_side_sw.inputs[1])
    L.new(rod_left_len_sw.outputs[0], rod_left_side_sw.inputs[2])
    rods_join = tree.nodes.new("GeometryNodeJoinGeometry")
    L.new(rod_right_sw.outputs[0], rods_join.inputs["Geometry"])
    L.new(rod_left_side_sw.outputs[0], rods_join.inputs["Geometry"])
    cyl_handles_join = tree.nodes.new("GeometryNodeJoinGeometry")
    L.new(crossbars_join.outputs["Geometry"], cyl_handles_join.inputs["Geometry"])
    L.new(rods_join.outputs["Geometry"], cyl_handles_join.inputs["Geometry"])
    comb_hand_scale = tree.nodes.new("ShaderNodeCombineXYZ")
    comb_hand_scale.inputs["Z"].default_value = 1.0
    L.new(gi.outputs["hands_length_x"], comb_hand_scale.inputs["X"])
    L.new(gi.outputs["hands_length_Y"], comb_hand_scale.inputs["Y"])
    cyl_handles_tf = tree.nodes.new("GeometryNodeTransform")
    L.new(cyl_handles_join.outputs["Geometry"], cyl_handles_tf.inputs["Geometry"])
    L.new(comb_hand_scale.outputs["Vector"], cyl_handles_tf.inputs["Scale"])

    # Section J: Handle type switch
    handle_switch = tree.nodes.new("GeometryNodeSwitch")
    L.new(gi.outputs["hand_type"], handle_switch.inputs[0])
    L.new(curved_handles_join.outputs["Geometry"], handle_switch.inputs[1])
    L.new(cyl_handles_tf.outputs["Geometry"], handle_switch.inputs[2])

    # Section K: Internal base cylinder
    base_circle = tree.nodes.new("GeometryNodeCurvePrimitiveCircle")
    base_circle.inputs["Radius"].default_value = 0.05
    base_fill = tree.nodes.new("GeometryNodeFillCurve")
    L.new(base_circle.outputs["Curve"], base_fill.inputs["Curve"])
    base_extrude = tree.nodes.new("GeometryNodeExtrudeMesh")
    base_extrude.inputs["Offset Scale"].default_value = 0.15
    L.new(base_fill.outputs["Mesh"], base_extrude.inputs["Mesh"])

    # Main assembly join
    main_join = tree.nodes.new("GeometryNodeJoinGeometry")
    L.new(assembly_tf.outputs["Geometry"], main_join.inputs["Geometry"])
    L.new(handle_switch.outputs[0], main_join.inputs["Geometry"])
    L.new(base_extrude.outputs["Mesh"], main_join.inputs["Geometry"])

    # Section L: Alternative "different_type" design
    alt_bezier = tree.nodes.new("GeometryNodeCurvePrimitiveBezierSegment")
    alt_bezier.inputs["Resolution"].default_value = 54
    alt_bezier.inputs["Start"].default_value = (0, 0, 0)
    alt_bezier.inputs["Start Handle"].default_value = (0, 0, 0.7)
    alt_bezier.inputs["End Handle"].default_value = (0.2, 0, 0.7)
    alt_bezier.inputs["End"].default_value = (1, 0, 0.9)
    alt_sparam = tree.nodes.new("GeometryNodeSplineParameter")
    alt_fcurve = tree.nodes.new("ShaderNodeFloatCurve")
    ac = alt_fcurve.mapping.curves[0]
    ac.points[0].location = (0.0, 0.70)
    ac.points[1].location = (1.0, 0.1625)
    ac.points.new(0.6295, 0.4125)
    alt_fcurve.mapping.update()
    alt_mul = tree.nodes.new("ShaderNodeMath")
    alt_mul.operation = "MULTIPLY"
    alt_mul.inputs[1].default_value = 1.0
    alt_set_rad = tree.nodes.new("GeometryNodeSetCurveRadius")
    alt_profile = tree.nodes.new("GeometryNodeCurvePrimitiveCircle")
    alt_profile.inputs["Radius"].default_value = 0.1
    alt_c2m = tree.nodes.new("GeometryNodeCurveToMesh")
    alt_c2m.inputs["Fill Caps"].default_value = True
    alt_pos = tree.nodes.new("GeometryNodeInputPosition")
    alt_sep = tree.nodes.new("ShaderNodeSeparateXYZ")
    alt_mrange = tree.nodes.new("ShaderNodeMapRange")
    alt_mrange.inputs[1].default_value = 0.2
    # inputs[2] (From Max) stays at default 1.0
    alt_mrange.inputs[3].default_value = 1.0
    alt_mrange.inputs[4].default_value = 1.8
    alt_mul_y = tree.nodes.new("ShaderNodeMath")
    alt_mul_y.operation = "MULTIPLY"
    alt_comb = tree.nodes.new("ShaderNodeCombineXYZ")
    alt_setpos = tree.nodes.new("GeometryNodeSetPosition")
    alt_subdiv = tree.nodes.new("GeometryNodeSubdivisionSurface")
    alt_subdiv.inputs["Level"].default_value = 1
    alt_smooth = tree.nodes.new("GeometryNodeSetShadeSmooth")
    alt_body_tf = tree.nodes.new("GeometryNodeTransform")
    alt_body_tf.inputs["Translation"].default_value = (0, 0, 0.1)
    _set_rotation(alt_body_tf, (0, 0, 0.6807))
    alt_body_tf.inputs["Scale"].default_value = (0.4, 0.4, 0.3)
    L.new(alt_sparam.outputs["Factor"], alt_fcurve.inputs["Value"])
    L.new(alt_fcurve.outputs["Value"], alt_mul.inputs[0])
    L.new(alt_bezier.outputs["Curve"], alt_set_rad.inputs["Curve"])
    L.new(alt_mul.outputs["Value"], alt_set_rad.inputs["Radius"])
    L.new(alt_set_rad.outputs["Curve"], alt_c2m.inputs["Curve"])
    L.new(alt_profile.outputs["Curve"], alt_c2m.inputs["Profile Curve"])
    L.new(alt_mul.outputs["Value"], alt_c2m.inputs["Scale"])  # Blender 5.0: SetCurveRadius no longer affects CurveToMesh
    L.new(alt_pos.outputs["Position"], alt_sep.inputs["Vector"])
    L.new(alt_sep.outputs["X"], alt_mrange.inputs[0])
    L.new(alt_sep.outputs["Y"], alt_mul_y.inputs[0])
    L.new(alt_mrange.outputs[0], alt_mul_y.inputs[1])
    L.new(alt_sep.outputs["X"], alt_comb.inputs["X"])
    L.new(alt_mul_y.outputs["Value"], alt_comb.inputs["Y"])
    L.new(alt_sep.outputs["Z"], alt_comb.inputs["Z"])
    L.new(alt_c2m.outputs["Mesh"], alt_setpos.inputs["Geometry"])
    L.new(alt_comb.outputs["Vector"], alt_setpos.inputs["Position"])
    L.new(alt_setpos.outputs["Geometry"], alt_subdiv.inputs["Mesh"])
    L.new(alt_subdiv.outputs["Mesh"], alt_smooth.inputs["Geometry"])
    L.new(alt_smooth.outputs["Geometry"], alt_body_tf.inputs["Geometry"])
    alt_base_circle = tree.nodes.new("GeometryNodeCurvePrimitiveCircle")
    alt_base_circle.inputs["Resolution"].default_value = 307
    alt_base_circle.inputs["Radius"].default_value = 0.055
    alt_base_fill = tree.nodes.new("GeometryNodeFillCurve")
    L.new(alt_base_circle.outputs["Curve"], alt_base_fill.inputs["Curve"])
    alt_base_extrude = tree.nodes.new("GeometryNodeExtrudeMesh")
    alt_base_extrude.inputs["Offset Scale"].default_value = 0.15
    L.new(alt_base_fill.outputs["Mesh"], alt_base_extrude.inputs["Mesh"])
    alt_stem = tree.nodes.new("GeometryNodeMeshCylinder")
    alt_stem.inputs["Vertices"].default_value = 100
    alt_stem.inputs["Radius"].default_value = 0.01
    alt_stem.inputs["Depth"].default_value = 0.7
    alt_stem_setpos = tree.nodes.new("GeometryNodeSetPosition")
    L.new(alt_stem.outputs["Mesh"], alt_stem_setpos.inputs["Geometry"])
    alt_stem_tf = tree.nodes.new("GeometryNodeTransform")
    alt_stem_tf.inputs["Translation"].default_value = (0.3, 0, 0.25)
    _set_rotation(alt_stem_tf, (0, -2.042, 0))
    alt_stem_tf.inputs["Scale"].default_value = (1.7, 3.1, 1)
    L.new(alt_stem_setpos.outputs["Geometry"], alt_stem_tf.inputs["Geometry"])
    alt_nozzle = tree.nodes.new("GeometryNodeMeshCylinder")
    alt_nozzle.inputs["Vertices"].default_value = 318
    alt_nozzle.inputs["Radius"].default_value = 0.02
    alt_nozzle.inputs["Depth"].default_value = 0.03
    alt_nozzle_tf = tree.nodes.new("GeometryNodeTransform")
    alt_nozzle_tf.inputs["Translation"].default_value = (0.595, 0, 0.38)
    L.new(alt_nozzle.outputs["Mesh"], alt_nozzle_tf.inputs["Geometry"])
    alt_stem_join = tree.nodes.new("GeometryNodeJoinGeometry")
    L.new(alt_stem_tf.outputs["Geometry"], alt_stem_join.inputs["Geometry"])
    L.new(alt_nozzle_tf.outputs["Geometry"], alt_stem_join.inputs["Geometry"])
    alt_stem_scale = tree.nodes.new("GeometryNodeTransform")
    alt_stem_scale.inputs["Scale"].default_value = (0.9, 1, 1)
    L.new(alt_stem_join.outputs["Geometry"], alt_stem_scale.inputs["Geometry"])
    alt_join = tree.nodes.new("GeometryNodeJoinGeometry")
    L.new(alt_body_tf.outputs["Geometry"], alt_join.inputs["Geometry"])
    L.new(alt_base_extrude.outputs["Mesh"], alt_join.inputs["Geometry"])
    L.new(alt_stem_scale.outputs["Geometry"], alt_join.inputs["Geometry"])
    alt_rotate = tree.nodes.new("GeometryNodeTransform")
    _set_rotation(alt_rotate, (0, 0, 3.1416))
    L.new(alt_join.outputs["Geometry"], alt_rotate.inputs["Geometry"])

    # Section M: Design switch
    design_switch = tree.nodes.new("GeometryNodeSwitch")
    L.new(gi.outputs["different_type"], design_switch.inputs[0])
    L.new(main_join.outputs["Geometry"], design_switch.inputs[1])
    L.new(alt_rotate.outputs["Geometry"], design_switch.inputs[2])

    # Section N: Parametric base plate
    base_quad = tree.nodes.new("GeometryNodeCurvePrimitiveQuadrilateral")
    base_quad.inputs["Height"].default_value = 0.7
    L.new(gi.outputs["base_width"], base_quad.inputs["Width"])
    base_fillet = tree.nodes.new("GeometryNodeFilletCurve")
    _set_node_enum(base_fillet, "POLY", "mode", "fillet_mode", "Mode")
    base_fillet.inputs["Count"].default_value = 19
    L.new(base_quad.outputs["Curve"], base_fillet.inputs["Curve"])
    L.new(gi.outputs["base_radius"], base_fillet.inputs["Radius"])
    base_plate_fill = tree.nodes.new("GeometryNodeFillCurve")
    L.new(base_fillet.outputs["Curve"], base_plate_fill.inputs["Curve"])
    base_plate_extrude = tree.nodes.new("GeometryNodeExtrudeMesh")
    base_plate_extrude.inputs["Offset Scale"].default_value = 0.05
    L.new(base_plate_fill.outputs["Mesh"], base_plate_extrude.inputs["Mesh"])

    # Final join
    final_join = tree.nodes.new("GeometryNodeJoinGeometry")
    L.new(design_switch.outputs[0], final_join.inputs["Geometry"])
    L.new(base_plate_extrude.outputs["Mesh"], final_join.inputs["Geometry"])
    L.new(final_join.outputs["Geometry"], out.inputs["Geometry"])

    return tree

def generate_tap_params(seed):
    """Generate tap shape parameters from seed (replicates U() calls in expose_input)."""

    state = np.random.get_state()
    np.random.seed(seed)
    params = {
        "base_width":      np.random.uniform(0.2, 0.3),
        "tap_head":        np.random.uniform(0.7, 1.1),
        "roation_z":       np.random.uniform(5.5, 7.0),
        "tap_height":      np.random.uniform(0.5, 1.0),
        "base_radius":     np.random.uniform(0.0, 0.1),
        "Switch":          bool(np.random.uniform() > 0.5),
        "Y":               np.random.uniform(-0.5, -0.06),
        "hand_type":       bool(np.random.uniform() > 0.2),
        "hands_length_x":  np.random.uniform(0.75, 1.25),
        "hands_length_Y":  np.random.uniform(0.95, 1.55),
        "one_side":        bool(np.random.uniform() > 0.5),
        "different_type":  bool(np.random.uniform() > 0.8),
        "length_one_side": bool(np.random.uniform() > 0.8),
    }
    np.random.set_state(state)
    return params

def standing_sink_tap_params(seed):
    params = generate_tap_params(seed)
    # Lock the faucet to the fuller arched branch used by the reference render.
    # Leaving these floats fully random often yields a very small deck plate and
    # subtle side hardware, which makes the faucet look missing in practice.
    params.update({
        "base_width": 0.29,
        "tap_head": 1.00,
        "roation_z": 6.05,
        "tap_height": 0.95,
        "base_radius": 0.075,
        "Y": -0.22,
        "hands_length_x": 1.00,
        "hands_length_Y": 1.05,
        "Switch": False,
        "hand_type": False,
        "one_side": False,
        "different_type": False,
        "length_one_side": False,
    })
    return params

def make_tap(tap_seed=None, tap_params=None):
    """Create tap/faucet using geometry nodes, matching TapFactory.create_asset."""

    if tap_params is None:
        if tap_seed is None:
            raise ValueError("Either tap_seed or tap_params must be provided")
        params = generate_tap_params(tap_seed)
    else:
        params = dict(tap_params)
    handle_ng = create_handle_nodegroup()
    tap_ng = create_water_tap_nodegroup(params, handle_ng)

    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    obj = bpy.context.active_object
    m = obj.modifiers.new("GeometryNodes", "NODES")
    m.node_group = tap_ng
    sel_none(); set_active(obj)
    bpy.ops.object.modifier_apply(modifier=m.name)
    sel_none()

    obj.scale = (0.4, 0.4, 0.4)
    obj.rotation_euler.z += np.pi
    apply_tf(obj, True)
    return obj

# ==============================================================================
# Build (replicate BathroomSinkFactory.create_asset)
# ==============================================================================
build_seed = int_hash((factory_seed, instance_id))
np.random.seed(build_seed)
# Build the actual material (replaces consume_material_rng's 305-call dummy)
if material_idx == 0:
    MAT_SURFACE = make_ceramic("StandingSinkSurface")
elif material_idx == 1:
    MAT_SURFACE = make_brushed_metal("StandingSinkSurface")
else:
    MAT_SURFACE = make_metal_basic("StandingSinkSurface")

obj = make_bowl()
remove_top(obj)
mod(obj, "SOLIDIFY", thickness=thickness)
subsurf(obj, side_levels)

obj.location = np.array(obj.location) - np.min(read_co(obj), 0)
apply_tf(obj, True)
dims = np.array(obj.dimensions)
obj.scale = np.array([width, size, depth]) / np.where(dims > 1e-6, dims, 1.0)
apply_tf(obj, True)

# Always extrude back (has_extrude = True)
extrude_back(obj)

# Always add pedestal stand (has_stand = True)
obj = add_stand(obj)

# Build geometry first; defer material slot assignment until after the final join
# (boolean / SOLIDIFY ops leave behind stale empty slots if we attach materials early).
hole = add_hole(obj)
obj  = join([obj, hole])
obj.rotation_euler[-1] = np.pi / 2
apply_tf(obj, True)

# Snapshot polygon count of body+hole before tap is appended.
_n_body_polys = len(obj.data.polygons)

# Tap faucet — full geometry node-based implementation
tap_instance = int(np.random.randint(1e7))
tap = make_tap(
    tap_params=standing_sink_tap_params(int_hash((factory_seed, tap_instance)))
)
min_x = np.min(read_co(tap)[:, 0])
tap.location = (
    (-1 - size_extrude + tap_offset) * size - min_x,
    width / 2,
    depth)
apply_tf(tap, True)
obj = join([obj, tap])

obj.name = "StandingSink"

# === Clean material slot assignment ====================================
# Wipe stale empty slots and rebuild deterministically: [SURFACE, TAP].
obj.data.materials.clear()
obj.data.materials.append(MAT_SURFACE)
MAT_TAP = make_metal_basic("StandingSinkTap")
obj.data.materials.append(MAT_TAP)
for i, p in enumerate(obj.data.polygons):
    p.material_index = 1 if i >= _n_body_polys else 0

if WEAR_DO_SCRATCH:  apply_scratches(obj)
if WEAR_DO_EDGEWEAR: apply_edge_wear(obj)
