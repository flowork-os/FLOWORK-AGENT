# [FL_INDEX: keywords="blender_factory, procedural_3d, MirrorFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: MirrorFactory | Category: factories_geo
# Prompt: A 3D model of a rectangular wall mirror rendered from a three-quarter perspective. The mirror features a thin flat rectangular frame with a dark border and a large reflective central panel with a warm bronze-tinted surface.

import os
import math
import bpy
import bmesh
import random
import colorsys
import numpy as np
from numpy.random import uniform


# ============================================================================
# ============================================================================

def seed_all(seed: int):
    np.random.seed(seed)
    random.seed(seed)


def hsv2rgba(hsv):
    h, s, v = hsv
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)


def _mat_log_uniform(lo, hi):
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
        v * float(_mat_log_uniform(0.2, 0.5)),
    )


def metal_hsv():
    if np.random.uniform() < 0.2:
        return metal_natural_hsv()
    return (np.random.uniform(0, 1),
            np.random.uniform(0.3, 0.6),
            _mat_log_uniform(0.02, 0.5))


def bark_hsv():
    wood_hex = ["#8b5a2b", "#a0522d", "#cd853f", "#d2691e",
                "#6b4423", "#5d4037", "#7b3f00"]
    h_str = wood_hex[np.random.randint(0, len(wood_hex))].lstrip("#")
    r, g, b = (int(h_str[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return colorsys.rgb_to_hsv(r, g, b)


def weighted_sample_mat(reg):
    classes, weights = zip(*reg)
    weights = np.array(weights, dtype=float)
    return classes[int(np.random.choice(len(classes), p=weights / weights.sum()))]


def _new_material(name: str) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    return mat


def _set_principled(bsdf, **kw):
    """Set Principled BSDF inputs with Blender-version-tolerant socket names."""

    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Specular": ("Specular IOR Level", "Specular"),
        "Coat Weight": ("Coat Weight", "Clearcoat"),
        "Sheen Weight": ("Sheen Weight", "Sheen"),
    }
    for k, v in kw.items():
        names = aliases.get(k, (k,))
        for name in names:
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


# ----------------------------------------------------------------------------
# Mirror canvas shader (direct port of metal/mirror.py:shader_mirror)
# ----------------------------------------------------------------------------
def make_mirror(name="Mirror") -> bpy.types.Material:
    mat = _new_material(name)
    nt = mat.node_tree
    glossy = nt.nodes.new("ShaderNodeBsdfGlossy")
    glossy.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    if "Roughness" in glossy.inputs:
        glossy.inputs["Roughness"].default_value = 0.0
    _connect_output(nt, glossy)
    return mat


# ----------------------------------------------------------------------------
# Metal shaders (decorative_metal entries)
# ----------------------------------------------------------------------------
def make_brushed_metal(name="BrushedMetal", base_color_hsv=None) -> bpy.types.Material:
    """Re-impl of materials/metal/brushed_metal.py."""

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


def make_galvanized_metal(name="GalvanizedMetal", base_color_hsv=None) -> bpy.types.Material:
    """Re-impl of materials/metal/galvanized_metal.py."""

    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(voronoi, "voronoi_dimensions"):
        try: voronoi.voronoi_dimensions = "4D"
        except TypeError: voronoi.voronoi_dimensions = "3D"
    if hasattr(voronoi, "distance"):
        try: voronoi.distance = "MINKOWSKI"
        except TypeError: pass
    voronoi.inputs["Scale"].default_value = 500.0
    if "W" in voronoi.inputs:
        voronoi.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(tex_coord.outputs["Object"], voronoi.inputs["Vector"])

    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[3].default_value = 0.1
    map_range.inputs[4].default_value = 0.5
    nt.links.new(voronoi.outputs[0], map_range.inputs[0])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf, Metallic=1.0,
        **{"Specular IOR Level": 0.0, "Base Color": hsv2rgba(base_color_hsv)},
    )
    nt.links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat


def make_grained_metal(name="GrainedMetal", base_color_hsv=None) -> bpy.types.Material:
    """Re-impl of materials/metal/grained_and_polished_metal.py."""

    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2000.0
    if "Detail" in noise.inputs:     noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs: noise.inputs["Distortion"].default_value = 2.0
    if "W" in noise.inputs:          noise.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    roughness_input = float(np.random.uniform(0.0, 1.0))
    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[0].default_value = roughness_input
    map_range.inputs[3].default_value = 0.05
    map_range.inputs[4].default_value = 0.25

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
    mul3.inputs[1].default_value = 0.01
    nt.links.new(mul2.outputs[0], mul3.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul3.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf, Metallic=1.0,
        **{"Specular IOR Level": 0.0, "Base Color": hsv2rgba(base_color_hsv)},
    )
    nt.links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


def make_hammered_metal(name="HammeredMetal", base_color_hsv=None) -> bpy.types.Material:
    """Re-impl of materials/metal/hammered_metal.py."""

    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(voronoi, "feature"):
        try: voronoi.feature = "SMOOTH_F1"
        except TypeError: pass
    voronoi.inputs["Scale"].default_value = 300.0
    if "Smoothness" in voronoi.inputs:
        voronoi.inputs["Smoothness"].default_value = 0.2
    if "W" in voronoi.inputs:
        voronoi.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(tex_coord.outputs["Object"], voronoi.inputs["Vector"])

    pow_node = nt.nodes.new("ShaderNodeMath")
    pow_node.operation = "POWER"
    pow_node.inputs[1].default_value = 2.5
    dist_out = voronoi.outputs.get("Distance") or voronoi.outputs[0]
    nt.links.new(dist_out, pow_node.inputs[0])

    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = _mat_log_uniform(0.001, 0.003)
    nt.links.new(pow_node.outputs[0], mul.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf, Metallic=1.0,
        **{"Specular IOR Level": 0.0, "Base Color": hsv2rgba(base_color_hsv), "Roughness": 0.1},
    )
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


# ----------------------------------------------------------------------------
# Wood shader (wood.Wood) — approximates wood.py grain using multi-octave noise
# (MusgraveTexture removed in Blender 5.0).
# ----------------------------------------------------------------------------
def make_wood(name="Wood", color=None) -> bpy.types.Material:
    if color is None:
        h, s, v = bark_hsv()
        color = hsv2rgba((h + np.random.uniform(-0.0, 0.05),
                          max(0.0, s + np.random.uniform(-0.3, 0.2)),
                          v * _mat_log_uniform(0.2, 20)))
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (5.0, 100.0, 100.0)
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    grain = nt.nodes.new("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = 10.0
    if "Detail" in grain.inputs:     grain.inputs["Detail"].default_value = 15.0
    if "Distortion" in grain.inputs: grain.inputs["Distortion"].default_value = 0.5
    nt.links.new(mapping.outputs["Vector"], grain.inputs["Vector"])

    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_node.inputs["Saturation"].default_value = 0.8
    hsv_node.inputs["Value"].default_value = 0.2
    hsv_node.inputs["Color"].default_value = color

    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
    nt.links.new(_noise_fac_output(grain), mix.inputs[0])
    nt.links.new(hsv_node.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = color

    noise_r = nt.nodes.new("ShaderNodeTexNoise")
    noise_r.inputs["Scale"].default_value = _mat_log_uniform(40, 50)
    base_rough = float(np.random.uniform(0.0, 0.4))
    fc = _build_float_curve(nt, _noise_fac_output(noise_r),
                            [(0, base_rough),
                             (1, base_rough + float(np.random.uniform(0.0, 0.8)))])

    mul_disp = nt.nodes.new("ShaderNodeMath")
    mul_disp.operation = "MULTIPLY"
    mul_disp.inputs[1].default_value = _mat_log_uniform(0.0002, 0.01)
    nt.links.new(_noise_fac_output(grain), mul_disp.inputs[0])
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_disp.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf,
                    **{"Coat Weight": float(np.clip(np.random.uniform(0, 1.4), 0, 1))})
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(fc.outputs["Value"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


# ----------------------------------------------------------------------------
# Plywood shaders (wood/plywood.py)
#   WhitePlywood    — tinted Principled BSDF (trivial port)
#   BlackPlywood    — shader_shelves_black_wood  : Voronoi grain + wave mix
#                     + 3-stop dark colorramp + displacement
#   BlondePlywood   — shader_shelves_wood        : same structure, HSV colorramp
#
# BlackPlywood and BlondePlywood share the same graph skeleton, so we use a
# shared builder and pass in the colour stops. MusgraveTexture is substituted
# with a stretched NoiseTexture (Blender 5.0 removal).
# ----------------------------------------------------------------------------
def make_white_plywood(name="WhitePlywood") -> bpy.types.Material:
    """Re-impl of plywood.py:shader_shelves_white + shader_shelves_white_sampler."""

    v = float(np.random.uniform(0.7, 1.0))
    base_color = (
        v * (1.0 + float(np.random.normal(0, 0.005))),
        v * (1.0 + float(np.random.normal(0, 0.005))),
        v * (1.0 + float(np.random.normal(0, 0.005))),
        1.0,
    )
    roughness = float(np.random.uniform(0.7, 1.0))
    mat = _new_material(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, **{"Base Color": base_color, "Roughness": roughness})
    _connect_output(nt, bsdf)
    return mat


def _build_plywood_shelves_graph(mat, color_ramp_builder, wave_scale, roughness):
    """Shared graph for shader_shelves_black_wood / shader_shelves_wood.

    color_ramp_builder(cr) populates the 3-stop base-color colorramp.
    """

    nt = mat.node_tree
    tex_coord_1 = nt.nodes.new("ShaderNodeTexCoord")
    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    mapping_1.inputs["Scale"].default_value = (0.1, 2.0, 2.0)
    nt.links.new(tex_coord_1.outputs["Object"], mapping_1.inputs["Vector"])

    noise_1 = nt.nodes.new("ShaderNodeTexNoise")
    noise_1.inputs["Scale"].default_value = 100.0
    if "Detail" in noise_1.inputs:     noise_1.inputs["Detail"].default_value = 10.0
    if "Distortion" in noise_1.inputs: noise_1.inputs["Distortion"].default_value = 2.0
    nt.links.new(mapping_1.outputs["Vector"], noise_1.inputs["Vector"])

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi.inputs["Scale"].default_value = 40.0
    nt.links.new(_noise_fac_output(noise_1), voronoi.inputs["Vector"])

    cr1 = nt.nodes.new("ShaderNodeValToRGB")
    fac1 = cr1.inputs.get("Fac") or cr1.inputs[0]
    nt.links.new(voronoi.outputs.get("Color") or voronoi.outputs[0], fac1)
    cr1.color_ramp.elements[0].position = 0.0864
    cr1.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr1.color_ramp.elements[1].position = 0.1091
    cr1.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (wave_scale, 0.1, 0.1)
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    if "Detail" in noise.inputs:     noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs: noise.inputs["Distortion"].default_value = 2.0
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])

    # MusgraveTexture substitute — stretched secondary noise fed from noise.Fac
    musgrave_sub = nt.nodes.new("ShaderNodeTexNoise")
    musgrave_sub.inputs["Scale"].default_value = 20.0
    if "Detail" in musgrave_sub.inputs: musgrave_sub.inputs["Detail"].default_value = 3.0
    nt.links.new(_noise_fac_output(noise), musgrave_sub.inputs["Vector"])

    mix1 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix1, "data_type"): mix1.data_type = "RGBA"
    nt.links.new(_noise_fac_output(musgrave_sub), mix1.inputs[6])
    nt.links.new(noise.outputs.get("Color") or noise.outputs[0], mix1.inputs[7])

    cr2 = nt.nodes.new("ShaderNodeValToRGB")
    fac2 = cr2.inputs.get("Fac") or cr2.inputs[0]
    nt.links.new(mix1.outputs[2], fac2)
    cr2.color_ramp.elements[0].position = 0.0818
    cr2.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr2.color_ramp.elements[1].position = 0.8500
    cr2.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    mix2 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix2, "data_type"): mix2.data_type = "RGBA"
    mix2.inputs[0].default_value = 0.6
    nt.links.new(cr1.outputs["Color"], mix2.inputs[6])
    nt.links.new(cr2.outputs["Color"], mix2.inputs[7])

    # Base-color 3-stop colorramp (filled by caller)
    cr_base = nt.nodes.new("ShaderNodeValToRGB")
    fac_base = cr_base.inputs.get("Fac") or cr_base.inputs[0]
    nt.links.new(mix2.outputs[2], fac_base)
    # Add the 3rd stop (ValToRGB starts with 2)
    cr_base.color_ramp.elements.new(0)
    color_ramp_builder(cr_base)

    # Displacement mix (unchanged 0.004 factor)
    mix3 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix3, "data_type"): mix3.data_type = "RGBA"
    mix3.inputs[0].default_value = 0.004
    nt.links.new(cr1.outputs["Color"], mix3.inputs[6])
    nt.links.new(cr2.outputs["Color"], mix3.inputs[7])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    disp.inputs["Scale"].default_value = 0.01
    nt.links.new(mix3.outputs[2], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=roughness)
    nt.links.new(cr_base.outputs["Color"], bsdf.inputs["Base Color"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])


def make_black_plywood(name="BlackPlywood") -> bpy.types.Material:
    """Re-impl of plywood.py:shader_shelves_black_wood."""

    wave_scale = float(np.random.uniform(1.0, 3.0))
    dark_scale = float(np.random.uniform(0.0, 0.01))
    gray_scale = float(np.random.uniform(0.01, 0.03))
    rgb = (float(np.random.uniform(0.015, 0.035)),
           float(np.random.uniform(0.0, 0.01)),
           float(np.random.uniform(0.0, 0.01)))
    roughness = float(np.random.uniform(0.75, 1.0))

    def build_base_ramp(cr):
        cr.color_ramp.elements[0].position = 0.15
        cr.color_ramp.elements[0].color = (dark_scale, dark_scale, dark_scale, 1.0)
        cr.color_ramp.elements[1].position = 0.5
        cr.color_ramp.elements[1].color = (gray_scale, gray_scale, gray_scale, 1.0)
        cr.color_ramp.elements[2].position = 1.0
        cr.color_ramp.elements[2].color = (*rgb, 1.0)

    mat = _new_material(name)
    _build_plywood_shelves_graph(mat, build_base_ramp, wave_scale, roughness)
    return mat


def make_blonde_plywood(name="BlondePlywood") -> bpy.types.Material:
    """Re-impl of plywood.py:shader_shelves_wood."""

    bright_hsv = (float(np.random.uniform(0.03, 0.09)),
                  float(np.random.uniform(0.5, 0.7)),
                  float(np.random.uniform(0.7, 1.0)))
    mid_hsv = (float(np.random.uniform(0.02, 0.06)),
               float(np.random.uniform(0.6, 1.0)),
               float(np.random.uniform(0.3, 0.6)))
    dark_hsv = (float(np.random.uniform(0.03, 0.05)),
                float(np.random.uniform(0.6, 1.0)),
                float(np.random.uniform(0.1, 0.3)))
    wave_scale = float(np.random.uniform(1.0, 3.0))
    roughness = float(np.random.uniform(0.75, 1.0))

    def build_base_ramp(cr):
        cr.color_ramp.elements[0].position = 0.02
        cr.color_ramp.elements[0].color = hsv2rgba(dark_hsv)
        cr.color_ramp.elements[1].position = 0.11
        cr.color_ramp.elements[1].color = hsv2rgba(mid_hsv)
        cr.color_ramp.elements[2].position = 0.8
        cr.color_ramp.elements[2].color = hsv2rgba(bright_hsv)

    mat = _new_material(name)
    _build_plywood_shelves_graph(mat, build_base_ramp, wave_scale, roughness)
    return mat


# ----------------------------------------------------------------------------
# Registries (mirror composition/material_assignments.py)
# ----------------------------------------------------------------------------
# material_assignments.py:122-124 — mirrors
MIRRORS = [
    (make_mirror, 1.0),
]

# material_assignments.py:171-176 — decorative_metal
DECORATIVE_METAL = [
    (make_brushed_metal,    1.0),
    (make_galvanized_metal, 1.0),
    (make_grained_metal,    1.0),
    (make_hammered_metal,   1.0),
]

# material_assignments.py:29-34 — woods
WOODS = [
    (make_wood,           1.0),
    (make_white_plywood,  0.1),
    (make_black_plywood,  0.1),
    (make_blonde_plywood, 0.1),
]

# material_assignments.py:282 — frame = decorative_metal + woods
FRAME = DECORATIVE_METAL + WOODS

REGISTRY = {
    "mirrors": MIRRORS,
    "frame":   FRAME,
}


def get_material(registry_key: str, name: str = None) -> bpy.types.Material:
    ctor = weighted_sample_mat(REGISTRY[registry_key])
    return ctor(name=name or registry_key.title())


# ============================================================================
# wear_tear post-processing — faithful raw-bpy ports
# ============================================================================
SCRATCH_LABEL = "scratch"
EDGE_WEAR_LABEL = "wear_tear"


def _find_node(nt, bl_idname):
    return next((n for n in nt.nodes if n.bl_idname == bl_idname), None)


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


def _value_node(nt, value):
    n = nt.nodes.new("ShaderNodeValue")
    n.outputs[0].default_value = value
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
    """Faithful raw-bpy port of wear_tear/scratches.py:Scratches.apply_over."""

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
        mix.data_type = "RGBA"
    if hasattr(mix, "clamp_result"):
        try: mix.clamp_result = True
        except TypeError: pass
    if hasattr(mix, "clamp_factor"):
        try: mix.clamp_factor = False
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
    """Faithful raw-bpy port of wear_tear/edge_wear.py:EdgeWear.apply_over."""

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
# === End of inlined material library ========================================
# ============================================================================


# ── Seed (overridden by Phase 1) ──
SEED = int(os.environ.get("SEED", 0))
random.seed(SEED)
np.random.seed(SEED)


# ── Scene cleanup ──
def clear_scene():
    bpy.context.scene.cursor.location = (0, 0, 0)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)


# ============================================================================
# FixedSeed(factory_seed)). Sampling order follows wall_art.py:102-117
# (MirrorFactory.assign_materials):
#   1. surface (canvas) = weighted_sample(mirrors)   -> Mirror
#   2. (Mirror shader consumes no RNG in generate())
#   3. frame_surface   = weighted_sample(frame)
#   4. scratch gate    (uniform > scratch_prob)
#   5. edge_wear gate  (uniform > edge_wear_prob)
#
# Note: the Mirror material has zero RNG consumption, so sampling order
# ============================================================================
seed_all(SEED)
MAT_CANVAS = get_material("mirrors", "MirrorCanvas")
MAT_FRAME  = get_material("frame",   "MirrorFrame")
WEAR_DO_SCRATCH  = (np.random.uniform() <= 0.5)
WEAR_DO_EDGEWEAR = (np.random.uniform() <= 0.5)


# ============================================================================
# === Geometry (verbatim copy from objects_blender/wall_decorations/
#     MirrorFactory.py, with per-part material append calls added). =========
# ============================================================================

def apply_tf(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def join_objs(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    return bpy.context.active_object


def build(seed=0):
    np.random.seed(seed)
    rng = np.random.default_rng(seed)
    clear_scene()

    width = float(np.exp(rng.uniform(math.log(0.4), math.log(2.0))))
    height = float(np.exp(rng.uniform(math.log(0.4), math.log(2.0))))
    thickness = float(rng.uniform(0.02, 0.05))
    depth = float(rng.uniform(0.01, 0.02))
    bevel_segments = int(rng.choice([0, 1, 4]))
    bevel_width = float(rng.uniform(depth / 4, depth / 2))

    hw = width / 2
    hh = height / 2

    # Canvas (flat panel in YZ plane, facing +X)
    bm = bmesh.new()
    v0 = bm.verts.new((0, -hw, -hh))
    v1 = bm.verts.new((0,  hw, -hh))
    v2 = bm.verts.new((0,  hw,  hh))
    v3 = bm.verts.new((0, -hw,  hh))
    bm.faces.new([v0, v1, v2, v3])
    mesh_canvas = bpy.data.meshes.new("canvas")
    bm.to_mesh(mesh_canvas)
    bm.free()
    canvas = bpy.data.objects.new("canvas", mesh_canvas)
    bpy.context.scene.collection.objects.link(canvas)

    sol = canvas.modifiers.new("sol", "SOLIDIFY")
    sol.thickness = 0.005
    sol.offset = 1
    bpy.context.view_layer.objects.active = canvas
    bpy.ops.object.modifier_apply(modifier=sol.name)
    apply_tf(canvas)

    # Mirror material on canvas
    canvas.data.materials.append(MAT_CANVAS)

    # Frame ring
    bm2 = bmesh.new()
    ohw = hw + thickness
    ohh = hh + thickness
    ov0 = bm2.verts.new((0, -ohw, -ohh))
    ov1 = bm2.verts.new((0,  ohw, -ohh))
    ov2 = bm2.verts.new((0,  ohw,  ohh))
    ov3 = bm2.verts.new((0, -ohw,  ohh))
    iv0 = bm2.verts.new((0, -hw, -hh))
    iv1 = bm2.verts.new((0,  hw, -hh))
    iv2 = bm2.verts.new((0,  hw,  hh))
    iv3 = bm2.verts.new((0, -hw,  hh))
    bm2.faces.new([ov0, ov1, iv1, iv0])
    bm2.faces.new([ov1, ov2, iv2, iv1])
    bm2.faces.new([ov2, ov3, iv3, iv2])
    bm2.faces.new([ov3, ov0, iv0, iv3])
    mesh_frame = bpy.data.meshes.new("frame")
    bm2.to_mesh(mesh_frame)
    bm2.free()
    frame = bpy.data.objects.new("frame", mesh_frame)
    bpy.context.scene.collection.objects.link(frame)

    sol2 = frame.modifiers.new("sol2", "SOLIDIFY")
    sol2.thickness = depth
    sol2.offset = 1
    bpy.context.view_layer.objects.active = frame
    bpy.ops.object.modifier_apply(modifier=sol2.name)

    if bevel_segments > 0:
        bv = frame.modifiers.new("bevel", "BEVEL")
        bv.width = bevel_width
        bv.segments = bevel_segments
        bpy.ops.object.modifier_apply(modifier=bv.name)

    apply_tf(frame)

    # Frame material
    frame.data.materials.append(MAT_FRAME)

    result = join_objs([canvas, frame])
    result.name = "MirrorFactory"
    apply_tf(result)

    # wear_tear post-processing (50/50 gates decided in Phase 1)
    if result is not None:
        if WEAR_DO_SCRATCH:  apply_scratches(result)
        if WEAR_DO_EDGEWEAR: apply_edge_wear(result)

    return result


build(SEED)
