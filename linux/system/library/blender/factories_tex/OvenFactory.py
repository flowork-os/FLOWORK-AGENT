# [FL_INDEX: keywords="blender_factory, procedural_3d, OvenFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: OvenFactory | Category: factories_tex
# Prompt: A 3D model of a freestanding gas kitchen oven range rendered from a three-quarter perspective. The appliance features a gray stone-textured metallic body, a black glass cooktop with four cast-iron gas burner grates arranged in a grid, a back control panel with round knobs and a digital clock display showing "12:01", and a lower oven compartment door with a horizontal bar handle.

import os
import bpy, math, string
import numpy as np
import random, colorsys

# Helpers
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
    """py:metal_hsv (simplified — drops natural-base lookup).

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
    """py:bark_hsv (uses a small hardcoded wood palette)."""

    wood_hex = ["#8b5a2b", "#a0522d", "#cd853f", "#d2691e", "#6b4423", "#5d4037", "#7b3f00"]
    h_str = wood_hex[np.random.randint(0, len(wood_hex))].lstrip("#")
    r, g, b = (int(h_str[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    return colorsys.rgb_to_hsv(r, g, b)

def weighted_sample(reg):
    """py:weighted_sample.

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

def _set_input(node, key, value):
    """Set an input socket value, preferring name lookup but falling back to index."""

    try:
        node.inputs[key].default_value = value
    except (KeyError, TypeError):
        if isinstance(key, int):
            raise
        # try common renames
        for alt in (key.replace(" IOR Level", ""), key + " IOR Level"):
            if alt in node.inputs:
                node.inputs[alt].default_value = value
                return
        raise

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

# Base material constructors
def make_metal_basic(name="MetalBasic", color_hsv=None) -> bpy.types.Material:
    """py:shader_metal."""

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
        **{"Base Color": hsv2rgba(color_hsv or metal_hsv())},
    )
    nt.links.new(fc.outputs["Value"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

def make_brushed_metal(name="BrushedMetal", base_color_hsv=None) -> bpy.types.Material:
    """py:shader_brushed_metal.

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
    hsv_node.inputs["Color"].default_value = hsv2rgba(base_color_hsv)
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

def make_galvanized_metal(name="GalvanizedMetal", base_color_hsv=None) -> bpy.types.Material:
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
        **{"Specular IOR Level": 0.0, "Base Color": hsv2rgba(base_color_hsv)},
    )
    nt.links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

def make_hammered_metal(name="HammeredMetal", base_color_hsv=None) -> bpy.types.Material:
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
        **{"Specular IOR Level": 0.0, "Base Color": hsv2rgba(base_color_hsv), "Roughness": 0.1},
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

def make_glass(name="Glass") -> bpy.types.Material:
    """Re-impl of materials/ceramic/glass.py:shader_glass (non-window variant)."""

    mat = _new_material(name)
    nt = mat.node_tree
    glass = nt.nodes.new("ShaderNodeBsdfPrincipled")
    if "Roughness" in glass.inputs:
        glass.inputs["Roughness"].default_value = 0.02
    if "IOR" in glass.inputs:
        glass.inputs["IOR"].default_value = 1.5
    if "Transmission Weight" in glass.inputs:
        glass.inputs["Transmission Weight"].default_value = 1.0
    elif "Transmission" in glass.inputs:
        glass.inputs["Transmission"].default_value = 1.0
        if "Transmission Weight" in glass.inputs:
            glass.inputs["Transmission Weight"].default_value = 1.0
        elif "Transmission" in glass.inputs:
            glass.inputs["Transmission"].default_value = 1.0
    # Tint via 50/50 white-or-light-color
    if np.random.uniform() < 0.5:
        color = (1.0, 1.0, 1.0, 1.0)
    else:
        color = hsv2rgba((np.random.uniform(0, 1), np.random.uniform(0.05, 0.25), 1.0))
    if "Color" in glass.inputs:
        glass.inputs["Base Color"].default_value = color
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

def get_material(registry_key: str, name: str = None) -> bpy.types.Material:
    """Pick a constructor via weighted_sample (uses current numpy.random state)."""

    ctor = weighted_sample(REGISTRY[registry_key])
    return ctor(name=name or registry_key.title())

# wear_tear post-processing
# Faithful raw-bpy translations of:
# Both follow the same pattern: walk obj.data.materials, find existing
# MaterialOutput / BSDF, inject a procedural wear graph, reconnect.
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

def apply_wear_tear(obj):
    """

    Two independent 50% probability gates: scratches and edge_wear.
    """

    if obj is None or obj.data is None or not hasattr(obj.data, "materials"):
        return
    scratch_p, edge_p = WEAR_TEAR_PROB
    if np.random.uniform() <= scratch_p:
        apply_scratches(obj)
    if np.random.uniform() <= edge_p:
        apply_edge_wear(obj)

SEED = int(os.environ.get('SEED', 0))

# ----------------------------------------------------------------------------
# geometry which uses int_hash((factory_seed, i)) in create_asset. We mirror this
# by sampling all materials + wear_tear gates on a clean seed_all(SEED) state here,
# then hand off to build() which re-seeds internally for geometry.
seed_all(SEED)
MAT_SURFACE    = get_material('metals', 'Surface')
MAT_BACK       = get_material('metals', 'Back')
MAT_WHITEMETAL = get_material('metals', 'WhiteMetal')
MAT_BLACKGLASS = get_material('appliance_front_maybeglass', 'SuperBlackGlass')
MAT_GLASS      = get_material('appliance_front_glass', 'Glass')
# wear_tear probability gates (50/50 each, mirroring factory.get_material_params)
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

def delete(objs):
    if not isinstance(objs, (list, tuple, set)):
        objs = [objs]
    for o in objs:
        if o and o.name in bpy.data.objects:
            bpy.data.objects.remove(o, do_unlink=True)

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
    sel_none()
    return o

def box(sx, sy, sz, loc=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.active_object
    o.scale = (sx / 2, sy / 2, sz / 2)
    apply_tf(o, loc=True)
    return o

def spawn_cube(size=1, location=(0, 0, 0), scale=(1, 1, 1)):
    """Mimic butil.spawn_cube: cube of given size, location, scale."""

    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    o = bpy.context.active_object
    o.scale = scale
    apply_tf(o, loc=True)
    return o

def spawn_cylinder(radius, depth, location=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=depth, location=location)
    o = bpy.context.active_object
    apply_tf(o, loc=True)
    return o

def bool_union(target, cutter):
    m = target.modifiers.new("BOOLEAN", "BOOLEAN")
    m.object = cutter
    m.operation = "UNION"
    sel_none(); set_active(target)
    bpy.ops.object.modifier_apply(modifier=m.name)
    sel_none()
    delete(cutter)

def bool_sub(target, cutter):
    m = target.modifiers.new("BOOLEAN", "BOOLEAN")
    m.object = cutter
    m.operation = "DIFFERENCE"
    if hasattr(m, "use_hole_tolerant"):
        m.use_hole_tolerant = True
    sel_none(); set_active(target)
    bpy.ops.object.modifier_apply(modifier=m.name)
    sel_none()
    delete(cutter)

def cyl_between(p0, p1, radius, verts=12):
    p0 = np.array(p0, dtype=float)
    p1 = np.array(p1, dtype=float)
    mid = (p0 + p1) / 2.0
    diff = p1 - p0
    length = np.linalg.norm(diff)
    if length < 1e-9:
        return None
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=length, vertices=verts,
                                        location=(mid[0], mid[1], mid[2]))
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

# ---- gn_cube: box with corner at Pos --------------------------------------
def gn_cube(size, pos):
    sx, sy, sz = size
    px, py, pz = pos
    cx = sx * 0.5 + px
    cy = sy * 0.5 + py
    cz = sz * 0.5 + pz
    return box(sx, sy, sz, (cx, cy, cz))

def gn_hollow_cube(size, pos, thickness, sw1=False, sw2=False, sw3=False,
                   sw4=False, sw5=False, sw6=False):
    """Hollow box with switchable walls. Switch=True removes that wall."""

    sx, sy, sz = size
    px, py, pz = pos
    t = thickness
    hx, hy, hz = sx*0.5, sy*0.5, sz*0.5
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

# ---- gn_handle: two standoff cubes + crossbar -----------------------------
def gn_handle(width, length, thickness):
    s1 = box(width, width, width, (0, 0, width / 2))
    s2 = box(width, width, width, (0, length, width / 2))
    bar_sy = length + width
    bar_cz = width + thickness / 2
    bar = box(width, bar_sy, thickness, (0, length / 2, bar_cz))
    handle = join([s1, s2, bar])
    # Bevel to match add_bevel(offset=0.01)
    sel_none(); set_active(handle)
    bpy.ops.object.modifier_add(type='BEVEL')
    bpy.context.object.modifiers["Bevel"].width = 0.01
    bpy.context.object.modifiers["Bevel"].segments = 8
    bpy.ops.object.modifier_apply(modifier="Bevel")
    sel_none()
    return handle

# ---- gn_text: string -> mesh with rotation and translation ----------------
def gn_text(translation, string, size, offset_scale=0.002):
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

# ---- nodegroup_o: thin ring (outline circle) ------------------------------
def gn_o(size):
    """Thin ring (knob outline) as a torus."""

    bpy.ops.mesh.primitive_torus_add(
        major_radius=size, minor_radius=0.0015,
        major_segments=32, minor_segments=8,
        location=(0, 0, 0.001))
    ring = bpy.context.active_object
    apply_tf(ring, loc=True)
    return ring

# ---- oven rack: flat grid of tubes ----------------------------------------
def gn_oven_rack(width, height, radius, amount):
    """Oven rack: rectangular frame + parallel cross-lines swept with tube profile.
    Width = extent in X, Height = extent in Y (naming follows original).
    """

    rods = []

    # Rectangular frame (quadrilateral)
    hw = width / 2
    hh = height / 2
    corners = [(-hw, -hh, 0), (hw, -hh, 0), (hw, hh, 0), (-hw, hh, 0)]
    for i in range(4):
        r = cyl_between(corners[i], corners[(i + 1) % 4], radius)
        if r:
            rods.append(r)

    if amount > 0:
        for sign in (1, -1):
            dx = sign * (width * 0.5) / amount
            for i in range(amount + 1):
                r = cyl_between((i * dx, -hh, 0), (i * dx, hh, 0), radius)
                if r:
                    rods.append(r)

    if not rods:
        return None
    return join(rods)

# ---- heater discs (non-gas top) -------------------------------------------
def make_heater(width, depth, radius_ratio, arrangement_ratio):
    """Grid of flat discs on top surface."""

    minimum = min(width, depth)
    radius = minimum * radius_ratio
    arrangement_dist = minimum * arrangement_ratio
    n_cols = max(1, int(math.floor(width / arrangement_dist)))
    n_rows = max(1, int(math.floor(depth / arrangement_dist)))

    discs = []
    col_step = width / n_cols
    row_step = depth / n_rows
    for row in range(n_rows):
        for col in range(n_cols):
            x = row_step * 0.5 + row * row_step
            y = col_step * 0.5 + col * col_step
            bpy.ops.mesh.primitive_cylinder_add(
                radius=radius, depth=0.001, vertices=32,
                location=(x, y, 0))
            d = bpy.context.active_object
            apply_tf(d, loc=True)
            discs.append(d)
    if not discs:
        return None
    return join(discs)

# ---- gas grates -----------------------------------------------------------
def _spoke_cube(loc, seg_len, thickness, angle):
    """Create a rotated spoke cube at loc with correct rotation around its center.
    Unlike spawn_cube, this sets location+scale+rotation BEFORE applying transforms,
    so the rotation happens around the object's origin (loc), not (0,0,0)."""

    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.active_object
    obj.scale = (seg_len, thickness, thickness)
    obj.rotation_euler[2] = angle
    apply_tf(obj, loc=True, rot=True, scale=True)
    return obj

def make_gas_grates(width, depth, grate_width, grate_depth, height, thickness,
                    grids, branches, center_ratio, middle_ratio):
    high_height = height + thickness * 0.9
    all_grates = []
    n_grids = len(grids)

    for i, n in enumerate(grids):
        cubes = []
        # Two parallel edge bars for this grid cell
        cubes.append(spawn_cube(
            size=1,
            location=(depth / 2,
                      grate_width / n_grids * i + (width - grate_width) / 2 + thickness / 2,
                      height),
            scale=(grate_depth + thickness, thickness, thickness)))
        cubes.append(spawn_cube(
            size=1,
            location=(depth / 2,
                      grate_width / n_grids * (i + 1) + (width - grate_width) / 2 - thickness / 2,
                      height),
            scale=(grate_depth + thickness, thickness, thickness)))

        # Cross bars within the cell
        for j in range(n + 1):
            cubes.append(spawn_cube(
                size=1,
                location=(grate_depth / n * j + (depth - grate_depth) / 2,
                          grate_width / n_grids * (i + 0.5) + (width - grate_width) / 2,
                          high_height),
                scale=(thickness, grate_width / n_grids, thickness)))

        # Radial spokes around burner centers
        for j in range(n):
            min_dist = min(grate_width / n_grids / 2, grate_depth / n / 2)
            line_len = max(grate_width / n_grids / 2, grate_depth / n / 2) - min_dist
            center_dist = min_dist * center_ratio
            middle_dist = min_dist * middle_ratio

            if grate_width / n_grids / 2 > grate_depth / n / 2:
                x_center, y_center = center_dist, line_len + center_dist
                x_middle, y_middle = middle_dist, line_len + middle_dist
                x_full, y_full = min_dist, line_len + min_dist
            else:
                x_center, y_center = center_dist + line_len, center_dist
                x_middle, y_middle = middle_dist + line_len, middle_dist
                x_full, y_full = min_dist + line_len, min_dist

            center_xy = (
                grate_depth / n * (j + 0.5) + (depth - grate_depth) / 2,
                grate_width / n_grids * (i + 0.5) + (width - grate_width) / 2,
            )

            for k in range(branches):
                angle = 2 * np.pi / branches * k

                # Inner spoke segment
                x0 = x_center * np.cos(angle)
                y0 = y_center * np.sin(angle)
                x1 = x_middle * np.cos(angle)
                y1 = y_middle * np.sin(angle)
                seg_len = ((x0 - x1)**2 + (y0 - y1)**2)**0.5
                if seg_len > 1e-6:
                    loc = (center_xy[0] + (x0 + x1) / 2,
                           center_xy[1] + (y0 + y1) / 2,
                           high_height)
                    actual_angle = np.arctan2(y1 - y0, x1 - x0)
                    cubes.append(_spoke_cube(loc, seg_len, thickness, actual_angle))

                # Outer spoke segment (to edge)
                x0, y0 = x1, y1
                if x_full - abs(x0) < y_full - abs(y0):
                    x1_new = x_full * np.sign(x0) if x0 != 0 else x_full
                    y1_new = y0
                else:
                    x1_new = x0
                    y1_new = y_full * np.sign(y0) if y0 != 0 else y_full
                seg_len = ((x0 - x1_new)**2 + (y0 - y1_new)**2)**0.5
                if seg_len > 1e-6:
                    loc = (center_xy[0] + (x0 + x1_new) / 2,
                           center_xy[1] + (y0 + y1_new) / 2,
                           high_height)
                    actual_angle = np.arctan2(y1_new - y0, x1_new - x0)
                    cubes.append(_spoke_cube(loc, seg_len, thickness, actual_angle))

            # Center cylinder (burner ring)
            all_grates.append(spawn_cylinder(
                center_dist + thickness, thickness / 2,
                location=(center_xy[0], center_xy[1], height)))

        # Join all cubes (not boolean union - avoids artifacts; VOXEL remesh
        # handles overlapping geometry correctly)
        grid_obj = join(cubes)

        # Remesh + smooth
        if grid_obj:
            sel_none(); set_active(grid_obj)
            bpy.ops.object.modifier_add(type="REMESH")
            bpy.context.object.modifiers["Remesh"].mode = "VOXEL"
            bpy.context.object.modifiers["Remesh"].voxel_size = 0.004
            bpy.ops.object.modifier_apply(modifier="Remesh")
            bpy.ops.object.modifier_add(type="SMOOTH")
            bpy.context.object.modifiers["Smooth"].iterations = 8
            bpy.context.object.modifiers["Smooth"].factor = 1
            bpy.ops.object.modifier_apply(modifier="Smooth")
            sel_none()
            all_grates.append(grid_obj)

    # Join all grid cells + cylinders
    result = join(all_grates)
    return result

# ---- parameters ------------------------------------------------------------
def _clip_gaussian(mean, std, min_val, max_val, max_tries=20):
    """Replicate clip_gaussian to consume the same random state."""

    i = 0
    while True:
        val = np.random.normal(mean, std)
        if min_val <= val <= max_val:
            return val
        if i == max_tries:
            return float(np.clip(val, min_val, max_val))
        i += 1

def _generate_text():
    """Replicate generate_text to consume the same random state."""

    _char_set = list(string.ascii_lowercase + string.ascii_uppercase + string.digits)
    _weights = np.concatenate([
        1.5 * np.ones(len(string.ascii_lowercase)),
        0.5 * np.ones(len(string.ascii_uppercase)),
        0.5 * np.ones(len(string.digits)),
    ])
    _weights /= _weights.sum()
    n = int(_clip_gaussian(3, 7, 2, 15))
    return "".join(np.random.choice(_char_set, size=n, replace=True, p=_weights))

def sample_params(seed=0):
    np.random.seed(seed)
    depth = 1 + np.random.normal(0, 0.1)
    width = 1 + np.random.normal(0, 0.1)
    height = 1 + np.random.normal(0, 0.1)
    door_thickness = np.random.uniform(0.05, 0.1) * depth
    door_rotation = 0
    rack_radius = np.random.uniform(0.01, 0.02) * depth
    rack_h_amount = np.random.randint(2, 4)
    rack_d_amount = np.random.randint(4, 6)
    panel_height = np.random.uniform(0.2, 0.4) * height
    panel_thickness = np.random.uniform(0.15, 0.25) * depth
    botton_amount = np.random.randint(1, 3) * 2
    botton_radius = np.random.uniform(0.05, 0.1) * width
    botton_thickness = np.random.uniform(0.02, 0.04) * depth
    heat_radius_ratio = np.random.uniform(0.1, 0.2)
    brand_name = _generate_text()  # Must consume same random state as original

    use_gas = int(np.random.randint(2))
    n_grids = int(np.random.randint(2, 5))
    grids = [int(np.random.randint(1, 4)) for _ in range(n_grids)]
    branches = 2 * int(np.random.randint(2, 9))
    grate_thickness = float(np.random.uniform(0.01, 0.03))
    center_ratio = float(np.random.uniform(0.05, 0.15))
    middle_ratio = float(np.random.uniform(0.5, 0.7))

    return {
        "Depth": depth,
        "Width": width,
        "Height": height,
        "DoorThickness": door_thickness,
        "DoorRotation": door_rotation,
        "RackRadius": rack_radius,
        "RackHAmount": rack_h_amount,
        "RackDAmount": rack_d_amount,
        "PanelHeight": panel_height,
        "PanelThickness": panel_thickness,
        "BottonAmount": botton_amount,
        "BottonRadius": botton_radius,
        "BottonThickness": botton_thickness,
        "HeaterRadiusRatio": heat_radius_ratio,
        "BrandName": brand_name,
        "UseGas": use_gas,
        "Grids": grids,
        "Branches": branches,
        "GrateThickness": grate_thickness,
        "CenterRatio": center_ratio,
        "MiddleRatio": middle_ratio,
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
    panel_height = p["PanelHeight"]
    panel_thickness = p["PanelThickness"]
    botton_amount = p["BottonAmount"]
    botton_radius = p["BottonRadius"]
    botton_thickness = p["BottonThickness"]
    heat_radius_ratio = p["HeaterRadiusRatio"]
    use_gas = p["UseGas"]

    parts = []

    # ======== 1. Body: hollow cube ========
    # Size=(Depth, Width, Height), Pos=(0,0,0), Thickness=DoorThickness
    # Switch2=True (remove top), Switch4=True (remove front-X wall)
    body = gn_hollow_cube(
        size=(D, W, H), pos=(0, 0, 0), thickness=dt,
        sw1=False, sw2=True, sw3=False, sw4=True, sw5=False, sw6=False,
    )
    if body:
        body.data.materials.append(MAT_BACK)
        parts.append(body)

    # ======== 2. Door assembly (cube + handle + brand text) ========
    # Door: black glass front; handle: surface metal; brand: surface metal
    door = gn_cube(size=(dt, W, H), pos=(D, 0, 0))
    door.data.materials.append(MAT_BLACKGLASS)

    width_h = W * 0.05
    length_h = W * 0.8
    thickness_h = width_h * 0.5
    handle = gn_handle(width_h, length_h, thickness_h)
    handle.rotation_euler = (0, math.pi / 2, 0)
    apply_tf(handle, rot=True)
    handle.location = (D + dt, W * 0.5 + length_h * (-0.5), H * 0.92)
    apply_tf(handle, loc=True)
    handle.data.materials.append(MAT_SURFACE)

    brand_text = gn_text((D + dt, W * 0.5, 0.03), p["BrandName"], H * 0.05)
    if brand_text:
        brand_text.data.materials.append(MAT_SURFACE)
        door_assembly = join([door, handle, brand_text])
    else:
        door_assembly = join([door, handle])
    parts.append(door_assembly)

    # ======== 3. Oven racks ========
    rack_w = D - dt * 2.1
    rack_h = W - dt * 2.1
    for ri in range(rack_h_amount + 1):
        z_range = H - dt * 2
        rack_z = (ri + 1) * z_range / (rack_h_amount + 1)
        rack = gn_oven_rack(rack_w, rack_h, rack_radius, rack_d_amount)
        if rack:
            rack.location = (D * 0.5, W * 0.5, rack_z)
            apply_tf(rack, loc=True)
            rack.data.materials.append(MAT_WHITEMETAL)
            parts.append(rack)

    # ======== 4. Top slab + heater discs ========
    top_slab = gn_cube(size=(D + dt, W, dt), pos=(0, 0, H))
    top_slab.data.materials.append(MAT_SURFACE)

    if not use_gas:
        heater_depth = (D + dt) - panel_thickness
        arrangement_ratio = heat_radius_ratio * 2.0 + 0.1
        heater = make_heater(W, heater_depth, heat_radius_ratio, arrangement_ratio)
        if heater:
            heater.location = (panel_thickness, 0, dt + H)
            apply_tf(heater, loc=True)
            heater.data.materials.append(MAT_GLASS)
        top_parts = [top_slab]
        if heater:
            top_parts.append(heater)
        top_assembly = join(top_parts)
    else:
        top_assembly = top_slab

    parts.append(top_assembly)

    # ======== 5. Panel section (tilted by -10 deg) ========
    panel_body = gn_cube(size=(panel_thickness, W, panel_height), pos=(0, 0, H + dt))
    panel_body.data.materials.append(MAT_SURFACE)

    # Panel bounding box center Z (for text/button placement)
    panel_min_z = H + dt
    panel_max_z = H + dt + panel_height
    panel_center_z = (panel_min_z + panel_max_z) / 2.0

    # Clock text "12:01" on panel
    clock_text = gn_text(
        (panel_thickness, W * 0.5, panel_center_z),
        "12:01", panel_height * 0.2)
    if clock_text:
        clock_text.data.materials.append(MAT_WHITEMETAL)

    # Buttons/knobs assembly
    # Original uses DuplicateElements with Amount = BottonAmount+2,
    # creating (BottonAmount+2) copies with DuplicateIndex 0..Amount-1.
    # Position: y = (DuplicateIndex+1) * Width / (Amount+1)
    # Middle knobs are deleted where DupIdx > half-1.01 AND DupIdx < half+0.99

    knob_count = botton_amount + 2  # = DuplicateElements Amount
    y_spacing = W / (knob_count + 1)
    half_val = knob_count * 0.5

    button_parts = []
    for bi in range(knob_count):  # DuplicateIndex 0..knob_count-1
        # Delete middle knobs: DupIdx > half-1.01 AND DupIdx < half+0.99
        if bi > half_val - 1.01 and bi < half_val + 0.99:
            continue

        y_offset = (bi + 1) * y_spacing

        # Knob cylinder
        bpy.ops.mesh.primitive_cylinder_add(
            radius=botton_radius, depth=botton_thickness,
            vertices=32, location=(0, 0, botton_thickness / 2))
        knob_cyl = bpy.context.active_object
        apply_tf(knob_cyl, loc=True)

        # Ring outline
        ring = gn_o(botton_radius + 0.005)

        knob = join([knob_cyl, ring])

        # Transform: translation=(PanelThickness, 0, panelCenterZ), rotation=(0, pi/2, 0)
        knob.rotation_euler = (0, math.pi / 2, 0)
        apply_tf(knob, rot=True)
        knob.location = (panel_thickness, y_offset, panel_center_z)
        apply_tf(knob, loc=True)

        # Text labels around the knob
        text_size = botton_radius * 0.25
        small_offset = panel_height * 0.05

        # "Off" text: at (PanelThickness, y_offset, panelCenterZ + BottonRadius*1.0 + small_offset)
        off_z = panel_center_z + botton_radius * 1.0 + small_offset
        off_text = gn_text((panel_thickness, y_offset, off_z), "Off", text_size)

        # "High" text: at (PanelThickness, y_offset + BottonRadius*0.7 + small_offset,
        #                   panelCenterZ + BottonRadius*0.7 + small_offset)
        high_off = botton_radius * 0.7 + small_offset
        high_text = gn_text(
            (panel_thickness, y_offset + high_off,
             panel_center_z + high_off),
            "High", text_size)

        # "Low" text: at (PanelThickness, y_offset + BottonRadius*(-0.7) + (-small_offset),
        #                  panelCenterZ + BottonRadius*0.7 + small_offset)
        low_off_y = botton_radius * (-0.7) + (-small_offset)
        low_text = gn_text(
            (panel_thickness, y_offset + low_off_y,
             panel_center_z + high_off),
            "Low", text_size)

        # "1" text: at (PanelThickness + BottonThickness, y_offset, panelCenterZ)
        one_text = gn_text(
            (panel_thickness + botton_thickness, y_offset, panel_center_z),
            "1", botton_radius, botton_thickness * 0.1)

        # Assign materials to sub-parts before joining into btn_group
        knob.data.materials.append(MAT_SURFACE)
        for t in (off_text, high_text, low_text, one_text):
            if t:
                t.data.materials.append(MAT_WHITEMETAL)
        parts_for_btn = [knob] + [t for t in (off_text, high_text, low_text, one_text) if t]
        btn_group = join(parts_for_btn)
        button_parts.append(btn_group)

    # Join panel body + clock + all buttons
    panel_parts = [panel_body, clock_text] + button_parts
    panel_assembly = join(panel_parts)

    # Tilt panel by -10 degrees around Y, pivot at Z=Height
    # Convert to instance-like behavior: translate so pivot is at origin, rotate, translate back
    if panel_assembly:
        # Move pivot to Z=Height (in local space, shift down by H)
        panel_assembly.location = (0, 0, -H)
        apply_tf(panel_assembly, loc=True)
        panel_assembly.rotation_euler = (0, -0.1745, 0)
        apply_tf(panel_assembly, rot=True)
        panel_assembly.location = (0, 0, H)
        apply_tf(panel_assembly, loc=True)
        parts.append(panel_assembly)

    # ======== 6. Gas grates (if use_gas) ========
    if use_gas:
        grate_width_val = W * 0.8
        gas_depth = D + 2 * dt
        grate_depth_val = gas_depth * 0.6
        grate_thickness_val = p["GrateThickness"]
        grate_z = H + dt - grate_thickness_val

        grates = make_gas_grates(
            W, gas_depth, grate_width_val, grate_depth_val,
            grate_z, grate_thickness_val,
            p["Grids"], p["Branches"],
            p["CenterRatio"], p["MiddleRatio"])
        if grates:
            grates.data.materials.append(MAT_SURFACE)

        # Boolean-subtract a hollow from the body for the grate recess
        hollow = spawn_cube(
            size=1,
            location=(gas_depth / 2, W / 2, H + dt),
            scale=(grate_depth_val + grate_thickness_val,
                   grate_width_val + grate_thickness_val,
                   grate_thickness_val * 2))
        # Add bevel to the hollow
        sel_none(); set_active(hollow)
        bpy.ops.object.modifier_add(type="BEVEL")
        bpy.context.object.modifiers["Bevel"].segments = 8
        bpy.context.object.modifiers["Bevel"].width = grate_thickness_val
        bpy.ops.object.modifier_apply(modifier="Bevel")
        sel_none()

        # We need to boolean-subtract hollow from the main body parts
        # First join all current parts, then subtract
        main_obj = join(parts)
        parts = []

        sel_none(); set_active(main_obj)
        m = main_obj.modifiers.new("BOOLEAN", "BOOLEAN")
        m.object = hollow
        m.operation = "DIFFERENCE"
        if hasattr(m, "use_hole_tolerant"):
            m.use_hole_tolerant = True
        bpy.ops.object.modifier_apply(modifier=m.name)
        sel_none()
        delete(hollow)

        # Join grates with the body
        if grates:
            parts = [main_obj, grates]
        else:
            parts = [main_obj]

    # ======== Join all ========
    obj = join(parts)
    if obj:
        obj.name = "Oven"
        if WEAR_DO_SCRATCH:  apply_scratches(obj)
        if WEAR_DO_EDGEWEAR: apply_edge_wear(obj)
    return obj

build(SEED)

