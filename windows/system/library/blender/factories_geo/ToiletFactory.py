# [FL_INDEX: keywords="blender_factory, procedural_3d, ToiletFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: ToiletFactory | Category: factories_geo
# Prompt: A 3D model of a standard floor-mounted toilet rendered from a three-quarter top angle. The toilet is all-white ceramic and consists of a round bowl with an open seat ring, an oval seat lid tilted upright, a rectangular water tank at the back with a flush handle on the side, and a round base connecting to the floor. The overall form is clean and modern with smooth porcelain-like shading.

import hashlib
import os

import bpy, bmesh
import numpy as np
import math, random, colorsys

def int_hash(x):
    m = hashlib.md5()
    for s in x:
        m.update(str(s).encode("utf-8"))
    return abs(int(m.hexdigest(), 16)) % (2**32 - 1)

# ============================================================================
# Inlined material library — ToiletFactory uses:
#   make_ceramic (ceramics: bowl/seat/cover/stand/back/tank)
#   make_metal_basic (metal_neutral: flush hardware)
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
    """Original uses MusgraveTexture (removed in Blender 5.0); we substitute NoiseTexture."""

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


# Registry — ToiletFactory uses ceramics (body) + metal_neutral (hardware)
metal_neutral = [(make_metal_basic, 1.0)]
ceramics = [(make_ceramic, 1.0)]
REGISTRY = {
    "metal_neutral": metal_neutral,
    "ceramics": ceramics,
}


def get_material(key, name=None):
    ctor = weighted_sample(REGISTRY[key])
    return ctor(name=name or key.title())


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

# ── seed & parameters ──────────────────────────────────────────────────────
factory_seed = int(os.environ.get("SEED", "0"))
instance_id = int(os.environ.get("INSTANCE_ID", str(factory_seed)))
np.random.seed(factory_seed)

size            = np.random.uniform(0.4,  0.5)
width           = size * np.random.uniform(0.7,  0.8)
height          = size * np.random.uniform(0.8,  0.9)
size_mid        = np.random.uniform(0.6,  0.65)
curve_scale     = np.exp(np.random.uniform(np.log(0.8), np.log(1.2), 4))
depth           = size * np.random.uniform(0.5,  0.6)
tube_scale      = np.random.uniform(0.25, 0.3)
thickness       = np.random.uniform(0.05, 0.06)
extrude_height  = np.random.uniform(0.015,0.02)
stand_depth     = depth * np.random.uniform(0.85,0.95)
stand_scale     = np.random.uniform(0.7,  0.85)
bottom_offset   = np.random.uniform(0.5,  1.5)
back_thickness  = thickness * np.random.uniform(0.0, 0.8)
back_size       = size * np.random.uniform(0.55, 0.65)
back_scale      = np.random.uniform(0.8,  1.0)
seat_thickness  = np.random.uniform(0.1,  0.3) * thickness
seat_size       = thickness * np.random.uniform(1.2, 1.6)
has_seat_cut    = np.random.uniform() < 0.1
tank_width      = width  * np.random.uniform(1.0, 1.2)
tank_height     = height * np.random.uniform(0.6, 1.0)
tank_size       = back_size - seat_size - np.random.uniform(0.02, 0.03)
tank_cap_height = np.random.uniform(0.03, 0.04)
tank_cap_extrude = 0.0 if np.random.uniform() < 0.5 else np.random.uniform(0.005, 0.01)
cover_rotation  = -np.random.uniform(0, np.pi / 2)
hardware_type   = np.random.choice(["button", "handle"])
hardware_cap    = np.random.uniform(0.01,  0.015)
hardware_radius = np.random.uniform(0.015, 0.02)
hardware_length = np.random.uniform(0.04,  0.05)
hardware_on_side = np.random.uniform() < 0.5
mid_offset      = (1 - size_mid) * size

#   surface (ceramics), hardware_surface (metal_neutral) + wear_tear gates
MAT_SURFACE  = get_material("ceramics", "ToiletSurface")
MAT_HARDWARE = get_material("metal_neutral", "ToiletHardware")
_scratch_p, _edge_wear_p = WEAR_TEAR_PROB
WEAR_DO_SCRATCH  = (np.random.uniform() <= _scratch_p)
WEAR_DO_EDGEWEAR = (np.random.uniform() <= _edge_wear_p)

# ── low-level helpers ──────────────────────────────────────────────────────
def read_co(o):
    a = np.zeros(len(o.data.vertices)*3)
    o.data.vertices.foreach_get("co", a)
    return a.reshape(-1, 3)

def write_co(o, a):
    o.data.vertices.foreach_set("co", a.reshape(-1))

def read_edges(o):
    a = np.zeros(len(o.data.edges)*2, int)
    o.data.edges.foreach_get("vertices", a)
    return a.reshape(-1, 2)

def read_ec(o):
    return read_co(o)[read_edges(o).reshape(-1)].reshape(-1, 2, 3).mean(1)

def read_fc(o):
    a = np.zeros(len(o.data.polygons)*3)
    o.data.polygons.foreach_get("center", a)
    return a.reshape(-1, 3)

def read_fn(o):
    a = np.zeros(len(o.data.polygons)*3)
    o.data.polygons.foreach_get("normal", a)
    return a.reshape(-1, 3)

def norm_vecs(v):
    r = v.copy(); n = np.linalg.norm(v, axis=-1)
    r[n > 0] /= n[n > 0, None]; return r


def sel_none():
    for o in list(bpy.context.selected_objects): o.select_set(False)
    if bpy.context.active_object: bpy.context.active_object.select_set(False)

def set_active(o):
    bpy.context.view_layer.objects.active = o; o.select_set(True)

def apply_tf(o, loc=False):
    sel_none(); set_active(o)
    bpy.ops.object.transform_apply(location=loc, rotation=True, scale=True)
    sel_none()

def clone(o):
    n = o.copy(); n.data = o.data.copy()
    for m in list(n.modifiers): n.modifiers.remove(m)
    bpy.context.scene.collection.objects.link(n); return n

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
    o.location = (0, 0, 0); o.rotation_euler = (0, 0, 0); o.scale = (1, 1, 1)
    sel_none(); return o

def sel_faces(o, mask):
    if callable(mask): x, y, z = read_fc(o).T; mask = mask(x, y, z)
    idx = np.nonzero(np.asarray(mask))[0]
    sel_none(); set_active(o)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type="FACE")
    bpy.ops.mesh.select_all(action="DESELECT")
    bm = bmesh.from_edit_mesh(o.data); bm.faces.ensure_lookup_table()
    for i in idx: bm.faces[i].select_set(True)
    bm.select_flush(False); bmesh.update_edit_mesh(o.data)
    bpy.ops.object.mode_set(mode='OBJECT')

def sel_edges(o, mask):
    idx = np.nonzero(np.asarray(mask))[0]
    sel_none(); set_active(o)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type="EDGE")
    bpy.ops.mesh.select_all(action="DESELECT")
    bm = bmesh.from_edit_mesh(o.data); bm.edges.ensure_lookup_table()
    for i in idx: bm.edges[i].select_set(True)
    bm.select_flush(False); bmesh.update_edit_mesh(o.data)
    bpy.ops.object.mode_set(mode='OBJECT')

def sel_verts(o, mask):
    if callable(mask): x, y, z = read_co(o).T; mask = mask(x, y, z)
    idx = np.nonzero(np.asarray(mask))[0]
    sel_none(); set_active(o)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type="VERT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bm = bmesh.from_edit_mesh(o.data); bm.verts.ensure_lookup_table()
    for i in idx: bm.verts[i].select_set(True)
    bm.select_flush(False); bmesh.update_edit_mesh(o.data)
    bpy.ops.object.mode_set(mode='OBJECT')

def new_cube():
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    return bpy.context.active_object

def new_cyl():
    bpy.ops.mesh.primitive_cylinder_add(location=(0, 0, 0.5), depth=1)
    o = bpy.context.active_object; apply_tf(o, True); return o

def subsurf(o, lvl, simple=False):
    mod(o, "SUBSURF", levels=lvl, render_levels=lvl,
        subdivision_type="SIMPLE" if simple else "CATMULL_CLARK")

# ── build_curve (bezier → aligned handles → convert to mesh → mirror) ───────
def build_curve():
    anchors = np.array([[0, width/2, 0],
                        [-size_mid*size, 0, mid_offset],
                        [0, 0, 0]], float)
    axes = [np.array([1,0,0]), np.array([0,1,0]), np.array([1,0,0])]

    bpy.ops.curve.primitive_bezier_curve_add(location=(0,0,0))
    o = bpy.context.active_object
    sel_none(); set_active(o)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.subdivide(number_cuts=1)  # 2→3 points
    bpy.ops.object.mode_set(mode='OBJECT')

    pts = o.data.splines[0].bezier_points
    for i in range(3): pts[i].co = anchors[:, i]
    for p in pts: p.handle_left_type = "AUTO"; p.handle_right_type = "AUTO"
    o.data.splines[0].resolution_u = 12

    # align handles onto their respective axes, scaled by curve_scale
    sc = [1, curve_scale[0], curve_scale[1], curve_scale[2], curve_scale[3], 1]
    for i, p in enumerate(pts):
        a = axes[i]
        p.handle_left_type = "FREE"; p.handle_right_type = "FREE"
        for side, idx in (('left', 2*i), ('right', 2*i+1)):
            h = np.array(getattr(p, 'handle_'+side) - p.co)
            proj = (h @ a) * a; np_ = np.linalg.norm(proj)
            if np_ > 1e-8:
                setattr(p, 'handle_'+side,
                        np.array(p.co) + proj/np_ * np.linalg.norm(h) * sc[idx])

    # curve2mesh: subdivide dense, convert, weld
    pts = o.data.splines[0].bezier_points
    cos = np.array([list(p.co) for p in pts])
    lengths = np.linalg.norm(cos[:-1] - cos[1:], axis=-1)
    sel_none(); set_active(o)
    bpy.ops.object.mode_set(mode='EDIT')
    for p in pts:
        if p.handle_left_type  == "FREE": p.handle_left_type  = "ALIGNED"
        if p.handle_right_type == "FREE": p.handle_right_type = "ALIGNED"
    for i in reversed(range(len(pts) - 1)):
        pts2 = list(o.data.splines[0].bezier_points)
        nc = min(int(lengths[i] / 5e-3) - 1, 64)
        if nc < 0: continue
        bpy.ops.curve.select_all(action="DESELECT")
        pts2[i].select_control_point = True
        pts2[i+1].select_control_point = True
        bpy.ops.curve.subdivide(number_cuts=nc)
    bpy.ops.object.mode_set(mode='OBJECT')
    o.data.splines[0].resolution_u = 1
    sel_none(); set_active(o); bpy.ops.object.convert(target="MESH")
    o = bpy.context.active_object
    mod(o, "WELD",   merge_threshold=1e-3)
    mod(o, "MIRROR", use_axis=(True, False, False))
    return o

# ── toilet build ─────────────────────────────────────────────────────────────
build_seed = int_hash((factory_seed, instance_id))
np.random.seed(build_seed)

upper = build_curve()

lower = clone(upper)
lower.scale    = [tube_scale] * 3
lower.location = (0, tube_scale * mid_offset / 2, -depth)
apply_tf(lower, True)

bottom = clone(upper)
bottom.scale    = [stand_scale] * 3
bottom.location = (0, tube_scale * mid_offset / 2 * bottom_offset, -height)
apply_tf(bottom, True)

# --- tube: bridge upper+lower loops, solidify, extrude top cap ---------------
obj = join([upper, lower])
sel_none(); set_active(obj)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_mode(type="EDGE")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.bridge_edge_loops(
    number_cuts=64, profile_shape_factor=np.random.uniform(0.1, 0.2), interpolation="SURFACE")
bpy.ops.object.mode_set(mode='OBJECT')
mod(obj, "SOLIDIFY", thickness=thickness, offset=1,
    solidify_mode="NON_MANIFOLD", nonmanifold_boundary_mode="FLAT")
sel_faces(obj, read_fn(obj)[:, 2] > 0.9)
sel_none(); set_active(obj)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.extrude_region_move(
    TRANSFORM_OT_translate={"value": (0, 0, thickness + extrude_height)})
bpy.ops.object.mode_set(mode='OBJECT')
x, y, z = read_co(obj).T
write_co(obj, np.stack([x, y, np.clip(z, None, extrude_height)], -1))

# --- seat plane: duplicate top faces, separate, extend back edge -------------
sel_faces(obj, lambda x, y, z: z > extrude_height * 2/3)
sel_none(); set_active(obj)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.duplicate_move()
bpy.ops.mesh.separate(type="SELECTED")
bpy.ops.object.mode_set(mode='OBJECT')
seat = next(o for o in bpy.context.selected_objects if o != obj)
sel_none()
sel_verts(seat, lambda x, y, z: y > mid_offset + seat_thickness)
sel_none(); set_active(seat)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.extrude_edges_move(
    TRANSFORM_OT_translate={"value": (0, seat_size + thickness*2, 0)})
bpy.ops.object.mode_set(mode='OBJECT')
xs, ys, zs = read_co(seat).T
write_co(seat, np.stack([xs, np.clip(ys, None, mid_offset + seat_size), zs], -1))

# --- seat lid (cover) --------------------------------------------------------
cover = clone(seat)

mod(seat, "SOLIDIFY", thickness=extrude_height, offset=1)
if has_seat_cut:
    cutter = new_cube()
    cutter.scale    = [thickness] * 3
    cutter.location = (0, -thickness/2 - size_mid*size, 0)
    apply_tf(cutter, True)
    sel_none()
    bm_ = seat.modifiers.new("BOOL", "BOOLEAN")
    bm_.object = cutter; bm_.operation = "DIFFERENCE"
    sel_none(); set_active(seat)
    bpy.ops.object.modifier_apply(modifier=bm_.name)
    sel_none(); set_active(cutter); bpy.ops.object.delete()
mod(seat, "BEVEL", segments=2)

xc, yc, _ = read_ec(cover).T
i = int(np.argmin(np.abs(xc) + np.abs(yc)))
sm = np.zeros(len(xc), bool); sm[i] = True
sel_edges(cover, sm)
sel_none(); set_active(cover)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.loop_multi_select()
bpy.ops.mesh.fill_grid()
bpy.ops.object.mode_set(mode='OBJECT')
mod(cover, "SOLIDIFY", thickness=extrude_height, offset=1)
cover.location = [0, -mid_offset - seat_size + extrude_height/2, -extrude_height/2]
apply_tf(cover, True)
cover.rotation_euler[0] = cover_rotation
cover.location = [0, mid_offset + seat_size - extrude_height/2, extrude_height*1.5]
apply_tf(cover, True)
mod(cover, "BEVEL", segments=2)

# --- stand: extract bottom edge loop, bridge with bottom disc ----------------
co_e = read_co(obj)[read_edges(obj).reshape(-1)].reshape(-1, 2, 3)
horiz = np.abs(norm_vecs(co_e[:, 0] - co_e[:, 1])[:, -1]) < 0.1
xe, ye, ze = read_ec(obj).T
ud = ze < -stand_depth
i = int(np.argmin(ye - horiz.astype(float) - ud.astype(float)))
sm = np.zeros(len(co_e), bool); sm[i] = True
sel_edges(obj, sm)
sel_none(); set_active(obj)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.loop_multi_select()
bpy.ops.mesh.duplicate_move()
bpy.ops.mesh.separate(type="SELECTED")
bpy.ops.object.mode_set(mode='OBJECT')
stand_loop = next(o for o in bpy.context.selected_objects if o != obj)
stand = join([stand_loop, bottom])
sel_none(); set_active(stand)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_mode(type="EDGE")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.bridge_edge_loops(number_cuts=64, profile_shape_factor=np.random.uniform(0.0, 0.15))
bpy.ops.object.mode_set(mode='OBJECT')

# --- back panel --------------------------------------------------------------
bk_mask  = read_fc(obj)[:, 1] > mid_offset - back_thickness
bk_face  = read_fn(obj)[:, 1] > 0.1
sel_none(); sel_faces(obj, bk_mask & bk_face)
sel_none(); set_active(obj)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.region_to_loop()
bpy.ops.mesh.duplicate_move()
bpy.ops.mesh.separate(type="SELECTED")
bpy.ops.object.mode_set(mode='OBJECT')
back = next(o for o in bpy.context.selected_objects if o != obj)
mod(back, "CORRECTIVE_SMOOTH")
sel_none(); set_active(back)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.mesh.extrude_edges_move(
    TRANSFORM_OT_translate={"value": (0, back_size + thickness*2, 0)})
bpy.ops.transform.resize(value=(back_scale, 1, 1))
bpy.ops.mesh.edge_face_add()
bpy.ops.object.mode_set(mode='OBJECT')
back.location[1] -= 0.01
apply_tf(back, True)
xb, yb, zb = read_co(back).T
write_co(back, np.stack([xb, np.clip(yb, None, mid_offset + back_size), zb], -1))

# --- tank + cap --------------------------------------------------------------
tank = new_cube()
tank.scale    = (tank_width/2, tank_size/2, tank_height/2)
tank.location = (0, mid_offset + back_size - tank_size/2, tank_height/2)
apply_tf(tank, True)
subsurf(tank, 2, True)
mod(tank, "BEVEL", segments=2)

cap = new_cube()
cap.scale    = (tank_width/2 + tank_cap_extrude,
                tank_size/2  + tank_cap_extrude,
                tank_cap_height/2)
cap.location = (0, mid_offset + back_size - tank_size/2, tank_height)
apply_tf(cap, True)
mod(cap, "BEVEL", width=np.random.uniform(0, extrude_height), segments=4)
tank = join([tank, cap])

# --- flush hardware ----------------------------------------------------------
if hardware_type == "button":
    hw = new_cyl()
    hw.scale    = (hardware_radius, hardware_radius, tank_cap_height/2 + 1e-3)
    hw.location = (0, mid_offset + back_size - tank_size/2, tank_height)
    apply_tf(hw, True)
else:
    hw = new_cyl()
    hw.scale = (hardware_radius, hardware_radius, hardware_cap)
    hw.rotation_euler[0] = np.pi / 2
    apply_tf(hw, True)

    lev = new_cyl()
    lev.scale = (hardware_radius/2, hardware_radius/2, hardware_length)
    lev.rotation_euler[1] = np.pi / 2
    lx, lz = np.random.uniform(0, 0.5), np.random.uniform(0, 0.5)
    lev.location = [-hardware_radius*lx, -hardware_cap, -hardware_radius*lz]
    apply_tf(lev, True)
    hw = join([hw, lev])

    if hardware_on_side:
        hx, hz = np.random.uniform(0.01, 0.02), np.random.uniform(0.02, 0.03)
        hw.location = [
            -tank_width/2 + hardware_radius + hx,
            mid_offset + back_size - tank_size,
            tank_height - hardware_radius - hz]
    else:
        hx, hz = np.random.uniform(0.01, 0.02), np.random.uniform(0.02, 0.03)
        hw.location = [
            -tank_width/2,
            mid_offset + back_size - tank_size + hardware_radius + hx,
            tank_height - hardware_radius - hz]
        hw.rotation_euler[-1] = -np.pi / 2
    apply_tf(hw, True)
    mod(hw, "BEVEL", width=np.random.uniform(0.005, 0.01), segments=2)

# --- bevel bowl, join all, orient --------------------------------------------
mod(obj, "BEVEL", segments=2)

# Per-part material assignment (must happen BEFORE join so slots survive):
#   obj (bowl), seat, cover, stand, back, tank -> ceramic surface
#   hw (flush hardware) -> metal
obj.data.materials.append(MAT_SURFACE)
seat.data.materials.append(MAT_SURFACE)
cover.data.materials.append(MAT_SURFACE)
stand.data.materials.append(MAT_SURFACE)
back.data.materials.append(MAT_SURFACE)
tank.data.materials.append(MAT_SURFACE)
hw.data.materials.append(MAT_HARDWARE)

toilet = join([obj, seat, cover, stand, back, tank, hw])
toilet.rotation_euler[-1] = np.pi / 2
sel_none(); set_active(toilet)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
sel_none()
toilet.name = "Toilet"

if WEAR_DO_SCRATCH:  apply_scratches(toilet)
if WEAR_DO_EDGEWEAR: apply_edge_wear(toilet)
