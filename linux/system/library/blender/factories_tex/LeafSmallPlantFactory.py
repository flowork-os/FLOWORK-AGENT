# [FL_INDEX: keywords="blender_factory, procedural_3d, LeafSmallPlantFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: LeafSmallPlantFactory | Category: factories_tex
# Prompt: A 3D model of a single broad leaf rendered from an elevated perspective, featuring a rounded teardrop-shaped blade with a slightly pointed tip, a subtle central crease along the midrib, and a flat profile with gentle surface undulation, colored in a muted olive green.

import os
import math
import random
import colorsys

import bpy
import numpy as np

SEED = int(os.environ.get("SEED", 0))

# ══════════════════════════════════════════════════════════════════════════════
#
# Procedural green plant shader: three independent 4D NoiseTextures drive
# (1) color mix between two random greens via MapRange+MixRGB,
# (2) roughness via MapRange,
# (3) translucency factor via MapRange.
# Final: MixShader(TranslucentBSDF, PrincipledBSDF).
# ══════════════════════════════════════════════════════════════════════════════

def seed_all(seed):
    np.random.seed(seed)
    random.seed(seed)

def _hsv2rgba(h, s, v):
    """Convert HSV to RGBA tuple, clamping s/v to valid range."""

    h = float(h) % 1.0
    s = max(0.0, min(1.0, float(s)))
    v = max(0.0, min(1.0, float(v)))
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (r, g, b, 1.0)

def _new_mat(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat

def _get_noise_fac(noise_node):
    """Get the Fac/Factor output from a noise node (Blender 4.x/5.x compat)."""

    return noise_node.outputs.get("Fac") or noise_node.outputs.get("Factor") or noise_node.outputs[0]

def _set_principled(bsdf, key, value):
    """Set a Principled BSDF input, tolerating Blender 4.x/5.x socket renames."""

    if key in bsdf.inputs:
        bsdf.inputs[key].default_value = value
        return
    fallbacks = {
        "Subsurface Weight": ("Subsurface",),
        "Subsurface": ("Subsurface Weight",),
    }
    for alt in fallbacks.get(key, ()):
        if alt in bsdf.inputs:
            bsdf.inputs[alt].default_value = value
            return

def _plant_green():
    return (
        float(np.random.uniform(0.25, 0.33)),
        float(np.random.normal(0.65, 0.03)),
        float(np.random.uniform(0.1, 0.45)),
    )

def _sample_noise_params():
    """Sample parameters for one 4D NoiseTexture call (mirrors noise() inner function).

    Returns dict with keys: W, Scale, Detail, Roughness, Distortion.
    Sampling order matches shader_simple_greenery noise() inner function.
    """

    return {
        "W": float(np.random.uniform(0, 100)),
        "Scale": float(np.random.normal(60, 25)),
        "Detail": float(np.random.uniform(0, 10)),
        "Roughness": float(np.random.uniform(0, 1)),
        "Distortion": float(np.random.uniform(0, 3)),
    }

def _build_noise_node(node_tree, params):
    """Create a ShaderNodeTexNoise with pre-sampled parameters."""

    noise = node_tree.nodes.new("ShaderNodeTexNoise")
    noise.noise_dimensions = "4D"
    noise.inputs["W"].default_value = params["W"]
    noise.inputs["Scale"].default_value = params["Scale"]
    noise.inputs["Detail"].default_value = params["Detail"]
    noise.inputs["Roughness"].default_value = params["Roughness"]
    noise.inputs["Distortion"].default_value = params["Distortion"]
    return noise

def make_leaf_material(seed, name="LeafFactory_Material"):
    """Faithful replication of shader_simple_greenery from

    Sampling order (all from numpy.random, seeded by raw SEED):
      1. noise_color_params: W, Scale, Detail, Roughness, Distortion  (for fac_color)
      2. fac_color_max: U(0.1, 1.0)                                  (MapRange To Max)
      3. color1_hsv: plant_green() -> H, S, V                        (MixRGB Color1)
      4. color2_hsv: plant_green() -> H, S, V                        (MixRGB Color2)
      5. noise_rough_params: W, Scale, Detail, Roughness, Distortion  (for rough)
      6. rough_from_min: U(0.1, 0.8)                                 (MapRange From Min)
      7. rough_from_max: U(0.1, 0.8)                                 (MapRange From Max)
      8. noise_translucent_params: W, Scale, Detail, Roughness, Distortion (for fac_translucent)
      9. translucent_from_min: U(0.6, 0.9)                           (MapRange From Min)
    """

    seed_all(seed)

    # 1. Noise for color factor
    noise_color_params = _sample_noise_params()
    # 2. MapRange To Max for color factor
    fac_color_to_max = float(np.random.uniform(0.1, 1.0))
    # 3-4. Two plant_green colors
    color1_hsv = _plant_green()
    color2_hsv = _plant_green()
    color1_rgba = _hsv2rgba(*color1_hsv)
    color2_rgba = _hsv2rgba(*color2_hsv)
    # 5. Noise for roughness
    noise_rough_params = _sample_noise_params()
    # 6-7. MapRange From Min / From Max for roughness
    rough_from_min = float(np.random.uniform(0.1, 0.8))
    rough_from_max = float(np.random.uniform(0.1, 0.8))
    # 8. Noise for translucent factor
    noise_translucent_params = _sample_noise_params()
    # 9. MapRange From Min for translucent factor
    translucent_from_min = float(np.random.uniform(0.6, 0.9))

    # --- Build node tree ---
    mat = _new_mat(name)
    nt = mat.node_tree
    link = nt.links.new

    # Noise -> MapRange(SMOOTHSTEP, To Max=fac_color_to_max) -> fac for color mix
    noise_color = _build_noise_node(nt, noise_color_params)
    map_range_color = nt.nodes.new("ShaderNodeMapRange")
    map_range_color.interpolation_type = "SMOOTHSTEP"
    # MapRange inputs: Value=0, From Min=1, From Max=2, To Min=3, To Max=4
    map_range_color.inputs[4].default_value = fac_color_to_max
    link(_get_noise_fac(noise_color), map_range_color.inputs["Value"])

    # MixRGB: blend Color1 and Color2 by the color factor
    mix_rgb = nt.nodes.new("ShaderNodeMix")
    mix_rgb.data_type = "RGBA"
    mix_rgb.blend_type = "MIX"
    link(map_range_color.outputs["Result"], mix_rgb.inputs[0])
    mix_rgb.inputs[6].default_value = color1_rgba
    mix_rgb.inputs[7].default_value = color2_rgba

    # TranslucentBSDF
    translucent_bsdf = nt.nodes.new("ShaderNodeBsdfTranslucent")
    link(mix_rgb.outputs[2], translucent_bsdf.inputs["Color"])

    # Noise -> MapRange(SMOOTHSTEP, From Min, From Max) -> roughness
    noise_rough = _build_noise_node(nt, noise_rough_params)
    map_range_rough = nt.nodes.new("ShaderNodeMapRange")
    map_range_rough.interpolation_type = "SMOOTHSTEP"
    map_range_rough.inputs[3].default_value = rough_from_min
    map_range_rough.inputs[4].default_value = rough_from_max
    link(_get_noise_fac(noise_rough), map_range_rough.inputs["Value"])

    # PrincipledBSDF
    principled = nt.nodes.new("ShaderNodeBsdfPrincipled")
    link(mix_rgb.outputs[2], principled.inputs["Base Color"])
    link(map_range_rough.outputs["Result"], principled.inputs["Roughness"])

    # Noise -> MapRange(SMOOTHSTEP, From Min=translucent_from_min) -> translucent fac
    noise_trans = _build_noise_node(nt, noise_translucent_params)
    map_range_trans = nt.nodes.new("ShaderNodeMapRange")
    map_range_trans.interpolation_type = "SMOOTHSTEP"
    map_range_trans.inputs[3].default_value = translucent_from_min
    link(_get_noise_fac(noise_trans), map_range_trans.inputs["Value"])

    # MixShader: fac=translucent_factor, 1=TranslucentBSDF, 2=PrincipledBSDF
    mix_shader = nt.nodes.new("ShaderNodeMixShader")
    link(map_range_trans.outputs["Result"], mix_shader.inputs["Fac"])
    link(translucent_bsdf.outputs["BSDF"], mix_shader.inputs[1])
    link(principled.outputs["BSDF"], mix_shader.inputs[2])

    # Output
    output = nt.nodes.new("ShaderNodeOutputMaterial")
    link(mix_shader.outputs["Shader"], output.inputs["Surface"])

    return mat

# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════

CATEG_MAT = make_leaf_material(SEED, "LeafFactory_Material")
CATEG_MAT.use_fake_user = True

# LeafFactory does NOT use wear_tear — no scratches / edge wear applied.

# ══════════════════════════════════════════════════════════════════════════════
# Geometry — copied verbatim from objects_blender/small_plants/LeafFactory.py
# ══════════════════════════════════════════════════════════════════════════════

random.seed(SEED)
np.random.seed(SEED)

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):
    bpy.data.meshes.remove(m)
bpy.context.scene.cursor.location = (0, 0, 0)

def make_leaf(genome=None):
    g = dict(leaf_width=0.5, alpha=0.3, use_wave=True, x_offset=0,
             flip_leaf=False, z_scaling=0, width_rand=0.33)
    if genome:
        g.update(genome)

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
    if g['flip_leaf']:
        a = a[::-1]
    x = np.sin(a) * (g['leaf_width'] + np.random.randn() * g['width_rand']) + g['x_offset']
    y = -np.cos(0.9 * (a - g['alpha']))
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
        bpy.context.object.modifiers['Wave'].height = np.random.randn() * 0.3
        bpy.context.object.modifiers['Wave'].width = 0.75 + np.random.randn() * 0.1
        bpy.context.object.modifiers['Wave'].speed = np.random.rand()

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target='MESH')
    bpy.context.scene.cursor.location = obj.data.vertices[-1].co
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    obj.location = (0, 0, 0)
    obj.scale *= 0.3
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return obj

obj = make_leaf()
obj.name = "LeafFactory"

# Attach textured material
obj.data.materials.clear()
obj.data.materials.append(CATEG_MAT)

print(f"LeafFactory built: {len(obj.data.vertices)} verts, "
      f"{len(obj.data.polygons)} faces, "
      f"{len(obj.data.materials)} material slots")

