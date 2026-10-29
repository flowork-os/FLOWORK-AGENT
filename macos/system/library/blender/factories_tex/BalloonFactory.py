# [FL_INDEX: keywords="blender_factory, procedural_3d, BalloonFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: BalloonFactory | Category: factories_tex
# Prompt: A 3D model of a balloon letter word sign rendered from a front perspective. The sign features a sequence of inflated, tubular letter forms spelling a random word, with rounded bubbly geometry, a dark outer surface, and a vivid blue-tinted interior visible through the open letterforms.

"""objects_blender_texture/wall_decorations/BalloonFactory.py

Texture-enabled conversion of objects_blender/wall_decorations/BalloonFactory.py.
Geometry is copied verbatim from the source; the material is sampled in Phase 1
at module level using the raw SEED's

    with FixedSeed(self.factory_seed):
        self.thickness = uniform(0.06, 0.1)
        material_gen = weighted_sample(material_assignments.decorative_metal)()
        self.surface = material_gen()

uniformly weighted list of four metal shaders:

    BrushedMetal, GalvanizedMetal, GrainedMetal, HammeredMetal

raw-bpy node-tree builders. BalloonFactory does NOT sample wear_tear, so this
textured script also has no WEAR_DO_* gates.
"""


import os
import math
import random
import colorsys
import string

import bpy
import bmesh
import numpy as np

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

def rgb2hsv(rgb):
    r, g, b = rgb[0], rgb[1], rgb[2]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return (h, s, v)

def hex2rgb(hexval):
    r = ((hexval >> 16) & 0xFF) / 255.0
    g = ((hexval >> 8) & 0xFF) / 255.0
    b = (hexval & 0xFF) / 255.0
    return (r, g, b)

def _mat_log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

_NATURAL_BASE_COLORS = [
    (0xC0C0C0, 1.0),
    (0x8C7853, 1.0),
    (0xBDBAAE, 1.0),
    (0xA9ACB6, 1.0),
    (0xB6AFA9, 1.0),
]

def _weighted_hex_choice(table):
    hexes, weights = zip(*table)
    weights = np.array(weights, dtype=float)
    weights = weights / weights.sum()
    return int(np.random.choice(hexes, p=weights))

def metal_natural_hsv():
    hexval = _weighted_hex_choice(_NATURAL_BASE_COLORS)
    h, s, v = rgb2hsv(hex2rgb(hexval))
    return (
        h + float(np.random.uniform(-0.1, 0.1)),
        s + float(np.random.uniform(-0.1, 0.1)),
        v * _mat_log_uniform(0.5, 0.2),
    )

def metal_hsv():
    """py:metal_hsv."""

    if np.random.uniform() < 0.2:
        return metal_natural_hsv()
    return (
        float(np.random.uniform(0, 1)),
        float(np.random.uniform(0.3, 0.6)),
        _mat_log_uniform(0.02, 0.5),
    )

# --- shader helpers --------------------------------------------------------

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

def _connect_output(nt, bsdf, displacement=None):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    if displacement is not None:
        nt.links.new(displacement, out.inputs["Displacement"])
    return out

# ----------------------------------------------------------------------------
# make_brushed_metal — port of metal/brushed_metal.py.
# ----------------------------------------------------------------------------
def make_brushed_metal(name="BrushedMetal", base_color_hsv=None) -> bpy.types.Material:
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    seed_val = float(np.random.uniform(-1000.0, 1000.0))

    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # Mapping used as a mix target AND as a structural vector for noise_texture_2
    mapping_1 = nt.nodes.new("ShaderNodeMapping")
    mapping_1.inputs["Scale"].default_value = (0.2, 0.2, 5.0)
    nt.links.new(tex_coord.outputs["Object"], mapping_1.inputs["Vector"])

    # noise_texture_2 — high-frequency streak noise
    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise2, "noise_dimensions"):
        try: noise2.noise_dimensions = "4D"
        except TypeError: pass
    noise2.inputs["Scale"].default_value = 100.0
    if "Detail" in noise2.inputs:     noise2.inputs["Detail"].default_value = 15.0
    if "Roughness" in noise2.inputs:  noise2.inputs["Roughness"].default_value = 0.4
    if "Distortion" in noise2.inputs: noise2.inputs["Distortion"].default_value = 0.1
    if "W" in noise2.inputs:          noise2.inputs["W"].default_value = seed_val
    nt.links.new(mapping_1.outputs["Vector"], noise2.inputs["Vector"])

    # noise_texture_1 — low-frequency colour perturbation for the mapping base
    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise1, "noise_dimensions"):
        try: noise1.noise_dimensions = "4D"
        except TypeError: pass
    noise1.inputs["Scale"].default_value = 0.1
    if "Detail" in noise1.inputs:     noise1.inputs["Detail"].default_value = 15.0
    if "Roughness" in noise1.inputs:  noise1.inputs["Roughness"].default_value = 0.0
    if "W" in noise1.inputs:          noise1.inputs["W"].default_value = seed_val
    nt.links.new(tex_coord.outputs["Object"], noise1.inputs["Vector"])

    # Mix(mapping, noise_texture_1, factor=0.2) — RGBA
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs[0].default_value = 0.2
    nt.links.new(mapping_1.outputs["Vector"], mix.inputs[6])
    nt.links.new(noise1.outputs["Color"], mix.inputs[7])

    # noise_texture (the third, uses the mix result as its vector)
    noise3 = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise3, "noise_dimensions"):
        try: noise3.noise_dimensions = "4D"
        except TypeError: pass
    noise3.inputs["Scale"].default_value = 100.0
    if "Detail" in noise3.inputs:     noise3.inputs["Detail"].default_value = 15.0
    if "Roughness" in noise3.inputs:  noise3.inputs["Roughness"].default_value = 0.6
    if "Distortion" in noise3.inputs: noise3.inputs["Distortion"].default_value = 0.1
    if "W" in noise3.inputs:          noise3.inputs["W"].default_value = seed_val
    nt.links.new(mix.outputs[2], noise3.inputs["Vector"])

    # Mix_1(noise_texture_2.Fac, noise_texture.Fac, factor=1.0, blend=DARKEN)
    mix1 = nt.nodes.new("ShaderNodeMix")
    mix1.data_type = "RGBA"
    mix1.blend_type = "DARKEN"
    mix1.inputs[0].default_value = 1.0
    nt.links.new(_noise_fac_output(noise2), mix1.inputs[6])
    nt.links.new(_noise_fac_output(noise3), mix1.inputs[7])

    # MapRange for HSV value multiplier
    map_range = nt.nodes.new("ShaderNodeMapRange")
    map_range.inputs[1].default_value = 0.4
    map_range.inputs[2].default_value = 0.6
    map_range.inputs[3].default_value = 0.8
    map_range.inputs[4].default_value = 1.2
    nt.links.new(mix1.outputs[2], map_range.inputs[0])

    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    hsv_node.inputs["Color"].default_value = hsv2rgba(base_color_hsv)
    nt.links.new(map_range.outputs["Result"], hsv_node.inputs["Value"])

    # MapRange for roughness
    map_range_r = nt.nodes.new("ShaderNodeMapRange")
    map_range_r.inputs[1].default_value = 0.4
    map_range_r.inputs[2].default_value = 0.6
    map_range_r.inputs[3].default_value = 0.2
    map_range_r.inputs[4].default_value = 0.3
    nt.links.new(mix1.outputs[2], map_range_r.inputs[0])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Metallic=1.0, **{"Specular IOR Level": 0.0})
    nt.links.new(hsv_node.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(map_range_r.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

# ----------------------------------------------------------------------------
# make_galvanized_metal — port of metal/galvanized_metal.py.
# ----------------------------------------------------------------------------
def make_galvanized_metal(name="GalvanizedMetal", base_color_hsv=None) -> bpy.types.Material:
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    seed_val = float(np.random.uniform(-1000.0, 1000.0))

    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # low-frequency perturbation of the object coords
    noise = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise, "noise_dimensions"):
        try: noise.noise_dimensions = "4D"
        except TypeError: pass
    noise.inputs["Scale"].default_value = 5.0
    if "Detail" in noise.inputs:     noise.inputs["Detail"].default_value = 15.0
    if "Roughness" in noise.inputs:  noise.inputs["Roughness"].default_value = 0.4
    if "Distortion" in noise.inputs: noise.inputs["Distortion"].default_value = 0.2
    if "W" in noise.inputs:          noise.inputs["W"].default_value = seed_val
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.clamp_factor = False
    mix.inputs[0].default_value = 0.05
    nt.links.new(tex_coord.outputs["Object"], mix.inputs[6])
    nt.links.new(noise.outputs["Color"], mix.inputs[7])

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(voronoi, "voronoi_dimensions"):
        try: voronoi.voronoi_dimensions = "4D"
        except TypeError: voronoi.voronoi_dimensions = "3D"
    if hasattr(voronoi, "distance"):
        try: voronoi.distance = "MINKOWSKI"
        except TypeError: pass
    voronoi.inputs["Scale"].default_value = 500.0
    if "W" in voronoi.inputs:
        voronoi.inputs["W"].default_value = seed_val
    nt.links.new(mix.outputs[2], voronoi.inputs["Vector"])

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

# ----------------------------------------------------------------------------
# make_grained_metal — port of metal/grained_and_polished_metal.py.
# ----------------------------------------------------------------------------
def make_grained_metal(name="GrainedMetal", base_color_hsv=None) -> bpy.types.Material:
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    # order mirrors shader_grained_metal: roughness, seed, base_color_hsv
    roughness_input = float(np.random.uniform(0.0, 1.0))
    seed_val = float(np.random.uniform(-1000.0, 1000.0))

    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    noise = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise, "noise_dimensions"):
        try: noise.noise_dimensions = "4D"
        except TypeError: pass
    noise.inputs["Scale"].default_value = 2000.0
    if "Detail" in noise.inputs:     noise.inputs["Detail"].default_value = 15.0
    if "Distortion" in noise.inputs: noise.inputs["Distortion"].default_value = 2.0
    if "W" in noise.inputs:          noise.inputs["W"].default_value = seed_val
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

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

# ----------------------------------------------------------------------------
# make_hammered_metal — port of metal/hammered_metal.py.
# ----------------------------------------------------------------------------
def make_hammered_metal(name="HammeredMetal", base_color_hsv=None) -> bpy.types.Material:
    if base_color_hsv is None:
        base_color_hsv = metal_hsv()
    # order: seed, base_color_hsv already sampled, scale
    seed_val = float(np.random.uniform(-1000.0, 1000.0))
    scale_val = _mat_log_uniform(0.8, 1.2)

    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    noise = nt.nodes.new("ShaderNodeTexNoise")
    if hasattr(noise, "noise_dimensions"):
        try: noise.noise_dimensions = "4D"
        except TypeError: pass
    noise.inputs["Scale"].default_value = 20.0 * scale_val
    if "Detail" in noise.inputs:     noise.inputs["Detail"].default_value = 15.0
    if "Roughness" in noise.inputs:  noise.inputs["Roughness"].default_value = 0.4
    if "Distortion" in noise.inputs: noise.inputs["Distortion"].default_value = 0.2
    if "W" in noise.inputs:          noise.inputs["W"].default_value = seed_val
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])

    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.clamp_factor = False
    mix.inputs[0].default_value = 0.01
    nt.links.new(tex_coord.outputs["Object"], mix.inputs[6])
    nt.links.new(noise.outputs["Color"], mix.inputs[7])

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    if hasattr(voronoi, "voronoi_dimensions"):
        try: voronoi.voronoi_dimensions = "4D"
        except TypeError: voronoi.voronoi_dimensions = "3D"
    if hasattr(voronoi, "feature"):
        try: voronoi.feature = "SMOOTH_F1"
        except TypeError: pass
    voronoi.inputs["Scale"].default_value = 300.0 * scale_val
    if "Smoothness" in voronoi.inputs:
        voronoi.inputs["Smoothness"].default_value = 0.2
    if "W" in voronoi.inputs:
        voronoi.inputs["W"].default_value = seed_val
    nt.links.new(mix.outputs[2], voronoi.inputs["Vector"])

    mul_d = nt.nodes.new("ShaderNodeMath")
    mul_d.operation = "MULTIPLY"
    mul_d.inputs[1].default_value = scale_val
    dist_out = voronoi.outputs.get("Distance") or voronoi.outputs[0]
    nt.links.new(dist_out, mul_d.inputs[0])

    pow_node = nt.nodes.new("ShaderNodeMath")
    pow_node.operation = "POWER"
    pow_node.inputs[1].default_value = 2.5
    nt.links.new(mul_d.outputs[0], pow_node.inputs[0])

    mul_scale = nt.nodes.new("ShaderNodeMath")
    mul_scale.operation = "MULTIPLY"
    mul_scale.inputs[1].default_value = _mat_log_uniform(0.001, 0.003)
    nt.links.new(pow_node.outputs[0], mul_scale.inputs[0])

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_scale.outputs[0], disp.inputs["Height"])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(
        bsdf, Metallic=1.0,
        **{"Specular IOR Level": 0.0, "Base Color": hsv2rgba(base_color_hsv), "Roughness": 0.1},
    )
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat

# ----------------------------------------------------------------------------
# Registry dispatch — faithful port of weighted_sample(decorative_metal)().
# decorative_metal = [(BrushedMetal, 1.0), (GalvanizedMetal, 1.0),
#                     (GrainedMetal, 1.0), (HammeredMetal, 1.0)]
# weighted_sample uses np.random.choice(classes, p=weights/weights.sum()),
# then the factory calls .generate() on the picked class, which samples
# base_color_hsv / seed / etc. internally.
# ----------------------------------------------------------------------------
_DECORATIVE_METAL_CHOICES = (
    make_brushed_metal,
    make_galvanized_metal,
    make_grained_metal,
    make_hammered_metal,
)
_DECORATIVE_METAL_WEIGHTS = (1.0, 1.0, 1.0, 1.0)

def get_decorative_metal_material(name: str = "BalloonMetal") -> bpy.types.Material:
    probs = np.array(_DECORATIVE_METAL_WEIGHTS, dtype=float)
    probs = probs / probs.sum()
    idx = int(np.random.choice(len(_DECORATIVE_METAL_CHOICES), p=probs))
    return _DECORATIVE_METAL_CHOICES[idx](name=name)

# --- Original geometry helpers (copied verbatim from objects_blender/) ---

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

def clip_gaussian(mean, std, lo, hi, rng):
    v = rng.normal(mean, std)
    return float(np.clip(v, lo, hi))

def generate_text(rng):
    charset = list(string.ascii_lowercase + string.ascii_uppercase + string.digits)
    weights = np.concatenate([
        1.5 * np.ones(len(string.ascii_lowercase)),
        0.5 * np.ones(len(string.ascii_uppercase)),
        0.5 * np.ones(len(string.digits)),
    ])
    weights /= weights.sum()
    n_chars = int(clip_gaussian(3, 7, 2, 15, rng))
    n_chars = max(2, min(n_chars, 15))
    return "".join(rng.choice(charset, size=n_chars, replace=True, p=weights))

def subdivide_edge_ring(obj, cuts, axis):
    """Subdivide edges aligned with the given axis direction."""

    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.edges.ensure_lookup_table()

    ax = np.array(axis, dtype=float)
    ax /= np.linalg.norm(ax) + 1e-9

    edges_to_sub = []
    for e in bm.edges:
        d = np.array(e.verts[1].co) - np.array(e.verts[0].co)
        d_norm = np.linalg.norm(d)
        if d_norm < 1e-6:
            continue
        alignment = abs(np.dot(d / d_norm, ax))
        if alignment > 0.7:
            edges_to_sub.append(e)

    if edges_to_sub:
        bmesh.ops.subdivide_edges(bm, edges=edges_to_sub, cuts=cuts)
    bm.to_mesh(me)
    bm.free()
    me.update()

SEED = int(os.environ.get('SEED', 0))
seed_all(SEED)

# BalloonFactory.__init__ order under FixedSeed(factory_seed):
#   1. self.thickness = uniform(0.06, 0.1)        -> consumes 1 np.random draw
#   2. material_gen = weighted_sample(decorative_metal)()
#        -> np.random.choice picks metal class
#   3. self.surface = material_gen()
#        -> class.generate() -> shader_* which samples base_color_hsv + seed
#   4. self.rel_scale = uniform(0.2, 0.3) * 4
#   5. self.displace  = uniform(0.02, 0.04)
#
# We preserve this exact numpy.random consumption order here so the material
# but their values are not used (geometry re-seeds with np.random.default_rng
# inside build()); we draw them only to keep the RNG stream aligned.
_init_thickness = float(np.random.uniform(0.06, 0.1))       # (1)
MAT_BALLOON = get_decorative_metal_material(name="BalloonMetal")  # (2)+(3)
_init_rel_scale = float(np.random.uniform(0.2, 0.3)) * 4    # (4)
_init_displace = float(np.random.uniform(0.02, 0.04))       # (5)
# BalloonFactory does NOT sample wear_tear — no WEAR_DO_* gates.

# --- Geometry build (verbatim from objects_blender/, with material append) ---
def build(seed=SEED):
    rng = np.random.default_rng(seed)
    np.random.seed(seed)
    clear_scene()

    alpha = 0.8
    thickness = float(rng.uniform(0.06, 0.1))
    rel_scale = float(rng.uniform(0.2, 0.3)) * 4
    displace_strength = float(rng.uniform(0.02, 0.04))

    # Create text object
    bpy.ops.object.text_add(location=(0, 0, 0))
    obj = bpy.context.active_object

    # Enter edit mode, clear default "Text", insert random text
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.font.select_all()
    bpy.ops.font.delete(type='SELECTION')
    text = generate_text(rng).upper()
    bpy.ops.font.text_insert(text=text)
    bpy.ops.object.mode_set(mode='OBJECT')

    # Convert text to mesh
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.active_object

    # Remesh fill (voxel remesh to fill holes)
    mod = obj.modifiers.new("remesh", "REMESH")
    mod.mode = 'VOXEL'
    mod.voxel_size = 0.02
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)

    # Solidify
    mod = obj.modifiers.new("solidify", "SOLIDIFY")
    mod.thickness = thickness
    mod.offset = 0.5
    bpy.ops.object.modifier_apply(modifier=mod.name)

    # Subdivide edge ring along Z for inflation shape
    subdivide_edge_ring(obj, 8, (0, 0, 1))

    # Subsurf
    mod = obj.modifiers.new("subsurf", "SUBSURF")
    mod.levels = 1
    mod.render_levels = 1
    bpy.ops.object.modifier_apply(modifier=mod.name)

    # Scale to rel_scale and orient
    obj.scale = [rel_scale] * 3
    obj.rotation_euler = (math.pi / 2, 0, math.pi / 2)
    apply_tf(obj)

    # Displace for surface micro-detail
    tex = bpy.data.textures.new("balloon_tex", type="CLOUDS")
    tex.noise_scale = 0.1
    mod = obj.modifiers.new("displace", "DISPLACE")
    mod.texture = tex
    mod.strength = displace_strength
    mod.mid_level = 0.5
    bpy.ops.object.modifier_apply(modifier=mod.name)

    # Smooth
    mod = obj.modifiers.new("smooth", "SMOOTH")
    mod.iterations = 5
    bpy.ops.object.modifier_apply(modifier=mod.name)

    apply_tf(obj)
    obj.name = "BalloonFactory"

    # Attach the metal material sampled in Phase 1
    if obj.data.materials:
        obj.data.materials[0] = MAT_BALLOON
    else:
        obj.data.materials.append(MAT_BALLOON)

    return obj

build(SEED)

