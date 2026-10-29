# [FL_INDEX: keywords="blender_factory, procedural_3d, MolluskFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: MolluskFactory | Category: factories_geo
# Prompt: A 3D model of a generic mollusk bivalve shell rendered from a three-quarter perspective, featuring two rounded oval valve halves connected at a hinge and partially open, with smooth outer surfaces showing subtle growth line textures in warm beige tones and a darker interior cavity.

import math
import random

import bmesh
import bpy
import mathutils
import numpy as np
from scipy.interpolate import interp1d

SEED = 0
random.seed(SEED)
np.random.seed(SEED)


# ── helpers ───────────────────────────────────────────────────────────────────

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    for m in list(bpy.data.meshes):
        bpy.data.meshes.remove(m)
    for e in list(bpy.data.objects):
        bpy.data.objects.remove(e)
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


# ── decoration ────────────────────────────────────────────────────────────────

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


# ══════════════════════════════════════════════════════════════════════════════
# SNAIL GEOMETRY (from SnailBaseFactory)
# ══════════════════════════════════════════════════════════════════════════════

def build_cross_section(n=40, affine=1.0, spike=0.0, concave=2.2):
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
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

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
    n = 40
    resolution = loop * freq
    concave = float(np.random.uniform(1.9, 2.1))

    obj = build_cross_section(n, affine, spike, concave)

    bpy.ops.object.empty_add(location=(0, 0, 0))
    empty = bpy.context.active_object
    empty.location = (longitudinal * np.random.choice([-1, 1]), 0, 0)
    empty.rotation_euler = (2 * np.pi / freq, 0, 0)
    empty.scale = (scale, scale, scale)

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

    bpy.ops.object.select_all(action="DESELECT")
    empty.select_set(True)
    bpy.context.view_layer.objects.active = empty
    bpy.ops.object.delete()

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

    dims = obj.dimensions
    max_dim = max(dims)
    if max_dim > 1e-6:
        s = 1.0 / max_dim
        obj.scale = (s, s, s)
    apply_tf(obj)

    obj.rotation_euler = tuple(np.random.uniform(0, 2 * np.pi, 3))
    apply_tf(obj)

    bb = np.array([list(obj.matrix_world @ mathutils.Vector(c)) for c in obj.bound_box])
    ctr = (bb.min(axis=0) + bb.max(axis=0)) / 2.0
    obj.location = (-ctr[0], -ctr[1], -ctr[2])
    obj.location[2] += obj.dimensions[2] * 0.4
    apply_tf(obj)

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


# Snail type builders

def build_volute():
    freq = 256
    shrink = float(np.random.uniform(0.5, 0.6))
    scale = solve_scale(shrink, freq)
    lateral = solve_lateral(float(np.random.uniform(0.4, 0.5)), freq, scale)
    longitude = solve_longitude(float(np.random.uniform(0.6, 0.7)), freq, scale)
    loop = int(np.random.randint(4, 5))
    return snail_make(lateral, longitude, freq, scale, loop)


def build_nautilus():
    freq = 256
    shrink = float(np.random.uniform(0.4, 0.5))
    scale = solve_scale(shrink, freq)
    lateral = solve_lateral(float(np.random.uniform(1.2, 1.4)), freq, scale)
    longitude = solve_longitude(float(np.random.uniform(0.2, 0.3)), freq, scale)
    loop = int(np.random.randint(4, 5))
    return snail_make(lateral, longitude, freq, scale, loop)


def build_plain_snail():
    return snail_make(lateral=0.15, longitudinal=0.04, freq=28, scale=0.99, loop=8)


def build_conch():
    freq = 256
    shrink = float(np.random.uniform(0.7, 0.8))
    scale = solve_scale(shrink, freq)
    lateral = solve_lateral(float(np.random.uniform(0.3, 0.4)), freq, scale)
    longitude = solve_longitude(float(np.random.uniform(0.7, 0.8)), freq, scale)
    loop = int(np.random.randint(8, 10))
    return snail_make(lateral, longitude, freq, scale, loop,
                      affine=float(np.random.uniform(0.8, 0.9)), spike=0.1)


# ══════════════════════════════════════════════════════════════════════════════
# SHELL GEOMETRY (from ShellBaseFactory)
# ══════════════════════════════════════════════════════════════════════════════

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


def add_radial_groove(obj):
    co = read_co(obj)
    x, y, z = co.T
    a = np.arctan(y / (x + 1e-6 * (x >= 0).astype(float)))
    r = np.sqrt(x * x + y * y + z * z)
    fn = 0.02 * np.cos(a * 45) * np.clip(r - 0.25, 0, None)
    for i in range(3):
        co[:, i] += fn[i]
    write_co(obj, co)
    return obj


def add_hinge(obj):
    length = 0.4
    width = 0.1
    x_fac = float(np.random.uniform(0.8, 1.0))
    vertices = [
        [0, -length, 0],
        [width, -length * x_fac, 0],
        [width, length * x_fac, 0],
        [0, length, 0],
    ]
    mesh = bpy.data.meshes.new("hinge")
    mesh.from_pydata(vertices, [], [[0, 1, 2, 3]])
    mesh.update()
    hinge = bpy.data.objects.new("hinge", mesh)
    bpy.context.collection.objects.link(hinge)
    bpy.context.view_layer.objects.active = hinge
    hinge.select_set(True)

    mod = hinge.modifiers.new("sub", 'SUBSURF')
    mod.levels = 2
    mod.render_levels = 2
    mod.subdivision_type = 'SIMPLE'
    bpy.ops.object.modifier_apply(modifier=mod.name)

    tex = bpy.data.textures.new(name="hinge_tex", type='STUCCI')
    mod2 = hinge.modifiers.new("disp", 'DISPLACE')
    mod2.strength = 0.2
    mod2.texture = tex
    bpy.ops.object.modifier_apply(modifier=mod2.name)

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    hinge.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.join()
    return bpy.context.active_object


def deep_clone(obj):
    mesh_copy = obj.data.copy()
    clone = bpy.data.objects.new(obj.name + "_clone", mesh_copy)
    bpy.context.collection.objects.link(clone)
    return clone


# Shell makers

def scallop_make():
    obj = build_filled_disc(1024)
    build_ellipse(obj, viewpoint=(0, 0, 1), softness=0.3)
    obj.scale = (1, 1.2, 1)
    apply_tf(obj)
    boundary = 0.42
    outer = float(np.random.uniform(0.28, 0.32))
    inner = float(np.random.uniform(0.18, 0.22))
    s = float(np.random.uniform(0.6, 0.7))
    angles = np.array([-boundary, -outer, -inner, inner, outer, boundary]) * np.pi
    scales = [0, s, 1, 1, s, 0]
    shape_by_angles(obj, angles, scales)
    add_radial_groove(obj)
    obj = add_hinge(obj)
    return obj


def clam_make():
    obj = build_filled_disc(1024)
    build_ellipse(obj, viewpoint=(0, 0, 1), softness=0.5)
    obj.scale = (1, 1.2, 1)
    apply_tf(obj)
    s = float(np.random.uniform(0.6, 0.7))
    angles = [
        -float(np.random.uniform(0.4, 0.5)),
        -float(np.random.uniform(0.3, 0.35)),
        float(np.random.uniform(-0.25, 0.25)),
        float(np.random.uniform(0.3, 0.35)),
        float(np.random.uniform(0.4, 0.5)),
    ]
    scales = [0, s, 1, s, 0]
    shape_by_angles(obj, np.array(angles) * np.pi, scales)
    return obj


def mussel_make():
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
    return obj


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


# ══════════════════════════════════════════════════════════════════════════════
# MAIN FACTORY
# ══════════════════════════════════════════════════════════════════════════════

def build_mollusk_factory():
    clear_scene()

    # Simulate MolluskFactory.__init__ FixedSeed(SEED):
    # Choose between SnailBase (0) and ShellBase (1)
    np.random.seed(SEED)
    type_choice = int(np.random.choice(2))  # equal weights [0.5, 0.5]

    # Determine specific maker within FixedSeed of the chosen base factory
    if type_choice == 0:
        # SnailBase.__init__ FixedSeed(SEED):
        np.random.seed(SEED)
        snail_builders = [build_volute, build_nautilus, build_plain_snail, build_conch]
        snail_idx = int(np.random.choice(len(snail_builders)))
        chosen_builder = snail_builders[snail_idx]
        is_snail = True
        print(f"MolluskFactory chose: SnailBase -> {chosen_builder.__name__}")
    else:
        # ShellBase.__init__ FixedSeed(SEED):
        np.random.seed(SEED)
        shell_makers = [scallop_make, clam_make, mussel_make]
        shell_idx = int(np.random.choice(len(shell_makers)))
        z_scale = log_uniform(2, 10)  # consumed but not used for geometry
        chosen_maker = shell_makers[shell_idx]
        is_snail = False
        print(f"MolluskFactory chose: ShellBase -> {chosen_maker.__name__}")

    # After all FixedSeed contexts restore, create_asset runs with fresh seed(SEED)
    np.random.seed(SEED)
    random.seed(SEED)

    if is_snail:
        obj = chosen_builder()
        obj = finalize_snail(obj)
    else:
        obj = create_shell_asset(chosen_maker)

    decorate_mollusk(obj, face_size=0.01)
    return obj


result = build_mollusk_factory()
result.name = "MolluskFactory"
print(f"MolluskFactory built: {len(result.data.vertices)} verts, "
      f"{len(result.data.polygons)} faces")
