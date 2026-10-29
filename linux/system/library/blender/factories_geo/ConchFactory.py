# [FL_INDEX: keywords="blender_factory, procedural_3d, ConchFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: ConchFactory | Category: factories_geo
# Prompt: A 3D model of a textured conch shell rendered from a three-quarter perspective, featuring a broad rounded body whorl with a pointed spire, prominent wavy ridges across the surface, and a wide aperture, decorated with irregular brown-and-cream undulating surface patterns.

import os
import math
import random
import colorsys

import bpy
import mathutils
import numpy as np

SEED = int(os.environ.get("SEED", "0"))
random.seed(SEED)
np.random.seed(SEED)


# -- helpers -------------------------------------------------------------------


def _seed_mat(seed):
    _s = ((seed + 1) * 2654435761) & 0xFFFFFFFF
    np.random.seed(_s); random.seed(_s)

def _hsv2rgba(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(float(h)%1, max(0,min(1,float(s))), max(0,min(1,float(v))))
    return (r, g, b, 1.0)

def _log_uniform(lo, hi):
    return float(np.exp(np.random.uniform(np.log(lo), np.log(hi))))

def _new_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; m.node_tree.nodes.clear()
    return m

def _fac(n):
    return n.outputs.get("Fac") or n.outputs.get("Factor") or n.outputs[0]

def make_category_mat(seed, name="MolluskMaterial"):
    _seed_mat(seed)
    if float(np.random.uniform(0, 1)) < 0.4:
        base_hue = float(np.random.uniform(0.0, 0.2))
    else:
        base_hue = float(np.random.uniform(0.05, 0.12))
    # ratio bimodal, x_scale=2, z_scale=log_uniform(0.2,1), distortion=log_uniform(2,20)
    ratio = (float(np.random.uniform(0.0, 0.3))
             if float(np.random.uniform(0, 1)) < 0.5
             else float(np.random.uniform(0.7, 1.0)))
    x_scale = 2.0
    z_scale = _log_uniform(0.2, 1.0)
    distortion = _log_uniform(2.0, 20.0)
    roughness = float(np.random.uniform(0.2, 0.8))
    specular = 0.3
    value_scale = _log_uniform(1.0, 20.0)
    saturation_scale = _log_uniform(0.4, 1.0)

    def _dark():
        return _hsv2rgba(
            base_hue + float(np.random.uniform(-0.06, 0.06)),
            float(np.random.uniform(0.6, 1.0)) * saturation_scale,
            0.005 * (value_scale ** 1.5),
        )
    def _light():
        return _hsv2rgba(
            base_hue + float(np.random.uniform(-0.06, 0.06)),
            float(np.random.uniform(0.6, 1.0)) * saturation_scale,
            0.05 * value_scale,
        )
    def _color_fn(dark_prob=0.4):
        return _dark() if float(np.random.uniform(0, 1)) < dark_prob else _light()

    n = int(np.random.randint(3, 5))  # 3 or 4 ColorRamp stops
    pos_0 = sorted(float(p) for p in np.random.uniform(0, 1, n))
    col_0 = [_color_fn(0.4) for _ in range(n)]
    pos_1 = sorted(float(p) for p in np.random.uniform(0, 1, n))
    col_1 = [_color_fn(0.4) for _ in range(n)]

    mat = _new_mat(name); nt = mat.node_tree; ln = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")

    # WaveTexture (SAW profile) — X bands
    wave_x = nt.nodes.new("ShaderNodeTexWave")
    wave_x.wave_profile = "SAW"
    wave_x.bands_direction = "X"
    ln(tc.outputs["Object"], wave_x.inputs["Vector"])
    wave_x.inputs["Scale"].default_value = x_scale
    wave_x.inputs["Distortion"].default_value = distortion

    # WaveTexture (SAW profile) — Z bands
    wave_z = nt.nodes.new("ShaderNodeTexWave")
    wave_z.wave_profile = "SAW"
    wave_z.bands_direction = "Z"
    ln(tc.outputs["Object"], wave_z.inputs["Vector"])
    wave_z.inputs["Scale"].default_value = z_scale
    wave_z.inputs["Distortion"].default_value = distortion

    # cr_0 from wave_x (HSV color mode, n sampled stops)
    cr_0 = nt.nodes.new("ShaderNodeValToRGB")
    cr_0.color_ramp.color_mode = "HSV"
    ln(_fac(wave_x), cr_0.inputs["Fac"])
    while len(cr_0.color_ramp.elements) < n:
        cr_0.color_ramp.elements.new(0.5)
    for i in range(n):
        cr_0.color_ramp.elements[i].position = pos_0[i]
        cr_0.color_ramp.elements[i].color = col_0[i]

    # cr_1 from wave_z
    cr_1 = nt.nodes.new("ShaderNodeValToRGB")
    cr_1.color_ramp.color_mode = "HSV"
    ln(_fac(wave_z), cr_1.inputs["Fac"])
    while len(cr_1.color_ramp.elements) < n:
        cr_1.color_ramp.elements.new(0.5)
    for i in range(n):
        cr_1.color_ramp.elements[i].position = pos_1[i]
        cr_1.color_ramp.elements[i].color = col_1[i]

    # MixRGB(ratio, cr_0, cr_1)
    mix_cr = nt.nodes.new("ShaderNodeMix"); mix_cr.data_type = "RGBA"
    mix_cr.inputs[0].default_value = float(ratio)
    ln(cr_0.outputs["Color"], mix_cr.inputs[6])
    ln(cr_1.outputs["Color"], mix_cr.inputs[7])

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    ln(mix_cr.outputs[2], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = roughness
    sk = "Specular IOR Level" if "Specular IOR Level" in bsdf.inputs else "Specular"
    bsdf.inputs[sk].default_value = specular
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    ln(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

CATEG_MAT = make_category_mat(SEED, "ConchFactory_Material")
CATEG_MAT.use_fake_user = True

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for e in list(bpy.data.objects):
        bpy.data.objects.remove(e)
    for t in list(bpy.data.textures):
        bpy.data.textures.remove(t)
    bpy.context.scene.cursor.location = (0, 0, 0)


def apply_tf(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def log_uniform(low, high):
    return float(np.exp(np.random.uniform(np.log(low), np.log(high))))


# -- snail spiral core --------------------------------------------------------

def build_cross_section(n=40, affine=1.0, spike=0.0, concave=2.2):
    """

    Build superellipse cross-section polygon.
    |cos(t)|^concave + |sin(t)|^concave defines the radius envelope.
    """

    perturb = 1.0 / (5 * n)
    angles = (np.arange(n) / n + np.random.uniform(-perturb, perturb, n)) * 2 * np.pi
    radius = np.abs(np.cos(angles)) ** concave + np.abs(np.sin(angles)) ** concave
    radius *= 1.0 + np.random.uniform(0, spike, n) * (np.random.uniform(0, 1, n) < 0.2)

    vertices = np.stack([
        np.cos(angles) * radius,
        np.sin(angles) * radius * affine,
        np.zeros_like(angles),
    ]).T

    edges = np.stack([np.arange(n), np.roll(np.arange(n), -1)]).T

    mesh = bpy.data.meshes.new("cross_section")
    mesh.from_pydata(vertices.tolist(), edges.tolist(), [])
    mesh.update()

    obj = bpy.data.objects.new("cross_section", mesh)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Small random rotation around Z
    obj.rotation_euler = (0, 0, float(np.random.uniform(0, np.pi / 12)))
    apply_tf(obj)

    return obj


def solve_scale(shrink, freq):
    return shrink ** (1.0 / freq)


def solve_lateral(ratio, freq, scale):
    indices = np.arange(freq)
    denom = (np.sin(2 * np.pi / freq * indices) * scale ** indices).sum()
    return ratio / denom


def solve_longitude(ratio, freq, scale):
    return ratio * (1 + scale ** freq) / freq


def snail_make(lateral=0.15, longitudinal=0.04, freq=28, scale=0.99,
               loop=8, affine=1.0, spike=0.0):
    """

    Uses ARRAY modifier with object offset to create spiral.
    """

    n = 40
    resolution = loop * freq
    concave = float(np.random.uniform(1.9, 2.1))

    # 1. Build cross-section
    obj = build_cross_section(n, affine, spike, concave)

    # 2. Create empty for object offset
    bpy.ops.object.empty_add(location=(0, 0, 0))
    empty = bpy.context.active_object
    empty.location = (longitudinal * np.random.choice([-1, 1]), 0, 0)
    empty.rotation_euler = (2 * np.pi / freq, 0, 0)
    empty.scale = (scale, scale, scale)

    # 3. Apply ARRAY modifier
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    mod = obj.modifiers.new("Array", 'ARRAY')
    mod.use_relative_offset = False
    mod.use_constant_offset = True
    mod.constant_offset_displace = (0, 0, lateral)
    mod.use_object_offset = True
    mod.offset_object = empty
    mod.count = resolution
    bpy.ops.object.modifier_apply(modifier=mod.name)

    # 4. Delete the empty
    bpy.ops.object.select_all(action="DESELECT")
    empty.select_set(True)
    bpy.context.view_layer.objects.active = empty
    bpy.ops.object.delete()

    # 5. Bridge edge loops to create surface
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.bridge_edge_loops()
    bpy.ops.object.mode_set(mode='OBJECT')

    return obj


def finalize_snail(obj):
    apply_tf(obj)

    # Normalize to max dimension = 1
    dims = obj.dimensions
    max_dim = max(dims)
    if max_dim > 1e-6:
        s = 1.0 / max_dim
        obj.scale = (s, s, s)
    apply_tf(obj)

    # Random rotation (full random Euler)
    obj.rotation_euler = tuple(np.random.uniform(0, 2 * np.pi, 3))
    apply_tf(obj)

    # Center the object
    bb = np.array([list(obj.matrix_world @ mathutils.Vector(c)) for c in obj.bound_box])
    ctr = (bb.min(axis=0) + bb.max(axis=0)) / 2.0
    obj.location = (-ctr[0], -ctr[1], -ctr[2])
    obj.location[2] += obj.dimensions[2] * 0.4
    apply_tf(obj)

    # Affine perturbation
    co = np.zeros(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)

    offsets = np.zeros_like(co)
    for axis in range(3):
        weights = np.random.uniform(-0.1, 0.1, 3)
        offsets[:, axis] = co @ weights
    co += offsets

    obj.data.vertices.foreach_set("co", co.reshape(-1))
    obj.data.update()

    return obj


# -- decoration ----------------------------------------------------------------

def subsurface2face_size(obj, face_size):
    """Subdivide mesh if average face area exceeds face_size."""

    arr = np.zeros(len(obj.data.polygons), dtype=float)
    if len(arr) == 0:
        return
    obj.data.polygons.foreach_get('area', arr)
    area = float(np.mean(arr))
    if area <= 1e-9 or face_size <= 0:
        return
    try:
        levels = int(np.ceil(np.log2(area / face_size)))
    except Exception:
        return
    if levels > 0:
        mod = obj.modifiers.new("sub", 'SUBSURF')
        mod.levels = levels
        mod.render_levels = levels
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)


def decorate_mollusk(obj, face_size=0.01):
    subsurface2face_size(obj, face_size)

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # SOLIDIFY: doubles geometry by creating inner+outer shell
    mod = obj.modifiers.new("solidify", 'SOLIDIFY')
    mod.thickness = 0.005
    bpy.ops.object.modifier_apply(modifier=mod.name)

    # DISPLACE: random STUCCI or MARBLE texture for surface detail
    t = np.random.choice(["STUCCI", "MARBLE"])
    tex = bpy.data.textures.new(name="mollusk_tex", type=t)
    tex.noise_scale = log_uniform(0.1, 0.2)
    mod2 = obj.modifiers.new("displace", 'DISPLACE')
    mod2.strength = 0.02
    mod2.mid_level = 0
    mod2.texture = tex
    bpy.ops.object.modifier_apply(modifier=mod2.name)


# -- main factory --------------------------------------------------------------

def build_conch():
    freq = 256

    shrink = float(np.random.uniform(0.7, 0.8))
    scale = solve_scale(shrink, freq)
    lateral = solve_lateral(float(np.random.uniform(0.3, 0.4)), freq, scale)
    longitude = solve_longitude(float(np.random.uniform(0.7, 0.8)), freq, scale)
    loop = int(np.random.randint(8, 10))
    affine = float(np.random.uniform(0.8, 0.9))

    obj = snail_make(lateral, longitude, freq, scale, loop, affine=affine, spike=0.1)
    return obj


def build_conch_factory():
    np.random.seed(SEED)
    random.seed(SEED)
    clear_scene()

    obj = build_conch()
    obj = finalize_snail(obj)

    print(f"Base geometry: {len(obj.data.vertices)} verts, "
          f"{len(obj.data.polygons)} faces")

    decorate_mollusk(obj, face_size=0.01)

    return obj


result = build_conch_factory()
result.data.materials.clear()
result.data.materials.append(CATEG_MAT)

result.name = "ConchFactory"
print(f"ConchFactory built: {len(result.data.vertices)} verts, "
      f"{len(result.data.polygons)} faces")
