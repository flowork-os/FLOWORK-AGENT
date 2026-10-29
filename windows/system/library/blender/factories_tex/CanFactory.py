# [FL_INDEX: keywords="blender_factory, procedural_3d, CanFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: CanFactory | Category: factories_tex
# Prompt: A 3D model of a square tin can rendered from a slightly elevated three-quarter perspective. The can features a boxy cube-like form with softly rounded vertical edges, a flat top with a recessed dark lid, and a warm brown metallic exterior.

import os, math, bpy, bmesh, random, colorsys
import numpy as np
from numpy.random import uniform

# --- Inlined material library (hand-crafted for CanFactory) ---

# ── Helpers ─────────────────────────────────────────────────────────────────
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

def metal_hsv():
    """py:metal_hsv."""

    if np.random.uniform() < 0.2:
        return (np.random.uniform(0, 1),
                np.random.uniform(0.0, 0.2),
                log_uniform(0.05, 0.3))
    return (np.random.uniform(0, 1),
            np.random.uniform(0.3, 0.6),
            log_uniform(0.02, 0.5))

def weighted_sample(reg):
    classes, weights = zip(*reg)
    weights = np.array(weights, dtype=float)
    return classes[int(np.random.choice(len(classes), p=weights / weights.sum()))]

def _new_material(name: str) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat

def _set_principled(bsdf, **kw):
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

def _build_float_curve(node_tree, value_socket, anchors):
    fc = node_tree.nodes.new("ShaderNodeFloatCurve")
    fc.mapping.use_clip = False
    curve = fc.mapping.curves[0]
    for i, (x, y) in enumerate(anchors):
        if i < 2:
            curve.points[i].location = (x, y)
        else:
            curve.points.new(x, y)
        curve.points[i].handle_type = "VECTOR"
    fc.mapping.update()
    node_tree.links.new(value_socket, fc.inputs["Value"])
    return fc

def _noise_fac_output(noise_node):
    if "Fac" in noise_node.outputs:
        return noise_node.outputs["Fac"]
    if "Factor" in noise_node.outputs:
        return noise_node.outputs["Factor"]
    return noise_node.outputs[0]

def _connect_output(node_tree, bsdf, displacement=None):
    out = node_tree.nodes.new("ShaderNodeOutputMaterial")
    node_tree.links.new(bsdf.outputs[0], out.inputs["Surface"])
    if displacement is not None:
        node_tree.links.new(displacement, out.inputs["Displacement"])
    return out

# ── Metal material constructors ─────────────────────────────────────────────

def make_metal_basic(name="MetalBasic", color_hsv=None) -> bpy.types.Material:
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
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    mapping_stretch = nt.nodes.new("ShaderNodeMapping")
    mapping_stretch.inputs["Scale"].default_value = (0.2, 0.2, 5.0)
    nt.links.new(tex_coord.outputs["Object"], mapping_stretch.inputs["Vector"])

    seed_val = float(np.random.uniform(-1000, 1000))

    noise_a = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise_a, "noise_dimensions"):
        try:
            noise_a.noise_dimensions = "4D"
        except TypeError:
            pass
    noise_a.inputs["Scale"].default_value = 100.0
    if "Detail" in noise_a.inputs:
        noise_a.inputs["Detail"].default_value = 15.0
    if "Roughness" in noise_a.inputs:
        noise_a.inputs["Roughness"].default_value = 0.4
    if "Distortion" in noise_a.inputs:
        noise_a.inputs["Distortion"].default_value = 0.1
    if "W" in noise_a.inputs:
        noise_a.inputs["W"].default_value = seed_val
    nt.links.new(mapping_stretch.outputs["Vector"], noise_a.inputs["Vector"])

    # Map range for brightness
    map_range_brightness = nt.nodes.new("ShaderNodeMapRange")
    map_range_brightness.inputs[1].default_value = 0.4
    map_range_brightness.inputs[2].default_value = 0.6
    map_range_brightness.inputs[3].default_value = 0.8
    map_range_brightness.inputs[4].default_value = 1.2
    nt.links.new(_noise_fac_output(noise_a), map_range_brightness.inputs[0])

    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_node.inputs["Color"].default_value = hsv2rgba(base_color_hsv)
    nt.links.new(map_range_brightness.outputs["Result"], hsv_node.inputs["Value"])

    # Roughness map range
    map_range_roughness = nt.nodes.new("ShaderNodeMapRange")
    map_range_roughness.inputs[1].default_value = 0.4
    map_range_roughness.inputs[2].default_value = 0.6
    map_range_roughness.inputs[3].default_value = 0.2
    map_range_roughness.inputs[4].default_value = 0.3
    nt.links.new(_noise_fac_output(noise_a), map_range_roughness.inputs[0])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Metallic=1.0, **{"Specular IOR Level": 0.0})
    nt.links.new(hsv_node.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(map_range_roughness.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

def make_galvanized_metal(name="GalvanizedMetal", base_color_hsv=None) -> bpy.types.Material:
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(voronoi, "voronoi_dimensions"):
        try:
            voronoi.voronoi_dimensions = "4D"
        except TypeError:
            voronoi.voronoi_dimensions = "3D"
    if hasattr(voronoi, "distance"):
        try:
            voronoi.distance = "MINKOWSKI"
        except TypeError:
            pass
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
        bsdf,
        Metallic=1.0,
        **{"Specular IOR Level": 0.0, "Base Color": hsv2rgba(base_color_hsv)},
    )
    nt.links.new(map_range.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

def make_grained_metal(name="GrainedMetal", base_color_hsv=None) -> bpy.types.Material:
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2000.0
    if "Detail" in noise.inputs:
        noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs:
        noise.inputs["Distortion"].default_value = 2.0
    if "W" in noise.inputs:
        noise.inputs["W"].default_value = float(np.random.uniform(-1000, 1000))
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    roughness_input = float(np.random.uniform(0.0, 1.0))
    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[0].default_value = roughness_input
    map_range.inputs[3].default_value = 0.05
    map_range.inputs[4].default_value = 0.25

    # Displacement chain: noise_fac * (mapped_roughness * 0.4) * 0.01
    mul_rough_factor = nt.nodes.new("ShaderNodeMath")
    mul_rough_factor.operation = "MULTIPLY"
    mul_rough_factor.inputs[1].default_value = 0.4
    nt.links.new(map_range.outputs["Result"], mul_rough_factor.inputs[0])

    mul_noise_rough = nt.nodes.new("ShaderNodeMath")
    mul_noise_rough.operation = "MULTIPLY"
    nt.links.new(_noise_fac_output(noise), mul_noise_rough.inputs[0])
    nt.links.new(mul_rough_factor.outputs[0], mul_noise_rough.inputs[1])

    mul_final_disp = nt.nodes.new("ShaderNodeMath")
    mul_final_disp.operation = "MULTIPLY"
    mul_final_disp.inputs[1].default_value = 0.01
    nt.links.new(mul_noise_rough.outputs[0], mul_final_disp.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_final_disp.outputs[0], disp.inputs["Height"])

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
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(voronoi, "feature"):
        try:
            voronoi.feature = "SMOOTH_F1"
        except TypeError:
            pass
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

    mul_scale = nt.nodes.new("ShaderNodeMath")
    mul_scale.operation = "MULTIPLY"
    mul_scale.inputs[1].default_value = log_uniform(0.001, 0.003)
    nt.links.new(pow_node.outputs[0], mul_scale.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_scale.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf,
        Metallic=1.0,
        **{"Specular IOR Level": 0.0, "Base Color": hsv2rgba(base_color_hsv), "Roughness": 0.1},
    )
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

def make_brushed_black_metal(name="BrushedBlackMetal") -> bpy.types.Material:
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

# ── Graphic design / wrap material constructors ─────────────────────────────

def make_basic_bsdf(name="BasicBSDF") -> bpy.types.Material:
    """Randomly colored Principled BSDF with variable roughness/metallic."""

    hsv_val = (float(np.random.uniform(0.05, 0.95)),
               float(np.random.uniform(0.05, 0.95)),
               float(np.random.uniform(0.05, 0.95)))
    mat = _new_material(name)
    nt = mat.node_tree
    color_node = nt.nodes.new("ShaderNodeRGB")
    color_node.outputs[0].default_value = hsv2rgba(hsv_val)

    roughness_val = float(np.clip(np.random.normal(0.6, 0.3), 0.05, 0.95))
    metallic_val = float(np.random.uniform(0, 1)) if np.random.uniform() < 0.3 else 0.0
    subsurface_val = 0.0 if np.random.uniform() < 0.8 else float(np.random.uniform(0, 0.2))

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(color_node.outputs[0], bsdf.inputs["Base Color"])
    _set_principled(
        bsdf,
        Roughness=roughness_val,
        Metallic=metallic_val,
        **{"Subsurface Weight": subsurface_val},
    )
    _connect_output(nt, bsdf)
    return mat

def make_text_label(name="TextLabel") -> bpy.types.Material:
    """The original Text class generates matplotlib PNG images with random patches,
    text and barcodes, then uses them as image textures. Since we cannot depend
    on matplotlib/PIL/font files in standalone scripts, we approximate the visual
    result with a procedural shader: colorful voronoi + noise patterns mixed with
    a base color, similar to how the original uses voronoi/noise for UV distortion.
    """

    mat = _new_material(name)
    nt = mat.node_tree

    # Random base and accent colors (mimicking the colormap logic)
    base_hue = float(np.random.uniform(0, 1))
    base_sat = float(np.random.uniform(0.3, 0.8))
    base_val = float(np.random.uniform(0.2, 0.7))
    accent_hue = float((base_hue + np.random.uniform(0.2, 0.5)) % 1.0)
    accent_sat = float(np.random.uniform(0.4, 0.9))
    accent_val = float(np.random.uniform(0.3, 0.8))

    base_color = hsv2rgba((base_hue, base_sat, base_val))
    accent_color = hsv2rgba((accent_hue, accent_sat, accent_val))

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # Voronoi for patch-like regions
    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi.inputs["Scale"].default_value = float(np.random.uniform(3.0, 8.0))
    nt.links.new(tex_coord.outputs["Object"], voronoi.inputs["Vector"])

    # Noise for texture variation
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = float(np.random.uniform(15.0, 40.0))
    if "Detail" in noise.inputs:
        noise.inputs["Detail"].default_value = 5.0
    if "Roughness" in noise.inputs:
        noise.inputs["Roughness"].default_value = 1.0
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    # Mix voronoi color and noise to create label-like pattern
    mix_pattern = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_pattern, "data_type"):
        mix_pattern.data_type = "RGBA"
    mix_pattern.inputs[0].default_value = float(np.random.uniform(0.3, 0.7))
    voronoi_color = voronoi.outputs.get("Color") or voronoi.outputs[0]
    nt.links.new(voronoi_color, mix_pattern.inputs[6])
    nt.links.new(_noise_fac_output(noise), mix_pattern.inputs[7])

    # ColorRamp to map the mixed pattern to label colors
    color_ramp = nt.nodes.new("ShaderNodeValToRGB")
    elements = color_ramp.color_ramp.elements
    elements[0].position = 0.3
    elements[0].color = base_color
    elements[1].position = 0.7
    elements[1].color = accent_color
    cr_fac = color_ramp.inputs.get("Fac") or color_ramp.inputs[0]
    nt.links.new(mix_pattern.outputs[2], cr_fac)

    # Second noise for roughness variation
    noise_rough = nt.nodes.new("ShaderNodeTexNoise")
    noise_rough.inputs["Scale"].default_value = 50.0

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(color_ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(_noise_fac_output(noise_rough), bsdf.inputs["Roughness"])
    _set_principled(
        bsdf,
        Metallic=float(np.random.uniform(0, 0.5)),
        **{"Specular IOR Level": float(np.random.uniform(0, 0.2))},
    )
    _connect_output(nt, bsdf)
    return mat

# ── Registries ──────────────────────────────────────────────────────────────

metals = [
    (make_metal_basic, 3.0),
    (make_brushed_metal, 2.0),
    (make_galvanized_metal, 1.0),
    (make_grained_metal, 1.0),
    (make_hammered_metal, 0.7),
    (make_brushed_black_metal, 0.3),
]

graphicdesign = [
    (make_text_label, 1.0),
    (make_basic_bsdf, 0.1),
]

REGISTRY = {
    "metals": metals,
    "graphicdesign": graphicdesign,
}

def get_material(registry_key: str, name: str = None) -> bpy.types.Material:
    ctor = weighted_sample(REGISTRY[registry_key])
    return ctor(name=name or registry_key.title())

# ── wear_tear post-processing ──────────────────────────────────────────────
# Faithful raw-bpy translations of:
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
            elem = elements.new(pos)
            elem.color = color
    return cr

def _noise_tex(nt, vector_socket, scale_val, detail=2.0, distortion=0.0, roughness=0.5):
    n = nt.nodes.new("ShaderNodeTexNoise")
    if vector_socket is not None:
        nt.links.new(vector_socket, n.inputs["Vector"])
    if isinstance(scale_val, (int, float)):
        n.inputs["Scale"].default_value = float(scale_val)
    else:
        nt.links.new(scale_val, n.inputs["Scale"])
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

    # First scratch direction
    combine_xyz_1 = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(n_angle1.outputs[0], combine_xyz_1.inputs["Y"])
    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    if hasattr(mapping_1, "vector_type"):
        try:
            mapping_1.vector_type = "TEXTURE"
        except TypeError:
            pass
    mapping_1.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], mapping_1.inputs["Vector"])
    nt.links.new(combine_xyz_1.outputs[0], mapping_1.inputs["Rotation"])
    noise_dir1 = _noise_tex(nt, mapping_1.outputs["Vector"], n_scale.outputs[0],
                            detail=15.0, distortion=22.8, roughness=0.0)

    # Second scratch direction
    combine_xyz_2 = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(n_angle2.outputs[0], combine_xyz_2.inputs["Y"])
    mapping_2 = nt.nodes.new("ShaderNodeMapping")
    if hasattr(mapping_2, "vector_type"):
        try:
            mapping_2.vector_type = "TEXTURE"
        except TypeError:
            pass
    mapping_2.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], mapping_2.inputs["Vector"])
    nt.links.new(combine_xyz_2.outputs[0], mapping_2.inputs["Rotation"])
    noise_dir2 = _noise_tex(nt, mapping_2.outputs["Vector"], n_scale.outputs[0],
                            detail=15.0, distortion=22.8, roughness=0.0)

    add_scratches = _math(nt, "ADD",
                          _noise_fac_output(noise_dir1),
                          _noise_fac_output(noise_dir2))

    # Mask noise
    mapping_mask = nt.nodes.new("ShaderNodeMapping")
    if hasattr(mapping_mask, "vector_type"):
        try:
            mapping_mask.vector_type = "TEXTURE"
        except TypeError:
            pass
    mapping_mask.inputs["Rotation"].default_value = (0.1588, -0.5742, 0.1920)
    nt.links.new(tex_coord.outputs["Object"], mapping_mask.inputs["Vector"])
    noise_mask = _noise_tex(nt, mapping_mask.outputs["Vector"],
                            n_mask_noise.outputs[0], detail=1.0)
    cr_mask = _color_ramp(nt, _noise_fac_output(noise_mask),
                          [(0.4109, (0, 0, 0, 1)), (1.0, (1, 1, 1, 1))])
    mul_mask_ratio = _math(nt, "MULTIPLY",
                           n_mask_ratio.outputs[0],
                           cr_mask.outputs["Color"])
    add_combined = _math(nt, "ADD",
                         add_scratches.outputs[0],
                         mul_mask_ratio.outputs[0],
                         clamp=True)

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
        except Exception as exc:
            print(f"  [scratches] failed on {mat.name}: {type(exc).__name__}: {exc}")

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
    n_scratch_mask_rnd = _value_node(nt, p["scratch_mask_randomness"])
    n_scratch_radius = _value_node(nt, p["scratch_radius"])
    n_worn_opacity = _value_node(nt, p["worn_off_opacity"])
    n_worn_radius = _value_node(nt, p["worn_off_radius"])
    n_worn_mask_rnd = _value_node(nt, p["worn_off_mask_randomness"])
    n_edge_whiteness = _value_node(nt, p["edge_base_color_whiteness"])
    n_edge_hue = _value_node(nt, p["edge_base_color_hue"])
    n_scratch_density = _value_node(nt, p["scratch_density"])

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    mapping = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

    # Scratch mask noise
    noise_scratch_mask = _noise_tex(nt, mapping.outputs["Vector"],
                                    n_scratch_mask_rnd.outputs[0], detail=1.0)
    cr_scratch_mask = _color_ramp(nt, _noise_fac_output(noise_scratch_mask),
                                  [(0.4436, (0, 0, 0, 1)), (0.5345, (1, 1, 1, 1))])

    # Bevel edge detection (scratch radius)
    bevel_scratch = nt.nodes.new("ShaderNodeBevel")
    bevel_scratch.samples = 20
    nt.links.new(n_scratch_radius.outputs[0], bevel_scratch.inputs["Radius"])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sub_scratch = _vmath(nt, "SUBTRACT", bevel_scratch.outputs[0], geo.outputs["Normal"])
    abs_scratch = _math(nt, "ABSOLUTE", sub_scratch.outputs["Vector"])
    cr_edge_scratch = _color_ramp(nt, abs_scratch.outputs[0],
                                  [(0.0691, (0, 0, 0, 1)), (0.1564, (1, 1, 1, 1))])

    mul_edge_mask = _math(nt, "MULTIPLY",
                          cr_scratch_mask.outputs["Color"],
                          cr_edge_scratch.outputs["Color"],
                          clamp=True)
    mul_scratch_opacity = _math(nt, "MULTIPLY",
                                n_scratch_opacity.outputs[0],
                                mul_edge_mask.outputs[0],
                                clamp=True)

    # Bevel edge detection (worn-off radius)
    bevel_worn = nt.nodes.new("ShaderNodeBevel")
    bevel_worn.samples = 20
    nt.links.new(n_worn_radius.outputs[0], bevel_worn.inputs["Radius"])
    sub_worn = _vmath(nt, "SUBTRACT", bevel_worn.outputs[0], geo.outputs["Normal"])
    abs_worn = _math(nt, "ABSOLUTE", sub_worn.outputs["Vector"])

    noise_worn_mask = _noise_tex(nt, mapping.outputs["Vector"],
                                 n_worn_mask_rnd.outputs[0], detail=1.0)
    cr_worn_mask = _color_ramp(nt, _noise_fac_output(noise_worn_mask),
                               [(0.0764, (1, 1, 1, 1)), (0.5709, (0, 0, 0, 1))])
    mul_worn_raw = _math(nt, "MULTIPLY",
                         abs_worn.outputs[0],
                         cr_worn_mask.outputs["Color"],
                         clamp=True)
    mul_worn_opacity = _math(nt, "MULTIPLY",
                             n_worn_opacity.outputs[0],
                             mul_worn_raw.outputs[0],
                             clamp=True)
    cr_worn_final = _color_ramp(nt, mul_worn_opacity.outputs[0],
                                [(0.0, (0, 0, 0, 1)), (0.7782, (1, 1, 1, 1))])

    # Edge color HSV
    combine_color = nt.nodes.new("ShaderNodeCombineColor")
    if hasattr(combine_color, "mode"):
        try:
            combine_color.mode = "HSV"
        except TypeError:
            pass
    nt.links.new(n_edge_hue.outputs[0], combine_color.inputs["Red"])
    combine_color.inputs["Green"].default_value = 0.7733
    combine_color.inputs["Blue"].default_value = 0.0100

    mix_edge_color = nt.nodes.new("ShaderNodeMix")
    if hasattr(mix_edge_color, "data_type"):
        mix_edge_color.data_type = "RGBA"
    if hasattr(mix_edge_color, "clamp_result"):
        try:
            mix_edge_color.clamp_result = True
        except TypeError:
            pass
    if hasattr(mix_edge_color, "clamp_factor"):
        try:
            mix_edge_color.clamp_factor = False
        except TypeError:
            pass
    nt.links.new(n_edge_whiteness.outputs[0], mix_edge_color.inputs[0])
    nt.links.new(combine_color.outputs[0], mix_edge_color.inputs[6])
    mix_edge_color.inputs[7].default_value = (0.02, 0.02, 0.02, 1.0)

    # Worn-edge BSDF 1
    bsdf_worn_1 = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix_edge_color.outputs[2], bsdf_worn_1.inputs["Base Color"])
    _set_principled(bsdf_worn_1, Metallic=0.3745, Roughness=0.1436,
                    **{"Specular IOR Level": 0.0})

    mix_shader_1 = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(cr_worn_final.outputs["Color"], mix_shader_1.inputs["Fac"])
    nt.links.new(original_bsdf_node.outputs[0], mix_shader_1.inputs[1])
    nt.links.new(bsdf_worn_1.outputs[0], mix_shader_1.inputs[2])

    # Scratch density via voronoi distance-to-edge
    map_horizontal = nt.nodes.new("ShaderNodeMapping")
    map_horizontal.inputs["Scale"].default_value = (10.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map_horizontal.inputs["Vector"])
    vor_horizontal = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(vor_horizontal, "feature"):
        try:
            vor_horizontal.feature = "DISTANCE_TO_EDGE"
        except TypeError:
            pass
    nt.links.new(map_horizontal.outputs["Vector"], vor_horizontal.inputs["Vector"])
    nt.links.new(n_scratch_density.outputs[0], vor_horizontal.inputs["Scale"])

    map_vertical = nt.nodes.new("ShaderNodeMapping")
    map_vertical.inputs["Scale"].default_value = (1.0, 10.0, 1.0)
    nt.links.new(tex_coord.outputs["Object"], map_vertical.inputs["Vector"])

    scale_density_2x = _vmath(nt, "SCALE", in0=n_scratch_density.outputs[0], scale=2.0)
    vor_vertical = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(vor_vertical, "feature"):
        try:
            vor_vertical.feature = "DISTANCE_TO_EDGE"
        except TypeError:
            pass
    nt.links.new(map_vertical.outputs["Vector"], vor_vertical.inputs["Vector"])
    nt.links.new(scale_density_2x.outputs[0], vor_vertical.inputs["Scale"])

    dist_h = vor_horizontal.outputs.get("Distance") or vor_horizontal.outputs[0]
    dist_v = vor_vertical.outputs.get("Distance") or vor_vertical.outputs[0]
    mul_dist = _math(nt, "MULTIPLY", dist_h, dist_v, clamp=True)
    cr_dist = _color_ramp(nt, mul_dist.outputs[0],
                          [(0.0, (1, 1, 1, 1)), (0.0073, (0, 0, 0, 1))])
    mul_edge_dist = _math(nt, "MULTIPLY",
                          cr_edge_scratch.outputs["Color"],
                          cr_dist.outputs["Color"],
                          clamp=True)
    mul_combined = _math(nt, "MULTIPLY",
                         mul_edge_mask.outputs[0],
                         mul_edge_dist.outputs[0],
                         clamp=True)

    # Worn-edge BSDF 2
    bsdf_worn_2 = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix_edge_color.outputs[2], bsdf_worn_2.inputs["Base Color"])
    _set_principled(bsdf_worn_2, Metallic=0.3855, Roughness=0.0,
                    **{"Specular IOR Level": 0.0})

    mix_shader_2 = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mul_scratch_opacity.outputs[0], mix_shader_2.inputs["Fac"])
    nt.links.new(mix_shader_1.outputs[0], mix_shader_2.inputs[1])
    nt.links.new(bsdf_worn_2.outputs[0], mix_shader_2.inputs[2])

    # Displacement
    scale_disp = _vmath(nt, "SCALE", in0=mul_combined.outputs[0], scale=2.0)
    if original_displacement_node is None:
        total_displacement = scale_disp.outputs[0]
    else:
        add_disp = _math(nt, "ADD",
                         original_displacement_node.outputs[0],
                         scale_disp.outputs[0],
                         clamp=True)
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
        except Exception as exc:
            print(f"  [edge_wear] failed on {mat.name}: {type(exc).__name__}: {exc}")

# ── Original geometry helpers (from objects_blender/tableware/CanFactory.py) ─

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for c in list(bpy.data.curves):
        bpy.data.curves.remove(c)
    for ng in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(ng)
    bpy.context.scene.cursor.location = (0, 0, 0)

def select_only(obj):
    bpy.ops.object.select_all(action='DESELECT')
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

def new_circle(vertices=32):
    bpy.ops.mesh.primitive_circle_add(vertices=vertices, location=(0, 0, 0))
    return bpy.context.active_object

def write_co(obj, coords):
    obj.data.vertices.foreach_set('co', coords.flatten().astype(np.float32))
    obj.data.update()

def make_circle_coords(radius, n_segments=256):
    angles = np.linspace(0, 2 * np.pi, n_segments, endpoint=False)
    return list(zip(radius * np.cos(angles), radius * np.sin(angles)))

def make_rounded_rect_coords(side, radius, n_corner=16):
    coords = []
    corners = [
        (side, side),
        (-side, side),
        (-side, -side),
        (side, -side),
    ]
    for cx, cy in corners:
        sx = 1 if cx > 0 else -1
        sy = 1 if cy > 0 else -1
        start_angle = np.arctan2(sy, sx) - np.pi / 2
        for j in range(n_corner):
            angle = start_angle + j * np.pi / (2 * n_corner)
            coords.append((cx + radius * np.cos(angle), cy + radius * np.sin(angle)))
    return coords

def make_coords(x_length, shape, skewness):
    if shape == 'circle':
        coords = make_circle_coords(x_length, 256)
    else:
        side = x_length * uniform(0.2, 0.8)
        coords = make_rounded_rect_coords(side, x_length - side, 16)
    return [(x, y / skewness) for x, y in coords]

def add_geo_cap(obj, cap_scale):
    tree = bpy.data.node_groups.new('GeoCap', 'GeometryNodeTree')
    tree.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    inp = tree.nodes.new('NodeGroupInput')
    inp.location = (-600, 0)
    out = tree.nodes.new('NodeGroupOutput')
    out.location = (600, 0)

    normal = tree.nodes.new('GeometryNodeInputNormal')
    normal.location = (-600, -200)
    sep = tree.nodes.new('ShaderNodeSeparateXYZ')
    sep.location = (-400, -200)
    tree.links.new(normal.outputs[0], sep.inputs[0])
    abs_node = tree.nodes.new('ShaderNodeMath')
    abs_node.operation = 'ABSOLUTE'
    abs_node.location = (-200, -200)
    tree.links.new(sep.outputs[2], abs_node.inputs[0])
    cmp = tree.nodes.new('FunctionNodeCompare')
    cmp.data_type = 'FLOAT'
    cmp.operation = 'GREATER_THAN'
    cmp.location = (0, -200)
    tree.links.new(abs_node.outputs[0], cmp.inputs[0])
    cmp.inputs[1].default_value = 1 - 1e-3

    extrude = tree.nodes.new('GeometryNodeExtrudeMesh')
    extrude.location = (0, 0)
    tree.links.new(inp.outputs[0], extrude.inputs['Mesh'])
    tree.links.new(cmp.outputs[0], extrude.inputs['Selection'])
    extrude.inputs['Offset Scale'].default_value = 0.0

    scale_elem = tree.nodes.new('GeometryNodeScaleElements')
    scale_elem.location = (200, 0)
    tree.links.new(extrude.outputs['Mesh'], scale_elem.inputs['Geometry'])
    tree.links.new(extrude.outputs['Top'], scale_elem.inputs['Selection'])
    scale_elem.inputs['Scale'].default_value = cap_scale

    extrude2 = tree.nodes.new('GeometryNodeExtrudeMesh')
    extrude2.location = (400, 0)
    tree.links.new(scale_elem.outputs[0], extrude2.inputs['Mesh'])
    tree.links.new(extrude.outputs['Top'], extrude2.inputs['Selection'])
    extrude2.inputs['Offset Scale'].default_value = -uniform(0.005, 0.01)

    tree.links.new(extrude2.outputs['Mesh'], out.inputs[0])

    mod = obj.modifiers.new('GeoCap', 'NODES')
    mod.node_group = tree
    select_only(obj)
    bpy.ops.object.modifier_apply(modifier=mod.name)

def sel_none():
    for o in list(bpy.context.selected_objects):
        o.select_set(False)
    if bpy.context.active_object:
        bpy.context.active_object.select_set(False)

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
    result = bpy.context.active_object
    sel_none()
    return result

def make_wrap(coords, z_length):
    """Create a thin cylinder sleeve for the can label.

    Replicates CanFactory.make_wrap() -- a cylinder whose
    top/bottom n-gon faces are deleted, then repositioned to wrap the
    can body. The wrap gets a separate material slot (graphicdesign).
    """

    n_verts = len(coords)
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=n_verts, depth=1, radius=1, location=(0, 0, 0.5))
    obj = bpy.context.active_object
    apply_transform(obj, loc=True)

    # Delete top and bottom n-gon faces (faces with > 4 verts)
    select_only(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    geom = [f for f in bm.faces if len(f.verts) > 4]
    bmesh.ops.delete(bm, geom=geom, context="FACES_ONLY")
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')

    # Reposition vertices to match the can cross-section
    lowest = z_length * float(uniform(0, 0.1))
    highest = z_length * float(uniform(0.9, 1.0))
    new_coords = np.concatenate(
        [np.array([[x, y, lowest], [x, y, highest]]) for x, y in coords]
    )
    write_co(obj, new_coords)

    # Slightly larger than body to prevent z-fighting
    obj.scale = (1 + 1e-3, 1 + 1e-3, 1)
    apply_transform(obj)

    return obj

# CanFactory.__init__ call order:
#   1. self.surface = weighted_sample(metals)()()
#   2. self.wrap_surface = weighted_sample(graphicdesign)()()
#   3. (Text special case -- skipped in standalone)
#   4. scratch_prob, edge_wear_prob = wear_tear_prob -> [0.5, 0.5]
#   5. self.scratch = None if uniform() > 0.5 else Scratches()
#   6. self.edge_wear = None if uniform() > 0.5 else EdgeWear()
#   7. self.texture_shared = uniform() < 0.2

SEED = int(os.environ.get('SEED', 0))
seed_all(SEED)

MAT_BODY = get_material("metals", "CanBody")
MAT_WRAP = get_material("graphicdesign", "CanLabel")

# wear_tear probability gates (50% each)
_scratch_prob, _edge_wear_prob = WEAR_TEAR_PROB
WEAR_DO_SCRATCH = (np.random.uniform() <= _scratch_prob)
WEAR_DO_EDGEWEAR = (np.random.uniform() <= _edge_wear_prob)

# texture_shared (consumed to keep RNG alignment, not used in standalone)
_texture_shared = np.random.uniform() < 0.2

# --- Geometry build with per-part material assignment ---
def sample_params(seed=0):
    """Sample geometry parameters. Re-seeds numpy for geometry isolation."""

    np.random.seed(seed)
    x_length = float(np.exp(np.random.uniform(np.log(0.05), np.log(0.1))))
    z_length = x_length * float(np.exp(np.random.uniform(np.log(0.5), np.log(2.5))))
    shape = np.random.choice(['circle', 'rectangle'])
    skewness = float(uniform(1, 2.5)) if uniform() < 0.5 else 1.0
    cap_scale = float(uniform(0.96, 0.98))
    return dict(
        x_length=x_length,
        z_length=z_length,
        shape=shape,
        skewness=skewness,
        cap_scale=cap_scale,
    )

def build(seed=SEED):
    clear_scene()

    p = sample_params(seed)
    x_length = p["x_length"]
    z_length = p["z_length"]
    shape = p["shape"]
    skewness = p["skewness"]
    cap_scale = p["cap_scale"]

    coords = make_coords(x_length, shape, skewness)
    n_verts = len(coords)

    # ── Body ──
    body = new_circle(vertices=n_verts)
    write_co(body, np.array([[x, y, 0] for x, y in coords]))
    select_only(body)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.edge_face_add()
    bpy.ops.object.mode_set(mode='OBJECT')
    modify_mesh(body, 'SOLIDIFY', thickness=z_length)
    add_geo_cap(body, cap_scale)

    # Material on body BEFORE join
    body.data.materials.append(MAT_BODY)

    # ── Wrap (label sleeve) ──
    wrap = make_wrap(coords, z_length)
    wrap.data.materials.append(MAT_WRAP)

    # ── Join ──
    obj = join([body, wrap])

    # ── wear_tear ──
    if obj is not None:
        if WEAR_DO_SCRATCH:
            apply_scratches(obj)
        if WEAR_DO_EDGEWEAR:
            apply_edge_wear(obj)

    return obj

build(SEED)

