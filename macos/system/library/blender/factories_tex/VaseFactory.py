# [FL_INDEX: keywords="blender_factory, procedural_3d, VaseFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: VaseFactory | Category: factories_tex
# Prompt: A 3D model of a decorative vase with a wide bulbous body and a narrower flared opening at the top, rendered from a slightly elevated three-quarter perspective. The vase features vertical fluted ridges running along its rounded body, a scalloped decorative base with a rough ornamental ring, and a gently flared rim at the top with a semi-transparent glass-like appearance.

factory_seed = 0

import hashlib
import os

import bpy
import numpy as np
import math, random, colorsys

def int_hash(x):
    m = hashlib.md5()
    for s in x:
        m.update(str(s).encode("utf-8"))
    return abs(int(m.hexdigest(), 16)) % (2**32 - 1)

# Inlined material library — VaseFactory uses:
#   Material from marble + tableware registry:
#     marble: make_marble(1.0), make_marble_regular(0.2), make_marble_voronoi(0.2)
#     tableware: make_ceramic(1.0), make_glass(1.0), make_plastic(1.0),
#                make_metal_basic(1.0), make_wood(1.0)
#   Additionally: make_vase_ceramic and make_colored_glass from vase.py
#   wear_tear (scratches + edge_wear) at 50% each

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
        "Coat Roughness": ("Coat Roughness", "Clearcoat Roughness"),
        "Subsurface Weight": ("Subsurface Weight", "Subsurface"),
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

# ---------- Material makers --------------------------------------------------

def make_vase_ceramic(name="VaseCeramic"):
    
    mat = _new_material(name)
    nt = mat.node_tree
    hsv = (np.random.uniform(0.0, 1.0),
           np.random.uniform(0.0, 0.75),
           np.random.uniform(0.0, 0.3))
    color = hsv2rgba(hsv)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf,
        **{"Base Color": color,
           "Subsurface Weight": 0.3,
           "Subsurface Radius": (0.002, 0.002, 0.002),
           "Subsurface Color": color,
           "Subsurface Anisotropy": 0.2,
           "Specular IOR Level": 0.2,
           "Roughness": 0.05,
           "Coat Weight": 0.5,
           "Coat Roughness": 0.05,
           "IOR": 1.47})
    _connect_output(nt, bsdf)
    return mat

def make_colored_glass(name="ColoredGlass"):
    
    mat = _new_material(name)
    nt = mat.node_tree
    hsv = (np.random.uniform(0.0, 1.0),
           np.random.uniform(0.0, 0.2),
           1.0)
    glass = nt.nodes.new("ShaderNodeBsdfPrincipled")
    glass.inputs["Base Color"].default_value = hsv2rgba(hsv)
    glass.inputs["Roughness"].default_value = float(np.random.uniform(0.05, 0.2))
    _connect_output(nt, glass)
    return mat

def make_marble(name="Marble"):
    
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    scale_vec = _vmath(nt, "SCALE", in0=tex_coord.outputs["Object"])
    vec_rotate = nt.nodes.new("ShaderNodeVectorRotate")
    vec_rotate.rotation_type = "EULER_XYZ"
    nt.links.new(scale_vec.outputs["Vector"], vec_rotate.inputs["Vector"])

    seed_val = _value_node(nt, 0.0)
    scale_val = _value_node(nt, 3.0)
    add_s = _math(nt, "ADD", scale_val.outputs[0], 1.0)

    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    noise2.noise_dimensions = "4D"
    noise2.inputs["Detail"].default_value = 15.0
    nt.links.new(vec_rotate.outputs["Vector"], noise2.inputs["Vector"])
    nt.links.new(seed_val.outputs[0], noise2.inputs["W"])
    nt.links.new(add_s.outputs[0], noise2.inputs["Scale"])

    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[1].default_value = 0.48
    map_range.inputs[2].default_value = 0.60
    nt.links.new(_noise_fac_output(noise2), map_range.inputs[0])

    noise0 = nt.nodes.new("ShaderNodeTexNoise")
    noise0.noise_dimensions = "4D"
    noise0.inputs["Detail"].default_value = 15.0
    nt.links.new(vec_rotate.outputs["Vector"], noise0.inputs["Vector"])
    nt.links.new(seed_val.outputs[0], noise0.inputs["W"])
    nt.links.new(scale_val.outputs[0], noise0.inputs["Scale"])

    noise3 = nt.nodes.new("ShaderNodeTexNoise")
    noise3.inputs["Scale"].default_value = 8.0
    noise3.inputs["Detail"].default_value = 15.0
    nt.links.new(_noise_fac_output(noise0), noise3.inputs["Vector"])

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi.feature = "DISTANCE_TO_EDGE"
    voronoi.voronoi_dimensions = "4D"
    voronoi.inputs["W"].default_value = 1.64
    voronoi.inputs["Scale"].default_value = 3.0
    nt.links.new(_noise_fac_output(noise3), voronoi.inputs["Vector"])

    cr1 = _color_ramp(nt, voronoi.outputs["Distance"],
                       [(0.0, (1, 1, 1, 1)), (0.03, (0, 0, 0, 1))])
    mul_veins = _math(nt, "MULTIPLY", map_range.outputs["Result"], cr1.outputs["Color"])

    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    noise1.noise_dimensions = "4D"
    noise1.inputs["Scale"].default_value = 8.0
    noise1.inputs["Detail"].default_value = 15.0
    nt.links.new(_noise_fac_output(noise0), noise1.inputs["Vector"])
    nt.links.new(seed_val.outputs[0], noise1.inputs["W"])

    mix1 = nt.nodes.new("ShaderNodeMix")
    mix1.data_type = "RGBA"
    mix1.inputs[0].default_value = 0.8
    nt.links.new(_noise_fac_output(noise0), mix1.inputs[6])
    nt.links.new(_noise_fac_output(noise1), mix1.inputs[7])

    cr0 = _color_ramp(nt, mix1.outputs[2],
                       [(0.3, (1, 1, 1, 1)), (0.9, (0, 0, 0, 1))])

    mix0 = nt.nodes.new("ShaderNodeMix")
    mix0.data_type = "RGBA"
    nt.links.new(mul_veins.outputs[0], mix0.inputs[0])
    nt.links.new(cr0.outputs["Color"], mix0.inputs[6])
    mix0.inputs[7].default_value = (0.0376, 0.0179, 0.0033, 1.0)

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    disp.inputs["Scale"].default_value = 0.02
    nt.links.new(mul_veins.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, **{"Specular IOR Level": 0.6, "Roughness": 0.1})
    nt.links.new(mix1.outputs[2], bsdf.inputs["Base Color"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

def make_marble_regular(name="MarbleRegular"):
    
    mat = _new_material(name)
    nt = mat.node_tree
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (20.0, 20.0, 20.0)
    nt.links.new(geo.outputs["Position"], mapping.inputs["Vector"])

    roughness = float(np.random.uniform(0.7, 0.9))
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.1
    noise.inputs["Detail"].default_value = 9.0
    noise.inputs["Roughness"].default_value = roughness
    noise.inputs["Distortion"].default_value = 0.2
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])

    mul = _math(nt, "MULTIPLY", _noise_fac_output(noise), 20.0)
    angle = float(np.random.uniform(0, 2 * np.pi))
    dot = _vmath(nt, "DOT_PRODUCT", mapping.outputs["Vector"],
                 (np.cos(angle), np.sin(angle), 0.0))
    add = _math(nt, "ADD", mul.outputs[0], dot.outputs["Value"])
    sine = _math(nt, "SINE", add.outputs[0])
    add1 = _math(nt, "ADD", sine.outputs[0], 1.0)

    darkness = float(np.random.uniform(0.0, 1.0))
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs[0].default_value = darkness
    mr.inputs[3].default_value = 0.2
    mr.inputs[4].default_value = 0.3
    power = _math(nt, "POWER", add1.outputs[0], mr.outputs["Result"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(power.outputs[0], bsdf.inputs["Base Color"])
    _connect_output(nt, bsdf)
    return mat

def make_marble_voronoi(name="MarbleVoronoi"):
    
    mat = _new_material(name)
    nt = mat.node_tree
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    mapping = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(geo.outputs["Position"], mapping.inputs["Vector"])

    roughness = float(np.random.uniform(0.5, 0.7))
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2.0
    noise.inputs["Detail"].default_value = 9.0
    noise.inputs["Roughness"].default_value = roughness
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])

    angle = float(np.random.uniform(0, 2 * np.pi))
    dot = _vmath(nt, "DOT_PRODUCT", mapping.outputs["Vector"],
                 (np.cos(angle), np.sin(angle), 0.0))
    add = _vmath(nt, "ADD", noise.outputs["Color"], dot.outputs["Value"])

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    nt.links.new(add.outputs["Vector"], voronoi.inputs["Vector"])
    cr = _color_ramp(nt, voronoi.outputs["Distance"],
                      [(float(np.random.uniform(0.4, 0.5)), (1, 1, 1, 1)),
                       (0.96, (0, 0, 0, 1))])
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(cr.outputs["Color"], bsdf.inputs["Base Color"])
    _set_principled(bsdf, Metallic=0.5, Roughness=0.0)
    _connect_output(nt, bsdf)
    return mat

def make_ceramic(name="Ceramic"):
    
    mat = _new_material(name)
    nt = mat.node_tree
    if np.random.uniform() < 0.8:
        color = hsv2rgba((np.random.uniform(0, 1),
                          np.random.uniform(0.2, 0.4),
                          log_uniform(0.3, 0.6)))
    else:
        color = hsv2rgba((0.0, 0.0, log_uniform(0.3, 0.6)))

    noise_r = nt.nodes.new("ShaderNodeTexNoise")
    noise_r.inputs["Scale"].default_value = log_uniform(20, 40)
    fc_r = _build_float_curve(nt, _noise_fac_output(noise_r), [(0, 0.0), (1, 0.8)])

    noise_c = nt.nodes.new("ShaderNodeTexNoise")
    noise_c.inputs["Scale"].default_value = log_uniform(20, 40)
    fc_c = _build_float_curve(nt, _noise_fac_output(noise_c), [(0, 0.0), (1, 0.8)])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf,
        **{"Base Color": color, "Coat Weight": 1.0, "Specular IOR Level": 1.0,
           "Subsurface Weight": float(np.random.uniform(0.02, 0.05))})
    nt.links.new(fc_r.outputs["Value"], bsdf.inputs["Roughness"])
    if "Coat Roughness" in bsdf.inputs:
        nt.links.new(fc_c.outputs["Value"], bsdf.inputs["Coat Roughness"])

    noise_d = nt.nodes.new("ShaderNodeTexNoise")
    noise_d.inputs["Scale"].default_value = log_uniform(20, 40)
    mul_d = _math(nt, "MULTIPLY", _noise_fac_output(noise_d), log_uniform(0.001, 0.005))
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_d.outputs[0], disp.inputs["Height"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

def make_glass(name="Glass"):
    
    mat = _new_material(name)
    nt = mat.node_tree
    glass = nt.nodes.new("ShaderNodeBsdfPrincipled")
    glass.inputs["Roughness"].default_value = 0.02
    glass.inputs["IOR"].default_value = 1.5
    if "Transmission Weight" in glass.inputs:
        glass.inputs["Transmission Weight"].default_value = 1.0
    elif "Transmission" in glass.inputs:
        glass.inputs["Transmission"].default_value = 1.0
    _connect_output(nt, glass)
    return mat

def make_metal_basic(name="MetalBasic"):
    
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = float(np.random.uniform(10, 25))
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])
    fc = _build_float_curve(nt, _noise_fac_output(noise),
        [(0, float(np.random.uniform(0, 0.2))),
         (1, float(np.random.uniform(0.4, 0.7)))])
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Metallic=1.0,
        **{"Specular IOR Level": float(np.random.uniform(0.5, 1.0)),
           "Base Color": hsv2rgba(metal_hsv())})
    nt.links.new(fc.outputs["Value"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

def make_plastic(name="Plastic"):
    """Simplified plastic: random colour, moderate roughness."""

    mat = _new_material(name)
    nt = mat.node_tree
    color = hsv2rgba((np.random.uniform(0, 1),
                      np.random.uniform(0.3, 0.8),
                      np.random.uniform(0.2, 0.8)))
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, **{"Base Color": color,
                             "Roughness": float(np.random.uniform(0.15, 0.45)),
                             "Specular IOR Level": 0.5})
    _connect_output(nt, bsdf)
    return mat

def make_wood(name="Wood"):
    """Simplified wood: warm brown procedural texture."""

    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = float(np.random.uniform(8, 20))
    noise.inputs["Detail"].default_value = 6.0
    noise.inputs["Distortion"].default_value = float(np.random.uniform(2, 6))
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    cr = _color_ramp(nt, _noise_fac_output(noise),
        [(0.0, hsv2rgba((0.07, 0.6, 0.15))),
         (0.5, hsv2rgba((0.06, 0.5, 0.35))),
         (1.0, hsv2rgba((0.08, 0.4, 0.5)))])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(cr.outputs["Color"], bsdf.inputs["Base Color"])
    _set_principled(bsdf, Roughness=float(np.random.uniform(0.3, 0.6)),
                    **{"Specular IOR Level": 0.3})
    _connect_output(nt, bsdf)
    return mat

# ---------- Material registry ------------------------------------------------
marble = [
    (make_marble, 1.0),
    (make_marble_regular, 0.2),
    (make_marble_voronoi, 0.2),
]
tableware = [
    (make_ceramic, 1.0),
    (make_glass, 1.0),
    (make_plastic, 1.0),
    (make_metal_basic, 1.0),
    (make_wood, 1.0),
]
vase_material_pool = marble + tableware

def get_vase_material(name="VaseMaterial"):
    ctor = weighted_sample(vase_material_pool)
    return ctor(name=name)

# ---- wear_tear ------------------------------------------------------------
WEAR_TEAR_PROB = [0.5, 0.5]
SCRATCH_LABEL = "scratch"
EDGE_WEAR_LABEL = "wear_tear"

def _find_node(nt, bl_idname):
    return next((n for n in nt.nodes if n.bl_idname == bl_idname), None)

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

def apply_wear_tear(obj):
    """Apply scratches and edge_wear with 50% probability each."""

    scratch_prob, edge_wear_prob = WEAR_TEAR_PROB
    if np.random.uniform() <= scratch_prob:
        apply_scratches(obj)
    if np.random.uniform() <= edge_wear_prob:
        apply_edge_wear(obj)

# End of inlined material library

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

# ── Node Group 1: star_profile ───────────────────────────────────────────────

def build_star_profile():
    """CurveStar -> ResampleCurve."""

    ng = bpy.data.node_groups.new("star_profile", "GeometryNodeTree")
    s_res = ng.interface.new_socket("Resolution", in_out="INPUT",
                                    socket_type="NodeSocketInt")
    s_res.default_value = 64
    s_pts = ng.interface.new_socket("Points", in_out="INPUT",
                                    socket_type="NodeSocketInt")
    s_pts.default_value = 64
    s_ir = ng.interface.new_socket("Inner Radius", in_out="INPUT",
                                   socket_type="NodeSocketFloat")
    s_ir.default_value = 0.9
    ng.interface.new_socket("Curve", in_out="OUTPUT",
                            socket_type="NodeSocketGeometry")
    nodes, links = ng.nodes, ng.links
    gi = nodes.new("NodeGroupInput")
    go = nodes.new("NodeGroupOutput")
    star = nodes.new("GeometryNodeCurveStar")
    star.inputs["Outer Radius"].default_value = 1.0
    links.new(gi.outputs["Points"], star.inputs["Points"])
    links.new(gi.outputs["Inner Radius"], star.inputs["Inner Radius"])
    resample = nodes.new("GeometryNodeResampleCurve")
    links.new(star.outputs["Curve"], resample.inputs["Curve"])
    links.new(gi.outputs["Resolution"], resample.inputs["Count"])
    links.new(resample.outputs[0], go.inputs[0])
    return ng

# ── Node Group 2: flip_index ────────────────────────────────────────────────

def build_flip_index():
    """(index % V_Res) * U_Res + floor(index / V_Res)"""

    ng = bpy.data.node_groups.new("flip_index", "GeometryNodeTree")
    s_v = ng.interface.new_socket("V Resolution", in_out="INPUT",
                                  socket_type="NodeSocketInt")
    s_v.default_value = 0
    s_u = ng.interface.new_socket("U Resolution", in_out="INPUT",
                                  socket_type="NodeSocketInt")
    s_u.default_value = 0
    ng.interface.new_socket("Index", in_out="OUTPUT",
                            socket_type="NodeSocketInt")
    nodes, links = ng.nodes, ng.links
    gi = nodes.new("NodeGroupInput")
    go = nodes.new("NodeGroupOutput")
    idx = nodes.new("GeometryNodeInputIndex")
    mod = nodes.new("ShaderNodeMath"); mod.operation = "MODULO"
    links.new(idx.outputs[0], mod.inputs[0])
    links.new(gi.outputs["V Resolution"], mod.inputs[1])
    mul = nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    links.new(mod.outputs[0], mul.inputs[0])
    links.new(gi.outputs["U Resolution"], mul.inputs[1])
    div = nodes.new("ShaderNodeMath"); div.operation = "DIVIDE"
    links.new(idx.outputs[0], div.inputs[0])
    links.new(gi.outputs["V Resolution"], div.inputs[1])
    flr = nodes.new("ShaderNodeMath"); flr.operation = "FLOOR"
    links.new(div.outputs[0], flr.inputs[0])
    add = nodes.new("ShaderNodeMath"); add.operation = "ADD"
    links.new(mul.outputs[0], add.inputs[0])
    links.new(flr.outputs[0], add.inputs[1])
    links.new(add.outputs[0], go.inputs[0])
    return ng

# ── Node Group 3: cylinder_side ──────────────────────────────────────────────

def build_cylinder_side():
    """MeshCylinder(U, V-1) + store UV."""

    ng = bpy.data.node_groups.new("cylinder_side", "GeometryNodeTree")
    s_u = ng.interface.new_socket("U Resolution", in_out="INPUT",
                                  socket_type="NodeSocketInt")
    s_u.default_value = 32
    s_v = ng.interface.new_socket("V Resolution", in_out="INPUT",
                                  socket_type="NodeSocketInt")
    s_v.default_value = 0
    ng.interface.new_socket("Geometry", in_out="OUTPUT",
                            socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Top", in_out="OUTPUT",
                            socket_type="NodeSocketBool")
    ng.interface.new_socket("Side", in_out="OUTPUT",
                            socket_type="NodeSocketBool")
    ng.interface.new_socket("Bottom", in_out="OUTPUT",
                            socket_type="NodeSocketBool")
    nodes, links = ng.nodes, ng.links
    gi = nodes.new("NodeGroupInput")
    go = nodes.new("NodeGroupOutput")
    sub = nodes.new("ShaderNodeMath"); sub.operation = "SUBTRACT"
    links.new(gi.outputs["V Resolution"], sub.inputs[0])
    sub.inputs[1].default_value = 1.0
    cyl = nodes.new("GeometryNodeMeshCylinder")
    links.new(gi.outputs["U Resolution"], cyl.inputs["Vertices"])
    links.new(sub.outputs[0], cyl.inputs["Side Segments"])
    store_uv = nodes.new("GeometryNodeStoreNamedAttribute")
    store_uv.data_type = "FLOAT_VECTOR"
    store_uv.domain = "CORNER"
    store_uv.inputs["Name"].default_value = "uv_map"
    links.new(cyl.outputs["Mesh"], store_uv.inputs["Geometry"])
    for inp in store_uv.inputs:
        if inp.name == "Value" and inp.type == "VECTOR":
            links.new(cyl.outputs["UV Map"], inp)
            break
    else:
        links.new(cyl.outputs["UV Map"], store_uv.inputs[3])
    links.new(store_uv.outputs[0], go.inputs["Geometry"])
    links.new(cyl.outputs["Top"], go.inputs["Top"])
    links.new(cyl.outputs["Side"], go.inputs["Side"])
    links.new(cyl.outputs["Bottom"], go.inputs["Bottom"])
    return ng

# ── Node Group 4: lofting ────────────────────────────────────────────────────

def build_lofting(flip_index_ng, cylinder_side_ng):
    """Lofting: transpose U x V grids via SampleIndex + flip_index."""

    ng = bpy.data.node_groups.new("lofting", "GeometryNodeTree")
    ng.interface.new_socket("Profile Curves", in_out="INPUT",
                            socket_type="NodeSocketGeometry")
    s_u = ng.interface.new_socket("U Resolution", in_out="INPUT",
                                  socket_type="NodeSocketInt")
    s_u.default_value = 32
    s_v = ng.interface.new_socket("V Resolution", in_out="INPUT",
                                  socket_type="NodeSocketInt")
    s_v.default_value = 32
    ng.interface.new_socket("Geometry", in_out="OUTPUT",
                            socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Top", in_out="OUTPUT",
                            socket_type="NodeSocketBool")
    ng.interface.new_socket("Side", in_out="OUTPUT",
                            socket_type="NodeSocketBool")
    ng.interface.new_socket("Bottom", in_out="OUTPUT",
                            socket_type="NodeSocketBool")
    nodes, links = ng.nodes, ng.links
    gi = nodes.new("NodeGroupInput")
    go = nodes.new("NodeGroupOutput")

    cyl_side = nodes.new("GeometryNodeGroup")
    cyl_side.node_tree = cylinder_side_ng
    links.new(gi.outputs["U Resolution"], cyl_side.inputs["U Resolution"])
    links.new(gi.outputs["V Resolution"], cyl_side.inputs["V Resolution"])

    idx_node = nodes.new("GeometryNodeInputIndex")
    eval_dom = nodes.new("GeometryNodeFieldOnDomain")
    eval_dom.data_type = "INT"; eval_dom.domain = "CURVE"
    links.new(idx_node.outputs[0], eval_dom.inputs[0])

    compare = nodes.new("FunctionNodeCompare")
    compare.data_type = "INT"; compare.operation = "EQUAL"
    compare.inputs[3].default_value = 0
    links.new(eval_dom.outputs[0], compare.inputs[2])

    curve_line = nodes.new("GeometryNodeCurvePrimitiveLine")
    dom_size = nodes.new("GeometryNodeAttributeDomainSize")
    dom_size.component = "CURVE"
    links.new(gi.outputs["Profile Curves"], dom_size.inputs["Geometry"])

    resample_spine = nodes.new("GeometryNodeResampleCurve")
    links.new(curve_line.outputs[0], resample_spine.inputs["Curve"])
    links.new(dom_size.outputs["Spline Count"], resample_spine.inputs["Count"])

    iop = nodes.new("GeometryNodeInstanceOnPoints")
    links.new(gi.outputs["Profile Curves"], iop.inputs["Points"])
    links.new(compare.outputs[0], iop.inputs["Selection"])
    links.new(resample_spine.outputs[0], iop.inputs["Instance"])

    realize = nodes.new("GeometryNodeRealizeInstances")
    links.new(iop.outputs[0], realize.inputs["Geometry"])

    pos1 = nodes.new("GeometryNodeInputPosition")
    flip1 = nodes.new("GeometryNodeGroup")
    flip1.node_tree = flip_index_ng
    links.new(dom_size.outputs["Spline Count"], flip1.inputs["V Resolution"])
    links.new(gi.outputs["U Resolution"], flip1.inputs["U Resolution"])

    sample1 = nodes.new("GeometryNodeSampleIndex")
    sample1.data_type = "FLOAT_VECTOR"
    links.new(gi.outputs["Profile Curves"], sample1.inputs["Geometry"])
    links.new(pos1.outputs[0], sample1.inputs["Value"])
    links.new(flip1.outputs[0], sample1.inputs["Index"])

    sp1 = nodes.new("GeometryNodeSetPosition")
    links.new(realize.outputs[0], sp1.inputs["Geometry"])
    links.new(sample1.outputs[0], sp1.inputs["Position"])

    sst = nodes.new("GeometryNodeCurveSplineType")
    sst.spline_type = "CATMULL_ROM"
    links.new(sp1.outputs[0], sst.inputs["Curve"])

    resample_v = nodes.new("GeometryNodeResampleCurve")
    links.new(sst.outputs[0], resample_v.inputs["Curve"])
    links.new(gi.outputs["V Resolution"], resample_v.inputs["Count"])

    pos2 = nodes.new("GeometryNodeInputPosition")
    flip2 = nodes.new("GeometryNodeGroup")
    flip2.node_tree = flip_index_ng
    links.new(gi.outputs["U Resolution"], flip2.inputs["V Resolution"])
    links.new(gi.outputs["V Resolution"], flip2.inputs["U Resolution"])

    sample2 = nodes.new("GeometryNodeSampleIndex")
    sample2.data_type = "FLOAT_VECTOR"
    links.new(resample_v.outputs[0], sample2.inputs["Geometry"])
    links.new(pos2.outputs[0], sample2.inputs["Value"])
    links.new(flip2.outputs[0], sample2.inputs["Index"])

    sp2 = nodes.new("GeometryNodeSetPosition")
    links.new(cyl_side.outputs["Geometry"], sp2.inputs["Geometry"])
    links.new(sample2.outputs[0], sp2.inputs["Position"])

    links.new(sp2.outputs[0], go.inputs["Geometry"])
    links.new(cyl_side.outputs["Top"], go.inputs["Top"])
    links.new(cyl_side.outputs["Side"], go.inputs["Side"])
    links.new(cyl_side.outputs["Bottom"], go.inputs["Bottom"])
    return ng

# ── Node Group 5: vase_profile ───────────────────────────────────────────────

def build_vase_profile():
    """Build 7 profile curve copies at different heights and scales."""

    ng = bpy.data.node_groups.new("vase_profile", "GeometryNodeTree")
    ng.interface.new_socket("Profile Curve", in_out="INPUT",
                            socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Height", in_out="INPUT",
                            socket_type="NodeSocketFloat")
    ng.interface.new_socket("Diameter", in_out="INPUT",
                            socket_type="NodeSocketFloat")
    ng.interface.new_socket("Top Scale", in_out="INPUT",
                            socket_type="NodeSocketFloat")
    ng.interface.new_socket("Neck Mid Position", in_out="INPUT",
                            socket_type="NodeSocketFloat")
    s_np = ng.interface.new_socket("Neck Position", in_out="INPUT",
                                   socket_type="NodeSocketFloat")
    s_np.default_value = 0.5
    ng.interface.new_socket("Neck Scale", in_out="INPUT",
                            socket_type="NodeSocketFloat")
    ng.interface.new_socket("Shoulder Position", in_out="INPUT",
                            socket_type="NodeSocketFloat")
    ng.interface.new_socket("Shoulder Thickness", in_out="INPUT",
                            socket_type="NodeSocketFloat")
    ng.interface.new_socket("Foot Scale", in_out="INPUT",
                            socket_type="NodeSocketFloat")
    ng.interface.new_socket("Foot Height", in_out="INPUT",
                            socket_type="NodeSocketFloat")
    ng.interface.new_socket("Geometry", in_out="OUTPUT",
                            socket_type="NodeSocketGeometry")
    nodes, links = ng.nodes, ng.links
    gi = nodes.new("NodeGroupInput")
    go = nodes.new("NodeGroupOutput")

    # Neck top
    comb_z_h = nodes.new("ShaderNodeCombineXYZ")
    links.new(gi.outputs["Height"], comb_z_h.inputs["Z"])
    mul_ts_d = nodes.new("ShaderNodeMath"); mul_ts_d.operation = "MULTIPLY"
    links.new(gi.outputs["Top Scale"], mul_ts_d.inputs[0])
    links.new(gi.outputs["Diameter"], mul_ts_d.inputs[1])
    neck_top = nodes.new("GeometryNodeTransform")
    links.new(gi.outputs["Profile Curve"], neck_top.inputs["Geometry"])
    links.new(comb_z_h.outputs[0], neck_top.inputs["Translation"])
    links.new(mul_ts_d.outputs[0], neck_top.inputs["Scale"])

    # Neck
    mul_h_np = nodes.new("ShaderNodeMath"); mul_h_np.operation = "MULTIPLY"
    links.new(gi.outputs["Height"], mul_h_np.inputs[0])
    links.new(gi.outputs["Neck Position"], mul_h_np.inputs[1])
    comb_z_np = nodes.new("ShaderNodeCombineXYZ")
    links.new(mul_h_np.outputs[0], comb_z_np.inputs["Z"])
    mul_d_ns = nodes.new("ShaderNodeMath"); mul_d_ns.operation = "MULTIPLY"
    links.new(gi.outputs["Diameter"], mul_d_ns.inputs[0])
    links.new(gi.outputs["Neck Scale"], mul_d_ns.inputs[1])
    neck = nodes.new("GeometryNodeTransform")
    links.new(gi.outputs["Profile Curve"], neck.inputs["Geometry"])
    links.new(comb_z_np.outputs[0], neck.inputs["Translation"])
    links.new(mul_d_ns.outputs[0], neck.inputs["Scale"])

    # Neck middle
    sub_1_np = nodes.new("ShaderNodeMath")
    sub_1_np.operation = "SUBTRACT"; sub_1_np.use_clamp = True
    sub_1_np.inputs[0].default_value = 1.0
    links.new(gi.outputs["Neck Position"], sub_1_np.inputs[1])
    mul_add = nodes.new("ShaderNodeMath"); mul_add.operation = "MULTIPLY_ADD"
    links.new(sub_1_np.outputs[0], mul_add.inputs[0])
    links.new(gi.outputs["Neck Mid Position"], mul_add.inputs[1])
    links.new(gi.outputs["Neck Position"], mul_add.inputs[2])
    mul_nm_h = nodes.new("ShaderNodeMath"); mul_nm_h.operation = "MULTIPLY"
    links.new(mul_add.outputs[0], mul_nm_h.inputs[0])
    links.new(gi.outputs["Height"], mul_nm_h.inputs[1])
    comb_z_nm = nodes.new("ShaderNodeCombineXYZ")
    links.new(mul_nm_h.outputs[0], comb_z_nm.inputs["Z"])
    add_ns_ts = nodes.new("ShaderNodeMath")
    links.new(gi.outputs["Neck Scale"], add_ns_ts.inputs[0])
    links.new(gi.outputs["Top Scale"], add_ns_ts.inputs[1])
    div_2 = nodes.new("ShaderNodeMath"); div_2.operation = "DIVIDE"
    links.new(add_ns_ts.outputs[0], div_2.inputs[0])
    div_2.inputs[1].default_value = 2.0
    mul_nm_d = nodes.new("ShaderNodeMath"); mul_nm_d.operation = "MULTIPLY"
    links.new(gi.outputs["Diameter"], mul_nm_d.inputs[0])
    links.new(div_2.outputs[0], mul_nm_d.inputs[1])
    neck_mid = nodes.new("GeometryNodeTransform")
    links.new(gi.outputs["Profile Curve"], neck_mid.inputs["Geometry"])
    links.new(comb_z_nm.outputs[0], neck_mid.inputs["Translation"])
    links.new(mul_nm_d.outputs[0], neck_mid.inputs["Scale"])

    join_neck = nodes.new("GeometryNodeJoinGeometry")
    links.new(neck.outputs[0], join_neck.inputs["Geometry"])
    links.new(neck_mid.outputs[0], join_neck.inputs["Geometry"])
    links.new(neck_top.outputs[0], join_neck.inputs["Geometry"])

    # Body
    map_sp = nodes.new("ShaderNodeMapRange")
    links.new(gi.outputs["Shoulder Position"], map_sp.inputs["Value"])
    links.new(gi.outputs["Foot Height"], map_sp.inputs["To Min"])
    links.new(gi.outputs["Neck Position"], map_sp.inputs["To Max"])
    sub_np_fh = nodes.new("ShaderNodeMath"); sub_np_fh.operation = "SUBTRACT"
    links.new(gi.outputs["Neck Position"], sub_np_fh.inputs[0])
    links.new(gi.outputs["Foot Height"], sub_np_fh.inputs[1])
    mul_st = nodes.new("ShaderNodeMath"); mul_st.operation = "MULTIPLY"
    links.new(sub_np_fh.outputs[0], mul_st.inputs[0])
    links.new(gi.outputs["Shoulder Thickness"], mul_st.inputs[1])
    add_bt = nodes.new("ShaderNodeMath")
    links.new(map_sp.outputs["Result"], add_bt.inputs[0])
    links.new(mul_st.outputs[0], add_bt.inputs[1])
    min_bt = nodes.new("ShaderNodeMath"); min_bt.operation = "MINIMUM"
    links.new(add_bt.outputs[0], min_bt.inputs[0])
    links.new(gi.outputs["Neck Position"], min_bt.inputs[1])
    mul_bt_h = nodes.new("ShaderNodeMath"); mul_bt_h.operation = "MULTIPLY"
    links.new(min_bt.outputs[0], mul_bt_h.inputs[0])
    links.new(gi.outputs["Height"], mul_bt_h.inputs[1])
    comb_z_bt = nodes.new("ShaderNodeCombineXYZ")
    links.new(mul_bt_h.outputs[0], comb_z_bt.inputs["Z"])
    body_top = nodes.new("GeometryNodeTransform")
    links.new(gi.outputs["Profile Curve"], body_top.inputs["Geometry"])
    links.new(comb_z_bt.outputs[0], body_top.inputs["Translation"])
    links.new(gi.outputs["Diameter"], body_top.inputs["Scale"])
    sub_bb = nodes.new("ShaderNodeMath"); sub_bb.operation = "SUBTRACT"
    links.new(map_sp.outputs["Result"], sub_bb.inputs[0])
    links.new(mul_st.outputs[0], sub_bb.inputs[1])
    max_bb = nodes.new("ShaderNodeMath"); max_bb.operation = "MAXIMUM"
    links.new(sub_bb.outputs[0], max_bb.inputs[0])
    links.new(gi.outputs["Foot Height"], max_bb.inputs[1])
    mul_bb_h = nodes.new("ShaderNodeMath"); mul_bb_h.operation = "MULTIPLY"
    links.new(max_bb.outputs[0], mul_bb_h.inputs[0])
    links.new(gi.outputs["Height"], mul_bb_h.inputs[1])
    comb_z_bb = nodes.new("ShaderNodeCombineXYZ")
    links.new(mul_bb_h.outputs[0], comb_z_bb.inputs["Z"])
    body_bot = nodes.new("GeometryNodeTransform")
    links.new(gi.outputs["Profile Curve"], body_bot.inputs["Geometry"])
    links.new(comb_z_bb.outputs[0], body_bot.inputs["Translation"])
    links.new(gi.outputs["Diameter"], body_bot.inputs["Scale"])

    join_body = nodes.new("GeometryNodeJoinGeometry")
    links.new(body_bot.outputs[0], join_body.inputs["Geometry"])
    links.new(body_top.outputs[0], join_body.inputs["Geometry"])

    # Foot
    mul_fh_h = nodes.new("ShaderNodeMath"); mul_fh_h.operation = "MULTIPLY"
    links.new(gi.outputs["Foot Height"], mul_fh_h.inputs[0])
    links.new(gi.outputs["Height"], mul_fh_h.inputs[1])
    comb_z_ft = nodes.new("ShaderNodeCombineXYZ")
    links.new(mul_fh_h.outputs[0], comb_z_ft.inputs["Z"])
    mul_d_fs = nodes.new("ShaderNodeMath"); mul_d_fs.operation = "MULTIPLY"
    links.new(gi.outputs["Diameter"], mul_d_fs.inputs[0])
    links.new(gi.outputs["Foot Scale"], mul_d_fs.inputs[1])
    foot_top = nodes.new("GeometryNodeTransform")
    links.new(gi.outputs["Profile Curve"], foot_top.inputs["Geometry"])
    links.new(comb_z_ft.outputs[0], foot_top.inputs["Translation"])
    links.new(mul_d_fs.outputs[0], foot_top.inputs["Scale"])
    foot_bot = nodes.new("GeometryNodeTransform")
    links.new(gi.outputs["Profile Curve"], foot_bot.inputs["Geometry"])
    links.new(mul_d_fs.outputs[0], foot_bot.inputs["Scale"])

    join_foot = nodes.new("GeometryNodeJoinGeometry")
    links.new(foot_bot.outputs[0], join_foot.inputs["Geometry"])
    links.new(foot_top.outputs[0], join_foot.inputs["Geometry"])

    # Join all
    join_all = nodes.new("GeometryNodeJoinGeometry")
    links.new(join_foot.outputs[0], join_all.inputs["Geometry"])
    links.new(join_body.outputs[0], join_all.inputs["Geometry"])
    links.new(join_neck.outputs[0], join_all.inputs["Geometry"])

    links.new(join_all.outputs[0], go.inputs[0])
    return ng

# ── Top-level geometry_vases nodegroup ───────────────────────────────────────

def build_geometry_vases(params, star_ng, vase_profile_ng, lofting_ng):
    """Top-level node group: star_profile -> vase_profile -> lofting -> delete top."""

    ng = bpy.data.node_groups.new("geometry_vases", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT",
                            socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT",
                            socket_type="NodeSocketGeometry")
    nodes, links = ng.nodes, ng.links
    gi = nodes.new("NodeGroupInput")
    go = nodes.new("NodeGroupOutput")

    star = nodes.new("GeometryNodeGroup")
    star.node_tree = star_ng
    star.inputs["Resolution"].default_value = params["U_resolution"]
    star.inputs["Points"].default_value = params["Profile Star Points"]
    star.inputs["Inner Radius"].default_value = params["Profile Inner Radius"]

    vp = nodes.new("GeometryNodeGroup")
    vp.node_tree = vase_profile_ng
    links.new(star.outputs["Curve"], vp.inputs["Profile Curve"])
    vp.inputs["Height"].default_value = params["Height"]
    vp.inputs["Diameter"].default_value = params["Diameter"]
    vp.inputs["Top Scale"].default_value = params["Top Scale"]
    vp.inputs["Neck Mid Position"].default_value = params["Neck Mid Position"]
    vp.inputs["Neck Position"].default_value = params["Neck Position"]
    vp.inputs["Neck Scale"].default_value = params["Neck Scale"]
    vp.inputs["Shoulder Position"].default_value = params["Shoulder Position"]
    vp.inputs["Shoulder Thickness"].default_value = params["Shoulder Thickness"]
    vp.inputs["Foot Scale"].default_value = params["Foot Scale"]
    vp.inputs["Foot Height"].default_value = params["Foot Height"]

    loft = nodes.new("GeometryNodeGroup")
    loft.node_tree = lofting_ng
    links.new(vp.outputs[0], loft.inputs["Profile Curves"])
    loft.inputs["U Resolution"].default_value = 64
    loft.inputs["V Resolution"].default_value = 64

    delete = nodes.new("GeometryNodeDeleteGeometry")
    links.new(loft.outputs["Geometry"], delete.inputs["Geometry"])
    links.new(loft.outputs["Top"], delete.inputs["Selection"])

    links.new(delete.outputs[0], go.inputs[0])
    return ng

# ── main ──────────────────────────────────────────────────────────────────────

def make_vase():
    instance_seed = int_hash((factory_seed, 0))
    np.random.seed(factory_seed)

    z = np.random.uniform(0.17, 0.5)
    x = z * np.random.uniform(0.3, 0.6)
    U_resolution = 64
    neck_scale = np.random.uniform(0.2, 0.8)

    params = {
        "Profile Inner Radius": np.random.choice([1.0, np.random.uniform(0.8, 1.0)]),
        "Profile Star Points": int(np.random.randint(16, U_resolution // 2 + 1)),
        "U_resolution": U_resolution,
        "V_resolution": 64,
        "Height": z,
        "Diameter": x,
        "Top Scale": neck_scale * np.random.uniform(0.8, 1.2),
        "Neck Mid Position": np.random.uniform(0.7, 0.95),
        "Neck Position": 0.5 * neck_scale + 0.5 + np.random.uniform(-0.05, 0.05),
        "Neck Scale": neck_scale,
        "Shoulder Position": np.random.uniform(0.3, 0.7),
        "Shoulder Thickness": np.random.uniform(0.1, 0.25),
        "Foot Scale": np.random.uniform(0.4, 0.6),
        "Foot Height": np.random.uniform(0.01, 0.1),
    }

    # -- build material (seeded from factory_seed) --
    material = get_vase_material("VaseMat")

    # -- build geometry node groups --
    top_ng = build_geometry_vases(
        params,
        build_star_profile(),
        build_vase_profile(),
        build_lofting(build_flip_index(), build_cylinder_side()),
    )

    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
    obj = bpy.context.active_object

    mod = obj.modifiers.new("VaseNodes", "NODES")
    mod.node_group = top_ng
    select_only(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)

    mod_s = obj.modifiers.new("SOLIDIFY", "SOLIDIFY")
    mod_s.thickness = 0.002
    select_only(obj)
    bpy.ops.object.modifier_apply(modifier=mod_s.name)

    mod_ss = obj.modifiers.new("SUBSURF", "SUBSURF")
    mod_ss.levels = 2
    mod_ss.render_levels = 2
    select_only(obj)
    bpy.ops.object.modifier_apply(modifier=mod_ss.name)

    # -- assign material --
    obj.data.materials.clear()
    obj.data.materials.append(material)

    # -- apply wear_tear (seed for wear_tear RNG) --
    seed_all(instance_seed)
    apply_wear_tear(obj)

    return obj

clear_scene()
make_vase()
