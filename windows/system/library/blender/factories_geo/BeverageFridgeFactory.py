# [FL_INDEX: keywords="blender_factory, procedural_3d, BeverageFridgeFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: BeverageFridgeFactory | Category: factories_geo
# Prompt: A compact, cube-shaped beverage refrigerator rendered as a 3D model. The mini fridge has a dark brown body with a smooth dark glass top surface and a vertical metallic door handle on the right side. The unit is a small under-counter style fridge with slightly reflective surfaces and subtle shadow cast beneath it, set against a plain white background.

import os
import bpy, math
import numpy as np
import random, colorsys


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
    """


    Original: 20% chance returns metal_natural_hsv (sampled from a hex color list);
    80% returns (uniform(0,1), uniform(0.3,0.6), log_uniform(0.02,0.5)).
    We approximate metal_natural with a desaturated dark sample.
    """

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
    """

    `reg` is a list of (constructor_callable, weight) tuples.
    """

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
    """


    Original chains 3 noise textures, mixes, mapranges and an HSV node. We use a
    simplified single-axis-stretched noise to fake the brushed look while keeping
    the math close to the original mapranges.
    """

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
        'Surface': ('HammeredMetal', (0.026475, 0.017968, 0.021766, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('GalvanizedMetal', (0.088339, 0.040658, 0.046775, 1.0)),
        'Back': ('GrainedMetal', (0.107286, 0.098531, 0.044695, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    1: {
        'Surface': ('GalvanizedMetal', (0.024895, 0.033282, 0.037841, 1.0)),
        'Front': ('BrushedMetal', (0.185719, 0.335869, 0.165349, 1.0)),
        'Handle': ('WhiteMetal', None),
        'Back': ('MetalBasic', (0.034550, 0.029275, 0.023780, 1.0)),
        'do_scratch': False, 'do_edge_wear': False,
    },
    2: {
        'Surface': ('BrushedMetal', (0.116347, 0.100952, 0.090133, 1.0)),
        'Front': ('GrainedMetal', (0.232902, 0.206732, 0.197067, 1.0)),
        'Handle': ('BrushedMetal', (0.035839, 0.040645, 0.027147, 1.0)),
        'Back': ('BrushedMetal', (0.084888, 0.094696, 0.048094, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    3: {
        'Surface': ('MetalBasic', (0.108716, 0.115828, 0.176357, 1.0)),
        'Front': ('MetalBasic', (0.053155, 0.082558, 0.040623, 1.0)),
        'Handle': ('GrainedMetal', (0.365711, 0.182228, 0.208655, 1.0)),
        'Back': ('MetalBasic', (0.110165, 0.163855, 0.124552, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    4: {
        'Surface': ('BrushedMetal', (0.244351, 0.215975, 0.208785, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('MetalBasic', (0.104378, 0.251327, 0.195028, 1.0)),
        'Back': ('GrainedMetal', (0.044902, 0.096796, 0.107233, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    5: {
        'Surface': ('MetalBasic', (0.178317, 0.158587, 0.154300, 1.0)),
        'Front': ('MetalBasic', (0.025203, 0.031810, 0.019141, 1.0)),
        'Handle': ('Wood', None),
        'Back': ('BrushedMetal', (0.120706, 0.120546, 0.188333, 1.0)),
        'do_scratch': False, 'do_edge_wear': False,
    },
    6: {
        'Surface': ('BrushedMetal', (0.075624, 0.034337, 0.036758, 1.0)),
        'Front': ('BlackGlass', (0.006800, 0.006800, 0.006800, 1.0)),
        'Handle': ('Wood', None),
        'Back': ('BrushedMetal', (0.113487, 0.065096, 0.115844, 1.0)),
        'do_scratch': False, 'do_edge_wear': False,
    },
    7: {
        'Surface': ('BrushedMetal', (0.085718, 0.054515, 0.071441, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('Wood', None),
        'Back': ('BrushedMetal', (0.110239, 0.107732, 0.107784, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    8: {
        'Surface': ('BrushedMetal', (0.040448, 0.024264, 0.026803, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('Wood', None),
        'Back': ('BrushedMetal', (0.116420, 0.167432, 0.088554, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    9: {
        'Surface': ('MetalBasic', (0.189819, 0.130667, 0.148070, 1.0)),
        'Front': ('MetalBasic', (0.139901, 0.284544, 0.186022, 1.0)),
        'Handle': ('BrushedMetal', (0.319464, 0.161373, 0.213052, 1.0)),
        'Back': ('MetalBasic', (0.318604, 0.332653, 0.208595, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    10: {
        'Surface': ('MetalBasic', (0.191899, 0.105403, 0.204174, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('WhiteMetal', None),
        'Back': ('MetalBasic', (0.088100, 0.075653, 0.030084, 1.0)),
        'do_scratch': False, 'do_edge_wear': False,
    },
    11: {
        'Surface': ('GrainedMetal', (0.055372, 0.039101, 0.036821, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('MetalBasic', (0.156920, 0.153553, 0.174643, 1.0)),
        'Back': ('HammeredMetal', (0.089844, 0.201623, 0.135680, 1.0)),
        'do_scratch': False, 'do_edge_wear': False,
    },
    12: {
        'Surface': ('MetalBasic', (0.020146, 0.008948, 0.012696, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('MetalBasic', (0.193669, 0.206893, 0.210255, 1.0)),
        'Back': ('MetalBasic', (0.039776, 0.028083, 0.057405, 1.0)),
        'do_scratch': False, 'do_edge_wear': False,
    },
    13: {
        'Surface': ('GalvanizedMetal', (0.039975, 0.038150, 0.061225, 1.0)),
        'Front': ('MetalBasic', (0.090924, 0.097856, 0.037798, 1.0)),
        'Handle': ('BrushedMetal', (0.120899, 0.119584, 0.128170, 1.0)),
        'Back': ('MetalBasic', (0.008267, 0.020001, 0.018585, 1.0)),
        'do_scratch': False, 'do_edge_wear': False,
    },
    14: {
        'Surface': ('MetalBasic', (0.126428, 0.148989, 0.165992, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('BrushedMetal', (0.121697, 0.118985, 0.191072, 1.0)),
        'Back': ('BrushedMetal', (0.064547, 0.066161, 0.027335, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    15: {
        'Surface': ('MetalBasic', (0.164426, 0.118308, 0.268707, 1.0)),
        'Front': ('MetalBasic', (0.231301, 0.136043, 0.136875, 1.0)),
        'Handle': ('BrushedMetal', (0.138263, 0.127330, 0.113958, 1.0)),
        'Back': ('HammeredMetal', (0.042039, 0.046521, 0.073238, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    16: {
        'Surface': ('MetalBasic', (0.160528, 0.172041, 0.178741, 1.0)),
        'Front': ('MetalBasic', (0.175322, 0.163255, 0.149682, 1.0)),
        'Handle': ('WhiteMetal', None),
        'Back': ('BrushedMetal', (0.126384, 0.148696, 0.155807, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    17: {
        'Surface': ('MetalBasic', (0.118126, 0.077555, 0.059568, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('MetalBasic', (0.035645, 0.076921, 0.051176, 1.0)),
        'Back': ('GrainedMetal', (0.078055, 0.100275, 0.115586, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    18: {
        'Surface': ('BrushedBlackMetal', (0.016700, 0.016700, 0.016700, 1.0)),
        'Front': ('GalvanizedMetal', (0.052147, 0.036928, 0.034757, 1.0)),
        'Handle': ('MetalBasic', (0.165860, 0.106218, 0.155735, 1.0)),
        'Back': ('GalvanizedMetal', (0.019743, 0.039485, 0.036713, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    19: {
        'Surface': ('GrainedMetal', (0.032634, 0.027970, 0.017952, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('PlasticRough', (0.189414, 0.157205, 0.405040, 1.0)),
        'Back': ('MetalBasic', (0.081669, 0.108680, 0.158448, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    20: {
        'Surface': ('GalvanizedMetal', (0.095636, 0.101501, 0.106594, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('Wood', None),
        'Back': ('GrainedMetal', (0.082786, 0.039394, 0.082375, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    21: {
        'Surface': ('GrainedMetal', (0.060791, 0.043586, 0.074541, 1.0)),
        'Front': ('MetalBasic', (0.246846, 0.378075, 0.167778, 1.0)),
        'Handle': ('MetalBasic', (0.066678, 0.115352, 0.064823, 1.0)),
        'Back': ('BrushedMetal', (0.043758, 0.046360, 0.074934, 1.0)),
        'do_scratch': False, 'do_edge_wear': False,
    },
    22: {
        'Surface': ('GalvanizedMetal', (0.016547, 0.013122, 0.020399, 1.0)),
        'Front': ('BrushedMetal', (0.164225, 0.144705, 0.236940, 1.0)),
        'Handle': ('Wood', None),
        'Back': ('MetalBasic', (0.085701, 0.138723, 0.159892, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    23: {
        'Surface': ('BrushedMetal', (0.287957, 0.466458, 0.244016, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('GalvanizedMetal', (0.073876, 0.037080, 0.019603, 1.0)),
        'Back': ('MetalBasic', (0.179104, 0.179104, 0.179104, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    24: {
        'Surface': ('HammeredMetal', (0.053557, 0.023949, 0.042878, 1.0)),
        'Front': ('BlackGlass', (0.006800, 0.006800, 0.006800, 1.0)),
        'Handle': ('BrushedMetal', (0.144634, 0.073378, 0.097993, 1.0)),
        'Back': ('GalvanizedMetal', (0.102118, 0.049949, 0.111810, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    25: {
        'Surface': ('BrushedMetal', (0.069633, 0.087793, 0.106897, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('GalvanizedMetal', (0.042291, 0.094171, 0.052582, 1.0)),
        'Back': ('BrushedMetal', (0.120935, 0.065998, 0.066808, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    26: {
        'Surface': ('BrushedMetal', (0.042934, 0.031850, 0.051446, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('MetalBasic', (0.095438, 0.050539, 0.073918, 1.0)),
        'Back': ('MetalBasic', (0.025016, 0.032559, 0.051702, 1.0)),
        'do_scratch': False, 'do_edge_wear': False,
    },
    27: {
        'Surface': ('MetalBasic', (0.026159, 0.016015, 0.036484, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('Wood', None),
        'Back': ('HammeredMetal', (0.273813, 0.304474, 0.159887, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    28: {
        'Surface': ('GrainedMetal', (0.200839, 0.199854, 0.178619, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('WhiteMetal', None),
        'Back': ('MetalBasic', (0.048434, 0.077713, 0.079715, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    29: {
        'Surface': ('GalvanizedMetal', (0.143680, 0.181079, 0.111237, 1.0)),
        'Front': ('GalvanizedMetal', (0.268608, 0.113658, 0.113599, 1.0)),
        'Handle': ('Wood', None),
        'Back': ('MetalBasic', (0.140427, 0.108104, 0.158474, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    30: {
        'Surface': ('MetalBasic', (0.189907, 0.380747, 0.404107, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('GalvanizedMetal', (0.015498, 0.010910, 0.022108, 1.0)),
        'Back': ('MetalBasic', (0.044651, 0.067180, 0.035828, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    31: {
        'Surface': ('BrushedMetal', (0.047342, 0.029123, 0.035285, 1.0)),
        'Front': ('MetalBasic', (0.046666, 0.026092, 0.047615, 1.0)),
        'Handle': ('MetalBasic', (0.098709, 0.175774, 0.122107, 1.0)),
        'Back': ('BrushedMetal', (0.062568, 0.065948, 0.017373, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    32: {
        'Surface': ('HammeredMetal', (0.102984, 0.192654, 0.161295, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('PlasticRough', (0.341473, 0.161219, 0.257574, 1.0)),
        'Back': ('MetalBasic', (0.013500, 0.033736, 0.027910, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    33: {
        'Surface': ('HammeredMetal', (0.058513, 0.021401, 0.013645, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('GrainedMetal', (0.025119, 0.028568, 0.038218, 1.0)),
        'Back': ('BrushedBlackMetal', (0.016700, 0.016700, 0.016700, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    34: {
        'Surface': ('GalvanizedMetal', (0.031216, 0.019205, 0.030989, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('PlasticRough', (0.152645, 0.314148, 0.397173, 1.0)),
        'Back': ('GrainedMetal', (0.158755, 0.149679, 0.142375, 1.0)),
        'do_scratch': False, 'do_edge_wear': False,
    },
    35: {
        'Surface': ('MetalBasic', (0.094499, 0.084991, 0.083861, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('Wood', None),
        'Back': ('GrainedMetal', (0.476323, 0.308051, 0.202762, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    36: {
        'Surface': ('MetalBasic', (0.092966, 0.035757, 0.036939, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('WhiteMetal', None),
        'Back': ('BrushedMetal', (0.024756, 0.032024, 0.041130, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    37: {
        'Surface': ('GalvanizedMetal', (0.037683, 0.016237, 0.020938, 1.0)),
        'Front': ('GrainedMetal', (0.030867, 0.021132, 0.025264, 1.0)),
        'Handle': ('Wood', None),
        'Back': ('GrainedMetal', (0.030832, 0.051532, 0.051706, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    38: {
        'Surface': ('BrushedMetal', (0.122191, 0.066119, 0.110364, 1.0)),
        'Front': ('GalvanizedMetal', (0.199393, 0.433140, 0.440115, 1.0)),
        'Handle': ('MetalBasic', (0.099121, 0.164525, 0.088034, 1.0)),
        'Back': ('MetalBasic', (0.390444, 0.291496, 0.180420, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    39: {
        'Surface': ('BrushedMetal', (0.190208, 0.420576, 0.302855, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('WhiteMetal', None),
        'Back': ('GrainedMetal', (0.313319, 0.214769, 0.297312, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    40: {
        'Surface': ('BrushedMetal', (0.282672, 0.254146, 0.367402, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('Wood', None),
        'Back': ('BrushedBlackMetal', (0.016700, 0.016700, 0.016700, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    41: {
        'Surface': ('BrushedMetal', (0.055072, 0.038653, 0.026903, 1.0)),
        'Front': ('HammeredMetal', (0.037427, 0.051561, 0.077736, 1.0)),
        'Handle': ('BrushedMetal', (0.145702, 0.181467, 0.217468, 1.0)),
        'Back': ('MetalBasic', (0.105474, 0.102459, 0.103100, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    42: {
        'Surface': ('GrainedMetal', (0.051533, 0.053253, 0.034347, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('Wood', None),
        'Back': ('MetalBasic', (0.318548, 0.178378, 0.192481, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    43: {
        'Surface': ('BrushedMetal', (0.040739, 0.025712, 0.017926, 1.0)),
        'Front': ('MetalBasic', (0.214444, 0.301861, 0.204361, 1.0)),
        'Handle': ('Wood', None),
        'Back': ('BrushedMetal', (0.258556, 0.106260, 0.221119, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    44: {
        'Surface': ('GalvanizedMetal', (0.341796, 0.142527, 0.193374, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('GrainedMetal', (0.333149, 0.309076, 0.187359, 1.0)),
        'Back': ('BrushedMetal', (0.122462, 0.080255, 0.115031, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    45: {
        'Surface': ('MetalBasic', (0.146342, 0.081790, 0.085383, 1.0)),
        'Front': ('MetalBasic', (0.027666, 0.040717, 0.041524, 1.0)),
        'Handle': ('PlasticRough', (0.011578, 0.015412, 0.004440, 1.0)),
        'Back': ('GrainedMetal', (0.093990, 0.120306, 0.067694, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    46: {
        'Surface': ('BrushedMetal', (0.039996, 0.024936, 0.056689, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('GrainedMetal', (0.036194, 0.040003, 0.052515, 1.0)),
        'Back': ('BrushedMetal', (0.046875, 0.071354, 0.028744, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    47: {
        'Surface': ('MetalBasic', (0.021923, 0.024155, 0.036336, 1.0)),
        'Front': ('GalvanizedMetal', (0.187904, 0.086524, 0.083234, 1.0)),
        'Handle': ('MetalBasic', (0.035426, 0.019350, 0.025597, 1.0)),
        'Back': ('MetalBasic', (0.047269, 0.022524, 0.031097, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    48: {
        'Surface': ('MetalBasic', (0.030871, 0.059120, 0.052358, 1.0)),
        'Front': ('MetalBasic', (0.144610, 0.143302, 0.143752, 1.0)),
        'Handle': ('MetalBasic', (0.172844, 0.166228, 0.253340, 1.0)),
        'Back': ('BrushedMetal', (0.273330, 0.426478, 0.215156, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    49: {
        'Surface': ('HammeredMetal', (0.018842, 0.024177, 0.009945, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('GrainedMetal', (0.045989, 0.057385, 0.077496, 1.0)),
        'Back': ('BrushedMetal', (0.033078, 0.044937, 0.030431, 1.0)),
        'do_scratch': False, 'do_edge_wear': False,
    },
    50: {
        'Surface': ('GrainedMetal', (0.054880, 0.029197, 0.043192, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('BrushedMetal', (0.059204, 0.108068, 0.076137, 1.0)),
        'Back': ('MetalBasic', (0.011820, 0.018592, 0.023664, 1.0)),
        'do_scratch': False, 'do_edge_wear': False,
    },
    51: {
        'Surface': ('BrushedMetal', (0.018398, 0.023321, 0.013454, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('GrainedMetal', (0.208797, 0.138636, 0.098888, 1.0)),
        'Back': ('MetalBasic', (0.103360, 0.082207, 0.156498, 1.0)),
        'do_scratch': False, 'do_edge_wear': True,
    },
    52: {
        'Surface': ('BrushedMetal', (0.075824, 0.179607, 0.131785, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('Wood', None),
        'Back': ('GrainedMetal', (0.138339, 0.064220, 0.090838, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    53: {
        'Surface': ('MetalBasic', (0.066150, 0.046388, 0.038480, 1.0)),
        'Front': ('BlackGlass', (0.006800, 0.006800, 0.006800, 1.0)),
        'Handle': ('BrushedMetal', (0.076726, 0.115576, 0.141381, 1.0)),
        'Back': ('MetalBasic', (0.115859, 0.107470, 0.108062, 1.0)),
        'do_scratch': False, 'do_edge_wear': False,
    },
    54: {
        'Surface': ('GrainedMetal', (0.024042, 0.033905, 0.056955, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('MetalBasic', (0.031972, 0.021601, 0.053879, 1.0)),
        'Back': ('BrushedMetal', (0.070220, 0.091057, 0.040350, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    55: {
        'Surface': ('GrainedMetal', (0.062166, 0.034252, 0.036662, 1.0)),
        'Front': ('MetalBasic', (0.010828, 0.021361, 0.014844, 1.0)),
        'Handle': ('Wood', None),
        'Back': ('MetalBasic', (0.081882, 0.094539, 0.052274, 1.0)),
        'do_scratch': False, 'do_edge_wear': False,
    },
    56: {
        'Surface': ('BrushedMetal', (0.020910, 0.039238, 0.046982, 1.0)),
        'Front': ('HammeredMetal', (0.015727, 0.010907, 0.022434, 1.0)),
        'Handle': ('MetalBasic', (0.352314, 0.233088, 0.484460, 1.0)),
        'Back': ('GrainedMetal', (0.017402, 0.031168, 0.023005, 1.0)),
        'do_scratch': False, 'do_edge_wear': False,
    },
    57: {
        'Surface': ('HammeredMetal', (0.053688, 0.069283, 0.084448, 1.0)),
        'Front': ('BlackGlass', (0.006800, 0.006800, 0.006800, 1.0)),
        'Handle': ('GalvanizedMetal', (0.212409, 0.159244, 0.163911, 1.0)),
        'Back': ('MetalBasic', (0.203884, 0.168415, 0.141545, 1.0)),
        'do_scratch': True, 'do_edge_wear': True,
    },
    58: {
        'Surface': ('MetalBasic', (0.246230, 0.243520, 0.131926, 1.0)),
        'Front': ('Glass', (1.000000, 1.000000, 1.000000, 1.0)),
        'Handle': ('WhiteMetal', None),
        'Back': ('GrainedMetal', (0.013788, 0.020446, 0.025829, 1.0)),
        'do_scratch': True, 'do_edge_wear': False,
    },
    59: {
        'Surface': ('BrushedMetal', (0.118040, 0.108089, 0.103232, 1.0)),
        'Front': ('BlackGlass', (0.006800, 0.006800, 0.006800, 1.0)),
        'Handle': ('GrainedMetal', (0.183849, 0.269539, 0.113119, 1.0)),
        'Back': ('MetalBasic', (0.051240, 0.080925, 0.079384, 1.0)),
        'do_scratch': False, 'do_edge_wear': False,
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


SEED = int(os.environ.get("SEED", "0"))
_baked = BAKED_MATERIALS.get(SEED)
if _baked is not None:
    MAT_SURFACE = get_baked_material(*_baked['Surface'], name='Surface')
    MAT_FRONT   = get_baked_material(*_baked['Front'],   name='Front')
    MAT_HANDLE  = get_baked_material(*_baked['Handle'],  name='Handle')
    MAT_BACK    = get_baked_material(*_baked['Back'],    name='Back')
    WEAR_DO_SCRATCH  = _baked['do_scratch']
    WEAR_DO_EDGEWEAR = _baked['do_edge_wear']
else:
    # Fallback for seeds outside baked range
    seed_all(SEED)
    MAT_SURFACE    = get_material('metals', 'Surface')
    MAT_FRONT      = get_material('appliance_front_maybeglass', 'Front')
    MAT_HANDLE     = get_material('appliance_handle', 'Handle')
    MAT_BACK       = get_material('metals', 'Back')
    _scratch_p, _edge_wear_p = WEAR_TEAR_PROB
    WEAR_DO_SCRATCH  = (np.random.uniform() <= _scratch_p)
    WEAR_DO_EDGEWEAR = (np.random.uniform() <= _edge_wear_p)


# ---- helpers ---------------------------------------------------------------
def sel_none():
    for o in list(bpy.context.selected_objects):
        o.select_set(False)
    if bpy.context.active_object:
        bpy.context.active_object.select_set(False)

def set_active(o):
    bpy.context.view_layer.objects.active = o
    o.select_set(True)

def apply_tf(o, loc=False, rot=True, scale=True):
    sel_none(); set_active(o)
    bpy.ops.object.transform_apply(location=loc, rotation=rot, scale=scale)
    sel_none()

def join(objs):
    objs = [o for o in objs if o is not None]
    if not objs:
        return None
    if len(objs) == 1:
        return objs[0]
    sel_none()
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.active_object
    o.location = (0, 0, 0)
    o.rotation_euler = (0, 0, 0)
    o.scale = (1, 1, 1)
    sel_none()
    return o

def box(sx, sy, sz, loc=(0, 0, 0)):
    """Create a box centered at *loc* with full extents (sx, sy, sz)."""

    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.scale = (sx / 2, sy / 2, sz / 2)
    apply_tf(o, loc=True)
    return o

def cyl_between(p0, p1, radius, verts=12):
    """Create a cylinder (rod) from point p0 to point p1 with given radius."""

    p0 = np.array(p0, dtype=float)
    p1 = np.array(p1, dtype=float)
    mid = (p0 + p1) / 2.0
    diff = p1 - p0
    length = np.linalg.norm(diff)
    if length < 1e-9:
        return None
    bpy.ops.mesh.primitive_cylinder_add(
        radius=radius, depth=length, vertices=verts,
        location=(mid[0], mid[1], mid[2]),
    )
    o = bpy.context.active_object
    up = np.array([0, 0, 1], dtype=float)
    d = diff / length
    cross = np.cross(up, d)
    dot = np.dot(up, d)
    if np.linalg.norm(cross) < 1e-9:
        if dot < 0:
            o.rotation_euler = (math.pi, 0, 0)
    else:
        angle = math.acos(np.clip(dot, -1, 1))
        axis = cross / np.linalg.norm(cross)
        o.rotation_mode = 'AXIS_ANGLE'
        o.rotation_axis_angle = (angle, axis[0], axis[1], axis[2])
    apply_tf(o, loc=True, rot=True, scale=True)
    return o

# ---- nodegroup_cube equivalent ---------------------------------------------
def gn_cube(size, pos):
    """Box of *size* with corner at pos (translated by size*0.5 + pos)."""

    sx, sy, sz = size
    px, py, pz = pos
    cx = sx * 0.5 + px
    cy = sy * 0.5 + py
    cz = sz * 0.5 + pz
    return box(sx, sy, sz, (cx, cy, cz))

# ---- nodegroup_hollow_cube equivalent --------------------------------------
def gn_hollow_cube(size, pos, thickness, sw1=False, sw2=False, sw3=False,
                   sw4=False, sw5=False, sw6=False):
    """Create up to 6 wall slabs forming a hollow box. Switch=True removes that wall."""

    sx, sy, sz = size
    px, py, pz = pos
    t = thickness
    hx, hy, hz = sx * 0.5, sy * 0.5, sz * 0.5
    # (switch, w_sx, w_sy, w_sz, cx, cy, cz)
    walls = [
        (sw3, t,  sy-2*t, sz-2*t, t/2+px,    hy+py,  hz-pz   ),  # left X wall
        (sw2, sx, sy-2*t, t,      hx+px,      hy+py,  sz-t/2-pz), # top Z slab
        (sw1, sx, sy-2*t, t,      hx+px,      hy+py,  t/2+pz  ),  # bottom Z slab
        (sw4, t,  sy-2*t, sz-2*t, sx-t/2,     hy+py,  hz-pz   ),  # right X wall
        (sw5, sx, t,      sz,     hx+px,      t/2+py, hz+pz   ),  # front Y wall
        (sw6, sx, t,      sz,     hx+px,      sy-t/2, hz+pz   ),  # back Y wall
    ]
    parts = [box(wx, wy, wz, (cx, cy, cz)) for sw, wx, wy, wz, cx, cy, cz in walls if not sw]
    return join(parts) if parts else None

# ---- nodegroup_handle equivalent -------------------------------------------
def gn_handle(width, length, thickness):
    """Two cube standoffs + one crossbar, with beveled edges."""

    s1 = box(width, width, width, (0, 0, width / 2))
    s2 = box(width, width, width, (0, length, width / 2))
    bar_sy = length + width
    bar_cz = width + thickness / 2
    bar = box(width, bar_sy, thickness, (0, length / 2, bar_cz))
    handle = join([s1, s2, bar])
    sel_none(); set_active(handle)
    bpy.ops.object.modifier_add(type='BEVEL')
    bpy.context.object.modifiers["Bevel"].width = 0.01
    bpy.context.object.modifiers["Bevel"].segments = 8
    bpy.ops.object.modifier_apply(modifier="Bevel")
    sel_none()
    return handle

# ---- nodegroup_oven_rack equivalent ----------------------------------------
def gn_oven_rack(rack_width, rack_height, radius, amount):
    """Reproduce nodegroup_oven_rack.

    Creates a rectangular outline (quadrilateral) of rack_width x rack_height,
    plus two sets of parallel lines (each duplicated `amount` times) going from
    bottom to top of the rectangle, offset along X. All swept with circular
    cross-section of given radius.

    The quadrilateral is centered at origin in XY. Lines go from
    (0, -rack_height/2, 0) to (0, rack_height/2, 0), duplicated and offset.
    """

    rods = []
    W = rack_width
    H = rack_height

    # Quadrilateral outline (rectangle W x H centered at origin)
    corners = [
        (-W / 2, -H / 2, 0),
        ( W / 2, -H / 2, 0),
        ( W / 2,  H / 2, 0),
        (-W / 2,  H / 2, 0),
    ]
    for i in range(4):
        r = cyl_between(corners[i], corners[(i + 1) % 4], radius)
        if r:
            rods.append(r)

    if amount > 0:
        for sign in (1, -1):
            dx = sign * (W * 0.5) / amount
            for i in range(amount + 1):
                r = cyl_between((i * dx, -H / 2, 0), (i * dx, H / 2, 0), radius)
                if r:
                    rods.append(r)

    if not rods:
        return None
    return join(rods)

# ---- nodegroup_text equivalent ---------------------------------------------
def gn_text(translation, string, size, offset_scale=0.002):
    """String-to-curves, fill, extrude, transform."""

    bpy.ops.object.text_add(location=(0, 0, 0))
    txt = bpy.context.active_object
    txt.data.body = string
    txt.data.size = size
    txt.data.align_x = 'CENTER'
    txt.data.align_y = 'BOTTOM_BASELINE'
    txt.data.extrude = offset_scale
    sel_none(); set_active(txt)
    bpy.ops.object.convert(target='MESH')
    mesh_obj = bpy.context.active_object
    mesh_obj.rotation_euler = (math.pi / 2, 0, math.pi / 2)
    apply_tf(mesh_obj, rot=True)
    tx, ty, tz = translation
    mesh_obj.location = (tx, ty, tz)
    apply_tf(mesh_obj, loc=True)
    return mesh_obj

# ---- parameters ------------------------------------------------------------
def sample_params(seed=0):
    np.random.seed(seed)
    depth = 1 + np.random.normal(0, 0.1)
    width = 1 + np.random.normal(0, 0.1)
    height = 1 + np.random.normal(0, 0.1)
    door_thickness = np.random.uniform(0.05, 0.1) * depth
    rack_radius = np.random.uniform(0.01, 0.02) * depth
    rack_h_amount = np.random.randint(2, 4)
    rack_d_amount = np.random.randint(4, 6)
    return {
        "Depth": depth,
        "Width": width,
        "Height": height,
        "DoorThickness": door_thickness,
        "RackRadius": rack_radius,
        "RackHAmount": rack_h_amount,
        "RackDAmount": rack_d_amount,
        "BrandName": "BrandName",
    }

# ---- build -----------------------------------------------------------------
def build(seed=SEED):
    p = sample_params(seed)
    D = p["Depth"]
    W = p["Width"]
    H = p["Height"]
    dt = p["DoorThickness"]
    rack_radius = p["RackRadius"]
    rack_h_amount = p["RackHAmount"]
    rack_d_amount = p["RackDAmount"]

    parts = []

    # ======== 1. Body: hollow cube ========
    # Size=(Depth, Width, Height), Thickness=DoorThickness
    # Switch2=True (remove top), Switch4=True (remove front-X wall)
    body = gn_hollow_cube(
        size=(D, W, H), pos=(0, 0, 0), thickness=dt,
        sw1=False, sw2=True, sw3=False, sw4=True, sw5=False, sw6=False,
    )
    if body:
        body.data.materials.append(MAT_BACK)
        parts.append(body)

    # ======== 2. Door: cube at front ========
    door = gn_cube(size=(dt, W, H), pos=(D, 0, 0))
    door.data.materials.append(MAT_FRONT)
    parts.append(door)

    # ======== 3. Handle ========
    width_h = W * 0.05
    length_h = H * 0.8
    thickness_h = width_h * 0.5
    handle = gn_handle(width_h, length_h, thickness_h)
    handle.rotation_euler = (0, math.pi / 2, 0)
    apply_tf(handle, rot=True)
    handle.rotation_euler = (-math.pi / 2, 0, 0)
    apply_tf(handle, rot=True)
    handle.location = (D + dt, W * 0.1, H * 0.9)
    apply_tf(handle, loc=True)
    handle.data.materials.append(MAT_HANDLE)
    parts.append(handle)

    # ======== 4. Brand text ========
    text_trans = (D + dt, W * 0.5, 0.03)
    text_size = H * 0.05
    brand_text = gn_text(text_trans, p["BrandName"], text_size)
    if brand_text:
        brand_text.data.materials.append(MAT_SURFACE)
        parts.append(brand_text)

    # ======== 5. Oven racks ========
    rack_w = D - dt * 2.1
    rack_h = W - dt * 2.1
    z_range = H - dt * 2
    for ri in range(rack_h_amount + 1):
        rack_z = (ri + 1) * z_range / (rack_h_amount + 1)
        rack = gn_oven_rack(rack_w, rack_h, rack_radius, rack_d_amount)
        if rack:
            rack.location = (D * 0.5, W * 0.5, rack_z)
            apply_tf(rack, loc=True)
            rack.data.materials.append(MAT_SURFACE)
            parts.append(rack)

    # ======== 6. Top / heater panel ========
    top = gn_cube(size=(D + dt, W, dt), pos=(0, 0, H))
    top.data.materials.append(MAT_SURFACE)
    parts.append(top)

    # ======== Join all ========
    obj = join(parts)
    if obj:
        obj.name = "BeverageFridge"
        if WEAR_DO_SCRATCH:  apply_scratches(obj)
        if WEAR_DO_EDGEWEAR: apply_edge_wear(obj)
    return obj

build(SEED)
