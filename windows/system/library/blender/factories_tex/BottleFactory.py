# [FL_INDEX: keywords="blender_factory, procedural_3d, BottleFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: BottleFactory | Category: factories_tex
# Prompt: A 3D model of a beverage bottle rendered from a three-quarter perspective. The bottle features a tapered conical body with a narrow cylindrical neck, a small rounded cap, and a decorative label band around the mid-section with colorful printed pattern.

"""Standalone textured BottleFactory -- mesh + materials in one file.

  - body: weighted_sample(material_assignments.plastics)  (Plastic/PlasticRough/PlasticTranslucent)
  - wrap: text.Text()() label/sticker material (matplotlib-generated image texture)
  - cap:  weighted_sample(material_assignments.metals)     (MetalBasic/BrushedMetal/GalvanizedMetal/
                                                            GrainedMetal/HammeredMetal/BrushedBlackMetal)
  - wear_tear: commented out in source -- NOT applied.
Geometry copied verbatim from objects_blender/tableware/BottleFactory.py.

Run: [SEED=0] blender --background --python BottleFactory.py
"""
import colorsys
import hashlib
import io
import math
import os
import random
import string
from collections.abc import Sized

import bpy
import numpy as np
from numpy.random import uniform

# Utilities

SEED = int(os.environ.get("SEED", "0"))

def seed_all(seed):
    np.random.seed(seed)
    random.seed(seed)

def int_hash(x):
    m = hashlib.md5()
    for s in x:
        m.update(str(s).encode("utf-8"))
    return abs(int(m.hexdigest(), 16)) % (2**32 - 1)

def log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def hsv2rgba(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(float(h) % 1.0,
                                   max(0.0, min(1.0, float(s))),
                                   max(0.0, min(1.0, float(v))))
    return (r, g, b, 1.0)

def metal_hsv():
    
    if np.random.uniform() < 0.2:
        # Approximate metal_natural_hsv: dark, slightly tinted
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

# Material helpers

def _new_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat

def _set_principled(bsdf, **kw):
    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Coat Weight": ("Coat Weight", "Clearcoat"),
    }
    for k, v in kw.items():
        if v is None:
            continue
        for name in aliases.get(k, (k,)):
            if name in bsdf.inputs:
                bsdf.inputs[name].default_value = v
                break

def _noise_fac(noise_node):
    """Get Fac/Factor output of a noise texture (Blender 4.4/5.0 compat)."""

    return (noise_node.outputs.get("Fac")
            or noise_node.outputs.get("Factor")
            or noise_node.outputs[0])

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

def _connect_output(nt, bsdf, displacement=None):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    if displacement is not None:
        nt.links.new(displacement, out.inputs["Displacement"])
    return out

# PLASTIC shaders  (body material)

def make_plastic_rough(name="PlasticRough", base_color=None, clear=False):
    """Translation of plastic_rough.py -> nodegroup_plastics + shader_rough_plastic."""

    roughness = float(np.random.uniform(0, 1))
    seed_val = float(np.random.uniform(-1000, 1000))
    if base_color is None:
        if clear:
            base_color = hsv2rgba(0, 0, log_uniform(0.02, 0.8))
        else:
            base_color = hsv2rgba(np.random.uniform(0, 1),
                                  np.random.uniform(0.5, 0.8),
                                  log_uniform(0.01, 0.5))

    mat = _new_material(name)
    nt = mat.node_tree
    ln = nt.links.new

    # --- Inline nodegroup_plastics ---
    # MapRange: roughness [0,1] -> [0.05, 0.25]
    mapped_rough = 0.05 + roughness * (0.25 - 0.05)

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = base_color
    bsdf.inputs["Roughness"].default_value = mapped_rough

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.noise_dimensions = "4D"
    noise.inputs["Scale"].default_value = 1.0 * 2000.0
    noise.inputs["W"].default_value = seed_val
    noise.inputs["Detail"].default_value = 15.0
    noise.inputs["Distortion"].default_value = 2.0
    ln(tex_coord.outputs["Object"], noise.inputs["Vector"])

    mul1 = nt.nodes.new("ShaderNodeMath")
    mul1.operation = "MULTIPLY"
    mul1.inputs[0].default_value = mapped_rough
    mul1.inputs[1].default_value = 0.4
    # result = mapped_rough * 0.4

    mul2 = nt.nodes.new("ShaderNodeMath")
    mul2.operation = "MULTIPLY"
    ln(_noise_fac(noise), mul2.inputs[0])
    ln(mul1.outputs[0], mul2.inputs[1])

    mul3 = nt.nodes.new("ShaderNodeMath")
    mul3.operation = "MULTIPLY"
    ln(mul2.outputs[0], mul3.inputs[0])
    mul3.inputs[1].default_value = 0.003

    # Displacement
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    ln(mul3.outputs[0], disp.inputs["Height"])

    _connect_output(nt, bsdf, disp.outputs[0])
    return mat

def make_plastic_translucent(name="PlasticTranslucent", base_color=None, clear=False):
    """Translation of plastic_translucent.py -> shader_translucent_plastic."""

    blend_val = float(random.uniform(0.2, 0.4))
    ior_val = float(random.uniform(1.2, 1.6))
    if base_color is None:
        if clear:
            base_color = hsv2rgba(0, 0, log_uniform(0.4, 0.8))
        else:
            base_color = hsv2rgba(np.random.uniform(0, 1),
                                  np.random.uniform(0.5, 0.8),
                                  log_uniform(0.4, 0.8))

    mat = _new_material(name)
    nt = mat.node_tree
    ln = nt.links.new

    layer_weight = nt.nodes.new("ShaderNodeLayerWeight")
    layer_weight.inputs["Blend"].default_value = blend_val

    glass = nt.nodes.new("ShaderNodeBsdfPrincipled")
    glass.inputs["Base Color"].default_value = base_color
    glass.inputs["Roughness"].default_value = 0.2
    glass.inputs["IOR"].default_value = ior_val
    if "Transmission Weight" in glass.inputs:
        glass.inputs["Transmission Weight"].default_value = 1.0
    elif "Transmission" in glass.inputs:
        glass.inputs["Transmission"].default_value = 1.0

    glossy = nt.nodes.new("ShaderNodeBsdfGlossy")
    glossy.inputs["Roughness"].default_value = 0.2

    mix_shader = nt.nodes.new("ShaderNodeMixShader")
    ln(layer_weight.outputs["Fresnel"], mix_shader.inputs["Fac"])
    ln(glass.outputs["BSDF"], mix_shader.inputs[1])
    ln(glossy.outputs["BSDF"], mix_shader.inputs[2])

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(mix_shader.outputs[0], out.inputs["Surface"])

    # Enable blend for EEVEE
    try:
        mat.blend_method = "HASHED"
    except Exception:
        pass
    return mat

def make_plastic(name="Plastic", clear=None):
    
    if clear is None:
        clear = np.random.uniform() < 0.2
    is_rough = float(np.random.uniform(0, 1))
    is_translucent = float(np.random.uniform(0, 1))
    if is_rough > is_translucent:
        return make_plastic_rough(name, clear=clear)
    else:
        return make_plastic_translucent(name, clear=clear)

# Plastics registry
plastics_registry = [
    (make_plastic, 1.0),
    (make_plastic_rough, 1.0),
    (make_plastic_translucent, 1.0),
]

# METAL shaders  (cap material)

def make_metal_basic(name="MetalBasic", color_hsv=None):
    """Translation of metal_basic.py -> shader_metal."""

    mat = _new_material(name)
    nt = mat.node_tree
    ln = nt.links.new

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = float(np.random.uniform(10, 25))
    ln(tex_coord.outputs["Object"], noise.inputs["Vector"])

    fc = _build_float_curve(
        nt, _noise_fac(noise),
        [(0, float(np.random.uniform(0, 0.2))),
         (1, float(np.random.uniform(0.4, 0.7)))],
    )

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    hsv = color_hsv or metal_hsv()
    _set_principled(
        bsdf,
        Metallic=1.0,
        **{"Specular IOR Level": float(np.random.uniform(0.5, 1.0))},
        **{"Base Color": hsv2rgba(*hsv)},
    )
    ln(fc.outputs["Value"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

def make_brushed_metal(name="BrushedMetal", color_hsv=None):
    """Translation of brushed_metal.py -> shader_brushed_metal (inline nodegroup)."""

    seed_val = float(np.random.uniform(-1000, 1000))
    hsv = color_hsv or metal_hsv()
    base_color = hsv2rgba(*hsv)
    scale = 1.0

    mat = _new_material(name)
    nt = mat.node_tree
    ln = nt.links.new

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # Mapping 1: scale (0.2, 0.2, 5)
    map1 = nt.nodes.new("ShaderNodeMapping")
    map1.inputs["Scale"].default_value = (0.2, 0.2, 5.0)
    ln(tex_coord.outputs["Object"], map1.inputs["Vector"])

    mul_scale = scale * 100.0
    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    noise1.noise_dimensions = "4D"
    noise1.inputs["Scale"].default_value = mul_scale
    noise1.inputs["W"].default_value = seed_val
    noise1.inputs["Detail"].default_value = 15.0
    noise1.inputs["Roughness"].default_value = 0.4
    noise1.inputs["Distortion"].default_value = 0.1
    ln(map1.outputs["Vector"], noise1.inputs["Vector"])

    # Mapping 2: scale (1, 1, 20)
    map2 = nt.nodes.new("ShaderNodeMapping")
    map2.inputs["Scale"].default_value = (1.0, 1.0, 20.0)
    ln(tex_coord.outputs["Object"], map2.inputs["Vector"])

    noise_low = nt.nodes.new("ShaderNodeTexNoise")
    noise_low.noise_dimensions = "4D"
    noise_low.inputs["Scale"].default_value = 0.1
    noise_low.inputs["W"].default_value = seed_val
    noise_low.inputs["Detail"].default_value = 15.0
    noise_low.inputs["Roughness"].default_value = 0.0
    ln(tex_coord.outputs["Object"], noise_low.inputs["Vector"])

    mix_vec = nt.nodes.new("ShaderNodeMix")
    mix_vec.data_type = "RGBA"
    mix_vec.inputs[0].default_value = 0.2
    ln(map2.outputs["Vector"], mix_vec.inputs[6])
    ln(noise_low.outputs["Color"], mix_vec.inputs[7])

    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    noise2.noise_dimensions = "4D"
    noise2.inputs["Scale"].default_value = mul_scale
    noise2.inputs["W"].default_value = seed_val
    noise2.inputs["Detail"].default_value = 15.0
    noise2.inputs["Roughness"].default_value = 0.6
    noise2.inputs["Distortion"].default_value = 0.1
    ln(mix_vec.outputs[2], noise2.inputs["Vector"])

    # Darken mix of two noise Fac outputs
    darken = nt.nodes.new("ShaderNodeMix")
    darken.data_type = "RGBA"
    darken.blend_type = "DARKEN"
    darken.inputs[0].default_value = 1.0
    ln(_noise_fac(noise1), darken.inputs[6])
    ln(_noise_fac(noise2), darken.inputs[7])

    # MapRange: darken -> [0.4,0.6] => [0.8,1.2] for value
    mr_val = nt.nodes.new("ShaderNodeMapRange")
    mr_val.inputs[1].default_value = 0.4
    mr_val.inputs[2].default_value = 0.6
    mr_val.inputs[3].default_value = 0.8
    mr_val.inputs[4].default_value = 1.2
    ln(darken.outputs[2], mr_val.inputs[0])

    hue_sat = nt.nodes.new("ShaderNodeHueSaturation")
    ln(mr_val.outputs["Result"], hue_sat.inputs["Value"])
    hue_sat.inputs["Color"].default_value = base_color

    # MapRange: darken -> [0.4,0.6] => [0.2,0.3] for roughness
    mr_rough = nt.nodes.new("ShaderNodeMapRange")
    mr_rough.inputs[1].default_value = 0.4
    mr_rough.inputs[2].default_value = 0.6
    mr_rough.inputs[3].default_value = 0.2
    mr_rough.inputs[4].default_value = 0.3
    ln(darken.outputs[2], mr_rough.inputs[0])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(hue_sat.outputs["Color"], bsdf.inputs["Base Color"])
    _set_principled(bsdf, Metallic=1.0, **{"Specular IOR Level": 0.0})
    ln(mr_rough.outputs["Result"], bsdf.inputs["Roughness"])

    _connect_output(nt, bsdf)
    return mat

def make_galvanized_metal(name="GalvanizedMetal", color_hsv=None):
    """Translation of galvanized_metal.py."""

    seed_val = float(np.random.uniform(-1000, 1000))
    hsv = color_hsv or metal_hsv()
    base_color = hsv2rgba(*hsv)
    scale = 1.0

    mat = _new_material(name)
    nt = mat.node_tree
    ln = nt.links.new

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.noise_dimensions = "4D"
    noise.inputs["Scale"].default_value = scale * 5.0
    noise.inputs["W"].default_value = seed_val
    noise.inputs["Detail"].default_value = 15.0
    noise.inputs["Roughness"].default_value = 0.4
    noise.inputs["Distortion"].default_value = 0.2
    ln(tex_coord.outputs["Object"], noise.inputs["Vector"])

    mix_vec = nt.nodes.new("ShaderNodeMix")
    mix_vec.data_type = "RGBA"
    mix_vec.clamp_factor = False
    mix_vec.inputs[0].default_value = 0.05
    ln(tex_coord.outputs["Object"], mix_vec.inputs[6])
    ln(noise.outputs["Color"], mix_vec.inputs[7])

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi.voronoi_dimensions = "4D"
    voronoi.distance = "MINKOWSKI"
    voronoi.inputs["Scale"].default_value = scale * 500.0
    voronoi.inputs["W"].default_value = seed_val
    ln(mix_vec.outputs[2], voronoi.inputs["Vector"])

    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs[3].default_value = 0.1
    mr.inputs[4].default_value = 0.5
    ln(voronoi.outputs["Color"], mr.inputs[0])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = base_color
    _set_principled(bsdf, Metallic=1.0, **{"Specular IOR Level": 0.0})
    ln(mr.outputs["Result"], bsdf.inputs["Roughness"])

    _connect_output(nt, bsdf)
    return mat

def make_grained_metal(name="GrainedMetal", color_hsv=None):
    """Translation of grained_and_polished_metal.py."""

    roughness = float(np.random.uniform(0, 1))
    seed_val = float(np.random.uniform(-1000, 1000))
    hsv = color_hsv or metal_hsv()
    base_color = hsv2rgba(*hsv)
    scale = 1.0

    mapped_rough = 0.05 + roughness * (0.25 - 0.05)

    mat = _new_material(name)
    nt = mat.node_tree
    ln = nt.links.new

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = base_color
    bsdf.inputs["Roughness"].default_value = mapped_rough
    _set_principled(bsdf, Metallic=1.0, **{"Specular IOR Level": 0.0})

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.noise_dimensions = "4D"
    noise.inputs["Scale"].default_value = scale * 2000.0
    noise.inputs["W"].default_value = seed_val
    noise.inputs["Detail"].default_value = 15.0
    noise.inputs["Distortion"].default_value = 2.0
    ln(tex_coord.outputs["Object"], noise.inputs["Vector"])

    mul1_val = mapped_rough * 0.4
    mul2 = nt.nodes.new("ShaderNodeMath")
    mul2.operation = "MULTIPLY"
    ln(_noise_fac(noise), mul2.inputs[0])
    mul2.inputs[1].default_value = mul1_val

    mul3 = nt.nodes.new("ShaderNodeMath")
    mul3.operation = "MULTIPLY"
    ln(mul2.outputs[0], mul3.inputs[0])
    mul3.inputs[1].default_value = 0.01

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    ln(mul3.outputs[0], disp.inputs["Height"])

    _connect_output(nt, bsdf, disp.outputs[0])
    return mat

def make_hammered_metal(name="HammeredMetal", color_hsv=None):
    """Translation of hammered_metal.py."""

    seed_val = float(np.random.uniform(-1000, 1000))
    hsv = color_hsv or metal_hsv()
    base_color = hsv2rgba(*hsv)
    scale = log_uniform(0.8, 1.2)
    disp_mul = log_uniform(0.001, 0.003)

    mat = _new_material(name)
    nt = mat.node_tree
    ln = nt.links.new

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = base_color
    bsdf.inputs["Roughness"].default_value = 0.1
    _set_principled(bsdf, Metallic=1.0, **{"Specular IOR Level": 0.0})

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.noise_dimensions = "4D"
    noise.inputs["Scale"].default_value = scale * 20.0
    noise.inputs["W"].default_value = seed_val
    noise.inputs["Detail"].default_value = 15.0
    noise.inputs["Roughness"].default_value = 0.4
    noise.inputs["Distortion"].default_value = 0.2
    ln(tex_coord.outputs["Object"], noise.inputs["Vector"])

    mix_vec = nt.nodes.new("ShaderNodeMix")
    mix_vec.data_type = "RGBA"
    mix_vec.clamp_factor = False
    mix_vec.inputs[0].default_value = 0.01
    ln(tex_coord.outputs["Object"], mix_vec.inputs[6])
    ln(noise.outputs["Color"], mix_vec.inputs[7])

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi.voronoi_dimensions = "4D"
    voronoi.feature = "SMOOTH_F1"
    voronoi.inputs["Scale"].default_value = scale * 300.0
    voronoi.inputs["W"].default_value = seed_val
    voronoi.inputs["Smoothness"].default_value = 0.2
    ln(mix_vec.outputs[2], voronoi.inputs["Vector"])

    mul_dist = nt.nodes.new("ShaderNodeMath")
    mul_dist.operation = "MULTIPLY"
    ln(voronoi.outputs["Distance"], mul_dist.inputs[0])
    mul_dist.inputs[1].default_value = scale

    power = nt.nodes.new("ShaderNodeMath")
    power.operation = "POWER"
    ln(mul_dist.outputs[0], power.inputs[0])
    power.inputs[1].default_value = 2.5

    mul_final = nt.nodes.new("ShaderNodeMath")
    mul_final.operation = "MULTIPLY"
    ln(power.outputs[0], mul_final.inputs[0])
    mul_final.inputs[1].default_value = disp_mul

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    ln(mul_final.outputs[0], disp.inputs["Height"])

    _connect_output(nt, bsdf, disp.outputs[0])
    return mat

def make_brushed_black_metal(name="BrushedBlackMetal"):
    """Translation of appliance.py -> shader_brushed_black_metal."""

    mat = _new_material(name)
    nt = mat.node_tree
    ln = nt.links.new

    aniso = nt.nodes.new("ShaderNodeBsdfAnisotropic")
    aniso.inputs["Color"].default_value = (0.0167, 0.0167, 0.0167, 1.0)

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(aniso.outputs["BSDF"], out.inputs["Surface"])
    return mat

# Metals registry (mirrors material_assignments.metals)
metals_registry = [
    (make_metal_basic, 3.0),
    (make_brushed_metal, 2.0),
    (make_galvanized_metal, 1.0),
    (make_grained_metal, 1.0),
    (make_hammered_metal, 0.7),
    (make_brushed_black_metal, 0.3),
]

# TEXT (wrap label) material

def _generate_text_string():
    """Generate random label text (simplified"""

    length = np.random.randint(3, 12)
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))

def _random_colormap():
    """Simplified colormap generator"""

    count = 20
    hue = (np.random.uniform() + np.linspace(0, 0.5, count)) % 1
    lightness = np.linspace(np.random.uniform(0.0, 0.3), np.random.uniform(0.6, 0.8), count)
    saturation = np.concatenate([
        np.linspace(1, 0.5, count // 2),
        np.linspace(0.5, 1, count // 2),
    ])
    saturation *= np.random.uniform(0, 1)
    lightness *= np.random.uniform(0.5, 1)
    return np.array([colorsys.hls_to_rgb(h, l, s) for h, l, s in zip(hue, lightness, saturation)])

def make_text_material(name="TextLabel"):
    """Translation of text.py -> Text.make_shader_func.

    Generates a procedural matplotlib image and uses it as an image texture,
    combined with voronoi/noise distortion for realistic label appearance.
    """

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from PIL import Image
        _HAS_MATPLOTLIB = True
    except ImportError:
        _HAS_MATPLOTLIB = False

    if not _HAS_MATPLOTLIB:
        # Fallback: simple colored plastic material if matplotlib unavailable
        return make_plastic(name=name)

    # --- Generate the label image ---
    colormap = _random_colormap()

    def random_color():
        r = np.random.uniform()
        if r < 0.03:
            return np.array([1, 1, 1])
        elif r < 0.08:
            return np.array([0, 0, 0])
        return colormap[np.random.randint(len(colormap))]

    size = 4
    dpi = 100
    fig = plt.figure(figsize=(size, size), dpi=dpi)
    ax = fig.add_axes((0, 0, 1, 1))
    bg_color = random_color()
    ax.set_facecolor(bg_color)

    # Add colored rectangles
    from matplotlib.patches import Rectangle, Circle, Ellipse
    n_patches = np.random.randint(5, 8)
    for _ in range(n_patches):
        x, y = np.random.uniform(0.1, 0.9), np.random.uniform(0.1, 0.9)
        w = np.random.uniform(0.05, 0.4)
        h = np.random.uniform(0.05, 0.4)
        fc = random_color()
        ec = random_color()
        patch_type = np.random.choice(["rect", "circle", "ellipse"])
        if patch_type == "rect":
            patch = Rectangle((x - w / 2, y - h / 2), w, h,
                              facecolor=fc, edgecolor=ec, linewidth=np.random.uniform(2, 5))
        elif patch_type == "circle":
            patch = Circle((x, y), min(w, h) / 2,
                           facecolor=fc, edgecolor=ec, linewidth=np.random.uniform(2, 5))
        else:
            patch = Ellipse((x, y), w, h,
                            facecolor=fc, edgecolor=ec, linewidth=np.random.uniform(2, 5))
        try:
            ax.add_patch(patch)
        except Exception:
            pass

    # Add text
    n_texts = np.random.randint(2, 4)
    for _ in range(n_texts):
        x = 0.5 + (np.random.uniform(0.1, 0.9) - 0.5) * 0.6
        y = np.random.uniform(0.1, 0.9)
        text_str = _generate_text_string()
        text_color = random_color()
        bg_c = random_color()
        font_size = np.random.uniform(8, 26)
        plt.figtext(x, y, text_str, size=font_size, ha="center", va="center",
                    c=text_color, rotation=np.random.uniform(-10, 10),
                    wrap=True, backgroundcolor=bg_c)

    # Add barcode
    if np.random.uniform() < 0.5:
        barcode_length = np.random.randint(25, 40)
        code = np.random.randint(0, 2, barcode_length)
        bar_h = np.random.uniform(0.06, 0.12)
        bar_w = bar_h * np.random.uniform(1.5, 3.0)
        bx = np.random.uniform(0.2, 0.8)
        by = np.random.uniform(0.1, 0.3)
        ax2 = fig.add_axes((bx - bar_w / 2, by - bar_h / 2, bar_w, bar_h))
        ax2.set_axis_off()
        ax2.imshow(code.reshape(1, -1), cmap="binary", aspect="auto", interpolation="nearest")

    # Render to buffer
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png")
    buffer.seek(0)
    px_size = size * dpi
    bpy_image = bpy.data.images.new("text_texture", width=px_size, height=px_size, alpha=True)
    data = np.asarray(Image.open(buffer), dtype=np.float32)[::-1, :] / 255.0
    bpy_image.pixels.foreach_set(data.ravel())
    bpy_image.pack()
    plt.close("all")

    # --- Build the shader ---
    emission = 0
    metallic_val = float(np.random.uniform(0, 0.5))
    specular_val = float(np.random.uniform(0, 0.2))
    distort_fac = float(np.random.uniform(0, 0.4)) if np.random.uniform() < 0.5 else 1.0

    mat = _new_material(name)
    nt = mat.node_tree
    ln = nt.links.new

    uv_map = nt.nodes.new("ShaderNodeUVMap")

    reroute = nt.nodes.new("NodeReroute")
    ln(uv_map.outputs["UV"], reroute.inputs[0])

    voronoi1 = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi1.inputs["Scale"].default_value = 60.0
    ln(reroute.outputs[0], voronoi1.inputs["Vector"])

    voronoi2 = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi2.inputs["Scale"].default_value = 60.0
    ln(reroute.outputs[0], voronoi2.inputs["Vector"])

    mix_voronoi = nt.nodes.new("ShaderNodeMix")
    mix_voronoi.data_type = "RGBA"
    ln(voronoi1.outputs["Position"], mix_voronoi.inputs[6])
    ln(voronoi2.outputs["Position"], mix_voronoi.inputs[7])

    # MusgraveTexture -> NoiseTexture in 4.4+
    musgrave = nt.nodes.new("ShaderNodeTexNoise")
    musgrave.inputs["Detail"].default_value = 5.6
    ln(reroute.outputs[0], musgrave.inputs["Vector"])

    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    noise1.inputs["Scale"].default_value = 35.4
    noise1.inputs["Detail"].default_value = 3.3
    noise1.inputs["Roughness"].default_value = 1.0
    ln(reroute.outputs[0], noise1.inputs["Vector"])

    mix3 = nt.nodes.new("ShaderNodeMix")
    mix3.data_type = "RGBA"
    mix3.inputs[0].default_value = float(np.random.uniform(0.2, 1.0))
    ln(_noise_fac(musgrave), mix3.inputs[6])
    ln(noise1.outputs["Color"], mix3.inputs[7])

    mix1 = nt.nodes.new("ShaderNodeMix")
    mix1.data_type = "RGBA"
    mix1.inputs[0].default_value = 0.0417
    ln(mix_voronoi.outputs[2], mix1.inputs[6])
    ln(mix3.outputs[2], mix1.inputs[7])

    mix2 = nt.nodes.new("ShaderNodeMix")
    mix2.data_type = "RGBA"
    mix2.inputs[0].default_value = distort_fac
    ln(mix1.outputs[2], mix2.inputs[6])
    ln(uv_map.outputs["UV"], mix2.inputs[7])

    img_tex = nt.nodes.new("ShaderNodeTexImage")
    img_tex.image = bpy_image
    ln(mix2.outputs[2], img_tex.inputs["Vector"])

    roughness_noise = nt.nodes.new("ShaderNodeTexNoise")

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(img_tex.outputs["Color"], bsdf.inputs["Base Color"])
    ln(_noise_fac(roughness_noise), bsdf.inputs["Roughness"])
    _set_principled(bsdf, Metallic=metallic_val,
                    **{"Specular IOR Level": specular_val})

    _connect_output(nt, bsdf)
    return mat

seed_all(SEED)

# Sample plastic for body
_plastic_ctor = weighted_sample(plastics_registry)
BODY_MAT = _plastic_ctor(name="BottleBody")
BODY_MAT.use_fake_user = True

# Sample text for wrap
WRAP_MAT = make_text_material(name="BottleWrap")
WRAP_MAT.use_fake_user = True

# Sample metal for cap
_metal_ctor = weighted_sample(metals_registry)
CAP_MAT = _metal_ctor(name="BottleCap")
CAP_MAT.use_fake_user = True

# texture_shared and cap_subsurf flags (consumed during __init__)
TEXTURE_SHARED = np.random.uniform() < 0.2
CAP_SUBSURF_SIMPLE = np.random.uniform() < 0.5

np.random.seed(SEED)
random.seed(SEED)

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for c in list(bpy.data.curves):
        bpy.data.curves.remove(c)
    bpy.context.scene.cursor.location = (0, 0, 0)

def select_only(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

def apply_transform(obj, loc=False):
    select_only(obj)
    bpy.ops.object.transform_apply(location=loc, rotation=True, scale=True)

def modify_mesh(obj, mod_type, apply=True, **kwargs):
    select_only(obj)
    mod = obj.modifiers.new(name=mod_type, type=mod_type)
    for k, v in kwargs.items():
        setattr(mod, k, v)
    if apply:
        bpy.ops.object.modifier_apply(modifier=mod.name)

def read_co(obj):
    arr = np.zeros(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get("co", arr)
    return arr.reshape(-1, 3)

def subsurf(obj, levels, simple=False):
    if levels > 0:
        modify_mesh(obj, "SUBSURF",
                     levels=levels, render_levels=levels,
                     subdivision_type="SIMPLE" if simple else "CATMULL_CLARK")

def new_cylinder(vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(location=(0, 0, 0.5), depth=1, vertices=vertices)
    obj = bpy.context.active_object
    apply_transform(obj, loc=True)
    return obj

def join_objects(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.location = 0, 0, 0
    obj.rotation_euler = 0, 0, 0
    obj.scale = 1, 1, 1
    bpy.ops.object.select_all(action="DESELECT")
    return obj

# -- spin --

def bezier_curve(anchors, vector_locations=(), resolution=None):
    n = [len(r) for r in anchors if isinstance(r, Sized)][0]
    anchors = np.array([
        np.array(r, dtype=float) if isinstance(r, Sized) else np.full(n, r)
        for r in anchors
    ])
    bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0))
    obj = bpy.context.active_object
    if n > 2:
        select_only(obj)
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.curve.subdivide(number_cuts=n - 2)
        bpy.ops.object.mode_set(mode="OBJECT")
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
    return curve2mesh(obj)

def curve2mesh(obj):
    points = obj.data.splines[0].bezier_points
    cos = np.array([p.co for p in points])
    length = np.linalg.norm(cos[:-1] - cos[1:], axis=-1)
    min_length = 5e-3
    select_only(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    for i in range(len(points)):
        if points[i].handle_left_type == "FREE":
            points[i].handle_left_type = "ALIGNED"
        if points[i].handle_right_type == "FREE":
            points[i].handle_right_type = "ALIGNED"
    for i in reversed(range(len(points) - 1)):
        points = list(obj.data.splines[0].bezier_points)
        number_cuts = min(int(length[i] / min_length) - 1, 64)
        if number_cuts < 0:
            continue
        bpy.ops.curve.select_all(action="DESELECT")
        points[i].select_control_point = True
        points[i + 1].select_control_point = True
        bpy.ops.curve.subdivide(number_cuts=number_cuts)
    obj.data.splines[0].resolution_u = 1
    bpy.ops.object.mode_set(mode="OBJECT")
    select_only(obj)
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.active_object
    modify_mesh(obj, "WELD", merge_threshold=1e-3)
    return obj

def spin(anchors, vector_locations=(), rotation_resolution=None, axis=(0, 0, 1)):
    obj = bezier_curve(anchors, vector_locations)
    co = read_co(obj)
    ax = np.array(axis)
    mean_radius = np.mean(np.linalg.norm(
        co - (co @ ax)[:, np.newaxis] * ax, axis=-1
    ))
    if rotation_resolution is None:
        rotation_resolution = min(int(2 * np.pi * mean_radius / 5e-3), 128)
    modify_mesh(obj, "WELD", merge_threshold=1e-3)
    select_only(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.spin(steps=rotation_resolution, angle=np.pi * 2, axis=axis)
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=1e-3)
    bpy.ops.object.mode_set(mode="OBJECT")
    return obj

# -- wrap builder --

def subdivide_edge_ring(obj, cuts):
    """Simplified subdivision of the cylinder's edge rings."""

    select_only(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.subdivide(number_cuts=cuts)
    bpy.ops.object.mode_set(mode="OBJECT")

def make_wrap_cylinder(bottle_obj, z_neck, z_waist, z_neck_offset, z_waist_offset,
                       z_length, wrap_mat):
    """Create the label wrap cylinder, UV-unwrap it, and assign the text material."""

    import bmesh

    obj = new_cylinder(vertices=128)
    # Remove top/bottom caps (faces with > 4 verts)
    select_only(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(obj.data)
    geom = [f for f in bm.faces if len(f.verts) > 4]
    bmesh.ops.delete(bm, geom=geom, context="FACES_ONLY")
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode="OBJECT")

    subdivide_edge_ring(obj, 16)

    z_max = z_neck - np.random.uniform(0.02, z_neck_offset) * (z_neck - z_waist)
    z_min = z_waist + np.random.uniform(0.02, z_waist_offset) * (z_neck - z_waist)
    radius = np.max(read_co(bottle_obj)[:, 0]) + 2e-3
    obj.scale = (radius, radius, (z_max - z_min) * z_length)
    obj.location[2] = z_min * z_length
    apply_transform(obj, loc=True)

    # UV unwrap (smart project for the cylindrical wrap)
    select_only(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project()
    bpy.ops.object.mode_set(mode="OBJECT")

    # Assign wrap material
    obj.data.materials.clear()
    obj.data.materials.append(wrap_mat)
    return obj

# -- BottleFactory --

def create_bottle():
    z_neck_offset = 0.05
    z_waist_offset = 0.15

    z_length = uniform(0.15, 0.25)
    x_length = z_length * uniform(0.15, 0.25)
    x_cap = uniform(0.3, 0.35)
    bottle_type = np.random.choice(["beer", "bordeaux", "champagne", "coke", "vintage"])
    bottle_width = uniform(0.002, 0.005)
    z_waist = 0

    if bottle_type == "beer":
        z_neck = uniform(0.5, 0.6)
        z_cap_ratio = uniform(0.05, 0.08)
        neck_size = uniform(0.06, 0.1)
        neck_ratio = uniform(0.4, 0.5)
        xa = [0, 1, 1, (neck_ratio + 1) / 2 + (1 - neck_ratio) / 2 * x_cap,
              neck_ratio + (1 - neck_ratio) * x_cap, x_cap, x_cap, 0]
        za = [0, 0, z_neck, z_neck + uniform(0.6, 0.7) * neck_size,
              z_neck + neck_size, 1 - z_cap_ratio, 1, 1]
        is_vec = [0, 1, 1, 0, 1, 1, 1, 0]
    elif bottle_type == "bordeaux":
        z_neck = uniform(0.6, 0.7)
        z_cap_ratio = uniform(0.1, 0.15)
        neck_size = uniform(0.1, 0.15)
        xa = [0, 1, 1, (1 + x_cap) / 2, x_cap, x_cap, 0]
        za = [0, 0, z_neck, z_neck + uniform(0.6, 0.7) * neck_size,
              z_neck + neck_size, 1, 1]
        is_vec = [0, 1, 1, 0, 1, 1, 0]
    elif bottle_type == "champagne":
        z_neck = uniform(0.4, 0.5)
        z_cap_ratio = uniform(0.05, 0.08)
        xa = [0, 1, 1, 1, (1 + x_cap) / 2, x_cap, x_cap, 0]
        za = [0, 0, z_neck, z_neck + uniform(0.08, 0.1), z_neck + uniform(0.15, 0.18),
              1 - z_cap_ratio, 1, 1]
        is_vec = [0, 1, 1, 0, 0, 1, 1, 0]
    elif bottle_type == "coke":
        z_waist = uniform(0.4, 0.5)
        z_neck = z_waist + uniform(0.2, 0.25)
        z_cap_ratio = uniform(0.05, 0.08)
        xa = [0, uniform(0.85, 0.95), 1, uniform(0.85, 0.95), 1, 1, x_cap, x_cap, 0]
        za = [0, 0, uniform(0.08, 0.12), uniform(0.18, 0.25), z_waist, z_neck,
              1 - z_cap_ratio, 1, 1]
        is_vec = [0, 1, 0, 0, 1, 1, 1, 1, 0]
    else:  # vintage
        z_waist = uniform(0.1, 0.15)
        z_neck = uniform(0.7, 0.75)
        z_cap_ratio = uniform(0.0, 0.08)
        x_lower = uniform(0.85, 0.95)
        xa = [0, x_lower, (x_lower + 1) / 2, 1, 1, (x_cap + 1) / 2, x_cap, x_cap, 0]
        za = [0, 0, z_waist - uniform(0.1, 0.15), z_waist, z_neck,
              z_neck + uniform(0.1, 0.2), 1 - z_cap_ratio, 1, 1]
        is_vec = [0, 1, 0, 1, 1, 0, 1, 1, 0]

    # 1. Bottle body
    x_anchors_abs = np.array(xa) * x_length
    z_anchors_abs = np.array(za) * z_length
    anchors = x_anchors_abs, 0, z_anchors_abs
    bottle = spin(anchors, np.nonzero(is_vec)[0])
    subsurf(bottle, 1)
    if bottle_width > 0:
        modify_mesh(bottle, "SOLIDIFY", thickness=bottle_width)

    # Assign body material
    bottle.data.materials.clear()
    bottle.data.materials.append(BODY_MAT)

    # 2. Wrap (label)
    wrap = make_wrap_cylinder(bottle, z_neck, z_waist, z_neck_offset, z_waist_offset,
                              z_length, WRAP_MAT)

    # 3. Cap
    cap = new_cylinder(vertices=128)
    cap.scale = [
        (x_cap + 0.1) * x_length,
        (x_cap + 0.1) * x_length,
        (z_cap_ratio + 0.01) * z_length,
    ]
    cap.location[2] = (1 - z_cap_ratio) * z_length
    apply_transform(cap, loc=True)
    subsurf(cap, 1, CAP_SUBSURF_SIMPLE)

    # Assign cap material
    cap.data.materials.clear()
    cap.data.materials.append(CAP_MAT)

    return join_objects([bottle, wrap, cap])

clear_scene()
obj = create_bottle()
obj.name = "BottleFactory"

n_slots = len(obj.data.materials)
n_verts = len(obj.data.vertices)
n_faces = len(obj.data.polygons)
print(f"BottleFactory built: {n_verts} verts, {n_faces} faces, {n_slots} material slot(s)")
for i, mat in enumerate(obj.data.materials):
    print(f"  slot {i}: {mat.name if mat else '(empty)'}")

