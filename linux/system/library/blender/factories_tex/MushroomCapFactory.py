# [FL_INDEX: keywords="blender_factory, procedural_3d, MushroomCapFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: MushroomCapFactory | Category: factories_tex
# Prompt: A 3D model of a mushroom cap rendered from a slightly elevated perspective, featuring a rounded, irregular dome shape with a beige-tan upper surface covered in organic wavy line patterns and a dark underside representing the gill region.

"""
Standalone Blender script -- MushroomCapFactory mesh + shaders, seed-controlled.
Reproduces MushroomCapFactory
(shader_cap, shader_noise, shader_voronoi, shader_speckle) and the default
gill shader (_default_shader).

Run:  blender --background --python MushroomCapFactory.py
"""
import os
import bpy
import bmesh
import hashlib
import numpy as np
import random
import colorsys
from collections.abc import Sized

C = bpy.context
D = bpy.data

# ---------------------------------------------------------------------------
# Seed utilities
# ---------------------------------------------------------------------------
class FixedSeed:
    def __init__(self, seed):
        self.seed = int(seed)
    def __enter__(self):
        self.py_state = random.getstate()
        self.np_state = np.random.get_state()
        random.seed(self.seed)
        np.random.seed(self.seed)
    def __exit__(self, *_):
        random.setstate(self.py_state)
        np.random.set_state(self.np_state)

def md5_hash(x):
    if isinstance(x, (tuple, list)):
        m = hashlib.md5()
        for s in x:
            m.update(str(s).encode("utf-8"))
        return m
    return hashlib.md5(str(x).encode("utf-8"))

def int_hash(x, max_val=(2**32 - 1)):
    return abs(int(md5_hash(x).hexdigest(), 16)) % max_val

def log_uniform(low, high, size=None):
    return np.exp(np.random.uniform(np.log(low), np.log(high), size))

def polygon_angles(n, min_angle=np.pi / 6, max_angle=np.pi * 2 / 3):
    if n <= 0:
        return np.array([])
    for _ in range(100):
        angles = np.sort(np.random.uniform(0, 2 * np.pi, n))
        diff = (angles - np.roll(angles, 1)) % (2 * np.pi)
        if (diff >= min_angle).all() and (diff <= max_angle).all():
            return angles
    return np.sort((np.arange(n) * (2 * np.pi / n) + np.random.uniform(0, 2 * np.pi)) % (2 * np.pi))

from numpy.random import uniform

# Inlined shader library -- faithful translation of
# Blender 5.0 adaptations: MusgraveTexture -> NoiseTexture; Mix RGBA socket
# indices [0]=Fac,[6]=A,[7]=B,[2]=Result; Principled "Specular IOR Level".
def seed_all(seed):
    np.random.seed(int(seed)); random.seed(int(seed))

def _hsv2rgba(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(float(h) % 1.0,
                                  max(0.0, min(1.0, float(s))),
                                  max(0.0, min(1.0, float(v))))
    return (r, g, b, 1.0)

def _mlog_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def _new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    return m

def _fac_out(node):
    return node.outputs.get("Fac") or node.outputs.get("Factor") or node.outputs[0]

def _spec_socket(bsdf):
    """Principled BSDF: 'Specular IOR Level' in 4.x+, 'Specular' in 3.x."""

    return "Specular IOR Level" if "Specular IOR Level" in bsdf.inputs else "Specular"

def _noise_as_musgrave(nt, ln, scale, vector_out=None):
    """Blender 5.0 replacement for `nw.musgrave(scale)`.
    Original: MusgraveTexture(Scale=s) -> MapRange(-1,1,0,1) to remap fBm to [0,1].
    Noise texture already outputs in [0,1] so we use it directly.
    """

    n = nt.nodes.new("ShaderNodeTexNoise")
    if vector_out is not None:
        ln(vector_out, n.inputs["Vector"])
    n.inputs["Scale"].default_value = float(scale)
    n.inputs["Detail"].default_value = 2.0
    n.inputs["Roughness"].default_value = 0.5
    return _fac_out(n)

def _raw_musgrave_noise(nt, ln, scale, vector_out=None):
    """For MusgraveTexture calls that are NOT wrapped in nw.musgrave()
    (i.e. use raw Musgrave output with range ~[-1,1]). Replace with noise but
    shift to [-1,1] via (noise*2 - 1) so downstream MapRange still works."""

    n = nt.nodes.new("ShaderNodeTexNoise")
    if vector_out is not None:
        ln(vector_out, n.inputs["Vector"])
    n.inputs["Scale"].default_value = float(scale)
    n.inputs["Detail"].default_value = 2.0
    n.inputs["Roughness"].default_value = 0.5
    # (noise*2 - 1) -> approx [-1, 1]
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY_ADD"
    ln(_fac_out(n), mul.inputs[0])
    mul.inputs[1].default_value = 2.0
    mul.inputs[2].default_value = -1.0
    return mul.outputs[0]

def _color_ramp_hsv(nt, ln, fac_out, positions, colors):
    """Replicates node_utils.build_color_ramp (default mode=HSV)."""

    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.color_mode = "HSV"
    cr.color_ramp.hue_interpolation = "NEAR"
    ln(fac_out, cr.inputs["Fac"])
    for _ in range(len(positions) - 2):
        cr.color_ramp.elements.new(0.0)
    for i, (p, c) in enumerate(zip(positions, colors)):
        cr.color_ramp.elements[i].position = float(p)
        cr.color_ramp.elements[i].color = c
    return cr

def _float_curve(nt, ln, fac_out, anchors, handle="VECTOR"):
    """Replicates NodeWrangler.build_float_curve."""

    fc = nt.nodes.new("ShaderNodeFloatCurve")
    ln(fac_out, fc.inputs["Value"])
    c = fc.mapping.curves[0]
    for i, (x, y) in enumerate(anchors):
        if i < 2:
            c.points[i].location = (float(x), float(y))
        else:
            c.points.new(float(x), float(y))
        c.points[i].handle_type = handle
    fc.mapping.use_clip = False
    fc.mapping.update()
    return fc

def _mix_rgba(nt, ln, fac_out, a_out, b_out):
    """Mix RGBA: inputs [0]=Factor, [6]=A, [7]=B, outputs [2]=Result."""

    m = nt.nodes.new("ShaderNodeMix"); m.data_type = "RGBA"
    ln(fac_out, m.inputs[0])
    ln(a_out, m.inputs[6])
    ln(b_out, m.inputs[7])
    return m

def _map_range(nt, ln, value_out, from_min, from_max, to_min, to_max):
    mr = nt.nodes.new("ShaderNodeMapRange")
    ln(value_out, mr.inputs["Value"])
    mr.inputs["From Min"].default_value = float(from_min)
    mr.inputs["From Max"].default_value = float(from_max)
    mr.inputs["To Min"].default_value = float(to_min)
    mr.inputs["To Max"].default_value = float(to_max)
    return mr

def _sample_common_colors(base_hue, bright_sat=(0.4, 0.8)):
    """Color sampling shared by shader_noise / shader_voronoi / shader_speckle."""

    bright_color = _hsv2rgba(base_hue, float(uniform(*bright_sat)), float(_mlog_uniform(0.05, 0.2)))
    dark_color = _hsv2rgba((base_hue + float(uniform(-0.05, 0.05))) % 1,
                           float(uniform(0.4, 0.8)),
                           float(_mlog_uniform(0.01, 0.05)))
    subsurface_color = _hsv2rgba((base_hue + float(uniform(-0.05, 0.05))) % 1,
                                 float(uniform(0.4, 0.8)),
                                 float(_mlog_uniform(0.05, 0.2)))
    light_color = _hsv2rgba(base_hue, float(uniform(0, 0.1)), float(uniform(0.2, 0.8)))
    return bright_color, dark_color, subsurface_color, light_color

def _apply_principled(nt, ln, color_out, subsurface_color):
    """Shared Principled BSDF wrap-up for all 4 cap shader variants."""

    roughness = float(uniform(0.2, 0.5) if uniform(0, 1) < 0.5 else uniform(0.8, 1.0))
    specular = float(uniform(0.2, 0.8))
    clearcoat = float(uniform(0.2, 0.5) if uniform(0, 1) < 0.25 else 0)

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(color_out, bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs[_spec_socket(bsdf)].default_value = specular
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = clearcoat
    elif "Clearcoat" in bsdf.inputs:
        bsdf.inputs["Clearcoat"].default_value = clearcoat
    if "Subsurface Color" in bsdf.inputs:
        bsdf.inputs["Subsurface Color"].default_value = subsurface_color
    bsdf.inputs["Subsurface Weight"].default_value = 0.01
    bsdf.inputs["Subsurface Radius"].default_value = (0.05, 0.05, 0.05)
    return bsdf

def make_shader_cap(base_hue, name="MushroomCap_Mat"):
    """Translated from MushroomCapFactory.shader_cap(nw, base_hue)."""

    bright_color = _hsv2rgba(base_hue, float(uniform(0.6, 0.8)), float(_mlog_uniform(0.05, 0.2)))
    dark_color = _hsv2rgba((base_hue + float(uniform(-0.05, 0.05))) % 1,
                           float(uniform(0.4, 0.8)),
                           float(_mlog_uniform(0.01, 0.05)))
    light_color = _hsv2rgba(base_hue, float(uniform(0, 0.1)), float(uniform(0.6, 0.8)))
    subsurface_color = _hsv2rgba((base_hue + float(uniform(-0.05, 0.05))) % 1,
                                 float(uniform(0.6, 0.8)),
                                 float(_mlog_uniform(0.05, 0.2)))
    anchors = [0.0, 0.3, 0.6, 1.0] if uniform(0, 1) < 0.5 else [0.0, 0.4, 0.7, 1.0]
    # Float curve anchors (sampled regardless of where applied)
    fc_a0 = (float(uniform(0, 0.2)), float(uniform(0.95, 0.98)))
    fc_a1 = (float(uniform(0.2, 0.4)), float(uniform(0.98, 1)))
    fc_a2 = (0.8, 1.0)

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new

    m500 = _noise_as_musgrave(nt, ln, 500.0)
    cr = _color_ramp_hsv(nt, ln, m500, anchors,
                          [dark_color, dark_color, bright_color, bright_color])

    # Attribute 'z' from geo_xyz (normalized |z| in [0,1])
    z_attr = nt.nodes.new("ShaderNodeAttribute")
    z_attr.attribute_name = "z"
    # Use the Fac output (value-like float broadcast)
    z_fac = z_attr.outputs.get("Fac") or z_attr.outputs[-1]
    musg_curve = _float_curve(nt, ln, z_fac, [fc_a0, fc_a1, fc_a2])
    light_rgb = nt.nodes.new("ShaderNodeRGB")
    light_rgb.outputs[0].default_value = light_color

    mix_c = _mix_rgba(nt, ln, musg_curve.outputs["Value"],
                      light_rgb.outputs[0], cr.outputs["Color"])

    bsdf = _apply_principled(nt, ln, mix_c.outputs[2], subsurface_color)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def make_shader_noise(base_hue, name="MushroomCap_Mat"):
    """Translated from MushroomCapFactory.shader_noise(nw, base_hue)."""

    bright_color, dark_color, subsurface_color, light_color = _sample_common_colors(base_hue)
    anchors = [0.0, 0.3, 0.6, 1.0] if uniform(0, 1) < 0.5 else [0.0, 0.4, 0.7, 1.0]

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new

    m500 = _noise_as_musgrave(nt, ln, 500.0)
    cr = _color_ramp_hsv(nt, ln, m500, anchors,
                          [dark_color, dark_color, bright_color, bright_color])

    # ratio: float_curve(musgrave(10), [(.52,0),(.56,.2),(.6,0)]) * map_range(musgrave(20), -.2,.1,0,1)
    m10 = _noise_as_musgrave(nt, ln, 10.0)
    ratio_curve = _float_curve(nt, ln, m10, [(0.52, 0.0), (0.56, 0.2), (0.6, 0.0)])

    # MusgraveTexture (raw) at scale=20 -> MapRange(-0.2, 0.1, 0, 1)
    m20_raw = _raw_musgrave_noise(nt, ln, 20.0)
    mr = _map_range(nt, ln, m20_raw, -0.2, 0.1, 0, 1)

    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    ln(ratio_curve.outputs["Value"], mul.inputs[0])
    ln(mr.outputs["Result"], mul.inputs[1])

    mix_c = _mix_rgba(nt, ln, mul.outputs[0], cr.outputs["Color"],
                      _rgb_node(nt, light_color).outputs[0])

    bsdf = _apply_principled(nt, ln, mix_c.outputs[2], subsurface_color)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def _rgb_node(nt, color):
    node = nt.nodes.new("ShaderNodeRGB")
    node.outputs[0].default_value = color
    return node

def make_shader_speckle(base_hue, name="MushroomCap_Mat"):
    """Translated from MushroomCapFactory.shader_speckle(nw, base_hue)."""

    bright_color, dark_color, subsurface_color, light_color = _sample_common_colors(base_hue)
    anchors = [0.0, 0.3, 0.6, 1.0] if uniform(0, 1) < 0.5 else [0.0, 0.4, 0.7, 1.0]

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new

    m500 = _noise_as_musgrave(nt, ln, 500.0)
    cr = _color_ramp_hsv(nt, ln, m500, anchors,
                          [dark_color, dark_color, bright_color, bright_color])

    m50 = _noise_as_musgrave(nt, ln, 50.0)
    speckle_curve = _float_curve(nt, ln, m50, [(0.7, 0.0), (0.72, 1.0)])

    mix_c = _mix_rgba(nt, ln, speckle_curve.outputs["Value"],
                      cr.outputs["Color"], _rgb_node(nt, light_color).outputs[0])

    bsdf = _apply_principled(nt, ln, mix_c.outputs[2], subsurface_color)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def make_shader_voronoi(base_hue, name="MushroomCap_Mat"):
    """Translated from MushroomCapFactory.shader_voronoi(nw, base_hue)."""

    bright_color = _hsv2rgba(base_hue, float(uniform(0.4, 0.8)), float(_mlog_uniform(0.05, 0.2)))
    dark_color = _hsv2rgba((base_hue + float(uniform(-0.05, 0.05))) % 1,
                           float(uniform(0.4, 0.8)),
                           float(_mlog_uniform(0.01, 0.05)))
    subsurface_color = _hsv2rgba((base_hue + float(uniform(-0.05, 0.05))) % 1,
                                 float(uniform(0.4, 0.8)),
                                 float(_mlog_uniform(0.05, 0.2)))
    light_color = _hsv2rgba(base_hue, float(uniform(0, 0.1)), float(uniform(0.2, 0.8)))
    anchors = [0.0, 0.3, 0.6, 1.0] if uniform(0, 1) < 0.5 else [0.0, 0.4, 0.7, 1.0]
    r_mid = float(uniform(0.5, 0.7))
    vor_scale = float(uniform(2.0, 2.5))

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new

    m500 = _noise_as_musgrave(nt, ln, 500.0)
    cr = _color_ramp_hsv(nt, ln, m500, anchors,
                          [dark_color, dark_color, bright_color, bright_color])

    # Named attributes 'x' and 'y' (from geo_xyz)
    x_attr = nt.nodes.new("ShaderNodeAttribute"); x_attr.attribute_name = "x"
    y_attr = nt.nodes.new("ShaderNodeAttribute"); y_attr.attribute_name = "y"
    x_out = x_attr.outputs.get("Fac") or x_attr.outputs[-1]
    y_out = y_attr.outputs.get("Fac") or y_attr.outputs[-1]

    # r = sqrt(x^2 + y^2)
    x_sq = nt.nodes.new("ShaderNodeMath"); x_sq.operation = "POWER"
    ln(x_out, x_sq.inputs[0]); x_sq.inputs[1].default_value = 2.0
    y_sq = nt.nodes.new("ShaderNodeMath"); y_sq.operation = "POWER"
    ln(y_out, y_sq.inputs[0]); y_sq.inputs[1].default_value = 2.0
    r_sum = nt.nodes.new("ShaderNodeMath"); r_sum.operation = "ADD"
    ln(x_sq.outputs[0], r_sum.inputs[0]); ln(y_sq.outputs[0], r_sum.inputs[1])
    r_node = nt.nodes.new("ShaderNodeMath"); r_node.operation = "POWER"
    ln(r_sum.outputs[0], r_node.inputs[0]); r_node.inputs[1].default_value = 0.5

    # coord = (x, y, 0) * float_curve(r, [(0,1),(r_mid,2),(1,8)])
    combine = nt.nodes.new("ShaderNodeCombineXYZ")
    ln(x_out, combine.inputs[0])
    ln(y_out, combine.inputs[1])
    combine.inputs[2].default_value = 0.0
    r_curve = _float_curve(nt, ln, r_node.outputs[0], [(0, 1), (r_mid, 2), (1, 8)])
    coord_scale = nt.nodes.new("ShaderNodeVectorMath"); coord_scale.operation = "SCALE"
    ln(combine.outputs[0], coord_scale.inputs[0])
    ln(r_curve.outputs["Value"], coord_scale.inputs["Scale"])

    # perturbed = coord + scale(noise2d, 0.2)
    noise2d = nt.nodes.new("ShaderNodeTexNoise")
    try:
        noise2d.noise_dimensions = "2D"
    except Exception:
        pass
    noise2d_scale = nt.nodes.new("ShaderNodeVectorMath"); noise2d_scale.operation = "SCALE"
    # NoiseTexture returns a Color as well; nw.scale() on a NoiseTexture node
    # uses the first output (Fac/scalar broadcast). Use its Color output (vector).
    noise_color = noise2d.outputs.get("Color") or noise2d.outputs[-1]
    ln(noise_color, noise2d_scale.inputs[0])
    noise2d_scale.inputs["Scale"].default_value = 0.2

    perturbed = nt.nodes.new("ShaderNodeVectorMath"); perturbed.operation = "ADD"
    ln(coord_scale.outputs[0], perturbed.inputs[0])
    ln(noise2d_scale.outputs[0], perturbed.inputs[1])

    # voronoi distance-to-edge 2D
    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    try:
        voronoi.voronoi_dimensions = "2D"
    except Exception:
        pass
    voronoi.feature = "DISTANCE_TO_EDGE"
    voronoi.inputs["Scale"].default_value = vor_scale
    ln(perturbed.outputs[0], voronoi.inputs["Vector"])

    # ratio = voronoi / (1 + 5 * r^2)
    r_sq2 = nt.nodes.new("ShaderNodeMath"); r_sq2.operation = "POWER"
    ln(r_node.outputs[0], r_sq2.inputs[0]); r_sq2.inputs[1].default_value = 2.0
    five_r = nt.nodes.new("ShaderNodeMath"); five_r.operation = "MULTIPLY"
    ln(r_sq2.outputs[0], five_r.inputs[0]); five_r.inputs[1].default_value = 5.0
    plus_one = nt.nodes.new("ShaderNodeMath"); plus_one.operation = "ADD"
    ln(five_r.outputs[0], plus_one.inputs[0]); plus_one.inputs[1].default_value = 1.0
    ratio_div = nt.nodes.new("ShaderNodeMath"); ratio_div.operation = "DIVIDE"
    ln(voronoi.outputs["Distance"], ratio_div.inputs[0])
    ln(plus_one.outputs[0], ratio_div.inputs[1])

    ratio_curve = _float_curve(nt, ln, ratio_div.outputs[0], [(0, 0.4), (0.04, 0.0)])

    # ratio *= map_range(musgrave(20), -0.2, 0.1, 0, 1)
    m20_raw = _raw_musgrave_noise(nt, ln, 20.0)
    mr = _map_range(nt, ln, m20_raw, -0.2, 0.1, 0, 1)
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    ln(ratio_curve.outputs["Value"], mul.inputs[0])
    ln(mr.outputs["Result"], mul.inputs[1])

    mix_c = _mix_rgba(nt, ln, mul.outputs[0], cr.outputs["Color"],
                      _rgb_node(nt, light_color).outputs[0])

    bsdf = _apply_principled(nt, ln, mix_c.outputs[2], subsurface_color)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def make_default_shader(base_hue, name="MushroomGill_Mat"):
    """Translated from MushroomCapFactory._default_shader(nw, base_hue).
    Plain Principled BSDF with HSV-sampled color. Used for gill material."""

    color = (*colorsys.hsv_to_rgb(
        (base_hue + float(uniform(-0.1, 0.1))) % 1,
        float(uniform(0.1, 0.3)),
        float(_mlog_uniform(0.02, 0.5)),
    ), 1.0)
    roughness = 0.8
    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def _sample_base_hue():
    """Mirrors MushroomCapFactory.__init__ base_hue logic."""

    if uniform(0, 1) >= 0.4:
        return float(uniform(0.02, 0.15))
    else:
        return float(uniform(0, 1))

def make_category_mat(seed, name="MushroomCap_Material"):
    """Phase 1 entry: samples base_hue + cap shader variant + returns (cap_mat, gill_mat).

    Sampling order mirrors MushroomCapFactory.__init__ in
      1. base_hue (uniform)
      2. shader weights sampled with weights [2,1,1,1]
      3. shader's own uniforms (via shaderfunc_to_material)
      4. _default_shader's uniforms (material_func())
    """
    # Knuth multiplicative hash for material seed (so each seed produces a
    # visually distinct shader despite Blender 5.0 RNG quirks).
    seed_all(((int(seed) + 1) * 2654435761) & 0xFFFFFFFF)

    base_hue = _sample_base_hue()

    shader_variants = [
        (make_shader_cap, 2),
        (make_shader_noise, 1),
        (make_shader_voronoi, 1),
        (make_shader_speckle, 1),
    ]
    fns, weights = zip(*shader_variants)
    weights = np.array(weights, dtype=float)
    idx = int(np.random.choice(len(fns), p=weights / weights.sum()))
    cap_mat = fns[idx](base_hue, name=name + "_cap")

    gill_mat = make_default_shader(base_hue, name=name + "_gill")

    cap_mat.use_fake_user = True
    gill_mat.use_fake_user = True
    return cap_mat, gill_mat

# ---------------------------------------------------------------------------
# Blender helper utilities (copied verbatim from objects_blender/)
# ---------------------------------------------------------------------------
def _select_none():
    for o in list(bpy.context.selected_objects):
        o.select_set(False)
    if bpy.context.active_object:
        bpy.context.active_object.select_set(False)

def _set_active(o):
    bpy.context.view_layer.objects.active = o
    if o is not None:
        o.select_set(True)

class Suppress:
    def __enter__(self): return self
    def __exit__(self, *exc): return True

class ViewportMode:
    def __init__(self, obj, mode):
        self.obj = obj; self.mode = mode
    def __enter__(self):
        self.prev_active = bpy.context.view_layer.objects.active
        _select_none(); _set_active(self.obj)
        self.prev_mode = getattr(bpy.context.object, "mode", "OBJECT") if bpy.context.object else "OBJECT"
        if bpy.context.object and self.prev_mode != self.mode:
            bpy.ops.object.mode_set(mode=self.mode)
        return self
    def __exit__(self, *_):
        try:
            if bpy.context.object and bpy.context.object.mode != self.prev_mode:
                bpy.ops.object.mode_set(mode=self.prev_mode)
        except Exception:
            try: bpy.ops.object.mode_set(mode="OBJECT")
            except Exception: pass
        if self.prev_active is not None:
            _set_active(self.prev_active)

class SelectObjects:
    def __init__(self, objs, active=0):
        self.objs = objs if isinstance(objs, (list, tuple)) else [objs]
        self.active_idx = active
    def __enter__(self):
        self.prev_sel = list(bpy.context.selected_objects)
        self.prev_active = bpy.context.view_layer.objects.active
        _select_none()
        for o in self.objs:
            if o is not None: o.select_set(True)
        if self.objs:
            _set_active(self.objs[self.active_idx])
        return self
    def __exit__(self, *_):
        _select_none()
        for o in self.prev_sel or []:
            if o and o.name in bpy.data.objects: o.select_set(True)
        if self.prev_active is not None and self.prev_active.name in bpy.data.objects:
            _set_active(self.prev_active)

def apply_transform(obj, loc=False, rot=True, scale=True):
    with SelectObjects(obj):
        bpy.ops.object.transform_apply(location=loc, rotation=rot, scale=scale)

def delete(objs):
    if not isinstance(objs, (list, tuple)):
        objs = [objs]
    for o in objs:
        if o is None: continue
        mesh = o.data if getattr(o, "type", None) == "MESH" else None
        try: bpy.data.objects.remove(o, do_unlink=True)
        except Exception: pass
        try:
            if mesh is not None and mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        except Exception: pass

def modify_mesh(obj, type_, apply=True, name=None, return_mod=False, **kwargs):
    if name is None:
        name = f"modify_mesh({type_})"
    mod = obj.modifiers.new(name=name, type=type_)
    mod.show_viewport = not apply
    for k, v in kwargs.items():
        try: setattr(mod, k, v)
        except Exception: pass
    if apply:
        with SelectObjects(obj):
            bpy.ops.object.modifier_apply(modifier=mod.name)
    return (obj, None if apply else mod) if return_mod else obj

# ---------------------------------------------------------------------------
# Mesh creation helpers
# ---------------------------------------------------------------------------
def data2mesh(vertices=(), edges=(), faces=(), name=""):
    mesh = bpy.data.meshes.new(name or "mesh")
    mesh.from_pydata(list(vertices), list(edges), list(faces))
    mesh.update()
    return mesh

def mesh2obj(mesh):
    obj = bpy.data.objects.new(mesh.name or "obj", mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    return obj

def join_objects(objs):
    if not isinstance(objs, list):
        objs = [objs]
    objs = [o for o in objs if o is not None]
    if len(objs) == 0:
        return None
    if len(objs) == 1:
        return objs[0]
    _select_none()
    for o in objs:
        o.select_set(True)
    _set_active(objs[0])
    bpy.ops.object.join()
    out = bpy.context.active_object
    out.location = (0, 0, 0)
    out.rotation_euler = (0, 0, 0)
    out.scale = (1, 1, 1)
    _select_none()
    return out

def read_co(obj):
    arr = np.zeros(len(obj.data.vertices) * 3, dtype=float)
    obj.data.vertices.foreach_get("co", arr)
    return arr.reshape(-1, 3)

def write_co(obj, arr):
    obj.data.vertices.foreach_set("co", np.asarray(arr, dtype=float).reshape(-1))
    obj.data.update()

def displace_vertices(obj, fn):
    co = read_co(obj)
    x, y, z = co.T
    d = fn(x, y, z)
    for i in range(3):
        co[:, i] += np.asarray(d[i])
    write_co(obj, co)

def subsurface2face_size(obj, face_size):
    arr = np.zeros(len(obj.data.polygons), dtype=float)
    if len(arr) == 0:
        return
    obj.data.polygons.foreach_get("area", arr)
    area = float(np.mean(arr))
    if area <= 1e-9 or face_size <= 0:
        return
    try:
        levels = int(np.ceil(np.log2(area / face_size)))
    except Exception:
        return
    if levels > 0:
        modify_mesh(obj, "SUBSURF", apply=True, levels=levels, render_levels=levels)

def remesh_with_attrs(obj, face_size):
    modify_mesh(obj, "REMESH", apply=True, voxel_size=face_size)
    return obj

def remesh_fill(obj, resolution=0.005):
    zmax = float(read_co(obj)[:, 2].max()) if len(obj.data.vertices) else 0.0
    modify_mesh(obj, "SOLIDIFY", apply=True, thickness=0.1)
    depth = int(np.ceil(np.log2((max(obj.dimensions) + 0.01) / max(resolution, 1e-5))))
    depth = max(depth, 4)
    modify_mesh(obj, "REMESH", apply=True, mode="SHARP", octree_depth=depth, use_remove_disconnected=False)
    co = read_co(obj)
    to_del = np.where(co[:, 2] > zmax + 1e-4)[0]
    if len(to_del):
        with ViewportMode(obj, "EDIT"):
            bm = bmesh.from_edit_mesh(obj.data)
            bm.verts.ensure_lookup_table()
            bmesh.ops.delete(bm, geom=[bm.verts[i] for i in to_del if i < len(bm.verts)], context="VERTS")
            bmesh.update_edit_mesh(obj.data)
    return obj

# ---------------------------------------------------------------------------
# Bezier curve + spin
# ---------------------------------------------------------------------------
def bezier_curve(anchors, vector_locations=(), resolution=None, to_mesh=True):
    n = [len(r) for r in anchors if isinstance(r, Sized)][0]
    anchors = np.array([
        np.array(r, dtype=float) if isinstance(r, Sized) else np.full(n, r)
        for r in anchors
    ])
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0))
    obj = bpy.context.active_object
    if n > 2:
        with ViewportMode(obj, "EDIT"):
            bpy.ops.curve.subdivide(number_cuts=n - 2)
    points = obj.data.splines[0].bezier_points
    for i in range(n):
        points[i].co = anchors[:, i]
    for i in range(n):
        if i in vector_locations:
            points[i].handle_left_type = "VECTOR"
            points[i].handle_right_type = "VECTOR"
        else:
            points[i].handle_left_type = "AUTO"
            points[i].handle_right_type = "AUTO"
    obj.data.splines[0].resolution_u = resolution if resolution is not None else 12
    if not to_mesh:
        return obj
    return curve2mesh(obj)

def curve2mesh(obj):
    points = obj.data.splines[0].bezier_points
    cos = np.array([p.co for p in points])
    length = np.linalg.norm(cos[:-1] - cos[1:], axis=-1) if len(cos) > 1 else np.array([])
    min_length = 5e-3
    with ViewportMode(obj, "EDIT"):
        for p in obj.data.splines[0].bezier_points:
            if p.handle_left_type == "FREE":
                p.handle_left_type = "ALIGNED"
            if p.handle_right_type == "FREE":
                p.handle_right_type = "ALIGNED"
        for i in reversed(range(max(len(points) - 1, 0))):
            points = list(obj.data.splines[0].bezier_points)
            number_cuts = min(int(length[i] / min_length) - 1, 64)
            if number_cuts < 0:
                continue
            bpy.ops.curve.select_all(action="DESELECT")
            points[i].select_control_point = True
            points[i + 1].select_control_point = True
            bpy.ops.curve.subdivide(number_cuts=number_cuts)
    obj.data.splines[0].resolution_u = 1
    with SelectObjects(obj):
        bpy.ops.object.convert(target="MESH")
    obj = bpy.context.active_object
    modify_mesh(obj, "WELD", apply=True, merge_threshold=1e-3)
    return obj

def spin(anchors, vector_locations=(), resolution=None, rotation_resolution=None,
         axis=(0, 0, 1), loop=False, dupli=False):
    obj = bezier_curve(anchors, vector_locations, resolution)
    co = read_co(obj)
    axis_v = np.array(axis, dtype=float)
    mean_radius = np.mean(
        np.linalg.norm(co - (co @ axis_v)[:, None] * axis_v, axis=-1)
    ) if len(co) else 0.05
    if rotation_resolution is None:
        rotation_resolution = min(max(int(2 * np.pi * max(mean_radius, 1e-3) / 5e-3), 8), 128)
    modify_mesh(obj, "WELD", apply=True, merge_threshold=1e-3)
    if loop:
        with ViewportMode(obj, "EDIT"), Suppress():
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.fill()
        remesh_fill(obj)
    with ViewportMode(obj, "EDIT"), Suppress():
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.spin(steps=rotation_resolution, angle=np.pi * 2, axis=axis, dupli=dupli)
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.remove_doubles(threshold=1e-3)
    return obj

# ---------------------------------------------------------------------------
# GeoNodes modifier helper
# ---------------------------------------------------------------------------

def _apply_geomod(obj, node_group, apply=True):
    """Add a pre-built GeoNodes modifier to obj, optionally apply it."""

    _select_none(); _set_active(obj)
    mod = obj.modifiers.new(name="GeoNodes", type="NODES")
    mod.node_group = node_group
    if apply:
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.node_groups.remove(node_group)
    _select_none()
    return mod

def _noise_fac_output(node):
    """Return the scalar factor output of a NoiseTexture node (Blender 4.x/5.x compat)."""

    for name in ("Fac", "Factor"):
        if name in node.outputs:
            return node.outputs[name]
    return node.outputs[0]

# ---------------------------------------------------------------------------
# GeoNodes builders (direct bpy API, no NodeWrangler)
# ---------------------------------------------------------------------------

def _build_geo_extension(noise_strength=0.2, noise_scale=2.0):
    """Build a GeoNodes tree that displaces geometry outward with noise."""

    noise_strength = uniform(noise_strength / 2, noise_strength)
    noise_scale = uniform(noise_scale * 0.7, noise_scale * 1.4)
    direction_offset = uniform(-1, 1, 3)

    ng = bpy.data.node_groups.new("geo_extension", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi = ng.nodes.new("NodeGroupInput")
    go = ng.nodes.new("NodeGroupOutput"); go.is_active_output = True

    pos = ng.nodes.new("GeometryNodeInputPosition")

    length_node = ng.nodes.new("ShaderNodeVectorMath"); length_node.operation = "LENGTH"
    ng.links.new(pos.outputs[0], length_node.inputs[0])

    inv_len = ng.nodes.new("ShaderNodeMath"); inv_len.operation = "DIVIDE"
    inv_len.inputs[0].default_value = 1.0
    ng.links.new(length_node.outputs["Value"], inv_len.inputs[1])

    dir_scale = ng.nodes.new("ShaderNodeVectorMath"); dir_scale.operation = "SCALE"
    ng.links.new(pos.outputs[0], dir_scale.inputs[0])
    ng.links.new(inv_len.outputs[0], dir_scale.inputs["Scale"])

    dir_add = ng.nodes.new("ShaderNodeVectorMath"); dir_add.operation = "ADD"
    ng.links.new(dir_scale.outputs[0], dir_add.inputs[0])
    dir_add.inputs[1].default_value = tuple(float(v) for v in direction_offset)

    noise_tex = ng.nodes.new("ShaderNodeTexNoise")
    ng.links.new(dir_add.outputs[0], noise_tex.inputs["Vector"])
    noise_tex.inputs["Scale"].default_value = noise_scale

    add_quarter = ng.nodes.new("ShaderNodeMath"); add_quarter.operation = "ADD"
    ng.links.new(_noise_fac_output(noise_tex), add_quarter.inputs[0])
    add_quarter.inputs[1].default_value = 0.25

    mul_strength = ng.nodes.new("ShaderNodeMath"); mul_strength.operation = "MULTIPLY"
    ng.links.new(add_quarter.outputs[0], mul_strength.inputs[0])
    mul_strength.inputs[1].default_value = noise_strength

    offset_scale = ng.nodes.new("ShaderNodeVectorMath"); offset_scale.operation = "SCALE"
    ng.links.new(pos.outputs[0], offset_scale.inputs[0])
    ng.links.new(mul_strength.outputs[0], offset_scale.inputs["Scale"])

    set_pos = ng.nodes.new("GeometryNodeSetPosition")
    ng.links.new(gi.outputs[0], set_pos.inputs["Geometry"])
    ng.links.new(offset_scale.outputs[0], set_pos.inputs["Offset"])

    ng.links.new(set_pos.outputs[0], go.inputs[0])
    return ng

def _build_geo_xyz():
    """Build GeoNodes tree: store normalized |x|, |y|, |z| as named attributes."""

    ng = bpy.data.node_groups.new("geo_xyz", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi = ng.nodes.new("NodeGroupInput")
    go = ng.nodes.new("NodeGroupOutput"); go.is_active_output = True

    pos = ng.nodes.new("GeometryNodeInputPosition")
    sep = ng.nodes.new("ShaderNodeSeparateXYZ")
    ng.links.new(pos.outputs[0], sep.inputs[0])

    prev_geom = gi.outputs[0]
    for axis_name, axis_out in [("x", "X"), ("y", "Y"), ("z", "Z")]:
        abs_node = ng.nodes.new("ShaderNodeMath"); abs_node.operation = "ABSOLUTE"
        ng.links.new(sep.outputs[axis_out], abs_node.inputs[0])

        attr_stat = ng.nodes.new("GeometryNodeAttributeStatistic")
        ng.links.new(prev_geom, attr_stat.inputs["Geometry"])
        ng.links.new(abs_node.outputs[0], attr_stat.inputs[2])

        div_node = ng.nodes.new("ShaderNodeMath"); div_node.operation = "DIVIDE"
        ng.links.new(abs_node.outputs[0], div_node.inputs[0])
        ng.links.new(attr_stat.outputs["Max"], div_node.inputs[1])

        store = ng.nodes.new("GeometryNodeStoreNamedAttribute")
        ng.links.new(prev_geom, store.inputs["Geometry"])
        store.inputs["Name"].default_value = axis_name
        ng.links.new(div_node.outputs[0], store.inputs["Value"])

        prev_geom = store.outputs["Geometry"]

    ng.links.new(prev_geom, go.inputs[0])
    return ng

def _build_geo_morel(voronoi_scale, randomness):
    """Build GeoNodes tree: store voronoi distance-to-edge < 0.05 as 'morel' attribute."""

    ng = bpy.data.node_groups.new("geo_morel", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi = ng.nodes.new("NodeGroupInput")
    go = ng.nodes.new("NodeGroupOutput"); go.is_active_output = True

    voronoi = ng.nodes.new("ShaderNodeTexVoronoi")
    voronoi.feature = "DISTANCE_TO_EDGE"
    voronoi.inputs["Scale"].default_value = voronoi_scale
    voronoi.inputs["Randomness"].default_value = randomness

    compare = ng.nodes.new("FunctionNodeCompare")
    compare.operation = "LESS_THAN"
    ng.links.new(voronoi.outputs["Distance"], compare.inputs[0])
    compare.inputs[1].default_value = 0.05

    store = ng.nodes.new("GeometryNodeStoreNamedAttribute")
    ng.links.new(gi.outputs[0], store.inputs["Geometry"])
    store.inputs["Name"].default_value = "morel"
    ng.links.new(compare.outputs["Result"], store.inputs["Value"])

    ng.links.new(store.outputs["Geometry"], go.inputs[0])
    return ng

# ---------------------------------------------------------------------------
# Surface stub helper
# ---------------------------------------------------------------------------

def _set_active_attribute(obj, name):
    attrs = obj.data.attributes
    for i, a in enumerate(attrs):
        if a.name == name:
            attrs.active_index = i
            try: attrs.active = attrs[i]
            except Exception: pass
            return

# ---------------------------------------------------------------------------
# Cap shape configs
# ---------------------------------------------------------------------------

def _campanulate():
    x = uniform(0.12, 0.15)
    return {
        "x_anchors": [0, x, x, 0.08, 0.04, 0],
        "z_anchors": [0, 0, uniform(0.03, 0.05), uniform(0.1, 0.12), uniform(0.16, 0.2), 0.2],
        "vector_locations": [],
        "has_gill": True,
    }

def _conical():
    z = uniform(0.2, 0.3)
    return {
        "x_anchors": [0, uniform(0.12, 0.15), 0.01, 0],
        "z_anchors": [0, 0, z, z],
        "vector_locations": [1],
        "has_gill": True,
    }

def _convex():
    z = uniform(0.14, 0.16)
    return {
        "x_anchors": [0, 0.15, 0.12, 0.01, 0],
        "z_anchors": [0, 0, uniform(0.04, 0.06), z, z],
        "vector_locations": [1],
        "has_gill": True,
    }

def _depressed():
    z = uniform(0.03, 0.05)
    return {
        "x_anchors": [0, 0.15, 0.12, 0],
        "z_anchors": [0, 0, uniform(0.06, 0.08), z],
        "vector_locations": [1],
        "has_gill": True,
    }

def _flat():
    z = uniform(0.05, 0.07)
    return {
        "x_anchors": [0, 0.15, 0.12, 0],
        "z_anchors": [0, 0, z, z],
        "vector_locations": [1],
        "has_gill": True,
    }

def _infundiuliform():
    z = uniform(0.08, 0.12)
    x = uniform(0.12, 0.15)
    return {
        "x_anchors": [0, 0.03, x, x - 0.01, 0],
        "z_anchors": [0, 0, z, z + uniform(0.005, 0.01), 0.02],
        "vector_locations": [],
        "has_gill": False,
    }

def _ovate():
    z = uniform(0.2, 0.3)
    return {
        "x_anchors": [0, uniform(0.12, 0.15), 0.08, 0.01, 0],
        "z_anchors": [0, 0, 0.8 * z, z, z],
        "vector_locations": [1],
        "has_gill": True,
    }

def _umbillicate():
    z = uniform(0.03, 0.05)
    return {
        "x_anchors": [0, 0.15, 0.12, 0.02, 0],
        "z_anchors": [0, 0.04, uniform(0.06, 0.08), z + 0.02, z],
        "vector_locations": [],
        "has_gill": False,
    }

def _umbonate():
    z = uniform(0.05, 0.07)
    z_ = z + uniform(0.02, 0.04)
    return {
        "x_anchors": [0, 0.15, 0.12, 0.06, 0.02, 0],
        "z_anchors": [0, 0, z - 0.01, z, z_, z_],
        "vector_locations": [1],
        "has_gill": True,
    }

# ---------------------------------------------------------------------------
# Parameter sampling (KEEP SEED -- many np.random calls)
# ---------------------------------------------------------------------------

def sample_params(seed):
    """Sample all factory params using the raw factory_seed (not hashed), matching __init__."""

    with FixedSeed(seed):
        x_scale, z_scale = uniform(0.7, 1.4, 2)

        cap_configs = [
            _campanulate, _conical, _convex, _depressed, _flat,
            _infundiuliform, _ovate, _umbillicate, _umbonate,
        ]
        config_weights = np.array([2, 2, 2, 1, 2, 1, 2, 1, 1])
        cap_config_fn = np.random.choice(cap_configs, p=config_weights / config_weights.sum())
        cap_config = cap_config_fn()
        cap_config = {
            **cap_config,
            "x_anchors": [v * x_scale for v in cap_config["x_anchors"]],
            "z_anchors": [v * z_scale for v in cap_config["z_anchors"]],
        }

        radius = max(cap_config["x_anchors"])
        inner_radius = float(log_uniform(0.2, 0.35)) * radius

        def _adnexed_gill():
            return {
                "x_anchors": [radius, (radius + inner_radius) / 2, inner_radius, inner_radius, radius],
                "z_anchors": [0, -uniform(0.05, 0.08), -uniform(0, 0.02), 0, 0],
                "vector_locations": [3],
            }

        def _decurrent_gill():
            return {
                "x_anchors": [radius, (radius + inner_radius) / 2, inner_radius, 0, radius],
                "z_anchors": [0, -uniform(0.05, 0.08), -uniform(0.08, 0.1), 0, 0],
                "vector_locations": [2],
            }

        gill_configs = [_adnexed_gill, _decurrent_gill, None]
        gill_weights = np.array([1, 1, 1])
        gill_choice = np.random.choice([0, 1, 2], p=gill_weights / gill_weights.sum())
        if not cap_config["has_gill"]:
            gill_config = None
        elif gill_choice == 2:
            gill_config = None
        else:
            gill_config = gill_configs[gill_choice]()

        shader_weights = np.array([2, 1, 1, 1])
        _shader_idx = np.random.choice(4, p=shader_weights / shader_weights.sum())
        is_morel = uniform(0, 1) < 0.5 and _shader_idx == 0

        morel_voronoi_scale = float(uniform(15, 20))
        morel_randomness = float(uniform(0.5, 1))

        n_cuts = 0
        cut_angles = []
        cut_widths = []
        cut_depths = []
        cut_rotations = []
        if max(cap_config["x_anchors"]) <= 0.1:
            n_cuts = int(np.random.randint(0, 5))
            cut_angles = list(polygon_angles(n_cuts, np.pi / 4, np.pi * 2))
            for _ in range(n_cuts):
                cut_widths.append(float(uniform(0.15, 0.2) * 0.4))
                cut_depths.append(float(radius * uniform(0.4, 0.7)))
                cut_rotations.append(float(cut_angles[len(cut_rotations)] + uniform(-np.pi / 4, np.pi / 4)))

        gill_rotation_resolution = int(np.random.randint(32, 64))

        texture_type = str(np.random.choice(["STUCCI", "MARBLE"]))
        texture_noise_scale = float(log_uniform(0.01, 0.05))

        twist_angle = float(uniform(-np.pi / 4, np.pi / 4))

        vertex_scale_factors = [float(v) for v in uniform(-0.25, 0.25, 4)]

    return {
        "x_scale": float(x_scale),
        "z_scale": float(z_scale),
        "cap_config": cap_config,
        "radius": float(radius),
        "inner_radius": float(inner_radius),
        "gill_config": gill_config,
        "is_morel": bool(is_morel),
        "morel_voronoi_scale": morel_voronoi_scale,
        "morel_randomness": morel_randomness,
        "n_cuts": n_cuts,
        "cut_angles": cut_angles,
        "cut_widths": cut_widths,
        "cut_depths": cut_depths,
        "cut_rotations": cut_rotations,
        "gill_rotation_resolution": gill_rotation_resolution,
        "texture_type": texture_type,
        "texture_noise_scale": texture_noise_scale,
        "twist_angle": twist_angle,
        "vertex_scale_factors": vertex_scale_factors,
    }

SEED = int(os.environ.get("SEED", 0))
MAT_CAP, MAT_GILL = make_category_mat(SEED, "MushroomCapFactory_Material")

# ---------------------------------------------------------------------------
# Build the mushroom cap
# ---------------------------------------------------------------------------
def build(seed=SEED, face_size=0.005):
    """Build a MushroomCapFactory mesh with the given seed (materials already captured)."""

    params = sample_params(seed)

    # Seed for create_asset random calls (geo_extension, etc.)
    build_seed = int_hash((seed, 0))
    np.random.seed(build_seed)
    random.seed(build_seed)

    cap_config = params["cap_config"]

    # 1. Create cap body via spin
    anchors = cap_config["x_anchors"], 0, cap_config["z_anchors"]
    obj = spin(anchors, cap_config["vector_locations"])

    # 2. Apply cuts (only for small caps)
    if params["n_cuts"] > 0:
        for i in range(params["n_cuts"]):
            angle = params["cut_angles"][i]
            width = params["cut_widths"][i]
            depth = params["cut_depths"][i]
            rot = params["cut_rotations"][i]
            vertices = [
                [0, 0, 0.4], [0.4, -width, 0.4], [0.4, width, 0.4],
                [0, 0, -1], [0.4, -width, -0.01], [0.4, width, -0.01],
            ]
            faces = [[0, 1, 2], [1, 0, 3, 4], [2, 1, 4, 5], [0, 2, 5, 3], [5, 4, 3]]
            cutter = mesh2obj(data2mesh(vertices, [], faces))
            displace_vertices(cutter, lambda x, y, z: (0, 2 * y * y, 0))
            modify_mesh(cutter, "SUBSURF", render_levels=5, levels=5, subdivision_type="SIMPLE")
            cutter.location = np.cos(angle) * depth, np.sin(angle) * depth, 0
            cutter.rotation_euler = 0, 0, rot
            modify_mesh(obj, "WELD", merge_threshold=0.002)
            modify_mesh(obj, "BOOLEAN", object=cutter, operation="DIFFERENCE", apply=True)
            delete(cutter)

    # 3. Remesh
    remesh_with_attrs(obj, face_size)

    # 4. Store xyz normalized attributes via GeoNodes (required by shader_cap / shader_voronoi)
    _apply_geomod(obj, _build_geo_xyz(), apply=True)

    # 5. Store morel attribute via GeoNodes
    _apply_geomod(obj, _build_geo_morel(params["morel_voronoi_scale"], params["morel_randomness"]), apply=True)

    # 6. Apply morel displacement if needed
    if params["is_morel"]:
        with SelectObjects(obj):
            _set_active_attribute(obj, "morel")
            try:
                bpy.ops.geometry.attribute_convert(mode="VERTEX_GROUP")
            except Exception:
                pass
        modify_mesh(obj, "DISPLACE", vertex_group="morel", strength=0.04, mid_level=0.7)

    # Assign cap material BEFORE the join(), per the "per-part material" rule.
    obj.data.materials.append(MAT_CAP)

    # 7. Add gills
    if params["gill_config"] is not None:
        gill_config = params["gill_config"]
        anchors = gill_config["x_anchors"], 0, gill_config["z_anchors"]
        gill = spin(
            anchors,
            gill_config["vector_locations"],
            dupli=True,
            loop=True,
            rotation_resolution=params["gill_rotation_resolution"],
        )
        subsurface2face_size(gill, face_size)
        modify_mesh(gill, "SMOOTH", apply=True, iterations=3)
        # Assign gill material BEFORE join() so the joined mesh retains both slots
        gill.data.materials.append(MAT_GILL)
        obj = join_objects([obj, gill])

    # 8. Texture displacement
    texture = bpy.data.textures.new(name="cap", type=params["texture_type"])
    texture.noise_scale = params["texture_noise_scale"]
    modify_mesh(obj, "DISPLACE", strength=0.008, texture=texture, mid_level=0)

    # 9. geo_extension displacement
    _apply_geomod(obj, _build_geo_extension(0.1), apply=True)

    # 10. Twist deformation
    modify_mesh(obj, "SIMPLE_DEFORM",
                deform_method="TWIST",
                angle=params["twist_angle"],
                deform_axis="X")

    # 11. Random vertex scaling
    r1, r2, r3, r4 = params["vertex_scale_factors"]
    displace_vertices(
        obj,
        lambda x, y, z: (
            np.where(x > 0, r1, r2) * x,
            np.where(y > 0, r3, r4) * y,
            0,
        ),
    )

    obj.name = "MushroomCapFactory"
    return obj

# ---------------------------------------------------------------------------
# Clear scene helper
# ---------------------------------------------------------------------------
def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    # NOTE: do not remove materials here -- MAT_CAP/MAT_GILL were created in Phase 1.
    for tex in list(bpy.data.textures):
        bpy.data.textures.remove(tex)
    for ng in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(ng)
    for curve in list(bpy.data.curves):
        bpy.data.curves.remove(curve)
    bpy.context.scene.cursor.location = (0, 0, 0)

clear_scene()
obj = build(SEED)

