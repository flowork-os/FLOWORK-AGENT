# [FL_INDEX: keywords="blender_factory, procedural_3d, BathtubFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: BathtubFactory | Category: factories_tex
# Prompt: A 3D model of a freestanding soaking bathtub rendered from a three-quarter top-down angle. The bathtub is all-white with a smooth, organically curved oval form. The outer body has a subtly textured hammered surface, and the inner bowl is glossy and smooth. A wide flat rim surrounds the top edge. The tub sits on a flat oval platform base, giving it a modern freestanding appearance.

factory_seed = 0
instance_id = 0

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

# Inlined material library -- BathtubFactory uses:
#   make_metal_basic (metal_neutral: legs + hole)
#   make_ceramic (ceramics: bathtub surface)
#   wear_tear (scratches + edge_wear)

def seed_all(seed):
    np.random.seed(seed)
    random.seed(seed)

def hsv2rgba(hsv):
    h, s, v = hsv
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

def log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def metal_hsv():
    
    if np.random.uniform() < 0.2:
        return (np.random.uniform(0, 1),
                np.random.uniform(0.0, 0.2),
                log_uniform(0.05, 0.3))
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

    # Roughness from noise -> float curve
    noise_r = nt.nodes.new("ShaderNodeTexNoise")
    noise_r.inputs["Scale"].default_value = log_uniform(20, 40)
    fc_r = _build_float_curve(nt, _noise_fac_output(noise_r), [(0, 0.0), (1, 0.8)])

    # Coat roughness from second noise -> float curve
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

# Registry -- BathtubFactory uses metal_neutral (legs, hole) + ceramics (surface)
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

# End of inlined material library

# ── clear default scene ───────────────────────────────────────────────────
for _obj in list(bpy.data.objects):
    bpy.data.objects.remove(_obj, do_unlink=True)
for _mesh in list(bpy.data.meshes):
    bpy.data.meshes.remove(_mesh)

# ── seed & parameters ──────────────────────────────────────────────────────
np.random.seed(factory_seed)

width         = np.random.uniform(1.5,  2.0)
size          = np.random.uniform(0.8,  1.0)
depth         = np.random.uniform(0.55, 0.7)
bathtub_type  = np.random.choice(["alcove", "freestanding"], p=[0.5, 0.5])
has_curve     = np.random.uniform() < 0.5
has_legs      = np.random.uniform() < 0.5
has_base      = bathtub_type != "freestanding"
thickness     = np.random.uniform(0.04, 0.08) if has_base else np.random.uniform(0.02, 0.04)
disp_x        = np.random.uniform(0, 0.2, 2)
disp_y        = np.random.uniform(0, 0.1)
leg_height    = np.random.uniform(0.2, 0.3) * depth
leg_side      = np.random.uniform(0.05, 0.1)
leg_radius    = np.random.uniform(0.02, 0.03)
leg_y_scale   = np.random.uniform()
leg_ss_level  = np.random.randint(3)
taper_factor  = np.random.uniform(-0.1, 0.1)
stretch_factor = np.random.uniform(-0.2, 0.2)  # drawn but unused (matches original RNG state)
alcove_levels = np.random.randint(1, 3) if has_base else 1
levels        = 5
side_levels   = 2
hole_radius   = np.random.uniform(0.015, 0.02)
# BevelSharp amount
bevel_amount  = np.random.uniform(0.001, 0.006)

# Material sampling -- continues consuming factory_seed RNG, mirroring
# BathtubFactory.__init__ which samples:
#   surface (ceramics), leg_surface (metal_neutral), hole_surface (metal_neutral)
#   + wear_tear gates, all inside `with FixedSeed(factory_seed):`
MAT_SURFACE = get_material("ceramics", "BathtubSurface")
MAT_LEG     = get_material("metal_neutral", "BathtubLeg")
MAT_HOLE    = get_material("metal_neutral", "BathtubHole")
_scratch_p, _edge_wear_p = WEAR_TEAR_PROB
WEAR_DO_SCRATCH  = (np.random.uniform() <= _scratch_p)
WEAR_DO_EDGEWEAR = (np.random.uniform() <= _edge_wear_p)

# ── helpers ────────────────────────────────────────────────────────────────
def read_co(o):
    a = np.zeros(len(o.data.vertices)*3)
    o.data.vertices.foreach_get("co", a); return a.reshape(-1,3)

def write_co(o, a): o.data.vertices.foreach_set("co", a.reshape(-1))

def read_fc(o):
    a = np.zeros(len(o.data.polygons)*3)
    o.data.polygons.foreach_get("center", a); return a.reshape(-1,3)

def read_fn(o):
    a = np.zeros(len(o.data.polygons)*3)
    o.data.polygons.foreach_get("normal", a); return a.reshape(-1,3)

def sel_none():
    for o in list(bpy.context.selected_objects): o.select_set(False)
    if bpy.context.active_object: bpy.context.active_object.select_set(False)

def set_active(o): bpy.context.view_layer.objects.active = o; o.select_set(True)

def apply_tf(o, loc=False):
    sel_none(); set_active(o)
    bpy.ops.object.transform_apply(location=loc, rotation=True, scale=True)
    sel_none()

def clone(o):
    n = o.copy(); n.data = o.data.copy()
    for m in list(n.modifiers): n.modifiers.remove(m)
    bpy.context.collection.objects.link(n); return n

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
    bpy.ops.mesh.primitive_cube_add(location=(0,0,0.5))
    o = bpy.context.active_object
    apply_tf(o, True)
    return o

def new_cyl_n(N):
    """Cylinder with N-sided profile, bottom at z=0, top at z=1 in local space."""

    bpy.ops.mesh.primitive_cylinder_add(vertices=N, location=(0,0,0.5), depth=1)
    o = bpy.context.active_object; apply_tf(o, True); return o

def new_cyl():
    bpy.ops.mesh.primitive_cylinder_add(location=(0,0,0.5), depth=1)
    o = bpy.context.active_object; apply_tf(o, True); return o

def mesh_obj(vertices=(), edges=(), faces=(), name=""):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(list(vertices), list(edges), list(faces))
    mesh.update()
    obj = bpy.data.objects.new(name or "mesh", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    return obj

def new_line(subdivisions=1, scale=1.0):
    verts = np.stack([
        np.linspace(0, scale, subdivisions + 1),
        np.zeros(subdivisions + 1),
        np.zeros(subdivisions + 1),
    ], -1)
    edges = np.stack([np.arange(subdivisions), np.arange(1, subdivisions + 1)], -1)
    obj = mesh_obj(verts, edges, name="line")
    sel_none(); obj.select_set(True)
    return obj

# ── contour functions ──────────────────────────────────────────────────────
def make_box_contour(t, i):
    return [
        (t + disp_x[0]*i,         t + disp_y*i),
        (width - t - disp_x[1]*i, t + disp_y*i),
        (width - t - disp_x[1]*i, size - t - disp_y*i),
        (t + disp_x[0]*i,         size - t - disp_y*i),
    ]

contour_fn = make_box_contour   # (corner type not in [alcove, freestanding])

def contour_cylinder(lower, upper, z0=0.0, z1=1.0):
    obj = new_cyl_n(len(lower))
    co = np.concatenate([
        np.array([[x, y, z0], [u, v, z1]])
        for (x, y), (u, v) in zip(lower, upper)
    ])
    write_co(obj, co)
    return obj

# ── geometry builders ──────────────────────────────────────────────────────
def make_base():
    c = contour_fn(0, 0)
    return contour_cylinder(c, c, 0.0, depth)

def make_bowl():
    if has_curve:
        lower = contour_fn(0, 1)
        upper = contour_fn(0, -1)
    else:
        lower = contour_fn(0, 0)
        upper = contour_fn(0, 0)
    obj = contour_cylinder(lower[::-1], upper[::-1], 0.0, depth*2)
    subsurf(obj, alcove_levels, True)
    subsurf(obj, levels - alcove_levels - side_levels)
    return obj

def make_cutter():
    if has_curve:
        lower = contour_fn(thickness, 1)
        upper = contour_fn(thickness, -1)
    else:
        lower = contour_fn(thickness, 0)
        upper = contour_fn(thickness, 0)
    obj = contour_cylinder(lower[::-1], upper[::-1], thickness, depth*2 - thickness)
    subsurf(obj, alcove_levels, True)
    subsurf(obj, levels - alcove_levels)
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
def make_freestanding():
    obj = make_bowl()
    remove_top(obj)
    sel_none(); set_active(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type="EDGE")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.region_to_loop()
    bpy.ops.mesh.extrude_edges_move()
    bpy.ops.transform.resize(value=(
        1 + thickness*2 / width,
        1 + thickness   / size,
        1))
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.location[1] -= size / 2
    apply_tf(obj, True)
    mod(obj, "SIMPLE_DEFORM", deform_method="TAPER",   angle=taper_factor)
    mod(obj, "SIMPLE_DEFORM", deform_method="STRETCH",  angle=taper_factor)
    z_min = np.min(read_co(obj)[:, -1])
    obj.location = (0, size/2, -z_min * np.random.uniform(0.5, 0.7))
    apply_tf(obj, True)
    return obj

def line_to_tube(obj, radius, profile_resolution=32):
    """profile_resolution = number of vertices around the tube cross-section.
    Blender's bevel_resolution is subdivisions per quarter, so we convert."""

    sel_none(); set_active(obj)
    bpy.ops.object.convert(target="CURVE")
    obj = bpy.context.active_object
    obj.data.dimensions = "3D"
    obj.data.resolution_u = 1
    obj.data.render_resolution_u = 1
    obj.data.bevel_depth = radius
    # bevel_resolution = subdivisions per quarter circle
    # profile_resolution = total vertices around circle
    # so bevel_resolution = max(1, profile_resolution // 4)
    obj.data.bevel_resolution = max(1, profile_resolution // 4)
    obj.data.use_fill_caps = True
    bpy.ops.object.convert(target="MESH")
    return bpy.context.active_object

def make_legs(obj):
    legs = []
    fc = read_fc(obj); fn = read_fn(obj)
    x, y, z = fc.T
    z_min = np.min(z); z_thresh = z_min + leg_height
    for u in [1, -1]:
        for v in [1, -1]:
            metric = np.where(z < z_thresh, u*x + v*y, -np.inf)
            i = np.argmax(metric)
            p = fc[i]; n = fn[i]
            q = p + leg_side * np.array([n[0], n[1]*leg_y_scale, n[2]])
            r = np.array([q[0], q[1], 0.0])
            leg = new_line(2)
            write_co(leg, np.stack([p, q, r]))
            subsurf(leg, leg_ss_level)
            leg = line_to_tube(leg, leg_radius, profile_resolution=32)
            mod(leg, "BEVEL", width=leg_radius * np.random.uniform(0.3, 0.7))
            leg.location[-1] = leg_radius
            apply_tf(leg, True)
            legs.append(leg)
    return legs

def add_base_platform(obj_ref):
    """Flat base for freestanding tub without legs."""

    obj2 = clone(obj_ref)
    x_, y_, z_ = read_co(obj2).T
    cutter = new_cube()
    cutter.scale = (10, 10, np.min(z_) + leg_height)
    apply_tf(cutter, True)
    bm_ = obj2.modifiers.new("BI", "BOOLEAN")
    bm_.object = cutter; bm_.operation = "INTERSECT"
    sel_none(); set_active(obj2)
    bpy.ops.object.modifier_apply(modifier=bm_.name); sel_none()
    sel_none(); set_active(cutter); bpy.ops.object.delete()
    sel_none(); set_active(obj2)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj2.data)
    geom = [f for f in bm.faces if len(f.verts) > 10]
    bmesh.ops.delete(bm, geom=geom, context="FACES_KEEP_BOUNDARY")
    bmesh.update_edit_mesh(obj2.data)
    bpy.ops.mesh.select_mode(type="EDGE")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.region_to_loop()
    bpy.ops.mesh.select_all(action="INVERT")
    bpy.ops.mesh.delete(type="EDGE")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.extrude_edges_move(
        TRANSFORM_OT_translate={"value": (0, 0, -depth)})
    bpy.ops.object.mode_set(mode='OBJECT')
    x, y, z = read_co(obj2).T
    write_co(obj2, np.stack([x, y, np.clip(z, 0, None)], -1))
    sel_none(); set_active(obj2)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    subsurf(obj2, 2)
    mod(obj2, "SOLIDIFY", thickness=thickness)
    return obj2

def find_hole(obj, x=None, y=None):
    if x is None: x = width / 2
    if y is None: y = size  / 2
    up = read_fn(obj)[:, -1] > 0
    fc = read_fc(obj)
    i = np.argmin(np.abs(fc[:, :2] - np.array([[x, y]])).sum(1) - up)
    return fc[i]

def add_hole(obj):
    if bathtub_type == "alcove":
        loc = find_hole(obj)
    elif bathtub_type == "freestanding":
        loc = find_hole(obj, np.random.uniform(0.35, 0.4) * width)
    else:
        loc = find_hole(obj, size/2, size/2)
    h = new_cyl()
    h.scale = (hole_radius, hole_radius, 0.005)
    h.location = tuple(loc)
    apply_tf(h, True)
    return h

# ── build ──────────────────────────────────────────────────────────────────
build_seed = int_hash((factory_seed, instance_id))
np.random.seed(build_seed)

# --- Build geometry, snapshotting polygon ranges per part ---
# The key insight: we MUST snapshot AFTER the SOLIDIFY+subsurf modifiers (which
# add polys to the body) but BEFORE we join in the legs/platform parts.
# Material indices are then assigned BEFORE the final BEVEL/SUBSURF operations
# so they're inherited correctly by any new polygons those modifiers create.
_has_legs_section = False

if has_base:
    obj = make_base()
    cutter = make_cutter()
    bm_ = obj.modifiers.new("BD", "BOOLEAN")
    bm_.object = cutter; bm_.operation = "DIFFERENCE"
    sel_none(); set_active(obj); bpy.ops.object.modifier_apply(modifier=bm_.name); sel_none()
    sel_none(); set_active(cutter); bpy.ops.object.delete()
    _n_body_polys_pre_legs = len(obj.data.polygons)  # alcove has no legs
else:
    obj = make_freestanding()
    parts = [obj]
    if has_legs:
        legs = make_legs(obj)
        parts.extend(legs)
    else:
        platform = add_base_platform(obj)
        parts.append(platform)
    mod(obj, "SOLIDIFY", thickness=thickness)
    subsurf(obj, side_levels)
    # SNAPSHOT after SOLIDIFY+subsurf inflated body poly count, before join
    _n_body_polys_pre_legs = len(obj.data.polygons)
    obj = join(parts)
    _has_legs_section = True

# SNAPSHOT after legs/platform joined, before hole
_n_body_polys_pre_hole = len(obj.data.polygons)

hole = add_hole(obj)
obj = join([obj, hole])

# --- Clean material slot assignment (BEFORE final SUBSURF/bevel ops) ---
# Final SUBSURF/bevel below will inherit material_index from source polys.
obj.data.materials.clear()
obj.data.materials.append(MAT_SURFACE)
obj.data.materials.append(MAT_LEG)
obj.data.materials.append(MAT_HOLE)
SURF_IDX, LEG_IDX, HOLE_IDX = 0, 1, 2

if _has_legs_section:
    leg_start = _n_body_polys_pre_legs
else:
    leg_start = _n_body_polys_pre_hole  # no legs -> empty leg range

for i, p in enumerate(obj.data.polygons):
    if i >= _n_body_polys_pre_hole:
        p.material_index = HOLE_IDX
    elif i >= leg_start:
        p.material_index = LEG_IDX
    else:
        p.material_index = SURF_IDX

# --- Final orient + finishing modifiers (inherit material_index) ---
obj.rotation_euler[-1] = np.pi / 2
apply_tf(obj, True)

if bathtub_type == "freestanding":
    mod(obj, "SUBSURF", levels=1, render_levels=1)
else:
    # BevelSharp: bevel edges sharper than 70°
    sel_none(); set_active(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.tris_convert_to_quads()
    bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type="EDGE")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.mesh.edges_select_sharp(sharpness=np.deg2rad(70))
    bpy.ops.mesh.bevel(offset=bevel_amount * 5, segments=5,
                       affect="EDGES", offset_type="WIDTH")
    bpy.ops.object.mode_set(mode='OBJECT')
    sel_none()

obj.name = "Bathtub"

if WEAR_DO_SCRATCH:  apply_scratches(obj)
if WEAR_DO_EDGEWEAR: apply_edge_wear(obj)

