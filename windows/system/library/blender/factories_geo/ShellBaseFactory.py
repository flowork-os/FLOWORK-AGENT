# [FL_INDEX: keywords="blender_factory, procedural_3d, ShellBaseFactory, infinigen, generator" | COT="Procedural 3D Blender asset generator from 3DCodeverse"]
# Asset: ShellBaseFactory | Category: factories_geo
# Prompt: A 3D model of a generic bivalve shell rendered from a three-quarter perspective, featuring two smooth rounded valve halves hinged together and partially open, with convex outer surfaces and an oval to circular outline, displayed with a clean white untextured surface.

import math
import random

import bmesh
import bpy
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


# ── shell geometry ────────────────────────────────────────────────────────────

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


# ── shell makers ─────────────────────────────────────────────────────────────

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


# ── main factory ──────────────────────────────────────────────────────────────

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


def build_shell_base_factory():
    np.random.seed(SEED)
    random.seed(SEED)
    clear_scene()

    # Simulate FixedSeed(factory_seed) from ShellBaseFactory.__init__
    # The FixedSeed saves state, seeds with SEED, consumes random calls,
    # then restores state. Since outer seed == factory_seed, restoring
    # brings us back to fresh seed(SEED) state.
    makers = [scallop_make, clam_make, mussel_make]
    old_state = np.random.get_state()
    np.random.seed(SEED)
    maker_idx = int(np.random.choice(len(makers)))
    z_scale = log_uniform(2, 10)  # consumed but not used for geometry
    np.random.set_state(old_state)

    chosen_maker = makers[maker_idx]
    print(f"ShellBaseFactory chose maker index {maker_idx}: {chosen_maker.__name__}")

    result = create_shell_asset(chosen_maker)
    return result


result = build_shell_base_factory()
result.name = "ShellBaseFactory"
print(f"ShellBaseFactory built: {len(result.data.vertices)} verts, "
      f"{len(result.data.polygons)} faces")
