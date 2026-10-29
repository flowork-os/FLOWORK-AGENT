# [FL_INDEX: keywords="blender_factory, procedural_3d, MusselFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: MusselFactory | Category: factories_geo
# Prompt: A 3D model of a textured mussel shell rendered from a three-quarter perspective, featuring two elongated teardrop-shaped valve halves hinged at a pointed end and partially open, with concentric growth ring patterns in brown-and-cream tones on the outer surfaces and a dark interior.

import os
import math
import random
import colorsys

import bmesh
import bpy
import numpy as np
from scipy.interpolate import interp1d

SEED = int(os.environ.get("SEED", 0))
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
    # base_hue: MolluskFactory.build_base_hue (40% broad, 60% narrow)
    if float(np.random.uniform(0, 1)) < 0.4:
        base_hue = float(np.random.uniform(0.0, 0.2))
    else:
        base_hue = float(np.random.uniform(0.05, 0.12))
    # Shell-type shader params (from shell.py ShellBaseFactory):
    # ratio=1, x_scale=2, z_scale=log_uniform(2,10), distortion=1
    ratio = 1.0
    x_scale = 2.0
    z_scale = _log_uniform(2.0, 10.0)
    distortion = 1.0
    # shader_mollusk locals
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

CATEG_MAT = make_category_mat(SEED, "MusselFactory_Material")
CATEG_MAT.use_fake_user = True

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for t in list(bpy.data.textures):
        bpy.data.textures.remove(t)
    bpy.context.scene.cursor.location = (0, 0, 0)


def apply_tf(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def read_co(obj):
    arr = np.zeros(len(obj.data.vertices) * 3)
    obj.data.vertices.foreach_get("co", arr)
    return arr.reshape(-1, 3)


def write_co(obj, arr):
    obj.data.vertices.foreach_set("co", arr.reshape(-1))
    obj.data.update()


def log_uniform(low, high):
    return float(np.exp(np.random.uniform(np.log(low), np.log(high))))


# -- shell geometry ------------------------------------------------------------

def build_filled_disc(n_verts=1024):
    bpy.ops.mesh.primitive_circle_add(vertices=n_verts, location=(1, 0, 0))
    obj = bpy.context.active_object
    apply_tf(obj)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.fill_grid()
    bpy.ops.object.mode_set(mode='OBJECT')

    return obj


def build_ellipse(obj, viewpoint=(0.0, 0.0, 1.0), softness=0.3):
    viewpoint = np.array(viewpoint)
    co = read_co(obj)

    x, y, z = co.T
    r = np.sqrt((x - 1) ** 2 + y ** 2 + z ** 2)
    t = 1.0 - softness + softness * r ** 4

    displacement = (1.0 - t)[:, np.newaxis] * (viewpoint[np.newaxis, :] - co)
    co += displacement
    write_co(obj, co)
    return obj


def shape_by_angles(obj, angles, scales):
    co = read_co(obj)
    x, y, z = co.T
    vert_angles = np.arctan2(y, x)

    f = interp1d(angles, scales, kind='quadratic', bounds_error=False, fill_value=0)
    vert_scales = f(vert_angles)

    co *= vert_scales[:, np.newaxis]
    write_co(obj, co)
    return obj


def deep_clone(obj):
    mesh_copy = obj.data.copy()
    clone = bpy.data.objects.new(obj.name + "_clone", mesh_copy)
    bpy.context.scene.collection.objects.link(clone)
    return clone


# -- mussel maker --------------------------------------------------------------

def mussel_make():
    """

    Build one mussel shell half.
    Matches ShellBaseFactory.mussel_make.
    """

    obj = build_filled_disc(1024)
    build_ellipse(obj, viewpoint=(0, 0, 1), softness=0.5)

    obj.scale = (1, 3, 1)
    apply_tf(obj)

    s = float(np.random.uniform(0.6, 0.8))
    angles = np.array([
        -0.5,
        -float(np.random.uniform(0.1, 0.15)),
        float(np.random.uniform(0.0, 0.25)),
        0.5,
    ]) * np.pi
    scales = [0, s, 1, float(np.random.uniform(0.6, 0.8))]
    shape_by_angles(obj, angles, scales)

    # No radial grooves for mussel
    # No hinge for mussel
    return obj


# -- main factory (base geometry) ----------------------------------------------

def create_shell_asset(maker_fn):
    upper = maker_fn()
    apply_tf(upper)

    dim = float(np.sqrt(upper.dimensions[0] * upper.dimensions[1] + 0.01))
    s = 1.0 / dim
    upper.scale = (s, s, s)
    upper.location[2] += 0.005
    apply_tf(upper)

    lower = deep_clone(upper)
    lower.scale = (1, 1, -1)
    apply_tf(lower)

    base = float(np.random.uniform(0, np.pi / 4))
    lower.rotation_euler[1] = -base
    upper.rotation_euler[1] = -base - float(np.random.uniform(np.pi / 6, np.pi / 3))

    bpy.ops.object.select_all(action="DESELECT")
    lower.select_set(True)
    upper.select_set(True)
    bpy.context.view_layer.objects.active = lower
    bpy.ops.object.join()

    result = bpy.context.active_object
    result.location = (0, 0, 0)
    result.rotation_euler = (0, 0, 0)
    result.scale = (1, 1, 1)
    return result


# -- decoration ----------------------------------------------------------------

def subsurface2face_size(obj, face_size):
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

    mod = obj.modifiers.new("solidify", 'SOLIDIFY')
    mod.thickness = 0.005
    bpy.ops.object.modifier_apply(modifier=mod.name)

    t = np.random.choice(["STUCCI", "MARBLE"])
    tex = bpy.data.textures.new(name="mollusk_tex", type=t)
    tex.noise_scale = log_uniform(0.1, 0.2)
    mod2 = obj.modifiers.new("displace", 'DISPLACE')
    mod2.strength = 0.02
    mod2.mid_level = 0
    mod2.texture = tex
    bpy.ops.object.modifier_apply(modifier=mod2.name)


# -- build composite ----------------------------------------------------------

def build_mussel_factory():
    np.random.seed(SEED)
    random.seed(SEED)
    clear_scene()
    obj = create_shell_asset(mussel_make)
    decorate_mollusk(obj, face_size=0.01)
    return obj


result = build_mussel_factory()
result.data.materials.clear()
result.data.materials.append(CATEG_MAT)

result.name = "MusselFactory"
print(f"MusselFactory built: {len(result.data.vertices)} verts, "
      f"{len(result.data.polygons)} faces")
