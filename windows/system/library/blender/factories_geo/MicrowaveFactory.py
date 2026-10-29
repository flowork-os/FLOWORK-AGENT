# [FL_INDEX: keywords="blender_factory, procedural_3d, MicrowaveFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: MicrowaveFactory | Category: factories_geo
# Prompt: A 3D model of a countertop microwave oven shown from a three-quarter top-down perspective. The appliance has a wide, low-profile rectangular dark brown body with rounded corners, a smooth dark navy blue top surface, small ventilation slots along the front lower edge, and a small door latch detail on the right side.

import os
import bpy, bmesh, math
import random, colorsys
import numpy as np


def seed_all(seed: int):
    """Seed numpy + python random. Call once before any geometry/material sampling."""

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
    """Create a fresh material with empty node tree (BSDF removed)."""

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
        "Sheen Tint": ("Sheen Tint",),
        "Subsurface Color": ("Subsurface Color",),
    }
    for k, v in kw.items():
        names = aliases.get(k, (k,))
        for name in names:
            if name in bsdf.inputs:
                bsdf.inputs[name].default_value = v
                break


def _build_float_curve(nt, value_socket, anchors):
    """Replica of NodeWrangler.build_float_curve — creates ShaderNodeFloatCurve."""

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
    """Blender 5.0 renamed Fac→Factor on some nodes; fall back to first output."""

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


# ============================================================================
# Base material constructors
# ============================================================================
def make_metal_basic(name="MetalBasic", color_hsv=None, base_color_rgba=None) -> bpy.types.Material:
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = float(np.random.uniform(10, 25))
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    fc = _build_float_curve(
        nt,
        _noise_fac_output(noise),
        [(0, float(np.random.uniform(0, 0.2))),
         (1, float(np.random.uniform(0.4, 0.7)))],
    )

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf,
        Metallic=1.0,
        **{"Specular IOR Level": float(np.random.uniform(0.5, 1.0))},
        **{"Base Color": base_color_rgba or hsv2rgba(color_hsv or metal_hsv())},
    )
    nt.links.new(fc.outputs["Value"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat


def make_brushed_metal(name="BrushedMetal", base_color_hsv=None, base_color_rgba=None) -> bpy.types.Material:
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # Stretched mapping in Z to simulate brush direction
    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    mapping_1.inputs["Scale"].default_value = (0.2, 0.2, 5.0)
    nt.links.new(tex_coord.outputs["Object"], mapping_1.inputs["Vector"])

    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise2, "noise_dimensions"):
        try: noise2.noise_dimensions = "4D"
        except TypeError: pass
    noise2.inputs["Scale"].default_value = float(100.0)
    if "Detail" in noise2.inputs:    noise2.inputs["Detail"].default_value = 15.0
    if "Roughness" in noise2.inputs: noise2.inputs["Roughness"].default_value = 0.4
    if "Distortion" in noise2.inputs:noise2.inputs["Distortion"].default_value = 0.1
    if "W" in noise2.inputs:         noise2.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(mapping_1.outputs["Vector"], noise2.inputs["Vector"])

    # Map range to brighten
    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[1].default_value = 0.4
    map_range.inputs[2].default_value = 0.6
    map_range.inputs[3].default_value = 0.8
    map_range.inputs[4].default_value = 1.2
    nt.links.new(_noise_fac_output(noise2), map_range.inputs[0])

    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_node.inputs["Color"].default_value = base_color_rgba or hsv2rgba(base_color_hsv)
    nt.links.new(map_range.outputs["Result"], hsv_node.inputs["Value"])

    # Roughness map range
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


def make_galvanized_metal(name="GalvanizedMetal", base_color_hsv=None, base_color_rgba=None) -> bpy.types.Material:
    """Re-impl of materials/metal/galvanized_metal.py:shader_galvanized_metal.

    Uses Voronoi for the spangle pattern. Falls back to 3D Voronoi if 4D unsupported.
    """

    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
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

    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[3].default_value = 0.1
    map_range.inputs[4].default_value = 0.5
    # Voronoi outputs may be named "Distance"/"Color"; default index 0 is fine
    nt.links.new(voronoi.outputs[0], map_range.inputs[0])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf,
        Metallic=1.0,
        **{"Specular IOR Level": 0.0, "Base Color": base_color_rgba or hsv2rgba(base_color_hsv)},
    )
    nt.links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat


def make_grained_metal(name="GrainedMetal", base_color_hsv=None, base_color_rgba=None) -> bpy.types.Material:
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

    # Displacement chain
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
        bsdf,
        Metallic=1.0,
        **{"Specular IOR Level": 0.0, "Base Color": base_color_rgba or hsv2rgba(base_color_hsv)},
    )
    nt.links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


def make_hammered_metal(name="HammeredMetal", base_color_hsv=None, base_color_rgba=None) -> bpy.types.Material:
    """Re-impl of materials/metal/hammered_metal.py — Voronoi smooth_f1 displacement."""

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

    # Distance ** 2.5 * small_factor → displacement
    pow_node = nt.nodes.new("ShaderNodeMath")
    pow_node.operation = "POWER"
    pow_node.inputs[1].default_value = 2.5
    # Voronoi distance output may be named "Distance" — fall back to index 0
    dist_out = voronoi.outputs.get("Distance") or voronoi.outputs[0]
    nt.links.new(dist_out, pow_node.inputs[0])

    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = log_uniform(0.001, 0.003)
    nt.links.new(pow_node.outputs[0], mul.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf,
        Metallic=1.0,
        **{"Specular IOR Level": 0.0, "Base Color": base_color_rgba or hsv2rgba(base_color_hsv), "Roughness": 0.1},
    )
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


def make_brushed_black_metal(name="BrushedBlackMetal") -> bpy.types.Material:
    """Re-impl of materials/metal/appliance.py:shader_brushed_black_metal.

    Original uses ShaderNodeBsdfAnisotropic. We use Principled BSDF with high
    anisotropic + dark color, since Anisotropic BSDF socket layout differs.
    """

    mat = _new_material(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf,
        Metallic=1.0,
        Roughness=0.4,
        Anisotropic=0.9,
        **{"Specular IOR Level": 0.5, "Base Color": (0.0167, 0.0167, 0.0167, 1.0)},
    )
    _connect_output(nt, bsdf)
    return mat


def make_white_metal(name="WhiteMetal") -> bpy.types.Material:
    """Re-impl of materials/metal/appliance.py:shader_white_metal."""

    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1.0, 1.0, 50.0)
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 20.0
    if "Detail" in noise.inputs:    noise.inputs["Detail"].default_value = 20.0
    if "Distortion" in noise.inputs:noise.inputs["Distortion"].default_value = 1.0
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])

    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position = 0.25
    cr.color_ramp.elements[0].color = (0.5244, 0.5244, 0.5244, 1.0)
    cr.color_ramp.elements[1].position = 1.0
    cr.color_ramp.elements[1].color = (0.9698, 0.9698, 0.9698, 1.0)
    # ColorRamp Fac input
    cr_in = cr.inputs.get("Fac") or cr.inputs[0]
    nt.links.new(_noise_fac_output(noise), cr_in)

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf,
        Metallic=1.0,
        Roughness=0.1,
        Anisotropic=0.9182,
        **{"Specular IOR Level": 1.0, "Sheen Weight": 0.0455},
    )
    nt.links.new(cr.outputs["Color"], bsdf.inputs["Base Color"])
    _connect_output(nt, bsdf)
    return mat


def make_glass(name="Glass", base_color_rgba=None) -> bpy.types.Material:
    """Re-impl of materials/ceramic/glass.py:shader_glass (non-window variant)."""

    mat = _new_material(name)
    nt = mat.node_tree
    glass = nt.nodes.new("ShaderNodeBsdfGlass")
    if "Roughness" in glass.inputs:
        glass.inputs["Roughness"].default_value = 0.02
    if "IOR" in glass.inputs:
        glass.inputs["IOR"].default_value = 1.5
    # Use baked color if provided, otherwise sample
    if base_color_rgba is not None:
        color = base_color_rgba
    elif np.random.uniform() < 0.5:
        color = (1.0, 1.0, 1.0, 1.0)
    else:
        color = hsv2rgba((np.random.uniform(0, 1), np.random.uniform(0.05, 0.25), 1.0))
    if "Color" in glass.inputs:
        glass.inputs["Color"].default_value = color
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(glass.outputs[0], out.inputs["Surface"])
    return mat


def make_black_glass(name="BlackGlass") -> bpy.types.Material:
    """Re-impl of materials/metal/appliance.py:shader_black_glass — GlossyBSDF dark."""

    mat = _new_material(name)
    nt = mat.node_tree
    glossy = nt.nodes.new("ShaderNodeBsdfGlossy")
    if "Color" in glossy.inputs:
        glossy.inputs["Color"].default_value = (0.0068, 0.0068, 0.0068, 1.0)
    if "Roughness" in glossy.inputs:
        glossy.inputs["Roughness"].default_value = 0.2
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(glossy.outputs[0], out.inputs["Surface"])
    return mat


def make_plastic_rough(name="PlasticRough", base_color=None) -> bpy.types.Material:
    """Re-impl of materials/plastic/plastic_rough.py:shader_rough_plastic."""

    if base_color is None:
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

    roughness_input = float(np.random.uniform(0.0, 1.0))
    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[0].default_value = roughness_input
    map_range.inputs[3].default_value = 0.05
    map_range.inputs[4].default_value = 0.25

    # Tiny displacement
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
    mul3.inputs[1].default_value = 0.003
    nt.links.new(mul2.outputs[0], mul3.inputs[0])
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul3.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, **{"Base Color": base_color})
    nt.links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


def make_wood(name="Wood", color=None) -> bpy.types.Material:
    """Simplified re-impl of materials/wood/wood.py:shader_wood.

    Original uses MusgraveTexture (REMOVED in Blender 5.0) for the wood grain.
    We substitute multi-octave NoiseTexture in stretched mapping to fake the
    grain look. Visually approximate, NOT pixel-identical to original.
    """

    if color is None:
        color = hsv2rgba(bark_hsv())
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # Stretched mapping to make wood grain anisotropic
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (5.0, 100.0, 100.0)
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    grain = nt.nodes.new("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = 10.0
    if "Detail" in grain.inputs:     grain.inputs["Detail"].default_value = 15.0
    if "Distortion" in grain.inputs: grain.inputs["Distortion"].default_value = 0.5
    nt.links.new(mapping.outputs["Vector"], grain.inputs["Vector"])

    # Color mix: dark grain over base color
    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_node.inputs["Saturation"].default_value = 0.8
    hsv_node.inputs["Value"].default_value = 0.2
    hsv_node.inputs["Color"].default_value = color

    # Mix node — Blender 5.0 uses ShaderNodeMix with data_type RGBA
    mix = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix, "data_type"):
        mix.data_type = "RGBA"
    # On RGBA mix: inputs[0]=Factor, inputs[6]=A_Color, inputs[7]=B_Color, outputs[2]=Result
    nt.links.new(_noise_fac_output(grain), mix.inputs[0])
    nt.links.new(hsv_node.outputs["Color"], mix.inputs[6])  # A: dark grain color
    mix.inputs[7].default_value = color                     # B: base color

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=float(np.random.uniform(0.4, 0.7)),
                    **{"Coat Weight": 0.2})
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    _connect_output(nt, bsdf)
    return mat


def make_screen_emissive(name="Screen") -> bpy.types.Material:
    """Substitute for the complex `text.Text` shader used by TV/Monitor screens.

    Picks a random tinted dark base + low-level emission so the screen reads as
    "powered on but display content not modeled".
    """

    mat = _new_material(name)
    nt = mat.node_tree
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    base = hsv2rgba((np.random.uniform(0, 1),
                     np.random.uniform(0.2, 0.6),
                     np.random.uniform(0.05, 0.2)))
    _set_principled(bsdf, **{"Base Color": base, "Roughness": 0.2, "Metallic": 0.0})
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = base
    elif "Emission" in bsdf.inputs:
        bsdf.inputs["Emission"].default_value = base
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = float(np.random.uniform(1.5, 3.0))
    _connect_output(nt, bsdf)
    return mat


# ============================================================================
# ============================================================================
metals = [
    (make_metal_basic, 3.0),
    (make_brushed_metal, 2.0),
    (make_galvanized_metal, 1.0),
    (make_grained_metal, 1.0),
    (make_hammered_metal, 0.7),
    (make_brushed_black_metal, 0.3),
]

metal_neutral = [
    (make_metal_basic, 1.0),
]

appliance_front_maybeglass = metals + [
    (make_black_glass, 4.0),
    (make_glass, 10.0),
]

appliance_front_glass = [
    (make_black_glass, 2.0),
    (make_glass, 10.0),
]

appliance_handle = metals + [
    (make_plastic_rough, 1.0),
    (make_wood, 3.0),
    (make_white_metal, 2.0),
]

graphicdesign = [
    (make_screen_emissive, 1.0),
]

REGISTRY = {
    "metals": metals,
    "metal_neutral": metal_neutral,
    "appliance_front_maybeglass": appliance_front_maybeglass,
    "appliance_front_glass": appliance_front_glass,
    "appliance_handle": appliance_handle,
    "graphicdesign": graphicdesign,
}


BAKED_MATERIALS = {
    0: {
        'Surface': ('BrushedMetal', (0.026976, 0.044259, 0.046867, 1.0)),
        'Back': ('GrainedMetal', (0.143451, 0.081684, 0.073835, 1.0)),
        'BlackGlass': ('MetalBasic', (0.063621, 0.031521, 0.042355, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    1: {
        'Surface': ('BrushedBlackMetal', (0.016700, 0.016700, 0.016700, 1.0)),
        'Back': ('MetalBasic', (0.034550, 0.029275, 0.023780, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': False, 'do_edge_wear': False,
    },
    2: {
        'Surface': ('GrainedMetal', (0.207930, 0.197915, 0.189294, 1.0)),
        'Back': ('MetalBasic', (0.100486, 0.157138, 0.146188, 1.0)),
        'BlackGlass': ('BlackGlass', (0.006800, 0.006800, 0.006800, 1.0)),
        'Glass': ('BlackGlass', (0.006800, 0.006800, 0.006800, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    3: {
        'Surface': ('MetalBasic', (0.038069, 0.049817, 0.028668, 1.0)),
        'Back': ('GalvanizedMetal', (0.351137, 0.407416, 0.237772, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('BlackGlass', (0.006800, 0.006800, 0.006800, 1.0)),
        'do_scratch': False, 'do_edge_wear': False,
    },
    4: {
        'Surface': ('MetalBasic', (0.221513, 0.408977, 0.305996, 1.0)),
        'Back': ('MetalBasic', (0.093866, 0.105738, 0.161964, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    5: {
        'Surface': ('MetalBasic', (0.072564, 0.087422, 0.137942, 1.0)),
        'Back': ('HammeredMetal', (0.228702, 0.228740, 0.208263, 1.0)),
        'BlackGlass': ('GrainedMetal', (0.156829, 0.086230, 0.085528, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    6: {
        'Surface': ('GrainedMetal', (0.080066, 0.055589, 0.114085, 1.0)),
        'Back': ('BrushedMetal', (0.127777, 0.201251, 0.158602, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    7: {
        'Surface': ('MetalBasic', (0.138217, 0.095719, 0.113261, 1.0)),
        'Back': ('MetalBasic', (0.162672, 0.165748, 0.132260, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    8: {
        'Surface': ('MetalBasic', (0.219172, 0.193767, 0.193689, 1.0)),
        'Back': ('BrushedBlackMetal', (0.016700, 0.016700, 0.016700, 1.0)),
        'BlackGlass': ('HammeredMetal', (0.055475, 0.032760, 0.015367, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    9: {
        'Surface': ('BrushedBlackMetal', (0.016700, 0.016700, 0.016700, 1.0)),
        'Back': ('MetalBasic', (0.036342, 0.014855, 0.032797, 1.0)),
        'BlackGlass': ('BlackGlass', (0.006800, 0.006800, 0.006800, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    10: {
        'Surface': ('BrushedMetal', (0.175157, 0.164551, 0.102992, 1.0)),
        'Back': ('GalvanizedMetal', (0.088611, 0.110223, 0.162273, 1.0)),
        'BlackGlass': ('GrainedMetal', (0.026760, 0.016169, 0.021974, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    11: {
        'Surface': ('MetalBasic', (0.053773, 0.033295, 0.055807, 1.0)),
        'Back': ('MetalBasic', (0.131803, 0.121565, 0.100456, 1.0)),
        'BlackGlass': ('GrainedMetal', (0.025056, 0.018718, 0.014799, 1.0)),
        'Glass': ('BlackGlass', (0.006800, 0.006800, 0.006800, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    12: {
        'Surface': ('GrainedMetal', (0.203347, 0.129851, 0.211785, 1.0)),
        'Back': ('MetalBasic', (0.285810, 0.465904, 0.279359, 1.0)),
        'BlackGlass': ('MetalBasic', (0.285404, 0.492236, 0.431810, 1.0)),
        'Glass': ('BlackGlass', (0.006800, 0.006800, 0.006800, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    13: {
        'Surface': ('MetalBasic', (0.337037, 0.383726, 0.231840, 1.0)),
        'Back': ('MetalBasic', (0.120899, 0.119584, 0.128170, 1.0)),
        'BlackGlass': ('MetalBasic', (0.034697, 0.029397, 0.048781, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    14: {
        'Surface': ('GalvanizedMetal', (0.052546, 0.035047, 0.048644, 1.0)),
        'Back': ('MetalBasic', (0.121697, 0.118985, 0.191072, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    15: {
        'Surface': ('MetalBasic', (0.231301, 0.136043, 0.136875, 1.0)),
        'Back': ('MetalBasic', (0.052362, 0.048721, 0.028196, 1.0)),
        'BlackGlass': ('MetalBasic', (0.040692, 0.070277, 0.056073, 1.0)),
        'Glass': ('BlackGlass', (0.006800, 0.006800, 0.006800, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    16: {
        'Surface': ('MetalBasic', (0.254623, 0.383620, 0.342464, 1.0)),
        'Back': ('MetalBasic', (0.119669, 0.219645, 0.254701, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    17: {
        'Surface': ('GrainedMetal', (0.088774, 0.121895, 0.074439, 1.0)),
        'Back': ('HammeredMetal', (0.021352, 0.032508, 0.027052, 1.0)),
        'BlackGlass': ('MetalBasic', (0.111292, 0.124465, 0.056083, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    18: {
        'Surface': ('MetalBasic', (0.099780, 0.099539, 0.113412, 1.0)),
        'Back': ('MetalBasic', (0.047837, 0.055967, 0.025618, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    19: {
        'Surface': ('BrushedMetal', (0.024069, 0.031288, 0.047463, 1.0)),
        'Back': ('GalvanizedMetal', (0.140477, 0.125395, 0.184251, 1.0)),
        'BlackGlass': ('BlackGlass', (0.006800, 0.006800, 0.006800, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': False, 'do_edge_wear': False,
    },
    20: {
        'Surface': ('GrainedMetal', (0.121965, 0.050623, 0.111567, 1.0)),
        'Back': ('GrainedMetal', (0.039533, 0.049877, 0.088214, 1.0)),
        'BlackGlass': ('MetalBasic', (0.025781, 0.023982, 0.047510, 1.0)),
        'Glass': ('BlackGlass', (0.006800, 0.006800, 0.006800, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    21: {
        'Surface': ('BrushedMetal', (0.027527, 0.018709, 0.034328, 1.0)),
        'Back': ('BrushedMetal', (0.066678, 0.115352, 0.064823, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    22: {
        'Surface': ('GrainedMetal', (0.074994, 0.092339, 0.131169, 1.0)),
        'Back': ('HammeredMetal', (0.112105, 0.112872, 0.091729, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': False, 'do_edge_wear': False,
    },
    23: {
        'Surface': ('MetalBasic', (0.288121, 0.164638, 0.261114, 1.0)),
        'Back': ('HammeredMetal', (0.076017, 0.116699, 0.108006, 1.0)),
        'BlackGlass': ('BrushedMetal', (0.099331, 0.101968, 0.064018, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    24: {
        'Surface': ('HammeredMetal', (0.102118, 0.049949, 0.111810, 1.0)),
        'Back': ('HammeredMetal', (0.072997, 0.046024, 0.068420, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    25: {
        'Surface': ('BrushedMetal', (0.290236, 0.475679, 0.496058, 1.0)),
        'Back': ('MetalBasic', (0.139987, 0.180659, 0.202978, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    26: {
        'Surface': ('BrushedMetal', (0.095438, 0.050539, 0.073918, 1.0)),
        'Back': ('MetalBasic', (0.012675, 0.027431, 0.031587, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': False, 'do_edge_wear': False,
    },
    27: {
        'Surface': ('MetalBasic', (0.122907, 0.116717, 0.048826, 1.0)),
        'Back': ('GrainedMetal', (0.213713, 0.090044, 0.201765, 1.0)),
        'BlackGlass': ('BrushedMetal', (0.019768, 0.023847, 0.029191, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': False, 'do_edge_wear': False,
    },
    28: {
        'Surface': ('BrushedMetal', (0.432780, 0.409551, 0.208770, 1.0)),
        'Back': ('GrainedMetal', (0.247696, 0.231068, 0.116521, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    29: {
        'Surface': ('MetalBasic', (0.268608, 0.113658, 0.113599, 1.0)),
        'Back': ('MetalBasic', (0.028112, 0.017228, 0.030298, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    30: {
        'Surface': ('MetalBasic', (0.087922, 0.109433, 0.183356, 1.0)),
        'Back': ('MetalBasic', (0.293705, 0.183084, 0.162053, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    31: {
        'Surface': ('MetalBasic', (0.047342, 0.029123, 0.035285, 1.0)),
        'Back': ('MetalBasic', (0.043623, 0.028124, 0.030498, 1.0)),
        'BlackGlass': ('BlackGlass', (0.006800, 0.006800, 0.006800, 1.0)),
        'Glass': ('BlackGlass', (0.006800, 0.006800, 0.006800, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    32: {
        'Surface': ('BrushedMetal', (0.020758, 0.011510, 0.026972, 1.0)),
        'Back': ('BrushedMetal', (0.013500, 0.033736, 0.027910, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    33: {
        'Surface': ('MetalBasic', (0.049559, 0.085489, 0.084209, 1.0)),
        'Back': ('MetalBasic', (0.023930, 0.016740, 0.009906, 1.0)),
        'BlackGlass': ('BrushedMetal', (0.080965, 0.119720, 0.085767, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    34: {
        'Surface': ('BrushedMetal', (0.091539, 0.083527, 0.044450, 1.0)),
        'Back': ('GrainedMetal', (0.033145, 0.023368, 0.014081, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    35: {
        'Surface': ('GrainedMetal', (0.334071, 0.168658, 0.156927, 1.0)),
        'Back': ('MetalBasic', (0.101486, 0.074074, 0.045943, 1.0)),
        'BlackGlass': ('BrushedMetal', (0.158472, 0.099098, 0.145438, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    36: {
        'Surface': ('BrushedMetal', (0.029923, 0.057302, 0.049379, 1.0)),
        'Back': ('BrushedMetal', (0.150107, 0.151506, 0.105024, 1.0)),
        'BlackGlass': ('GalvanizedMetal', (0.038943, 0.056967, 0.060122, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    37: {
        'Surface': ('GalvanizedMetal', (0.052215, 0.023887, 0.058414, 1.0)),
        'Back': ('HammeredMetal', (0.167299, 0.163711, 0.151973, 1.0)),
        'BlackGlass': ('MetalBasic', (0.185928, 0.198895, 0.267808, 1.0)),
        'Glass': ('BlackGlass', (0.006800, 0.006800, 0.006800, 1.0)),
        'do_scratch': False, 'do_edge_wear': False,
    },
    38: {
        'Surface': ('BrushedMetal', (0.191196, 0.210602, 0.460998, 1.0)),
        'Back': ('GrainedMetal', (0.390444, 0.291496, 0.180420, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    39: {
        'Surface': ('BrushedMetal', (0.114828, 0.110737, 0.048256, 1.0)),
        'Back': ('MetalBasic', (0.009812, 0.009492, 0.020892, 1.0)),
        'BlackGlass': ('BlackGlass', (0.006800, 0.006800, 0.006800, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    40: {
        'Surface': ('BrushedMetal', (0.232630, 0.131622, 0.231599, 1.0)),
        'Back': ('GalvanizedMetal', (0.055692, 0.032182, 0.029929, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    41: {
        'Surface': ('GalvanizedMetal', (0.024573, 0.042234, 0.033943, 1.0)),
        'Back': ('MetalBasic', (0.014486, 0.027597, 0.017608, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': False, 'do_edge_wear': False,
    },
    42: {
        'Surface': ('MetalBasic', (0.087814, 0.143339, 0.120666, 1.0)),
        'Back': ('MetalBasic', (0.122532, 0.134645, 0.073480, 1.0)),
        'BlackGlass': ('BrushedMetal', (0.025785, 0.016669, 0.027389, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    43: {
        'Surface': ('MetalBasic', (0.214444, 0.301861, 0.204361, 1.0)),
        'Back': ('MetalBasic', (0.244568, 0.242429, 0.359021, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    44: {
        'Surface': ('MetalBasic', (0.098773, 0.105648, 0.155340, 1.0)),
        'Back': ('MetalBasic', (0.122462, 0.080255, 0.115031, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    45: {
        'Surface': ('BrushedMetal', (0.379506, 0.264567, 0.390425, 1.0)),
        'Back': ('MetalBasic', (0.103289, 0.092302, 0.138420, 1.0)),
        'BlackGlass': ('BrushedMetal', (0.054262, 0.044746, 0.026155, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    46: {
        'Surface': ('GrainedMetal', (0.046875, 0.071354, 0.028744, 1.0)),
        'Back': ('BrushedMetal', (0.034690, 0.050818, 0.050239, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('BlackGlass', (0.006800, 0.006800, 0.006800, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    47: {
        'Surface': ('MetalBasic', (0.072820, 0.109586, 0.112599, 1.0)),
        'Back': ('GrainedMetal', (0.063038, 0.116290, 0.072154, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    48: {
        'Surface': ('BrushedMetal', (0.145885, 0.170133, 0.183785, 1.0)),
        'Back': ('BrushedMetal', (0.159538, 0.179776, 0.384594, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('BlackGlass', (0.006800, 0.006800, 0.006800, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    49: {
        'Surface': ('HammeredMetal', (0.062750, 0.032510, 0.042847, 1.0)),
        'Back': ('MetalBasic', (0.033078, 0.044937, 0.030431, 1.0)),
        'BlackGlass': ('GrainedMetal', (0.075980, 0.076278, 0.130531, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    50: {
        'Surface': ('HammeredMetal', (0.011820, 0.018592, 0.023664, 1.0)),
        'Back': ('GalvanizedMetal', (0.211487, 0.102734, 0.143180, 1.0)),
        'BlackGlass': ('BlackGlass', (0.006800, 0.006800, 0.006800, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    51: {
        'Surface': ('GalvanizedMetal', (0.053883, 0.032061, 0.049149, 1.0)),
        'Back': ('BrushedMetal', (0.078054, 0.037975, 0.070734, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    52: {
        'Surface': ('HammeredMetal', (0.071759, 0.044668, 0.020192, 1.0)),
        'Back': ('GalvanizedMetal', (0.038680, 0.080998, 0.083877, 1.0)),
        'BlackGlass': ('BlackGlass', (0.006800, 0.006800, 0.006800, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    53: {
        'Surface': ('BrushedMetal', (0.116763, 0.285485, 0.210303, 1.0)),
        'Back': ('GrainedMetal', (0.121912, 0.119231, 0.109601, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    54: {
        'Surface': ('MetalBasic', (0.170780, 0.167876, 0.169048, 1.0)),
        'Back': ('GalvanizedMetal', (0.252224, 0.276882, 0.134632, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    55: {
        'Surface': ('GrainedMetal', (0.053079, 0.033997, 0.031446, 1.0)),
        'Back': ('BrushedMetal', (0.181342, 0.243765, 0.104093, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    56: {
        'Surface': ('HammeredMetal', (0.099722, 0.167914, 0.209374, 1.0)),
        'Back': ('GalvanizedMetal', (0.238521, 0.391816, 0.400829, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('BlackGlass', (0.006800, 0.006800, 0.006800, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    57: {
        'Surface': ('BrushedMetal', (0.222976, 0.174578, 0.172414, 1.0)),
        'Back': ('BrushedMetal', (0.131385, 0.124544, 0.121915, 1.0)),
        'BlackGlass': ('BrushedMetal', (0.258836, 0.258836, 0.258836, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    58: {
        'Surface': ('MetalBasic', (0.188225, 0.188225, 0.188225, 1.0)),
        'Back': ('MetalBasic', (0.073746, 0.128795, 0.086098, 1.0)),
        'BlackGlass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    59: {
        'Surface': ('MetalBasic', (0.122263, 0.120897, 0.044873, 1.0)),
        'Back': ('MetalBasic', (0.051240, 0.080925, 0.079384, 1.0)),
        'BlackGlass': ('MetalBasic', (0.112088, 0.059763, 0.087045, 1.0)),
        'Glass': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
}


def get_baked_material(mat_type, base_color_rgba, name="Material"):
    if base_color_rgba is None:
        base_color_rgba = (0.5, 0.5, 0.5, 1.0)
    if mat_type == "MetalBasic":
        return make_metal_basic(name=name, base_color_rgba=base_color_rgba)
    elif mat_type == "BrushedMetal":
        return make_brushed_metal(name=name, base_color_rgba=base_color_rgba)
    elif mat_type == "GalvanizedMetal":
        return make_galvanized_metal(name=name, base_color_rgba=base_color_rgba)
    elif mat_type == "GrainedMetal":
        return make_grained_metal(name=name, base_color_rgba=base_color_rgba)
    elif mat_type == "HammeredMetal":
        return make_hammered_metal(name=name, base_color_rgba=base_color_rgba)
    elif mat_type == "BrushedBlackMetal":
        return make_brushed_black_metal(name=name)
    elif mat_type == "WhiteMetal":
        return make_white_metal(name=name)
    elif mat_type == "BlackGlass":
        return make_black_glass(name=name)
    elif mat_type == "Glass":
        return make_glass(name=name, base_color_rgba=base_color_rgba)
    elif mat_type == "PlasticRough":
        return make_plastic_rough(name=name, base_color=base_color_rgba)
    elif mat_type == "Wood":
        return make_wood(name=name, color=base_color_rgba)
    elif mat_type == "Text":
        return make_screen_emissive(name=name)
    else:
        mat = _new_material(name)
        nt = mat.node_tree
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        _set_principled(bsdf, Metallic=1.0, **{"Base Color": base_color_rgba})
        _connect_output(nt, bsdf)
        return mat


def get_material(registry_key: str, name: str = None) -> bpy.types.Material:
    """Pick a constructor via weighted_sample (uses current numpy.random state)."""

    ctor = weighted_sample(REGISTRY[registry_key])
    return ctor(name=name or registry_key.title())


# ============================================================================
# wear_tear post-processing
# Faithful raw-bpy translations of:
# Both follow the same pattern: walk obj.data.materials, find existing
# MaterialOutput / BSDF, inject a procedural wear graph, reconnect.
# ============================================================================
WEAR_TEAR_PROB = [0.5, 0.5]
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
        # SCALE op uses inputs[3] (Scale) on VectorMath
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
    """stops = [(position, (r,g,b,a)), ...]"""

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
    """Replica of wear_tear/scratches.py:get_scratch_params."""

    return dict(
        angle1=float(np.random.uniform(10.0, 80.0)),
        angle2=float(np.random.uniform(-80.0, -10.0)),
        scratch_scale=log_uniform(5, 80),
        scratch_mask_ratio=log_uniform(0.01, 0.9),
        scratch_mask_noise=log_uniform(5, 40),
        scratch_depth=log_uniform(0.1, 1.0),
    )


def _build_scratch_graph(nt, params):
    """Build the scratch displacement node graph and return the Displacement output socket.

    Faithful translation of wear_tear/scratches.py:scratch_shader.
    """

    n_angle1 = _value_node(nt, params["angle1"])
    n_angle2 = _value_node(nt, params["angle2"])
    n_scale = _value_node(nt, params["scratch_scale"])
    n_mask_ratio = _value_node(nt, params["scratch_mask_ratio"])
    n_mask_noise = _value_node(nt, params["scratch_mask_noise"])
    n_depth = _value_node(nt, params["scratch_depth"])

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # First scratch direction
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

    # Second scratch direction
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

    # Mask noise
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
            continue   # idempotency: already applied
        mat_out = _find_node(nt, "ShaderNodeOutputMaterial")
        if mat_out is None:
            continue
        try:
            disp_out = _build_scratch_graph(nt, params)
            nt.links.new(disp_out, mat_out.inputs["Displacement"])
            # Mark idempotency
            disp_out.node.label = SCRATCH_LABEL
        except Exception as e:
            print(f"  [scratches] failed on {mat.name}: {type(e).__name__}: {e}")


def get_edge_wear_params():
    """Replica of wear_tear/edge_wear.py:get_edge_wear_params."""

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
    """Faithful raw-bpy port of edge_wear.py:shader_edge_tear_free_node_group.

    Returns (final_bsdf_socket, final_displacement_socket).
    """

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

    # Scratch mask noise
    noise_a = _noise_tex(nt, mapping.outputs["Vector"], n_scratch_mask_randomness.outputs[0], detail=1.0)
    cr_a = _color_ramp(nt, _noise_fac_output(noise_a),
                       [(0.4436, (0, 0, 0, 1)), (0.5345, (1, 1, 1, 1))])

    # Bevel edge detection (scratch radius)
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

    # Bevel edge detection (worn-off radius)
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

    # Edge color HSV
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

    # Worn-edge BSDFs (Principled)
    bsdf_worn1 = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix.outputs[2], bsdf_worn1.inputs["Base Color"])
    _set_principled(bsdf_worn1, Metallic=0.3745, Roughness=0.1436,
                    **{"Specular IOR Level": 0.0})

    # Mix the original BSDF with the worn version
    mix_shader = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(cr_d.outputs["Color"], mix_shader.inputs["Fac"])
    nt.links.new(original_bsdf_node.outputs[0], mix_shader.inputs[1])
    nt.links.new(bsdf_worn1.outputs[0], mix_shader.inputs[2])

    # Scratch density via voronoi distance-to-edge (two perpendicular)
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

    # Scale density by 2 for vertical
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

    # Displacement
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
            continue   # idempotency
        mat_out = _find_node(nt, "ShaderNodeOutputMaterial")
        if mat_out is None:
            continue
        # Find original BSDF feeding Surface
        surface_links = mat_out.inputs["Surface"].links
        if not surface_links:
            continue
        original_bsdf = surface_links[0].from_node
        # Find original displacement (if any)
        disp_links = mat_out.inputs["Displacement"].links
        original_disp = disp_links[0].from_node if disp_links else None
        try:
            final_bsdf_socket, final_disp_socket = _build_edge_wear_graph(
                nt, original_bsdf, original_disp, params)
            # Reconnect
            nt.links.new(final_bsdf_socket, mat_out.inputs["Surface"])
            nt.links.new(final_disp_socket, mat_out.inputs["Displacement"])
            # Mark idempotency on the new mix_shader
            final_bsdf_socket.node.label = EDGE_WEAR_LABEL
        except Exception as e:
            print(f"  [edge_wear] failed on {mat.name}: {type(e).__name__}: {e}")


SEED = int(os.environ.get("SEED", 0))

_baked = BAKED_MATERIALS.get(SEED)
if _baked is not None:
    MAT_SURFACE    = get_baked_material(*_baked['Surface'],    name='Surface')
    MAT_BACK       = get_baked_material(*_baked['Back'],       name='Back')
    MAT_BLACKGLASS = get_baked_material(*_baked['BlackGlass'], name='BlackGlass')
    MAT_GLASS      = get_baked_material(*_baked['Glass'],      name='Glass')
    WEAR_DO_SCRATCH  = _baked['do_scratch']
    WEAR_DO_EDGEWEAR = _baked['do_edge_wear']
else:
    seed_all(SEED)
    MAT_SURFACE    = get_material("metals", "Surface")
    MAT_BACK       = get_material("metals", "Back")
    MAT_BLACKGLASS = get_material("appliance_front_maybeglass", "BlackGlass")
    MAT_GLASS      = get_material("appliance_front_glass", "Glass")
    _scratch_p, _edge_wear_p = WEAR_TEAR_PROB
    WEAR_DO_SCRATCH  = (np.random.uniform() <= _scratch_p)
    WEAR_DO_EDGEWEAR = (np.random.uniform() <= _edge_wear_p)

# ---- helpers ---------------------------------------------------------------
def sel_none():
    for o in list(bpy.context.selected_objects): o.select_set(False)
    if bpy.context.active_object: bpy.context.active_object.select_set(False)

def set_active(o):
    bpy.context.view_layer.objects.active = o; o.select_set(True)

def apply_tf(o, loc=False):
    sel_none(); set_active(o)
    bpy.ops.object.transform_apply(location=loc, rotation=True, scale=True)
    sel_none()

def delete(objs):
    if not isinstance(objs, (list, tuple, set)): objs = [objs]
    for o in objs:
        if o and o.name in bpy.data.objects:
            bpy.data.objects.remove(o, do_unlink=True)

def join(objs):
    objs = [o for o in objs if o is not None]
    if not objs: return None
    if len(objs) == 1: return objs[0]
    sel_none()
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.active_object; sel_none(); return o

def box(sx, sy, sz, loc=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.scale = (sx / 2, sy / 2, sz / 2)
    apply_tf(o, loc=True); return o

def bool_sub(target, cutter):
    m = target.modifiers.new("BOOLEAN", "BOOLEAN")
    m.object = cutter; m.operation = "DIFFERENCE"
    if hasattr(m, "use_hole_tolerant"): m.use_hole_tolerant = True
    sel_none(); set_active(target)
    bpy.ops.object.modifier_apply(modifier=m.name); sel_none()
    delete(cutter)

# ---- parameters -----------------------------------------------------------
def sample_params(seed=0):
    np.random.seed(seed)
    D  = float(np.random.uniform(0.5, 0.7))
    W  = float(np.random.uniform(0.6, 1.0))
    H  = float(np.random.uniform(0.35, 0.45))
    PW = float(np.random.uniform(0.2, 0.4))
    MZ = float(np.random.uniform(0.05, 0.1))
    DT = float(np.random.uniform(0.02, 0.04))
    DM = float(np.random.uniform(0.03, 0.1))
    return dict(D=D, W=W, H=H, PW=PW, MZ=MZ, DT=DT, DM=DM)

# ---- sub-assemblies -------------------------------------------------------
def make_text(translation, string, size, offset_scale=0.002):
    bpy.ops.object.text_add(location=(0, 0, 0))
    txt = bpy.context.active_object
    txt.data.body = string; txt.data.size = size
    txt.data.align_x = 'CENTER'; txt.data.align_y = 'BOTTOM_BASELINE'
    txt.data.extrude = offset_scale
    sel_none(); set_active(txt)
    bpy.ops.object.convert(target='MESH')
    txt = bpy.context.active_object
    txt.rotation_euler = (math.pi / 2, 0, math.pi / 2)
    apply_tf(txt)
    txt.location = translation; apply_tf(txt, loc=True)
    return txt

def make_plate(scale_val=0.1):
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0))
    profile = bpy.context.active_object
    pts = profile.data.splines[0].bezier_points
    pts[0].co = (0, 0, 0)
    pts[0].handle_left = (0, 0, 0)
    pts[0].handle_right = (0, 0, 0)
    pts[0].handle_left_type = 'FREE'
    pts[0].handle_right_type = 'FREE'
    pts[1].co = (1, 0, 0.4)
    pts[1].handle_left = (1, 0, 0)
    pts[1].handle_right = (1, 0, 0.4)
    pts[1].handle_left_type = 'FREE'
    pts[1].handle_right_type = 'FREE'
    profile.rotation_euler = (math.pi / 2, 0, 0)
    apply_tf(profile)
    bpy.ops.curve.primitive_bezier_circle_add(location=(0, 0, 0))
    circle = bpy.context.active_object
    circle.data.resolution_u = 32
    circle.data.bevel_mode = 'OBJECT'
    circle.data.bevel_object = profile
    sel_none(); set_active(circle)
    bpy.ops.object.convert(target='MESH')
    plate = bpy.context.active_object
    plate.scale = (scale_val, scale_val, scale_val)
    apply_tf(plate)
    delete(profile)
    return plate

# ---- build -----------------------------------------------------------------
def build(seed=SEED):
    p = sample_params(seed)
    D, W, H = p['D'], p['W'], p['H']
    PW, MZ, DT, DM = p['PW'], p['MZ'], p['DT'], p['DM']
    mat_surface    = MAT_SURFACE
    mat_back       = MAT_BACK
    mat_blackglass = MAT_BLACKGLASS
    mat_glass      = MAT_GLASS

    # === BODY ===
    body = box(D, W, H, (D / 2, W / 2, H / 2))
    cavity = box(D, W - PW, H - MZ, (D/2 + MZ/2, (W - PW)/2 + MZ/2, H/2))
    bool_sub(body, cavity)

    for ix in range(10):
        for iz in range(7):
            bool_sub(body, box(0.03, 0.03, 0.01, (0.115 + ix * 0.04, 0.015, 0.055 + iz * 0.02)))

    body.data.materials.append(mat_back)

    # === DOOR ===
    threshold = (W - PW) + MZ * 0.5
    step = W / 9.0
    n_below = min(9, int(threshold / step))
    win_y_max = n_below * step if n_below > 0 else threshold

    window = box(DT, win_y_max, H, (D + DT / 2, win_y_max / 2, H / 2))
    brand = make_text((D + DT, win_y_max / 2, DM), "BrandName", 0.03)
    # Per-part materials BEFORE joining: window=BlackGlass, brand=Surface metal.
    window.data.materials.append(mat_blackglass)
    brand.data.materials.append(mat_surface)
    door_win = join([window, brand])

    # === PLATE ===
    plate = make_plate(0.1)
    plate.location = (D * 0.5 + MZ / 2, (W - PW) * 0.5 + MZ / 2, MZ / 2)
    apply_tf(plate, loc=True)
    plate.data.materials.append(mat_glass)

    # === CONTROL PANEL ===
    panel_sy = W - win_y_max
    panel_cy = win_y_max + panel_sy / 2
    panel = box(DT, panel_sy, H, (D + DT / 2, panel_cy, H / 2))
    clock = make_text((D + DT, panel_cy, H - DM - 0.1), "12:01", 0.05, 0.005)
    panel.data.materials.append(mat_surface)
    clock.data.materials.append(mat_surface)

    obj = join([body, door_win, plate, panel, clock])
    if obj:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        co = np.array([v.co[:] for v in bm.verts])
        # filter out degenerate (infinity-tagged) verts
        mask = np.linalg.norm(co, axis=-1) < 0.5e5
        pts_min = co[mask].min(axis=0)
        pts_max = co[mask].max(axis=0)
        eps = 1e-4
        bevel_indices = []
        for edge in bm.edges:
            on_bounds = 0
            for j in range(3):
                v0 = edge.verts[0].co[j]; v1 = edge.verts[1].co[j]
                if ((abs(v0 - pts_min[j]) < eps and abs(v1 - pts_min[j]) < eps) or
                    (abs(v0 - pts_max[j]) < eps and abs(v1 - pts_max[j]) < eps)):
                    on_bounds += 1
            if on_bounds >= 2:
                bevel_indices.append(edge.index)
        bm.free()
        if bevel_indices:
            sel_none(); set_active(obj)
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='EDGE')
            bpy.ops.mesh.select_all(action='DESELECT')
            bm2 = bmesh.from_edit_mesh(obj.data)
            bm2.edges.ensure_lookup_table()
            for idx in bevel_indices:
                bm2.edges[idx].select_set(True)
            bmesh.update_edit_mesh(obj.data)
            bpy.ops.mesh.bevel(offset=0.03, offset_pct=0, segments=8, release_confirm=True)
            bpy.ops.object.mode_set(mode='OBJECT')
            sel_none()
        obj.name = "Microwave"

    if obj is not None:
        if WEAR_DO_SCRATCH:  apply_scratches(obj)
        if WEAR_DO_EDGEWEAR: apply_edge_wear(obj)
    return obj

build(SEED)
