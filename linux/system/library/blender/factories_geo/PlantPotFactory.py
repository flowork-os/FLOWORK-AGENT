# [FL_INDEX: keywords="blender_factory, procedural_3d, PlantPotFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: PlantPotFactory | Category: factories_geo
# Prompt: A 3D model of a wide hemispherical plant pot rendered from a slightly elevated three-quarter perspective. The pot features a smooth rounded bowl shape with a wide open rim, a uniform deep purple-blue exterior, a glossy appearance, and a flat or slightly recessed base.

"""PlantPotFactory — textured standalone Blender script (pot only, no plant/dirt).
Surface: decorative_hard pool (VaseCeramic/ColoredGlass/Marble/GlassVolume/Ceramic/metals).
Wear-tear DISABLED (PanFactory family). Geometry from objects_blender/tableware/PlantPotFactory.py.
"""
# SEED-deterministic: all random calls seeded from SEED

import os
import math
import random
import colorsys
import hashlib

import bmesh
import bpy
import numpy as np
from numpy.random import uniform


# ============================================================================
# === Seed ===================================================================
# ============================================================================

SEED = int(os.environ.get("SEED", "0"))


def int_hash(x):
    m = hashlib.md5()
    for s in x:
        m.update(str(s).encode("utf-8"))
    return abs(int(m.hexdigest(), 16)) % (2**32 - 1)


def seed_all(seed):
    np.random.seed(seed)
    random.seed(seed)


# ============================================================================
# === Utilities ==============================================================
# ============================================================================

def log_uniform(low, high, size=None):
    return np.exp(np.random.uniform(np.log(low), np.log(high), size))


def hsv2rgba(hsv):
    h, s, v = hsv
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)


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

def weighted_sample(registry):
    classes, weights = zip(*registry)
    weights = np.array(weights, dtype=float)
    return classes[int(np.random.choice(len(classes), p=weights / weights.sum()))]


class FixedSeed:
    def __init__(self, seed):
        self.seed = int(seed)
    def __enter__(self):
        self._py = random.getstate()
        self._np = np.random.get_state()
        random.seed(self.seed)
        np.random.seed(self.seed)
    def __exit__(self, *_):
        random.setstate(self._py)
        np.random.set_state(self._np)


# ============================================================================
# === Scene helpers ==========================================================
# ============================================================================

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for c in list(bpy.data.curves):
        bpy.data.curves.remove(c)
    for ng in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(ng)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
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


def subsurf(obj, levels, simple=False):
    if levels > 0:
        modify_mesh(obj, 'SUBSURF',
                     levels=levels, render_levels=levels,
                     subdivision_type='SIMPLE' if simple else 'CATMULL_CLARK')


def new_base_circle(vertices=32):
    bpy.ops.mesh.primitive_circle_add(location=(0, 0, 0), vertices=vertices)
    return bpy.context.active_object


def join_objects(objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    obj = bpy.context.active_object
    obj.location = 0, 0, 0
    obj.rotation_euler = 0, 0, 0
    obj.scale = 1, 1, 1
    bpy.ops.object.select_all(action='DESELECT')
    return obj


# ============================================================================
# === Material helpers =======================================================
# ============================================================================

def _new_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat


def _set_principled(bsdf, **kw):
    aliases = {
        "Specular IOR Level": ("Specular IOR Level", "Specular"),
        "Coat Weight": ("Coat Weight", "Clearcoat"),
        "Coat Roughness": ("Coat Roughness", "Clearcoat Roughness"),
        "Subsurface Weight": ("Subsurface Weight", "Subsurface"),
        "Transmission Weight": ("Transmission Weight", "Transmission"),
    }
    for k, v in kw.items():
        for name in aliases.get(k, (k,)):
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


def _math(nt, op, a, b):
    node = nt.nodes.new("ShaderNodeMath")
    node.operation = op
    if hasattr(a, "outputs"):
        nt.links.new(a.outputs[0] if hasattr(a.outputs[0], "links") else a, node.inputs[0])
    elif isinstance(a, (int, float)):
        node.inputs[0].default_value = float(a)
    else:
        nt.links.new(a, node.inputs[0])

    if hasattr(b, "outputs"):
        nt.links.new(b.outputs[0] if hasattr(b.outputs[0], "links") else b, node.inputs[1])
    elif isinstance(b, (int, float)):
        node.inputs[1].default_value = float(b)
    else:
        nt.links.new(b, node.inputs[1])
    return node


def _connect_output(nt, bsdf, displacement=None):
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    if displacement is not None:
        nt.links.new(displacement, out.inputs["Displacement"])
    return out


# ============================================================================
# === POT material factories (decorative_hard pool) ==========================
# ============================================================================

# --- Ceramic ---------------------------------------------------------------
def make_ceramic(name="Ceramic"):
    mat = _new_material(name)
    nt = mat.node_tree
    if np.random.uniform() < 0.8:
        color = hsv2rgba((np.random.uniform(0, 1),
                          np.random.uniform(0.2, 0.4),
                          float(log_uniform(0.3, 0.6))))
    else:
        color = hsv2rgba((0.0, 0.0, float(log_uniform(0.3, 0.6))))

    noise_r = nt.nodes.new("ShaderNodeTexNoise")
    noise_r.inputs["Scale"].default_value = float(log_uniform(20, 40))
    fc_r = _build_float_curve(nt, _noise_fac_output(noise_r), [(0, 0.0), (1, 0.8)])

    noise_c = nt.nodes.new("ShaderNodeTexNoise")
    noise_c.inputs["Scale"].default_value = float(log_uniform(20, 40))
    fc_c = _build_float_curve(nt, _noise_fac_output(noise_c), [(0, 0.0), (1, 0.8)])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, **{
        "Base Color": color,
        "Coat Weight": 1.0,
        "Specular IOR Level": 1.0,
        "Subsurface Weight": float(np.random.uniform(0.02, 0.05)),
    })
    nt.links.new(fc_r.outputs["Value"], bsdf.inputs["Roughness"])
    if "Coat Roughness" in bsdf.inputs:
        nt.links.new(fc_c.outputs["Value"], bsdf.inputs["Coat Roughness"])

    noise_d = nt.nodes.new("ShaderNodeTexNoise")
    noise_d.inputs["Scale"].default_value = float(log_uniform(20, 40))
    mul_d = _math(nt, "MULTIPLY", _noise_fac_output(noise_d), float(log_uniform(0.001, 0.005)))
    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_d.outputs[0], disp.inputs["Height"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


# --- VaseCeramic -----------------------------------------------------------
def make_vase_ceramic(name="VaseCeramic"):
    mat = _new_material(name)
    nt = mat.node_tree
    hsv = (uniform(0.0, 1.0), uniform(0.0, 0.75), uniform(0.0, 0.3))
    color = hsv2rgba(hsv)

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, **{
        "Base Color": color,
        "Subsurface Weight": 0.3,
        "Specular IOR Level": 0.2,
        "Roughness": 0.05,
        "Coat Weight": 0.5,
        "Coat Roughness": 0.05,
        "IOR": 1.47,
    })
    _connect_output(nt, bsdf)
    return mat


# --- ColoredGlass ---------------------------------------------------------
def make_colored_glass(name="ColoredGlass"):
    mat = _new_material(name)
    nt = mat.node_tree
    hsv = (uniform(0.0, 1.0), uniform(0.0, 0.2), 1.0)
    glass = nt.nodes.new("ShaderNodeBsdfGlass")
    glass.inputs["Color"].default_value = hsv2rgba(hsv)
    glass.inputs["Roughness"].default_value = float(uniform(0.05, 0.2))
    _connect_output(nt, glass)
    return mat


# --- Marble ----------------------------------------------------------------
def make_marble(name="Marble"):
    mat = _new_material(name)
    nt = mat.node_tree
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    scale_node = nt.nodes.new("ShaderNodeVectorMath")
    scale_node.operation = "SCALE"
    nt.links.new(tex_coord.outputs["Object"], scale_node.inputs[0])

    rotate_node = nt.nodes.new("ShaderNodeVectorRotate")
    rotate_node.rotation_type = "EULER_XYZ"
    nt.links.new(scale_node.outputs["Vector"], rotate_node.inputs["Vector"])

    seed_val = 0.0
    scale_val = 3.0
    add_val = scale_val + 1.0

    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    noise1.noise_dimensions = "4D"
    nt.links.new(rotate_node.outputs["Vector"], noise1.inputs["Vector"])
    noise1.inputs["W"].default_value = seed_val
    noise1.inputs["Scale"].default_value = scale_val
    noise1.inputs["Detail"].default_value = 15.0

    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    noise2.noise_dimensions = "4D"
    nt.links.new(rotate_node.outputs["Vector"], noise2.inputs["Vector"])
    noise2.inputs["W"].default_value = seed_val
    noise2.inputs["Scale"].default_value = add_val
    noise2.inputs["Detail"].default_value = 15.0

    mr = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(_noise_fac_output(noise2), mr.inputs["Value"])
    mr.inputs[1].default_value = 0.48
    mr.inputs[2].default_value = 0.60

    noise3 = nt.nodes.new("ShaderNodeTexNoise")
    nt.links.new(_noise_fac_output(noise1), noise3.inputs["Vector"])
    noise3.inputs["Scale"].default_value = 8.0
    noise3.inputs["Detail"].default_value = 15.0

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi.feature = "DISTANCE_TO_EDGE"
    voronoi.voronoi_dimensions = "4D"
    nt.links.new(_noise_fac_output(noise3), voronoi.inputs["Vector"])
    voronoi.inputs["W"].default_value = 1.64
    voronoi.inputs["Scale"].default_value = 3.0

    cr1 = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(voronoi.outputs["Distance"], cr1.inputs["Fac"])
    cr1.color_ramp.elements[0].position = 0.0
    cr1.color_ramp.elements[0].color = (1, 1, 1, 1)
    cr1.color_ramp.elements[1].position = 0.03
    cr1.color_ramp.elements[1].color = (0, 0, 0, 1)

    mul_mr_cr1 = _math(nt, "MULTIPLY", mr.outputs["Result"], cr1.outputs["Color"])

    noise4 = nt.nodes.new("ShaderNodeTexNoise")
    noise4.noise_dimensions = "4D"
    nt.links.new(_noise_fac_output(noise1), noise4.inputs["Vector"])
    noise4.inputs["W"].default_value = seed_val
    noise4.inputs["Scale"].default_value = 8.0
    noise4.inputs["Detail"].default_value = 15.0

    mix1 = nt.nodes.new("ShaderNodeMix")
    mix1.data_type = "RGBA"
    mix1.inputs[0].default_value = 0.8
    nt.links.new(_noise_fac_output(noise1), mix1.inputs[6])
    nt.links.new(_noise_fac_output(noise4), mix1.inputs[7])

    cr2 = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(mix1.outputs[2], cr2.inputs["Fac"])
    cr2.color_ramp.elements[0].position = 0.3
    cr2.color_ramp.elements[0].color = (1, 1, 1, 1)
    cr2.color_ramp.elements[1].position = 0.9
    cr2.color_ramp.elements[1].color = (0, 0, 0, 1)

    mix2 = nt.nodes.new("ShaderNodeMix")
    mix2.data_type = "RGBA"
    nt.links.new(mul_mr_cr1.outputs[0], mix2.inputs[0])
    nt.links.new(cr2.outputs["Color"], mix2.inputs[6])
    mix2.inputs[7].default_value = (0.0376, 0.0179, 0.0033, 1.0)

    disp = nt.nodes.new("ShaderNodeDisplacement")
    nt.links.new(mul_mr_cr1.outputs[0], disp.inputs["Height"])
    disp.inputs["Midlevel"].default_value = 0.0
    disp.inputs["Scale"].default_value = 0.02

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix1.outputs[2], bsdf.inputs["Base Color"])
    _set_principled(bsdf, **{"Specular IOR Level": 0.6, "Roughness": 0.1})
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


# --- GlassVolume -----------------------------------------------------------
def make_glass_volume(name="GlassVolume"):
    mat = _new_material(name)
    nt = mat.node_tree
    if np.random.uniform() < 0.3:
        color = (1, 1, 1, 1)
    else:
        color = hsv2rgba((uniform(0, 1), uniform(0.5, 0.9), uniform(0.6, 0.9)))

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    _set_principled(bsdf, Roughness=0.0, **{"Transmission Weight": 1.0})

    vol = nt.nodes.new("ShaderNodeVolumeAbsorption")
    vol.inputs["Color"].default_value = color
    vol.inputs["Density"].default_value = 100.0

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    nt.links.new(vol.outputs[0], out.inputs["Volume"])
    return mat


# --- BrushedMetal ----------------------------------------------------------
def make_brushed_metal(name="BrushedMetal"):
    mat = _new_material(name)
    nt = mat.node_tree
    base_color = hsv2rgba(metal_hsv())
    scale = 1.0
    seed_val = float(uniform(-1000, 1000))

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    mapping1 = nt.nodes.new("ShaderNodeMapping")
    mapping1.inputs["Scale"].default_value = (0.2, 0.2, 5.0)
    nt.links.new(tex_coord.outputs["Object"], mapping1.inputs["Vector"])

    mul_scale = _math(nt, "MULTIPLY", scale, 100.0)

    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    noise1.noise_dimensions = "4D"
    nt.links.new(mapping1.outputs["Vector"], noise1.inputs["Vector"])
    noise1.inputs["W"].default_value = seed_val
    nt.links.new(mul_scale.outputs[0], noise1.inputs["Scale"])
    noise1.inputs["Detail"].default_value = 15.0
    noise1.inputs["Roughness"].default_value = 0.4
    noise1.inputs["Distortion"].default_value = 0.1

    mapping2 = nt.nodes.new("ShaderNodeMapping")
    mapping2.inputs["Scale"].default_value = (1.0, 1.0, 20.0)
    nt.links.new(tex_coord.outputs["Object"], mapping2.inputs["Vector"])

    noise_low = nt.nodes.new("ShaderNodeTexNoise")
    noise_low.noise_dimensions = "4D"
    nt.links.new(tex_coord.outputs["Object"], noise_low.inputs["Vector"])
    noise_low.inputs["W"].default_value = seed_val
    noise_low.inputs["Scale"].default_value = 0.1
    noise_low.inputs["Detail"].default_value = 15.0
    noise_low.inputs["Roughness"].default_value = 0.0

    mix_vec = nt.nodes.new("ShaderNodeMix")
    mix_vec.data_type = "RGBA"
    mix_vec.inputs[0].default_value = 0.2
    nt.links.new(mapping2.outputs["Vector"], mix_vec.inputs[6])
    nt.links.new(noise_low.outputs["Color"], mix_vec.inputs[7])

    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    noise2.noise_dimensions = "4D"
    nt.links.new(mix_vec.outputs[2], noise2.inputs["Vector"])
    noise2.inputs["W"].default_value = seed_val
    nt.links.new(mul_scale.outputs[0], noise2.inputs["Scale"])
    noise2.inputs["Detail"].default_value = 15.0
    noise2.inputs["Roughness"].default_value = 0.6
    noise2.inputs["Distortion"].default_value = 0.1

    mix_dark = nt.nodes.new("ShaderNodeMix")
    mix_dark.data_type = "RGBA"
    mix_dark.blend_type = "DARKEN"
    mix_dark.inputs[0].default_value = 1.0
    nt.links.new(_noise_fac_output(noise1), mix_dark.inputs[6])
    nt.links.new(_noise_fac_output(noise2), mix_dark.inputs[7])

    mr_color = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(mix_dark.outputs[2], mr_color.inputs["Value"])
    mr_color.inputs[1].default_value = 0.4
    mr_color.inputs[2].default_value = 0.6
    mr_color.inputs[3].default_value = 0.8
    mr_color.inputs[4].default_value = 1.2

    hsv_node = nt.nodes.new("ShaderNodeHueSaturation")
    nt.links.new(mr_color.outputs["Result"], hsv_node.inputs["Value"])
    hsv_node.inputs["Color"].default_value = base_color

    mr_rough = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(mix_dark.outputs[2], mr_rough.inputs["Value"])
    mr_rough.inputs[1].default_value = 0.4
    mr_rough.inputs[2].default_value = 0.6
    mr_rough.inputs[3].default_value = 0.2
    mr_rough.inputs[4].default_value = 0.3

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(hsv_node.outputs["Color"], bsdf.inputs["Base Color"])
    _set_principled(bsdf, Metallic=1.0, **{"Specular IOR Level": 0.0})
    nt.links.new(mr_rough.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat


# --- GalvanizedMetal -------------------------------------------------------
def make_galvanized_metal(name="GalvanizedMetal"):
    mat = _new_material(name)
    nt = mat.node_tree
    base_color = hsv2rgba(metal_hsv())
    scale = 1.0
    seed_val = float(uniform(-1000, 1000))

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    mul_s = _math(nt, "MULTIPLY", scale, 5.0)

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.noise_dimensions = "4D"
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])
    noise.inputs["W"].default_value = seed_val
    nt.links.new(mul_s.outputs[0], noise.inputs["Scale"])
    noise.inputs["Detail"].default_value = 15.0
    noise.inputs["Roughness"].default_value = 0.4
    noise.inputs["Distortion"].default_value = 0.2

    mix_vec = nt.nodes.new("ShaderNodeMix")
    mix_vec.data_type = "RGBA"
    mix_vec.clamp_factor = False
    mix_vec.inputs[0].default_value = 0.05
    nt.links.new(tex_coord.outputs["Object"], mix_vec.inputs[6])
    nt.links.new(noise.outputs["Color"], mix_vec.inputs[7])

    mul_v = _math(nt, "MULTIPLY", scale, 500.0)

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi.voronoi_dimensions = "4D"
    voronoi.distance = "MINKOWSKI"
    nt.links.new(mix_vec.outputs[2], voronoi.inputs["Vector"])
    voronoi.inputs["W"].default_value = seed_val
    nt.links.new(mul_v.outputs[0], voronoi.inputs["Scale"])

    mr = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(voronoi.outputs["Color"], mr.inputs["Value"])
    mr.inputs[3].default_value = 0.1
    mr.inputs[4].default_value = 0.5

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = base_color
    _set_principled(bsdf, Metallic=1.0, **{"Specular IOR Level": 0.0})
    nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat


# --- GrainedMetal ----------------------------------------------------------
def make_grained_metal(name="GrainedMetal"):
    mat = _new_material(name)
    nt = mat.node_tree
    base_color = hsv2rgba(metal_hsv())
    scale = 1.0
    seed_val = float(uniform(-1000, 1000))
    roughness = float(uniform(0.0, 1.0))

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    mr_rough = nt.nodes.new("ShaderNodeMapRange")
    mr_rough.inputs["Value"].default_value = roughness
    mr_rough.inputs[3].default_value = 0.05
    mr_rough.inputs[4].default_value = 0.25

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = base_color
    _set_principled(bsdf, Metallic=1.0, **{"Specular IOR Level": 0.0})
    nt.links.new(mr_rough.outputs["Result"], bsdf.inputs["Roughness"])

    mul_scale = _math(nt, "MULTIPLY", scale, 2000.0)

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.noise_dimensions = "4D"
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])
    noise.inputs["W"].default_value = seed_val
    nt.links.new(mul_scale.outputs[0], noise.inputs["Scale"])
    noise.inputs["Detail"].default_value = 15.0
    noise.inputs["Distortion"].default_value = 2.0

    mul1 = _math(nt, "MULTIPLY", mr_rough.outputs["Result"], 0.4)
    mul2 = _math(nt, "MULTIPLY", _noise_fac_output(noise), mul1.outputs[0])
    mul3 = _math(nt, "MULTIPLY", mul2.outputs[0], 0.01)

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul3.outputs[0], disp.inputs["Height"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


# --- HammeredMetal ---------------------------------------------------------
def make_hammered_metal(name="HammeredMetal"):
    mat = _new_material(name)
    nt = mat.node_tree
    base_color = hsv2rgba(metal_hsv())
    scale = float(log_uniform(0.8, 1.2))
    seed_val = float(uniform(-1000, 1000))

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = base_color
    _set_principled(bsdf, Metallic=1.0, **{"Specular IOR Level": 0.0, "Roughness": 0.1})

    mul_s = _math(nt, "MULTIPLY", scale, 20.0)

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.noise_dimensions = "4D"
    nt.links.new(tex_coord.outputs["Object"], noise.inputs["Vector"])
    noise.inputs["W"].default_value = seed_val
    nt.links.new(mul_s.outputs[0], noise.inputs["Scale"])
    noise.inputs["Detail"].default_value = 15.0
    noise.inputs["Roughness"].default_value = 0.4
    noise.inputs["Distortion"].default_value = 0.2

    mix_vec = nt.nodes.new("ShaderNodeMix")
    mix_vec.data_type = "RGBA"
    mix_vec.clamp_factor = False
    mix_vec.inputs[0].default_value = 0.01
    nt.links.new(tex_coord.outputs["Object"], mix_vec.inputs[6])
    nt.links.new(noise.outputs["Color"], mix_vec.inputs[7])

    mul_v = _math(nt, "MULTIPLY", scale, 300.0)

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi.voronoi_dimensions = "4D"
    voronoi.feature = "SMOOTH_F1"
    try:
        voronoi.inputs["Smoothness"].default_value = 0.2
    except Exception:
        pass
    nt.links.new(mix_vec.outputs[2], voronoi.inputs["Vector"])
    voronoi.inputs["W"].default_value = seed_val
    nt.links.new(mul_v.outputs[0], voronoi.inputs["Scale"])

    mul_dist = _math(nt, "MULTIPLY", voronoi.outputs["Distance"], scale)
    power = _math(nt, "POWER", mul_dist.outputs[0], 2.5)
    mul_disp = _math(nt, "MULTIPLY", power.outputs[0], float(log_uniform(0.001, 0.003)))

    disp = nt.nodes.new("ShaderNodeDisplacement")
    disp.inputs["Midlevel"].default_value = 0.0
    nt.links.new(mul_disp.outputs[0], disp.inputs["Height"])
    _connect_output(nt, bsdf, displacement=disp.outputs[0])
    return mat


DECORATIVE_HARD_REGISTRY = [
    (make_brushed_metal, 1.0),
    (make_galvanized_metal, 1.0),
    (make_grained_metal, 1.0),
    (make_hammered_metal, 1.0),
    (make_vase_ceramic, 4.0),
    (make_colored_glass, 2.0),
    (make_marble, 1.0),
    (make_glass_volume, 2.0),
    (make_ceramic, 1.0),
]


# ============================================================================
# === PlantPot creation (geometry verbatim from objects_blender) ==============
# ============================================================================

def create_plant_pot():
    depth = float(log_uniform(0.5, 1.0))
    r_expand = uniform(1.1, 1.3)
    alpha = uniform(0.5, 0.8)
    r_mid = (r_expand - 1) * alpha + 1
    thickness = float(log_uniform(0.04, 0.06))
    scale = float(log_uniform(0.1, 0.15))

    n = 4 * int(log_uniform(4, 8))
    base = new_base_circle(vertices=n)
    middle = new_base_circle(vertices=n)
    middle.location[2] = depth / 2
    middle.scale = [r_mid] * 3
    upper = new_base_circle(vertices=n)
    upper.location[2] = depth
    upper.scale = [r_expand] * 3
    apply_transform(upper, loc=True)
    obj = join_objects([base, middle, upper])

    select_only(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.bridge_edge_loops()
    bm = bmesh.from_edit_mesh(obj.data)
    for v in bm.verts:
        v.select_set(bool(np.abs(v.co[2]) < 1e-3))
    bm.select_flush(False)
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')

    select_only(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.fill_grid(use_interp_simple=True, offset=np.random.randint(n // 4))
    bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
    bpy.ops.object.mode_set(mode='OBJECT')

    obj.rotation_euler[2] = np.pi / n
    apply_transform(obj)

    # No handle, no bar, no guard for PlantPot
    modify_mesh(obj, 'SOLIDIFY', thickness=thickness, offset=1)
    subsurf(obj, 1, True)
    subsurf(obj, 3)

    obj.scale = [scale] * 3
    apply_transform(obj)

    return obj


# ============================================================================
# === Main build =============================================================
# ============================================================================

def make_potting_soil_material(name="PlantPotDirt"):
    import colorsys
    base_hue = float(np.random.uniform(0.05, 0.10))
    dark = colorsys.hsv_to_rgb(base_hue, np.random.uniform(0.5, 0.8),
                                np.random.uniform(0.04, 0.12))
    light = colorsys.hsv_to_rgb(base_hue + float(np.random.uniform(-0.02, 0.02)),
                                np.random.uniform(0.4, 0.7),
                                np.random.uniform(0.10, 0.22))
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = float(np.random.uniform(20.0, 80.0))
    noise.inputs["Detail"].default_value = 8.0
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    cr = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(noise.outputs[0], cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.3
    cr.color_ramp.elements[0].color = (dark[0], dark[1], dark[2], 1.0)
    cr.color_ramp.elements[1].position = 0.7
    cr.color_ramp.elements[1].color = (light[0], light[1], light[2], 1.0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(cr.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.85
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def build():
    clear_scene()

    # Geometry params: use raw SEED (matches objects_blender/PlantPotFactory.py).
    seed_all(SEED)
    pot = create_plant_pot()

    # Shade smooth
    select_only(pot)
    bpy.ops.object.shade_smooth()

    # Material sampling: raw SEED, decorative_hard pool.
    # PanFactory (parent) sets scratch=edge_wear=None, so NO wear_tear for PlantPot.
    mat_seed = int_hash((SEED, 0))
    seed_all(mat_seed)
    pot_make_fn = weighted_sample(DECORATIVE_HARD_REGISTRY)
    pot_mat = pot_make_fn(name="PlantPotSurface")
    pot.data.materials.append(pot_mat)

    # self.dirt_surface (material_assignments.potting_soil). Standalone factory
    # does not emit dirt fill mesh so this slot is structural only.
    dirt_mat = make_potting_soil_material("PlantPotDirt")
    pot.data.materials.append(dirt_mat)

    pot.name = "PlantPotFactory"
    return pot


build()
