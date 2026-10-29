# [FL_INDEX: keywords="blender_factory, procedural_3d, WindowFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: WindowFactory | Category: factories_geo
# Prompt: A 3D model of a rectangular window rendered from a three-quarter perspective. The window features a solid rectangular frame with one or more vertical panels, each fitted with horizontal slat blinds that can appear fully closed or partially open, and the frame varies in coloring from painted white or cream to a natural wood tone.

"""
Textured WindowFactory — hand-converted from objects_blender/windows/WindowFactory.py

  FrameMaterial        <- weighted_sample(material_assignments.woods)
  CurtainFrameMaterial <- weighted_sample(material_assignments.metals)
  CurtainMaterial      <- weighted_sample(material_assignments.curtain)
  Material (glass)     <- surface.shaderfunc_to_material(shader_window_glass)

Per-part assignment (from nodegroup_window_geometry):
  outer frame, panel dividers, sub-frame dividers, shutter slats -> FrameMaterial
  glass panes                                                    -> Material (window glass)
  curtain rod                                                    -> CurtainFrameMaterial
  curtain panels                                                 -> CurtainMaterial

"""
# SEED-deterministic: all random calls seeded from SEED

import os
import math
import random
import colorsys

import bmesh
import bpy
import numpy as np

# ============================================================================
# Inlined material library — raw bpy port of the shaders needed by WindowFactory
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

def log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def clip_gaussian(mean, std, lo, hi, _clip_at_std=None):
    
    while True:
        v = float(np.random.normal(mean, std))
        if lo <= v <= hi:
            return v

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

def bark_hsv():
    wood_hex = ["#8b5a2b", "#a0522d", "#cd853f", "#d2691e", "#6b4423", "#5d4037", "#7b3f00"]
    h_str = wood_hex[np.random.randint(0, len(wood_hex))].lstrip("#")
    r, g, b = (int(h_str[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return colorsys.rgb_to_hsv(r, g, b)

def weighted_sample(reg):
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
    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Specular": ("Specular IOR Level", "Specular"),
        "Coat Weight": ("Coat Weight", "Clearcoat"),
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

def _connect_output(nt, surface_node, displacement=None, volume=None):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(surface_node.outputs[0], out.inputs["Surface"])
    if displacement is not None:
        nt.links.new(displacement, out.inputs["Displacement"])
    if volume is not None:
        nt.links.new(volume.outputs[0], out.inputs["Volume"])
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

# ------------------------------------------------------------------
# Metals
# ------------------------------------------------------------------
def make_metal_basic(name="MetalBasic") -> bpy.types.Material:
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
                    **{"Specular IOR Level": float(np.random.uniform(0.5, 1.0))},
                    **{"Base Color": hsv2rgba(metal_hsv())})
    nt.links.new(fc.outputs["Value"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

def make_brushed_metal(name="BrushedMetal") -> bpy.types.Material:
    base = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (0.2, 0.2, 5.0)
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])
    noise = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise, "noise_dimensions"):
        try: noise.noise_dimensions = "4D"
        except TypeError: pass
    noise.inputs["Scale"].default_value = 100.0
    if "Detail" in noise.inputs:     noise.inputs["Detail"].default_value = 15.0
    if "Roughness" in noise.inputs:  noise.inputs["Roughness"].default_value = 0.4
    if "Distortion" in noise.inputs: noise.inputs["Distortion"].default_value = 0.1
    if "W" in noise.inputs:          noise.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs[1].default_value = 0.4; mr.inputs[2].default_value = 0.6
    mr.inputs[3].default_value = 0.8; mr.inputs[4].default_value = 1.2
    nt.links.new(_noise_fac_output(noise), mr.inputs[0])
    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_node.inputs["Color"].default_value = hsv2rgba(base)
    nt.links.new(mr.outputs["Result"], hsv_node.inputs["Value"])
    mr_r = nt.nodes.new("ShaderNodeMapRange")
    mr_r.inputs[1].default_value = 0.4; mr_r.inputs[2].default_value = 0.6
    mr_r.inputs[3].default_value = 0.2; mr_r.inputs[4].default_value = 0.3
    nt.links.new(_noise_fac_output(noise), mr_r.inputs[0])
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Metallic=1.0, **{"Specular IOR Level": 0.0})
    nt.links.new(hsv_node.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(mr_r.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

def make_galvanized_metal(name="GalvanizedMetal") -> bpy.types.Material:
    base = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(voronoi, "voronoi_dimensions"):
        try: voronoi.voronoi_dimensions = "4D"
        except TypeError:
            voronoi.voronoi_dimensions = "3D"
    if hasattr(voronoi, "distance"):
        try: voronoi.distance = "MINKOWSKI"
        except TypeError: pass
    voronoi.inputs["Scale"].default_value = 500.0
    if "W" in voronoi.inputs:
        voronoi.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(tex_coord.outputs["Object"], voronoi.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs[3].default_value = 0.1; mr.inputs[4].default_value = 0.5
    nt.links.new(voronoi.outputs[0], mr.inputs[0])
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Metallic=1.0,
                    **{"Specular IOR Level": 0.0, "Base Color": hsv2rgba(base)})
    nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

def make_grained_metal(name="GrainedMetal") -> bpy.types.Material:
    base = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2000.0
    if "Detail" in noise.inputs:     noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs: noise.inputs["Distortion"].default_value = 2.0
    if "W" in noise.inputs:          noise.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs[0].default_value = float(np.random.uniform(0.0, 1.0))
    mr.inputs[3].default_value = 0.05; mr.inputs[4].default_value = 0.25
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Metallic=1.0,
                    **{"Specular IOR Level": 0.0, "Base Color": hsv2rgba(base)})
    nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

def make_hammered_metal(name="HammeredMetal") -> bpy.types.Material:
    base = metal_hsv()
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
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Metallic=1.0, Roughness=0.1,
                    **{"Specular IOR Level": 0.0, "Base Color": hsv2rgba(base)})
    _connect_output(nt, bsdf)
    return mat

def make_brushed_black_metal(name="BrushedBlackMetal") -> bpy.types.Material:
    mat = _new_material(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Metallic=1.0, Roughness=0.4, Anisotropic=0.9,
                    **{"Specular IOR Level": 0.5,
                       "Base Color": (0.0167, 0.0167, 0.0167, 1.0)})
    _connect_output(nt, bsdf)
    return mat

# ------------------------------------------------------------------
# Woods (for frame + curtain Wood option)
# ------------------------------------------------------------------
def make_wood(name="Wood") -> bpy.types.Material:
    """Port of materials/wood/wood.py:shader_wood — simplified because original
    uses MusgraveTexture (removed in Blender 5.0). We substitute multi-octave
    NoiseTexture on a stretched mapping for a visually similar grain pattern."""

    color = hsv2rgba(bark_hsv())
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
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=float(np.random.uniform(0.4, 0.7)),
                    **{"Coat Weight": 0.2})
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    _connect_output(nt, bsdf)
    return mat

def make_white_plywood(name="WhitePlywood") -> bpy.types.Material:
    """Port of materials/wood/plywood.py:shader_shelves_white — flat white wood."""

    v = float(np.random.uniform(0.7, 1.0))
    rgb = [v * (1.0 + float(np.random.normal(0, 0.005))) for _ in range(3)]
    roughness = float(np.random.uniform(0.7, 1.0))
    mat = _new_material(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=roughness,
                    **{"Base Color": (rgb[0], rgb[1], rgb[2], 1.0)})
    _connect_output(nt, bsdf)
    return mat

def _plywood_wavy(nt, wave_scale, dark_scale, gray_scale):
    """Shared dark-wavy-grain mask used by BlackPlywood and BlondePlywood.

    Returns the output socket of a ColorRamp-mix giving a 0..1 grain factor on
    object coordinates, plus the mapping/texture nodes (so callers can reference
    outputs directly).
    """

    tex_coord1 = nt.nodes.new("ShaderNodeTexCoord")
    map1 = nt.nodes.new("ShaderNodeMapping")
    map1.inputs["Scale"].default_value = (0.1, 2.0, 2.0)
    nt.links.new(tex_coord1.outputs["Object"], map1.inputs["Vector"])
    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    noise1.inputs["Scale"].default_value = 100.0
    if "Detail" in noise1.inputs:     noise1.inputs["Detail"].default_value = 10.0
    if "Distortion" in noise1.inputs: noise1.inputs["Distortion"].default_value = 2.0
    nt.links.new(map1.outputs["Vector"], noise1.inputs["Vector"])
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 40.0
    nt.links.new(_noise_fac_output(noise1), vor.inputs["Vector"])
    cr1 = nt.nodes.new("ShaderNodeValToRGB")
    cr1.color_ramp.elements[0].position = 0.0864
    cr1.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr1.color_ramp.elements[1].position = 0.1091
    cr1.color_ramp.elements[1].color = (1, 1, 1, 1)
    nt.links.new(vor.outputs[0], cr1.inputs["Fac"] if "Fac" in cr1.inputs else cr1.inputs[0])

    tex_coord2 = nt.nodes.new("ShaderNodeTexCoord")
    map2 = nt.nodes.new("ShaderNodeMapping")
    map2.inputs["Scale"].default_value = (wave_scale, 0.1, 0.1)
    nt.links.new(tex_coord2.outputs["Object"], map2.inputs["Vector"])
    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    noise2.inputs["Scale"].default_value = 3.0
    if "Detail" in noise2.inputs:     noise2.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise2.inputs: noise2.inputs["Distortion"].default_value = 2.0
    nt.links.new(map2.outputs["Vector"], noise2.inputs["Vector"])
    cr2 = nt.nodes.new("ShaderNodeValToRGB")
    cr2.color_ramp.elements[0].position = 0.0818
    cr2.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr2.color_ramp.elements[1].position = 0.8500
    cr2.color_ramp.elements[1].color = (1, 1, 1, 1)
    nt.links.new(_noise_fac_output(noise2), cr2.inputs["Fac"] if "Fac" in cr2.inputs else cr2.inputs[0])

    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
    mix.inputs[0].default_value = 0.6
    nt.links.new(cr1.outputs["Color"], mix.inputs[6])
    nt.links.new(cr2.outputs["Color"], mix.inputs[7])
    return mix.outputs[2]

def make_black_plywood(name="BlackPlywood") -> bpy.types.Material:
    """Port of materials/wood/plywood.py:shader_shelves_black_wood."""

    wave_scale = float(np.random.uniform(1.0, 3.0))
    base_rgb = (float(np.random.uniform(0.015, 0.035)),
                float(np.random.uniform(0.0, 0.01)),
                float(np.random.uniform(0.0, 0.01)))
    roughness = float(np.random.uniform(0.75, 1.0))
    mat = _new_material(name)
    nt = mat.node_tree
    mix_out = _plywood_wavy(nt, wave_scale, 0.005, 0.02)
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position = 0.02
    cr.color_ramp.elements[0].color = (0, 0, 0, 1)
    cr.color_ramp.elements[1].position = 0.8
    cr.color_ramp.elements[1].color = (*base_rgb, 1.0)
    nt.links.new(mix_out, cr.inputs["Fac"] if "Fac" in cr.inputs else cr.inputs[0])
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=roughness)
    nt.links.new(cr.outputs["Color"], bsdf.inputs["Base Color"])
    _connect_output(nt, bsdf)
    return mat

def make_blonde_plywood(name="BlondePlywood") -> bpy.types.Material:
    """Port of materials/wood/plywood.py:shader_shelves_wood (BlondePlywood)."""

    wave_scale = float(np.random.uniform(1.0, 3.0))
    bright_hsv = (float(np.random.uniform(0.03, 0.09)),
                  float(np.random.uniform(0.5, 0.7)),
                  float(np.random.uniform(0.7, 1.0)))
    mid_hsv = (float(np.random.uniform(0.02, 0.06)),
               float(np.random.uniform(0.6, 1.0)),
               float(np.random.uniform(0.3, 0.6)))
    dark_hsv_ = (float(np.random.uniform(0.03, 0.05)),
                 float(np.random.uniform(0.6, 1.0)),
                 float(np.random.uniform(0.1, 0.3)))
    roughness = float(np.random.uniform(0.75, 1.0))

    mat = _new_material(name)
    nt = mat.node_tree
    mix_out = _plywood_wavy(nt, wave_scale, 0.005, 0.02)

    cr = nt.nodes.new("ShaderNodeValToRGB")
    # Original has 3 color stops (dark/mid/bright)
    cr.color_ramp.elements.new(0.11)
    cr.color_ramp.elements[0].position = 0.02
    cr.color_ramp.elements[0].color = hsv2rgba(dark_hsv_)
    cr.color_ramp.elements[1].position = 0.11
    cr.color_ramp.elements[1].color = hsv2rgba(mid_hsv)
    cr.color_ramp.elements[2].position = 0.8
    cr.color_ramp.elements[2].color = hsv2rgba(bright_hsv)
    nt.links.new(mix_out, cr.inputs["Fac"] if "Fac" in cr.inputs else cr.inputs[0])
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=roughness)
    nt.links.new(cr.outputs["Color"], bsdf.inputs["Base Color"])
    _connect_output(nt, bsdf)
    return mat

# ------------------------------------------------------------------
# Curtain options: FineKnitFabric, Wood (above), PlasticRough, GlassVolume, LampShade
# ------------------------------------------------------------------
def make_fine_knit_fabric(name="FineKnitFabric") -> bpy.types.Material:
    """Port of materials/fabric/fine_knit_fabric.py:shader_material — simplified:
    the original uses a procedural UV-based wave pattern to simulate thread weave.
    We approximate with a high-frequency noise grain + a tinted base color."""

    color = tuple(float(v) for v in np.random.uniform(0.2, 1.0, 3))
    roughness = float(np.random.uniform(0.0, 1.0))
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 200.0
    if "Detail" in noise.inputs:     noise.inputs["Detail"].default_value = 8.0
    if "Distortion" in noise.inputs: noise.inputs["Distortion"].default_value = 0.5
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])
    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
    nt.links.new(_noise_fac_output(noise), mix.inputs[0])
    mix.inputs[6].default_value = (color[0] * 0.6, color[1] * 0.6, color[2] * 0.6, 1.0)
    mix.inputs[7].default_value = (color[0], color[1], color[2], 1.0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=max(0.6, roughness),
                    **{"Sheen Weight": 0.5})
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    # Tiny displacement for cloth micro-structure
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    disp.inputs["Scale"].default_value = 0.003
    nt.links.new(_noise_fac_output(noise), disp.inputs["Height"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

def make_plastic_rough(name="PlasticRough") -> bpy.types.Material:
    base_color = hsv2rgba((np.random.uniform(0, 1),
                           np.random.uniform(0.5, 0.8),
                           log_uniform(0.01, 0.5)))
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2000.0
    if "Detail" in noise.inputs:     noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs: noise.inputs["Distortion"].default_value = 2.0
    if "W" in noise.inputs:          noise.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs[0].default_value = float(np.random.uniform(0.0, 1.0))
    mr.inputs[3].default_value = 0.05; mr.inputs[4].default_value = 0.25
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, **{"Base Color": base_color})
    nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

def make_glass_volume(name="GlassVolume") -> bpy.types.Material:
    """Port of materials/ceramic/glass_volume.py:shader_glass_volume — Principled BSDF
    with Transmission=1 + volume absorption (tinted)."""

    if np.random.uniform(0, 1) < 0.3:
        color = (1.0, 1.0, 1.0, 1.0)
    else:
        color = hsv2rgba((np.random.uniform(0, 1),
                          np.random.uniform(0.5, 0.9),
                          np.random.uniform(0.6, 0.9)))
    mat = _new_material(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=0.0,
                    **{"Transmission Weight": 1.0})
    vol = nt.nodes.new("ShaderNodeVolumeAbsorption")
    vol.inputs["Color"].default_value = color
    vol.inputs["Density"].default_value = 100.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    nt.links.new(vol.outputs[0], out.inputs["Volume"])
    return mat

def make_lampshade(name="LampShade") -> bpy.types.Material:
    """Port of materials/lamp_shaders.py:shader_lampshade — subsurface + tinted
    translucent via mix-shader gated on camera ray."""

    mat = _new_material(name)
    nt = mat.node_tree
    light_path = nt.nodes.new("ShaderNodeLightPath")
    obj_info = nt.nodes.new("ShaderNodeObjectInfo")
    wn = nt.nodes.new("ShaderNodeTexWhiteNoise")
    if hasattr(wn, "noise_dimensions"):
        try: wn.noise_dimensions = "4D"
        except TypeError: pass
    nt.links.new(obj_info.outputs["Random"], wn.inputs["Vector"] if "Vector" in wn.inputs else wn.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
    mix.inputs[0].default_value = 0.9
    nt.links.new(wn.outputs["Color"], mix.inputs[6])
    mix.inputs[7].default_value = (0.5, 0.4444, 0.3669, 1.0)
    bsdf_a = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf_a, Roughness=float(np.random.uniform(0.5, 0.8)),
                    IOR=4.0,
                    **{"Subsurface Weight": float(np.random.uniform(0.03, 0.08)),
                       "Transmission Weight": float(np.random.uniform(0.05, 0.2))})
    nt.links.new(mix.outputs[2], bsdf_a.inputs["Base Color"])
    bsdf_b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf_b, Roughness=0.7)
    nt.links.new(mix.outputs[2], bsdf_b.inputs["Base Color"])
    mix_sh = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(light_path.outputs["Is Camera Ray"], mix_sh.inputs["Fac"])
    nt.links.new(bsdf_a.outputs[0], mix_sh.inputs[1])
    nt.links.new(bsdf_b.outputs[0], mix_sh.inputs[2])
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(mix_sh.outputs[0], out.inputs["Surface"])
    return mat

# ------------------------------------------------------------------
# Window glass — faithful port of shader_window_glass in window.py
# ------------------------------------------------------------------
def make_window_glass(name="WindowGlass") -> bpy.types.Material:
    """

    Non-refractive glass: Transparent mixed with Glossy, and camera-ray gated
    MixShader so non-camera rays are fully transparent (render efficiency trick
    for single-sided window meshes)."""

    roughness = clip_gaussian(0, 0.015, 0, 0.03, 0.03)
    transmission = float(np.random.uniform(0.05, 0.12))

    mat = _new_material(name)
    nt = mat.node_tree

    transparent = nt.nodes.new("ShaderNodeBsdfTransparent")

    glossy = nt.nodes.new("ShaderNodeBsdfGlossy")
    if "Roughness" in glossy.inputs:
        glossy.inputs["Roughness"].default_value = roughness

    # Mix transparent/glossy by transmission probability
    mix1 = nt.nodes.new("ShaderNodeMixShader")
    mix1.inputs["Fac"].default_value = transmission
    nt.links.new(transparent.outputs[0], mix1.inputs[1])
    nt.links.new(glossy.outputs[0], mix1.inputs[2])

    # Camera-ray gate: non-camera rays pass through straight (fully transparent)
    light_path = nt.nodes.new("ShaderNodeLightPath")
    mix2 = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(light_path.outputs["Is Camera Ray"], mix2.inputs["Fac"])
    nt.links.new(transparent.outputs[0], mix2.inputs[1])
    nt.links.new(mix1.outputs[0], mix2.inputs[2])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(mix2.outputs[0], out.inputs["Surface"])
    return mat

# ============================================================================
# ============================================================================
woods = [
    (make_wood, 1.0),
    (make_white_plywood, 0.1),
    (make_black_plywood, 0.1),
    (make_blonde_plywood, 0.1),
]

metals = [
    (make_metal_basic, 3.0),
    (make_brushed_metal, 2.0),
    (make_galvanized_metal, 1.0),
    (make_grained_metal, 1.0),
    (make_hammered_metal, 0.7),
    (make_brushed_black_metal, 0.3),
]

curtain = [
    (make_fine_knit_fabric, 1.0),
    (make_wood, 2.0),
    (make_plastic_rough, 2.0),
    (make_glass_volume, 0.5),
    (make_lampshade, 2.0),
]

REGISTRY = {
    "woods": woods,
    "metals": metals,
    "curtain": curtain,
}

def get_material(registry_key: str, name: str = None) -> bpy.types.Material:
    ctor = weighted_sample(REGISTRY[registry_key])
    return ctor(name=name or registry_key.title())

SEED = int(os.environ.get("SEED", 0))

# Phase 1 — material sampling on raw SEED (mirrors sample_parameters RNG order)
seed_all(SEED)
# Burn sample_parameters draws that precede the material picks
_ = float(np.random.uniform(0.05, 0.1))     # frame_width
_ = float(np.random.uniform(0.01, _))       # sub_frame_width
_ = int(np.random.randint(1, 2))            # sub_frame_h_amount
_ = int(np.random.randint(1, 2))            # sub_frame_v_amount
_ = float(np.random.uniform(0.01, 0.03))    # glass_thickness
_ = float(np.random.uniform(0.001, 0.003))  # shutter_panel_radius
_ = float(np.random.uniform(0.03, 0.05))    # shutter_width
_ = float(np.random.uniform(0.003, 0.007))  # shutter_thickness
_ = float(np.random.uniform(0, 1))          # shutter_rotation
_ = float(np.random.uniform(0.001, 0.003))  # shutter_interval delta
_cfd = float(np.random.uniform(0.05, 0.1))  # curtain_frame_depth
_ = float(np.random.uniform(0.03, _cfd))    # curtain_depth
_ = float(np.random.uniform(0.01, 0.02))    # curtain_frame_radius

MAT_FRAME        = get_material("woods",   "FrameMaterial")
MAT_CURTAINFRAME = get_material("metals",  "CurtainFrameMaterial")
MAT_CURTAIN      = get_material("curtain", "CurtainMaterial")
MAT_GLASS        = make_window_glass("WindowGlass")

# Geometry — from objects_blender/windows/WindowFactory.py
def clear_scene():
    bpy.context.scene.cursor.location = (0, 0, 0)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)

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

def add_box(x0, x1, y0, y1, z0, z1, name="box", material=None):
    bm = bmesh.new()
    verts = [
        bm.verts.new((x0, y0, z0)), bm.verts.new((x1, y0, z0)),
        bm.verts.new((x1, y1, z0)), bm.verts.new((x0, y1, z0)),
        bm.verts.new((x0, y0, z1)), bm.verts.new((x1, y0, z1)),
        bm.verts.new((x1, y1, z1)), bm.verts.new((x0, y1, z1)),
    ]
    faces = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    for f in faces:
        bm.faces.new([verts[i] for i in f])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    apply_tf(obj)
    if material is not None:
        obj.data.materials.append(material)
    return obj

def build(seed=SEED):
    rng = np.random.default_rng(seed)
    np.random.seed(seed)
    clear_scene()

    W = float(rng.uniform(1.0, 3.0))
    H = float(rng.uniform(1.0, 3.0))

    frame_width = float(rng.uniform(0.05, 0.1))
    frame_thickness = float(rng.uniform(0.05, 0.12))
    glass_thickness = float(rng.uniform(0.01, 0.03))
    sub_frame_width = float(rng.uniform(glass_thickness, frame_width))

    panel_width = float(rng.uniform(0.4, min(W, 1.0)))
    panel_height = float(rng.uniform(0.4, min(H, 1.0)))
    panel_v_amount = max(int(W // panel_width), 1)
    panel_h_amount = max(int(H // panel_height), 1)

    sub_panel_width = float(rng.uniform(0.4, min(panel_width, 1.0)))
    sub_panel_height = float(rng.uniform(0.4, min(panel_height, 1.0)))
    sub_panel_height = max(min(sub_panel_height, 2 * sub_panel_width), 0.5 * sub_panel_width)
    sub_frame_v_amount = max(int(panel_width // sub_panel_width), 1)
    sub_frame_h_amount = max(int(panel_height // sub_panel_height), 1)

    has_shutter = rng.random() < 0.5
    has_curtain = rng.random() < 0.5
    if has_curtain:
        has_shutter = False

    hw = W / 2
    hh = H / 2
    parts = []

    # Outer frame (4 bars) — FrameMaterial
    parts.append(add_box(-hw, hw, 0, frame_thickness, -hh, -hh + frame_width, "frame_bot", MAT_FRAME))
    parts.append(add_box(-hw, hw, 0, frame_thickness,  hh - frame_width,  hh, "frame_top", MAT_FRAME))
    parts.append(add_box(-hw, -hw + frame_width, 0, frame_thickness, -hh + frame_width, hh - frame_width, "frame_l", MAT_FRAME))
    parts.append(add_box( hw - frame_width,  hw, 0, frame_thickness, -hh + frame_width, hh - frame_width, "frame_r", MAT_FRAME))

    inner_w = W - 2 * frame_width
    inner_h = H - 2 * frame_width

    # Panel dividers — FrameMaterial
    sub_frame_thickness = float(rng.uniform(glass_thickness, frame_thickness))
    for i in range(1, panel_h_amount):
        z_pos = -hh + frame_width + inner_h * i / panel_h_amount
        parts.append(add_box(-hw + frame_width, hw - frame_width, 0, frame_thickness,
                             z_pos - frame_width / 2, z_pos + frame_width / 2,
                             "panel_h", MAT_FRAME))
    for j in range(1, panel_v_amount):
        x_pos = -hw + frame_width + inner_w * j / panel_v_amount
        parts.append(add_box(x_pos - frame_width / 2, x_pos + frame_width / 2,
                             0, frame_thickness,
                             -hh + frame_width, hh - frame_width,
                             "panel_v", MAT_FRAME))

    # Sub-frame dividers — FrameMaterial
    p_w = inner_w / panel_v_amount
    p_h = inner_h / panel_h_amount
    for pi in range(panel_h_amount):
        for pj in range(panel_v_amount):
            px0 = -hw + frame_width + pj * p_w
            pz0 = -hh + frame_width + pi * p_h
            for si in range(1, sub_frame_h_amount):
                z_pos = pz0 + p_h * si / sub_frame_h_amount
                parts.append(add_box(px0, px0 + p_w, 0, sub_frame_thickness,
                                     z_pos - sub_frame_width / 2, z_pos + sub_frame_width / 2,
                                     "sub_h", MAT_FRAME))
            for sj in range(1, sub_frame_v_amount):
                x_pos = px0 + p_w * sj / sub_frame_v_amount
                parts.append(add_box(x_pos - sub_frame_width / 2, x_pos + sub_frame_width / 2,
                                     0, sub_frame_thickness,
                                     pz0, pz0 + p_h,
                                     "sub_v", MAT_FRAME))

    # Glass panes — window glass Material
    glass_y = frame_thickness / 2 - glass_thickness / 2
    sp_w = (p_w - sub_frame_width * (sub_frame_v_amount - 1)) / sub_frame_v_amount
    sp_h = (p_h - sub_frame_width * (sub_frame_h_amount - 1)) / sub_frame_h_amount

    for pi in range(panel_h_amount):
        for pj in range(panel_v_amount):
            px0 = -hw + frame_width + pj * p_w
            pz0 = -hh + frame_width + pi * p_h
            for si in range(sub_frame_h_amount):
                for sj in range(sub_frame_v_amount):
                    gx0 = px0 + sj * (sp_w + sub_frame_width)
                    gz0 = pz0 + si * (sp_h + sub_frame_width)
                    parts.append(add_box(gx0, gx0 + sp_w, glass_y, glass_y + glass_thickness,
                                         gz0, gz0 + sp_h,
                                         "glass", MAT_GLASS))

    # Shutters — FrameMaterial
    if has_shutter:
        shutter_width = float(rng.uniform(0.03, 0.05))
        shutter_thickness = float(rng.uniform(0.003, 0.007))
        shutter_rotation = float(rng.uniform(0, 1)) * math.pi / 2
        shutter_interval = shutter_width + float(rng.uniform(0.001, 0.003))
        n_slats = int(inner_h / shutter_interval)

        for i in range(n_slats):
            z_slat = -hh + frame_width + i * shutter_interval
            slat_y = -shutter_thickness / 2
            slat = add_box(-hw + frame_width, hw - frame_width,
                           slat_y, slat_y + shutter_thickness,
                           z_slat, z_slat + shutter_width, "slat", MAT_FRAME)
            slat.rotation_euler.x = shutter_rotation
            apply_tf(slat)
            parts.append(slat)

    # Curtain rod + curtain panels
    if has_curtain:
        rod_r = float(rng.uniform(0.01, 0.02))
        rod_y = float(rng.uniform(0.05, 0.1))
        curtain_depth = float(rng.uniform(0.03, rod_y))
        curtain_interval_number = max(int(W / float(rng.uniform(0.08, 0.2))), 3)
        curtain_mid_l = -float(rng.uniform(0, W / 2))
        curtain_mid_r = float(rng.uniform(0, W / 2))

        # Rod — CurtainFrameMaterial
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=12, radius=rod_r, depth=W + 0.2,
            location=(0, -rod_y, hh + rod_r),
        )
        rod = bpy.context.active_object
        rod.rotation_euler.y = math.pi / 2
        apply_tf(rod)
        rod.data.materials.append(MAT_CURTAINFRAME)
        parts.append(rod)

        # Curtain panels — CurtainMaterial
        for side in [-1, 1]:
            if side == -1:
                cx_start = -hw
                cx_end = curtain_mid_l
            else:
                cx_start = curtain_mid_r
                cx_end = hw

            curtain_w = abs(cx_end - cx_start)
            if curtain_w < 0.05:
                continue

            bm_c = bmesh.new()
            n_fold = max(curtain_interval_number, 4)
            for fi in range(n_fold + 1):
                t = fi / n_fold
                fold_x = cx_start + curtain_w * t
                fold_y = -curtain_depth * (1.0 + 0.3 * math.sin(t * math.pi * n_fold * 0.5))
                v_bot = bm_c.verts.new((fold_x, fold_y, -hh + frame_width))
                v_top = bm_c.verts.new((fold_x, fold_y, hh + rod_r))
            bm_c.verts.ensure_lookup_table()
            for fi in range(n_fold):
                base = fi * 2
                bm_c.faces.new([bm_c.verts[base], bm_c.verts[base + 2],
                                bm_c.verts[base + 3], bm_c.verts[base + 1]])
            c_mesh = bpy.data.meshes.new("curtain")
            bm_c.to_mesh(c_mesh)
            bm_c.free()
            curtain = bpy.data.objects.new("curtain", c_mesh)
            bpy.context.scene.collection.objects.link(curtain)

            sol = curtain.modifiers.new("sol", "SOLIDIFY")
            sol.thickness = 0.005
            bpy.context.view_layer.objects.active = curtain
            bpy.ops.object.modifier_apply(modifier=sol.name)

            apply_tf(curtain)
            curtain.data.materials.append(MAT_CURTAIN)
            parts.append(curtain)

    result = join_objs(parts) if len(parts) > 1 else parts[0]

    # Bevel sharp edges for smoother appearance
    bv = result.modifiers.new("bevel", "BEVEL")
    bv.width = 0.003
    bv.segments = 2
    bv.limit_method = "ANGLE"
    bv.angle_limit = math.radians(60)
    bpy.context.view_layer.objects.active = result
    bpy.ops.object.modifier_apply(modifier=bv.name)

    result.name = "WindowFactory"
    apply_tf(result)

    return result

build(SEED)
