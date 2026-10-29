# [FL_INDEX: keywords="blender_factory, procedural_3d, LargePlantContainerFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: LargePlantContainerFactory | Category: factories_tex
# Prompt: A 3D model of a wide shallow plant container with a live plant rendered from a slightly elevated three-quarter perspective. The container features a wide bowl shape with a low profile and a pastel lavender exterior, filled with soil, and supporting broad leafy green plant foliage with large elongated leaves.

"""LargePlantContainerFactory — standalone textured large plant container.

Produces: ceramic/metal pot + potting-soil dirt + procedural monocot (agave)
rosette. Mirrors LargePlantContainerFactory, whose plant pool is
restricted to [MonocotFactory]; geometry follows AgaveMonocotFactory's
phyllotaxis rosette.

Geometry copied verbatim from:
  objects_blender/tableware/LargePlantContainerFactory.py

Shaders translated faithfully from sources:
  Pot surface — material_assignments.decorative_hard pool:

  Dirt surface — material_assignments.potting_soil pool:

  Monocot (agave) leaves — MonocotGrowthFactory.shader_monocot:

  Wear-tear (50%/50% from TablewareFactory) applied to POT ONLY:

Material binding model:
  PlantPotFactory (subclass of PotFactory -> PanFactory -> TablewareFactory)
  overrides self.surface with weighted_sample(decorative_hard).
  LargePlantContainerFactory selects dirt_surface from potting_soil.
  MonocotFactory assigns shader_monocot to the plant.
  Pot gets wear-tear (50/50); dirt and plant do not,'s
  TablewareFactory.finalize_assets (only the base factory's surface wears).
"""


import os
import math
import random
import colorsys
import hashlib

import bmesh
import bpy
import numpy as np
from mathutils import Vector, noise as mu_noise
from numpy.random import uniform

# --- Seed ---

SEED = int(os.environ.get("SEED", 0))

def int_hash(x):
    m = hashlib.md5()
    for s in x:
        m.update(str(s).encode("utf-8"))
    return abs(int(m.hexdigest(), 16)) % (2**32 - 1)

def seed_all(seed):
    np.random.seed(seed)
    random.seed(seed)

# --- Utilities ---

def log_uniform(low, high, size=None):
    return np.exp(np.random.uniform(np.log(low), np.log(high), size))

def hsv2rgba(hsv):
    h, s, v = hsv
    h = h - math.floor(h)
    s = max(0.0, min(1.0, s))
    v = max(0.0, min(1.0, v))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

def metal_hsv():
    if np.random.uniform() < 0.2:
        return (np.random.uniform(0, 1),
                np.random.uniform(0.0, 0.2),
                float(log_uniform(0.05, 0.3)))
    return (np.random.uniform(0, 1),
            np.random.uniform(0.3, 0.6),
            float(log_uniform(0.02, 0.5)))

def random_color_neighbour(base, dr, dg, db):
    """Perturb each RGB channel of base by +/-d."""

    r, g, b, a = base
    r += np.random.uniform(-dr, dr)
    g += np.random.uniform(-dg, dg)
    b += np.random.uniform(-db, db)
    return (max(0, min(1, r)), max(0, min(1, g)), max(0, min(1, b)), a)

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

# --- Scene helpers ---

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

def read_co(obj):
    arr = np.zeros(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get('co', arr)
    return arr.reshape(-1, 3)

def write_co(obj, arr):
    obj.data.vertices.foreach_set('co', arr.reshape(-1))
    obj.data.update()

def read_edges(obj):
    arr = np.zeros(len(obj.data.edges) * 2, dtype=int)
    obj.data.edges.foreach_get('vertices', arr)
    return arr.reshape(-1, 2)

def read_edge_center(obj):
    return read_co(obj)[read_edges(obj).reshape(-1)].reshape(-1, 2, 3).mean(1)

def read_edge_direction(obj):
    cos = read_co(obj)[read_edges(obj).reshape(-1)].reshape(-1, 2, 3)
    d = cos[:, 1] - cos[:, 0]
    n = np.linalg.norm(d, axis=-1)
    d[n > 0] /= n[n > 0, None]
    return d

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

# --- Material helpers ---

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

# --- POT material factories (decorative_hard pool) ---

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
    glass = nt.nodes.new("ShaderNodeBsdfPrincipled")
    glass.inputs["Base Color"].default_value = hsv2rgba(hsv)
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

# decorative_hard registry (mirrors material_assignments.decorative_hard)
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

# --- DIRT material factories (potting_soil pool) ---

def make_dirt(name="Dirt"):
    """Faithful translation of terrain/dirt.py shader_dirt.

    Creates a cracked-earth color pattern via noise + voronoi distance-to-edge,
    with variable roughness.
    """

    mat = _new_material(name)
    nt = mat.node_tree

    geom = nt.nodes.new("ShaderNodeNewGeometry")
    position = geom.outputs["Position"]

    scale = 0.5
    dens_crack = float(uniform(0, 0.1))
    scal_crack = float(uniform(5, 15))
    widt_crack = float(uniform(0.01, 0.05))

    # Noise 1 — main color pattern
    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    noise1.noise_dimensions = "4D"
    nt.links.new(position, noise1.inputs["Vector"])
    noise1.inputs["Scale"].default_value = 8.0 * scale
    noise1.inputs["Detail"].default_value = 16.0
    noise1.inputs["W"].default_value = float(uniform(0, 10))

    # Noise 2 — crack density mask
    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    noise2.noise_dimensions = "4D"
    nt.links.new(position, noise2.inputs["Vector"])
    noise2.inputs["Scale"].default_value = 5.0 * scale
    noise2.inputs["W"].default_value = float(uniform(0, 10))

    cr2 = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(_noise_fac_output(noise2), cr2.inputs["Value"])
    cr2.inputs[1].default_value = 0.445 + (2 * dens_crack) - 0.1
    cr2.inputs[2].default_value = 0.505 + (2 * dens_crack) - 0.1
    cr2.inputs[3].default_value = 0.0
    cr2.inputs[4].default_value = 1.0
    cr2.clamp = True

    # Noise 3 — voronoi distortion
    noise3 = nt.nodes.new("ShaderNodeTexNoise")
    noise3.noise_dimensions = "4D"
    nt.links.new(position, noise3.inputs["Vector"])
    noise3.inputs["Scale"].default_value = 1.0 * scale
    noise3.inputs["Detail"].default_value = 16.0
    noise3.inputs["W"].default_value = float(uniform(0, 10))

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi.feature = "DISTANCE_TO_EDGE"
    nt.links.new(noise3.outputs["Color"], voronoi.inputs["Vector"])
    voronoi.inputs["Scale"].default_value = scal_crack * scale

    cr1 = nt.nodes.new("ShaderNodeMapRange")
    nt.links.new(voronoi.outputs["Distance"], cr1.inputs["Value"])
    cr1.inputs[1].default_value = 0.0
    cr1.inputs[2].default_value = widt_crack
    cr1.inputs[3].default_value = 0.0
    cr1.inputs[4].default_value = 1.0
    cr1.clamp = True

    # mix = (1-cr2)*cr1 + cr2*0.5
    sub_cr2 = nt.nodes.new("ShaderNodeVectorMath")
    sub_cr2.operation = "SUBTRACT"
    sub_cr2.inputs[0].default_value = (1.0, 1.0, 1.0)
    nt.links.new(cr2.outputs["Result"], sub_cr2.inputs[1])

    mul1 = nt.nodes.new("ShaderNodeVectorMath")
    mul1.operation = "MULTIPLY"
    nt.links.new(sub_cr2.outputs["Vector"], mul1.inputs[0])
    nt.links.new(cr1.outputs["Result"], mul1.inputs[1])

    mul2 = nt.nodes.new("ShaderNodeVectorMath")
    mul2.operation = "MULTIPLY"
    nt.links.new(cr2.outputs["Result"], mul2.inputs[0])
    mul2.inputs[1].default_value = (0.5, 0.5, 0.5)

    mix_add = nt.nodes.new("ShaderNodeVectorMath")
    mix_add.operation = "ADD"
    nt.links.new(mul1.outputs["Vector"], mix_add.inputs[0])
    nt.links.new(mul2.outputs["Vector"], mix_add.inputs[1])

    # Color ramp for base color
    cr_color = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(_noise_fac_output(noise1), cr_color.inputs["Fac"])
    cr_color.color_ramp.elements.new(0)
    cr_color.color_ramp.elements[0].position = 0.223
    cr_color.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr_color.color_ramp.elements[1].position = 0.71
    col1 = [0.18, 0.075, 0.05, 1.0]
    col2 = [0.19, 0.03, 0.02, 1.0]
    for i in range(3):
        col1[i] += float(np.random.uniform(-0.05, 0.05))
        col2[i] += float(np.random.uniform(-0.05, 0.05))
    cr_color.color_ramp.elements[1].color = tuple(max(0, min(1, c)) for c in col1)
    cr_color.color_ramp.elements[2].position = 1.0
    cr_color.color_ramp.elements[2].color = tuple(max(0, min(1, c)) for c in col2)

    # Mix color: mix(fac=mix_add, black, cr_color)
    mix_color = nt.nodes.new("ShaderNodeMix")
    mix_color.data_type = "RGBA"
    nt.links.new(mix_add.outputs["Vector"], mix_color.inputs[0])
    mix_color.inputs[6].default_value = (0.0, 0.0, 0.0, 1.0)
    nt.links.new(cr_color.outputs["Color"], mix_color.inputs[7])

    # Roughness ramp
    cr_rough = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(_noise_fac_output(noise1), cr_rough.inputs["Fac"])
    cr_rough.color_ramp.elements[0].position = 0.08
    cr_rough.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr_rough.color_ramp.elements[1].position = 0.768
    cr_rough.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix_color.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(cr_rough.outputs["Color"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

def make_soil(name="Soil"):
    """Faithful translation of terrain/soil.py shader_soil.

    Creates pebbly soil with two-tone color (soil + pebble colors) using
    voronoi-based pebble pattern.
    """

    mat = _new_material(name)
    nt = mat.node_tree

    darkness = 1.5
    soil_col_1 = random_color_neighbour(
        (0.28 / darkness, 0.11 / darkness, 0.042 / darkness, 1.0), 0.05, 0.1, 0.1)
    soil_col_2 = random_color_neighbour(
        (0.22 / darkness, 0.0906 / darkness, 0.035 / darkness, 1.0), 0.05, 0.1, 0.1)
    peb_col_1 = random_color_neighbour((0.3813, 0.1714, 0.0782, 1.0), 0.1, 0.1, 0.1)
    peb_col_2 = random_color_neighbour((0.314, 0.1274, 0.0578, 1.0), 0.1, 0.1, 0.1)

    tex_coord = nt.nodes.new("ShaderNodeTexCoord")

    # Pebble voronoi (simplified — one scale instead of three)
    peb_size = float(uniform(2.0, 5.0))
    noise_mag = (1.0 / peb_size) * float(uniform(1.5, 2.0))

    noise_peb = nt.nodes.new("ShaderNodeTexNoise")
    noise_peb.noise_dimensions = "4D"
    nt.links.new(tex_coord.outputs["Object"], noise_peb.inputs["Vector"])
    noise_peb.inputs["W"].default_value = float(uniform(0, 10))
    noise_peb.inputs["Scale"].default_value = peb_size

    mul_noise = nt.nodes.new("ShaderNodeVectorMath")
    mul_noise.operation = "MULTIPLY"
    nt.links.new(noise_peb.outputs["Color"], mul_noise.inputs[0])
    mul_noise.inputs[1].default_value = (noise_mag, noise_mag, noise_mag)

    add_pos = nt.nodes.new("ShaderNodeVectorMath")
    add_pos.operation = "ADD"
    nt.links.new(mul_noise.outputs["Vector"], add_pos.inputs[0])
    nt.links.new(tex_coord.outputs["Object"], add_pos.inputs[1])

    voronoi = nt.nodes.new("ShaderNodeTexVoronoi")
    voronoi.voronoi_dimensions = "4D"
    nt.links.new(add_pos.outputs["Vector"], voronoi.inputs["Vector"])
    voronoi.inputs["W"].default_value = float(uniform(0, 10))
    voronoi.inputs["Scale"].default_value = peb_size

    # Pebble roundness colorramp
    peb_roundness = float(uniform(0.5, 1.0))
    peb_amount = float(uniform(0.2, 0.5))

    cr_peb = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(voronoi.outputs["Distance"], cr_peb.inputs["Fac"])
    cr_peb.color_ramp.elements[0].position = 0.0
    cr_peb.color_ramp.elements[0].color = (peb_roundness, peb_roundness, peb_roundness, 1.0)
    cr_peb.color_ramp.elements.new(0)
    cr_peb.color_ramp.elements[1].position = peb_amount / 8
    cr_peb.color_ramp.elements[1].color = (peb_roundness / 2, peb_roundness / 2, peb_roundness / 2, 1.0)
    cr_peb.color_ramp.elements[2].position = peb_amount
    cr_peb.color_ramp.elements[2].color = (0.0, 0.0, 0.0, 1.0)

    # AO for darkening in crevices
    ao = nt.nodes.new("ShaderNodeAmbientOcclusion")

    cr_ao = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(ao.outputs["Color"], cr_ao.inputs["Fac"])
    cr_ao.color_ramp.elements[0].position = 0.8
    cr_ao.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    cr_ao.color_ramp.elements[1].position = 1.0
    cr_ao.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)

    noise_col = nt.nodes.new("ShaderNodeTexNoise")
    noise_col.noise_dimensions = "4D"
    noise_col.inputs["W"].default_value = float(uniform(0, 10))
    noise_col.inputs["Scale"].default_value = 10.0

    mix_ao_noise = nt.nodes.new("ShaderNodeMix")
    mix_ao_noise.data_type = "RGBA"
    nt.links.new(cr_ao.outputs["Color"], mix_ao_noise.inputs[6])
    nt.links.new(_noise_fac_output(noise_col), mix_ao_noise.inputs[7])

    cr_soil = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(mix_ao_noise.outputs[2], cr_soil.inputs["Fac"])
    cr_soil.color_ramp.elements[0].position = 0.0
    cr_soil.color_ramp.elements[0].color = soil_col_1
    cr_soil.color_ramp.elements[1].position = 1.0
    cr_soil.color_ramp.elements[1].color = soil_col_2

    cr_peb_col = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(cr_peb.outputs["Color"], cr_peb_col.inputs["Fac"])
    cr_peb_col.color_ramp.elements[0].position = 0.0
    cr_peb_col.color_ramp.elements[0].color = peb_col_1
    cr_peb_col.color_ramp.elements[1].position = 1.0
    cr_peb_col.color_ramp.elements[1].color = peb_col_2

    mix_final = nt.nodes.new("ShaderNodeMix")
    mix_final.data_type = "RGBA"
    nt.links.new(cr_peb.outputs["Color"], mix_final.inputs[0])
    nt.links.new(cr_soil.outputs["Color"], mix_final.inputs[6])
    nt.links.new(cr_peb_col.outputs["Color"], mix_final.inputs[7])

    # Roughness
    inv_peb = _math(nt, "MULTIPLY_ADD", cr_peb.outputs["Color"], -1.0)
    inv_peb.inputs[2].default_value = 1.0

    cr_rough = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(inv_peb.outputs[0], cr_rough.inputs["Fac"])
    cr_rough.color_ramp.elements.new(0)
    cr_rough.color_ramp.elements.new(0)
    cr_rough.color_ramp.elements[0].position = 0.0
    cr_rough.color_ramp.elements[0].color = (0.5, 0.5, 0.5, 1.0)
    cr_rough.color_ramp.elements[1].position = 0.8636
    cr_rough.color_ramp.elements[1].color = (0.7, 0.7, 0.7, 1.0)
    cr_rough.color_ramp.elements[2].position = 0.9427
    cr_rough.color_ramp.elements[2].color = (0.95, 0.95, 0.95, 1.0)
    cr_rough.color_ramp.elements[3].position = 1.0
    cr_rough.color_ramp.elements[3].color = (0.98, 0.98, 0.98, 1.0)

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mix_final.outputs[2], bsdf.inputs["Base Color"])
    _set_principled(bsdf, **{"Specular IOR Level": 0.2})
    nt.links.new(cr_rough.outputs["Color"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

def make_mud(name="Mud"):
    """Faithful translation of terrain/mud.py shader_mud.

    Dark brownish mud with subtle noise variation.
    """

    mat = _new_material(name)
    nt = mat.node_tree

    geom = nt.nodes.new("ShaderNodeNewGeometry")
    position = geom.outputs["Position"]

    noise1 = nt.nodes.new("ShaderNodeTexNoise")
    noise1.noise_dimensions = "4D"
    nt.links.new(position, noise1.inputs["Vector"])
    noise1.inputs["W"].default_value = 9.6366
    noise1.inputs["Scale"].default_value = float(np.random.normal(5, 0.5))

    col1 = [0.0216, 0.0145, 0.0113, 1.0]
    col2 = [0.0424, 0.0308, 0.0142, 1.0]
    for i in range(3):
        col1[i] += float(np.random.normal(0, 0.005))
        col2[i] += float(np.random.normal(0, 0.005))
    col1 = [max(0, min(1, c)) for c in col1]
    col2 = [max(0, min(1, c)) for c in col2]

    cr = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(_noise_fac_output(noise1), cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.0
    cr.color_ramp.elements[0].color = tuple(col1)
    cr.color_ramp.elements[1].position = 1.0
    cr.color_ramp.elements[1].color = tuple(col2)

    # Roughness from musgrave-like pattern (using noise since musgrave removed in 4.4+)
    noise2 = nt.nodes.new("ShaderNodeTexNoise")
    nt.links.new(position, noise2.inputs["Vector"])
    noise2.inputs["Scale"].default_value = 0.2
    noise2.inputs["Detail"].default_value = 16.0
    noise2.inputs["Roughness"].default_value = 1.0

    x1 = float(uniform(0.85, 0.95))
    x2 = float(uniform(0.65, 0.75))

    cr_rough = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(_noise_fac_output(noise2), cr_rough.inputs["Fac"])
    cr_rough.color_ramp.elements[0].position = 0.0
    cr_rough.color_ramp.elements[0].color = (x1, x1, x1, 1.0)
    cr_rough.color_ramp.elements[1].position = 1.0
    cr_rough.color_ramp.elements[1].color = (x2, x2, x2, 1.0)

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(cr.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(cr_rough.outputs["Color"], bsdf.inputs["Roughness"])
    _connect_output(nt, bsdf)
    return mat

def make_sand(name="Sand"):
    """Faithful translation of terrain/sand.py shader_SAND.

    Sandy color with subtle noise variation.
    """

    mat = _new_material(name)
    nt = mat.node_tree

    hue = float(uniform(0.04, 0.12))
    sand_col = hsv2rgba((hue, float(uniform(0.4, 0.7)), float(uniform(0.3, 0.6))))

    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = float(uniform(50, 200))
    noise.inputs["Detail"].default_value = 10.0

    cr = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(_noise_fac_output(noise), cr.inputs["Fac"])
    cr.color_ramp.elements[0].position = 0.3
    r, g, b, a = sand_col
    cr.color_ramp.elements[0].color = (r * 0.8, g * 0.8, b * 0.8, 1.0)
    cr.color_ramp.elements[1].position = 0.7
    cr.color_ramp.elements[1].color = sand_col

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(cr.outputs["Color"], bsdf.inputs["Base Color"])
    _set_principled(bsdf, Roughness=float(uniform(0.7, 0.95)),
                    **{"Specular IOR Level": 0.2})
    _connect_output(nt, bsdf)
    return mat

# potting_soil registry (mirrors material_assignments.potting_soil)
POTTING_SOIL_REGISTRY = [
    (make_mud, 1),
    (make_sand, 1),
    (make_soil, 3),
    (make_dirt, 6),
]

# --- MONOCOT (agave leaves) material ---

def make_monocot_leaf(name="MonocotLeaf"):
    """Faithful translation of MonocotGrowthFactory.shader_monocot.

    Agave hue pool: uniform(0.12, 0.32) (green), bright_color HSV
    (hue, 0.6-0.8, 0.05-0.1), dark_color (hue±0.03, 0.8-1.0, 0.05-0.2).

    Standalone 'distance' attribute is not available, so we fall back to
    the musgrave/noise color-ramp branch (use_distance=False path).
    """

    mat = _new_material(name)
    nt = mat.node_tree

    # Colors: AgaveMonocotFactory.build_base_hue() -> uniform(0.12, 0.32)
    base_hue = float(uniform(0.12, 0.32))
    bright_color = hsv2rgba((
        base_hue,
        float(uniform(0.6, 0.8)),
        float(log_uniform(0.05, 0.1)),
    ))
    dark_color = hsv2rgba((
        (base_hue + float(uniform(-0.03, 0.03))) % 1.0,
        float(uniform(0.8, 1.0)),
        float(log_uniform(0.05, 0.2)),
    ))

    specular = float(uniform(0.0, 0.2))
    clearcoat = 0.0 if uniform() < 0.8 else float(uniform(0.2, 0.5))

    # build_color_ramp(nw, musgrave(10), [0,0.3,0.7,1], [br,br,dk,dk])
    # Musgrave removed in Blender 4.4+; use NoiseTexture at matching scale.
    noise_mus = nt.nodes.new("ShaderNodeTexNoise")
    noise_mus.inputs["Scale"].default_value = 10.0
    noise_mus.inputs["Detail"].default_value = 15.0
    noise_mus.inputs["Roughness"].default_value = 0.5

    cr_color = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(_noise_fac_output(noise_mus), cr_color.inputs["Fac"])
    # 4 stops: bright, bright, dark, dark at 0, 0.3, 0.7, 1
    cr_color.color_ramp.elements[0].position = 0.0
    cr_color.color_ramp.elements[0].color = bright_color
    cr_color.color_ramp.elements[1].position = 1.0
    cr_color.color_ramp.elements[1].color = dark_color
    el_mid1 = cr_color.color_ramp.elements.new(0.3)
    el_mid1.color = bright_color
    el_mid2 = cr_color.color_ramp.elements.new(0.7)
    el_mid2.color = dark_color

    # Roughness curve from noise(scale=50): build_float_curve [(0,0.5),(1,0.8)]
    noise_rough = nt.nodes.new("ShaderNodeTexNoise")
    noise_rough.inputs["Scale"].default_value = 50.0
    fc_rough = _build_float_curve(
        nt, _noise_fac_output(noise_rough), [(0.0, 0.5), (1.0, 0.8)]
    )

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(cr_color.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(fc_rough.outputs["Value"], bsdf.inputs["Roughness"])
    _set_principled(bsdf, **{
        "Specular IOR Level": specular,
        "Coat Weight": clearcoat,
        "Subsurface Weight": 0.01,
        "Subsurface Radius": (0.01, 0.01, 0.01),
    })
    _connect_output(nt, bsdf)
    return mat

# --- Wear-tear ---

def apply_scratches(obj):
    """Translation of wear_tear/scratches.py — adds displacement scratches."""

    params = {
        "angle1": float(uniform(10, 80)),
        "angle2": float(uniform(-80, -10)),
        "scratch_scale": float(log_uniform(5, 80)),
        "scratch_mask_ratio": float(log_uniform(0.01, 0.9)),
        "scratch_mask_noise": float(log_uniform(5, 40)),
        "scratch_depth": float(log_uniform(0.1, 1.0)),
    }
    for mat in obj.data.materials:
        if mat is None or not mat.use_nodes:
            continue
        nt = mat.node_tree
        if any(n.label == "scratch" for n in nt.nodes):
            continue

        out_nodes = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"]
        if not out_nodes:
            continue
        out_node = out_nodes[0]

        tex_coord = nt.nodes.new("ShaderNodeTexCoord")

        cxyz1 = nt.nodes.new("ShaderNodeCombineXYZ")
        cxyz1.inputs["Y"].default_value = params["angle1"]
        m1 = nt.nodes.new("ShaderNodeMapping")
        m1.vector_type = "TEXTURE"
        m1.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
        nt.links.new(tex_coord.outputs["Object"], m1.inputs["Vector"])
        nt.links.new(cxyz1.outputs[0], m1.inputs["Rotation"])

        n1 = nt.nodes.new("ShaderNodeTexNoise")
        nt.links.new(m1.outputs["Vector"], n1.inputs["Vector"])
        n1.inputs["Scale"].default_value = params["scratch_scale"]
        n1.inputs["Detail"].default_value = 15.0
        n1.inputs["Roughness"].default_value = 0.0
        n1.inputs["Distortion"].default_value = 22.8

        cxyz2 = nt.nodes.new("ShaderNodeCombineXYZ")
        cxyz2.inputs["Y"].default_value = params["angle2"]
        m2 = nt.nodes.new("ShaderNodeMapping")
        m2.vector_type = "TEXTURE"
        m2.inputs["Scale"].default_value = (25.0, 1.0, 1.0)
        nt.links.new(tex_coord.outputs["Object"], m2.inputs["Vector"])
        nt.links.new(cxyz2.outputs[0], m2.inputs["Rotation"])

        n2 = nt.nodes.new("ShaderNodeTexNoise")
        nt.links.new(m2.outputs["Vector"], n2.inputs["Vector"])
        n2.inputs["Scale"].default_value = params["scratch_scale"]
        n2.inputs["Detail"].default_value = 15.0
        n2.inputs["Roughness"].default_value = 0.0
        n2.inputs["Distortion"].default_value = 22.8

        add_n = _math(nt, "ADD", _noise_fac_output(n1), _noise_fac_output(n2))

        m3 = nt.nodes.new("ShaderNodeMapping")
        m3.vector_type = "TEXTURE"
        m3.inputs["Rotation"].default_value = (0.1588, -0.5742, 0.192)
        nt.links.new(tex_coord.outputs["Object"], m3.inputs["Vector"])

        n3 = nt.nodes.new("ShaderNodeTexNoise")
        nt.links.new(m3.outputs["Vector"], n3.inputs["Vector"])
        n3.inputs["Scale"].default_value = params["scratch_mask_noise"]
        n3.inputs["Detail"].default_value = 1.0

        cr = nt.nodes.new("ShaderNodeValToRGB")
        nt.links.new(_noise_fac_output(n3), cr.inputs["Fac"])
        cr.color_ramp.elements[0].position = 0.4109
        cr.color_ramp.elements[0].color = (0, 0, 0, 1)
        cr.color_ramp.elements[1].position = 1.0
        cr.color_ramp.elements[1].color = (1, 1, 1, 1)

        mul_mask = _math(nt, "MULTIPLY", params["scratch_mask_ratio"], cr.outputs["Color"])

        add_clamped = nt.nodes.new("ShaderNodeMath")
        add_clamped.operation = "ADD"
        add_clamped.use_clamp = True
        nt.links.new(add_n.outputs[0], add_clamped.inputs[0])
        nt.links.new(mul_mask.outputs[0], add_clamped.inputs[1])

        mr = nt.nodes.new("ShaderNodeMapRange")
        nt.links.new(add_clamped.outputs[0], mr.inputs["Value"])
        mr.inputs[1].default_value = 0.7
        mr.inputs[2].default_value = 0.72
        mr.inputs[4].default_value = 0.9

        disp = nt.nodes.new("ShaderNodeDisplacement")
        nt.links.new(mr.outputs["Result"], disp.inputs["Height"])
        disp.inputs["Midlevel"].default_value = 0.0
        disp.inputs["Scale"].default_value = params["scratch_depth"]

        nt.links.new(disp.outputs[0], out_node.inputs["Displacement"])
        disp.label = "scratch"

def apply_edge_wear(obj):
    """Translation of wear_tear/edge_wear.py — mixes in worn-edge shader."""

    params = {
        "_worn_off_opacity": float(uniform(0.01)),
        "_worn_off_radius": float(uniform(0.005, 0.01)),
        "_scratch_radius": float(uniform(0.01, 0.03)),
        "_worn_off_mask_randomness": float(uniform(2.5, 3.0)),
        "_edge_base_color_hue": float(uniform(0.0, 1.0)),
        "_edge_base_color_whiteness": float(uniform(0.1, 0.6)),
        "_scratch_mask_randomness": float(np.random.choice(
            [uniform(0.1, 5.0), uniform(1.0, 10.0)])),
        "_scratch_density": float(np.random.choice([uniform(1.5, 10.0)])),
        "_scratch_opacity": float(uniform(0.5, 1.0)),
    }

    for mat in obj.data.materials:
        if mat is None or not mat.use_nodes:
            continue
        nt = mat.node_tree

        if any(n.label == "wear_tear" for n in nt.nodes):
            continue

        out_nodes = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"]
        if not out_nodes:
            continue
        out_node = out_nodes[0]

        surf_links = out_node.inputs["Surface"].links
        if not surf_links:
            continue
        original_bsdf = surf_links[0].from_node

        disp_links = out_node.inputs["Displacement"].links
        original_displacement = disp_links[0].from_node if disp_links else None

        tex_coord = nt.nodes.new("ShaderNodeTexCoord")
        mapping = nt.nodes.new("ShaderNodeMapping")
        nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])

        noise_sm = nt.nodes.new("ShaderNodeTexNoise")
        nt.links.new(mapping.outputs["Vector"], noise_sm.inputs["Vector"])
        noise_sm.inputs["Scale"].default_value = params["_scratch_mask_randomness"]
        noise_sm.inputs["Detail"].default_value = 1.0

        cr_sm = nt.nodes.new("ShaderNodeValToRGB")
        nt.links.new(_noise_fac_output(noise_sm), cr_sm.inputs["Fac"])
        cr_sm.color_ramp.elements[0].position = 0.4436
        cr_sm.color_ramp.elements[0].color = (0, 0, 0, 1)
        cr_sm.color_ramp.elements[1].position = 0.5345
        cr_sm.color_ramp.elements[1].color = (1, 1, 1, 1)

        bevel1 = nt.nodes.new("ShaderNodeBevel")
        bevel1.samples = 20
        bevel1.inputs["Radius"].default_value = params["_scratch_radius"]

        geom = nt.nodes.new("ShaderNodeNewGeometry")

        sub1 = nt.nodes.new("ShaderNodeVectorMath")
        sub1.operation = "SUBTRACT"
        nt.links.new(bevel1.outputs[0], sub1.inputs[0])
        nt.links.new(geom.outputs["Normal"], sub1.inputs[1])

        abs1 = nt.nodes.new("ShaderNodeMath")
        abs1.operation = "ABSOLUTE"
        nt.links.new(sub1.outputs["Vector"], abs1.inputs[0])

        cr1 = nt.nodes.new("ShaderNodeValToRGB")
        nt.links.new(abs1.outputs[0], cr1.inputs["Fac"])
        cr1.color_ramp.elements[0].position = 0.0691
        cr1.color_ramp.elements[0].color = (0, 0, 0, 1)
        cr1.color_ramp.elements[1].position = 0.1564
        cr1.color_ramp.elements[1].color = (1, 1, 1, 1)

        mul_sm_cr1 = nt.nodes.new("ShaderNodeMath")
        mul_sm_cr1.operation = "MULTIPLY"
        mul_sm_cr1.use_clamp = True
        nt.links.new(cr_sm.outputs["Color"], mul_sm_cr1.inputs[0])
        nt.links.new(cr1.outputs["Color"], mul_sm_cr1.inputs[1])

        mul_scratch_opacity = nt.nodes.new("ShaderNodeMath")
        mul_scratch_opacity.operation = "MULTIPLY"
        mul_scratch_opacity.use_clamp = True
        mul_scratch_opacity.inputs[0].default_value = params["_scratch_opacity"]
        nt.links.new(mul_sm_cr1.outputs[0], mul_scratch_opacity.inputs[1])

        bevel2 = nt.nodes.new("ShaderNodeBevel")
        bevel2.samples = 20
        bevel2.inputs["Radius"].default_value = params["_worn_off_radius"]

        sub2 = nt.nodes.new("ShaderNodeVectorMath")
        sub2.operation = "SUBTRACT"
        nt.links.new(bevel2.outputs[0], sub2.inputs[0])
        nt.links.new(geom.outputs["Normal"], sub2.inputs[1])

        abs2 = nt.nodes.new("ShaderNodeMath")
        abs2.operation = "ABSOLUTE"
        nt.links.new(sub2.outputs["Vector"], abs2.inputs[0])

        noise_wo = nt.nodes.new("ShaderNodeTexNoise")
        nt.links.new(mapping.outputs["Vector"], noise_wo.inputs["Vector"])
        noise_wo.inputs["Scale"].default_value = params["_worn_off_mask_randomness"]
        noise_wo.inputs["Detail"].default_value = 1.0

        cr_wo = nt.nodes.new("ShaderNodeValToRGB")
        nt.links.new(_noise_fac_output(noise_wo), cr_wo.inputs["Fac"])
        cr_wo.color_ramp.elements[0].position = 0.0764
        cr_wo.color_ramp.elements[0].color = (1, 1, 1, 1)
        cr_wo.color_ramp.elements[1].position = 0.5709
        cr_wo.color_ramp.elements[1].color = (0, 0, 0, 1)

        mul_wo = nt.nodes.new("ShaderNodeMath")
        mul_wo.operation = "MULTIPLY"
        mul_wo.use_clamp = True
        nt.links.new(abs2.outputs[0], mul_wo.inputs[0])
        nt.links.new(cr_wo.outputs["Color"], mul_wo.inputs[1])

        mul_wo_opacity = nt.nodes.new("ShaderNodeMath")
        mul_wo_opacity.operation = "MULTIPLY"
        mul_wo_opacity.use_clamp = True
        mul_wo_opacity.inputs[0].default_value = params["_worn_off_opacity"]
        nt.links.new(mul_wo.outputs[0], mul_wo_opacity.inputs[1])

        cr3 = nt.nodes.new("ShaderNodeValToRGB")
        nt.links.new(mul_wo_opacity.outputs[0], cr3.inputs["Fac"])
        cr3.color_ramp.elements[0].position = 0.0
        cr3.color_ramp.elements[0].color = (0, 0, 0, 1)
        cr3.color_ramp.elements[1].position = 0.7782
        cr3.color_ramp.elements[1].color = (1, 1, 1, 1)

        combine_color = nt.nodes.new("ShaderNodeCombineColor")
        combine_color.mode = "HSV"
        combine_color.inputs["Red"].default_value = params["_edge_base_color_hue"]
        combine_color.inputs["Green"].default_value = 0.7733
        combine_color.inputs["Blue"].default_value = 0.01

        mix_edge_color = nt.nodes.new("ShaderNodeMix")
        mix_edge_color.data_type = "RGBA"
        mix_edge_color.clamp_result = True
        mix_edge_color.inputs[0].default_value = params["_edge_base_color_whiteness"]
        nt.links.new(combine_color.outputs[0], mix_edge_color.inputs[6])
        mix_edge_color.inputs[7].default_value = (0.02, 0.02, 0.02, 1.0)

        edge_bsdf1 = nt.nodes.new("ShaderNodeBsdfPrincipled")
        nt.links.new(mix_edge_color.outputs[2], edge_bsdf1.inputs["Base Color"])
        _set_principled(edge_bsdf1, Metallic=0.3745,
                        **{"Specular IOR Level": 0.0, "Roughness": 0.1436})

        mix_sh1 = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(cr3.outputs["Color"], mix_sh1.inputs["Fac"])
        nt.links.new(original_bsdf.outputs[0], mix_sh1.inputs[1])
        nt.links.new(edge_bsdf1.outputs[0], mix_sh1.inputs[2])

        mapping_v1 = nt.nodes.new("ShaderNodeMapping")
        mapping_v1.inputs["Scale"].default_value = (10.0, 1.0, 1.0)
        nt.links.new(tex_coord.outputs["Object"], mapping_v1.inputs["Vector"])

        vor1 = nt.nodes.new("ShaderNodeTexVoronoi")
        vor1.feature = "DISTANCE_TO_EDGE"
        nt.links.new(mapping_v1.outputs["Vector"], vor1.inputs["Vector"])
        vor1.inputs["Scale"].default_value = params["_scratch_density"]

        mapping_v2 = nt.nodes.new("ShaderNodeMapping")
        mapping_v2.inputs["Scale"].default_value = (1.0, 10.0, 1.0)
        nt.links.new(tex_coord.outputs["Object"], mapping_v2.inputs["Vector"])

        vor2 = nt.nodes.new("ShaderNodeTexVoronoi")
        vor2.feature = "DISTANCE_TO_EDGE"
        nt.links.new(mapping_v2.outputs["Vector"], vor2.inputs["Vector"])
        vor2.inputs["Scale"].default_value = params["_scratch_density"] * 2.0

        mul_vor = nt.nodes.new("ShaderNodeMath")
        mul_vor.operation = "MULTIPLY"
        mul_vor.use_clamp = True
        nt.links.new(vor1.outputs["Distance"], mul_vor.inputs[0])
        nt.links.new(vor2.outputs["Distance"], mul_vor.inputs[1])

        cr6 = nt.nodes.new("ShaderNodeValToRGB")
        nt.links.new(mul_vor.outputs[0], cr6.inputs["Fac"])
        cr6.color_ramp.elements[0].position = 0.0
        cr6.color_ramp.elements[0].color = (1, 1, 1, 1)
        cr6.color_ramp.elements[1].position = 0.0073
        cr6.color_ramp.elements[1].color = (0, 0, 0, 1)

        mul_edge_scratch = nt.nodes.new("ShaderNodeMath")
        mul_edge_scratch.operation = "MULTIPLY"
        mul_edge_scratch.use_clamp = True
        nt.links.new(cr1.outputs["Color"], mul_edge_scratch.inputs[0])
        nt.links.new(cr6.outputs["Color"], mul_edge_scratch.inputs[1])

        mul_combined = nt.nodes.new("ShaderNodeMath")
        mul_combined.operation = "MULTIPLY"
        mul_combined.use_clamp = True
        nt.links.new(mul_sm_cr1.outputs[0], mul_combined.inputs[0])
        nt.links.new(mul_edge_scratch.outputs[0], mul_combined.inputs[1])

        edge_bsdf2 = nt.nodes.new("ShaderNodeBsdfPrincipled")
        nt.links.new(mix_edge_color.outputs[2], edge_bsdf2.inputs["Base Color"])
        _set_principled(edge_bsdf2, Metallic=0.3855,
                        **{"Specular IOR Level": 0.0, "Roughness": 0.0})

        mix_sh2 = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(mul_scratch_opacity.outputs[0], mix_sh2.inputs["Fac"])
        nt.links.new(mix_sh1.outputs[0], mix_sh2.inputs[1])
        nt.links.new(edge_bsdf2.outputs[0], mix_sh2.inputs[2])

        nt.links.new(mix_sh2.outputs[0], out_node.inputs["Surface"])

        scale_mul6 = nt.nodes.new("ShaderNodeVectorMath")
        scale_mul6.operation = "SCALE"
        nt.links.new(mul_combined.outputs[0], scale_mul6.inputs[0])
        scale_mul6.inputs["Scale"].default_value = 2.0

        if original_displacement is not None:
            add_disp = nt.nodes.new("ShaderNodeMath")
            add_disp.operation = "ADD"
            add_disp.use_clamp = True
            nt.links.new(original_displacement.outputs[0], add_disp.inputs[0])
            nt.links.new(scale_mul6.outputs["Vector"], add_disp.inputs[1])
            nt.links.new(add_disp.outputs[0], out_node.inputs["Displacement"])
        else:
            nt.links.new(scale_mul6.outputs["Vector"], out_node.inputs["Displacement"])

        mix_sh2.label = "wear_tear"

# --- PlantPot creation (geometry verbatim from objects_blender) ---

def create_plant_pot(depth, r_expand, r_mid, thickness, scale):
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

    modify_mesh(obj, 'SOLIDIFY', thickness=thickness, offset=1)
    subsurf(obj, 1, True)
    subsurf(obj, 3)

    obj.scale = [scale] * 3
    apply_transform(obj)
    return obj

# --- Dirt creation (geometry verbatim from objects_blender) ---

def create_dirt(pot, depth, scale, dirt_ratio):
    dirt_z = dirt_ratio * depth * scale

    horizontal = np.abs(read_edge_direction(pot)[:, -1]) < 0.1
    edge_center = read_edge_center(pot)
    z = edge_center[:, -1]
    idx = np.argmin(np.abs(z - dirt_z) - horizontal.astype(float) * 10)
    radius = np.sqrt((edge_center[idx] ** 2)[:2].sum())

    selection = np.zeros(len(pot.data.edges), dtype=bool)
    selection[idx] = True

    select_only(pot)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(pot.data)
    bm.edges.ensure_lookup_table()
    for i in np.nonzero(selection)[0]:
        bm.edges[i].select_set(True)
    bm.select_flush(False)
    bmesh.update_edit_mesh(pot.data)
    bpy.ops.mesh.loop_multi_select(ring=False)
    bpy.ops.mesh.duplicate_move()
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')

    dirt = bpy.context.selected_objects[-1]
    bpy.ops.object.select_all(action='DESELECT')

    select_only(dirt)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.fill_grid()
    bpy.ops.object.mode_set(mode='OBJECT')
    subsurf(dirt, 3)

    # Displace dirt surface with multi-octave noise
    co = read_co(dirt)
    seed_offset = Vector((np.random.uniform(-100, 100),
                          np.random.uniform(-100, 100),
                          np.random.uniform(-100, 100)))
    noise_scale = 1.0 / max(radius, 0.01)
    for i in range(len(co)):
        p = Vector((float(co[i, 0]), float(co[i, 1]), float(co[i, 2])))
        h = mu_noise.noise(p * noise_scale * 3.0 + seed_offset) * 0.45
        h += mu_noise.noise(p * noise_scale * 7.0 + seed_offset * 2) * 0.25
        h += mu_noise.noise(p * noise_scale * 15.0 + seed_offset * 3) * 0.15
        h += mu_noise.noise(p * noise_scale * 25.0 + seed_offset * 5) * 0.08
        co[i, 2] += h * radius * 0.3
    write_co(dirt, co)

    co = read_co(dirt)
    x, y, _ = co.T
    to_delete = np.nonzero(np.sqrt(x**2 + y**2) > radius * 0.92)[0]
    if len(to_delete) > 0:
        select_only(dirt)
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(dirt.data)
        bm.verts.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[bm.verts[i] for i in to_delete])
        bmesh.update_edit_mesh(dirt.data)
        bpy.ops.object.mode_set(mode='OBJECT')

    dirt.location[2] -= 0.02
    apply_transform(dirt, loc=True)
    return dirt, dirt_z, radius

# --- Plant (procedural monocot leaves, verbatim geometry) ---

def origin2lowest_x(obj):
    """Shift vertices so the leftmost X point is at origin."""

    co = read_co(obj)
    if not len(co):
        return
    i = int(np.argmin(co[:, 0]))
    co -= co[i]
    write_co(obj, co)

def origin2lowest(obj):
    co = read_co(obj)
    if not len(co):
        return
    i = np.argmin(co[:, -1])
    obj.location[0] = -float(co[i, 0])
    obj.location[1] = -float(co[i, 1])
    obj.location[2] = -float(co[i, 2])
    apply_transform(obj, loc=True)

def create_monocot_leaf(length, half_width, vein_freq=150.0):
    """Create a monocot leaf's agave pipeline.

    Pipeline: outline shape -> vein ridges -> cup shape (y^2) -> surface noise
    -> SOLIDIFY -> subsurf -> rotate+Z Y-bend rotate-Z -> Z-bend.
    Final orientation: along +X (base at leftmost, tip at +X).
    """

    n_seg_x = 48
    n_seg_y = 16
    bpy.ops.mesh.primitive_grid_add(
        x_subdivisions=n_seg_x, y_subdivisions=n_seg_y,
        size=1, location=(0, 0, 0))
    leaf_obj = bpy.context.active_object
    leaf_obj.scale = (length, half_width * 2, 1)
    apply_transform(leaf_obj)

    co = read_co(leaf_obj)
    x_min, x_max = co[:, 0].min(), co[:, 0].max()
    x_range = max(x_max - x_min, 1e-8)
    t = (co[:, 0] - x_min) / x_range  # 0..1 along length

    # 1. Leaf outline: agave-like shape
    rise = np.clip(t / 0.12, 0, 1)
    swell = np.interp(t, [0.12, 0.70], np.clip([0.55, 1.0], 0, 1))
    taper_raw = np.clip((t - 0.70) / 0.30, 0, 1)
    taper = 1.0 - taper_raw ** 1.3
    width_profile = rise * swell * taper

    y_limit = half_width * width_profile
    outside = np.abs(co[:, 1]) > y_limit + 1e-6
    co[outside, 1] = np.sign(co[outside, 1]) * y_limit[outside]

    # 2. Parallel vein ridges
    cut_angle = uniform(-0.1, 0.1)
    vein_pattern = np.cos(
        (np.abs(co[:, 1]) * np.cos(cut_angle) - co[:, 0] * np.sin(cut_angle))
        * vein_freq
    )
    vein_mask = vein_pattern > uniform(0.88, 0.94)
    midrib = np.abs(co[:, 1]) < uniform(0.002, 0.005)
    vein_depth = uniform(0.003, 0.005)
    co[:, 2] -= (vein_mask | midrib).astype(float) * vein_depth

    # 3. Cup shape
    y_ratio = uniform(0.3, 1.0)
    cup_r = uniform(0.1, 0.3)
    co[:, 2] += y_ratio * cup_r * co[:, 1] ** 2

    # 4. Surface noise
    noise_offset = Vector((uniform(-100, 100), uniform(-100, 100), uniform(-100, 100)))
    noise_strength = uniform(0.003, 0.007)
    for i in range(len(co)):
        p = Vector((float(co[i, 0]), float(co[i, 1]), float(co[i, 2])))
        n = mu_noise.noise(p * 3.0 + noise_offset)
        co[i, 2] += n * noise_strength

    # 5. Edge waviness
    for i in range(len(co)):
        if abs(co[i, 1]) > y_limit[i] * 0.7:
            p = Vector((float(co[i, 0]) * 5, float(co[i, 1]) * 5, 0.0))
            co[i, 1] += mu_noise.noise(p + noise_offset) * half_width * 0.03

    write_co(leaf_obj, co)

    modify_mesh(leaf_obj, 'WELD', merge_threshold=length * 0.003)
    modify_mesh(leaf_obj, 'SOLIDIFY', thickness=half_width * 0.03, offset=-1)
    subsurf(leaf_obj, 1, simple=False)

    # 6. Y-bend
    leaf_obj.rotation_euler[1] = -np.pi / 2
    apply_transform(leaf_obj)
    y_bend = uniform(0.3, 0.7) * np.pi / 6
    modify_mesh(leaf_obj, 'SIMPLE_DEFORM',
                 deform_method='BEND', angle=y_bend, deform_axis='Y')
    leaf_obj.rotation_euler[1] = np.pi / 2
    apply_transform(leaf_obj)

    # 7. Z-bend
    z_bend = uniform(-0.5, 0.5) * np.pi / 6
    if abs(z_bend) > 0.01:
        modify_mesh(leaf_obj, 'SIMPLE_DEFORM',
                     deform_method='BEND', angle=z_bend, deform_axis='Z')

    # 8. Move origin to leftmost (base) point
    origin2lowest_x(leaf_obj)

    return leaf_obj

def create_large_plant(plant_seed):
    """Create a dense rosette's AgaveMonocotFactory.

    Phyllotaxis spiral with 20-30 deg angle, tilt from 18-27 deg (inner) to
    72-94 deg (outer), backward Y-bend per leaf, post-assembly gravity droop.
    """

    np.random.seed(plant_seed)

    count = int(np.exp(uniform(np.log(32), np.log(64))))
    angle = uniform(np.pi / 9, np.pi / 6)
    stem_offset = uniform(0.0, 0.5)
    min_y_angle = uniform(np.pi * 0.10, np.pi * 0.15)
    max_y_angle = uniform(np.pi * 0.40, np.pi * 0.52)
    z_drag = uniform(0.05, 0.10)
    leaf_prob = uniform(0.8, 0.9)
    perturb = 0.05
    vein_freq = float(np.exp(uniform(np.log(100), np.log(250))))

    sc0 = uniform(0.8, 1.0)
    sc1 = uniform(0.6, 1.0)

    stem_h = max(stem_offset, 0.02)
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=8, depth=stem_h, radius=0.01,
        location=(0, 0, stem_h / 2))
    stem = bpy.context.active_object
    apply_transform(stem, loc=True)
    parts = [stem]

    accumulated_z_rot = 0.0
    for i in range(count):
        t = i / max(count - 1, 1)

        if uniform(0, 1) > leaf_prob:
            accumulated_z_rot += uniform(angle * 0.95, angle * 1.05)
            continue

        s = float(np.interp(t, [0, 0.5, 1.0], [sc0, 1.0, sc1]))

        leaf_len = uniform(1.0, 1.5) * s
        leaf_hw = leaf_len * uniform(0.06, 0.10)

        leaf_obj = create_monocot_leaf(leaf_len, leaf_hw, vein_freq=vein_freq)

        y_rot = -float(np.interp(t, [0, 1], [min_y_angle, max_y_angle]))
        y_rot += uniform(-perturb, perturb)

        z_rot = accumulated_z_rot + uniform(-perturb, perturb)
        accumulated_z_rot += uniform(angle * 0.95, angle * 1.05)

        z_pos = stem_offset * t

        leaf_obj.rotation_euler = (0, y_rot, z_rot)
        leaf_obj.location = (0, 0, z_pos)
        apply_transform(leaf_obj, loc=True)

        parts.append(leaf_obj)

    plant = join_objects(parts)

    # Post-assembly gravity droop
    co = read_co(plant)
    r_sq = co[:, 0] ** 2 + co[:, 1] ** 2
    co[:, 2] -= z_drag * r_sq
    write_co(plant, co)

    # Center plant at origin (XY)
    co = read_co(plant)
    cx = (co[:, 0].max() + co[:, 0].min()) / 2
    cy = (co[:, 1].max() + co[:, 1].min()) / 2
    plant.location[0] = -cx
    plant.location[1] = -cy
    apply_transform(plant, loc=True)

    return plant

# --- Main build ---

def build():
    clear_scene()

    # Factory-level seed (geometry params)
    seed_all(SEED)

    with FixedSeed(SEED):
        depth = float(log_uniform(0.5, 1.0))
        r_expand = uniform(1.1, 1.3)
        alpha = uniform(0.5, 0.8)
        r_mid = (r_expand - 1) * alpha + 1
        thickness = float(log_uniform(0.04, 0.06))
        scale = float(log_uniform(0.1, 0.15))
        dirt_ratio = uniform(0.7, 0.8)

        # LargePlantContainer overrides (from plant_container.py lines 134-139)
        depth = float(log_uniform(1.0, 1.5))
        scale = float(log_uniform(0.15, 0.25))
        side_size = scale * uniform(1.5, 2.0) * r_expand
        top_size = uniform(1.0, 1.5)
        plant_seed = np.random.randint(1e6)

    pot = create_plant_pot(depth, r_expand, r_mid, thickness, scale)
    dirt, dirt_z, _ = create_dirt(pot, depth, scale, dirt_ratio)
    plant = create_large_plant(plant_seed)

    origin2lowest(plant)
    bound = np.max(np.abs(np.array(plant.bound_box)), axis=0)
    bound = np.maximum(bound, 1e-6)
    plant_scale = float(np.min(np.array([side_size, side_size, top_size]) / bound))
    plant.scale = [plant_scale] * 3
    plant.location[2] = dirt_z
    apply_transform(plant, loc=True)

    # Shade smooth all pieces
    for obj in [pot, dirt, plant]:
        select_only(obj)
        bpy.ops.object.shade_smooth()

    # --- Material assignment ---
    # Use create_asset seed for material randomness (matches int_hash pattern)
    asset_seed = int_hash((SEED, 0))
    seed_all(asset_seed)

    # Pot material (decorative_hard)
    pot_make_fn = weighted_sample(DECORATIVE_HARD_REGISTRY)
    pot_mat = pot_make_fn()
    pot.data.materials.append(pot_mat)

    # Dirt material (potting_soil)
    dirt_make_fn = weighted_sample(POTTING_SOIL_REGISTRY)
    dirt_mat = dirt_make_fn()
    dirt.data.materials.append(dirt_mat)

    # Plant material (monocot shader, agave hue)
    plant_mat = make_monocot_leaf()
    plant.data.materials.append(plant_mat)

    # Wear-tear on pot only (50% each, independent — from TablewareFactory)
    scratch_prob = 0.5
    edge_wear_prob = 0.5
    if np.random.uniform() <= scratch_prob:
        apply_scratches(pot)
    if np.random.uniform() <= edge_wear_prob:
        apply_edge_wear(pot)

    # Join pot + plant + dirt into one object
    result = join_objects([pot, plant, dirt])
    result.name = "LargePlantContainerFactory"
    return result

build()

