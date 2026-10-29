# [FL_INDEX: keywords="blender_factory, procedural_3d, MushroomFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: MushroomFactory | Category: factories_tex
# Prompt: A 3D model of a cluster of mushrooms rendered from a slightly elevated perspective, featuring a main large mushroom with a broad tan cap on a thick textured pale stem alongside one or two smaller companion mushrooms of varying heights, all growing from a shared base.

"""Standalone Blender script for MushroomFactory (with textures).

Reproduces geometry from:
and faithfully reproduces the shaders from:

Materials:
  MAT_CAP       – cap surface, one of 4 procedural cap shaders (weights 2/1/1/1)
  MAT_GILL      – gills under cap, shader_mushroom
  MAT_STEM      – stem body, shader_mushroom (independent second call)
  MAT_WEB       – stem web ring, shader_mushroom (independent third call)

Seeding:
  - Materials are sampled under `with FixedSeed(SEED)`'s
    MushroomGrowthFactory.__init__ / MushroomCapFactory.__init__ / MushroomStemFactory.__init__.
  - Geometry seeding (int_hash((seed, i))) is unchanged from objects_blender source.
"""


import os
import colorsys
import math

import bpy
import bmesh
import numpy as np
import random
import hashlib
from collections.abc import Sized
from numpy.random import uniform
from mathutils import Euler, kdtree

C = bpy.context
D = bpy.data

# ---------------------------------------------------------------------------
# Seed utilities (copied verbatim from objects_blender source)
# ---------------------------------------------------------------------------

class FixedSeed:
    def __init__(self, seed):
        self.seed = int(seed)
        self.py_state = None
        self.np_state = None
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
            m.update(str(s).encode('utf-8'))
        return m
    return hashlib.md5(str(x).encode('utf-8'))

def int_hash(x, max_val=(2**32 - 1)):
    return abs(int(md5_hash(x).hexdigest(), 16)) % max_val

def log_uniform(low, high, size=None):
    return np.exp(np.random.uniform(np.log(low), np.log(high), size))

def polygon_angles(n, min_angle=np.pi / 6, max_angle=np.pi * 2 / 3):
    if n <= 0:
        return np.array([])
    for _ in range(100):
        angles = np.sort(uniform(0, 2 * np.pi, n))
        difference = (angles - np.roll(angles, 1)) % (2 * np.pi)
        if (difference >= min_angle).all() and (difference <= max_angle).all():
            return angles
    return np.sort((np.arange(n) * (2 * np.pi / n) + uniform(0, 2 * np.pi)) % (2 * np.pi))

# Inlined material library — hand-crafted for the mushroom category.
# Raw-bpy translation of:
# RNG consumption order inside each shader is preserved exactly.

def _hsv2rgba(h, s, v):
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

def _shader_log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(math.log(lo), math.log(hi))))

def _shader_uniform(lo, hi):
    return float(np.random.uniform(lo, hi))

def _new_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat

def _musgrave_scalar(nt, scale, vector_socket=None):
    """Build ``nw.musgrave(scale)`` helper: MapRange(Noise, -1, 1, 0, 1).

    Blender 4.1+ removed Musgrave; we use ShaderNodeTexNoise as the replacement
    driven through the same Map Range so the downstream color ramp behaves
    identically (0..1 output).
    """

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = float(scale)
    if "Detail" in noise.inputs:
        noise.inputs["Detail"].default_value = 8.0
    if vector_socket is not None:
        nt.links.new(vector_socket, noise.inputs["Vector"])
    fac = noise.outputs.get("Fac") or noise.outputs.get("Factor") or noise.outputs[0]

    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -1.0
    mr.inputs["From Max"].default_value = 1.0
    mr.inputs["To Min"].default_value = 0.0
    mr.inputs["To Max"].default_value = 1.0
    nt.links.new(fac, mr.inputs["Value"])
    return mr.outputs["Result"]

def _build_color_ramp(nt, fac_socket, positions, colors):
    """Mirror node_utils.build_color_ramp with HSV interpolation mode."""

    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.color_mode = "HSV"
    nt.links.new(fac_socket, cr.inputs["Fac"])
    elements = cr.color_ramp.elements
    size = len(positions)
    while len(elements) < size:
        elements.new(0.0)
    for i, (p, c) in enumerate(zip(positions, colors)):
        elements[i].position = float(p)
        elements[i].color = c
    return cr.outputs["Color"]

def _principled_bsdf_common(nt, base_color_socket, base_color_value, roughness,
                             specular, clearcoat, subsurface_color):
    """Shared Principled BSDF wiring used by shader_cap/noise/voronoi/speckle."""

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    if base_color_socket is not None:
        nt.links.new(base_color_socket, bsdf.inputs["Base Color"])
    elif base_color_value is not None:
        bsdf.inputs["Base Color"].default_value = base_color_value
    bsdf.inputs["Roughness"].default_value = roughness
    spec_key = "Specular IOR Level" if "Specular IOR Level" in bsdf.inputs else "Specular"
    bsdf.inputs[spec_key].default_value = specular
    coat_key = "Coat Weight" if "Coat Weight" in bsdf.inputs else (
        "Clearcoat" if "Clearcoat" in bsdf.inputs else None)
    if coat_key is not None:
        bsdf.inputs[coat_key].default_value = clearcoat
    sss_col_key = "Subsurface Color" if "Subsurface Color" in bsdf.inputs else None
    if sss_col_key is not None:
        bsdf.inputs[sss_col_key].default_value = subsurface_color
    sss_weight_key = "Subsurface Weight" if "Subsurface Weight" in bsdf.inputs else (
        "Subsurface" if "Subsurface" in bsdf.inputs else None)
    if sss_weight_key is not None:
        bsdf.inputs[sss_weight_key].default_value = 0.01
    sss_radius_key = "Subsurface Radius" if "Subsurface Radius" in bsdf.inputs else None
    if sss_radius_key is not None:
        try:
            bsdf.inputs[sss_radius_key].default_value = (0.05, 0.05, 0.05)
        except Exception:
            pass
    return bsdf

def _mix_rgb(nt, fac_socket_or_value, a_socket_or_value, b_socket_or_value):
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    if hasattr(fac_socket_or_value, "bl_idname"):
        nt.links.new(fac_socket_or_value, mix.inputs[0])
    else:
        mix.inputs[0].default_value = float(fac_socket_or_value)
    if hasattr(a_socket_or_value, "bl_idname"):
        nt.links.new(a_socket_or_value, mix.inputs[6])
    else:
        mix.inputs[6].default_value = a_socket_or_value
    if hasattr(b_socket_or_value, "bl_idname"):
        nt.links.new(b_socket_or_value, mix.inputs[7])
    else:
        mix.inputs[7].default_value = b_socket_or_value
    return mix.outputs[2]

def _build_float_curve(nt, value_socket, points):
    """Mirror nw.build_float_curve with VECTOR handles."""

    fc = nt.nodes.new("ShaderNodeFloatCurve")
    fc.mapping.use_clip = False
    curve = fc.mapping.curves[0]
    n = len(points)
    for i, (x, y) in enumerate(points):
        if i < 2:
            curve.points[i].location = (float(x), float(y))
        else:
            curve.points.new(float(x), float(y))
    for i in range(n):
        curve.points[i].handle_type = "VECTOR"
    fc.mapping.update()
    nt.links.new(value_socket, fc.inputs["Value"])
    return fc.outputs["Value"]

def make_shader_mushroom(base_hue, name="MushroomBody"):
    """Translation of growth.py :: shader_mushroom.

    RNG consumption order:
      front_color: uniform(-0.1,0.1), uniform(0.1,0.3), log_uniform(0.02,0.5)
      back_color : uniform(-0.1,0.1), uniform(0.1,0.3), log_uniform(0.02,0.5)
      z_scale    : uniform(5,10)
    """

    roughness = 0.8
    front_h = (base_hue + _shader_uniform(-0.1, 0.1)) % 1
    front_s = _shader_uniform(0.1, 0.3)
    front_v = _shader_log_uniform(0.02, 0.5)
    front_color = _hsv2rgba(front_h, front_s, front_v)

    back_h = (base_hue + _shader_uniform(-0.1, 0.1)) % 1
    back_s = _shader_uniform(0.1, 0.3)
    back_v = _shader_log_uniform(0.02, 0.5)
    back_color = _hsv2rgba(back_h, back_s, back_v)

    z_scale = _shader_uniform(5, 10)

    mat = _new_mat(name); nt = mat.node_tree

    # Texture coord -> separate -> z * z_scale -> combine -> Musgrave(scale=200) -> MapRange -> ColorRamp(HSV)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    mul_z = nt.nodes.new("ShaderNodeMath"); mul_z.operation = "MULTIPLY"
    nt.links.new(sep.outputs["Z"], mul_z.inputs[0])
    mul_z.inputs[1].default_value = z_scale
    combine = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(sep.outputs["X"], combine.inputs["X"])
    nt.links.new(sep.outputs["Y"], combine.inputs["Y"])
    nt.links.new(mul_z.outputs[0], combine.inputs["Z"])

    musgrave_out = _musgrave_scalar(nt, scale=200, vector_socket=combine.outputs[0])
    color_out = _build_color_ramp(
        nt, musgrave_out,
        [0.0, 0.3, 0.7, 1.0],
        [front_color, front_color, back_color, back_color],
    )
    bsdf = _principled_bsdf_common(
        nt, color_out, None, roughness=roughness,
        specular=0.5, clearcoat=0.0,
        subsurface_color=(front_color[0], front_color[1], front_color[2], 1.0),
    )
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def _sample_common_cap_colors(base_hue, bright_sat_lo, bright_sat_hi, light_sat_lo, light_sat_hi, light_val_lo, light_val_hi):
    """RNG in the order shared by shader_cap/noise/voronoi/speckle."""

    bright = _hsv2rgba(base_hue, _shader_uniform(bright_sat_lo, bright_sat_hi), _shader_log_uniform(0.05, 0.2))
    dark = _hsv2rgba(
        (base_hue + _shader_uniform(-0.05, 0.05)) % 1,
        _shader_uniform(0.4, 0.8),
        _shader_log_uniform(0.01, 0.05),
    )
    return bright, dark

def _sample_cap_anchors():
    return [0.0, 0.3, 0.6, 1.0] if _shader_uniform(0, 1) < 0.5 else [0.0, 0.4, 0.7, 1.0]

def _sample_principled_tail():
    """Tail RNG consumption shared by all cap shaders."""

    roughness = _shader_uniform(0.2, 0.5) if _shader_uniform(0, 1) < 0.5 else _shader_uniform(0.8, 1.0)
    specular = _shader_uniform(0.2, 0.8)
    clearcoat = _shader_uniform(0.2, 0.5) if _shader_uniform(0, 1) < 0.25 else 0.0
    return roughness, specular, clearcoat

def make_shader_cap(base_hue, name="MushroomCap"):
    """cap.py :: shader_cap — z-driven light/dark mix over musgrave color ramp."""

    bright_color = _hsv2rgba(base_hue, _shader_uniform(0.6, 0.8), _shader_log_uniform(0.05, 0.2))
    dark_color = _hsv2rgba(
        (base_hue + _shader_uniform(-0.05, 0.05)) % 1,
        _shader_uniform(0.4, 0.8),
        _shader_log_uniform(0.01, 0.05),
    )
    light_color = _hsv2rgba(base_hue, _shader_uniform(0, 0.1), _shader_uniform(0.6, 0.8))
    subsurface_color = _hsv2rgba(
        (base_hue + _shader_uniform(-0.05, 0.05)) % 1,
        _shader_uniform(0.6, 0.8),
        _shader_log_uniform(0.05, 0.2),
    )
    anchors = _sample_cap_anchors()

    # FloatCurve "light mask" anchors (used inside shader)
    z_curve_pts = [
        (_shader_uniform(0, 0.2), _shader_uniform(0.95, 0.98)),
        (_shader_uniform(0.2, 0.4), _shader_uniform(0.98, 1.0)),
        (0.8, 1.0),
    ]
    roughness, specular, clearcoat = _sample_principled_tail()

    mat = _new_mat(name); nt = mat.node_tree

    # musgrave(500) color ramp between dark and bright
    mus_out = _musgrave_scalar(nt, 500)
    color_out = _build_color_ramp(
        nt, mus_out, anchors,
        [dark_color, dark_color, bright_color, bright_color],
    )

    # z attribute -> float curve -> mix(light_color, color)
    z_attr = nt.nodes.new("ShaderNodeAttribute"); z_attr.attribute_name = "z"
    z_fac = z_attr.outputs.get("Fac") or z_attr.outputs[0]
    fc_out = _build_float_curve(nt, z_fac, z_curve_pts)
    mixed = _mix_rgb(nt, fc_out, light_color, color_out)

    bsdf = _principled_bsdf_common(
        nt, mixed, None, roughness=roughness,
        specular=specular, clearcoat=clearcoat, subsurface_color=subsurface_color,
    )
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def make_shader_noise(base_hue, name="MushroomCapNoise"):
    """cap.py :: shader_noise — bright/dark ramp with noise-driven light speckles."""

    bright_color = _hsv2rgba(base_hue, _shader_uniform(0.4, 0.8), _shader_log_uniform(0.05, 0.2))
    dark_color = _hsv2rgba(
        (base_hue + _shader_uniform(-0.05, 0.05)) % 1,
        _shader_uniform(0.4, 0.8),
        _shader_log_uniform(0.01, 0.05),
    )
    subsurface_color = _hsv2rgba(
        (base_hue + _shader_uniform(-0.05, 0.05)) % 1,
        _shader_uniform(0.4, 0.8),
        _shader_log_uniform(0.05, 0.2),
    )
    light_color = _hsv2rgba(base_hue, _shader_uniform(0, 0.1), _shader_uniform(0.2, 0.8))
    anchors = _sample_cap_anchors()
    roughness, specular, clearcoat = _sample_principled_tail()

    mat = _new_mat(name); nt = mat.node_tree

    mus_out = _musgrave_scalar(nt, 500)
    color_out = _build_color_ramp(
        nt, mus_out, anchors,
        [dark_color, dark_color, bright_color, bright_color],
    )

    mus10 = _musgrave_scalar(nt, 10)
    ratio = _build_float_curve(nt, mus10, [(0.52, 0), (0.56, 0.2), (0.6, 0.0)])

    # map_range(musgrave(20), -0.2..0.1 -> 0..1) (second musgrave helper produces 0..1, so
    # reproduce the original by re-biasing: but passes the raw MusgraveTexture,
    # not nw.musgrave, through MapRange(-0.2, 0.1, 0, 1). We replicate literally.
    noise20 = nt.nodes.new("ShaderNodeTexNoise")
    noise20.inputs["Scale"].default_value = 20.0
    if "Detail" in noise20.inputs:
        noise20.inputs["Detail"].default_value = 8.0
    n20_fac = noise20.outputs.get("Fac") or noise20.outputs[0]
    mr20 = nt.nodes.new("ShaderNodeMapRange")
    mr20.inputs["From Min"].default_value = -0.2
    mr20.inputs["From Max"].default_value = 0.1
    mr20.inputs["To Min"].default_value = 0.0
    mr20.inputs["To Max"].default_value = 1.0
    nt.links.new(n20_fac, mr20.inputs["Value"])

    mul_r = nt.nodes.new("ShaderNodeMath"); mul_r.operation = "MULTIPLY"
    nt.links.new(ratio, mul_r.inputs[0])
    nt.links.new(mr20.outputs["Result"], mul_r.inputs[1])

    mixed = _mix_rgb(nt, mul_r.outputs[0], color_out, light_color)

    bsdf = _principled_bsdf_common(
        nt, mixed, None, roughness=roughness,
        specular=specular, clearcoat=clearcoat, subsurface_color=subsurface_color,
    )
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def make_shader_voronoi(base_hue, name="MushroomCapVoronoi"):
    """cap.py :: shader_voronoi — voronoi distance-to-edge driven ring pattern."""

    bright_color = _hsv2rgba(base_hue, _shader_uniform(0.4, 0.8), _shader_log_uniform(0.05, 0.2))
    dark_color = _hsv2rgba(
        (base_hue + _shader_uniform(-0.05, 0.05)) % 1,
        _shader_uniform(0.4, 0.8),
        _shader_log_uniform(0.01, 0.05),
    )
    subsurface_color = _hsv2rgba(
        (base_hue + _shader_uniform(-0.05, 0.05)) % 1,
        _shader_uniform(0.4, 0.8),
        _shader_log_uniform(0.05, 0.2),
    )
    light_color = _hsv2rgba(base_hue, _shader_uniform(0, 0.1), _shader_uniform(0.2, 0.8))
    anchors = _sample_cap_anchors()
    radial_knee = _shader_uniform(0.5, 0.7)
    voronoi_scale = _shader_uniform(2, 2.5)
    roughness, specular, clearcoat = _sample_principled_tail()

    mat = _new_mat(name); nt = mat.node_tree

    mus_out = _musgrave_scalar(nt, 500)
    color_out = _build_color_ramp(
        nt, mus_out, anchors,
        [dark_color, dark_color, bright_color, bright_color],
    )

    # x, y as named attributes (the geo_xyz modifier stores them)
    x_attr = nt.nodes.new("ShaderNodeAttribute"); x_attr.attribute_name = "x"
    y_attr = nt.nodes.new("ShaderNodeAttribute"); y_attr.attribute_name = "y"
    x_fac = x_attr.outputs.get("Fac") or x_attr.outputs[0]
    y_fac = y_attr.outputs.get("Fac") or y_attr.outputs[0]

    # r = sqrt(x^2 + y^2)
    x_sq = nt.nodes.new("ShaderNodeMath"); x_sq.operation = "POWER"; x_sq.inputs[1].default_value = 2
    nt.links.new(x_fac, x_sq.inputs[0])
    y_sq = nt.nodes.new("ShaderNodeMath"); y_sq.operation = "POWER"; y_sq.inputs[1].default_value = 2
    nt.links.new(y_fac, y_sq.inputs[0])
    r2 = nt.nodes.new("ShaderNodeMath"); r2.operation = "ADD"
    nt.links.new(x_sq.outputs[0], r2.inputs[0])
    nt.links.new(y_sq.outputs[0], r2.inputs[1])
    r_node = nt.nodes.new("ShaderNodeMath"); r_node.operation = "POWER"; r_node.inputs[1].default_value = 0.5
    nt.links.new(r2.outputs[0], r_node.inputs[0])

    # coord = combine(x, y, 0) * build_float_curve(r, [(0,1),(knee,2),(1,8)])
    combine_xy = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(x_fac, combine_xy.inputs["X"])
    nt.links.new(y_fac, combine_xy.inputs["Y"])
    # z defaults to 0
    scale_curve = _build_float_curve(nt, r_node.outputs[0], [(0, 1), (radial_knee, 2), (1, 8)])
    coord_scale = nt.nodes.new("ShaderNodeVectorMath"); coord_scale.operation = "SCALE"
    nt.links.new(combine_xy.outputs[0], coord_scale.inputs[0])
    nt.links.new(scale_curve, coord_scale.inputs["Scale"])

    # perturbed_position = coord + noise2D * 0.2
    noise2d = nt.nodes.new("ShaderNodeTexNoise")
    noise2d.noise_dimensions = "2D"
    noise_color = noise2d.outputs.get("Color") or noise2d.outputs[1]
    perturb = nt.nodes.new("ShaderNodeVectorMath"); perturb.operation = "SCALE"
    nt.links.new(noise_color, perturb.inputs[0])
    perturb.inputs["Scale"].default_value = 0.2
    pos_add = nt.nodes.new("ShaderNodeVectorMath"); pos_add.operation = "ADD"
    nt.links.new(coord_scale.outputs[0], pos_add.inputs[0])
    nt.links.new(perturb.outputs[0], pos_add.inputs[1])

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi.voronoi_dimensions = "2D"
    voronoi.feature = "DISTANCE_TO_EDGE"
    voronoi.inputs["Scale"].default_value = voronoi_scale
    nt.links.new(pos_add.outputs[0], voronoi.inputs["Vector"])

    # ratio = voronoi / (1 + 5 * r^2)
    r2_5 = nt.nodes.new("ShaderNodeMath"); r2_5.operation = "MULTIPLY"
    r2_5.inputs[1].default_value = 5.0
    nt.links.new(r2.outputs[0], r2_5.inputs[0])
    denom = nt.nodes.new("ShaderNodeMath"); denom.operation = "ADD"
    denom.inputs[0].default_value = 1.0
    nt.links.new(r2_5.outputs[0], denom.inputs[1])
    ratio = nt.nodes.new("ShaderNodeMath"); ratio.operation = "DIVIDE"
    nt.links.new(voronoi.outputs["Distance"], ratio.inputs[0])
    nt.links.new(denom.outputs[0], ratio.inputs[1])

    ratio_curve = _build_float_curve(nt, ratio.outputs[0], [(0, 0.4), (0.04, 0)])

    # noise(20) -> MapRange(-0.2, 0.1, 0, 1) -> multiply ratio
    noise20 = nt.nodes.new("ShaderNodeTexNoise")
    noise20.inputs["Scale"].default_value = 20.0
    n20_fac = noise20.outputs.get("Fac") or noise20.outputs[0]
    mr20 = nt.nodes.new("ShaderNodeMapRange")
    mr20.inputs["From Min"].default_value = -0.2
    mr20.inputs["From Max"].default_value = 0.1
    mr20.inputs["To Min"].default_value = 0.0
    mr20.inputs["To Max"].default_value = 1.0
    nt.links.new(n20_fac, mr20.inputs["Value"])
    mul_r = nt.nodes.new("ShaderNodeMath"); mul_r.operation = "MULTIPLY"
    nt.links.new(ratio_curve, mul_r.inputs[0])
    nt.links.new(mr20.outputs["Result"], mul_r.inputs[1])

    mixed = _mix_rgb(nt, mul_r.outputs[0], color_out, light_color)

    bsdf = _principled_bsdf_common(
        nt, mixed, None, roughness=roughness,
        specular=specular, clearcoat=clearcoat, subsurface_color=subsurface_color,
    )
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def make_shader_speckle(base_hue, name="MushroomCapSpeckle"):
    """cap.py :: shader_speckle — bright/dark ramp with high-frequency speckles."""

    bright_color = _hsv2rgba(base_hue, _shader_uniform(0.4, 0.8), _shader_log_uniform(0.05, 0.2))
    dark_color = _hsv2rgba(
        (base_hue + _shader_uniform(-0.05, 0.05)) % 1,
        _shader_uniform(0.4, 0.8),
        _shader_log_uniform(0.01, 0.05),
    )
    subsurface_color = _hsv2rgba(
        (base_hue + _shader_uniform(-0.05, 0.05)) % 1,
        _shader_uniform(0.4, 0.8),
        _shader_log_uniform(0.05, 0.2),
    )
    light_color = _hsv2rgba(base_hue, _shader_uniform(0, 0.1), _shader_uniform(0.2, 0.8))
    anchors = _sample_cap_anchors()
    roughness, specular, clearcoat = _sample_principled_tail()

    mat = _new_mat(name); nt = mat.node_tree

    mus_out = _musgrave_scalar(nt, 500)
    color_out = _build_color_ramp(
        nt, mus_out, anchors,
        [dark_color, dark_color, bright_color, bright_color],
    )

    mus50 = _musgrave_scalar(nt, 50)
    speckle = _build_float_curve(nt, mus50, [(0.7, 0.0), (0.72, 1.0)])
    mixed = _mix_rgb(nt, speckle, color_out, light_color)

    bsdf = _principled_bsdf_common(
        nt, mixed, None, roughness=roughness,
        specular=specular, clearcoat=clearcoat, subsurface_color=subsurface_color,
    )
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

_CAP_SHADERS = [make_shader_cap, make_shader_noise, make_shader_voronoi, make_shader_speckle]

def build_base_hue_value():
    """Mirror MushroomGrowthFactory.build_base_hue."""

    if _shader_uniform(0, 1) < 0.4:
        return _shader_uniform(0, 1)
    else:
        return _shader_uniform(0.02, 0.15)

# ---------------------------------------------------------------------------
# Blender utility helpers (copied verbatim from objects_blender source)
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
    def __enter__(self):
        return self
    def __exit__(self, *exc):
        return True

class ViewportMode:
    def __init__(self, obj, mode):
        self.obj = obj
        self.mode = mode
        self.prev_active = None
        self.prev_mode = None
    def __enter__(self):
        self.prev_active = bpy.context.view_layer.objects.active
        _select_none(); _set_active(self.obj)
        self.prev_mode = getattr(bpy.context.object, 'mode', 'OBJECT') if bpy.context.object else 'OBJECT'
        if bpy.context.object and self.prev_mode != self.mode:
            bpy.ops.object.mode_set(mode=self.mode)
        return self
    def __exit__(self, *_):
        try:
            if bpy.context.object and bpy.context.object.mode != self.prev_mode:
                bpy.ops.object.mode_set(mode=self.prev_mode)
        except Exception:
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except Exception:
                pass
        if self.prev_active is not None:
            _set_active(self.prev_active)

class SelectObjects:
    def __init__(self, objs, active=0):
        self.objs = objs if isinstance(objs, (list, tuple)) else [objs]
        self.active_idx = active
        self.prev_sel = None
        self.prev_active = None
    def __enter__(self):
        self.prev_sel = list(bpy.context.selected_objects)
        self.prev_active = bpy.context.view_layer.objects.active
        _select_none()
        for o in self.objs:
            if o is not None:
                o.select_set(True)
        if self.objs:
            _set_active(self.objs[self.active_idx])
        return self
    def __exit__(self, *_):
        _select_none()
        for o in self.prev_sel or []:
            if o and o.name in bpy.data.objects:
                o.select_set(True)
        if self.prev_active is not None and self.prev_active.name in bpy.data.objects:
            _set_active(self.prev_active)

def apply_transform(obj, loc=False, rot=True, scale=True):
    with SelectObjects(obj):
        bpy.ops.object.transform_apply(location=loc, rotation=rot, scale=scale)

def delete(objs):
    if not isinstance(objs, (list, tuple)):
        objs = [objs]
    for o in objs:
        if o is None:
            continue
        mesh = o.data if getattr(o, 'type', None) == 'MESH' else None
        try:
            bpy.data.objects.remove(o, do_unlink=True)
        except Exception:
            pass
        try:
            if mesh is not None and mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        except Exception:
            pass

def modify_mesh(obj, type_, apply=True, name=None, return_mod=False, **kwargs):
    if name is None:
        name = f'modify_mesh({type_})'
    mod = obj.modifiers.new(name=name, type=type_)
    mod.show_viewport = not apply
    for k, v in kwargs.items():
        try:
            setattr(mod, k, v)
        except Exception:
            pass
    if apply:
        with SelectObjects(obj):
            bpy.ops.object.modifier_apply(modifier=mod.name)
    return (obj, None if apply else mod) if return_mod else obj

def deep_clone_obj(obj):
    new_obj = obj.copy()
    if obj.data is not None:
        new_obj.data = obj.data.copy()
    coll = obj.users_collection[0] if obj.users_collection else bpy.context.scene.collection
    coll.objects.link(new_obj)
    return new_obj

# ---------------------------------------------------------------------------
# Mesh helpers (copied verbatim)
# ---------------------------------------------------------------------------

def data2mesh(vertices=(), edges=(), faces=(), name=''):
    mesh = bpy.data.meshes.new(name or 'mesh')
    mesh.from_pydata(list(vertices), list(edges), list(faces))
    mesh.update()
    return mesh

def mesh2obj(mesh):
    obj = bpy.data.objects.new(mesh.name or 'obj', mesh)
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
    obj.data.vertices.foreach_get('co', arr)
    return arr.reshape(-1, 3)

def write_co(obj, arr):
    obj.data.vertices.foreach_set('co', np.asarray(arr, dtype=float).reshape(-1))
    obj.data.update()

def displace_vertices(obj, fn):
    co = read_co(obj)
    x, y, z = co.T
    d = fn(x, y, z)
    for i in range(3):
        co[:, i] += np.asarray(d[i])
    write_co(obj, co)

def origin2lowest(obj, vertical=False):
    co = read_co(obj)
    if len(co) == 0:
        return
    i = np.argmin(co[:, -1])
    if vertical:
        obj.location[-1] = -co[i, -1]
    else:
        obj.location = -co[i]
    apply_transform(obj, loc=True)

def subsurface2face_size(obj, face_size):
    arr = np.zeros(len(obj.data.polygons), dtype=float)
    if len(arr) == 0:
        return
    obj.data.polygons.foreach_get('area', arr)
    area = float(np.mean(arr))
    if area <= 1e-9 or face_size <= 0:
        return
    try:
        levels = int(np.ceil(np.log2(area / face_size)))
    except Exception:
        return
    if levels > 0:
        modify_mesh(obj, 'SUBSURF', apply=True, levels=levels, render_levels=levels)

def remesh_with_attrs(obj, face_size):
    modify_mesh(obj, 'REMESH', apply=True, voxel_size=face_size)
    return obj

def remesh_fill(obj, resolution=0.005):
    zmax = float(read_co(obj)[:, 2].max()) if len(obj.data.vertices) else 0.0
    modify_mesh(obj, 'SOLIDIFY', apply=True, thickness=0.1)
    depth = int(np.ceil(np.log2((max(obj.dimensions) + 0.01) / max(resolution, 1e-5))))
    depth = max(depth, 4)
    modify_mesh(obj, 'REMESH', apply=True, mode='SHARP', octree_depth=depth, use_remove_disconnected=False)
    co = read_co(obj)
    to_del = np.where(co[:, 2] > zmax + 1e-4)[0]
    if len(to_del):
        with ViewportMode(obj, 'EDIT'):
            bm = bmesh.from_edit_mesh(obj.data)
            bm.verts.ensure_lookup_table()
            bmesh.ops.delete(bm, geom=[bm.verts[i] for i in to_del if i < len(bm.verts)], context='VERTS')
            bmesh.update_edit_mesh(obj.data)
    return obj

# ---------------------------------------------------------------------------
# Bezier curve + spin (copied verbatim)
# ---------------------------------------------------------------------------

def bezier_curve(anchors, vector_locations=(), resolution=None, to_mesh=True):
    n = [len(r) for r in anchors if isinstance(r, Sized)][0]
    anchors = np.array([np.array(r, dtype=float) if isinstance(r, Sized) else np.full(n, r) for r in anchors])
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0))
    obj = bpy.context.active_object
    if n > 2:
        with ViewportMode(obj, 'EDIT'):
            bpy.ops.curve.subdivide(number_cuts=n - 2)
    points = obj.data.splines[0].bezier_points
    for i in range(n):
        points[i].co = anchors[:, i]
    for i in range(n):
        if i in vector_locations:
            points[i].handle_left_type = 'VECTOR'
            points[i].handle_right_type = 'VECTOR'
        else:
            points[i].handle_left_type = 'AUTO'
            points[i].handle_right_type = 'AUTO'
    obj.data.splines[0].resolution_u = resolution if resolution is not None else 12
    if not to_mesh:
        return obj
    return curve2mesh(obj)

def curve2mesh(obj):
    points = obj.data.splines[0].bezier_points
    cos = np.array([p.co for p in points])
    length = np.linalg.norm(cos[:-1] - cos[1:], axis=-1) if len(cos) > 1 else np.array([])
    min_length = 5e-3
    with ViewportMode(obj, 'EDIT'):
        for p in obj.data.splines[0].bezier_points:
            if p.handle_left_type == 'FREE':
                p.handle_left_type = 'ALIGNED'
            if p.handle_right_type == 'FREE':
                p.handle_right_type = 'ALIGNED'
        for i in reversed(range(max(len(points) - 1, 0))):
            points = list(obj.data.splines[0].bezier_points)
            number_cuts = min(int(length[i] / min_length) - 1, 64)
            if number_cuts < 0:
                continue
            bpy.ops.curve.select_all(action='DESELECT')
            points[i].select_control_point = True
            points[i + 1].select_control_point = True
            bpy.ops.curve.subdivide(number_cuts=number_cuts)
    obj.data.splines[0].resolution_u = 1
    with SelectObjects(obj):
        bpy.ops.object.convert(target='MESH')
    obj = bpy.context.active_object
    modify_mesh(obj, 'WELD', apply=True, merge_threshold=1e-3)
    return obj

def spin(anchors, vector_locations=(), resolution=None, rotation_resolution=None,
         axis=(0, 0, 1), loop=False, dupli=False):
    obj = bezier_curve(anchors, vector_locations, resolution)
    co = read_co(obj)
    axis_v = np.array(axis, dtype=float)
    mean_radius = np.mean(np.linalg.norm(co - (co @ axis_v)[:, None] * axis_v, axis=-1)) if len(co) else 0.05
    if rotation_resolution is None:
        rotation_resolution = min(max(int(2 * np.pi * max(mean_radius, 1e-3) / 5e-3), 8), 128)
    modify_mesh(obj, 'WELD', apply=True, merge_threshold=1e-3)
    if loop:
        with ViewportMode(obj, 'EDIT'), Suppress():
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.fill()
        remesh_fill(obj)
    with ViewportMode(obj, 'EDIT'), Suppress():
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.spin(steps=rotation_resolution, angle=np.pi * 2, axis=axis, dupli=dupli)
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=1e-3)
    return obj

# ---------------------------------------------------------------------------
# GeoNodes helpers (copied verbatim)
# ---------------------------------------------------------------------------

def _apply_geomod(obj, node_group, apply=True):
    _select_none(); _set_active(obj)
    mod = obj.modifiers.new(name='GeoNodes', type='NODES')
    mod.node_group = node_group
    if apply:
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.node_groups.remove(node_group)
    _select_none()
    return mod

def _noise_fac_output(node):
    for name in ("Fac", "Factor"):
        if name in node.outputs:
            return node.outputs[name]
    return node.outputs[0]

def _wave_fac_output(node):
    for name in ("Fac", "Factor"):
        if name in node.outputs:
            return node.outputs[name]
    return node.outputs[0]

def _set_active_attribute(obj, name):
    attrs = obj.data.attributes
    for i, a in enumerate(attrs):
        if a.name == name:
            attrs.active_index = i
            try:
                attrs.active = attrs[i]
            except Exception:
                pass
            return

def _build_geo_extension(noise_strength=0.2, noise_scale=2.0):
    noise_strength = uniform(noise_strength / 2, noise_strength)
    noise_scale = uniform(noise_scale * 0.7, noise_scale * 1.4)
    direction_offset = uniform(-1, 1, 3)

    ng = bpy.data.node_groups.new("geo_extension", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput'); go.is_active_output = True

    pos = ng.nodes.new('GeometryNodeInputPosition')

    length_node = ng.nodes.new('ShaderNodeVectorMath'); length_node.operation = 'LENGTH'
    ng.links.new(pos.outputs[0], length_node.inputs[0])

    inv_len = ng.nodes.new('ShaderNodeMath'); inv_len.operation = 'DIVIDE'
    inv_len.inputs[0].default_value = 1.0
    ng.links.new(length_node.outputs['Value'], inv_len.inputs[1])

    dir_scale = ng.nodes.new('ShaderNodeVectorMath'); dir_scale.operation = 'SCALE'
    ng.links.new(pos.outputs[0], dir_scale.inputs[0])
    ng.links.new(inv_len.outputs[0], dir_scale.inputs['Scale'])

    dir_add = ng.nodes.new('ShaderNodeVectorMath'); dir_add.operation = 'ADD'
    ng.links.new(dir_scale.outputs[0], dir_add.inputs[0])
    dir_add.inputs[1].default_value = tuple(float(v) for v in direction_offset)

    noise_tex = ng.nodes.new('ShaderNodeTexNoise')
    ng.links.new(dir_add.outputs[0], noise_tex.inputs['Vector'])
    noise_tex.inputs['Scale'].default_value = noise_scale

    add_quarter = ng.nodes.new('ShaderNodeMath'); add_quarter.operation = 'ADD'
    ng.links.new(_noise_fac_output(noise_tex), add_quarter.inputs[0])
    add_quarter.inputs[1].default_value = 0.25

    mul_strength = ng.nodes.new('ShaderNodeMath'); mul_strength.operation = 'MULTIPLY'
    ng.links.new(add_quarter.outputs[0], mul_strength.inputs[0])
    mul_strength.inputs[1].default_value = noise_strength

    offset_scale = ng.nodes.new('ShaderNodeVectorMath'); offset_scale.operation = 'SCALE'
    ng.links.new(pos.outputs[0], offset_scale.inputs[0])
    ng.links.new(mul_strength.outputs[0], offset_scale.inputs['Scale'])

    set_pos = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(gi.outputs[0], set_pos.inputs['Geometry'])
    ng.links.new(offset_scale.outputs[0], set_pos.inputs['Offset'])

    ng.links.new(set_pos.outputs[0], go.inputs[0])
    return ng

def _build_geo_xyz():
    ng = bpy.data.node_groups.new("geo_xyz", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput'); go.is_active_output = True

    pos = ng.nodes.new('GeometryNodeInputPosition')
    sep = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(pos.outputs[0], sep.inputs[0])

    prev_geom = gi.outputs[0]
    for axis_name, axis_out in [("x", "X"), ("y", "Y"), ("z", "Z")]:
        abs_node = ng.nodes.new('ShaderNodeMath'); abs_node.operation = 'ABSOLUTE'
        ng.links.new(sep.outputs[axis_out], abs_node.inputs[0])

        attr_stat = ng.nodes.new('GeometryNodeAttributeStatistic')
        ng.links.new(prev_geom, attr_stat.inputs['Geometry'])
        ng.links.new(abs_node.outputs[0], attr_stat.inputs[2])

        div_node = ng.nodes.new('ShaderNodeMath'); div_node.operation = 'DIVIDE'
        ng.links.new(abs_node.outputs[0], div_node.inputs[0])
        ng.links.new(attr_stat.outputs['Max'], div_node.inputs[1])

        store = ng.nodes.new('GeometryNodeStoreNamedAttribute')
        ng.links.new(prev_geom, store.inputs['Geometry'])
        store.inputs['Name'].default_value = axis_name
        ng.links.new(div_node.outputs[0], store.inputs['Value'])

        prev_geom = store.outputs['Geometry']

    ng.links.new(prev_geom, go.inputs[0])
    return ng

def _build_geo_morel(voronoi_scale, randomness):
    ng = bpy.data.node_groups.new("geo_morel", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput'); go.is_active_output = True

    voronoi = ng.nodes.new('ShaderNodeTexVoronoi')
    voronoi.feature = 'DISTANCE_TO_EDGE'
    voronoi.inputs['Scale'].default_value = voronoi_scale
    voronoi.inputs['Randomness'].default_value = randomness

    compare = ng.nodes.new('FunctionNodeCompare')
    compare.operation = 'LESS_THAN'
    ng.links.new(voronoi.outputs['Distance'], compare.inputs[0])
    compare.inputs[1].default_value = 0.05

    store = ng.nodes.new('GeometryNodeStoreNamedAttribute')
    ng.links.new(gi.outputs[0], store.inputs['Geometry'])
    store.inputs['Name'].default_value = "morel"
    ng.links.new(compare.outputs['Result'], store.inputs['Value'])

    ng.links.new(store.outputs['Geometry'], go.inputs[0])
    return ng

def _build_geo_band(length, scale):
    wave_scale = float(log_uniform(5, 10))
    wave_distortion = float(uniform(5, 10))
    z_threshold = float(-uniform(0.3, 0.7) * length)

    ng = bpy.data.node_groups.new("geo_band", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput'); go.is_active_output = True

    wave = ng.nodes.new('ShaderNodeTexWave')
    wave.bands_direction = 'Z'
    wave.wave_profile = 'SAW'
    wave.inputs['Scale'].default_value = wave_scale
    wave.inputs['Distortion'].default_value = wave_distortion
    wave.inputs['Detail Scale'].default_value = 2.0

    pos = ng.nodes.new('GeometryNodeInputPosition')
    sep = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(pos.outputs[0], sep.inputs[0])

    compare = ng.nodes.new('FunctionNodeCompare')
    compare.operation = 'LESS_THAN'
    ng.links.new(sep.outputs['Z'], compare.inputs[0])
    compare.inputs[1].default_value = z_threshold

    normal_node = ng.nodes.new('GeometryNodeInputNormal')
    add_bias = ng.nodes.new('ShaderNodeVectorMath'); add_bias.operation = 'ADD'
    ng.links.new(normal_node.outputs[0], add_bias.inputs[0])
    add_bias.inputs[1].default_value = (0.0, 0.0, 2.0)
    norm_node = ng.nodes.new('ShaderNodeVectorMath'); norm_node.operation = 'NORMALIZE'
    ng.links.new(add_bias.outputs[0], norm_node.inputs[0])

    mul_scale = ng.nodes.new('ShaderNodeMath'); mul_scale.operation = 'MULTIPLY'
    ng.links.new(_wave_fac_output(wave), mul_scale.inputs[0])
    mul_scale.inputs[1].default_value = scale

    offset_node = ng.nodes.new('ShaderNodeVectorMath'); offset_node.operation = 'SCALE'
    ng.links.new(norm_node.outputs[0], offset_node.inputs[0])
    ng.links.new(mul_scale.outputs[0], offset_node.inputs['Scale'])

    set_pos = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(gi.outputs[0], set_pos.inputs['Geometry'])
    ng.links.new(compare.outputs['Result'], set_pos.inputs['Selection'])
    ng.links.new(offset_node.outputs[0], set_pos.inputs['Offset'])

    ng.links.new(set_pos.outputs[0], go.inputs[0])
    return ng

def _build_geo_inverse_band(scale):
    wave_scale = float(log_uniform(5, 10))
    wave_distortion = float(uniform(5, 10))

    ng = bpy.data.node_groups.new("geo_inverse_band", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput'); go.is_active_output = True

    pos = ng.nodes.new('GeometryNodeInputPosition')
    sep = ng.nodes.new('ShaderNodeSeparateXYZ')
    ng.links.new(pos.outputs[0], sep.inputs[0])

    neg_z = ng.nodes.new('ShaderNodeMath'); neg_z.operation = 'MULTIPLY'
    neg_z.inputs[0].default_value = -1.0
    ng.links.new(sep.outputs['Z'], neg_z.inputs[1])

    combine = ng.nodes.new('ShaderNodeCombineXYZ')
    ng.links.new(sep.outputs['X'], combine.inputs['X'])
    ng.links.new(sep.outputs['Y'], combine.inputs['Y'])
    ng.links.new(neg_z.outputs[0], combine.inputs['Z'])

    wave = ng.nodes.new('ShaderNodeTexWave')
    wave.bands_direction = 'Z'
    wave.wave_profile = 'SAW'
    ng.links.new(combine.outputs[0], wave.inputs['Vector'])
    wave.inputs['Scale'].default_value = wave_scale
    wave.inputs['Distortion'].default_value = wave_distortion
    wave.inputs['Detail Scale'].default_value = 2.0

    normal_node = ng.nodes.new('GeometryNodeInputNormal')
    add_bias = ng.nodes.new('ShaderNodeVectorMath'); add_bias.operation = 'ADD'
    ng.links.new(normal_node.outputs[0], add_bias.inputs[0])
    add_bias.inputs[1].default_value = (0.0, 0.0, 2.0)
    norm_node = ng.nodes.new('ShaderNodeVectorMath'); norm_node.operation = 'NORMALIZE'
    ng.links.new(add_bias.outputs[0], norm_node.inputs[0])

    mul_scale = ng.nodes.new('ShaderNodeMath'); mul_scale.operation = 'MULTIPLY'
    ng.links.new(_wave_fac_output(wave), mul_scale.inputs[0])
    mul_scale.inputs[1].default_value = scale

    offset_node = ng.nodes.new('ShaderNodeVectorMath'); offset_node.operation = 'SCALE'
    ng.links.new(norm_node.outputs[0], offset_node.inputs[0])
    ng.links.new(mul_scale.outputs[0], offset_node.inputs['Scale'])

    set_pos = ng.nodes.new('GeometryNodeSetPosition')
    ng.links.new(gi.outputs[0], set_pos.inputs['Geometry'])
    ng.links.new(offset_node.outputs[0], set_pos.inputs['Offset'])

    ng.links.new(set_pos.outputs[0], go.inputs[0])
    return ng

def _build_geo_voronoi():
    voronoi_scale = float(uniform(15, 20))

    ng = bpy.data.node_groups.new("geo_voronoi", 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    gi = ng.nodes.new('NodeGroupInput')
    go = ng.nodes.new('NodeGroupOutput'); go.is_active_output = True

    voronoi = ng.nodes.new('ShaderNodeTexVoronoi')
    voronoi.feature = 'DISTANCE_TO_EDGE'
    voronoi.inputs['Scale'].default_value = voronoi_scale

    compare = ng.nodes.new('FunctionNodeCompare')
    compare.operation = 'LESS_THAN'
    ng.links.new(voronoi.outputs['Distance'], compare.inputs[0])
    compare.inputs[1].default_value = 0.06

    sep_geo = ng.nodes.new('GeometryNodeSeparateGeometry')
    ng.links.new(gi.outputs[0], sep_geo.inputs['Geometry'])
    ng.links.new(compare.outputs['Result'], sep_geo.inputs['Selection'])

    ng.links.new(sep_geo.outputs['Selection'], go.inputs[0])
    return ng

# ---------------------------------------------------------------------------
# Cap shape configs (copied verbatim)
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
    return {"x_anchors": [0, uniform(0.12, 0.15), 0.01, 0], "z_anchors": [0, 0, z, z], "vector_locations": [1], "has_gill": True}

def _convex():
    z = uniform(0.14, 0.16)
    return {"x_anchors": [0, 0.15, 0.12, 0.01, 0], "z_anchors": [0, 0, uniform(0.04, 0.06), z, z], "vector_locations": [1], "has_gill": True}

def _depressed():
    z = uniform(0.03, 0.05)
    return {"x_anchors": [0, 0.15, 0.12, 0], "z_anchors": [0, 0, uniform(0.06, 0.08), z], "vector_locations": [1], "has_gill": True}

def _flat():
    z = uniform(0.05, 0.07)
    return {"x_anchors": [0, 0.15, 0.12, 0], "z_anchors": [0, 0, z, z], "vector_locations": [1], "has_gill": True}

def _infundiuliform():
    z = uniform(0.08, 0.12); x = uniform(0.12, 0.15)
    return {"x_anchors": [0, 0.03, x, x - 0.01, 0], "z_anchors": [0, 0, z, z + uniform(0.005, 0.01), 0.02], "vector_locations": [], "has_gill": False}

def _ovate():
    z = uniform(0.2, 0.3)
    return {"x_anchors": [0, uniform(0.12, 0.15), 0.08, 0.01, 0], "z_anchors": [0, 0, 0.8 * z, z, z], "vector_locations": [1], "has_gill": True}

def _umbillicate():
    z = uniform(0.03, 0.05)
    return {"x_anchors": [0, 0.15, 0.12, 0.02, 0], "z_anchors": [0, 0.04, uniform(0.06, 0.08), z + 0.02, z], "vector_locations": [], "has_gill": False}

def _umbonate():
    z = uniform(0.05, 0.07); z_ = z + uniform(0.02, 0.04)
    return {"x_anchors": [0, 0.15, 0.12, 0.06, 0.02, 0], "z_anchors": [0, 0, z - 0.01, z, z_, z_], "vector_locations": [1], "has_gill": True}

# ---------------------------------------------------------------------------
# Parameter sampling helpers (copied verbatim)
# ---------------------------------------------------------------------------

def _sample_cap_params(seed):
    with FixedSeed(seed):
        x_scale, z_scale = uniform(0.7, 1.4, 2)
        cap_configs = [_campanulate, _conical, _convex, _depressed, _flat, _infundiuliform, _ovate, _umbillicate, _umbonate]
        config_weights = np.array([2, 2, 2, 1, 2, 1, 2, 1, 1])
        cap_config = np.random.choice(cap_configs, p=config_weights / config_weights.sum())()
        cap_config = {**cap_config, "x_anchors": [v * x_scale for v in cap_config["x_anchors"]], "z_anchors": [v * z_scale for v in cap_config["z_anchors"]]}
        radius = max(cap_config["x_anchors"])
        inner_radius = float(log_uniform(0.2, 0.35)) * radius

        def _adnexed():
            return {"x_anchors": [radius, (radius + inner_radius) / 2, inner_radius, inner_radius, radius], "z_anchors": [0, -uniform(0.05, 0.08), -uniform(0, 0.02), 0, 0], "vector_locations": [3]}
        def _decurrent():
            return {"x_anchors": [radius, (radius + inner_radius) / 2, inner_radius, 0, radius], "z_anchors": [0, -uniform(0.05, 0.08), -uniform(0.08, 0.1), 0, 0], "vector_locations": [2]}

        gill_choice = np.random.choice([0, 1, 2], p=np.array([1, 1, 1]) / 3.0)
        gill_config = None
        if cap_config["has_gill"] and gill_choice != 2:
            gill_config = [_adnexed, _decurrent][gill_choice]()

        shader_weights = np.array([2, 1, 1, 1])
        _shader_idx = np.random.choice(4, p=shader_weights / shader_weights.sum())
        is_morel = uniform(0, 1) < 0.5 and _shader_idx == 0
        morel_voronoi_scale = float(uniform(15, 20))
        morel_randomness = float(uniform(0.5, 1))

        n_cuts = 0; cut_angles = []; cut_widths = []; cut_depths = []; cut_rotations = []
        if max(cap_config["x_anchors"]) <= 0.1:
            n_cuts = int(np.random.randint(0, 5))
            cut_angles = list(polygon_angles(n_cuts, np.pi / 4, np.pi * 2))
            for ci in range(n_cuts):
                cut_widths.append(float(uniform(0.15, 0.2) * 0.4))
                cut_depths.append(float(radius * uniform(0.4, 0.7)))
                cut_rotations.append(float(cut_angles[ci] + uniform(-np.pi / 4, np.pi / 4)))

        gill_rotation_resolution = int(np.random.randint(32, 64))
        texture_type = str(np.random.choice(["STUCCI", "MARBLE"]))
        texture_noise_scale = float(log_uniform(0.01, 0.05))
        twist_angle = float(uniform(-np.pi / 4, np.pi / 4))
        vertex_scale_factors = [float(v) for v in uniform(-0.25, 0.25, 4)]

    return {
        "cap_config": cap_config, "radius": float(radius), "inner_radius": float(inner_radius),
        "gill_config": gill_config, "is_morel": bool(is_morel),
        "morel_voronoi_scale": morel_voronoi_scale, "morel_randomness": morel_randomness,
        "n_cuts": n_cuts, "cut_angles": cut_angles, "cut_widths": cut_widths,
        "cut_depths": cut_depths, "cut_rotations": cut_rotations,
        "gill_rotation_resolution": gill_rotation_resolution,
        "texture_type": texture_type, "texture_noise_scale": texture_noise_scale,
        "twist_angle": twist_angle, "vertex_scale_factors": vertex_scale_factors,
    }

def _sample_stem_params(seed, inner_radius):
    with FixedSeed(seed):
        web_builders = ['hollow', 'solid', None]
        web_weights = np.array([1, 1, 2])
        web_builder = np.random.choice(web_builders, p=web_weights / web_weights.sum())
        has_band = uniform(0, 1) < 0.75
    return {'inner_radius': float(inner_radius), 'web_builder': web_builder, 'has_band': bool(has_band)}

# ---------------------------------------------------------------------------
# Build cap / stem meshes (copied verbatim, with material insertions)
# ---------------------------------------------------------------------------

def _build_cap(cap_params, face_size):
    cap_config = cap_params["cap_config"]
    anchors = cap_config["x_anchors"], 0, cap_config["z_anchors"]
    obj = spin(anchors, cap_config["vector_locations"])

    if cap_params["n_cuts"] > 0:
        for i in range(cap_params["n_cuts"]):
            angle = cap_params["cut_angles"][i]; width = cap_params["cut_widths"][i]
            depth = cap_params["cut_depths"][i]; rot = cap_params["cut_rotations"][i]
            vertices = [[0, 0, 0.4], [0.4, -width, 0.4], [0.4, width, 0.4], [0, 0, -1], [0.4, -width, -0.01], [0.4, width, -0.01]]
            faces = [[0, 1, 2], [1, 0, 3, 4], [2, 1, 4, 5], [0, 2, 5, 3], [5, 4, 3]]
            cutter = mesh2obj(data2mesh(vertices, [], faces))
            displace_vertices(cutter, lambda x, y, z: (0, 2 * y * y, 0))
            modify_mesh(cutter, "SUBSURF", render_levels=5, levels=5, subdivision_type="SIMPLE")
            cutter.location = np.cos(angle) * depth, np.sin(angle) * depth, 0
            cutter.rotation_euler = 0, 0, rot
            modify_mesh(obj, "WELD", merge_threshold=0.002)
            modify_mesh(obj, "BOOLEAN", object=cutter, operation="DIFFERENCE", apply=True)
            delete(cutter)

    remesh_with_attrs(obj, face_size)
    _apply_geomod(obj, _build_geo_xyz(), apply=True)
    _apply_geomod(obj, _build_geo_morel(cap_params["morel_voronoi_scale"], cap_params["morel_randomness"]), apply=True)

    if cap_params["is_morel"]:
        with SelectObjects(obj):
            _set_active_attribute(obj, "morel")
            try: bpy.ops.geometry.attribute_convert(mode="VERTEX_GROUP")
            except Exception: pass
        modify_mesh(obj, "DISPLACE", vertex_group="morel", strength=0.04, mid_level=0.7)

    # Assign cap surface material (before joining gills)
    obj.data.materials.clear()
    obj.data.materials.append(MAT_CAP)

    if cap_params["gill_config"] is not None:
        gc = cap_params["gill_config"]
        gill = spin((gc["x_anchors"], 0, gc["z_anchors"]), gc["vector_locations"], dupli=True, loop=True, rotation_resolution=cap_params["gill_rotation_resolution"])
        subsurface2face_size(gill, face_size)
        modify_mesh(gill, "SMOOTH", apply=True, iterations=3)
        # Assign gill material before join so the slot survives
        gill.data.materials.clear()
        gill.data.materials.append(MAT_GILL)
        obj = join_objects([obj, gill])

    texture = bpy.data.textures.new(name="cap", type=cap_params["texture_type"])
    texture.noise_scale = cap_params["texture_noise_scale"]
    modify_mesh(obj, "DISPLACE", strength=0.008, texture=texture, mid_level=0)
    _apply_geomod(obj, _build_geo_extension(0.1), apply=True)
    modify_mesh(obj, "SIMPLE_DEFORM", deform_method="TWIST", angle=cap_params["twist_angle"], deform_axis="X")

    r1, r2, r3, r4 = cap_params["vertex_scale_factors"]
    displace_vertices(obj, lambda x, y, z: (np.where(x > 0, r1, r2) * x, np.where(y > 0, r3, r4) * y, 0))
    return obj

def _build_stem(stem_params, face_size):
    inner_radius = stem_params['inner_radius']
    web_builder_name = stem_params['web_builder']
    has_band = stem_params['has_band']

    length = log_uniform(0.4, 0.8)
    x_anchors = (0, inner_radius, log_uniform(1, 2) * inner_radius, inner_radius * uniform(1, 1.2), 0)
    z_anchors = 0, 0, -length * uniform(0.3, 0.7), -length, -length
    obj = spin((x_anchors, 0, z_anchors), [1, 4])
    remesh_with_attrs(obj, face_size)

    if has_band:
        _apply_geomod(obj, _build_geo_band(length, uniform(0.008, 0.01)), apply=True)

    # Assign stem body material
    obj.data.materials.clear()
    obj.data.materials.append(MAT_STEM)

    if web_builder_name is not None:
        if web_builder_name == 'hollow':
            outer_r = inner_radius * uniform(2, 3.5); z = uniform(0.0, 0.05); wl = log_uniform(0.2, 0.4)
            web = spin(((inner_radius, (outer_r + inner_radius) / 2, outer_r), 0, (-z, -z - uniform(0.3, 0.4) * wl, -z - wl)))
            modify_mesh(web, 'SUBSURF', apply=True, render_levels=3, levels=3)
            _apply_geomod(web, _build_geo_voronoi(), apply=True)
            modify_mesh(web, 'SMOOTH', apply=True, iterations=2)
        else:
            outer_r = inner_radius * uniform(1.5, 3.5); z = uniform(0.0, 0.05); wl = uniform(0.15, 0.2)
            web = spin(((inner_radius, (outer_r + inner_radius) / 2, outer_r), 0, (-z, -z - uniform(0.3, 0.4) * wl, -z - wl)))
            _apply_geomod(web, _build_geo_inverse_band(-uniform(0.008, 0.01)), apply=True)
            modify_mesh(web, 'SMOOTH', apply=True, iterations=3)
        _apply_geomod(web, _build_geo_extension(), apply=True)
        subsurface2face_size(web, face_size / 2)
        modify_mesh(web, 'SMOOTH', apply=True, iterations=3)
        # Assign web material before join
        web.data.materials.clear()
        web.data.materials.append(MAT_WEB)
        obj = join_objects([web, obj])

    texture = bpy.data.textures.new(name="stem_stucci", type="STUCCI")
    texture.noise_scale = uniform(0.005, 0.01)
    modify_mesh(obj, 'DISPLACE', strength=0.008, texture=texture, mid_level=0)
    modify_mesh(obj, 'SIMPLE_DEFORM', deform_method='BEND', angle=-uniform(0, np.pi / 2), deform_axis='Y')
    return obj

# ---------------------------------------------------------------------------
# Build a single growth (cap + stem) (copied verbatim)
# ---------------------------------------------------------------------------

def _build_growth(factory_seed, i, face_size):
    with FixedSeed(factory_seed):
        if uniform(0, 1) < 0.4:
            _base_hue = uniform(0, 1)
        else:
            _base_hue = uniform(0.02, 0.15)
        cap_params = _sample_cap_params(factory_seed)
        stem_params = _sample_stem_params(factory_seed, cap_params["inner_radius"])

    geom_seed = int_hash((factory_seed, i))
    with FixedSeed(geom_seed):
        cap = _build_cap(cap_params, face_size)
        stem = _build_stem(stem_params, face_size)
        obj = join_objects([cap, stem])
        origin2lowest(obj)
    return obj, cap_params["radius"]

# ---------------------------------------------------------------------------
# Placement logic (copied verbatim)
# ---------------------------------------------------------------------------

def _find_closest(keypoints, rotations, start_locs, directions, radius):
    vertices = [k.copy() for k in keypoints]
    locations = [np.zeros(3)]
    scales = np.tile(uniform(0.3, 1.2, len(keypoints))[:, np.newaxis], 3)
    for i in range(len(vertices)):
        vertices[i] = (np.array(Euler(rotations[i]).to_matrix()) @ np.diag(scales[i]) @ vertices[i].T).T
    for i in range(1, len(vertices)):
        basis = np.concatenate(vertices[:i])
        kd = kdtree.KDTree(len(basis))
        for idx, v in enumerate(basis):
            kd.insert(v, idx)
        kd.balance()
        for d in np.linspace(0, 4, 20) * radius:
            offset = start_locs[i] + directions[i] * d
            if min(kd.find(v + offset)[-1] for v in vertices[i]) > 0.008:
                break
        else:
            offset = start_locs[i] + directions[i] * 4 * radius
        vertices[i] += offset
        locations.append(offset)
    return locations, rotations, scales

def _cluster_make(keypoints, lowered, radius):
    n = len(keypoints)
    angles = polygon_angles(n, np.pi / 10, np.pi * 2)
    rot_y = uniform(0, np.pi / 6, n) if lowered else np.zeros(n)
    rot_z = angles + uniform(-np.pi / 8, np.pi / 8, n)
    rotations = np.stack([np.zeros(n), rot_y, rot_z], -1)
    start_locs = np.zeros((n, 3))
    directions = np.stack([np.cos(angles), np.sin(angles), np.zeros(n)], -1)
    return _find_closest(keypoints, rotations, start_locs, directions, radius)

def _directional_make(keypoints, lowered, radius):
    n = len(keypoints)
    rot_y = uniform(0, np.pi / 6, n) if lowered else np.zeros(n)
    rot_z = -np.pi / 2 + uniform(-np.pi / 8, np.pi / 8, n)
    rotations = np.stack([np.zeros(n), rot_y, rot_z], -1)
    start_locs = np.stack([np.linspace(0, radius * n * 0.4, n), np.zeros(n), np.zeros(n)], -1)
    directions = np.tile([0, 1, 0], (n, 1))
    return _find_closest(keypoints, rotations, start_locs, directions, radius)

# ---------------------------------------------------------------------------
# Build (MushroomFactory)
# ---------------------------------------------------------------------------

MAX_CLUSTER = 10

def build(seed=0, face_size=0.01):
    factory_seed = seed

    with FixedSeed(factory_seed):
        maker_choice = np.random.choice([0, 1])  # 0=directional, 1=cluster
        lowered = uniform(0, 1) < 0.5

        if uniform(0, 1) < 0.4:
            _bh = uniform(0, 1)
        else:
            _bh = uniform(0.02, 0.15)

        cap_params = _sample_cap_params(factory_seed)
        stem_params = _sample_stem_params(factory_seed, cap_params["inner_radius"])
        radius = cap_params["radius"]
        tolerant_length = uniform(0, 0.2)

    geom_seed = int_hash((factory_seed, 0))

    with FixedSeed(geom_seed):
        n = np.random.randint(1, 6)
        mushrooms = []
        keypoints_list = []

        for j in range(n):
            obj, _radius = _build_growth(factory_seed, j + 0 * MAX_CLUSTER, face_size / 2)
            clone = deep_clone_obj(obj)
            modify_mesh(clone, 'REMESH', voxel_size=0.04)
            mushrooms.append(obj)
            k = np.array([v.co for v in clone.data.vertices if v.co[-1] > tolerant_length])
            if len(k) == 0:
                k = np.array([v.co for v in clone.data.vertices])
            if len(k) == 0:
                k = np.zeros((1, 3))
            keypoints_list.append(k)
            delete(clone)

        if maker_choice == 0:
            locations, rotations, scales = _directional_make(keypoints_list, lowered, radius)
        else:
            locations, rotations, scales = _cluster_make(keypoints_list, lowered, radius)

        for m, loc, rot, scl in zip(mushrooms, locations, rotations, scales):
            m.location = loc
            m.rotation_euler = rot
            m.scale = scl
            apply_transform(m, loc=True)

        obj = join_objects(mushrooms)
        modify_mesh(
            obj, 'SIMPLE_DEFORM',
            deform_method='BEND',
            angle=uniform(-np.pi / 8, np.pi / 8),
            deform_axis=np.random.choice(['X', 'Y']),
        )

    obj.name = "MushroomFactory"
    return obj

# ---------------------------------------------------------------------------
# Clear scene
# ---------------------------------------------------------------------------

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    for tex in list(bpy.data.textures):
        bpy.data.textures.remove(tex)
    for ng in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(ng)
    for c in list(bpy.data.curves):
        bpy.data.curves.remove(c)
    bpy.context.scene.cursor.location = (0, 0, 0)

SEED = int(os.environ.get('SEED', 0))
clear_scene()

# MushroomGrowthFactory.__init__(factory_seed) opens FixedSeed(factory_seed) and:
#   base_hue = build_base_hue()  # consumes 1-2 uniforms
#   material_func = lambda : shader_mushroom(base_hue)
#   cap_factory  = MushroomCapFactory(factory_seed, base_hue, material_func)
#   stem_factory = MushroomStemFactory(factory_seed, cap.inner_radius, material_func)
#
# Both cap_factory and stem_factory enter their own FixedSeed(factory_seed) inside,
# so each starts from the raw seed again. Materials inside each factory are created
# AFTER the geometry-parameter sampling consumes RNG.

with FixedSeed(SEED):
    _BASE_HUE = build_base_hue_value()

# ---- Cap factory __init__ ----
# Replay cap param sampling (same RNG consumption as _sample_cap_params) then
# materialize the selected shader followed by the gill material (shader_mushroom).
with FixedSeed(SEED):
    _x_scale, _z_scale = uniform(0.7, 1.4, 2)
    _cap_cfgs = [_campanulate, _conical, _convex, _depressed, _flat,
                 _infundiuliform, _ovate, _umbillicate, _umbonate]
    _cfg_w = np.array([2, 2, 2, 1, 2, 1, 2, 1, 1])
    _cap_cfg = np.random.choice(_cap_cfgs, p=_cfg_w / _cfg_w.sum())()
    _cap_cfg = {
        **_cap_cfg,
        "x_anchors": [v * _x_scale for v in _cap_cfg["x_anchors"]],
        "z_anchors": [v * _z_scale for v in _cap_cfg["z_anchors"]],
    }
    _radius = max(_cap_cfg["x_anchors"])
    _inner_radius = float(log_uniform(0.2, 0.35)) * _radius
    # gill_config consumption (np.random.choice of 3 + optional lambda call)
    _gill_choice = np.random.choice([0, 1, 2], p=np.array([1, 1, 1]) / 3.0)
    if _cap_cfg["has_gill"] and _gill_choice != 2:
        if _gill_choice == 0:
            _ = [uniform(0.05, 0.08), uniform(0, 0.02)]
        else:
            _ = [uniform(0.05, 0.08), uniform(0.08, 0.1)]
    # shader_func choice
    _sh_w = np.array([2, 1, 1, 1])
    _shader_idx = int(np.random.choice(4, p=_sh_w / _sh_w.sum()))
    # is_morel consumption: uniform(0, 1) < 0.5 AND chosen shader == shader_cap (idx 0)
    _is_morel_flag = uniform(0, 1) < 0.5 and _shader_idx == 0

    # Now sample the cap material first, then the gill (mushroom-body) material.
    MAT_CAP = _CAP_SHADERS[_shader_idx](_BASE_HUE, name="MushroomFactory_Cap")
    MAT_GILL = make_shader_mushroom(_BASE_HUE, name="MushroomFactory_Gill")

# ---- Stem factory __init__ ----
with FixedSeed(SEED):
    _web_opts = ['hollow', 'solid', None]
    _web_w = np.array([1, 1, 2])
    _ = np.random.choice(_web_opts, p=_web_w / _web_w.sum())
    _ = uniform(0, 1) < 0.75
    MAT_STEM = make_shader_mushroom(_BASE_HUE, name="MushroomFactory_Stem")
    MAT_WEB = make_shader_mushroom(_BASE_HUE, name="MushroomFactory_Web")

for _m in (MAT_CAP, MAT_GILL, MAT_STEM, MAT_WEB):
    _m.use_fake_user = True

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

obj = build(SEED)
print(f"MushroomFactory built: {len(obj.data.vertices)} verts, "
      f"{len(obj.data.polygons)} faces, "
      f"{len(obj.data.materials)} material slots")

