# [FL_INDEX: keywords="blender_factory, procedural_3d, LeafHeartFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: LeafHeartFactory | Category: factories_geo
# Prompt: A 3D model of a single heart-shaped leaf rendered from an elevated perspective, featuring a broad symmetrical blade with two rounded lobes at the base forming a heart silhouette, a pointed tip, a central crease along the midrib, and subtle vein-like surface lines, colored in a flat green tone.

# SEED-deterministic: all random calls seeded from SEED
import os, math, colorsys, random
import bpy
import numpy as np
from numpy.random import normal, uniform
from types import SimpleNamespace

# ============================================================
# Inlined material library -- simple_greenery shader
# ============================================================

def seed_all(seed):
    np.random.seed(seed)
    random.seed(seed)


def _hsv2rgba(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(float(h) % 1.0,
                                    max(0.0, min(1.0, float(s))),
                                    max(0.0, min(1.0, float(v))))
    return (r, g, b, 1.0)


def _plant_green():
    """Sample a random plant-green HSV tuple."""

    return (uniform(0.25, 0.33), normal(0.65, 0.03), uniform(0.1, 0.45))


def _fac(node):
    """Return the scalar factor output of a texture node (Blender 4.x 'Fac' or 5.0 'Factor')."""

    return node.outputs.get("Fac") or node.outputs.get("Factor") or node.outputs[0]


def _new_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat


def make_simple_greenery(name="SimpleGreenery"):
    """Faithful translation of shader_simple_greenery
    Creates three independent 4D noise textures (each with random W, Scale,
    Detail, Roughness, Distortion) and uses them to drive:
      1. colour mix factor  (two plant_green colours blended via MixRGB)
      2. roughness           (MapRange -> PrincipledBSDF.Roughness)
      3. translucent weight  (MapRange -> MixShader.Fac)
    Final surface = MixShader(translucent, principled).
    """

    mat = _new_mat(name)
    nt = mat.node_tree
    ln = nt.links.new

    # -- helper: one 4D noise with fully random params --
    def _noise():
        n = nt.nodes.new("ShaderNodeTexNoise")
        n.noise_dimensions = "4D"
        n.inputs["W"].default_value = float(uniform(0, 100))
        n.inputs["Scale"].default_value = float(normal(60, 25))
        n.inputs["Detail"].default_value = float(uniform(0, 10))
        n.inputs["Roughness"].default_value = float(uniform(0, 1))
        n.inputs["Distortion"].default_value = float(uniform(0, 3))
        return n

    # Noise 1 -- colour mix factor
    noise_color = _noise()
    map_color = nt.nodes.new("ShaderNodeMapRange")
    map_color.interpolation_type = "SMOOTHSTEP"
    # MapRange inputs: 0=Value, 1=FromMin(0), 2=FromMax(1), 3=ToMin(0), 4=ToMax
    ln(_fac(noise_color), map_color.inputs["Value"])
    map_color.inputs[4].default_value = float(uniform(0.1, 1.0))  # To Max

    # Two plant-green colours
    color_a = _hsv2rgba(*_plant_green())
    color_b = _hsv2rgba(*_plant_green())

    mix_rgb = nt.nodes.new("ShaderNodeMixRGB")
    ln(map_color.outputs["Result"], mix_rgb.inputs["Fac"])
    mix_rgb.inputs["Color1"].default_value = color_a
    mix_rgb.inputs["Color2"].default_value = color_b

    # Translucent BSDF
    translucent = nt.nodes.new("ShaderNodeBsdfTranslucent")
    ln(mix_rgb.outputs["Color"], translucent.inputs["Color"])

    # Noise 2 -- roughness
    noise_rough = _noise()
    map_rough = nt.nodes.new("ShaderNodeMapRange")
    map_rough.interpolation_type = "SMOOTHSTEP"
    ln(_fac(noise_rough), map_rough.inputs["Value"])
    map_rough.inputs[3].default_value = float(uniform(0.1, 0.8))  # To Min
    map_rough.inputs[4].default_value = float(uniform(0.1, 0.8))  # To Max

    # Principled BSDF
    principled = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(mix_rgb.outputs["Color"], principled.inputs["Base Color"])
    ln(map_rough.outputs["Result"], principled.inputs["Roughness"])

    # Noise 3 -- translucent mix weight
    noise_trans = _noise()
    map_trans = nt.nodes.new("ShaderNodeMapRange")
    map_trans.interpolation_type = "SMOOTHSTEP"
    ln(_fac(noise_trans), map_trans.inputs["Value"])
    map_trans.inputs[3].default_value = float(uniform(0.6, 0.9))  # To Min

    # Mix translucent + principled
    mix_shader = nt.nodes.new("ShaderNodeMixShader")
    ln(map_trans.outputs["Result"], mix_shader.inputs["Fac"])
    ln(translucent.outputs["BSDF"], mix_shader.inputs[1])
    ln(principled.outputs["BSDF"], mix_shader.inputs[2])

    # Output
    output = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(mix_shader.outputs["Shader"], output.inputs["Surface"])

    return mat


# ============================================================
# Phase 1 -- Material sampling on raw SEED (mirrors __init__)
# ============================================================
SEED = int(os.environ.get("SEED", "0"))
seed_all(SEED)

MAT_LEAF = make_simple_greenery(name="LeafHeart_SimpleGreenery")
MAT_LEAF.use_fake_user = True


# ============================================================
# Original geometry helpers (from objects_blender/small_plants/LeafHeartFactory.py)
# ============================================================
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)
bpy.context.scene.cursor.location = (0, 0, 0)


def make_leaf_heart(genome=None):
    genome_defaults = dict(leaf_width=1.0, use_wave=True, z_scaling=0, width_rand=0.1)
    if genome:
        genome_defaults.update(genome)
    g = genome_defaults

    bpy.ops.mesh.primitive_circle_add(
        enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.edge_face_add()
    obj = bpy.context.active_object
    n = len(obj.data.vertices) // 2

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='VERT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.data.vertices[0].select = True
    obj.data.vertices[-1].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide()

    a = np.linspace(0, np.pi, n)
    x = (16.0 * (np.sin(a - np.pi) ** 3)
         * (g['leaf_width'] + np.random.randn() * g['width_rand']))
    y = (13.0 * np.cos(a - np.pi)
         - 5 * np.cos(2 * (a - np.pi))
         - 2 * np.cos(3 * (a - np.pi)))
    x, y = x * 0.3, y * 0.3
    z = x ** 2 * g['z_scaling']
    full_coords = np.concatenate([
        np.stack([x, y, z], 1),
        np.stack([-x[::-1], y[::-1], z], 1),
        np.array([[0, y[0], 0]]),
    ]).flatten()
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.data.vertices.foreach_set('co', full_coords)

    if g['use_wave']:
        bpy.ops.object.modifier_add(type='WAVE')
        bpy.context.object.modifiers['Wave'].height = 0.8 * np.random.randn() * 0.8
        bpy.context.object.modifiers['Wave'].width = 3.5 + np.random.randn() * 1.0
        bpy.context.object.modifiers['Wave'].speed = 40 + np.random.uniform(-10, 20)

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target='MESH')
    bpy.context.scene.cursor.location = obj.data.vertices[-1].co
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    obj.location = (0, 0, 0)
    obj.scale *= 0.2
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    # Assign material
    if len(obj.data.materials) == 0:
        obj.data.materials.append(MAT_LEAF)

    return obj


# Re-seed geometry RNG independent of material phase RNG state
seed_all(SEED)
make_leaf_heart()
