# [FL_INDEX: keywords="blender_factory, procedural_3d, CellShelfFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: CellShelfFactory | Category: factories_geo
# Prompt: A 3D model of a wide rectangular cell shelf unit rendered from a three-quarter perspective, featuring a grid of open compartments arranged in rows and columns with diagonal cross-dividers inside each cell, all in a light wood-grain appearance.

"""
CellShelfFactory — texture-enabled standalone port.

Geometry is copied verbatim from
(see the "Original geometry" block below).

Shader sources translated faithfully from:
        shader_shelves_white        -> make_shelves_white
        shader_shelves_wood         -> make_shelves_wood
        shader_shelves_black_wood   -> make_shelves_black_wood
        shader_metal                -> make_metal_basic
        shader_brushed_metal        -> make_brushed_metal
        shader_galvanized_metal     -> make_galvanized_metal
        shader_grained_metal        -> make_grained_metal
        shader_hammered_metal       -> make_hammered_metal
        shader_brushed_black_metal  -> make_brushed_black_metal

so the wear_tear gates are intentionally NOT applied.
"""
import os
import math
import bpy
import random
import colorsys
import numpy as np
from contextlib import contextmanager

# ============================================================================
# ============================ material library =============================
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


def metal_hsv():
    if np.random.uniform() < 0.2:
        return (float(np.random.uniform(0, 1)),
                float(np.random.uniform(0.0, 0.2)),
                _mat_log_uniform(0.05, 0.3))
    return (float(np.random.uniform(0, 1)),
            float(np.random.uniform(0.3, 0.6)),
            _mat_log_uniform(0.02, 0.5))


def weighted_sample_mat(registry):
    classes, weights = zip(*registry)
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


def _connect_output(nt, bsdf, displacement=None):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    if displacement is not None:
        nt.links.new(displacement, out.inputs["Displacement"])
    return out


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


# ----------------------------------------------------------------------------
# Shelves wood-family shaders (plywood.py) — faithful raw-bpy ports
# ----------------------------------------------------------------------------
def make_shelves_white(name="ShelvesWhite",
                       rgb=None, roughness=None) -> bpy.types.Material:
    """Port of plywood.py:shader_shelves_white."""

    if rgb is None:
        rgb = [0.9, 0.9, 0.9]
    if roughness is None:
        roughness = 0.9
    mat = _new_material(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    _set_principled(bsdf, Roughness=float(roughness))
    _connect_output(nt, bsdf)
    return mat


def _build_shelves_grain_chain(nt, tex_coord, wave_scale_val, z_axis_texture=False):
    """Common wood-grain node chain shared by shelves_wood and shelves_black_wood.

    Returns the `mix_2.outputs["Result"]` socket that drives the base-color
    ColorRamp in the calling shader, plus the `displacement` node whose output
    goes to Material Output.
    """
    # --- texture_coordinate_1 + mapping_1 + noise_1 + voronoi + colorramp_1 ---
    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    if z_axis_texture:
        mapping_1.inputs["Scale"].default_value = (0.1, 0.1, 2.0)
    else:
        mapping_1.inputs["Scale"].default_value = (0.1, 2.0, 2.0)
    nt.links.new(tex_coord.outputs["Object"], mapping_1.inputs["Vector"])

    noise_1 = nt.nodes.new("ShaderNodeTexNoise")
    noise_1.inputs["Scale"].default_value = 100.0
    if "Detail" in noise_1.inputs:
        noise_1.inputs["Detail"].default_value = 10.0
    if "Distortion" in noise_1.inputs:
        noise_1.inputs["Distortion"].default_value = 2.0
    nt.links.new(mapping_1.outputs["Vector"], noise_1.inputs["Vector"])

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi.inputs["Scale"].default_value = 40.0
    # Voronoi Vector takes the noise Fac output (a float broadcast to vec by
    nt.links.new(_noise_fac_output(noise_1), voronoi.inputs["Vector"])

    cr1 = nt.nodes.new("ShaderNodeValToRGB")
    fac_in1 = cr1.inputs.get("Fac") or cr1.inputs[0]
    # original uses voronoi.outputs["Color"] → same semantics
    color_out1 = voronoi.outputs.get("Color") or voronoi.outputs[0]
    nt.links.new(color_out1, fac_in1)
    cr1.color_ramp.elements[0].position = 0.0864
    cr1.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr1.color_ramp.elements[1].position = 0.1091
    cr1.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # --- texture_coordinate + mapping + noise + (musgrave sub) + mix_1 + cr2 -
    mapping = nt.nodes.new("ShaderNodeMapping")
    if z_axis_texture:
        mapping.inputs["Scale"].default_value = (wave_scale_val, wave_scale_val, 0.1)
    else:
        mapping.inputs["Scale"].default_value = (wave_scale_val, 0.1, 0.1)
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    if "Detail" in noise.inputs:
        noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs:
        noise.inputs["Distortion"].default_value = 2.0
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])

    # MusgraveTexture was removed in Blender 5.0 — substitute a second
    # stretched noise so the final mix preserves the "warped grain" feel.
    musgrave = nt.nodes.new("ShaderNodeTexNoise")
    musgrave.inputs["Scale"].default_value = 20.0
    if "Detail" in musgrave.inputs:
        musgrave.inputs["Detail"].default_value = 3.0
    if "Distortion" in musgrave.inputs:
        musgrave.inputs["Distortion"].default_value = 0.0
    nt.links.new(_noise_fac_output(noise), musgrave.inputs["Vector"])

    mix_1 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_1, "data_type"):
        mix_1.data_type = "RGBA"
    # mix_1 uses default factor (0.5), inputs A=musgrave, B=noise.Color
    nt.links.new(_noise_fac_output(musgrave), mix_1.inputs[6])
    noise_color = noise.outputs.get("Color") or noise.outputs[0]
    nt.links.new(noise_color, mix_1.inputs[7])

    cr2 = nt.nodes.new("ShaderNodeValToRGB")
    fac_in2 = cr2.inputs.get("Fac") or cr2.inputs[0]
    # mix_1 Result socket (index 2 for RGBA Mix node)
    nt.links.new(mix_1.outputs[2], fac_in2)
    cr2.color_ramp.elements[0].position = 0.0818
    cr2.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr2.color_ramp.elements[1].position = 0.8500
    cr2.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    # --- mix_2 (Factor 0.6, A=cr1, B=cr2) → base-color driver -----------------
    mix_2 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_2, "data_type"):
        mix_2.data_type = "RGBA"
    mix_2.inputs[0].default_value = 0.6
    nt.links.new(cr1.outputs["Color"], mix_2.inputs[6])
    nt.links.new(cr2.outputs["Color"], mix_2.inputs[7])

    # --- mix_3 (Factor 0.004) → displacement height ---------------------------
    mix_3 = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_3, "data_type"):
        mix_3.data_type = "RGBA"
    mix_3.inputs[0].default_value = 0.004
    nt.links.new(cr1.outputs["Color"], mix_3.inputs[6])
    nt.links.new(cr2.outputs["Color"], mix_3.inputs[7])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    disp.inputs["Scale"].default_value = 0.01
    nt.links.new(mix_3.outputs[2], disp.inputs["Height"])

    return mix_2.outputs[2], disp


def make_shelves_wood(name="ShelvesWood",
                      bright_hsv=None, mid_hsv=None, dark_hsv=None,
                      wave_scale=None, roughness=None,
                      z_axis_texture=False) -> bpy.types.Material:
    """Port of plywood.py:shader_shelves_wood (blonde wood)."""

    if bright_hsv is None: bright_hsv = [0.068, 0.665, 0.805]
    if mid_hsv is None:    mid_hsv    = [0.042, 0.853, 0.447]
    if dark_hsv is None:   dark_hsv   = [0.043, 0.882, 0.183]
    if wave_scale is None: wave_scale = 2.0
    if roughness is None:  roughness  = 0.9

    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    driver_socket, disp = _build_shelves_grain_chain(
        nt, tex_coord, wave_scale, z_axis_texture=z_axis_texture)

    # 3-stop color ramp through dark/mid/bright HSVs (element index 0,1,2)
    cr = nt.nodes.new("ShaderNodeValToRGB")
    fac_in = cr.inputs.get("Fac") or cr.inputs[0]
    nt.links.new(driver_socket, fac_in)
    cr.color_ramp.elements.new(0.5)  # add third element; will repositioned below
    cr.color_ramp.elements[0].position = 0.02
    cr.color_ramp.elements[0].color = hsv2rgba(dark_hsv)
    cr.color_ramp.elements[1].position = 0.11
    cr.color_ramp.elements[1].color = hsv2rgba(mid_hsv)
    cr.color_ramp.elements[2].position = 0.8
    cr.color_ramp.elements[2].color = hsv2rgba(bright_hsv)

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=float(roughness))
    nt.links.new(cr.outputs["Color"], bsdf.inputs["Base Color"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


def make_shelves_black_wood(name="ShelvesBlackWood",
                            dark_scale=None, gray_scale=None, rgb=None,
                            wave_scale=None, roughness=None,
                            z_axis_texture=False) -> bpy.types.Material:
    """Port of plywood.py:shader_shelves_black_wood."""

    if dark_scale is None: dark_scale = 0.005
    if gray_scale is None: gray_scale = 0.02
    if rgb is None:        rgb        = [0.02, 0.002, 0.002]
    if wave_scale is None: wave_scale = 2.0
    if roughness is None:  roughness  = 0.9

    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    driver_socket, disp = _build_shelves_grain_chain(
        nt, tex_coord, wave_scale, z_axis_texture=z_axis_texture)

    cr = nt.nodes.new("ShaderNodeValToRGB")
    fac_in = cr.inputs.get("Fac") or cr.inputs[0]
    nt.links.new(driver_socket, fac_in)
    cr.color_ramp.elements.new(0.5)
    cr.color_ramp.elements[0].position = 0.15
    cr.color_ramp.elements[0].color = (dark_scale, dark_scale, dark_scale, 1.0)
    cr.color_ramp.elements[1].position = 0.5
    cr.color_ramp.elements[1].color = (gray_scale, gray_scale, gray_scale, 1.0)
    cr.color_ramp.elements[2].position = 1.0
    cr.color_ramp.elements[2].color = (*rgb, 1.0)

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=float(roughness))
    nt.links.new(cr.outputs["Color"], bsdf.inputs["Base Color"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


# ----------------------------------------------------------------------------
# (used for the screw-head instances via material_assignments.metals)
# ----------------------------------------------------------------------------
def make_metal_basic(name="MetalBasic", base_color_hsv=None) -> bpy.types.Material:
    """Port of metal/metal_basic.py:shader_metal."""

    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = float(np.random.uniform(10, 25))
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    fc = _build_float_curve(nt, _noise_fac_output(noise),
                            [(0.0, float(np.random.uniform(0.0, 0.2))),
                             (1.0, float(np.random.uniform(0.4, 0.7)))])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf, Metallic=1.0,
        **{"Specular IOR Level": float(np.random.uniform(0.5, 1.0)),
           "Base Color": hsv2rgba(base_color_hsv)},
    )
    nt.links.new(fc.outputs["Value"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat


def make_brushed_metal(name="BrushedMetal", base_color_hsv=None) -> bpy.types.Material:
    """Port of metal/brushed_metal.py:shader_brushed_metal."""

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
    if "Detail" in noise2.inputs:    noise2.inputs["Detail"].default_value = 15.0
    if "Roughness" in noise2.inputs: noise2.inputs["Roughness"].default_value = 0.4
    if "Distortion" in noise2.inputs:noise2.inputs["Distortion"].default_value = 0.1
    if "W" in noise2.inputs:         noise2.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
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
    """Port of metal/galvanized_metal.py:shader_galvanized_metal."""

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
    """Port of metal/grained_and_polished_metal.py:shader_grained_metal."""

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
    """Port of metal/hammered_metal.py:shader_hammered_metal."""

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
        **{"Specular IOR Level": 0.0, "Base Color": hsv2rgba(base_color_hsv),
           "Roughness": 0.1},
    )
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


def make_brushed_black_metal(name="BrushedBlackMetal") -> bpy.types.Material:
    """Port of metal/appliance.py:shader_brushed_black_metal.

    Original uses ShaderNodeBsdfAnisotropic. We route through a Principled BSDF
    with near-black base color, metallic 1.0, and zero specular — this gives
    the same dark brushed look while using the canonical BSDF.
    """

    mat = _new_material(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf, Metallic=1.0,
        **{"Base Color": (0.0167, 0.0167, 0.0167, 1.0),
           "Roughness": 0.25,
           "Specular IOR Level": 0.0},
    )
    _connect_output(nt, bsdf)
    return mat


# ----------------------------------------------------------------------------
METALS_REGISTRY = [
    (make_metal_basic,        3.0),
    (make_brushed_metal,      2.0),
    (make_galvanized_metal,   1.0),
    (make_grained_metal,      1.0),
    (make_hammered_metal,     0.7),
    (make_brushed_black_metal, 0.3),
]


# wood_material key probabilities
WOOD_KEYS = ["black_wood", "white", "wood"]
WOOD_PROBS = [0.3, 0.2, 0.5]


def make_shelves_wood_from_key(key: str, name: str = None) -> bpy.types.Material:
    """Dispatch on the wood_material key exactly as cell_shelf.get_material_func."""

    if key == "black_wood":
        return make_shelves_black_wood(name or "ShelvesBlackWood")
    if key == "white":
        return make_shelves_white(name or "ShelvesWhite")
    if key == "wood":
        return make_shelves_wood(name or "ShelvesWood")
    raise NotImplementedError(f"unknown wood key: {key!r}")


def get_metal_material(name: str = "Metal") -> bpy.types.Material:
    ctor = weighted_sample_mat(METALS_REGISTRY)
    return ctor(name=name)


# ---------------------------------------------------------------------------
# Geometry (SetMaterial nodes added for wood + screw metal slots)
# ---------------------------------------------------------------------------

@contextmanager
def FixedSeed(seed):
    py_st, np_st = random.getstate(), np.random.get_state()
    random.seed(int(seed)); np.random.seed(int(seed))
    try: yield
    finally: random.setstate(py_st); np.random.set_state(np_st)

def to_nodegroup(name):
    def reg(fn):
        def init(*a, **k):
            ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
            fn(NodeWrangler(ng), *a, **k)
            return ng
        return init
    return reg

def _infer_output_socket(item):
    if isinstance(item, bpy.types.NodeSocket): return item
    if outputs := getattr(item, 'outputs', None):
        return next((s for s in outputs if getattr(s, 'enabled', True)), outputs[0])

class NodeWrangler:
    def __init__(self, ng):
        self.node_group = ng.node_group if isinstance(ng, bpy.types.NodesModifier) else ng
        self.nodes, self.links = self.node_group.nodes, self.node_group.links

    def expose_input(self, name, val=None, dtype=None):
        gi = next((n for n in self.nodes if n.bl_idname == 'NodeGroupInput'), None) or self.nodes.new('NodeGroupInput')
        inames = [s.name for s in self.node_group.interface.items_tree if s.in_out == 'INPUT']
        if name not in inames:
            self.node_group.interface.new_socket(name=name, in_out='INPUT', socket_type=dtype or 'NodeSocketFloat')
            inames.append(name)
        try: return gi.outputs[name]
        except: return gi.outputs[inames.index(name)]

    def val(self, v):
        n = self.nodes.new('ShaderNodeValue'); n.outputs[0].default_value = float(v); return n

    def new_node(self, node_type, input_args=None, attrs=None, input_kwargs=None, label=None, expose_input=None):
        if expose_input:
            for spec in expose_input:
                dtype, name, val = spec if len(spec) == 3 else (None, spec[0], spec[1] if len(spec) > 1 else None)
                self.expose_input(name, val=val, dtype=dtype)
        if node_type in bpy.data.node_groups:
            n = self.nodes.new('GeometryNodeGroup'); n.node_tree = bpy.data.node_groups[node_type]
        else:
            n = self.nodes.new(node_type)
        if label: n.label = label
        if attrs:
            for k, v in attrs.items():
                try: setattr(n, k, v)
                except: pass
        def connect(sock, item):
            if isinstance(item, list):
                for sub in item:
                    out = _infer_output_socket(sub)
                    if out is not None:
                        try: self.links.new(out, sock)
                        except: pass
                return
            out = _infer_output_socket(item)
            if out is not None:
                try: self.links.new(out, sock)
                except: pass
            else:
                try: sock.default_value = item
                except:
                    try: sock.default_value = tuple(item)
                    except: pass
        if input_args:
            for i, item in enumerate(input_args):
                if i < len(n.inputs): connect(n.inputs[i], item)
        if input_kwargs:
            is_go = (n.bl_idname == 'NodeGroupOutput')
            for k, item in input_kwargs.items():
                if is_go and k not in [s.name for s in n.inputs]:
                    out_s = _infer_output_socket(item)
                    st = out_s.bl_idname if out_s else 'NodeSocketFloat'
                    st = {'NodeSocketFloatUnsigned': 'NodeSocketFloat', 'NodeSocketVirtual': 'NodeSocketFloat'}.get(st, st)
                    try: self.node_group.interface.new_socket(name=k, in_out='OUTPUT', socket_type=st)
                    except: pass
                try: connect(n.inputs[k], item)
                except:
                    try:
                        idx = [s.name for s in n.inputs].index(k)
                        connect(n.inputs[idx], item)
                    except: pass
        return n

def make_geo_object(geo_func, kwargs):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
    obj = bpy.context.active_object
    ng = bpy.data.node_groups.new('GeoNodes', 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    geo_func(NodeWrangler(ng), **kwargs)
    mod = obj.modifiers.new('GeoNodes', 'NODES')
    mod.node_group = ng
    for o in bpy.context.selected_objects: o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj

class Nodes:
    CombineXYZ    = 'ShaderNodeCombineXYZ'
    GroupInput    = 'NodeGroupInput'
    GroupOutput   = 'NodeGroupOutput'
    JoinGeometry  = 'GeometryNodeJoinGeometry'
    Math          = 'ShaderNodeMath'
    MeshCube      = 'GeometryNodeMeshCube'
    RealizeInstances = 'GeometryNodeRealizeInstances'
    SetMaterial   = 'GeometryNodeSetMaterial'
    Transform     = 'GeometryNodeTransform'

@to_nodegroup("nodegroup_tagged_cube")
def nodegroup_tagged_cube(nw):
    gi = nw.new_node(Nodes.GroupInput, expose_input=[('NodeSocketVector', 'Size', (1.0, 1.0, 1.0))])
    cube = nw.new_node(Nodes.MeshCube, input_kwargs={'Size': gi.outputs['Size']})
    nw.new_node(Nodes.GroupOutput, input_kwargs={'Geometry': cube})

@to_nodegroup("nodegroup_screw_head")
def nodegroup_screw_head(nw):
    cyl = nw.new_node("GeometryNodeMeshCylinder", input_kwargs={"Radius": 0.005, "Depth": 0.001})
    gi = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "Z", 0.5), ("NodeSocketFloat", "leg", 0.5),
        ("NodeSocketFloat", "X", 0.5), ("NodeSocketFloat", "external", 0.5),
        ("NodeSocketFloat", "depth", 0.5),
    ])
    ext = gi.outputs["external"]
    sub  = nw.new_node(Nodes.Math, input_kwargs={0: gi.outputs["X"], 1: ext}, attrs={"operation": "SUBTRACT"})
    mul  = nw.new_node(Nodes.Math, input_kwargs={0: sub}, attrs={"operation": "MULTIPLY"})       # (X-ext)*0.5
    mul1 = nw.new_node(Nodes.Math, input_kwargs={0: ext}, attrs={"operation": "MULTIPLY"})       # ext*0.5
    add1 = nw.new_node(Nodes.Math, input_kwargs={0: gi.outputs["Z"], 1: gi.outputs["leg"]})
    mul2 = nw.new_node(Nodes.Math, input_kwargs={0: ext, 1: 2.0}, attrs={"operation": "MULTIPLY"})
    add2 = nw.new_node(Nodes.Math, input_kwargs={0: add1, 1: mul2})
    sub1 = nw.new_node(Nodes.Math, input_kwargs={0: gi.outputs["depth"], 1: mul1}, attrs={"operation": "SUBTRACT"})
    mul3 = nw.new_node(Nodes.Math, input_kwargs={0: mul, 1: -1.0}, attrs={"operation": "MULTIPLY"})
    for px, py in [(mul, mul1), (mul, sub1), (mul3, sub1), (mul3, mul1)]:
        xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": px, "Y": py, "Z": add2})
        nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cyl.outputs["Mesh"], "Translation": xyz})
    geo = [n for n in nw.nodes if n.bl_idname == Nodes.Transform]
    join = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": geo})
    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": join}, attrs={"is_active_output": True})

@to_nodegroup("nodegroup_base_frame")
def nodegroup_base_frame(nw):
    gi = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "leg_height", 0.5), ("NodeSocketFloat", "leg_size", 0.5),
        ("NodeSocketFloat", "depth", 0.5), ("NodeSocketFloat", "bottom_x", 0.5),
    ])
    ls, lh, bx, dp = gi.outputs["leg_size"], gi.outputs["leg_height"], gi.outputs["bottom_x"], gi.outputs["depth"]
    xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": ls, "Y": ls, "Z": lh})
    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": xyz, "Vertices X": 5, "Vertices Y": 5, "Vertices Z": 5})
    mul  = nw.new_node(Nodes.Math, input_kwargs={0: bx}, attrs={"operation": "MULTIPLY"})
    mul1 = nw.new_node(Nodes.Math, input_kwargs={0: ls}, attrs={"operation": "MULTIPLY"})
    mul2 = nw.new_node(Nodes.Math, input_kwargs={0: lh}, attrs={"operation": "MULTIPLY"})
    sub  = nw.new_node(Nodes.Math, input_kwargs={0: mul, 1: mul1}, attrs={"operation": "SUBTRACT"})
    sneg = nw.new_node(Nodes.Math, input_kwargs={0: sub, 1: -1.0}, attrs={"operation": "MULTIPLY"})
    sub1 = nw.new_node(Nodes.Math, input_kwargs={0: dp, 1: mul1}, attrs={"operation": "SUBTRACT"})
    legs = []
    for px, py in [(sub, mul1), (sneg, mul1), (sub, sub1), (sneg, sub1)]:
        xyz_l = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": px, "Y": py, "Z": mul2})
        legs.append(nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube, "Translation": xyz_l}))
    mul4 = nw.new_node(Nodes.Math, input_kwargs={0: ls, 1: 2.0}, attrs={"operation": "MULTIPLY"})
    sub2 = nw.new_node(Nodes.Math, input_kwargs={0: bx, 1: mul4}, attrs={"operation": "SUBTRACT"})
    xyz5 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": sub2, "Y": ls, "Z": ls})
    cube1 = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": xyz5, "Vertices X": 5, "Vertices Y": 5, "Vertices Z": 5})
    sub3 = nw.new_node(Nodes.Math, input_kwargs={0: lh, 1: mul1}, attrs={"operation": "SUBTRACT"})
    for py in [mul1, sub1]:
        xyz_c = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Y": py, "Z": sub3})
        legs.append(nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube1, "Translation": xyz_c}))
    sub5 = nw.new_node(Nodes.Math, input_kwargs={0: dp, 1: mul4}, attrs={"operation": "SUBTRACT"})
    xyz8 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": ls, "Y": sub5, "Z": ls})
    cube2 = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": xyz8, "Vertices X": 5, "Vertices Y": 5, "Vertices Z": 5})
    sub6 = nw.new_node(Nodes.Math, input_kwargs={0: bx, 1: ls}, attrs={"operation": "SUBTRACT"})
    mul5 = nw.new_node(Nodes.Math, input_kwargs={0: sub6}, attrs={"operation": "MULTIPLY"})
    mul6 = nw.new_node(Nodes.Math, input_kwargs={0: sub5}, attrs={"operation": "MULTIPLY"})
    add6 = nw.new_node(Nodes.Math, input_kwargs={0: mul6, 1: ls})
    m5n  = nw.new_node(Nodes.Math, input_kwargs={0: mul5, 1: -1.0}, attrs={"operation": "MULTIPLY"})
    for px in [mul5, m5n]:
        xyz_s = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": px, "Y": add6, "Z": sub3})
        legs.append(nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube2, "Translation": xyz_s}))
    join = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": legs})
    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": join}, attrs={"is_active_output": True})

@to_nodegroup("nodegroup_back_board")
def nodegroup_back_board(nw):
    gi = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "X", 0.0), ("NodeSocketFloat", "Z", 0.5),
        ("NodeSocketFloat", "leg", 0.5), ("NodeSocketFloat", "external", 0.5),
    ])
    xyz = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": gi.outputs["X"], "Y": 0.01, "Z": gi.outputs["Z"]})
    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": xyz, "Vertices X": 5, "Vertices Y": 5, "Vertices Z": 5})
    mul  = nw.new_node(Nodes.Math, input_kwargs={0: gi.outputs["Z"]}, attrs={"operation": "MULTIPLY"})
    add1 = nw.new_node(Nodes.Math, input_kwargs={0: mul, 1: gi.outputs["leg"]})
    add2 = nw.new_node(Nodes.Math, input_kwargs={0: add1, 1: gi.outputs["external"]})
    xyz5 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Z": add2})
    t6   = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube, "Translation": xyz5})
    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": t6}, attrs={"is_active_output": True})

@to_nodegroup("nodegroup_attach_gadget")
def nodegroup_attach_gadget(nw):
    gi = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "z", 0.5), ("NodeSocketFloat", "base_leg", 0.5),
        ("NodeSocketFloat", "x", 0.5), ("NodeSocketFloat", "thickness", 0.5),
        ("NodeSocketFloat", "size", 0.5),
    ])
    sz   = gi.outputs["size"]
    xyz  = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": sz, "Y": 0.001, "Z": sz})
    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": xyz})
    mul  = nw.new_node(Nodes.Math, input_kwargs={0: gi.outputs["x"]}, attrs={"operation": "MULTIPLY"})
    sub  = nw.new_node(Nodes.Math, input_kwargs={0: mul, 1: gi.outputs["thickness"]}, attrs={"operation": "SUBTRACT"})
    mul1 = nw.new_node(Nodes.Math, input_kwargs={0: sz}, attrs={"operation": "MULTIPLY"})
    sub1 = nw.new_node(Nodes.Math, input_kwargs={0: sub, 1: mul1}, attrs={"operation": "SUBTRACT"})
    mul2 = nw.new_node(Nodes.Math, input_kwargs={0: sub1, 1: -1.0}, attrs={"operation": "MULTIPLY"})
    add1 = nw.new_node(Nodes.Math, input_kwargs={0: gi.outputs["base_leg"], 1: gi.outputs["z"]})
    add2 = nw.new_node(Nodes.Math, input_kwargs={0: add1, 1: gi.outputs["thickness"]})
    add3 = nw.new_node(Nodes.Math, input_kwargs={0: add2, 1: -0.02})
    sub2 = nw.new_node(Nodes.Math, input_kwargs={0: add3, 1: mul1}, attrs={"operation": "SUBTRACT"})
    for px in [mul2, sub1]:
        xyz_g = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": px, "Z": sub2})
        nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube, "Translation": xyz_g})
    geo = [n for n in nw.nodes if n.bl_idname == Nodes.Transform]
    join = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": geo})
    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": join}, attrs={"is_active_output": True})

@to_nodegroup("nodegroup_h_division_placement")
def nodegroup_h_division_placement(nw):
    gi = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "depth", 0.5), ("NodeSocketFloat", "cell_size", 0.5),
        ("NodeSocketFloat", "leg_height", 0.5), ("NodeSocketFloat", "division_board_thickness", 0.5),
        ("NodeSocketFloat", "external_board_thickness", 0.5), ("NodeSocketFloat", "index", 0.5),
    ])
    ext  = gi.outputs["external_board_thickness"]
    idx  = gi.outputs["index"]
    mul  = nw.new_node(Nodes.Math, input_kwargs={0: gi.outputs["depth"]}, attrs={"operation": "MULTIPLY"})
    mul1 = nw.new_node(Nodes.Math, input_kwargs={0: idx, 1: gi.outputs["cell_size"]}, attrs={"operation": "MULTIPLY"})
    add1 = nw.new_node(Nodes.Math, input_kwargs={0: idx, 1: -1.0})
    mul2 = nw.new_node(Nodes.Math, input_kwargs={0: add1, 1: ext}, attrs={"operation": "MULTIPLY"})
    add3 = nw.new_node(Nodes.Math, input_kwargs={0: mul1, 1: mul2})
    add4 = nw.new_node(Nodes.Math, input_kwargs={0: gi.outputs["division_board_thickness"], 1: gi.outputs["leg_height"]})
    mul3 = nw.new_node(Nodes.Math, input_kwargs={0: ext}, attrs={"operation": "MULTIPLY"})
    add5 = nw.new_node(Nodes.Math, input_kwargs={0: add4, 1: mul3})
    add6 = nw.new_node(Nodes.Math, input_kwargs={0: add3, 1: add5})
    xyz  = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Y": mul, "Z": add6})
    nw.new_node(Nodes.GroupOutput, input_kwargs={"Vector": xyz}, attrs={"is_active_output": True})

@to_nodegroup("nodegroup_h_division_board")
def nodegroup_h_division_board(nw, tag_support=False):
    gi = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "cell_size", 0.5), ("NodeSocketFloat", "horizontal_cell_num", 0.5),
        ("NodeSocketFloat", "division_board_thickness", 0.5), ("NodeSocketFloat", "depth", 0.0),
    ])
    hn   = gi.outputs["horizontal_cell_num"]
    mul  = nw.new_node(Nodes.Math, input_kwargs={0: hn, 1: gi.outputs["cell_size"]}, attrs={"operation": "MULTIPLY"})
    add1 = nw.new_node(Nodes.Math, input_kwargs={0: hn, 1: -1.0})
    mul1 = nw.new_node(Nodes.Math, input_kwargs={0: add1, 1: gi.outputs["division_board_thickness"]}, attrs={"operation": "MULTIPLY"})
    add2 = nw.new_node(Nodes.Math, input_kwargs={0: mul, 1: mul1})
    xyz  = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": add2, "Y": gi.outputs["depth"], "Z": gi.outputs["division_board_thickness"]})
    if tag_support:
        cube = nw.new_node(nodegroup_tagged_cube().name, input_kwargs={"Size": xyz})
    else:
        cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": xyz, "Vertices X": 5, "Vertices Y": 5, "Vertices Z": 5})
    nw.new_node(Nodes.GroupOutput, input_kwargs={"Mesh": cube}, attrs={"is_active_output": True})

@to_nodegroup("nodegroup_v_division_board_placement")
def nodegroup_v_division_board_placement(nw):
    gi = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "depth", 0.5), ("NodeSocketFloat", "base_leg", 0.5),
        ("NodeSocketFloat", "external_thickness", 0.5), ("NodeSocketFloat", "side_z", 0.5),
        ("NodeSocketFloat", "index", 0.5), ("NodeSocketFloat", "h_cell_num", 0.5),
        ("NodeSocketFloat", "division_thickness", 0.5), ("NodeSocketFloat", "cell_size", 0.5),
    ])
    hn   = gi.outputs["h_cell_num"]
    idx  = gi.outputs["index"]
    add1 = nw.new_node(Nodes.Math, input_kwargs={0: hn, 1: -1.0})
    mul  = nw.new_node(Nodes.Math, input_kwargs={1: add1}, attrs={"operation": "MULTIPLY"})
    sub  = nw.new_node(Nodes.Math, input_kwargs={0: mul, 1: idx}, attrs={"operation": "SUBTRACT"})
    add3 = nw.new_node(Nodes.Math, input_kwargs={0: sub})
    mul1 = nw.new_node(Nodes.Math, input_kwargs={0: add3, 1: gi.outputs["division_thickness"]}, attrs={"operation": "MULTIPLY"})
    mul2 = nw.new_node(Nodes.Math, input_kwargs={0: hn}, attrs={"operation": "MULTIPLY"})
    sub1 = nw.new_node(Nodes.Math, input_kwargs={0: mul2, 1: idx}, attrs={"operation": "SUBTRACT"})
    mul3 = nw.new_node(Nodes.Math, input_kwargs={0: gi.outputs["cell_size"], 1: sub1}, attrs={"operation": "MULTIPLY"})
    add4 = nw.new_node(Nodes.Math, input_kwargs={0: mul1, 1: mul3})
    mul4 = nw.new_node(Nodes.Math, input_kwargs={0: gi.outputs["depth"]}, attrs={"operation": "MULTIPLY"})
    add5 = nw.new_node(Nodes.Math, input_kwargs={0: gi.outputs["base_leg"], 1: gi.outputs["external_thickness"]})
    mul5 = nw.new_node(Nodes.Math, input_kwargs={0: gi.outputs["side_z"]}, attrs={"operation": "MULTIPLY"})
    add6 = nw.new_node(Nodes.Math, input_kwargs={0: add5, 1: mul5})
    xyz  = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": add4, "Y": mul4, "Z": add6})
    nw.new_node(Nodes.GroupOutput, input_kwargs={"Vector": xyz}, attrs={"is_active_output": True})

@to_nodegroup("nodegroup_v_division_board")
def nodegroup_v_division_board(nw):
    gi = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "division_board_thickness", 0.0), ("NodeSocketFloat", "depth", 0.0),
        ("NodeSocketFloat", "cell_size", 0.5), ("NodeSocketFloat", "vertical_cell_num", 0.5),
    ])
    vn   = gi.outputs["vertical_cell_num"]
    mul  = nw.new_node(Nodes.Math, input_kwargs={0: gi.outputs["cell_size"], 1: vn}, attrs={"operation": "MULTIPLY"})
    sub  = nw.new_node(Nodes.Math, input_kwargs={0: vn, 1: 1.0}, attrs={"operation": "SUBTRACT"})
    mul1 = nw.new_node(Nodes.Math, input_kwargs={0: sub, 1: gi.outputs["division_board_thickness"]}, attrs={"operation": "MULTIPLY"})
    add1 = nw.new_node(Nodes.Math, input_kwargs={0: mul, 1: mul1})
    d001 = nw.new_node(Nodes.Math, input_kwargs={0: gi.outputs["depth"], 1: -0.001})
    xyz  = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": gi.outputs["division_board_thickness"], "Y": d001, "Z": add1})
    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": xyz, "Vertices X": 5, "Vertices Y": 5, "Vertices Z": 5})
    nw.new_node(Nodes.GroupOutput, input_kwargs={"Mesh": cube, "Value": add1}, attrs={"is_active_output": True})

@to_nodegroup("nodegroup_top_bottom_board")
def nodegroup_top_bottom_board(nw, tag_support=False):
    gi = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "base_leg_height", 0.5), ("NodeSocketFloat", "horizontal_cell_num", 0.5),
        ("NodeSocketFloat", "vertical_cell_num", 0.5), ("NodeSocketFloat", "cell_size", 0.5),
        ("NodeSocketFloat", "depth", 0.5), ("NodeSocketFloat", "division_board_thickness", 0.5),
        ("NodeSocketFloat", "external_board_thickness", 0.5),
    ])
    ext = gi.outputs["external_board_thickness"]
    div = gi.outputs["division_board_thickness"]
    hn  = gi.outputs["horizontal_cell_num"]
    vn  = gi.outputs["vertical_cell_num"]
    cs  = gi.outputs["cell_size"]
    dp  = gi.outputs["depth"]
    blh = gi.outputs["base_leg_height"]
    mul  = nw.new_node(Nodes.Math, input_kwargs={0: ext, 1: 2.0}, attrs={"operation": "MULTIPLY"})
    add3 = nw.new_node(Nodes.Math, input_kwargs={0: hn, 1: -1.0})
    mul1 = nw.new_node(Nodes.Math, input_kwargs={0: div, 1: add3}, attrs={"operation": "MULTIPLY"})
    add4 = nw.new_node(Nodes.Math, input_kwargs={0: mul, 1: mul1})
    mul2 = nw.new_node(Nodes.Math, input_kwargs={0: cs, 1: hn}, attrs={"operation": "MULTIPLY"})
    add6 = nw.new_node(Nodes.Math, input_kwargs={0: add4, 1: mul2})
    add7 = nw.new_node(Nodes.Math, input_kwargs={0: add6, 1: 0.002})
    xyz3 = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": add7, "Y": dp, "Z": ext})
    if tag_support:
        cube1 = nw.new_node(nodegroup_tagged_cube().name, input_kwargs={"Size": xyz3})
    else:
        cube1 = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": xyz3, "Vertices X": 5, "Vertices Y": 5, "Vertices Z": 5})
    mul3  = nw.new_node(Nodes.Math, input_kwargs={0: dp}, attrs={"operation": "MULTIPLY"})
    mul4  = nw.new_node(Nodes.Math, input_kwargs={0: ext}, attrs={"operation": "MULTIPLY"})
    add10 = nw.new_node(Nodes.Math, input_kwargs={0: mul4, 1: blh})
    xyz_b = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Y": mul3, "Z": add10})
    t2    = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube1, "Translation": xyz_b})
    add11 = nw.new_node(Nodes.Math, input_kwargs={0: add10, 1: ext})
    mul5  = nw.new_node(Nodes.Math, input_kwargs={0: vn, 1: cs}, attrs={"operation": "MULTIPLY"})
    add13 = nw.new_node(Nodes.Math, input_kwargs={0: add11, 1: mul5})
    add14 = nw.new_node(Nodes.Math, input_kwargs={0: vn, 1: -1.0})
    mul6  = nw.new_node(Nodes.Math, input_kwargs={0: div, 1: add14}, attrs={"operation": "MULTIPLY"})
    add15 = nw.new_node(Nodes.Math, input_kwargs={0: add13, 1: mul6})
    xyz_t = nw.new_node(Nodes.CombineXYZ, input_kwargs={"Y": mul3, "Z": add15})
    t     = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube1, "Translation": xyz_t})
    join  = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": [t2, t]})
    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": join, "x": add7}, attrs={"is_active_output": True})

@to_nodegroup("nodegroup_side_board")
def nodegroup_side_board(nw):
    gi = nw.new_node(Nodes.GroupInput, expose_input=[
        ("NodeSocketFloat", "base_leg_height", 0.5), ("NodeSocketFloat", "horizontal_cell_num", 0.5),
        ("NodeSocketFloat", "vertical_cell_num", 0.5), ("NodeSocketFloat", "cell_size", 0.5),
        ("NodeSocketFloat", "depth", 0.5), ("NodeSocketFloat", "division_thickness", 0.5),
        ("NodeSocketFloat", "external_thickness", 0.5),
    ])
    ext = gi.outputs["external_thickness"]
    dp  = gi.outputs["depth"]
    vn  = gi.outputs["vertical_cell_num"]
    div = gi.outputs["division_thickness"]
    cs  = gi.outputs["cell_size"]
    hn  = gi.outputs["horizontal_cell_num"]
    blh = gi.outputs["base_leg_height"]
    sub  = nw.new_node(Nodes.Math, input_kwargs={0: vn, 1: 1.0}, attrs={"operation": "SUBTRACT"})
    mul  = nw.new_node(Nodes.Math, input_kwargs={0: sub, 1: div}, attrs={"operation": "MULTIPLY"})
    mul1 = nw.new_node(Nodes.Math, input_kwargs={0: vn, 1: cs}, attrs={"operation": "MULTIPLY"})
    add5 = nw.new_node(Nodes.Math, input_kwargs={0: mul, 1: mul1})
    xyz  = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": ext, "Y": dp, "Z": add5})
    cube = nw.new_node(Nodes.MeshCube, input_kwargs={"Size": xyz, "Vertices X": 5, "Vertices Y": 5, "Vertices Z": 5})
    mul2 = nw.new_node(Nodes.Math, input_kwargs={0: cs, 1: hn}, attrs={"operation": "MULTIPLY"})
    sub1 = nw.new_node(Nodes.Math, input_kwargs={0: hn, 1: 1.0}, attrs={"operation": "SUBTRACT"})
    mul3 = nw.new_node(Nodes.Math, input_kwargs={0: div, 1: sub1}, attrs={"operation": "MULTIPLY"})
    add6 = nw.new_node(Nodes.Math, input_kwargs={0: ext, 1: mul3})
    add7 = nw.new_node(Nodes.Math, input_kwargs={0: mul2, 1: add6})
    mul4 = nw.new_node(Nodes.Math, input_kwargs={1: add7}, attrs={"operation": "MULTIPLY"})
    mul5 = nw.new_node(Nodes.Math, input_kwargs={0: dp}, attrs={"operation": "MULTIPLY"})
    mul6 = nw.new_node(Nodes.Math, input_kwargs={0: add5}, attrs={"operation": "MULTIPLY"})
    add8 = nw.new_node(Nodes.Math, input_kwargs={0: mul6, 1: blh})
    add9 = nw.new_node(Nodes.Math, input_kwargs={0: ext, 1: add8})
    mul7 = nw.new_node(Nodes.Math, input_kwargs={0: mul4, 1: -1.0}, attrs={"operation": "MULTIPLY"})
    sides = []
    for px in [mul4, mul7]:
        xyz_s = nw.new_node(Nodes.CombineXYZ, input_kwargs={"X": px, "Y": mul5, "Z": add9})
        sides.append(nw.new_node(Nodes.Transform, input_kwargs={"Geometry": cube, "Translation": xyz_s}))
    join = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": sides})
    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": join}, attrs={"is_active_output": True})

def geometry_nodes(nw, **kwargs):
    mat_wood  = kwargs.get("mat_wood", None)
    mat_screw = kwargs.get("mat_screw", None)

    blh = nw.val(kwargs["base_leg_height"])
    hn  = nw.val(kwargs["horizontal_cell_num"])
    vn  = nw.val(kwargs["vertical_cell_num"])
    cs  = nw.val(kwargs["cell_size"])
    dp  = nw.val(kwargs["depth"])
    div = nw.val(kwargs["division_board_thickness"])
    ext = nw.val(kwargs["external_board_thickness"])

    sideboard = nw.new_node(nodegroup_side_board().name, input_kwargs={
        "base_leg_height": blh, "horizontal_cell_num": hn, "vertical_cell_num": vn,
        "cell_size": cs, "depth": dp, "division_thickness": div, "external_thickness": ext,
    })
    topbottomboard = nw.new_node(
        nodegroup_top_bottom_board(tag_support=kwargs.get("tag_support", False)).name,
        input_kwargs={
            "base_leg_height": blh, "horizontal_cell_num": hn, "vertical_cell_num": vn,
            "cell_size": cs, "depth": dp, "division_board_thickness": div, "external_board_thickness": ext,
        })
    vdivisionboard = nw.new_node(nodegroup_v_division_board().name, input_kwargs={
        "division_board_thickness": div, "depth": dp, "cell_size": cs, "vertical_cell_num": vn,
    })

    all_components = [sideboard, topbottomboard.outputs["Geometry"]]

    v_division_boards = []
    for i in range(1, kwargs["horizontal_cell_num"]):
        placement = nw.new_node(nodegroup_v_division_board_placement().name, input_kwargs={
            "depth": dp, "base_leg": blh, "external_thickness": ext,
            "side_z": vdivisionboard.outputs["Value"], "index": nw.val(i),
            "h_cell_num": hn, "division_thickness": div, "cell_size": cs,
        })
        v_division_boards.append(nw.new_node(Nodes.Transform, input_kwargs={
            "Geometry": vdivisionboard.outputs["Mesh"], "Translation": placement,
        }))
    if v_division_boards:
        all_components.append(nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": v_division_boards}))

    hdivisionboard = nw.new_node(
        nodegroup_h_division_board(tag_support=kwargs.get("tag_support", False)).name,
        input_kwargs={
            "cell_size": cs, "horizontal_cell_num": hn,
            "division_board_thickness": div, "depth": dp,
        })
    h_division_boards = []
    for j in range(1, kwargs["vertical_cell_num"]):
        placement = nw.new_node(nodegroup_h_division_placement().name, input_kwargs={
            "depth": dp, "cell_size": cs, "leg_height": blh,
            "division_board_thickness": ext, "external_board_thickness": div, "index": nw.val(j),
        })
        h_division_boards.append(nw.new_node(Nodes.Transform, input_kwargs={
            "Geometry": hdivisionboard, "Translation": placement,
        }))
    if h_division_boards:
        all_components.append(nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": h_division_boards}))

    if kwargs["has_backboard"]:
        all_components.append(nw.new_node(nodegroup_back_board().name, input_kwargs={
            "X": topbottomboard.outputs["x"], "Z": vdivisionboard.outputs["Value"],
            "leg": blh, "external": ext,
        }))
    else:
        all_components.append(nw.new_node(nodegroup_attach_gadget().name, input_kwargs={
            "z": vdivisionboard.outputs["Value"], "base_leg": blh,
            "x": topbottomboard.outputs["x"], "thickness": ext,
            "size": nw.val(kwargs["attachment_size"]),
        }))

    join4    = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": all_components})
    realize  = nw.new_node(Nodes.RealizeInstances, input_kwargs={"Geometry": join4})
    # === Assign wood material to everything before the screws are joined ===
    if mat_wood is not None:
        wood_set = nw.new_node(Nodes.SetMaterial,
                               input_kwargs={"Geometry": realize, "Material": mat_wood})
    else:
        wood_set = realize
    merge_components = [wood_set]

    if kwargs["has_base_frame"]:
        baseframe = nw.new_node(nodegroup_base_frame().name, input_kwargs={
            "leg_height": blh, "leg_size": nw.val(kwargs["base_leg_size"]),
            "depth": dp, "bottom_x": topbottomboard.outputs["x"],
        })
        base_real = nw.new_node(Nodes.RealizeInstances, input_kwargs={"Geometry": baseframe})
        if mat_screw is not None:
            base_real = nw.new_node(Nodes.SetMaterial,
                                    input_kwargs={"Geometry": base_real, "Material": mat_screw})
        merge_components.append(base_real)

    screwhead = nw.new_node(nodegroup_screw_head().name, input_kwargs={
        "Z": vdivisionboard.outputs["Value"], "leg": blh,
        "X": topbottomboard.outputs["x"], "external": ext, "depth": dp,
    })
    screw_real = nw.new_node(Nodes.RealizeInstances, input_kwargs={"Geometry": screwhead})
    if mat_screw is not None:
        screw_real = nw.new_node(Nodes.SetMaterial,
                                 input_kwargs={"Geometry": screw_real, "Material": mat_screw})
    merge_components.append(screw_real)

    join2      = nw.new_node(Nodes.JoinGeometry, input_kwargs={"Geometry": merge_components})
    triangulate = nw.new_node("GeometryNodeTriangulate", input_kwargs={"Mesh": join2})
    transform   = nw.new_node(Nodes.Transform, input_kwargs={"Geometry": triangulate, "Rotation": (0.0, 0.0, -1.5708)})
    nw.new_node(Nodes.GroupOutput, input_kwargs={"Geometry": transform}, attrs={"is_active_output": True})

class CellShelfBaseFactory:
    def __init__(self, factory_seed, coarse=False):
        self.factory_seed = int(factory_seed)
        with FixedSeed(factory_seed):
            self.params = self.sample_params()
            self.params = self.get_asset_params(self.params)

    def get_asset_params(self, params):
        if params is None: params = {}
        if params.get("depth") is None:
            params["depth"] = np.clip(np.random.normal(0.39, 0.05), 0.29, 0.49)
        if params.get("cell_size") is None:
            params["cell_size"] = np.clip(np.random.normal(0.335, 0.03), 0.26, 0.40)
        if params.get("vertical_cell_num") is None:
            params["vertical_cell_num"] = np.random.randint(1, 7)
        if params.get("horizontal_cell_num") is None:
            params["horizontal_cell_num"] = np.random.randint(1, 7)
        if params.get("division_board_thickness") is None:
            params["division_board_thickness"] = np.clip(np.random.normal(0.015, 0.005), 0.008, 0.022)
        if params.get("external_board_thickness") is None:
            params["external_board_thickness"] = np.clip(np.random.normal(0.04, 0.005), 0.028, 0.052)
        if params.get("has_backboard") is None:
            params["has_backboard"] = False
        if params.get("has_base_frame") is None:
            params["has_base_frame"] = np.random.choice([True, False], p=[0.4, 0.6])
        if params["has_base_frame"]:
            if params.get("base_leg_height") is None:
                params["base_leg_height"] = np.clip(np.random.normal(0.174, 0.03), 0.1, 0.25)
            if params.get("base_leg_size") is None:
                params["base_leg_size"] = np.clip(np.random.normal(0.035, 0.007), 0.02, 0.05)
            if params.get("base_material") is None:
                params["base_material"] = np.random.choice(["black", "white"], p=[0.4, 0.6])
        else:
            params["base_leg_height"] = 0.0
            params["base_leg_size"] = 0.0
            params["base_material"] = "white"
        if params.get("attachment_size") is None:
            params["attachment_size"] = np.clip(np.random.normal(0.05, 0.02), 0.02, 0.1)
        if params.get("wood_material") is None:
            params["wood_material"] = np.random.choice(["black_wood", "white", "wood"], p=[0.3, 0.2, 0.5])
        params["tag_support"] = True
        # Phase-1 materials injected in build(); placeholders here
        params["wood_material"] = None
        params["base_material"] = None
        return params

    def sample_params(self):
        return {}

    def create_asset(self, i=0, mat_wood=None, mat_screw=None, **kwargs):
        call_kwargs = dict(self.params)
        call_kwargs["mat_wood"] = mat_wood
        call_kwargs["mat_screw"] = mat_screw
        return make_geo_object(geometry_nodes, call_kwargs)

class CellShelfFactory(CellShelfBaseFactory):
    def sample_params(self):
        params = {}
        params["Dimensions"] = (
            np.random.uniform(0.3, 0.45),
            np.random.uniform(2 * 0.35, 6 * 0.35),
            np.random.uniform(1 * 0.35, 6 * 0.35),
        )
        h_cell_num = int(params["Dimensions"][1] / 0.35)
        params["cell_size"] = params["Dimensions"][1] / h_cell_num
        params["horizontal_cell_num"] = h_cell_num
        params["vertical_cell_num"] = max(int(params["Dimensions"][2] / params["cell_size"]), 1)
        params["depth"] = params["Dimensions"][0]
        params["has_base_frame"] = False
        params["Dimensions"] = list(params["Dimensions"])
        params["Dimensions"][2] = params["vertical_cell_num"] * params["cell_size"]
        return params


# Phase 1: material on raw SEED; Phase 2: geometry on AssetFactory default (no int_hash)
SEED = int(os.environ.get("SEED", 0))
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)
for ng in list(bpy.data.node_groups):
    bpy.data.node_groups.remove(ng)
bpy.context.scene.cursor.location = (0, 0, 0)


seed_all(SEED)
_ = np.random.uniform(0.3, 0.45)
_ = np.random.uniform(2 * 0.35, 6 * 0.35)
_ = np.random.uniform(1 * 0.35, 6 * 0.35)
_ = np.clip(np.random.normal(0.015, 0.005), 0.008, 0.022)
_ = np.clip(np.random.normal(0.04, 0.005), 0.028, 0.052)
_ = np.clip(np.random.normal(0.05, 0.02), 0.02, 0.1)
_WOOD_KEY = np.random.choice(WOOD_KEYS, p=WOOD_PROBS)
MAT_WOOD = make_shelves_wood_from_key(str(_WOOD_KEY), name="ShelvesBody")

# Screw metal from the 6-way pool; sampled after wood to tie to raw SEED.
MAT_SCREW = get_metal_material(name="ShelvesScrewMetal")


def build(seed=SEED):
    factory = CellShelfFactory(int(seed))
    obj = factory.create_asset(i=0, mat_wood=MAT_WOOD, mat_screw=MAT_SCREW)
    if obj is not None:
        obj.name = "CellShelfFactory"
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        try:
            bpy.ops.object.shade_smooth()
        except RuntimeError:
            pass
        obj.select_set(False)
        obj.data.update()
        fallback = MAT_WOOD if MAT_WOOD is not None else next((mat for mat in obj.data.materials if mat is not None), None)
        if fallback is not None:
            for i in range(len(obj.data.materials)):
                if obj.data.materials[i] is None:
                    obj.data.materials[i] = fallback
    return obj


build(SEED)
